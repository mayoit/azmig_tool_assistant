"""
Interactive wizard for Azure bulk migration
"""
from typing import Optional, List, Tuple
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import box
from azure.identity import DefaultAzureCredential
from azure.core.credentials import TokenCredential
from .models import (
    MigrationType,
    AzureMigrateProject,
    ReplicationCache,
    MachineValidationReport,
    ValidationResult
)
from .config.parsers import ConfigParser
from .mock import MockServersValidator
from .live import LiveServersValidator
from .clients.azure_migrate_client import AzureMigrateIntegration, RecoveryServicesIntegration

console = Console()


class MigrationWizard:
    """Interactive wizard for bulk migration workflow"""

    def __init__(self, live_mode: bool = False, credential: Optional[TokenCredential] = None):
        self.live_mode = live_mode

        # Use provided credential or create DefaultAzureCredential
        if live_mode:
            self.credential = credential if credential else DefaultAzureCredential()
        else:
            self.credential = None

        # Use appropriate validator based on mode
        if live_mode:
            self.validator = LiveServersValidator(self.credential)
        else:
            self.validator = MockServersValidator(success_rate=0.95)

        self.migrate_integration = AzureMigrateIntegration(
            self.credential) if live_mode else None
        self.recovery_integration = RecoveryServicesIntegration(
            self.credential) if live_mode else None

    def show_welcome(self):
        """Display welcome banner"""
        mode = "[green]LIVE[/green]" if self.live_mode else "[yellow]MOCK[/yellow]"
        console.print(Panel.fit(
            f"[bold cyan]Azure Bulk Migration Tool[/bold cyan]\n"
            f"Mode: {mode}\n"
            f"Version: 1.0.0",
            border_style="cyan",
            box=box.DOUBLE
        ))

    def select_migration_type(self) -> MigrationType:
        """Step 1: Select migration type (New or Patch)"""
        console.print("\n[bold cyan]Step 1: Migration Type[/bold cyan]")

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")

        table.add_row("1", "New Batch Migration - Start fresh migration batch")
        table.add_row(
            "2", "Patch Existing Migration - Update existing migration")

        console.print(table)

        choice = Prompt.ask(
            "Select migration type",
            choices=["1", "2"],
            default="1"
        )

        if choice == "1":
            console.print("[green]✓[/green] Selected: New Batch Migration\n")
            return MigrationType.NEW_BATCH
        else:
            console.print(
                "[green]✓[/green] Selected: Patch Existing Migration\n")
            return MigrationType.PATCH_EXISTING

    def select_migrate_project(self, subscription_id: Optional[str] = None) -> Optional[AzureMigrateProject]:
        """Step 2: Select Azure Migrate project"""
        console.print("[bold cyan]Step 2: Azure Migrate Project[/bold cyan]")

        if not self.live_mode:
            console.print(
                "[yellow]⚠ Mock mode: Using dummy project[/yellow]\n")
            return AzureMigrateProject(
                name="mock-migrate-project",
                resource_group="mock-rg",
                subscription_id="00000000-0000-0000-0000-000000000000",
                location="eastus"
            )

        # Get subscription ID if not provided
        if not subscription_id:
            subscription_id = Prompt.ask("Enter Azure Subscription ID")

        # Optionally filter by resource group
        filter_rg = Confirm.ask("Filter by resource group?", default=False)
        rg_name = None
        if filter_rg:
            rg_name = Prompt.ask("Enter resource group name")

        console.print("[cyan]Fetching Azure Migrate projects...[/cyan]")

        if self.migrate_integration:
            projects = self.migrate_integration.list_migrate_projects(
                subscription_id, rg_name)
        else:
            console.print(
                "[red]✗ Azure Migrate integration not available in mock mode[/red]\n")
            return None

        if not projects:
            console.print("[red]✗ No Azure Migrate projects found[/red]\n")
            return None

        # Display projects
        table = Table(title="Available Azure Migrate Projects",
                      box=box.ROUNDED)
        table.add_column("#", style="cyan")
        table.add_column("Project Name", style="green")
        table.add_column("Resource Group", style="yellow")
        table.add_column("Location", style="magenta")

        for idx, project in enumerate(projects, 1):
            table.add_row(str(idx), project.name,
                          project.resource_group, project.location)

        console.print(table)

        if len(projects) == 1:
            if Confirm.ask(f"Use project '{projects[0].name}'?", default=True):
                console.print(
                    f"[green]✓[/green] Selected: {projects[0].name}\n")
                return projects[0]
        else:
            choice = int(Prompt.ask(
                "Select project number",
                choices=[str(i) for i in range(1, len(projects) + 1)]
            ))
            selected = projects[choice - 1]
            console.print(f"[green]✓[/green] Selected: {selected.name}\n")
            return selected

        return None

    def select_replication_cache(self, subscription_id: str) -> Optional[ReplicationCache]:
        """Step 3: Select replication cache/staging"""
        console.print(
            "[bold cyan]Step 3: Replication Cache Configuration[/bold cyan]")

        if not self.live_mode:
            console.print("[yellow]⚠ Mock mode: Using dummy cache[/yellow]\n")
            return ReplicationCache(
                name="mock-cache",
                resource_group="mock-rg",
                storage_account="mockstorage",
                subscription_id="00000000-0000-0000-0000-000000000000"
            )

        # For now, manual input (could be enhanced to list existing caches)
        cache_rg = Prompt.ask("Enter cache resource group name")
        cache_name = Prompt.ask("Enter cache/staging storage account name")

        cache = ReplicationCache(
            name=f"{cache_name}-cache",
            resource_group=cache_rg,
            storage_account=cache_name,
            subscription_id=subscription_id
        )

        console.print(f"[green]✓[/green] Cache configured: {cache.name}\n")
        return cache

    def upload_and_validate_excel(self, excel_path: Optional[str] = None) -> Tuple[bool, List, List[ValidationResult]]:
        """Step 4: Upload and validate Excel file"""
        console.print(
            "[bold cyan]Step 4: Upload and Validate Excel[/bold cyan]")

        # Get Excel file path
        if not excel_path:
            excel_path = Prompt.ask("Enter path to Excel file")

        if not Path(excel_path).exists():
            console.print(f"[red]✗ File not found: {excel_path}[/red]\n")
            return False, [], []

        # Parse and validate Excel structure
        console.print("[cyan]Parsing Excel file...[/cyan]")
        parser = ConfigParser(excel_path)
        success, configs, validation_results = parser.parse_layer2()

        # Display validation results
        for result in validation_results:
            if result.passed:
                console.print(f"[green]✓[/green] {result.message}")
            else:
                console.print(f"[red]✗[/red] {result.message}")

        if not success:
            console.print(
                "\n[red]Excel validation failed. Please fix errors and try again.[/red]\n")
            return False, [], validation_results

        console.print(
            f"\n[green]✓[/green] Excel file validated successfully ({len(configs)} machines)\n")
        return True, configs, validation_results

    def run_azure_validations(self, configs: List, project: AzureMigrateProject) -> List[MachineValidationReport]:
        """Step 5: Run Azure validations"""
        console.print(
            "[bold cyan]Step 5: Azure Resource Validation[/bold cyan]")

        # Get user object ID for RBAC checks
        user_oid = None
        if Confirm.ask("Validate RBAC permissions?", default=True):
            user_oid = Prompt.ask(
                "Enter your Azure AD Object ID (optional)", default="")
            if not user_oid:
                user_oid = None

        # Run validations using the validator (mock or live)
        console.print("\n[cyan]Running validations...[/cyan]")
        validation_results = self.validator.validate_all(
            configs,
            project=project,
            user_object_id=user_oid,
            skip_rbac=(user_oid is None),
            skip_discovery=False
        )

        # Create validation reports
        reports = []
        for config in configs:
            machine_results = validation_results.get(
                config.target_machine_name, [])

            # Determine overall status
            all_passed = all(r.passed for r in machine_results)
            any_failed = any(not r.passed for r in machine_results)

            overall_status = "PASSED" if all_passed else (
                "FAILED" if any_failed else "WARNING")

            report = MachineValidationReport(
                config=config,
                validations=machine_results,
                overall_status=overall_status
            )
            reports.append(report)

        # Display summary
        self._display_validation_summary(reports)

        return reports

    def _display_validation_summary(self, reports: List[MachineValidationReport]):
        """Display validation summary table"""
        table = Table(title="Validation Summary", box=box.ROUNDED)
        table.add_column("Machine Name", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Passed", style="green")
        table.add_column("Failed", style="red")

        for report in reports:
            passed_count = sum(1 for v in report.validations if v.passed)
            failed_count = sum(1 for v in report.validations if not v.passed)

            status_color = "green" if report.overall_status == "PASSED" else "red"
            status_text = f"[{status_color}]{report.overall_status}[/{status_color}]"

            table.add_row(
                report.config.target_machine_name,
                status_text,
                str(passed_count),
                str(failed_count)
            )

        console.print("\n")
        console.print(table)
        console.print()

    def enable_replication(
        self,
        reports: List[MachineValidationReport],
        project: AzureMigrateProject,
        cache: ReplicationCache
    ) -> List[dict]:
        """Step 6: Enable replication for validated machines"""
        console.print("[bold cyan]Step 6: Enable Replication[/bold cyan]")

        # Filter valid machines
        valid_reports = [r for r in reports if r.is_valid()]

        if not valid_reports:
            console.print(
                "[red]✗ No machines passed validation. Cannot enable replication.[/red]\n")
            return []

        console.print(
            f"[green]{len(valid_reports)} machines ready for replication[/green]")

        if not Confirm.ask("Proceed with enabling replication?", default=True):
            console.print("[yellow]Replication cancelled by user[/yellow]\n")
            return []

        if not self.live_mode:
            console.print(
                "[yellow]⚠ Mock mode: Simulating replication enablement[/yellow]")
            results = []
            for report in valid_reports:
                results.append({
                    "machine_name": report.config.target_machine_name,
                    "status": "simulated_success",
                    "message": "Mock mode: Replication would be enabled"
                })
            return results

        # Enable replication for each machine
        results = []
        console.print("\n[cyan]Enabling replication...[/cyan]")

        for report in valid_reports:
            console.print(f"  Processing: {report.config.target_machine_name}")
            if self.migrate_integration:
                result = self.migrate_integration.enable_replication(
                    report.config,
                    project,
                    cache
                )
            else:
                result = {
                    "machine_name": report.config.target_machine_name,
                    "status": "not_implemented",
                    "message": "Replication integration not available"
                }
            results.append(result)

        console.print(f"\n[green]✓[/green] Replication enablement completed\n")
        return results

    def run(self, excel_path: Optional[str] = None, export_json: Optional[str] = None):
        """Run the complete migration wizard"""
        self.show_welcome()

        # Step 1: Migration type
        migration_type = self.select_migration_type()

        # Step 2: Select Azure Migrate project
        project = self.select_migrate_project()
        if not project:
            console.print(
                "[red]Cannot proceed without Azure Migrate project[/red]")
            return

        # Step 3: Select replication cache
        cache = self.select_replication_cache(project.subscription_id)
        if not cache:
            console.print(
                "[red]Cannot proceed without replication cache[/red]")
            return

        # Step 4: Upload and validate Excel
        success, configs, excel_validations = self.upload_and_validate_excel(
            excel_path)
        if not success or not configs:
            return

        # Step 5: Run Azure validations
        reports = self.run_azure_validations(configs, project)

        # Step 6: Enable replication
        if reports:
            replication_results = self.enable_replication(
                reports,
                project,
                cache
            )

            # Export results if requested
            if export_json and replication_results:
                import json
                with open(export_json, 'w') as f:
                    json.dump(replication_results, f, indent=2)
                console.print(
                    f"[blue]Results exported to: {export_json}[/blue]")

        console.print(
            "\n[bold green]Migration wizard completed![/bold green]\n")
