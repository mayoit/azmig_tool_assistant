"""
Enhanced Table Formatter - Rich tables with box drawing characters for validation results
"""
from rich.console import Console
from rich.table import Table
from rich import box
from typing import List

from ..models import (
    ProjectReadinessResult,
    ValidationStatus,
    LandingZoneValidationReport,
    MachineValidationReport
)

console = Console()


class EnhancedTableFormatter:
    """Format validation results with enhanced tables"""

    # Status symbols
    STATUS_SYMBOLS = {
        ValidationStatus.OK: "✅",
        ValidationStatus.WARNING: "⚠️",
        ValidationStatus.FAILED: "❌",
        ValidationStatus.SKIPPED: "⏭️"
    }

    # Status colors
    STATUS_COLORS = {
        ValidationStatus.OK: "green",
        ValidationStatus.WARNING: "yellow",
        ValidationStatus.FAILED: "red",
        ValidationStatus.SKIPPED: "dim"
    }

    @staticmethod
    def format_landing_zone_results(results: List[ProjectReadinessResult]) -> Table:
        """
        Create table for Landing Zone validation results

        Args:
            results: List of project readiness results

        Returns:
            Rich Table object
        """
        table = Table(
            title="[bold cyan]Landing Zone: Azure Migrate Project Readiness[/bold cyan]",
            box=box.DOUBLE_EDGE,
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Subscription", style="cyan", no_wrap=True)
        table.add_column("Migrate Project", style="cyan")
        table.add_column("Region", style="blue")
        table.add_column("Access", justify="center", width=8)
        table.add_column("Appliances", justify="center", width=12)
        table.add_column("Storage", justify="center", width=10)
        table.add_column("Quota", justify="center", width=8)
        table.add_column("Overall", justify="center", width=10)

        for idx, result in enumerate(results, start=1):
            # Format each validation status
            access_status = EnhancedTableFormatter._format_status(
                result.access_result.status if result.access_result else ValidationStatus.SKIPPED
            )

            appliance_status = EnhancedTableFormatter._format_status(
                result.appliance_result.status if result.appliance_result else ValidationStatus.SKIPPED
            )
            if result.appliance_result and result.appliance_result.unhealthy_count > 0:
                appliance_status += f" ({result.appliance_result.unhealthy_count}⚠️)"

            storage_status = EnhancedTableFormatter._format_status(
                result.storage_result.status if result.storage_result else ValidationStatus.SKIPPED
            )

            quota_status = EnhancedTableFormatter._format_status(
                result.quota_result.status if result.quota_result else ValidationStatus.SKIPPED
            )

            overall_status = EnhancedTableFormatter._format_status(
                result.overall_status)

            # Truncate long subscription IDs
            sub_id = result.config.subscription_id
            if len(sub_id) > 20:
                sub_id = f"{sub_id[:8]}...{sub_id[-4:]}"

            table.add_row(
                str(idx),
                sub_id,
                result.config.migrate_project_name,
                result.config.region,
                access_status,
                appliance_status,
                storage_status,
                quota_status,
                overall_status
            )

        return table

    @staticmethod
    def format_servers_results(results: List[MachineValidationReport]) -> Table:
        """
        Create table for Servers (machine-level) validation results

        Args:
            results: List of machine validation reports

        Returns:
            Rich Table object
        """
        table = Table(
            title="[bold cyan]Servers: Machine-Level Migration Readiness[/bold cyan]",
            box=box.DOUBLE_EDGE,
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Target Machine", style="cyan")
        table.add_column("Target Region", style="blue")
        table.add_column("Target SKU", style="green")
        table.add_column("Target RG", style="yellow")
        table.add_column("Disk Type", style="magenta")
        table.add_column("Validations", justify="center", width=12)
        table.add_column("Status", justify="center", width=20)

        for idx, report in enumerate(results, start=1):
            passed_count = sum(1 for v in report.validations if v.passed)
            failed_count = len(report.validations) - passed_count

            validations_str = f"{passed_count}✅ {failed_count}❌"

            # Determine status symbol and text
            if report.overall_status == "PASSED":
                status = "[green]✅ OK[/green]"
            elif report.overall_status == "WARNING":
                status = "[yellow]⚠️ Warning[/yellow]"
            else:
                # Get first failure reason
                failed = report.get_failed_validations()
                if failed:
                    reason = failed[0].message.split(':')[-1].strip()[:30]
                    status = f"[red]❌ {reason}[/red]"
                else:
                    status = "[red]❌ Failed[/red]"

            table.add_row(
                str(idx),
                report.config.machine_name,
                report.config.target_region,
                report.config.target_machine_sku,
                report.config.target_rg,
                report.config.target_disk_type,
                validations_str,
                status
            )

        return table

    @staticmethod
    def format_landing_zone_summary(report: LandingZoneValidationReport) -> Table:
        """
        Create summary table for Landing Zone validation

        Args:
            report: Landing Zone validation report

        Returns:
            Rich Table object
        """
        table = Table(
            title="[bold]Landing Zone Validation Summary[/bold]",
            box=box.ROUNDED,
            show_header=False
        )

        table.add_column("Metric", style="bold cyan")
        table.add_column("Count", justify="right", style="bold")

        summary = report.get_summary()

        table.add_row("Total Projects", str(report.total_projects))
        table.add_row("✅ Ready", f"[green]{report.ready_projects}[/green]")
        table.add_row(
            "⚠️ Warnings", f"[yellow]{report.warning_projects}[/yellow]")
        table.add_row("❌ Failed", f"[red]{report.failed_projects}[/red]")
        table.add_row("Success Rate",
                      f"[bold]{summary['success_rate']}[/bold]")

        return table

    @staticmethod
    def _format_status(status: ValidationStatus) -> str:
        """Format status with symbol and color"""
        symbol = EnhancedTableFormatter.STATUS_SYMBOLS.get(status, "❓")
        color = EnhancedTableFormatter.STATUS_COLORS.get(status, "white")
        status_text = status.value

        return f"[{color}]{symbol} {status_text}[/{color}]"

    @staticmethod
    def display_landing_zone_details(result: ProjectReadinessResult):
        """
        Display detailed Landing Zone validation results for a single project

        Args:
            result: Project readiness result
        """
        console.print(
            f"\n[bold cyan]Project: {result.config.migrate_project_name}[/bold cyan]")
        console.print(f"Subscription: {result.config.subscription_id}")
        console.print(f"Region: {result.config.region}\n")

        # Access validation details
        if result.access_result:
            console.print("[bold]Access & Permissions:[/bold]")
            ar = result.access_result
            console.print(
                f"  Migrate Project: {'✅' if ar.has_contributor_migrate_project else '❌'} {ar.details.get('migrate_project', 'Unknown')}")
            # Recovery vault validation removed - will be auto-discovered from migrate project
            console.print(
                f"  Subscription: {'✅' if ar.has_reader_subscription else '❌'} {ar.details.get('subscription', 'Unknown')}")
            console.print()

        # Appliance health details
        if result.appliance_result:
            console.print("[bold]Appliance Health:[/bold]")
            for appliance in result.appliance_result.appliances:
                symbol = "✅" if appliance.health_status.value == "Healthy" else (
                    "⚠️" if appliance.health_status.value == "Warning" else "❌")
                console.print(
                    f"  {symbol} {appliance.name}: {appliance.health_status.value}")
                if appliance.alerts:
                    for alert in appliance.alerts:
                        console.print(f"      ⚠️ {alert}")
            console.print()

        # Storage cache details
        if result.storage_result and result.storage_result.storage_info:
            console.print("[bold]Storage Cache:[/bold]")
            si = result.storage_result.storage_info
            console.print(f"  Account: {si.account_name}")
            console.print(f"  SKU: {si.sku}")
            console.print(f"  {'✅ Exists' if si.exists else '❌ Not found'}")
            if si.created_by_tool:
                console.print(f"  ⚡ Auto-created by tool")
            console.print()

        # Quota details
        if result.quota_result:
            console.print("[bold]vCPU Quotas:[/bold]")
            for quota in result.quota_result.quotas:
                console.print(
                    f"  {quota.family}: {quota.available}/{quota.total_quota} available")
            if result.quota_result.insufficient_families:
                console.print(
                    f"  [yellow]⚠️ Insufficient: {', '.join(result.quota_result.insufficient_families)}[/yellow]")
            if result.quota_result.recommended_skus:
                console.print(
                    f"  [cyan]💡 Recommended: {', '.join(result.quota_result.recommended_skus[:3])}[/cyan]")
            console.print()

    # ========================================
    # Backward Compatibility Aliases
    # ========================================

    @staticmethod
    def format_layer1_results(results: List[ProjectReadinessResult]) -> Table:
        """
        Alternative name for format_landing_zone_results() - Format Landing Zone validation results

        Args:
            results: List of project readiness results

        Returns:
            Rich Table with formatted results
        """
        return EnhancedTableFormatter.format_landing_zone_results(results)

    @staticmethod
    def format_layer2_results(results: List[MachineValidationReport]) -> Table:
        """
        Alternative name for format_servers_results() - Format Servers validation results

        Args:
            results: List of machine validation reports

        Returns:
            Rich Table with formatted results
        """
        return EnhancedTableFormatter.format_servers_results(results)

    @staticmethod
    def format_layer1_summary(report: LandingZoneValidationReport) -> Table:
        """
        Alternative name for format_landing_zone_summary() - Format Landing Zone summary

        Args:
            report: Landing zone validation report

        Returns:
            Rich Table with summary information
        """
        return EnhancedTableFormatter.format_landing_zone_summary(report)

    @staticmethod
    def display_layer1_details(result: ProjectReadinessResult):
        """
        Alternative name for display_landing_zone_details() - Display Landing Zone details

        Args:
            result: Project readiness result
        """
        return EnhancedTableFormatter.display_landing_zone_details(result)
