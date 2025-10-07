"""
Live mode - Azure Bulk Migration with Azure API integration
"""
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from ..wizard import MigrationWizard
from ..config.validation_config import get_validation_config, reset_validation_config
from ..auth import get_azure_credential
from ..config.parsers import ConfigParser
from ..live.landing_zone_validator import LiveLandingZoneValidator
from ..models import MigrateProjectConfig, ValidationStatus
import json
from datetime import datetime

console = Console()


def run_live_mode(
    excel_path: Optional[str] = None,
    export_json: Optional[str] = None,
    validation_config_path: Optional[str] = None,
    validation_profile: Optional[str] = None,
    auth_method: Optional[str] = None,
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    operation: Optional[str] = None,
    lz_file: Optional[str] = None
):
    """
    Run migration wizard in live mode with Azure API integration

    Args:
        excel_path: Path to Excel file with migration configurations
        export_json: Path to export results to JSON
        validation_config_path: Path to validation configuration file
        validation_profile: Name of validation profile to use
        auth_method: Authentication method (azure_cli, managed_identity, service_principal, etc.)
        tenant_id: Azure tenant ID (for service principal)
        client_id: Azure client ID (for service principal or managed identity)
        client_secret: Azure client secret (for service principal)
        operation: Operation type (lz_validation, server_validation, replication, full_wizard)
        lz_file: Path to Landing Zone CSV/JSON file
    """
    console.rule("[bold green]Live Mode - Azure Integration[/bold green]")

    # Authenticate to Azure
    console.print("\n[bold cyan]🔐 Azure Authentication[/bold cyan]\n")

    try:
        credential = get_azure_credential(
            auth_method=auth_method,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
    except Exception as e:
        console.print(f"[red]✗ Authentication failed: {e}[/red]")
        console.print(
            "[yellow]Please check your credentials and try again[/yellow]")
        return

    # Load validation configuration (optional)
    config = None
    if validation_config_path:
        try:
            reset_validation_config()  # Clear cached config
            config = get_validation_config(validation_config_path)

            # Apply profile if specified
            if validation_profile and validation_profile != "default":
                config._apply_profile(validation_profile)
                console.print(
                    f"[cyan]Using validation profile:[/cyan] {validation_profile}\n")
        except FileNotFoundError:
            console.print(
                f"[yellow]Warning: Validation config file not found: {validation_config_path}[/yellow]")
            console.print(
                "[yellow]Continuing with default validation settings[/yellow]\n")
    elif validation_profile:
        # User specified a profile but no config file - try to load default config
        try:
            reset_validation_config()
            config = get_validation_config(None)
            config._apply_profile(validation_profile)
            console.print(
                f"[cyan]Using validation profile:[/cyan] {validation_profile}\n")
        except FileNotFoundError:
            console.print(
                "[yellow]Warning: No validation config file found[/yellow]")
            console.print(
                "[yellow]Continuing with default validation settings[/yellow]\n")

    # Run wizard based on operation type
    wizard = MigrationWizard(live_mode=True, credential=credential)

    # Handle different operation types
    if operation == 'lz_validation':
        console.print("\n[bold]Running Landing Zone Validation Only[/bold]\n")
        if lz_file:
            run_landing_zone_validation(
                lz_file, credential, validation_config_path, export_json)
        else:
            console.print(
                "[red]Error:[/red] Landing Zone file is required for this operation")
            console.print(
                "[yellow]Tip:[/yellow] Provide a CSV or JSON file with Landing Zone configurations")
    elif operation == 'server_validation':
        console.print("\n[bold]Running Server Validation Only[/bold]\n")
        # TODO: Implement server-only validation
        wizard.run(excel_path=excel_path, export_json=export_json)
    elif operation == 'replication':
        console.print("\n[bold]Enabling Replication[/bold]\n")
        wizard.run(excel_path=excel_path, export_json=export_json)
    else:
        # Default: full wizard
        wizard.run(excel_path=excel_path, export_json=export_json)


def run_landing_zone_validation(lz_file: str, credential, validation_config_path: Optional[str], export_json: Optional[str]):
    """
    Run Landing Zone-only validation in live mode

    Args:
        lz_file: Path to Landing Zone CSV/JSON file
        credential: Azure credential object
        validation_config_path: Path to validation configuration file
        export_json: Path to export results to JSON
    """
    # Load validation config
    validation_config = get_validation_config(
        validation_config_path) if validation_config_path else None

    # Parse Landing Zone file
    parser = ConfigParser(config_path=lz_file)
    success, landing_zones, error_msg = parser.parse_landing_zone()

    if not success:
        console.print(f"\n[red]Error:[/red] {error_msg}")
        return

    console.print(
        f"\n[cyan]Found {len(landing_zones)} Landing Zone(s) to validate[/cyan]\n")

    # Create validator
    validator = LiveLandingZoneValidator(
        credential=credential, validation_config=validation_config)

    # Validate each Landing Zone
    results = []
    for lz in landing_zones:
        console.print(
            f"[bold]Validating Landing Zone:[/bold] {lz.migrate_project_name}")
        console.print(
            f"  Region: {lz.region} | Appliance: {lz.appliance_name} ({lz.appliance_type})\n")

        result = validator.validate_project(lz)
        results.append((lz, result))

        # Display result
        _display_lz_result(lz, result)

    # Display summary
    _display_lz_summary(results)

    # Export to JSON if requested
    if export_json:
        _export_lz_results(results, export_json)


def _display_lz_result(lz: MigrateProjectConfig, result):
    """Display validation result for a single Landing Zone"""
    status_color = "green" if result.overall_status == ValidationStatus.OK else "red"
    status_symbol = "✓" if result.overall_status == ValidationStatus.OK else "✗"

    console.print(
        f"[{status_color}]{status_symbol} Overall Status:[/{status_color}] {result.overall_status.value}\n")

    # Create results table
    table = Table(title="Validation Results", show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    # Access validation
    if result.access_result:
        status = "✓" if result.access_result.status == ValidationStatus.OK else "✗"
        color = "green" if result.access_result.status == ValidationStatus.OK else "red"
        table.add_row(
            "Access (RBAC)",
            f"[{color}]{status}[/{color}]",
            result.access_result.message
        )

    # Appliance health
    if result.appliance_result:
        status = "✓" if result.appliance_result.status == ValidationStatus.OK else "✗"
        color = "green" if result.appliance_result.status == ValidationStatus.OK else "red"
        details = f"{result.appliance_result.message}"
        table.add_row(
            "Appliance Health",
            f"[{color}]{status}[/{color}]",
            details
        )

    # Storage cache
    if result.storage_result:
        status = "✓" if result.storage_result.status == ValidationStatus.OK else "✗"
        color = "green" if result.storage_result.status == ValidationStatus.OK else "red"
        table.add_row(
            "Storage Cache",
            f"[{color}]{status}[/{color}]",
            result.storage_result.message
        )

    # Quota
    if result.quota_result:
        status = "✓" if result.quota_result.status == ValidationStatus.OK else "✗"
        color = "green" if result.quota_result.status == ValidationStatus.OK else "red"
        table.add_row(
            "Quota",
            f"[{color}]{status}[/{color}]",
            result.quota_result.message
        )

    console.print(table)
    console.print()


def _display_lz_summary(results: List[tuple]):
    """Display summary of all Landing Zone validations"""
    total = len(results)
    passed = sum(
        1 for _, result in results if result.overall_status == ValidationStatus.OK)
    failed = total - passed

    console.print("\n" + "=" * 60)
    console.print("[bold]Validation Summary[/bold]")
    console.print("=" * 60)

    summary_table = Table(show_header=False, box=box.SIMPLE)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", justify="right")

    summary_table.add_row("Total Landing Zones", str(total))
    summary_table.add_row("[green]Passed[/green]", f"[green]{passed}[/green]")
    summary_table.add_row("[red]Failed[/red]", f"[red]{failed}[/red]")

    console.print(summary_table)
    console.print()

    if failed == 0:
        console.print(
            "[green]✓ All Landing Zones passed validation![/green]\n")
    else:
        console.print(
            f"[yellow]⚠ {failed} Landing Zone(s) failed validation[/yellow]\n")


def _export_lz_results(results: List[tuple], export_path: str):
    """Export Landing Zone validation results to JSON"""
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "mode": "live",
        "operation": "landing_zone_validation",
        "total_landing_zones": len(results),
        "results": []
    }

    for lz, result in results:
        lz_data = {
            "migrate_project_name": lz.migrate_project_name,
            "subscription_id": lz.subscription_id,
            "region": lz.region,
            "appliance_name": lz.appliance_name,
            "appliance_type": lz.appliance_type,
            "overall_status": result.overall_status.value,
            "validations": {}
        }

        if result.access_result:
            lz_data["validations"]["access"] = {
                "status": result.access_result.status.value,
                "message": result.access_result.message
            }

        if result.appliance_result:
            lz_data["validations"]["appliance"] = {
                "status": result.appliance_result.status.value,
                "message": result.appliance_result.message
            }

        if result.storage_result:
            lz_data["validations"]["storage"] = {
                "status": result.storage_result.status.value,
                "message": result.storage_result.message
            }

        if result.quota_result:
            lz_data["validations"]["quota"] = {
                "status": result.quota_result.status.value,
                "message": result.quota_result.message
            }

        export_data["results"].append(lz_data)

    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2)

    console.print(f"[green]✓ Results exported to:[/green] {export_path}\n")
