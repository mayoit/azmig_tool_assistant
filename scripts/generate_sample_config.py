"""
Generate sample Layer 1 configuration files (CSV and JSON)
"""
import csv
import json
from pathlib import Path
from typing import List, Dict


def generate_sample_csv(output_path: Path = Path("tests/data/sample_migrate_projects.csv")):
    """
    Generate sample CSV configuration file with realistic Azure values

    Args:
        output_path: Path where CSV will be saved
    """
    # CSV headers
    headers = [
        "Subscription ID",
        "Migrate Project Name",
        "Appliance Type",
        "Appliance Name",
        "Region",
        "Cache Storage Account",
        "Migrate Project Subscription",
        "Migrate Resource Group",
        "Recovery Vault Name"
    ]

    # Sample projects covering different scenarios
    rows = [
        [
            "12345678-1234-1234-1234-123456789abc",
            "migration-project-prod",
            "VMware",
            "VMwareReplicationAppliance01",
            "eastus",
            "migcacheprod001",
            "12345678-1234-1234-1234-123456789abc",
            "rg-migration-prod",
            "vault-migration-prod"
        ],
        [
            "87654321-4321-4321-4321-cba987654321",
            "migration-project-dev",
            "HyperV",
            "HyperVReplicationAppliance01",
            "westus2",
            "migcachedev001",
            "87654321-4321-4321-4321-cba987654321",
            "rg-migration-dev",
            ""  # Optional - can be empty
        ],
        [
            "11111111-2222-3333-4444-555555555555",
            "migration-project-test",
            "VMware",
            "VMwareReplicationAppliance02",
            "centralus",
            "migcachetest001",
            "11111111-2222-3333-4444-555555555555",
            "rg-migration-test",
            "vault-migration-test"
        ]
    ]

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return output_path


def generate_sample_json(output_path: Path = Path("tests/data/sample_migrate_projects.json")):
    """
    Generate sample JSON configuration file with realistic Azure values

    Args:
        output_path: Path where JSON will be saved
    """
    # Sample projects with additional metadata in JSON format
    config = {
        "version": "1.0",
        "description": "Sample Azure Migrate project configuration for bulk migration",
        "created_by": "Azure Bulk Migration Tool v2.1.0",
        "projects": [
            {
                "subscription_id": "12345678-1234-1234-1234-123456789abc",
                "migrate_project_name": "migration-project-prod",
                "appliance_type": "VMware",
                "appliance_name": "VMwareReplicationAppliance01",
                "region": "eastus",
                "cache_storage_account": "migcacheprod001",
                "migrate_project_subscription": "12345678-1234-1234-1234-123456789abc",
                "migrate_resource_group": "rg-migration-prod",
                "recovery_vault_name": "vault-migration-prod",
                "notes": "Production environment - critical workloads"
            },
            {
                "subscription_id": "87654321-4321-4321-4321-cba987654321",
                "migrate_project_name": "migration-project-dev",
                "appliance_type": "HyperV",
                "appliance_name": "HyperVReplicationAppliance01",
                "region": "westus2",
                "cache_storage_account": "migcachedev001",
                "migrate_project_subscription": "87654321-4321-4321-4321-cba987654321",
                "migrate_resource_group": "rg-migration-dev",
                "recovery_vault_name": "",
                "notes": "Development environment - non-critical"
            },
            {
                "subscription_id": "11111111-2222-3333-4444-555555555555",
                "migrate_project_name": "migration-project-test",
                "appliance_type": "VMware",
                "appliance_name": "VMwareReplicationAppliance02",
                "region": "centralus",
                "cache_storage_account": "migcachetest001",
                "migrate_project_subscription": "11111111-2222-3333-4444-555555555555",
                "migrate_resource_group": "rg-migration-test",
                "recovery_vault_name": "vault-migration-test",
                "notes": "Testing environment - validation only"
            }
        ]
    }

    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    return output_path


def generate_minimal_template(output_path: Path = Path("examples/template_migrate_projects.csv")):
    """
    Generate minimal CSV template with headers only (for users to fill in)

    Args:
        output_path: Path where CSV will be saved
    """
    # CSV headers
    headers = [
        "Subscription ID",
        "Migrate Project Name",
        "Appliance Type",
        "Appliance Name",
        "Region",
        "Cache Storage Account",
        "Migrate Project Subscription",
        "Migrate Resource Group",
        "Recovery Vault Name"
    ]

    # Single empty row with defaults
    rows = [
        [
            "",  # subscription_id
            "",  # migrate_project_name
            "VMware",  # appliance_type - default
            "",  # appliance_name
            "eastus",  # region - default
            "",  # cache_storage_account
            "",  # migrate_project_subscription
            "",  # migrate_resource_group
            ""   # recovery_vault_name - optional
        ]
    ]

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return output_path


if __name__ == "__main__":
    """Generate sample files when run directly"""
    from rich.console import Console

    console = Console()

    console.print(
        "[bold cyan]Generating sample Layer 1 configuration files...[/bold cyan]\n")

    # Generate CSV
    csv_path = generate_sample_csv()
    console.print(f"[green]✅ Generated:[/green] {csv_path}")

    # Generate JSON
    json_path = generate_sample_json()
    console.print(f"[green]✅ Generated:[/green] {json_path}")

    # Generate template
    template_path = generate_minimal_template()
    console.print(f"[green]✅ Generated:[/green] {template_path}")

    console.print("\n[bold]Sample configurations created successfully![/bold]")
    console.print(
        "\n[dim]Use these files to configure your Azure Migrate projects for Layer 1 validation.[/dim]")
