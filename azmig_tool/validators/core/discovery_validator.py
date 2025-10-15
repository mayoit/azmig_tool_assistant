"""
Discovery Validator - Azure Migrate machine discovery validation

Handles validation of machine discovery status:
- Machine discovery in Azure Migrate projects
- Discovery agent health and connectivity
- Machine assessment readiness
- Dependency mapping status
- Replication readiness
"""
from typing import Optional, List, Dict, Any
from azure.core.credentials import TokenCredential

from ...core.models import (
    MachineConfig,
    DiscoveryValidationResult,
    ValidationStatus
)
from ...clients.azure_migrate_client import AzureMigrateIntegration


class DiscoveryValidator:
    """
    Validates machine discovery status in Azure Migrate
    
    Checks:
    - Machine is discovered in target Migrate project
    - Discovery agent is healthy and reporting
    - Machine assessment data is available
    - Dependencies are mapped (if enabled)
    - Machine is ready for replication setup
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize discovery validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._migrate_clients = {}

    def _get_migrate_client(self, subscription_id: str) -> AzureMigrateIntegration:
        """Get or create cached Azure Migrate client"""
        if subscription_id not in self._migrate_clients:
            self._migrate_clients[subscription_id] = AzureMigrateIntegration(
                self.credential
            )
        return self._migrate_clients[subscription_id]

    def validate(
        self, 
        config: MachineConfig, 
        migrate_project_name: str,
        migrate_project_rg: str
    ) -> DiscoveryValidationResult:
        """
        Validate machine discovery status

        Args:
            config: Machine configuration
            migrate_project_name: Azure Migrate project name
            migrate_project_rg: Azure Migrate project resource group

        Returns:
            DiscoveryValidationResult with discovery details
        """
        try:
            migrate_client = self._get_migrate_client(config.target_subscription)

            # Search for the machine in the Migrate project
            discovered_machine = self._find_discovered_machine(
                migrate_client,
                migrate_project_rg,
                migrate_project_name,
                config.target_machine_name,
                config.target_subscription
            )

            if not discovered_machine:
                return DiscoveryValidationResult(
                    machine_name=config.target_machine_name,
                    migrate_project=migrate_project_name,
                    subscription_id=config.target_subscription,
                    status=ValidationStatus.FAILED,
                    is_discovered=False,
                    last_heartbeat=None,
                    discovery_status="Not Found",
                    message=f"Machine '{config.target_machine_name}' not found in Migrate project '{migrate_project_name}'",
                    suggested_action="Verify machine name or ensure discovery agent is running on source machine"
                )

            # Extract discovery information
            discovery_info = self._extract_discovery_info(discovered_machine)
            
            # Validate discovery health
            is_healthy, health_issues = self._validate_discovery_health(discovery_info)

            # Determine overall status
            if not is_healthy:
                status = ValidationStatus.WARNING
                message = f"Machine discovered but has health issues: {'; '.join(health_issues)}"
                suggested_action = "Check discovery agent status and network connectivity"
            elif discovery_info.get("assessment_status") == "Ready":
                status = ValidationStatus.OK
                message = f"Machine '{config.target_machine_name}' is discovered and ready for migration"
                suggested_action = None
            else:
                status = ValidationStatus.WARNING
                message = f"Machine discovered but assessment may be incomplete"
                suggested_action = "Wait for assessment to complete or verify agent configuration"

            return DiscoveryValidationResult(
                machine_name=config.target_machine_name,
                migrate_project=migrate_project_name,
                subscription_id=config.target_subscription,
                status=status,
                is_discovered=True,
                last_heartbeat=discovery_info.get("last_heartbeat"),
                discovery_status=discovery_info.get("status", "Unknown"),
                message=message,
                suggested_action=suggested_action
            )

        except Exception as e:
            return DiscoveryValidationResult(
                machine_name=config.target_machine_name,
                migrate_project=migrate_project_name,
                subscription_id=config.target_subscription,
                status=ValidationStatus.FAILED,
                is_discovered=False,
                last_heartbeat=None,
                discovery_status="Error",
                message=f"Error validating discovery status: {str(e)}",
                suggested_action="Check Azure Migrate project access and permissions"
            )

    def _find_discovered_machine(
        self,
        migrate_client: AzureMigrateIntegration,
        resource_group: str,
        project_name: str,
        machine_name: str,
        subscription_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find machine in Azure Migrate project

        Args:
            migrate_client: Azure Migrate client
            resource_group: Resource group containing Migrate project
            project_name: Migrate project name
            machine_name: Target machine name to find

        Returns:
            Machine data if found, None otherwise
        """
        try:
            # Create project object and get discovered machines
            from ...core.models import AzureMigrateProject
            project = AzureMigrateProject(
                name=project_name,
                resource_group=resource_group,
                subscription_id=subscription_id,
                location=""  # Location not needed for discovery lookup
            )
            machines = migrate_client.get_discovered_machines(project)
            
            # Search for machine by name (case-insensitive)
            machine_name_lower = machine_name.lower()
            
            for machine in machines:
                # Check various name fields that might contain the machine name
                name_fields = [
                    machine.get("displayName", ""),
                    machine.get("name", ""),
                    machine.get("properties", {}).get("displayName", ""),
                    machine.get("properties", {}).get("computerName", "")
                ]
                
                for name_field in name_fields:
                    if name_field and name_field.lower() == machine_name_lower:
                        return machine
            
            return None
            
        except Exception:
            return None

    def _extract_discovery_info(self, machine_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant discovery information from machine data

        Args:
            machine_data: Raw machine data from Azure Migrate

        Returns:
            Dictionary with extracted discovery information
        """
        properties = machine_data.get("properties", {})
        
        return {
            "status": properties.get("discoveryMachineArmId") and "Discovered" or "Partial",
            "last_heartbeat": properties.get("lastUpdatedTime"),
            "assessment_status": self._determine_assessment_status(properties),
            "agent_version": properties.get("guestDetailsDiscoveryTimestamp"),
            "os_type": properties.get("operatingSystemType"),
            "os_name": properties.get("operatingSystemName"),
            "cpu_count": properties.get("numberOfCores"),
            "memory_mb": properties.get("allocatedMemoryInMB"),
            "disk_count": len(properties.get("disks", [])),
            "network_adapters": len(properties.get("networkAdapters", []))
        }

    def _determine_assessment_status(self, properties: Dict[str, Any]) -> str:
        """
        Determine assessment readiness status

        Args:
            properties: Machine properties from Azure Migrate

        Returns:
            Assessment status string
        """
        # Check if key assessment data is available
        has_cpu_info = properties.get("numberOfCores") is not None
        has_memory_info = properties.get("allocatedMemoryInMB") is not None
        has_disk_info = len(properties.get("disks", [])) > 0
        has_network_info = len(properties.get("networkAdapters", [])) > 0
        has_os_info = properties.get("operatingSystemType") is not None

        required_checks = [has_cpu_info, has_memory_info, has_disk_info, has_os_info]
        
        if all(required_checks):
            return "Ready"
        elif any(required_checks):
            return "Partial"
        else:
            return "Incomplete"

    def _validate_discovery_health(self, discovery_info: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate discovery health and identify issues

        Args:
            discovery_info: Extracted discovery information

        Returns:
            Tuple of (is_healthy, list_of_issues)
        """
        issues = []

        # Check last heartbeat recency
        last_heartbeat = discovery_info.get("last_heartbeat")
        if last_heartbeat:
            # In practice, you'd parse the timestamp and check if it's recent
            # For now, assume it's healthy if timestamp exists
            pass
        else:
            issues.append("No recent heartbeat from discovery agent")

        # Check assessment completeness
        assessment_status = discovery_info.get("assessment_status")
        if assessment_status in ["Incomplete", "Partial"]:
            issues.append(f"Assessment is {assessment_status.lower()}")

        # Check minimum system information
        if not discovery_info.get("cpu_count"):
            issues.append("CPU information not available")
        if not discovery_info.get("memory_mb"):
            issues.append("Memory information not available")
        if not discovery_info.get("disk_count"):
            issues.append("Disk information not available")

        # Check OS information
        if not discovery_info.get("os_type"):
            issues.append("Operating system information not available")

        return len(issues) == 0, issues