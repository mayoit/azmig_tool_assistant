"""
Intelligent Server Validation System
Advanced validation that matches servers to migrate projects and performs intelligent checks
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich import box
from azure.core.credentials import TokenCredential

from ..core.models import (
    MigrationConfig,
    MigrateProjectConfig,
    ProjectReadinessResult,
    MachineValidationReport,
    ValidationResult,
    ValidationStage,
    MachineDiscoveryInfo,
    AzureMigrateProject
)
from .base.validator_interface import BaseValidatorInterface
from ..clients.azure_migrate_client import AzureMigrateIntegration

console = Console()


@dataclass
class ProjectMatchResult:
    """Result of matching a server to a migrate project"""
    server_config: MigrationConfig
    matched_project: Optional[MigrateProjectConfig] = None
    cache_storage_account: Optional[str] = None
    recovery_vault: Optional[str] = None
    validation_issues: Optional[List[str]] = None
    discovery_info: Optional[MachineDiscoveryInfo] = None

    def __post_init__(self):
        if self.validation_issues is None:
            self.validation_issues = []


class IntelligentServerValidator:
    """
    Intelligent server validation that matches servers to migrate projects
    and performs advanced discovery and readiness checks
    """

    def __init__(self, validator: BaseValidatorInterface, credential: Optional[TokenCredential] = None):
        """
        Initialize with a base validator for Azure API calls

        Args:
            validator: Base validator implementing Azure API calls
            credential: Optional Azure credential for live API calls (any TokenCredential type)
        """
        self.validator = validator
        self.landing_zone_projects: List[MigrateProjectConfig] = []
        self.project_results: List[ProjectReadinessResult] = []

        # Initialize Azure Migrate client for live API calls
        if credential is None:
            raise ValueError(
                "Credential is required. Use CachedCredentialFactory.create_credential() to get cached credentials.")
        self.credential = credential
        self.azure_migrate_client = AzureMigrateIntegration(self.credential)

    def load_landing_zone_data(self, projects: List[MigrateProjectConfig],
                               project_results: Optional[List[ProjectReadinessResult]] = None):
        """
        Load landing zone project data for intelligent matching

        Args:
            projects: List of migrate project configurations
            project_results: Optional project readiness results
        """
        self.landing_zone_projects = projects
        self.project_results = project_results or []

        console.print(
            f"[cyan]✓ Loaded {len(projects)} landing zone projects for intelligent matching[/cyan]")
        for project in projects:
            console.print(
                f"  • {project.migrate_project_name} ({project.region})")

    def match_server_to_project(self, server: MigrationConfig) -> ProjectMatchResult:
        """
        Match a server configuration to the appropriate migrate project

        Args:
            server: Server migration configuration

        Returns:
            ProjectMatchResult with matching project and validation issues
        """
        result = ProjectMatchResult(server_config=server)

        # Step 1: Direct project name match
        matched_project = None
        for project in self.landing_zone_projects:
            if project.migrate_project_name == server.migrate_project_name:
                matched_project = project
                break

        if not matched_project:
            if result.validation_issues is not None:
                result.validation_issues.append(
                    f"No landing zone project found for '{server.migrate_project_name}'"
                )
            return result

        result.matched_project = matched_project

        # Step 2: Validate region compatibility
        if server.target_region.lower() != matched_project.region.lower():
            if result.validation_issues is not None:
                result.validation_issues.append(
                    f"Region mismatch: Server targets '{server.target_region}' but project is in '{matched_project.region}'"
                )

        # Step 3: Auto-discover cache storage
        cache_storage = self._discover_cache_storage(server, matched_project)
        if cache_storage:
            result.cache_storage_account = cache_storage
        else:
            if result.validation_issues is not None:
                result.validation_issues.append(
                    f"Could not determine cache storage for subscription '{server.target_subscription}' in region '{server.target_region}'"
                )

        # Step 4: Auto-discover recovery vault
        result.recovery_vault = self._discover_recovery_vault(matched_project)

        return result

    def _discover_cache_storage(self, server: MigrationConfig, project: MigrateProjectConfig) -> Optional[str]:
        """
        Intelligently discover the appropriate cache storage account

        Priority logic:
        1. If server subscription matches project subscription -> use project cache storage
        2. If server is in different subscription -> use project cache storage with cross-subscription warning
        3. Future enhancement: Query Azure APIs to discover cache storage accounts in target subscription
        """
        # Same subscription - use project cache storage
        if server.target_subscription == project.migrate_project_subscription:
            return project.cache_storage_account

        # Different subscription - use project cache storage but warn about cross-subscription scenario
        console.print(
            f"[yellow]⚠ Cross-subscription migration detected: server in '{server.target_subscription}' using cache from project subscription '{project.migrate_project_subscription}'[/yellow]")
        console.print(
            f"[dim]� Consider ensuring network connectivity between subscriptions for cache storage access[/dim]")
        
        return project.cache_storage_account

    def _discover_recovery_vault(self, project: MigrateProjectConfig) -> Optional[str]:
        """Auto-discover recovery vault from migrate project"""
        # Try to get from project results first
        for result in self.project_results:
            if result.config.migrate_project_name == project.migrate_project_name:
                if hasattr(result.config, 'recovery_vault_name') and result.config.recovery_vault_name:
                    return result.config.recovery_vault_name

        # Fall back to project config
        if hasattr(project, 'recovery_vault_name') and project.recovery_vault_name:
            return project.recovery_vault_name

        # Generate expected recovery vault name based on migrate project
        return f"{project.migrate_project_name}-MigrateVault-{project.migrate_project_name[-10:]}"

    def check_machine_discovery(self, server: MigrationConfig, project: MigrateProjectConfig) -> MachineDiscoveryInfo:
        """
        Check if machine is discovered in Azure Migrate

        Args:
            server: Server configuration
            project: Matched migrate project

        Returns:
            MachineDiscoveryInfo with discovery status and details
        """
        # This would make actual Azure Migrate API calls
        # For now, we'll simulate the discovery check

        discovery_info = MachineDiscoveryInfo(
            machine_name=server.machine_name,
            discovered=False  # Will be updated by actual API call
        )

        try:
            # Make live Azure Migrate API call to check discovery
            discovered_machines = self._get_discovered_machines(project)

            # Enhanced machine name matching logic
            server_name_lower = server.machine_name.lower()

            for machine in discovered_machines:
                machine_name = machine.get('name', '').lower()

                # Direct match
                if machine_name == server_name_lower:
                    discovery_info.discovered = True
                    discovery_info.ip_address = machine.get('ipAddress')
                    discovery_info.datacenter_location = machine.get(
                        'datacenter')
                    discovery_info.os_type = machine.get('osType')
                    discovery_info.cpu_cores = machine.get('cpuCores')
                    discovery_info.memory_mb = machine.get('memoryMB')
                    discovery_info.disk_count = machine.get('diskCount')
                    discovery_info.last_seen = machine.get('lastSeen')
                    discovery_info.discovery_source = "Azure Migrate API"
                    console.print(
                        f"[green]✓ Machine discovered: {machine.get('name')} (IP: {machine.get('ipAddress')})[/green]")
                    break

                # Handle naming variations (d- vs p- prefix, etc.)
                # Remove common prefixes and compare base names
                server_base = server_name_lower.replace(
                    'p-', '').replace('d-', '')
                machine_base = machine_name.replace('p-', '').replace('d-', '')

                if server_base == machine_base and server_base != server_name_lower:
                    discovery_info.discovered = True
                    discovery_info.ip_address = machine.get('ipAddress')
                    discovery_info.datacenter_location = machine.get(
                        'datacenter')
                    discovery_info.os_type = machine.get('osType')
                    discovery_info.cpu_cores = machine.get('cpuCores')
                    discovery_info.memory_mb = machine.get('memoryMB')
                    discovery_info.disk_count = machine.get('diskCount')
                    discovery_info.last_seen = machine.get('lastSeen')
                    discovery_info.discovery_source = "Azure Migrate API (name variation)"
                    console.print(
                        f"[green]✓ Machine discovered (name variation): {server.machine_name} → {machine.get('name')} (IP: {machine.get('ipAddress')})[/green]")
                    break

        except Exception as e:
            console.print(
                f"[yellow]⚠ Could not check discovery status for {server.machine_name}: {str(e)}[/yellow]")

        return discovery_info

    def _get_discovered_machines(self, project: MigrateProjectConfig) -> List[Dict]:
        """
        Get discovered machines from Azure Migrate using live API calls

        Makes actual Azure Migrate API call to get discovered machines
        """
        try:
            # Create AzureMigrateProject object for the API call
            azure_project = AzureMigrateProject(
                subscription_id=project.migrate_project_subscription or project.subscription_id,
                resource_group=project.migrate_resource_group or project.cache_storage_resource_group,
                name=project.migrate_project_name,
                location=project.region
            )

            console.print(
                f"[dim]🔍 Querying Azure Migrate API for discovered machines in project '{azure_project.name}'...[/dim]")

            # Make the actual API call using the Azure Migrate client
            discovered_machines_raw = self.azure_migrate_client.get_discovered_machines(
                azure_project)

            # Transform to legacy format for backward compatibility with intelligent validator
            discovered_machines = []
            for machine in discovered_machines_raw:
                machine_info = {
                    "name": machine.get('display_name', machine.get('name', '')),
                    "ipAddress": self._extract_ip_address(machine),
                    "datacenter": self._extract_datacenter_from_properties(machine),
                    "osType": machine.get('operating_system', 'Unknown'),
                    "cpuCores": machine.get('cores', 0),
                    "memoryMB": machine.get('memory_mb', 0),
                    "diskCount": len(machine.get('disks', [])),
                    "lastSeen": "Live API Response"
                }
                discovered_machines.append(machine_info)

            console.print(f"[green]✓ Retrieved {len(discovered_machines)} discovered machines from Azure Migrate API[/green]")
            return discovered_machines

        except Exception as e:
            console.print(f"[red]❌ Error querying Azure Migrate API: {str(e)}[/red]")
            return []

    def _extract_ip_address(self, machine: Dict) -> str:
        """Extract IP address from machine data"""
        # Try different possible IP address fields
        # Check for 'ip_addresses' field (from our updated azure_migrate_client)
        if 'ip_addresses' in machine and machine['ip_addresses']:
            ip_list = machine['ip_addresses']
            if isinstance(ip_list, list) and len(ip_list) > 0:
                # Filter out IPv6 addresses if both IPv4 and IPv6 are present
                ipv4_addresses = [ip for ip in ip_list if ':' not in ip]
                if ipv4_addresses:
                    return ipv4_addresses[0]  # Prefer IPv4
                else:
                    return ip_list[0]  # Return first IP if no IPv4 found
            return str(ip_list)
        # Legacy field names for backward compatibility
        elif 'ipAddresses' in machine and machine['ipAddresses']:
            ip_list = machine['ipAddresses']
            if isinstance(ip_list, list) and len(ip_list) > 0:
                # Filter out IPv6 addresses if both IPv4 and IPv6 are present
                ipv4_addresses = [ip for ip in ip_list if ':' not in ip]
                if ipv4_addresses:
                    return ipv4_addresses[0]  # Prefer IPv4
                else:
                    return ip_list[0]  # Return first IP if no IPv4 found
            return str(ip_list)
        elif 'ip_address' in machine:
            return machine['ip_address']
        elif 'networkAdapters' in machine and machine['networkAdapters']:
            adapters = machine['networkAdapters']
            if isinstance(adapters, list) and adapters:
                return adapters[0].get('ipAddress', 'Unknown')
        return 'Unknown'

    def _extract_datacenter_from_properties(self, machine: Dict) -> str:
        """Extract datacenter information from machine properties"""
        # This would typically come from the discovery source or appliance info
        # For now, we'll use a default or try to infer from other data
        if 'location' in machine:
            return machine['location']
        elif 'fabric' in machine:
            return machine['fabric']
        return 'Unknown'

    def validate_migration_readiness(self, match_result: ProjectMatchResult) -> List[ValidationResult]:
        """
        Validate if server is ready for migration based on discovery and project data

        Args:
            match_result: Result from project matching

        Returns:
            List of validation results for migration readiness
        """
        validations = []
        server = match_result.server_config

        # Validation 1: Project matching
        if match_result.matched_project:
            validations.append(ValidationResult(
                stage=ValidationStage.PROJECT_MATCHING,
                passed=True,
                message=f"Successfully matched to project '{match_result.matched_project.migrate_project_name}'"
            ))
        else:
            validations.append(ValidationResult(
                stage=ValidationStage.PROJECT_MATCHING,
                passed=False,
                message=f"No matching project found for '{server.migrate_project_name}'"
            ))

        # Validation 2: Discovery status
        if match_result.discovery_info:
            if match_result.discovery_info.discovered:
                validations.append(ValidationResult(
                    stage=ValidationStage.MACHINE_DISCOVERY,
                    passed=True,
                    message=f"Machine discovered in datacenter (IP: {match_result.discovery_info.ip_address})",
                    details={
                        "ip_address": match_result.discovery_info.ip_address,
                        "datacenter": match_result.discovery_info.datacenter_location,
                        "os_type": match_result.discovery_info.os_type,
                        "last_seen": match_result.discovery_info.last_seen
                    }
                ))
            else:
                validations.append(ValidationResult(
                    stage=ValidationStage.MACHINE_DISCOVERY,
                    passed=False,
                    message=f"Machine '{server.machine_name}' not discovered in Azure Migrate",
                    details={
                        "appliance": match_result.matched_project.appliance_name if match_result.matched_project else "unknown"}
                ))

        # Validation 3: Cache storage availability
        if match_result.cache_storage_account:
            validations.append(ValidationResult(
                stage=ValidationStage.CACHE_STORAGE,
                passed=True,
                message=f"Cache storage available: {match_result.cache_storage_account}"
            ))
        else:
            validations.append(ValidationResult(
                stage=ValidationStage.CACHE_STORAGE,
                passed=False,
                message="No cache storage account available for replication"
            ))

        # Validation 4: Recovery vault availability
        if match_result.recovery_vault:
            validations.append(ValidationResult(
                stage=ValidationStage.RECOVERY_VAULT,
                passed=True,
                message=f"Recovery vault available: {match_result.recovery_vault}"
            ))
        else:
            validations.append(ValidationResult(
                stage=ValidationStage.RECOVERY_VAULT,
                passed=False,
                message="No recovery vault available for backup and replication"
            ))

        # Validation 5: Additional validation issues
        if match_result.validation_issues:
            for issue in match_result.validation_issues:
                validations.append(ValidationResult(
                    stage=ValidationStage.CONFIGURATION_VALIDATION,
                    passed=False,
                    message=issue
                ))

        return validations

    def intelligent_validate_all(self, servers: List[MigrationConfig]) -> List[MachineValidationReport]:
        """
        Perform intelligent validation of all servers

        Args:
            servers: List of server configurations

        Returns:
            List of machine validation reports with intelligent insights
        """
        console.print(
            f"\n[bold cyan]🧠 Starting Intelligent Server Validation[/bold cyan]")
        console.print(
            f"Validating {len(servers)} servers against {len(self.landing_zone_projects)} landing zone projects...")

        reports = []

        for i, server in enumerate(servers, 1):
            console.print(
                f"\n[cyan]Validating server {i}/{len(servers)}: {server.machine_name}[/cyan]")

            # Step 1: Match server to project
            match_result = self.match_server_to_project(server)

            # Step 2: Check machine discovery if project matched
            if match_result.matched_project:
                match_result.discovery_info = self.check_machine_discovery(
                    server, match_result.matched_project)

            # Step 3: Validate migration readiness
            validations = self.validate_migration_readiness(match_result)

            # Step 4: Get additional standard validations from base validator
            try:
                standard_validations = self.validator.validate_machine_config(
                    server)
                validations.extend(standard_validations)
            except Exception as e:
                console.print(
                    f"[yellow]⚠ Standard validation error for {server.machine_name}: {str(e)}[/yellow]")

            # Step 5: Calculate overall status
            failed_validations = [v for v in validations if not v.passed]
            if not failed_validations:
                overall_status = "PASSED"
            elif len(failed_validations) < len(validations) / 2:  # More than half passed
                overall_status = "WARNING"
            else:
                overall_status = "FAILED"

            # Step 6: Create machine validation report
            report = MachineValidationReport(
                config=server,
                validations=validations,
                overall_status=overall_status,
                discovery_info=match_result.discovery_info,
                matched_project=match_result.matched_project.migrate_project_name if match_result.matched_project else None,
                cache_storage=match_result.cache_storage_account,
                recovery_vault=match_result.recovery_vault
            )

            reports.append(report)

            # Show quick status
            passed_count = sum(1 for v in validations if v.passed)
            total_count = len(validations)
            status = "✅ Ready" if passed_count == total_count else f"⚠️ {total_count - passed_count} issues"
            console.print(
                f"  → {status} ({passed_count}/{total_count} validations passed)")

        self._display_intelligent_summary(reports)
        return reports

    def _display_intelligent_summary(self, reports: List[MachineValidationReport]):
        """Display intelligent validation summary"""
        console.print(f"\n[bold]🧠 Intelligent Validation Summary[/bold]")

        # Summary statistics
        total_servers = len(reports)
        discovered_count = sum(1 for r in reports if hasattr(
            r, 'discovery_info') and r.discovery_info and r.discovery_info.discovered)
        matched_projects = sum(1 for r in reports if hasattr(
            r, 'matched_project') and r.matched_project)
        ready_count = sum(1 for r in reports if r.overall_status == "PASSED")

        summary_table = Table(box=box.ROUNDED)
        summary_table.add_column("Metric", style="bold cyan")
        summary_table.add_column("Count", style="bold", justify="right")
        summary_table.add_column("Status", style="bold")

        summary_table.add_row("Total Servers", str(total_servers), "")
        summary_table.add_row("Project Matches", str(matched_projects),
                              f"[green]{matched_projects}/{total_servers}[/green]" if matched_projects == total_servers else f"[yellow]{matched_projects}/{total_servers}[/yellow]")
        summary_table.add_row("Discovered Machines", str(discovered_count),
                              f"[green]{discovered_count}/{total_servers}[/green]" if discovered_count == total_servers else f"[yellow]{discovered_count}/{total_servers}[/yellow]")
        summary_table.add_row("Migration Ready", str(ready_count),
                              f"[green]{ready_count}/{total_servers}[/green]" if ready_count == total_servers else f"[red]{ready_count}/{total_servers}[/red]")

        console.print(summary_table)

        # Show detailed machine status
        if reports:
            self._display_machine_details_table(reports)

    def _display_machine_details_table(self, reports: List[MachineValidationReport]):
        """Display detailed machine validation table"""
        console.print(f"\n[bold]Machine Validation Details[/bold]")

        table = Table(box=box.DOUBLE_EDGE, show_header=True,
                      header_style="bold magenta")
        table.add_column("#", style="dim", width=3, justify="right")
        table.add_column("Machine Name", style="cyan")
        table.add_column("Project Match", style="green")
        table.add_column("Discovery", style="blue", justify="center")
        table.add_column("IP Address", style="yellow")
        table.add_column("Datacenter", style="magenta")
        table.add_column("Cache Storage", style="cyan")
        table.add_column("Status", style="bold", justify="center")

        for i, report in enumerate(reports, 1):
            # Project match
            project_match = "No Match"
            if hasattr(report, 'matched_project') and report.matched_project:
                project_match = report.matched_project[:20] + "..." if len(
                    report.matched_project) > 20 else report.matched_project

            # Discovery status
            discovery_status = "❓ Unknown"
            ip_address = "Unknown"
            datacenter = "Unknown"
            if hasattr(report, 'discovery_info') and report.discovery_info:
                discovery_status = "✅ Yes" if report.discovery_info.discovered else "❌ No"
                ip_address = report.discovery_info.ip_address or "Unknown"
                datacenter = report.discovery_info.datacenter_location or "Unknown"

            # Cache storage
            cache_storage = "None"
            if hasattr(report, 'cache_storage') and report.cache_storage:
                cache_storage = report.cache_storage[:20] + "..." if len(
                    report.cache_storage) > 20 else report.cache_storage

            # Overall status
            if report.overall_status == "PASSED":
                status = "[green]✅ Ready[/green]"
            elif report.overall_status == "WARNING":
                status = "[yellow]⚠️ Issues[/yellow]"
            else:
                failed_validations = [
                    v for v in report.validations if not v.passed]
                first_issue = failed_validations[0].message[:15] + \
                    "..." if failed_validations else "Failed"
                status = f"[red]❌ {first_issue}[/red]"

            table.add_row(
                str(i),
                report.config.machine_name,
                project_match,
                discovery_status,
                ip_address,
                datacenter,
                cache_storage,
                status
            )

        console.print(table)
