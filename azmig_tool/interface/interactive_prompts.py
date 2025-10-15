#!/usr/bin/env python3
"""
Interactive prompting system for Azure Bulk Migration Tool.
Provides scenario-based wizards for user-friendly operation.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

from ..management.template_manager import TemplateManager
from ..management.project_manager import ProjectManager, ProjectConfig, ProjectAuthConfig, AuthMethod, ProjectStatus

console = Console()


class InteractivePrompter:
    """Handles all interactive prompts for the migration tool."""

    def __init__(self):
        self.console = Console()
        self.template_manager = TemplateManager(self.console)
        self.project_manager = ProjectManager()

    def prompt_migration_type(self) -> Tuple[str, Optional[ProjectConfig]]:
        """
        Prompt user to select migration type (New vs Patch Existing).
        This is the first prompt when starting the tool.

        Returns:
            Tuple[str, Optional[ProjectConfig]]: Migration type and project config (if existing)
        """
        self.console.print("\n[bold cyan]Step 1: Migration Type[/bold cyan]\n")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Number", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Description", style="dim")

        table.add_row("1", "New Batch Migration",
                      "Start fresh migration batch")
        table.add_row("2", "Patch Existing Migration",
                      "Update existing migration")

        self.console.print(table)

        choice = Prompt.ask(
            "\nSelect migration type [1/2]",
            choices=["1", "2"],
            default="1"
        )

        if choice == "1":
            self.console.print(
                "[green]✓[/green] Selected: New Batch Migration")
            return "new", None
        else:
            self.console.print(
                "[green]✓[/green] Selected: Patch Existing Migration")

            # Show existing projects
            existing_project = self._select_existing_project()
            return "patch", existing_project

    def _select_existing_project(self) -> Optional[ProjectConfig]:
        """Select from existing projects"""
        projects = self.project_manager.list_projects()

        if not projects:
            self.console.print(
                "[yellow]⚠[/yellow] No existing projects found. Creating new project...")
            return None

        self.console.print(
            f"\n[cyan]Found {len(projects)} existing project(s):[/cyan]\n")

        table = Table(show_header=True, box=None)
        table.add_column("ID", style="cyan", width=3)
        table.add_column("Project Name", style="white")
        table.add_column("Status", style="bold")
        table.add_column("Last Updated", style="dim")
        table.add_column("Auth Method", style="dim")

        for i, project in enumerate(projects, 1):
            status_color = {
                ProjectStatus.CREATED: "yellow",
                ProjectStatus.IN_PROGRESS: "blue",
                ProjectStatus.COMPLETED: "green",
                ProjectStatus.FAILED: "red",
                ProjectStatus.ARCHIVED: "dim"
            }.get(project.status, "white")

            # Format last updated time
            try:
                updated_dt = datetime.fromisoformat(project.updated_at)
                updated_str = updated_dt.strftime("%Y-%m-%d %H:%M")
            except:
                updated_str = project.updated_at

            table.add_row(
                str(i),
                project.project_name,
                f"[{status_color}]{project.status.value.title()}[/{status_color}]",
                updated_str,
                project.auth_config.auth_method.value
            )

        self.console.print(table)

        # Add option to create new project
        max_choice = len(projects)
        choices = [str(i) for i in range(1, max_choice + 1)] + ["n"]

        self.console.print(
            f"\n[dim]Enter 'n' to create a new project instead[/dim]")

        choice = Prompt.ask(
            f"Select project [1-{max_choice}/n]",
            choices=choices
        )

        if choice == "n":
            return None

        selected_project = projects[int(choice) - 1]
        self.console.print(
            f"[green]✓[/green] Selected project: {selected_project.project_name}")

        return selected_project

    def prompt_new_project_creation(self, auth_config: ProjectAuthConfig) -> ProjectConfig:
        """Create a new project with authentication configuration"""
        self.console.print(
            f"\n[bold cyan]Creating New Migration Project[/bold cyan]\n")

        # Get project name
        project_name = Prompt.ask(
            "Enter project name",
            default=f"Migration_{datetime.now().strftime('%Y%m%d_%H%M')}"
        )

        # Get optional description
        description = Prompt.ask("Project description (optional)", default="")
        description = description.strip() or None

        # Create project
        project = self.project_manager.create_project(
            project_name=project_name,
            auth_config=auth_config,
            description=description
        )

        self.console.print(
            f"[green]✓[/green] Created project: {project.project_name}")
        self.console.print(
            f"[dim]→ Project folder: {project.project_path}[/dim]")
        self.console.print(f"[dim]→ LZ files: {project.lz_folder}[/dim]")
        self.console.print(
            f"[dim]→ Server files: {project.servers_folder}[/dim]")
        self.console.print(f"[dim]→ Results: {project.results_folder}[/dim]\n")

        return project

    def prompt_authentication_config(self) -> ProjectAuthConfig:
        """
        Prompt user for authentication configuration.

        Returns:
            ProjectAuthConfig: Authentication configuration for the project
        """
        self.console.print(
            f"\n[bold cyan]🔐 Azure Authentication Setup[/bold cyan]\n")

        # Authentication method selection
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Number", style="cyan")
        table.add_column("Method", style="white")
        table.add_column("Description", style="dim")

        auth_methods = [
            ("1", "Azure CLI", "Use existing Azure CLI login (az login)"),
            ("2", "Service Principal", "Use Azure Service Principal credentials"),
            ("3", "Managed Identity", "Use Azure Managed Identity (for Azure VMs)"),
            ("4", "Interactive", "Interactive browser-based authentication"),
            ("5", "Device Code", "Device code flow for restricted environments"),
            ("6", "Default", "Auto-detect best authentication method")
        ]

        for num, name, desc in auth_methods:
            table.add_row(num, name, desc)

        self.console.print(table)

        choice = Prompt.ask(
            "\nSelect authentication method [1-6]",
            choices=["1", "2", "3", "4", "5", "6"],
            default="1"
        )

        auth_method_map = {
            "1": AuthMethod.AZURE_CLI,
            "2": AuthMethod.SERVICE_PRINCIPAL,
            "3": AuthMethod.MANAGED_IDENTITY,
            "4": AuthMethod.INTERACTIVE,
            "5": AuthMethod.DEVICE_CODE,
            "6": AuthMethod.DEFAULT
        }

        auth_method = auth_method_map[choice]
        self.console.print(f"[green]✓[/green] Selected: {auth_method.value}")

        # Collect additional parameters based on method
        tenant_id = None
        client_id = None
        subscription_id = None

        if auth_method == AuthMethod.SERVICE_PRINCIPAL:
            self.console.print(
                f"\n[yellow]Service Principal Configuration:[/yellow]")
            tenant_id = Prompt.ask("Azure Tenant ID")
            client_id = Prompt.ask("Azure Client ID")
            self.console.print(
                "[dim]Note: Client secret will be prompted securely during authentication[/dim]")

        elif auth_method == AuthMethod.MANAGED_IDENTITY:
            self.console.print(
                f"\n[yellow]Managed Identity Configuration:[/yellow]")
            client_id = Prompt.ask(
                "Client ID (optional, for user-assigned MI)", default="")
            client_id = client_id.strip() or None

        # Optional subscription ID for all methods
        if Confirm.ask(f"\nDo you want to specify a default Azure subscription ID?", default=False):
            subscription_id = Prompt.ask("Azure Subscription ID")

        return ProjectAuthConfig(
            auth_method=auth_method,
            tenant_id=tenant_id,
            client_id=client_id,
            subscription_id=subscription_id,
            created_at=datetime.now().isoformat()
        )

    def prompt_operation_type(self) -> str:
        """
        Prompt user to select operation type.

        Returns:
            str: Operation type ('lz_validation', 'server_validation', 'replication', 'configure_validations')
        """
        self.console.print(
            "\n[bold cyan]🎯 What would you like to do?[/bold cyan]\n")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Number", style="cyan")
        table.add_column("Operation", style="white")
        table.add_column("Description", style="dim")

        operations = [
            ("1", "Landing Zone Validation",
             "Validate Azure Migrate project readiness"),
            ("2", "Server Validation", "Validate individual server configurations"),
            ("3", "Enable Replication", "Enable replication for validated servers"),
            ("4", "Configure Validations",
             "Adjust validation settings interactively"),
            ("5", "Full Migration Wizard", "Complete end-to-end migration workflow")
        ]

        for num, name, desc in operations:
            table.add_row(num, name, desc)

        self.console.print(table)
        self.console.print()

        choice = Prompt.ask(
            "[cyan]Select operation[/cyan]",
            choices=["1", "2", "3", "4", "5"],
            default="5"
        )

        operation_map = {
            "1": "lz_validation",
            "2": "server_validation",
            "3": "replication",
            "4": "configure_validations",
            "5": "full_wizard"
        }

        return operation_map[choice]

    def prompt_file_path(self, file_type: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
        """
        Prompt user for file path with validation.

        Args:
            file_type: Type of file (e.g., 'Excel', 'CSV', 'JSON', 'YAML')
            required: Whether the file is required
            default: Default file path

        Returns:
            str: File path or None if not required and skipped
        """
        while True:
            prompt_text = f"[cyan]Path to {file_type} file[/cyan]"

            if default:
                file_path = Prompt.ask(prompt_text, default=default)
            elif not required:
                file_path = Prompt.ask(f"{prompt_text} (press Enter to skip)")
                if not file_path:
                    return None
            else:
                file_path = Prompt.ask(prompt_text)

            # Expand user path
            file_path = os.path.expanduser(file_path)

            # Check if file exists
            if os.path.isfile(file_path):
                self.console.print(f"[green]✓[/green] File found: {file_path}")
                return file_path
            else:
                self.console.print(f"[red]✗[/red] File not found: {file_path}")
                if not required and not Confirm.ask("[yellow]Try again?[/yellow]", default=False):
                    return None

    def prompt_landing_zone_file(self) -> Optional[str]:
        """Prompt for Landing Zone configuration file using template manager."""
        self.console.print("\n[bold]📋 Landing Zone Configuration[/bold]")
        self.console.print(
            "Select a template or provide a custom file with Landing Zone details\n")

        # Show template information
        self.console.print("[dim]Required columns/fields:[/dim]")

        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan")
        table.add_column("Example", style="dim")

        table.add_row("subscription_id", "12345678-1234-...")
        table.add_row("migrate_project_name", "MigrateProject-EastUS")
        table.add_row("appliance_type", "vmware|hyperv|physical")
        table.add_row("appliance_name", "MigrateAppliance-VMware-EastUS")
        table.add_row("region", "eastus")
        table.add_row("cache_storage_account", "cachestorage001")
        table.add_row("cache_storage_resource_group", "rg-storage-eastus")
        table.add_row("migrate_project_subscription", "12345678-1234-...")
        table.add_row("migrate_resource_group", "migrate-rg")

        self.console.print(table)
        self.console.print()

        self.console.print("[dim]Appliance types:[/dim]")
        self.console.print("  [cyan]•[/cyan] vmware  - VMware vSphere")
        self.console.print("  [cyan]•[/cyan] hyperv  - Microsoft Hyper-V")
        self.console.print(
            "  [cyan]•[/cyan] physical - Physical/AWS/GCP/Xen/Other")
        self.console.print()

        # Use template manager for file selection
        return self.template_manager.select_lz_template(allow_new=True)

    def prompt_servers_file(self) -> Optional[str]:
        """Prompt for servers configuration file using template manager."""
        self.console.print("\n[bold]📊 Server Configuration[/bold]")
        self.console.print(
            "Select a server template or provide a custom file with server and Landing Zone details\n")

        # Show template information
        self.console.print("[dim]Server columns required:[/dim]")

        server_table = Table(show_header=True, box=None, padding=(0, 1))
        server_table.add_column("Field", style="cyan")
        server_table.add_column("Example", style="dim")

        server_table.add_row("target_machine", "example-server-01")
        server_table.add_row("target_region", "eastus")
        server_table.add_row("target_subscription", "aaaaaaaa-bbbb-cccc...")
        server_table.add_row("target_rg", "example-target-rg")
        server_table.add_row("target_vnet", "example-vnet")
        server_table.add_row("target_subnet", "example-subnet")
        server_table.add_row("target_machine_sku", "Standard_D4s_v3")
        server_table.add_row("target_disk_type", "StandardSSD_LRS")

        self.console.print(server_table)
        self.console.print()

        self.console.print(
            "[dim]Landing Zone columns (for integrated templates):[/dim]")

        lz_table = Table(show_header=True, box=None, padding=(0, 1))
        lz_table.add_column("Field", style="yellow")
        lz_table.add_column("Example", style="dim")

        lz_table.add_row("migrate_project_subscription", "12345678-1234-...")
        lz_table.add_row("migrate_project_name", "MigrateProject-EastUS")
        lz_table.add_row("appliance_type", "vmware|hyperv|physical")
        lz_table.add_row("appliance_name", "MigrateAppliance-VMware-EastUS")
        lz_table.add_row("cache_storage_account", "cachestorage001")
        lz_table.add_row("cache_storage_resource_group", "rg-storage-eastus")
        lz_table.add_row("migrate_resource_group", "migrate-rg")

        self.console.print(lz_table)
        self.console.print()

        # Use template manager for file selection
        return self.template_manager.select_server_template(allow_new=True)

    def prompt_export_json(self) -> Optional[str]:
        """Prompt for JSON export path."""
        export = Confirm.ask(
            "\n[cyan]Export results to JSON?[/cyan]",
            default=False
        )

        if not export:
            return None

        default_name = "migration_results.json"
        json_path = Prompt.ask(
            "[cyan]JSON export file path[/cyan]",
            default=default_name
        )

        return json_path

    def _get_nested_value(self, config: Dict, path: str, default: Any = True) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = path.split('.')
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def _set_nested_value(self, config: Dict, path: str, value: Any):
        """Set nested dictionary value using dot notation."""
        keys = path.split('.')
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def show_summary(self, operation: str, params: Dict[str, Any]):
        """
        Display operation summary before execution.

        Args:
            operation: Operation type
            params: Operation parameters
        """
        self.console.print("\n" + "="*60)
        self.console.print("[bold cyan]📋 Operation Summary[/bold cyan]")
        self.console.print("="*60 + "\n")

        operation_names = {
            "lz_validation": "Landing Zone Validation",
            "server_validation": "Server Validation",
            "replication": "Enable Replication",
            "configure_validations": "Configure Validations",
            "full_wizard": "Full Migration Wizard"
        }

        self.console.print(
            f"[bold]Operation:[/bold] {operation_names.get(operation, operation)}")

        for key, value in params.items():
            if value is not None:
                self.console.print(
                    f"[bold]{key.replace('_', ' ').title()}:[/bold] {value}")

        self.console.print("\n" + "="*60 + "\n")

        proceed = Confirm.ask(
            "[bold cyan]Proceed with this operation?[/bold cyan]",
            default=True
        )

        return proceed


def get_interactive_inputs(mode: str, provided_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to gather all required inputs interactively.

    Args:
        mode: Azure integration mode (unused parameter for compatibility)
        provided_params: Parameters already provided via CLI

    Returns:
        Dict: Complete parameters for operation
    """
    prompter = InteractivePrompter()
    params = provided_params.copy()

    # Determine operation type
    if 'operation' not in params or params['operation'] is None:
        params['operation'] = prompter.prompt_operation_type()

    operation = params['operation']

    # Handle different operations
    # Validation configuration is no longer supported as separate operation
    # Settings are now managed via project-persistent ValidationSettings
    if operation == 'configure_validations':
        console.print(
            "[yellow]⚠ Configure Validations operation is deprecated.[/yellow]")
        console.print(
            "[dim]Validation settings are now managed per-project via the wizard interface.[/dim]")
        console.print(
            "[dim]Use 'azmig' (wizard mode) to manage project validation settings.[/dim]")
        return params

    # Validation configuration is now project-persistent via ValidationSettings
    # No need to prompt for separate validation config files
    params['validation_config'] = None
    params['validation_profile'] = None

    # Operation-specific prompts
    if operation in ['lz_validation', 'full_wizard']:
        if 'lz_file' not in params or params['lz_file'] is None:
            params['lz_file'] = prompter.prompt_landing_zone_file()

    if operation in ['server_validation', 'replication', 'full_wizard']:
        if 'excel' not in params or params['excel'] is None:
            params['excel'] = prompter.prompt_servers_file()

            # Try to extract Azure configuration from server file
            if params['excel']:
                azure_config = prompter.template_manager.extract_azure_config_from_server_file(
                    params['excel'])
                if azure_config:
                    console.print(
                        f"\n[green]✓[/green] Extracted Azure configuration from server file")
                    console.print(
                        f"[dim]Subscription ID: {azure_config.get('subscription_id', 'Not found')}[/dim]")
                    console.print(
                        f"[dim]Migrate Project: {azure_config.get('migrate_project_name', 'Not found')}[/dim]")
                    params['extracted_azure_config'] = azure_config

    # Export JSON prompt
    if 'export_json' not in params or params['export_json'] is None:
        params['export_json'] = prompter.prompt_export_json()

    # Show summary and confirm
    if not prompter.show_summary(operation, params):
        console.print("[yellow]Operation cancelled by user[/yellow]")
        exit(0)

    return params
