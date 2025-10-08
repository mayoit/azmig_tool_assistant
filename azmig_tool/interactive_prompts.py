#!/usr/bin/env python3
"""
Interactive prompting system for Azure Bulk Migration Tool.
Provides scenario-based wizards for user-friendly operation.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

console = Console()


class InteractivePrompter:
    """Handles all interactive prompts for the migration tool."""

    def __init__(self):
        self.console = Console()

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
        """Prompt for Landing Zone configuration file (CSV or JSON)."""
        self.console.print("\n[bold]📋 Landing Zone Configuration[/bold]")
        self.console.print(
            "Provide a CSV or JSON file with Landing Zone details\n")

        # Show template information
        self.console.print("[dim]Required columns/fields:[/dim]")

        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan")
        table.add_column("Example", style="dim")

        table.add_row("subscription_id", "12345678-1234-...")
        table.add_row("resource_group", "migrate-rg")
        table.add_row("migrate_project_name", "MigrateProject-EastUS")
        table.add_row("recovery_vault_name", "RecoveryVault-EastUS")
        table.add_row("region", "eastus")
        table.add_row("cache_storage_account", "cachestorage001")
        table.add_row("appliance_name", "MigrateAppliance-VMware-EastUS")
        table.add_row("virtualization_type", "vmware|hyperv|physical")

        self.console.print(table)
        self.console.print()

        self.console.print("[dim]Virtualization types:[/dim]")
        self.console.print("  [cyan]•[/cyan] vmware  - VMware vSphere")
        self.console.print("  [cyan]•[/cyan] hyperv  - Microsoft Hyper-V")
        self.console.print(
            "  [cyan]•[/cyan] physical - Physical/AWS/GCP/Xen/Other")
        self.console.print()

        # Show template file locations
        template_csv = "examples/template_landing_zones.csv"
        template_json = "examples/template_landing_zones.json"

        if os.path.isfile(template_csv) or os.path.isfile(template_json):
            self.console.print("[dim]Template files available:[/dim]")
            if os.path.isfile(template_csv):
                self.console.print(f"  [cyan]→[/cyan] {template_csv}")
            if os.path.isfile(template_json):
                self.console.print(f"  [cyan]→[/cyan] {template_json}")
            self.console.print()

        file_type = Prompt.ask(
            "[cyan]File format[/cyan]",
            choices=["csv", "json"],
            default="csv"
        )

        # Check if user wants to use template
        if file_type == "csv" and os.path.isfile(template_csv):
            use_template = Confirm.ask(
                f"[cyan]Use template file: {template_csv}?[/cyan]",
                default=False
            )
            if use_template:
                return template_csv
        elif file_type == "json" and os.path.isfile(template_json):
            use_template = Confirm.ask(
                f"[cyan]Use template file: {template_json}?[/cyan]",
                default=False
            )
            if use_template:
                return template_json

        return self.prompt_file_path(f"Landing Zone {file_type.upper()}")

    def prompt_servers_file(self) -> str:
        """Prompt for servers Excel file."""
        self.console.print("\n[bold]📊 Servers Configuration[/bold]")
        self.console.print(
            "Provide an Excel file with server mapping details\n")

        # Check for common file locations
        common_paths = [
            "servers.xlsx",
            "migration.xlsx",
            "tests/data/sample_migration.xlsx"
        ]

        for path in common_paths:
            if os.path.isfile(path):
                use_default = Confirm.ask(
                    f"[cyan]Use found file: {path}?[/cyan]",
                    default=True
                )
                if use_default:
                    return path

        return self.prompt_file_path("Excel (servers)")  # type: ignore

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

    def prompt_validation_config(self) -> Optional[str]:
        """Prompt for validation configuration file."""
        self.console.print("\n[bold]⚙️ Validation Configuration[/bold]")

        # Check if default config exists
        default_config = "validation_config.yaml"

        if os.path.isfile(default_config):
            use_default = Confirm.ask(
                f"[cyan]Use existing config: {default_config}?[/cyan]",
                default=True
            )
            if use_default:
                return default_config

        # Offer to create default config
        create_config = Confirm.ask(
            "[cyan]Create default validation configuration?[/cyan]",
            default=True
        )

        if create_config:
            from .config.validation_config import ValidationConfigLoader
            try:
                config_path = ValidationConfigLoader.create_default_config()
                self.console.print(f"[green]✓[/green] Created: {config_path}")
                return config_path
            except FileExistsError:
                return default_config

        # Prompt for custom config
        use_custom = Confirm.ask(
            "[cyan]Use custom validation config file?[/cyan]",
            default=False
        )

        if use_custom:
            return self.prompt_file_path("Validation YAML", required=False)

        return None

    def prompt_validation_profile(self) -> Optional[str]:
        """Prompt for validation profile selection."""
        self.console.print("\n[bold]📋 Validation Profile[/bold]\n")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Number", style="cyan")
        table.add_column("Profile", style="white")
        table.add_column("Description", style="dim")

        profiles = [
            ("1", "full", "All validations (production)"),
            ("2", "quick", "Fast validation (development)"),
            ("3", "rbac_only", "Permission checks only"),
            ("4", "resource_only", "Infrastructure checks only"),
            ("5", "default", "Standard validation set")
        ]

        for num, name, desc in profiles:
            table.add_row(num, name, desc)

        self.console.print(table)
        self.console.print()

        use_profile = Confirm.ask(
            "[cyan]Use a validation profile?[/cyan]",
            default=True
        )

        if not use_profile:
            return None

        choice = Prompt.ask(
            "[cyan]Select profile[/cyan]",
            choices=["1", "2", "3", "4", "5"],
            default="1"
        )

        profile_map = {
            "1": "full",
            "2": "quick",
            "3": "rbac_only",
            "4": "resource_only",
            "5": "default"
        }

        selected = profile_map[choice]
        self.console.print(f"[green]✓[/green] Selected profile: {selected}")
        return selected

    def configure_validations_interactive(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Interactive validation configuration editor.

        Args:
            config_path: Path to existing config file

        Returns:
            Dict: Updated validation configuration
        """
        from .config.validation_config import ValidationConfigLoader

        self.console.print(
            "\n[bold cyan]⚙️ Interactive Validation Configuration[/bold cyan]\n")

        # Load existing config or create new
        if config_path and os.path.isfile(config_path):
            loader = ValidationConfigLoader.load(config_path)
            config = loader.config_data
            self.console.print(
                f"[green]✓[/green] Loaded config: {config_path}\n")
        else:
            # Create default config structure
            config = {
                "landing_zone": {
                    "access_validation": {"enabled": True},
                    "appliance_health": {"enabled": True},
                    "storage_cache": {"enabled": True},
                    "quota_validation": {"enabled": True}
                },
                "servers": {
                    "region_validation": {"enabled": True},
                    "resource_group_validation": {"enabled": True},
                    "vnet_subnet_validation": {"enabled": True},
                    "vm_sku_validation": {"enabled": True},
                    "disk_type_validation": {"enabled": True},
                    "discovery_validation": {"enabled": True},
                    "rbac_validation": {"enabled": True}
                },
                "global": {
                    "fail_fast": False,
                    "parallel_execution": False
                },
                "active_profile": "default"
            }
            self.console.print(
                "[yellow]ℹ[/yellow] Using default configuration\n")

        # Landing Zone Validations
        self.console.print("[bold]Landing Zone Validations:[/bold]\n")

        lz_validations = {
            "Access Validation (RBAC)": "landing_zone.access_validation.enabled",
            "Appliance Health": "landing_zone.appliance_health.enabled",
            "Storage Cache": "landing_zone.storage_cache.enabled",
            "Quota Validation": "landing_zone.quota_validation.enabled"
        }

        for name, path in lz_validations.items():
            current = self._get_nested_value(config, path)
            enabled = Confirm.ask(
                f"[cyan]{name}[/cyan] (current: {current})",
                default=current
            )
            self._set_nested_value(config, path, enabled)

        # Servers Validations
        self.console.print("\n[bold]Server Validations:[/bold]\n")

        server_validations = {
            "Region Validation": "servers.region_validation.enabled",
            "Resource Group": "servers.resource_group_validation.enabled",
            "VNet/Subnet": "servers.vnet_subnet_validation.enabled",
            "VM SKU": "servers.vm_sku_validation.enabled",
            "Disk Type": "servers.disk_type_validation.enabled",
            "Discovery Status": "servers.discovery_validation.enabled",
            "RBAC Permissions": "servers.rbac_validation.enabled"
        }

        for name, path in server_validations.items():
            current = self._get_nested_value(config, path)
            enabled = Confirm.ask(
                f"[cyan]{name}[/cyan] (current: {current})",
                default=current
            )
            self._set_nested_value(config, path, enabled)

        # Global Settings
        self.console.print("\n[bold]Global Settings:[/bold]\n")

        fail_fast = Confirm.ask(
            "[cyan]Fail fast (stop on first error)?[/cyan]",
            default=self._get_nested_value(config, "global.fail_fast", False)
        )
        self._set_nested_value(config, "global.fail_fast", fail_fast)

        parallel = Confirm.ask(
            "[cyan]Parallel execution?[/cyan]",
            default=self._get_nested_value(
                config, "global.parallel_execution", False)
        )
        self._set_nested_value(config, "global.parallel_execution", parallel)

        # Save configuration
        save_config = Confirm.ask(
            "\n[cyan]Save configuration to file?[/cyan]",
            default=True
        )

        if save_config:
            save_path = Prompt.ask(
                "[cyan]Save as[/cyan]",
                default=config_path or "validation_config.yaml"
            )

            # Save YAML
            import yaml
            with open(save_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            self.console.print(
                f"[green]✓[/green] Configuration saved: {save_path}\n")

        return config

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
    if operation == 'configure_validations':
        config = prompter.configure_validations_interactive(
            params.get('validation_config'))
        params['validation_config_dict'] = config
        return params

    # Prompt for validation config if not provided
    config_was_prompted = False
    if 'validation_config' not in params or params['validation_config'] is None:
        params['validation_config'] = prompter.prompt_validation_config()
        config_was_prompted = True

    # Prompt for validation profile if not provided
    # Skip profile prompt if user just selected a custom config file
    if 'validation_profile' not in params or params['validation_profile'] is None:
        # Check if user provided a custom config file
        has_custom_config = params.get('validation_config') is not None

        if has_custom_config and config_was_prompted:
            # User just chose a custom config - skip profile and inform them
            console.print(
                "[dim]Using custom validation config without profile overrides[/dim]\n")
            params['validation_profile'] = None
        elif not has_custom_config:
            # No config file - offer validation profile
            params['validation_profile'] = prompter.prompt_validation_profile()
        else:
            # Config was provided via CLI, still offer profile as override option
            params['validation_profile'] = prompter.prompt_validation_profile()

    # Operation-specific prompts
    if operation in ['lz_validation', 'full_wizard']:
        if 'lz_file' not in params or params['lz_file'] is None:
            params['lz_file'] = prompter.prompt_landing_zone_file()

    if operation in ['server_validation', 'replication', 'full_wizard']:
        if 'excel' not in params or params['excel'] is None:
            params['excel'] = prompter.prompt_servers_file()

    # Export JSON prompt
    if 'export_json' not in params or params['export_json'] is None:
        params['export_json'] = prompter.prompt_export_json()

    # Show summary and confirm
    if not prompter.show_summary(operation, params):
        console.print("[yellow]Operation cancelled by user[/yellow]")
        exit(0)

    return params
