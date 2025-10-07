"""
Test script for Landing Zone (Layer 1) validation system
Demonstrates the complete flow: config loading → validation → enhanced table display
"""
from pathlib import Path
from rich.console import Console

from azmig_tool.config.parsers import ConfigParser
from azmig_tool.mock import MockLandingZoneValidator
from azmig_tool.models import Layer1ValidationReport
from azmig_tool.formatters.table_formatter import EnhancedTableFormatter

console = Console()


def test_layer1_validation_flow():
    """
    Test the complete Layer 1 validation flow:
    1. Load configuration from CSV/JSON
    2. Run validation using Mock validator
    3. Display results using Enhanced Table Formatter
    """
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print(
        "[bold cyan]  Azure Bulk Migration Tool - Layer 1 Validation  [/bold cyan]")
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")

    # Step 1: Load configuration
    console.print("[bold]Step 1:[/bold] Loading project configuration...\n")

    csv_path = Path("tests/data/sample_migrate_projects.csv")
    if not csv_path.exists():
        console.print(
            f"[red]❌ Error:[/red] {csv_path} not found. Run generate_sample_config.py first.")
        return

    parser = ConfigParser(str(csv_path))

    try:
        success, projects, error_msg = parser.parse_layer1()
        if not success:
            console.print(f"[red]❌ Error:[/red] {error_msg}")
            return
        console.print(
            f"[green]✅ Loaded {len(projects)} projects from {csv_path}[/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Error loading config:[/red] {e}")
        return

    # Step 2: Run validation
    console.print(
        "[bold]Step 2:[/bold] Running Layer 1 validation (Mock mode)...\n")

    validator = MockLandingZoneValidator(
        success_rate=0.8)  # 80% success rate for demo
    results = []

    for idx, project in enumerate(projects, start=1):
        console.print(
            f"  [{idx}/{len(projects)}] Validating {project.migrate_project_name}...", end=" ")
        result = validator.validate_project(project)
        results.append(result)

        # Show quick status
        if result.is_ready():
            console.print("[green]✅ Ready[/green]")
        elif result.overall_status.value == "WARNING":
            console.print("[yellow]⚠️ Warnings[/yellow]")
        else:
            console.print("[red]❌ Failed[/red]")

    console.print()

    # Step 3: Create validation report
    console.print("[bold]Step 3:[/bold] Generating validation report...\n")

    report = Layer1ValidationReport()
    for result in results:
        report.add_result(result)

    # Step 4: Display results with enhanced tables
    console.print("[bold]Step 4:[/bold] Displaying results\n")

    # Summary table
    summary_table = EnhancedTableFormatter.format_layer1_summary(report)
    console.print(summary_table)
    console.print()

    # Main results table
    results_table = EnhancedTableFormatter.format_layer1_results(results)
    console.print(results_table)
    console.print()

    # Step 5: Show detailed view for first result
    console.print("[bold]Step 5:[/bold] Detailed view (first project)\n")

    if results:
        EnhancedTableFormatter.display_layer1_details(results[0])

    # Summary
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    summary = report.get_summary()
    console.print(f"[bold]Validation Complete![/bold]")
    console.print(f"  Projects Ready: [green]{report.ready_projects}[/green]")
    console.print(
        f"  With Warnings: [yellow]{report.warning_projects}[/yellow]")
    console.print(f"  Failed: [red]{report.failed_projects}[/red]")
    console.print(f"  Success Rate: [bold]{summary['success_rate']}[/bold]")
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")

    # Next steps
    console.print("[bold]Next Steps:[/bold]")
    if report.ready_projects == report.total_projects:
        console.print(
            "  [green]✅ All projects ready! Proceed to Layer 2 (machine validation)[/green]")
    elif report.failed_projects > 0:
        console.print(
            f"  [red]❌ Fix {report.failed_projects} failed project(s) before proceeding[/red]")
    else:
        console.print(
            f"  [yellow]⚠️ Review {report.warning_projects} warning(s), then proceed with caution[/yellow]")


if __name__ == "__main__":
    test_layer1_validation_flow()
