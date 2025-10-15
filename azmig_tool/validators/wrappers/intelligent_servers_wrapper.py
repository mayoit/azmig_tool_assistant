"""
Intelligent Servers Validator Wrapper

Combines the core server validation capabilities of ServersValidatorWrapper
with the intelligent project matching and discovery features of IntelligentServerValidator.

Features:
- Intelligent server-to-project matching
- Live Azure Migrate discovery integration  
- Cross-subscription scenario handling
- Configuration-driven validation execution
- Enhanced reporting with discovery status
- Auto-discovery of cache storage and recovery vaults

Usage:
    from azmig_tool.validators.wrappers import IntelligentServersValidatorWrapper
    from azmig_tool.config.validation_config import get_validation_config
    
    wrapper = IntelligentServersValidatorWrapper(credential, get_validation_config())
    wrapper.load_landing_zone_data(lz_projects, lz_results)
    report = wrapper.intelligent_validate_all(machine_configs)
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from azure.core.credentials import TokenCredential
from rich.console import Console
from rich.table import Table
from rich import box

from .servers_wrapper import ServersValidatorWrapper, ServerValidationResult, ServersValidationReport
from ...core.models import (
    MachineConfig,
    MigrateProjectConfig,
    ProjectReadinessResult,
    MachineValidationReport,
    ValidationResult,
    ValidationStage,
    ValidationStatus,
    MachineDiscoveryInfo,
    AzureMigrateProject
)
from ...config.validation_config import ValidationConfig
from ...clients.azure_migrate_client import AzureMigrateIntegration

console = Console()


@dataclass
class ProjectMatchResult:
    """Result of matching a server to a migrate project"""
    server_config: MachineConfig
    matched_project: Optional[MigrateProjectConfig] = None
    cache_storage_account: Optional[str] = None
    recovery_vault: Optional[str] = None
    validation_issues: List[str] = field(default_factory=list)
    discovery_info: Optional[MachineDiscoveryInfo] = None


@dataclass
class IntelligentServerValidationResult(ServerValidationResult):
    """Enhanced server validation result with intelligent features"""
    # Inherit all fields from ServerValidationResult
    # Add intelligent validation fields
    project_match_result: Optional[ValidationResult] = None
    discovery_result: Optional[ValidationResult] = None
    cache_storage_result: Optional[ValidationResult] = None
    recovery_vault_result: Optional[ValidationResult] = None
    
    # Metadata from intelligent matching
    matched_project_name: Optional[str] = None
    discovery_info: Optional[MachineDiscoveryInfo] = None


@dataclass 
class IntelligentServersValidationReport(ServersValidationReport):
    """Enhanced validation report with intelligent insights"""
    # Inherit from base report
    # Add intelligent summary data
    project_matches: int = 0
    discovered_machines: int = 0
    cross_subscription_scenarios: int = 0


class IntelligentServersValidatorWrapper(ServersValidatorWrapper):
    """
    Intelligent servers validator that combines core validation with smart project matching
    
    Extends ServersValidatorWrapper with:
    - Automatic server-to-project matching
    - Live Azure Migrate discovery checks
    - Cross-subscription scenario handling
    - Enhanced reporting with discovery insights
    """

    def __init__(self, credential: TokenCredential, validation_config: ValidationConfig):
        """
        Initialize intelligent servers validator
        
        Args:
            credential: Azure credential for API calls
            validation_config: Validation configuration settings
        """
        super().__init__(credential, validation_config)
        
        # Additional components for intelligent validation
        self.azure_migrate_client = AzureMigrateIntegration(credential)
        self.landing_zone_projects: List[MigrateProjectConfig] = []
        self.project_results: List[ProjectReadinessResult] = []
        
    def load_landing_zone_data(self, 
                              projects: List[MigrateProjectConfig],
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
            console.print(f"  • {project.migrate_project_name} ({project.region})")
    
    def match_server_to_project(self, server: MachineConfig) -> ProjectMatchResult:
        """
        Match a server configuration to the appropriate migrate project
        
        Args:
            server: Server machine configuration
            
        Returns:
            ProjectMatchResult with matching project and validation issues
        """
        result = ProjectMatchResult(server_config=server)
        
        # Step 1: Match by target region and subscription (since MachineConfig doesn't have migrate_project_name)
        matched_project = None
        for project in self.landing_zone_projects:
            # Match by target region and subscription
            if (server.target_region.lower() == project.region.lower() and 
                server.target_subscription == project.migrate_project_subscription):
                matched_project = project
                break
        
        if not matched_project:
            # Try to find any project in the same region as fallback
            for project in self.landing_zone_projects:
                if server.target_region.lower() == project.region.lower():
                    matched_project = project
                    result.validation_issues.append(
                        f"Using fallback project '{project.migrate_project_name}' based on region match")
                    break
        
        if not matched_project:
            result.validation_issues.append(
                f"No landing zone project found for region '{server.target_region}'")
            return result
        
        result.matched_project = matched_project
        
        # Step 2: Validate region compatibility
        if server.target_region.lower() != matched_project.region.lower():
            result.validation_issues.append(
                f"Region mismatch: Server targets '{server.target_region}' but project is in '{matched_project.region}'")
        
        # Step 3: Auto-discover cache storage
        cache_storage = self._discover_cache_storage(server, matched_project)
        if cache_storage:
            result.cache_storage_account = cache_storage
        else:
            result.validation_issues.append(
                f"Could not determine cache storage for subscription '{server.target_subscription}' in region '{server.target_region}'")
        
        # Step 4: Auto-discover recovery vault
        result.recovery_vault = self._discover_recovery_vault(matched_project)
        
        return result
    
    def _discover_cache_storage(self, server: MachineConfig, project: MigrateProjectConfig) -> Optional[str]:
        """
        Intelligently discover the appropriate cache storage account
        
        Priority logic:
        1. If server subscription matches project subscription -> use project cache storage
        2. If server is in different subscription -> use project cache storage with cross-subscription warning
        """
        # Same subscription - use project cache storage
        if server.target_subscription == project.migrate_project_subscription:
            return project.cache_storage_account
        
        # Different subscription - use project cache storage but warn about cross-subscription scenario
        console.print(
            f"[yellow]⚠ Cross-subscription migration detected: server in '{server.target_subscription}' using cache from project subscription '{project.migrate_project_subscription}'[/yellow]")
        console.print(
            f"[dim]💡 Consider ensuring network connectivity between subscriptions for cache storage access[/dim]")
        
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
    
    def check_machine_discovery(self, server: MachineConfig, project: MigrateProjectConfig) -> MachineDiscoveryInfo:
        """
        Check if machine is discovered in Azure Migrate
        
        Args:
            server: Server configuration
            project: Matched migrate project
            
        Returns:
            MachineDiscoveryInfo with discovery status and details
        """
        discovery_info = MachineDiscoveryInfo(
            machine_name=server.target_machine_name,
            discovered=False
        )
        
        try:
            # Make live Azure Migrate API call to check discovery
            discovered_machines = self._get_discovered_machines(project)
            
            # Enhanced machine name matching logic
            server_name_lower = server.target_machine_name.lower()
            
            for machine in discovered_machines:
                machine_name = machine.get('name', '').lower()
                
                # Direct match
                if machine_name == server_name_lower:
                    discovery_info.discovered = True
                    discovery_info.ip_address = machine.get('ipAddress')
                    discovery_info.datacenter_location = machine.get('datacenter')
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
                server_base = server_name_lower.replace('p-', '').replace('d-', '')
                machine_base = machine_name.replace('p-', '').replace('d-', '')
                
                if server_base == machine_base and server_base != server_name_lower:
                    discovery_info.discovered = True
                    discovery_info.ip_address = machine.get('ipAddress')
                    discovery_info.datacenter_location = machine.get('datacenter')
                    discovery_info.os_type = machine.get('osType')
                    discovery_info.cpu_cores = machine.get('cpuCores')
                    discovery_info.memory_mb = machine.get('memoryMB')
                    discovery_info.disk_count = machine.get('diskCount')
                    discovery_info.last_seen = machine.get('lastSeen')
                    discovery_info.discovery_source = "Azure Migrate API (name variation)"
                    console.print(
                        f"[green]✓ Machine discovered (name variation): {server.target_machine_name} → {machine.get('name')} (IP: {machine.get('ipAddress')})[/green]")
                    break
        
        except Exception as e:
            console.print(
                f"[yellow]⚠ Could not check discovery status for {server.target_machine_name}: {str(e)}[/yellow]")
        
        return discovery_info
    
    def _get_discovered_machines(self, project: MigrateProjectConfig) -> List[Dict]:
        """
        Get discovered machines from Azure Migrate using live API calls
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
            discovered_machines_raw = self.azure_migrate_client.get_discovered_machines(azure_project)
            
            # Transform to legacy format for backward compatibility
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
        elif 'ipAddresses' in machine and machine['ipAddresses']:
            ip_list = machine['ipAddresses']
            if isinstance(ip_list, list) and len(ip_list) > 0:
                ipv4_addresses = [ip for ip in ip_list if ':' not in ip]
                if ipv4_addresses:
                    return ipv4_addresses[0]
                else:
                    return ip_list[0]
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
        if 'location' in machine:
            return machine['location']
        elif 'fabric' in machine:
            return machine['fabric']
        return 'Unknown'
    
    def create_intelligent_validation_results(self, match_result: ProjectMatchResult) -> List[ValidationResult]:
        """
        Create intelligent validation results based on project matching
        
        Args:
            match_result: Result from project matching
            
        Returns:
            List of validation results for intelligent features
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
                message=f"No matching project found for target region '{server.target_region}'"
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
                    message=f"Machine '{server.target_machine_name}' not discovered in Azure Migrate",
                    details={
                        "appliance": match_result.matched_project.appliance_name if match_result.matched_project else "unknown"
                    }
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
        for issue in match_result.validation_issues:
            validations.append(ValidationResult(
                stage=ValidationStage.CONFIGURATION_VALIDATION,
                passed=False,
                message=issue
            ))
        
        return validations
    
    def intelligent_validate_all_servers(self, 
                                       configs: List[MachineConfig],
                                       migrate_project_name: Optional[str] = None,
                                       migrate_project_rg: Optional[str] = None) -> IntelligentServersValidationReport:
        """
        Perform intelligent validation of all servers with project matching and discovery
        
        Args:
            configs: List of machine configurations
            migrate_project_name: Azure Migrate project name (for discovery validation)
            migrate_project_rg: Azure Migrate project resource group
            
        Returns:
            IntelligentServersValidationReport with enhanced insights
        """
        console.print(f"\n[bold cyan]🧠 Starting Intelligent Server Validation[/bold cyan]")
        console.print(f"Validating {len(configs)} servers against {len(self.landing_zone_projects)} landing zone projects...")
        
        report = IntelligentServersValidationReport()
        
        for i, config in enumerate(configs, 1):
            console.print(f"\n[cyan]Validating server {i}/{len(configs)}: {config.target_machine_name}[/cyan]")
            
            # Step 1: Match server to project
            match_result = self.match_server_to_project(config)
            if match_result.matched_project:
                report.project_matches += 1
            
            # Step 2: Check machine discovery if project matched
            if match_result.matched_project:
                match_result.discovery_info = self.check_machine_discovery(config, match_result.matched_project)
                if match_result.discovery_info and match_result.discovery_info.discovered:
                    report.discovered_machines += 1
            
            # Step 3: Run standard validations from base wrapper
            server_result = self._validate_single_server(config, migrate_project_name, migrate_project_rg)
            
            # Step 4: Create intelligent validation results  
            intelligent_validations = self.create_intelligent_validation_results(match_result)
            
            # Step 5: Create enhanced server result
            enhanced_result = IntelligentServerValidationResult(
                machine_config=server_result.machine_config,
                region_result=server_result.region_result,
                resource_group_result=server_result.resource_group_result,
                vnet_result=server_result.vnet_result,
                vmsku_result=server_result.vmsku_result,
                disk_result=server_result.disk_result,
                discovery_result=server_result.discovery_result,
                rbac_result=server_result.rbac_result,
                overall_status=server_result.overall_status,
                validation_timestamp=server_result.validation_timestamp,
                # Enhanced fields
                matched_project_name=match_result.matched_project.migrate_project_name if match_result.matched_project else None,
                discovery_info=match_result.discovery_info
            )
            
            # Add intelligent validation results to the enhanced result
            for validation in intelligent_validations:
                if validation.stage == ValidationStage.PROJECT_MATCHING:
                    enhanced_result.project_match_result = validation
                elif validation.stage == ValidationStage.MACHINE_DISCOVERY:
                    enhanced_result.discovery_result = validation
                elif validation.stage == ValidationStage.CACHE_STORAGE:
                    enhanced_result.cache_storage_result = validation
                elif validation.stage == ValidationStage.RECOVERY_VAULT:
                    enhanced_result.recovery_vault_result = validation
            
            report.add_result(enhanced_result)
            
            # Show quick status
            passed_standard = sum(1 for field in ['region_result', 'resource_group_result', 'vnet_result', 'vmsku_result', 'disk_result', 'rbac_result']
                                if getattr(enhanced_result, field) and getattr(enhanced_result, field).passed)
            passed_intelligent = sum(1 for v in intelligent_validations if v.passed)
            
            total_passed = passed_standard + passed_intelligent
            total_validations = 6 + len(intelligent_validations)  # 6 standard + intelligent validations
            
            status = "✅ Ready" if total_passed == total_validations else f"⚠️ {total_validations - total_passed} issues"
            console.print(f"  → {status} ({total_passed}/{total_validations} validations passed)")
        
        self._display_intelligent_summary(report)
        return report
    
    def _display_intelligent_summary(self, report: IntelligentServersValidationReport):
        """Display intelligent validation summary with enhanced insights"""
        console.print(f"\n[bold]🧠 Intelligent Validation Summary[/bold]")
        
        # Summary statistics
        summary_table = Table(box=box.ROUNDED)
        summary_table.add_column("Metric", style="bold cyan")
        summary_table.add_column("Count", style="bold", justify="right")
        summary_table.add_column("Status", style="bold")
        
        summary_table.add_row("Total Servers", str(report.total_servers), "")
        summary_table.add_row("Project Matches", str(report.project_matches),
                            f"[green]{report.project_matches}/{report.total_servers}[/green]" if report.project_matches == report.total_servers 
                            else f"[yellow]{report.project_matches}/{report.total_servers}[/yellow]")
        summary_table.add_row("Discovered Machines", str(report.discovered_machines),
                            f"[green]{report.discovered_machines}/{report.total_servers}[/green]" if report.discovered_machines == report.total_servers
                            else f"[yellow]{report.discovered_machines}/{report.total_servers}[/yellow]")
        summary_table.add_row("Migration Ready", str(report.ready_servers),
                            f"[green]{report.ready_servers}/{report.total_servers}[/green]" if report.ready_servers == report.total_servers
                            else f"[red]{report.ready_servers}/{report.total_servers}[/red]")
        
        console.print(summary_table)
        
        # Show detailed machine status
        if report.server_results:
            # Filter to get only IntelligentServerValidationResult instances
            intelligent_results = [r for r in report.server_results if isinstance(r, IntelligentServerValidationResult)]
            if intelligent_results:
                self._display_machine_details_table(intelligent_results)
    
    def _display_machine_details_table(self, results: List[IntelligentServerValidationResult]):
        """Display detailed machine validation table with intelligent insights"""
        console.print(f"\n[bold]Machine Validation Details[/bold]")
        
        table = Table(box=box.DOUBLE_EDGE, show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3, justify="right")
        table.add_column("Machine Name", style="cyan")
        table.add_column("Project Match", style="green")
        table.add_column("Discovery", style="blue", justify="center")
        table.add_column("IP Address", style="yellow")
        table.add_column("Datacenter", style="magenta")
        table.add_column("Status", style="bold", justify="center")
        
        for i, result in enumerate(results, 1):
            # Project match
            project_match = "No Match"
            if result.matched_project_name:
                project_match = result.matched_project_name[:20] + "..." if len(result.matched_project_name) > 20 else result.matched_project_name
            
            # Discovery status
            discovery_status = "❓ Unknown"
            ip_address = "Unknown"
            datacenter = "Unknown"
            if result.discovery_info:
                discovery_status = "✅ Yes" if result.discovery_info.discovered else "❌ No"
                ip_address = result.discovery_info.ip_address or "Unknown"
                datacenter = result.discovery_info.datacenter_location or "Unknown"
            
            # Overall status
            if result.overall_status == ValidationStatus.OK:
                status = "[green]✅ Ready[/green]"
            elif result.overall_status == ValidationStatus.WARNING:
                status = "[yellow]⚠️ Issues[/yellow]"
            else:
                status = "[red]❌ Failed[/red]"
            
            table.add_row(
                str(i),
                result.machine_config.target_machine_name,
                project_match,
                discovery_status,
                ip_address,
                datacenter,
                status
            )
        
        console.print(table)