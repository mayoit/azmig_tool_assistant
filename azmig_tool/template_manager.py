"""
Template Manager for Azure Migration Tool
Handles template discovery, listing, selection, and saving
"""

import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm


@dataclass
class TemplateInfo:
    """Information about a template file"""
    name: str
    path: str
    file_type: str  # csv, json, yaml
    description: str = ""


class TemplateManager:
    """Manages templates in the data/ folder structure"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.base_path = Path(__file__).parent.parent / "data"
        self.servers_path = self.base_path / "servers"
        self.lz_path = self.base_path / "lz"

        # Ensure directories exist
        self._create_directories()

    def _create_directories(self):
        """Create template directories if they don't exist"""
        for path in [self.servers_path, self.lz_path]:
            path.mkdir(parents=True, exist_ok=True)

    def list_server_templates(self) -> List[TemplateInfo]:
        """List all server templates (CSV/JSON files with server configurations)"""
        templates = []

        for file_path in self.servers_path.glob("*"):
            if file_path.suffix.lower() in ['.csv', '.json']:
                description = self._get_template_description(file_path)
                templates.append(TemplateInfo(
                    name=file_path.stem,
                    path=str(file_path),
                    file_type=file_path.suffix[1:].lower(),
                    description=description
                ))

        return sorted(templates, key=lambda x: x.name)

    def list_lz_templates(self) -> List[TemplateInfo]:
        """List all Landing Zone templates (CSV/JSON files with LZ configurations)"""
        templates = []

        for file_path in self.lz_path.glob("*"):
            if file_path.suffix.lower() in ['.csv', '.json']:
                description = self._get_template_description(file_path)
                templates.append(TemplateInfo(
                    name=file_path.stem,
                    path=str(file_path),
                    file_type=file_path.suffix[1:].lower(),
                    description=description
                ))

        return sorted(templates, key=lambda x: x.name)

    def _get_template_description(self, file_path: Path) -> str:
        """Extract description from template file"""
        try:
            if file_path.suffix.lower() == '.csv':
                # For CSV, use filename as description
                name_parts = file_path.stem.replace('_', ' ').title()
                return f"{name_parts} Template"
            elif file_path.suffix.lower() == '.json':
                # For JSON, try to read a description field
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'description' in data:
                        return data['description']
                    return f"JSON template with {len(data.get('servers', data.get('landing_zones', [])))} entries"
        except Exception:
            pass

        return "Template file"

    def display_templates(self, templates: List[TemplateInfo], title: str) -> None:
        """Display templates in a nice table format"""
        if not templates:
            self.console.print(
                f"[yellow]No {title.lower()} templates found[/yellow]")
            return

        table = Table(title=title)
        table.add_column("ID", style="cyan", width=4)
        table.add_column("Name", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Description", style="dim")

        for i, template in enumerate(templates, 1):
            table.add_row(
                str(i),
                template.name,
                template.file_type.upper(),
                template.description
            )

        self.console.print(table)

    def select_server_template(self, allow_new: bool = True) -> Optional[str]:
        """Interactive server template selection"""
        templates = self.list_server_templates()

        self.console.print("\n[bold blue]📋 Server Templates[/bold blue]")
        self.display_templates(templates, "Available Server Templates")

        if not templates and not allow_new:
            return None

        options = []
        if templates:
            options.extend([f"{i}" for i in range(1, len(templates) + 1)])

        if allow_new:
            options.append("n")
            self.console.print("\n[dim]Options:[/dim]")
            if templates:
                self.console.print(
                    "[dim]1-{} - Select template by ID[/dim]".format(len(templates)))
            self.console.print("[dim]n - Create new template[/dim]")

        if not options:
            return None

        choice = Prompt.ask(
            "Select template",
            choices=options,
            default="1" if templates else "n"
        )

        if choice == "n":
            return self._create_new_server_template()
        else:
            selected_template = templates[int(choice) - 1]
            return selected_template.path

    def select_lz_template(self, allow_new: bool = True) -> Optional[str]:
        """Interactive Landing Zone template selection"""
        templates = self.list_lz_templates()

        self.console.print(
            "\n[bold blue]🏗️ Landing Zone Templates[/bold blue]")
        self.display_templates(templates, "Available Landing Zone Templates")

        if not templates and not allow_new:
            return None

        options = []
        if templates:
            options.extend([f"{i}" for i in range(1, len(templates) + 1)])

        if allow_new:
            options.append("n")
            self.console.print("\n[dim]Options:[/dim]")
            if templates:
                self.console.print(
                    "[dim]1-{} - Select template by ID[/dim]".format(len(templates)))
            self.console.print("[dim]n - Create new template[/dim]")

        if not options:
            return None

        choice = Prompt.ask(
            "Select template",
            choices=options,
            default="1" if templates else "n"
        )

        if choice == "n":
            return self._create_new_lz_template()
        else:
            selected_template = templates[int(choice) - 1]
            return selected_template.path

    def _create_new_server_template(self) -> Optional[str]:
        """Create new server template"""
        self.console.print(
            "\n[bold yellow]Create New Server Template[/bold yellow]")

        name = Prompt.ask("Template name")
        if not name:
            return None

        # Clean the name for filename
        clean_name = name.lower().replace(' ', '_').replace('-', '_')

        format_choice = Prompt.ask(
            "Template format",
            choices=["csv", "json"],
            default="csv"
        )

        template_type = Prompt.ask(
            "Template type",
            choices=["server_only", "server_with_lz"],
            default="server_with_lz"
        )

        file_path = self.servers_path / f"{clean_name}.{format_choice}"

        if format_choice == "csv":
            return self._create_csv_server_template(file_path, template_type)
        else:
            return self._create_json_server_template(file_path, template_type)

    def _create_new_lz_template(self) -> Optional[str]:
        """Create new Landing Zone template"""
        self.console.print(
            "\n[bold yellow]Create New Landing Zone Template[/bold yellow]")

        name = Prompt.ask("Template name")
        if not name:
            return None

        clean_name = name.lower().replace(' ', '_').replace('-', '_')

        format_choice = Prompt.ask(
            "Template format",
            choices=["csv", "json"],
            default="csv"
        )

        file_path = self.lz_path / f"{clean_name}.{format_choice}"

        if format_choice == "csv":
            return self._create_csv_lz_template(file_path)
        else:
            return self._create_json_lz_template(file_path)

    def _create_csv_server_template(self, file_path: Path, template_type: str) -> str:
        """Create CSV server template"""
        if template_type == "server_with_lz":
            # Server + LZ columns
            headers = [
                "Source Machine", "Target Machine", "Target Region", "Target Subscription",
                "Target RG", "Target VNet", "Target Subnet", "Target Machine SKU", "Target Disk Type",
                "Migrate Project Subscription", "Migrate Project Name", "Appliance Type",
                "Appliance Name", "Cache Storage Account", "Cache Storage Resource Group",
                "Migrate Resource Group", "Recovery Vault Name"
            ]
            sample_row = [
                "example-server-01", "example-server-01", "eastus", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "example-target-rg", "example-vnet", "example-subnet", "Standard_D4s_v3", "StandardSSD_LRS",
                "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "example-migrate-project", "vmware",
                "example-appliance-01", "examplecachestorage01", "example-storage-rg",
                "example-migrate-rg", "example-recovery-vault"
            ]
        else:
            # Server only columns
            headers = [
                "Source Machine", "Target Machine", "Target Region", "Target Subscription",
                "Target RG", "Target VNet", "Target Subnet", "Target Machine SKU", "Target Disk Type"
            ]
            sample_row = [
                "example-server-01", "example-server-01", "eastus", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "example-target-rg", "example-vnet", "example-subnet", "Standard_D4s_v3", "StandardSSD_LRS"
            ]

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerow(sample_row)

        self.console.print(
            f"[green]✓[/green] Created server template: {file_path}")
        return str(file_path)

    def _create_json_server_template(self, file_path: Path, template_type: str) -> str:
        """Create JSON server template"""
        if template_type == "server_with_lz":
            # Server + LZ template
            template_data = {
                "description": f"Server template with integrated Landing Zone configuration",
                "servers": [
                    {
                        "source_machine": "example-server-01",
                        "target_machine": "example-server-01",
                        "target_region": "eastus",
                        "target_subscription": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                        "target_rg": "example-target-rg",
                        "target_vnet": "example-vnet",
                        "target_subnet": "example-subnet",
                        "target_machine_sku": "Standard_D4s_v3",
                        "target_disk_type": "StandardSSD_LRS",
                        "migrate_project_subscription": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                        "migrate_project_name": "example-migrate-project",
                        "appliance_type": "vmware",
                        "appliance_name": "example-appliance-01",
                        "cache_storage_account": "examplecachestorage01",
                        "cache_storage_resource_group": "example-storage-rg",
                        "migrate_resource_group": "example-migrate-rg"
                    }
                ]
            }
        else:
            # Server only template
            template_data = {
                "description": "Server-only template",
                "servers": [
                    {
                        "source_machine": "example-server-01",
                        "target_machine": "example-server-01",
                        "target_region": "eastus",
                        "target_subscription": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                        "target_rg": "example-target-rg",
                        "target_vnet": "example-vnet",
                        "target_subnet": "example-subnet",
                        "target_machine_sku": "Standard_D4s_v3",
                        "target_disk_type": "StandardSSD_LRS"
                    }
                ]
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2)

        self.console.print(
            f"[green]✓[/green] Created server template: {file_path}")
        return str(file_path)

    def _create_csv_lz_template(self, file_path: Path) -> str:
        """Create CSV Landing Zone template"""
        headers = [
            "Subscription ID", "Migrate Project Name", "Appliance Type", "Appliance Name",
            "Region", "Cache Storage Account", "Cache Storage Resource Group",
            "Migrate Project Subscription", "Migrate Resource Group", "Recovery Vault Name"
        ]
        sample_row = [
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "example-migrate-project", "vmware",
            "example-appliance-01", "eastus", "examplecachestorage01", "example-storage-rg",
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "example-migrate-rg", "example-recovery-vault"
        ]

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerow(sample_row)

        self.console.print(
            f"[green]✓[/green] Created Landing Zone template: {file_path}")
        return str(file_path)

    def _create_json_lz_template(self, file_path: Path) -> str:
        """Create JSON Landing Zone template"""
        template_data = {
            "description": "Landing Zone configuration template",
            "landing_zones": [
                {
                    "subscription_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "migrate_project_name": "example-migrate-project",
                    "appliance_type": "vmware",
                    "appliance_name": "example-appliance-01",
                    "region": "eastus",
                    "cache_storage_account": "examplecachestorage01",
                    "cache_storage_resource_group": "example-storage-rg",
                    "migrate_project_subscription": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "migrate_resource_group": "example-migrate-rg"
                }
            ]
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2)

        self.console.print(
            f"[green]✓[/green] Created Landing Zone template: {file_path}")
        return str(file_path)

    def extract_azure_config_from_server_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        Extract Azure configuration from server file if it contains LZ data

        Returns dict with keys:
        - subscription_id: Azure subscription ID
        - migrate_project_name: Azure Migrate project name  
        - migrate_project_subscription: Migrate project subscription
        - appliance_name: Appliance name
        - appliance_type: Appliance type
        - Other LZ fields if available
        """
        try:
            file_path_obj = Path(file_path)

            if file_path_obj.suffix.lower() == '.json':
                return self._extract_azure_config_from_json(file_path_obj)
            elif file_path_obj.suffix.lower() == '.csv':
                return self._extract_azure_config_from_csv(file_path_obj)

        except Exception as e:
            self.console.print(
                f"[yellow]Warning: Could not extract Azure config from {file_path}: {e}[/yellow]")

        return None

    def _extract_azure_config_from_json(self, file_path: Path) -> Optional[Dict[str, str]]:
        """Extract Azure config from JSON server file"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Check if this is a server file with LZ data
        servers = data.get('servers', [])
        if not servers:
            return None

        first_server = servers[0]

        # Check if this server entry has LZ fields
        lz_fields = [
            'migrate_project_subscription', 'migrate_project_name',
            'appliance_type', 'appliance_name', 'cache_storage_account',
            'migrate_resource_group'
        ]

        # If any LZ fields are present, extract the config
        if any(field in first_server for field in lz_fields):
            azure_config = {}

            # Map server file fields to Azure config
            azure_config['subscription_id'] = first_server.get('migrate_project_subscription',
                                                               first_server.get('target_subscription'))
            azure_config['migrate_project_name'] = first_server.get(
                'migrate_project_name', '')
            azure_config['migrate_project_subscription'] = first_server.get(
                'migrate_project_subscription', '')
            azure_config['appliance_name'] = first_server.get(
                'appliance_name', '')
            azure_config['appliance_type'] = first_server.get(
                'appliance_type', '')
            azure_config['cache_storage_account'] = first_server.get(
                'cache_storage_account', '')
            azure_config['cache_storage_resource_group'] = first_server.get(
                'cache_storage_resource_group', '')
            azure_config['migrate_resource_group'] = first_server.get(
                'migrate_resource_group', '')
            azure_config['region'] = first_server.get('target_region', '')

            # Remove empty values
            return {k: v for k, v in azure_config.items() if v}

        return None

    def _extract_azure_config_from_csv(self, file_path: Path) -> Optional[Dict[str, str]]:
        """Extract Azure config from CSV server file"""
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return None

        first_row = rows[0]

        # Check if this CSV has LZ columns (case-insensitive matching)
        column_mapping = {col.lower().replace(
            ' ', '_'): col for col in first_row.keys()}

        lz_field_patterns = [
            'migrate_project_subscription', 'migrate_project_name',
            'appliance_type', 'appliance_name', 'cache_storage_account',
            'migrate_resource_group'
        ]

        # Check if any LZ fields are present
        found_lz_fields = False
        for pattern in lz_field_patterns:
            if pattern in column_mapping:
                found_lz_fields = True
                break

        if found_lz_fields:
            azure_config = {}

            # Helper function to get value with various possible column names
            def get_value(patterns: List[str]) -> str:
                for pattern in patterns:
                    if pattern in column_mapping:
                        return first_row.get(column_mapping[pattern], '').strip()
                return ''

            azure_config['subscription_id'] = get_value([
                'migrate_project_subscription', 'target_subscription', 'subscription_id'
            ])
            azure_config['migrate_project_name'] = get_value([
                'migrate_project_name'
            ])
            azure_config['migrate_project_subscription'] = get_value([
                'migrate_project_subscription'
            ])
            azure_config['appliance_name'] = get_value([
                'appliance_name'
            ])
            azure_config['appliance_type'] = get_value([
                'appliance_type'
            ])
            azure_config['cache_storage_account'] = get_value([
                'cache_storage_account'
            ])
            azure_config['cache_storage_resource_group'] = get_value([
                'cache_storage_resource_group'
            ])
            azure_config['migrate_resource_group'] = get_value([
                'migrate_resource_group'
            ])
            azure_config['region'] = get_value([
                'target_region', 'region'
            ])

            # Remove empty values
            return {k: v for k, v in azure_config.items() if v}

        return None
