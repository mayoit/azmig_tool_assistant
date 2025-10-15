"""
Interactive wizard for Azure bulk migration
"""
from typing import Optional, List, Tuple, Dict
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import box
from azure.core.credentials import TokenCredential
from ..core.models import (
    MigrationType,
    AzureMigrateProject,
    ReplicationCache,
    MachineValidationReport,
    ValidationResult,
    ValidationStage,
    MigrationConfig,
    ValidationStatus
)
from ..config.parsers import ConfigParser
from ..validators.wrappers import ServersValidatorWrapper
from ..clients.azure_migrate_client import AzureMigrateIntegration, RecoveryServicesIntegration
from ..management.template_manager import TemplateManager
from ..management.project_manager import ProjectManager, ProjectConfig, ProjectAuthConfig, AuthMethod, ProjectStatus
from .interactive_prompts import InteractivePrompter
from ..utils.auth import get_current_user_object_id
from ..config.validation_config import ValidationConfig, get_validation_config
from ..validators.wrappers import IntelligentServersValidatorWrapper

console = Console()


class MigrationWizard:
    """Interactive wizard for bulk migration workflow"""

    def __init__(self, credential: Optional[TokenCredential] = None, project: Optional[ProjectConfig] = None):
        # Store credential for later initialization (after project selection)
        self._credential = credential
        self.credential = None  # Will be set after project/auth selection

        # These will be initialized after authentication
        self.validator = None
        self.migrate_integration = None
        self.recovery_integration = None

        # Add template manager for extracting Azure config from files
        self.template_manager = TemplateManager(console)

        # Project management
        self.project_manager = ProjectManager()
        self.current_project = project
        self.prompter = InteractivePrompter()

    def _initialize_azure_components(self, credential):
        """Initialize Azure components after authentication is established"""
        self.credential = credential
        validation_config = get_validation_config()
        self.validator = ServersValidatorWrapper(self.credential, validation_config)  # type: ignore
        self.migrate_integration = AzureMigrateIntegration(
            self.credential)  # type: ignore
        self.recovery_integration = RecoveryServicesIntegration(
            self.credential)  # type: ignore

    def _setup_token_caching_for_project(self):
        """Setup token caching for the current project if using interactive authentication"""
        if (self.current_project and
                self.current_project.auth_config.auth_method == AuthMethod.INTERACTIVE):

            try:
                from ..utils.auth import CachedCredentialFactory

                # Replace current credential with cached version
                cached_credential = CachedCredentialFactory.create_credential(
                    self.current_project.auth_config,
                    self.project_manager,
                    self.current_project
                )

                # Re-initialize Azure components with cached credential
                self._initialize_azure_components(cached_credential)

                console.print(
                    "[dim]🔐 Token caching enabled for interactive authentication[/dim]")

            except Exception as e:
                console.print(
                    f"[yellow]⚠️ Could not setup token caching: {e}[/yellow]")
                # Continue without caching

    def show_welcome(self):
        """Display welcome banner"""
        console.print(Panel.fit(
            f"[bold cyan]Azure Bulk Migration Tool[/bold cyan]\n"
            f"[green]Azure Integration Ready[/green]\n"
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

    def select_migrate_project(self, subscription_id: Optional[str] = None, azure_config: Optional[Dict] = None) -> Optional[AzureMigrateProject]:
        """Step 2: Select Azure Migrate project"""
        console.print("[bold cyan]Step 2: Azure Migrate Project[/bold cyan]")

        # Show extracted Azure config if available
        if azure_config:
            console.print(
                "[green]✓[/green] Using Azure configuration from server file:")
            config_table = Table(show_header=False, box=None, padding=(0, 1))
            config_table.add_column("Field", style="cyan")
            config_table.add_column("Value", style="green")

            if azure_config.get('subscription_id'):
                config_table.add_row(
                    "Subscription ID", azure_config['subscription_id'])
            if azure_config.get('migrate_project_name'):
                config_table.add_row(
                    "Project Name", azure_config['migrate_project_name'])
            if azure_config.get('appliance_type'):
                config_table.add_row(
                    "Appliance Type", azure_config['appliance_type'])
            if azure_config.get('region'):
                config_table.add_row("Region", azure_config['region'])

            console.print(config_table)
            console.print()

        # Get subscription ID if not provided
        if not subscription_id:
            # Try to use migrate project subscription from azure_config first
            if azure_config and azure_config.get('migrate_project_subscription'):
                subscription_id = azure_config['migrate_project_subscription']
                console.print(
                    f"[green]✓[/green] Using migrate project subscription from server file: {subscription_id}")
            elif azure_config and azure_config.get('subscription_id'):
                subscription_id = azure_config['subscription_id']
                console.print(
                    f"[green]✓[/green] Using subscription ID from server file: {subscription_id}")
            else:
                subscription_id = Prompt.ask("Enter Azure Subscription ID")

        # Auto-discover or optionally filter by resource group
        rg_name = None
        if azure_config and azure_config.get('migrate_resource_group'):
            rg_name = azure_config['migrate_resource_group']
            console.print(
                f"[green]✓[/green] Using resource group from configuration: {rg_name}")
        else:
            filter_rg = Confirm.ask("Filter by resource group?", default=False)
            if filter_rg:
                rg_name = Prompt.ask("Enter resource group name")

        console.print("[cyan]Fetching Azure Migrate projects...[/cyan]")

        if not subscription_id:
            console.print("[red]✗ Subscription ID is required[/red]")
            return None

        projects = self.migrate_integration.list_migrate_projects(
            subscription_id, rg_name)

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

    def select_replication_cache(self, subscription_id: str, azure_config: Optional[Dict] = None) -> Optional[ReplicationCache]:
        """Step 5: Select replication cache/staging"""
        console.print(
            "[bold cyan]Step 5: Replication Cache Configuration[/bold cyan]")

        # Auto-discover cache storage from LZ configuration
        if azure_config and azure_config.get('cache_storage_account') and azure_config.get('cache_storage_resource_group'):
            cache_name = azure_config['cache_storage_account']
            cache_rg = azure_config['cache_storage_resource_group']
            console.print(
                f"[green]✓[/green] Using cache storage from configuration:")
            console.print(f"[dim]→ Storage Account: {cache_name}[/dim]")
            console.print(f"[dim]→ Resource Group: {cache_rg}[/dim]")
            console.print(f"[dim]→ Subscription: {subscription_id}[/dim]")
            console.print(
                f"[dim]→ Region: {azure_config.get('region', 'Not specified')}[/dim]\n")
        else:
            # Fallback to manual input if no cache config available
            console.print(
                "No cache storage configuration found in file. Please enter manually:")
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

    def upload_and_validate_landing_zone_file(self, file_path: Optional[str] = None) -> Tuple[bool, List, List[ValidationResult], str]:
        """Upload and validate landing zone configuration file (CSV/JSON)"""
        console.print(
            "[bold cyan]Step 3: Upload and Validate Landing Zone Configuration[/bold cyan]")

        # Get file path
        if not file_path:
            file_path = Prompt.ask(
                "Enter path to landing zone configuration file")

        if not Path(file_path).exists():
            console.print(f"[red]✗ File not found: {file_path}[/red]\n")
            return False, [], [], file_path

        # Parse and validate file structure
        console.print(
            f"[cyan]Parsing landing zone configuration file...[/cyan]")
        parser = ConfigParser(file_path)

        # Validate file exists first
        file_result = parser.validate_file_exists()
        if not file_result.passed:
            console.print(f"[red]✗[/red] {file_result.message}")
            return False, [], [file_result], file_path
        else:
            console.print(f"[green]✓[/green] {file_result.message}")

        # Detect file type and use landing zone parser
        file_type = parser._detect_file_type()
        console.print(f"[dim]Detected file type: {file_type}[/dim]")

        if file_type in ["csv", "json"]:
            # Parse landing zone configurations
            console.print(
                f"[cyan]Parsing {file_type.upper()} landing zone configuration file...[/cyan]")
            try:
                success, lz_configs, message = parser.parse_landing_zone()

                validation_results = []
                if success and lz_configs:
                    console.print(
                        f"[green]✓[/green] Successfully parsed {len(lz_configs)} landing zone configuration(s)")
                    validation_results = [
                        ValidationResult(
                            stage=ValidationStage.EXCEL_STRUCTURE,
                            passed=True,
                            message=f"Landing zone configuration validated successfully"
                        )
                    ]
                elif success and not lz_configs:
                    console.print(
                        "[yellow]⚠[/yellow] File parsed successfully but contains no landing zone configurations")
                    validation_results = [
                        ValidationResult(
                            stage=ValidationStage.EXCEL_STRUCTURE,
                            passed=False,
                            message="No landing zone configurations found"
                        )
                    ]
                else:
                    console.print(
                        f"[red]✗[/red] Failed to parse landing zone file: {message}")
                    validation_results = [
                        ValidationResult(
                            stage=ValidationStage.EXCEL_STRUCTURE,
                            passed=False,
                            message=f"Failed to parse landing zone file: {message}"
                        )
                    ]

            except Exception as e:
                console.print(
                    f"[red]✗[/red] Error reading {file_type.upper()} file: {e}")
                success = False
                lz_configs = []
                validation_results = [
                    ValidationResult(
                        stage=ValidationStage.EXCEL_STRUCTURE,
                        passed=False,
                        message=f"Error reading {file_type.upper()} file: {str(e)}"
                    )
                ]
        else:
            console.print(
                f"[red]✗[/red] Unsupported file type for landing zone: {file_type}")
            console.print("Landing zone files must be CSV or JSON format")
            success = False
            lz_configs = []
            validation_results = [
                ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Unsupported file type for landing zone: {file_type}. Must be CSV or JSON."
                )
            ]

        # Display validation results
        for result in validation_results:
            if result.passed:
                console.print(f"[green]✓[/green] {result.message}")
            else:
                console.print(f"[red]✗[/red] {result.message}")

        if not success:
            console.print(
                "\n[red]Landing zone validation failed. Please fix errors and try again.[/red]\n")
            return False, [], validation_results, file_path

        console.print(
            f"\n[green]✓[/green] Landing zone file validated successfully ({len(lz_configs)} projects)\n")
        return True, lz_configs, validation_results, file_path

    def upload_and_validate_servers_file(self, file_path: Optional[str] = None) -> Tuple[bool, List, List[ValidationResult], str]:
        """Step 1.5: Upload and validate servers file (CSV/JSON/Excel)"""
        console.print(
            "[bold cyan]Step 3: Upload and Validate Server Configuration[/bold cyan]")

        # Get file path
        if not file_path:
            file_path = Prompt.ask("Enter path to server configuration file")

        if not Path(file_path).exists():
            console.print(f"[red]✗ File not found: {file_path}[/red]\n")
            return False, [], [], file_path

        # Parse and validate file structure
        console.print(f"[cyan]Parsing server configuration file...[/cyan]")
        parser = ConfigParser(file_path)

        # Validate file exists first
        file_result = parser.validate_file_exists()
        if not file_result.passed:
            console.print(f"[red]✗[/red] {file_result.message}")
            return False, [], [file_result], file_path
        else:
            console.print(f"[green]✓[/green] {file_result.message}")

        # Detect file type and use appropriate parser
        file_type = parser._detect_file_type()
        console.print(f"[dim]Detected file type: {file_type}[/dim]")

        if file_type == "excel":
            # Use Excel parser for .xlsx files
            success, configs, validation_results = parser.parse_servers()
        elif file_type in ["csv", "json"]:
            # For CSV/JSON files, parse server configurations
            console.print(
                f"[cyan]Parsing {file_type.upper()} server configuration file...[/cyan]")
            try:
                success, configs, validation_results = self._parse_csv_json_servers(
                    file_path, file_type)

                if success and configs:
                    console.print(
                        f"[green]✓[/green] Successfully parsed {len(configs)} server configuration(s)")
                elif success and not configs:
                    console.print(
                        "[yellow]⚠[/yellow] File parsed successfully but contains no server configurations")
                else:
                    console.print(
                        f"[red]✗[/red] Failed to parse {file_type.upper()} file")

            except Exception as e:
                console.print(
                    f"[red]✗[/red] Error reading {file_type.upper()} file: {e}")
                success = False
                configs = []
                validation_results = [
                    ValidationResult(
                        stage=ValidationStage.EXCEL_STRUCTURE,
                        passed=False,
                        message=f"Error reading {file_type.upper()} file: {str(e)}"
                    )
                ]
        else:
            console.print(f"[red]✗[/red] Unsupported file type: {file_type}")
            success = False
            configs = []
            validation_results = [
                ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Unsupported file type: {file_type}"
                )
            ]

        # Display validation results
        for result in validation_results:
            if result.passed:
                console.print(f"[green]✓[/green] {result.message}")
            else:
                console.print(f"[red]✗[/red] {result.message}")

        if not success:
            console.print(
                "\n[red]Excel validation failed. Please fix errors and try again.[/red]\n")
            return False, [], validation_results, file_path

        console.print(
            f"\n[green]✓[/green] Excel file validated successfully ({len(configs)} machines)\n")
        return True, configs, validation_results, file_path

    def run_azure_validations(self, configs: List, project: AzureMigrateProject) -> List[MachineValidationReport]:
        """Step 5: Run Azure validations"""
        console.print(
            "[bold cyan]Step 6: Azure Resource Validation[/bold cyan]")

        # Get validation configuration
        validation_config = get_validation_config()

        # Get user object ID for RBAC checks if RBAC validation is enabled
        user_oid = None
        if validation_config.is_servers_rbac_validation_enabled():
            console.print(
                "[cyan]RBAC validation enabled - detecting current user...[/cyan]")

            if self.credential:
                user_oid = get_current_user_object_id(self.credential)

                if not user_oid:
                    console.print(
                        "[yellow]⚠[/yellow] Could not auto-detect Azure AD Object ID")
                    console.print(
                        "[yellow]⚠[/yellow] RBAC validation will be skipped")
            else:
                console.print(
                    "[yellow]⚠[/yellow] No credential available for RBAC validation")
        else:
            console.print(
                "[dim]RBAC validation disabled by configuration[/dim]")

        # Show validation config being used
        console.print("[cyan]Using project validation settings[/cyan]")

        # Run validations using Azure validator
        console.print("\n[cyan]Running validations...[/cyan]")
        validation_results = self.validator.validate_all(
            configs,
            migrate_project_name=getattr(project, 'migrate_project_name', None) if project else None,
            migrate_project_rg=getattr(project, 'migrate_resource_group', None) if project else None
        )

        # Create validation reports from new wrapper results
        reports = []
        for server_result in validation_results.server_results:
            config = server_result.machine_config

            # Convert server validation results to machine results format
            machine_results = []
            
            # Convert individual validation results to the old format
            result_mappings = [
                ("Region", server_result.region_result),
                ("Resource Group", server_result.resource_group_result), 
                ("VNet", server_result.vnet_result),
                ("VM SKU", server_result.vmsku_result),
                ("Disk", server_result.disk_result),
                ("Discovery", server_result.discovery_result),
                ("RBAC", server_result.rbac_result)
            ]
            
            for name, result in result_mappings:
                if result and hasattr(result, 'status'):
                    # Convert to old ValidationResult format
                    from ..core.models import ValidationResult, ValidationStage
                    machine_results.append(ValidationResult(
                        stage=ValidationStage.AZURE_RESOURCES,  # Default stage
                        passed=result.status == ValidationStatus.OK,
                        message=getattr(result, 'message', f"{name} validation"),
                        details=getattr(result, 'details', {}) if hasattr(result, 'details') else {}
                    ))

            # Determine overall status
            if server_result.overall_status == ValidationStatus.OK:
                overall_status = "PASSED"
            elif server_result.overall_status == ValidationStatus.FAILED:
                overall_status = "FAILED"
            elif server_result.overall_status == ValidationStatus.WARNING:
                overall_status = "WARNING"
            else:
                overall_status = "SKIPPED"

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
                report.config.machine_name,
                status_text,
                str(passed_count),
                str(failed_count)
            )

        console.print("\n")
        console.print(table)
        console.print()

    def run_landing_zone_validation_workflow(self, lz_configs: List, validation_choice: str, file_path: str):
        """Handle Landing Zone validation workflow specifically"""
        console.print("[bold cyan]Step 4: Landing Zone Validation[/bold cyan]")

        # For Landing Zone validation, we validate the migrate projects themselves
        # not individual machines
        validation_config = get_validation_config()

        console.print(
            f"[cyan]Found {len(lz_configs)} migrate project(s) to validate[/cyan]")

        # Initialize Landing Zone validator if not already done
        if not hasattr(self, 'lz_validator') or not self.lz_validator:
            if not self.credential:
                console.print("[red]✗[/red] Azure credentials not available for validation")
                console.print("[yellow]⚠[/yellow] Please ensure you are authenticated to Azure")
                return
            from ..validators.wrappers import LandingZoneValidatorWrapper
            self.lz_validator = LandingZoneValidatorWrapper(self.credential, validation_config)

        # Run Landing Zone validations
        console.print("\n[cyan]Running Landing Zone validations...[/cyan]")

        all_results = []
        validation_errors = []

        for lz_config in lz_configs:
            console.print(
                f"\n[dim]Validating project: {lz_config.migrate_project_name}[/dim]")
            console.print(
                f"[dim]→ Subscription: {lz_config.subscription_id}[/dim]")
            console.print(f"[dim]→ Region: {lz_config.region}[/dim]")

            # Check if this migrate project is already validated
            skip_validations = {}
            revalidate_all = False

            if hasattr(self, 'current_project') and self.current_project:
                # Check if migrate project is already validated
                if self.project_manager.is_migrate_project_already_validated(
                    self.current_project,
                    lz_config.migrate_project_name,
                    getattr(lz_config, 'migrate_project_subscription',
                            lz_config.subscription_id)
                ):
                    console.print(
                        "  [yellow]⚠ This migrate project has already been validated[/yellow]")
                    revalidate_all = Confirm.ask(
                        "  Do you want to revalidate all components?", default=False)
                    if not revalidate_all:
                        console.print(
                            "  [green]✓ Using cached validation results[/green]")
                        continue  # Skip to next LZ config

                # Check individual components if not revalidating all
                if not revalidate_all:
                    # Check appliance
                    appliance_name = getattr(lz_config, 'appliance_name', '')
                    if appliance_name and self.project_manager.is_appliance_already_validated(
                        self.current_project, appliance_name, lz_config.migrate_project_name
                    ):
                        appliance_info = self.project_manager.get_validated_component_info(
                            self.current_project, "appliance",
                            appliance_name=appliance_name,
                            migrate_project_name=lz_config.migrate_project_name
                        )
                        validated_at = appliance_info.get(
                            'validated_at', 'N/A') if appliance_info else 'N/A'
                        console.print(
                            f"  [cyan]📋 Appliance '{appliance_name}' already validated ({validated_at})[/cyan]")
                        skip_appliance = not Confirm.ask(
                            "    Revalidate appliance?", default=False)
                        skip_validations['appliance'] = skip_appliance

                    # Check cache storage
                    storage_account = getattr(
                        lz_config, 'cache_storage_account', '')
                    if storage_account and self.project_manager.is_cache_storage_already_validated(
                        self.current_project, storage_account, lz_config.subscription_id
                    ):
                        storage_info = self.project_manager.get_validated_component_info(
                            self.current_project, "cache_storage",
                            storage_account=storage_account,
                            subscription_id=lz_config.subscription_id
                        )
                        validated_at = storage_info.get(
                            'validated_at', 'N/A') if storage_info else 'N/A'
                        console.print(
                            f"  [cyan]📋 Cache Storage '{storage_account}' already validated ({validated_at})[/cyan]")
                        skip_storage = not Confirm.ask(
                            "    Revalidate cache storage?", default=False)
                        skip_validations['cache_storage'] = skip_storage

            # Run LZ validations based on config
            project_results = []

            # 1. Access/RBAC Validation
            if validation_config.is_access_validation_enabled():
                console.print("  • Checking access permissions...")
                try:
                    access_result = self.lz_validator.validate_access(
                        lz_config)
                    
                    if access_result:  # Only process if validation was performed
                        project_results.append(access_result)

                        if access_result.status == ValidationStatus.FAILED:
                            console.print(
                                f"    [red]✗[/red] {access_result.message}")
                            validation_errors.append(
                                f"{lz_config.migrate_project_name}: {access_result.message}")
                        else:
                            console.print(
                                f"    [green]✓[/green] {access_result.message}")
                    else:
                        console.print("    [dim]Access validation disabled[/dim]")

                except Exception as e:
                    console.print(
                        f"    [red]✗[/red] Access validation failed: {str(e)}")
                    validation_errors.append(
                        f"{lz_config.migrate_project_name}: Access validation error - {str(e)}")

            # 2. Appliance Health Check
            if validation_config.is_appliance_health_enabled():
                if skip_validations.get('appliance', False):
                    console.print(
                        "  • [dim]Skipping appliance health check (using cached result)[/dim]")
                    console.print(
                        f"    [green]✓[/green] Appliance '{getattr(lz_config, 'appliance_name', 'Unknown')}' validation skipped (cached)")
                else:
                    console.print("  • Checking appliance health...")
                    try:
                        appliance_result = self.lz_validator.validate_appliance_health(
                            lz_config)
                        
                        if appliance_result:  # Only process if validation was performed
                            project_results.append(appliance_result)

                            if appliance_result.status == ValidationStatus.FAILED:
                                console.print(
                                    f"    [red]✗[/red] {appliance_result.message}")
                                validation_errors.append(
                                    f"{lz_config.migrate_project_name}: {appliance_result.message}")
                            else:
                                console.print(
                                    f"    [green]✓[/green] {appliance_result.message}")
                        else:
                            console.print("    [dim]Appliance health validation disabled[/dim]")

                    except Exception as e:
                        console.print(
                            f"    [red]✗[/red] Appliance health check failed: {str(e)}")
                        validation_errors.append(
                            f"{lz_config.migrate_project_name}: Appliance health error - {str(e)}")

            # 3. Storage Cache Validation
            if validation_config.is_storage_cache_enabled():
                if skip_validations.get('cache_storage', False):
                    console.print(
                        "  • [dim]Skipping cache storage validation (using cached result)[/dim]")
                    console.print(
                        f"    [green]✓[/green] Cache storage '{getattr(lz_config, 'cache_storage_account', 'Unknown')}' validation skipped (cached)")
                else:
                    console.print("  • Validating cache storage...")
                    try:
                        storage_result = self.lz_validator.validate_storage_cache(
                            lz_config)
                        
                        if storage_result:  # Only process if validation was performed
                            project_results.append(storage_result)

                            if storage_result.status == ValidationStatus.FAILED:
                                console.print(
                                    f"    [red]✗[/red] {storage_result.message}")
                                validation_errors.append(
                                    f"{lz_config.migrate_project_name}: {storage_result.message}")
                            else:
                                console.print(
                                    f"    [green]✓[/green] {storage_result.message}")
                        else:
                            console.print("    [dim]Storage cache validation disabled[/dim]")

                    except Exception as e:
                        console.print(
                            f"    [red]✗[/red] Storage cache validation failed: {str(e)}")
                        validation_errors.append(
                            f"{lz_config.migrate_project_name}: Storage cache error - {str(e)}")

            # 4. Quota Validation
            if validation_config.is_quota_validation_enabled():
                console.print("  • Checking quotas...")
                try:
                    quota_result = self.lz_validator.validate_quota(lz_config)
                    
                    if quota_result:  # Only process if validation was performed
                        project_results.append(quota_result)

                        if quota_result.status == ValidationStatus.FAILED:
                            console.print(
                                f"    [red]✗[/red] {quota_result.message}")
                            validation_errors.append(
                                f"{lz_config.migrate_project_name}: {quota_result.message}")
                        else:
                            console.print(
                                f"    [green]✓[/green] {quota_result.message}")
                    else:
                        console.print("    [dim]Quota validation disabled[/dim]")

                except Exception as e:
                    console.print(
                        f"    [red]✗[/red] Quota validation failed: {str(e)}")
                    validation_errors.append(
                        f"{lz_config.migrate_project_name}: Quota validation error - {str(e)}")

            all_results.extend(project_results)

            # Save successfully validated LZ config to project (if all validations passed for this LZ)
            lz_validation_passed = all(
                result.status == ValidationStatus.OK
                for result in project_results
            )

            if lz_validation_passed and hasattr(self, 'current_project') and self.current_project:
                # Convert LZ config to dictionary format matching CSV structure
                lz_config_dict = {
                    "Subscription ID": lz_config.subscription_id,
                    "Migrate Project Name": lz_config.migrate_project_name,
                    "Appliance Type": getattr(lz_config, 'appliance_type', ''),
                    "Appliance Name": getattr(lz_config, 'appliance_name', ''),
                    "Region": lz_config.region,
                    "Cache Storage Account": getattr(lz_config, 'cache_storage_account', ''),
                    "Cache Storage Resource Group": getattr(lz_config, 'cache_storage_resource_group', ''),
                    "Migrate Project Subscription": getattr(lz_config, 'migrate_project_subscription', lz_config.subscription_id),
                    "Migrate Resource Group": getattr(lz_config, 'migrate_resource_group', ''),
                    "Recovery Vault Name": getattr(lz_config, 'recovery_vault_name', '')
                }

                # Save to project configuration
                try:
                    self.project_manager.add_validated_lz_config(
                        self.current_project, lz_config_dict
                    )
                    console.print(
                        f"    [green]💾 Saved validated configuration for project: {lz_config.migrate_project_name}[/green]")
                except Exception as e:
                    console.print(
                        f"    [yellow]⚠ Warning: Could not save LZ config: {str(e)}[/yellow]")

        # Display results summary
        console.print(
            f"\n[bold cyan]Landing Zone Validation Summary[/bold cyan]")
        console.print(f"[dim]Validated {len(lz_configs)} project(s)[/dim]")

        if validation_errors:
            console.print(
                f"\n[red]❌ {len(validation_errors)} validation error(s) found:[/red]")
            for error in validation_errors:
                console.print(f"  [red]•[/red] {error}")
            console.print(
                f"\n[red]⚠[/red] Landing Zone validation FAILED - please fix the above issues before proceeding")
        else:
            console.print(
                f"\n[green]✅ All Landing Zone validations PASSED[/green]")
            console.print(
                f"[green]✓[/green] Landing Zone is ready for migration")

        console.print(
            f"\n[blue]Landing Zone validation finished for validation choice: {validation_choice}[/blue]")

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

        # Enable replication using Azure integration

        # Enable replication for each machine
        results = []
        console.print("\n[cyan]Enabling replication...[/cyan]")

        for report in valid_reports:
            console.print(f"  Processing: {report.config.machine_name}")
            if self.migrate_integration:
                result = self.migrate_integration.enable_replication(
                    report.config,
                    project,
                    cache
                )
            else:
                result = {
                    "machine_name": report.config.machine_name,
                    "status": "not_implemented",
                    "message": "Replication integration not available"
                }
            results.append(result)

        console.print(f"\n[green]✓[/green] Replication enablement completed\n")
        return results

    def run(self, excel_path: Optional[str] = None, export_json: Optional[str] = None):
        """Run the complete migration wizard"""
        self.show_welcome()

        # Step 1: Project Selection (New vs Patch Existing) - First Prompt
        if not self.current_project:
            migration_type, existing_project = self.prompter.prompt_migration_type()

            if migration_type == "patch" and existing_project:
                # Use existing project and its saved authentication
                self.current_project = existing_project
                console.print(
                    f"\n[green]✓[/green] Using existing project: {existing_project.project_name}")
                console.print(
                    f"[dim]→ Auth method: {existing_project.auth_config.auth_method.value}[/dim]")
                console.print(
                    f"[dim]→ Project folder: {existing_project.project_path}[/dim]")

                # Display any previously validated LZ configurations
                if self.project_manager.has_validated_lz_configs(existing_project):
                    console.print(
                        "\n[cyan]📋 Previously Validated Landing Zone Configurations:[/cyan]")
                    lz_configs = self.project_manager.get_validated_lz_configs(
                        existing_project)

                    if lz_configs["migrate_projects"]:
                        console.print("  [yellow]Migrate Projects:[/yellow]")
                        for mp in lz_configs["migrate_projects"]:
                            # Check if this is the new grouped structure or old flat structure
                            if 'app_landing_zones' in mp:
                                # New grouped structure
                                console.print(f"    • {mp.get('Migrate Project Name', 'Unknown')} "
                                              f"({mp.get('Migrate Project Subscription', 'Unknown Subscription')})")
                                console.print(
                                    f"      → Appliance: {mp.get('Appliance Name', 'Unknown')} ({mp.get('Appliance Type', 'Unknown Type')})")
                                console.print(
                                    f"      → Recovery Vault: {mp.get('Recovery Vault Name', 'None')}")

                                # Display app landing zones for this migrate project
                                app_lzs = mp.get('app_landing_zones', [])
                                if app_lzs:
                                    console.print(
                                        f"      → Application Landing Zones ({len(app_lzs)}):")
                                    for alz in app_lzs:
                                        console.print(f"        • {alz.get('Cache Storage Account', 'Unknown')} "
                                                      f"in {alz.get('Region', 'Unknown Region')} "
                                                      f"({alz.get('Subscription ID', 'Unknown Sub')})")
                                else:
                                    console.print(
                                        f"      → No application landing zones configured")
                            else:
                                # Old flat structure - display in legacy format
                                console.print(f"    • {mp.get('Migrate Project Name', 'Unknown')} "
                                              f"({mp.get('Subscription ID', 'Unknown Subscription')}) "
                                              f"in {mp.get('Region', 'Unknown Region')}")
                                console.print(
                                    f"      → [dim]Legacy format - will be upgraded on next validation[/dim]")

                    console.print(
                        "[green]✓ These configurations will be available during server validation[/green]\n")
                else:
                    console.print(
                        "[dim]→ No previous LZ validations found[/dim]\n")

                # Display and configure project validation settings
                console.print(
                    "[bold cyan]📋 Project Validation Settings[/bold cyan]")

                # Create ValidationConfig from project's validation_settings
                from ..config.validation_config import ValidationConfig
                global_validation_config = ValidationConfig(
                    config_data=self.current_project.validation_settings.to_dict()
                )

                # Display current validation profile summary
                settings = self.current_project.validation_settings
                console.print(
                    f"[green]✓[/green] Using project validation settings")
                console.print(
                    f"[dim]   • Landing Zone validations: {sum([settings.lz_access_validation, settings.lz_appliance_health, settings.lz_storage_cache, settings.lz_quota_validation])}/4 enabled[/dim]")
                console.print(f"[dim]   • Server validations: {sum([settings.server_region_validation, settings.server_resource_group_validation, settings.server_vnet_subnet_validation, settings.server_vm_sku_validation, settings.server_disk_type_validation, settings.server_discovery_validation, settings.server_rbac_validation])}/7 enabled[/dim]")
                console.print(
                    f"[dim]   • Parallel execution: {'enabled' if settings.parallel_execution else 'disabled'}[/dim]")
                console.print(
                    f"[dim]   • Fail fast: {'enabled' if settings.fail_fast else 'disabled'}[/dim]")

                # Option to modify validation settings
                modify_settings = Confirm.ask(
                    "Do you want to modify validation settings for this session?", default=False)
                if modify_settings:
                    self._prompt_validation_settings_editor()
                    # Recreate ValidationConfig with updated settings
                    global_validation_config = ValidationConfig(
                        config_data=self.current_project.validation_settings.to_dict()
                    )
                console.print()  # Add spacing
            else:
                # Create new project - need authentication first
                auth_config = self.prompter.prompt_authentication_config()
                self.current_project = self.prompter.prompt_new_project_creation(
                    auth_config)

                # Initialize token caching for the newly created project
                if self.current_project:
                    self._setup_token_caching_for_project()

                # Display validation settings for new project if project was created successfully
                if self.current_project:
                    console.print(
                        "\n[bold cyan]📋 Project Validation Settings[/bold cyan]")

                    # Create ValidationConfig from project's validation_settings
                    from ..config.validation_config import ValidationConfig
                    global_validation_config = ValidationConfig(
                        config_data=self.current_project.validation_settings.to_dict()
                    )

                    # Display current validation profile summary
                    settings = self.current_project.validation_settings
                    console.print(
                        f"[green]✓[/green] Using default validation settings for new project")
                    console.print(
                        f"[dim]   • Landing Zone validations: {sum([settings.lz_access_validation, settings.lz_appliance_health, settings.lz_storage_cache, settings.lz_quota_validation])}/4 enabled[/dim]")
                    console.print(
                        f"[dim]   • Server validations: {sum([settings.server_region_validation, settings.server_resource_group_validation, settings.server_vnet_subnet_validation, settings.server_vm_sku_validation, settings.server_disk_type_validation, settings.server_discovery_validation, settings.server_rbac_validation])}/7 enabled[/dim]")
                    console.print(
                        f"[dim]   • Parallel execution: {'enabled' if settings.parallel_execution else 'disabled'}[/dim]")
                    console.print(
                        f"[dim]   • Fail fast: {'enabled' if settings.fail_fast else 'disabled'}[/dim]")

                    # Option to modify validation settings
                    modify_settings = Confirm.ask(
                        "Do you want to modify validation settings for this session?", default=False)
                    if modify_settings:
                        self._prompt_validation_settings_editor()
                        # Recreate ValidationConfig with updated settings
                        global_validation_config = ValidationConfig(
                            config_data=self.current_project.validation_settings.to_dict()
                        )
                    console.print()  # Add spacing

        # Initialize Azure components with project authentication
        if not self.credential:
            if self._credential:
                self._initialize_azure_components(self._credential)
            else:
                # Initialize credential based on project auth config with cached token support
                from ..utils.auth import CachedCredentialFactory, get_current_tenant_id
                credential = CachedCredentialFactory.create_credential(
                    self.current_project.auth_config,
                    self.project_manager,
                    self.current_project
                )
                self._initialize_azure_components(credential)

                # If tenant_id wasn't saved in project config, capture it now
                if not self.current_project.auth_config.tenant_id:
                    detected_tenant_id = get_current_tenant_id(credential)
                    if detected_tenant_id:
                        console.print(
                            "[green]✓[/green] Saving tenant ID to project configuration...")
                        self.project_manager.update_project_tenant_id(
                            self.current_project, detected_tenant_id)

        # Update project status
        self.project_manager.update_project_status(
            self.current_project, ProjectStatus.IN_PROGRESS)

        # Step 2: Ask for validation intention first
        console.print(
            f"\n[bold cyan]Step 2: Validation Type Selection[/bold cyan]")
        console.print("What type of validation do you want to perform?")
        console.print("  [bold]1[/bold] Landing Zone Validation Only")
        console.print("  [bold]2[/bold] Server Migration Validation Only")

        validation_choice = Prompt.ask("Select validation type [1/2]",
                                       choices=["1", "2"], default="2")

        validation_types = {
            "1": "Landing Zone Only",
            "2": "Server Migration Only"
        }
        console.print(
            f"[green]✓[/green] Selected: {validation_types[validation_choice]}\n")

        # Step 3: Upload and validate configuration file based on validation type
        if validation_choice == "1":
            # Landing Zone Only - ask for LZ file
            console.print(
                "[bold cyan]Step 3: Upload Landing Zone Configuration[/bold cyan]")
            console.print(
                "Please provide a Landing Zone configuration file (CSV/JSON with migrate project details)")

        elif validation_choice == "2":
            # Server Migration Only - ask for server file
            console.print(
                "[bold cyan]Step 3: Upload Server Configuration[/bold cyan]")
            console.print(
                "Please provide a Server configuration file with machine details:")
            console.print(
                "Required columns: Target Machine, Target Region, Target Subscription, Target RG, Target VNet, Target Subnet, Target Machine SKU, Target Disk Type, Migrate Project Name")

        # Route to appropriate upload method based on validation choice
        if validation_choice == "1":
            # Landing Zone Only - use LZ upload method
            if not excel_path:
                # Look for LZ files in project landing_zone directory first
                landing_zone_folder = Path(
                    self.current_project.project_path) / "landing_zone"
                lz_files = list(landing_zone_folder.glob("*.csv")) + \
                    list(landing_zone_folder.glob("*.json"))

                if lz_files:
                    console.print(
                        f"\n[cyan]Found landing zone files in project:[/cyan]")
                    for i, file_path in enumerate(lz_files, 1):
                        console.print(f"  {i}. {file_path.name}")

                    if Confirm.ask("Use existing landing zone file from project?", default=True):
                        choice = Prompt.ask(f"Select file [1-{len(lz_files)}]",
                                            choices=[str(i) for i in range(
                                                1, len(lz_files) + 1)],
                                            default="1")
                        excel_path = str(lz_files[int(choice) - 1])

            success, configs, excel_validations, actual_file_path = self.upload_and_validate_landing_zone_file(
                excel_path)

        else:
            # Server Migration - use server upload method with intelligent lookup
            if not excel_path:
                # Look for server files in project directory first
                server_files = list(self.current_project.servers_folder.glob("*.xlsx")) + \
                    list(self.current_project.servers_folder.glob("*.csv")) + \
                    list(self.current_project.servers_folder.glob("*.json"))

                if server_files:
                    console.print(
                        f"\n[cyan]Found server files in project:[/cyan]")
                    for i, file_path in enumerate(server_files, 1):
                        console.print(f"  {i}. {file_path.name}")

                    if Confirm.ask("Use existing server file from project?", default=True):
                        choice = Prompt.ask(f"Select file [1-{len(server_files)}]",
                                            choices=[str(i) for i in range(
                                                1, len(server_files) + 1)],
                                            default="1")
                        excel_path = str(server_files[int(choice) - 1])

            success, configs, excel_validations, actual_file_path = self.upload_and_validate_servers_file(
                excel_path)

        if not success or not configs:
            return

        # Use the actual file path for Azure config extraction
        excel_path = actual_file_path

        # Check if this is Landing Zone validation - if so, handle it separately
        if validation_choice == "1" and configs and hasattr(configs[0], 'migrate_project_name'):
            # This is Landing Zone validation with MigrateProjectConfig objects
            console.print(
                "\n[cyan]Landing Zone validation detected - running LZ-specific workflow...[/cyan]")
            self.run_landing_zone_validation_workflow(
                configs, validation_choice, excel_path)
            return

        # For Server Migration validation - use intelligent lookup from project settings
        console.print(
            "\n[cyan]🔍 Using intelligent project lookup for server validation...[/cyan]")

        # Track server file in project
        self.project_manager.add_validation_file(
            self.current_project,
            Path(excel_path).name,
            "server"
        )

        # The server validation will use project settings to automatically find:
        # - Matching migrate projects based on server file data
        # - Cache storage accounts for each subscription/region combination
        # - Discovery status and machine health from Azure Migrate
        console.print(
            "[green]✓[/green] Server file loaded - validation will use project configuration")

        # For server validation, we'll skip individual project/cache selection
        # The validation will intelligently find matching configurations from project settings
        console.print(
            "\n[cyan]Server validation will automatically match configurations from project settings[/cyan]")
        # Step 4: Run intelligent server validations using project settings
        console.print("\n[cyan]Step 4: Intelligent Server Validation[/cyan]")

        reports = []
        replication_results = []

        try:
            # Initialize intelligent validator if we have credentials
            if self.credential:
                from ..config.validation_config import get_validation_config
                intelligent_validator = IntelligentServersValidatorWrapper(
                    self.credential, get_validation_config())

                # Load landing zone project data from saved project configurations
                landing_zone_projects = []

                console.print(
                    "[cyan]🔍 Loading landing zone project configurations from project data...[/cyan]")

                # Get validated LZ configurations from project manager
                if self.project_manager.has_validated_lz_configs(self.current_project):
                    lz_configs = self.project_manager.get_validated_lz_configs(
                        self.current_project)

                    if lz_configs and "migrate_projects" in lz_configs:
                        from ..core.models import MigrateProjectConfig

                        for mp_data in lz_configs["migrate_projects"]:
                            # Convert saved data to MigrateProjectConfig objects
                            try:
                                project_config = MigrateProjectConfig(
                                    subscription_id=mp_data.get(
                                        'Subscription ID', ''),
                                    migrate_project_name=mp_data.get(
                                        'Migrate Project Name', ''),
                                    appliance_type=mp_data.get(
                                        'Appliance Type', 'VMware'),
                                    appliance_name=mp_data.get(
                                        'Appliance Name', ''),
                                    region=mp_data.get('Region', ''),
                                    cache_storage_account=mp_data.get(
                                        'Cache Storage Account', ''),
                                    migrate_project_subscription=mp_data.get(
                                        'Migrate Project Subscription', ''),
                                    migrate_resource_group=mp_data.get(
                                        'Migrate Resource Group', ''),
                                    cache_storage_resource_group=mp_data.get(
                                        'Cache Storage Resource Group', ''),
                                    recovery_vault_name=mp_data.get(
                                        'Recovery Vault Name')
                                )
                                landing_zone_projects.append(project_config)
                            except Exception as e:
                                console.print(
                                    f"[yellow]⚠ Warning: Could not load project config for {mp_data.get('Migrate Project Name', 'unknown')}: {str(e)}[/yellow]")

                    console.print(
                        f"[green]✓ Loaded {len(landing_zone_projects)} landing zone project configurations from project data[/green]")
                else:
                    console.print(
                        "[yellow]⚠ No validated landing zone configurations found in project[/yellow]")
                    console.print(
                        "[yellow]  Please run Landing Zone validation first to populate project data[/yellow]")

                    # Fallback: try to extract from server configs (limited data)
                    console.print(
                        "[cyan]🔄 Attempting fallback: extracting project names from server data...[/cyan]")
                    unique_project_names = set()
                    for config in configs:
                        if hasattr(config, 'migrate_project_name'):
                            unique_project_names.add(
                                config.migrate_project_name)

                    console.print(
                        f"[yellow]⚠ Found {len(unique_project_names)} unique project names in server data but missing detailed project configurations[/yellow]")
                    for name in unique_project_names:
                        console.print(f"  • {name}")
                    console.print(
                        "[yellow]  Limited validation will be performed without full project details[/yellow]")

                # Load landing zone data into intelligent validator
                intelligent_validator.load_landing_zone_data(
                    landing_zone_projects)

                # Extract server configurations
                server_configs = []
                for config in configs:
                    if hasattr(config, 'to_migration_config'):
                        # ConsolidatedMigrationConfig objects (from Excel)
                        server_config = config.to_migration_config()
                        server_configs.append(server_config)
                    elif hasattr(config, 'machine_name') and hasattr(config, 'migrate_project_name'):
                        # Already MigrationConfig objects (from CSV)
                        server_configs.append(config)
                    else:
                        console.print(
                            f"[yellow]⚠ Warning: Unknown config type for {config}, skipping[/yellow]")

                console.print(
                    f"[cyan]📋 Extracted {len(server_configs)} server configurations from {len(configs)} input configs[/cyan]")

                console.print(
                    f"[cyan]🧠 Running intelligent validation for {len(server_configs)} servers...[/cyan]")

                # Run intelligent validation
                report = intelligent_validator.intelligent_validate_all_servers(
                    server_configs)

                console.print(
                    f"\n[green]✅ Intelligent validation completed for {report.total_servers} machines[/green]")

            else:
                console.print(
                    "[yellow]⚠ No validator available - skipping intelligent validation[/yellow]")

        except Exception as e:
            console.print(
                f"[red]❌ Error during intelligent validation: {str(e)}[/red]")
            # Fall back to basic validation results
            reports = []

        # Export results if requested
        if export_json and replication_results:
            import json
            with open(export_json, 'w') as f:
                json.dump(replication_results, f, indent=2)
            console.print(
                f"[blue]Results exported to: {export_json}[/blue]")

        console.print(
            "\n[bold green]Migration wizard completed![/bold green]\n")

    def _parse_csv_json_servers(self, file_path: str, file_type: str) -> tuple[bool, list, list]:
        """Parse CSV/JSON server configuration files into MigrationConfig objects"""
        import csv
        import json

        configs = []
        validation_results = []

        try:
            if file_type == "csv":
                # Parse CSV file
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                    if not rows:
                        validation_results.append(
                            ValidationResult(
                                stage=ValidationStage.EXCEL_STRUCTURE,
                                passed=True,
                                message="CSV file is empty"
                            )
                        )
                        return True, configs, validation_results

                    # Parse each row into MigrationConfig
                    for i, row in enumerate(rows, 1):
                        try:
                            # Map CSV columns to MigrationConfig fields
                            # Use Target Machine as the single machine name (same for source and target)
                            config = MigrationConfig(
                                machine_name=row.get(
                                    'Target Machine', '').strip(),
                                target_subscription=row.get(
                                    'Target Subscription', '').strip(),
                                target_rg=row.get('Target RG', '').strip(),
                                target_region=row.get(
                                    'Target Region', '').strip(),
                                target_vnet=row.get('Target VNet', '').strip(),
                                target_subnet=row.get(
                                    'Target Subnet', '').strip(),
                                target_machine_sku=row.get(
                                    'Target Machine SKU', '').strip(),
                                target_disk_type=row.get(
                                    'Target Disk Type', '').strip(),
                                migrate_project_name=row.get(
                                    'Migrate Project Name', '').strip()
                            )

                            # Validate required fields
                            if not config.machine_name:
                                validation_results.append(
                                    ValidationResult(
                                        stage=ValidationStage.EXCEL_STRUCTURE,
                                        passed=False,
                                        message=f"Row {i}: Missing Target Machine"
                                    )
                                )
                                continue

                            configs.append(config)

                        except Exception as e:
                            validation_results.append(
                                ValidationResult(
                                    stage=ValidationStage.EXCEL_STRUCTURE,
                                    passed=False,
                                    message=f"Row {i}: Error parsing server config - {str(e)}"
                                )
                            )

            elif file_type == "json":
                # Parse JSON file
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle both single config and array of configs
                server_configs = data if isinstance(data, list) else [data]

                for i, server_data in enumerate(server_configs, 1):
                    try:
                        config = MigrationConfig(
                            machine_name=server_data.get(
                                'machine_name', '').strip(),
                            target_subscription=server_data.get(
                                'target_subscription', '').strip(),
                            target_rg=server_data.get('target_rg', '').strip(),
                            target_region=server_data.get(
                                'target_region', '').strip(),
                            target_vnet=server_data.get(
                                'target_vnet', '').strip(),
                            target_subnet=server_data.get(
                                'target_subnet', '').strip(),
                            target_machine_sku=server_data.get(
                                'target_machine_sku', '').strip(),
                            target_disk_type=server_data.get(
                                'target_disk_type', '').strip(),
                            migrate_project_name=server_data.get(
                                'migrate_project_name', '').strip()
                        )

                        # Validate required fields
                        if not config.machine_name:
                            validation_results.append(
                                ValidationResult(
                                    stage=ValidationStage.EXCEL_STRUCTURE,
                                    passed=False,
                                    message=f"Config {i}: Missing machine_name"
                                )
                            )
                            continue

                        configs.append(config)

                    except Exception as e:
                        validation_results.append(
                            ValidationResult(
                                stage=ValidationStage.EXCEL_STRUCTURE,
                                passed=False,
                                message=f"Config {i}: Error parsing server config - {str(e)}"
                            )
                        )

            # Add success validation if we have configs
            if configs:
                validation_results.append(
                    ValidationResult(
                        stage=ValidationStage.EXCEL_STRUCTURE,
                        passed=True,
                        message=f"Successfully parsed {len(configs)} server configuration(s) from {file_type.upper()} file"
                    )
                )

            return True, configs, validation_results

        except Exception as e:
            validation_results.append(
                ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Error parsing {file_type.upper()} file: {str(e)}"
                )
            )
            return False, [], validation_results

    def _prompt_validation_settings_editor(self):
        """Interactive editor for validation settings"""
        from ..management.project_manager import ValidationSettings

        if not self.current_project:
            console.print("[red]Error: No current project available for settings editor[/red]")
            return
            
        settings = self.current_project.validation_settings
        console.print("\n[bold cyan]🔧 Validation Settings Editor[/bold cyan]")
        console.print(
            "[dim]Configure which validations to run for this project[/dim]\n")

        while True:
            # Display current settings in categories
            console.print("[bold yellow]Current Settings:[/bold yellow]")

            # Global Settings
            console.print("[bold]Global Settings:[/bold]")
            console.print(
                f"  1. Fail Fast: {self._format_setting(settings.fail_fast)}")
            console.print(
                f"  2. Parallel Execution: {self._format_setting(settings.parallel_execution)}")
            console.print(
                f"  3. Timeout (seconds): [cyan]{settings.timeout_seconds}[/cyan]")

            # Landing Zone Settings
            console.print("\n[bold]Landing Zone Validations:[/bold]")
            console.print(
                f"  4. Access Validation: {self._format_setting(settings.lz_access_validation)}")
            console.print(
                f"  5. Migrate Project RBAC: {self._format_setting(settings.lz_migrate_project_rbac)}")
            console.print(
                f"  6. Recovery Vault RBAC: {self._format_setting(settings.lz_recovery_vault_rbac)}")
            console.print(
                f"  7. Subscription RBAC: {self._format_setting(settings.lz_subscription_rbac)}")
            console.print(
                f"  8. Appliance Health: {self._format_setting(settings.lz_appliance_health)}")
            console.print(
                f"  9. Storage Cache: {self._format_setting(settings.lz_storage_cache)}")
            console.print(
                f" 10. Quota Validation: {self._format_setting(settings.lz_quota_validation)}")
            console.print(
                f" 11. Auto-create Storage: {self._format_setting(settings.lz_auto_create_storage)}")

            # Server Settings
            console.print("\n[bold]Server Validations:[/bold]")
            console.print(
                f" 12. Region Validation: {self._format_setting(settings.server_region_validation)}")
            console.print(
                f" 13. Resource Group Validation: {self._format_setting(settings.server_resource_group_validation)}")
            console.print(
                f" 14. VNet/Subnet Validation: {self._format_setting(settings.server_vnet_subnet_validation)}")
            console.print(
                f" 15. VM SKU Validation: {self._format_setting(settings.server_vm_sku_validation)}")
            console.print(
                f" 16. Disk Type Validation: {self._format_setting(settings.server_disk_type_validation)}")
            console.print(
                f" 17. Discovery Validation: {self._format_setting(settings.server_discovery_validation)}")
            console.print(
                f" 18. Server RBAC Validation: {self._format_setting(settings.server_rbac_validation)}")

            console.print("\n[bold]Preset Profiles:[/bold]")
            console.print(" 19. Apply Default Profile (balanced)")
            console.print(" 20. Apply Quick Profile (minimal checks)")
            console.print(" 21. Apply Full Profile (all checks)")

            console.print("\n[bold]Actions:[/bold]")
            console.print(" s. Save changes to project")
            console.print(" q. Quit without saving")

            choice = Prompt.ask(
                "Select option to modify [1-21/s/q]", default="q")

            if choice == "q":
                console.print(
                    "[yellow]Exiting without saving changes[/yellow]")
                break
            elif choice == "s":
                # current_project is guaranteed to be non-None due to check at method start
                assert self.current_project is not None
                self.project_manager.update_validation_settings(
                    self.current_project, settings)
                console.print(
                    "[green]✓ Validation settings saved to project![/green]")
                break
            elif choice == "1":
                settings.fail_fast = not settings.fail_fast
            elif choice == "2":
                settings.parallel_execution = not settings.parallel_execution
            elif choice == "3":
                new_timeout = Prompt.ask(
                    "Enter timeout in seconds", default=str(settings.timeout_seconds))
                try:
                    settings.timeout_seconds = int(new_timeout)
                except ValueError:
                    console.print(
                        "[red]Invalid number, keeping current value[/red]")
            elif choice == "4":
                settings.lz_access_validation = not settings.lz_access_validation
            elif choice == "5":
                settings.lz_migrate_project_rbac = not settings.lz_migrate_project_rbac
            elif choice == "6":
                settings.lz_recovery_vault_rbac = not settings.lz_recovery_vault_rbac
            elif choice == "7":
                settings.lz_subscription_rbac = not settings.lz_subscription_rbac
            elif choice == "8":
                settings.lz_appliance_health = not settings.lz_appliance_health
            elif choice == "9":
                settings.lz_storage_cache = not settings.lz_storage_cache
            elif choice == "10":
                settings.lz_quota_validation = not settings.lz_quota_validation
            elif choice == "11":
                settings.lz_auto_create_storage = not settings.lz_auto_create_storage
            elif choice == "12":
                settings.server_region_validation = not settings.server_region_validation
            elif choice == "13":
                settings.server_resource_group_validation = not settings.server_resource_group_validation
            elif choice == "14":
                settings.server_vnet_subnet_validation = not settings.server_vnet_subnet_validation
            elif choice == "15":
                settings.server_vm_sku_validation = not settings.server_vm_sku_validation
            elif choice == "16":
                settings.server_disk_type_validation = not settings.server_disk_type_validation
            elif choice == "17":
                settings.server_discovery_validation = not settings.server_discovery_validation
            elif choice == "18":
                settings.server_rbac_validation = not settings.server_rbac_validation
            elif choice == "19":
                self.current_project.validation_settings = ValidationSettings.create_default()
                settings = self.current_project.validation_settings
                console.print("[green]✓ Applied default profile[/green]")
            elif choice == "20":
                self.current_project.validation_settings = ValidationSettings.create_quick_profile()
                settings = self.current_project.validation_settings
                console.print("[green]✓ Applied quick profile[/green]")
            elif choice == "21":
                self.current_project.validation_settings = ValidationSettings.create_full_profile()
                settings = self.current_project.validation_settings
                console.print("[green]✓ Applied full profile[/green]")
            else:
                console.print("[red]Invalid option, please try again[/red]")

            console.print()  # Add spacing

    def _format_setting(self, value: bool) -> str:
        """Format boolean setting for display"""
        return "[green]✓ enabled[/green]" if value else "[red]✗ disabled[/red]"
