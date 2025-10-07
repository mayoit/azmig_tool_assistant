"""
Mock mode - Azure Bulk Migration simulation (offline testing)
"""
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..wizard import MigrationWizard
from ..config.validation_config import get_validation_config, reset_validation_config
from ..config.parsers import ConfigParser
from ..mock.landing_zone_validator import MockLandingZoneValidator
from ..models import MigrateProjectConfig, ValidationStatus

console = Console()


def run_mock_mode(
    excel_path: Optional[str] = None,
    export_json: Optional[str] = None,
    validation_config_path: Optional[str] = None,
    validation_profile: Optional[str] = None,
    operation: Optional[str] = None,
    lz_file: Optional[str] = None
):
    """
    Run migration wizard in mock mode for offline testing

    Args:
        excel_path: Path to Excel file with migration configurations
        export_json: Path to export results to JSON
        validation_config_path: Path to validation configuration file
        validation_profile: Name of validation profile to use
        operation: Operation type (lz_validation, server_validation, replication, full_wizard)
        lz_file: Path to Landing Zone CSV/JSON file
    """
    console.rule("[bold yellow]Mock Mode - Offline Simulation[/bold yellow]")

    # Load validation configuration
    if validation_config_path or validation_profile:
        reset_validation_config()  # Clear cached config
        config = get_validation_config(validation_config_path)

        # Apply profile if specified
        if validation_profile and validation_profile != "default":
            config._apply_profile(validation_profile)
            console.print(
                f"[cyan]Using validation profile:[/cyan] {validation_profile}\n")

    # Run wizard based on operation type
    wizard = MigrationWizard(live_mode=False)

    # Handle different operation types
    if operation == 'lz_validation':
        console.print(
            "\n[bold]Running Landing Zone Validation Only (Mock)[/bold]\n")
        if lz_file:
            run_landing_zone_validation(
                lz_file, validation_config_path, export_json)
        else:
            console.print(
                "[red]Error:[/red] Landing Zone file required for LZ validation")
            console.print(
                "Use --lz-file to specify CSV/JSON file or run interactive mode")
    elif operation == 'server_validation':
        console.print("\n[bold]Running Server Validation Only (Mock)[/bold]\n")
        # TODO: Implement server-only validation
        wizard.run(excel_path=excel_path, export_json=export_json)
    elif operation == 'replication':
        console.print("\n[bold]Simulating Replication (Mock)[/bold]\n")
        wizard.run(excel_path=excel_path, export_json=export_json)
    else:
        # Default: full wizard
        wizard.run(excel_path=excel_path, export_json=export_json)


def run_landing_zone_validation(
    lz_file: str,
    validation_config_path: Optional[str] = None,
    export_json: Optional[str] = None
):
    """
    Run Landing Zone validation only (no full migration wizard)

    Args:
        lz_file: Path to Landing Zone CSV/JSON file
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
    validator = MockLandingZoneValidator(
        success_rate=0.85, validation_config=validation_config)

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
    console.rule("[bold]Validation Summary[/bold]")

    total = len(results)
    passed = sum(
        1 for _, result in results if result.overall_status == ValidationStatus.OK)
    failed = total - passed

    summary_table = Table(show_header=True)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", justify="right")

    summary_table.add_row("Total Landing Zones", str(total))
    summary_table.add_row("[green]Passed[/green]", str(passed))
    if failed > 0:
        summary_table.add_row("[red]Failed[/red]", str(failed))

    console.print(summary_table)
    console.print()

    if failed == 0:
        console.print(
            "[green]✓ All Landing Zones passed validation![/green]\n")
    else:
        console.print(
            f"[red]✗ {failed} Landing Zone(s) failed validation[/red]\n")


def _export_lz_results(results: List[tuple], export_path: str):
    """Export Landing Zone validation results to JSON"""
    import json
    from datetime import datetime

    output = {
        "operation": "lz_validation",
        "timestamp": datetime.now().isoformat(),
        "mode": "mock",
        "total_landing_zones": len(results),
        "results": []
    }

    for lz, result in results:
        lz_result = {
            "landing_zone": lz.migrate_project_name,
            "region": lz.region,
            "appliance_name": lz.appliance_name,
            "virtualization_type": lz.virtualization_type,
            "status": result.overall_status.value,
            "validations": {
                "access": result.access_validation.status.value if result.access_validation else "skipped",
                "appliance_health": result.appliance_health.status.value if result.appliance_health else "skipped",
                "storage_cache": result.storage_cache.status.value if result.storage_cache else "skipped",
                "quota": result.quota_validation.status.value if result.quota_validation else "skipped"
            }
        }
        output["results"].append(lz_result)

    output["summary"] = {
        "passed": sum(1 for _, r in results if r.overall_status == ValidationStatus.OK),
        "failed": sum(1 for _, r in results if r.overall_status != ValidationStatus.OK)
    }

    with open(export_path, 'w') as f:
        json.dump(output, f, indent=2)

    console.print(f"[green]✓[/green] Results exported to: {export_path}\n")
