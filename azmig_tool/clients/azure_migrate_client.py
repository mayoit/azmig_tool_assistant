"""
Azure Migrate integration for discovery and replication enablement
"""
from typing import List, Optional, Dict
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from rich.console import Console
from ..models import (
    MigrationConfig,
    ValidationResult,
    ValidationStage,
    AzureMigrateProject,
    ReplicationCache
)
from .azure_client import AzureMigrateApiClient
from ..constants import AZURE_ROLE_IDS

console = Console()


class AzureMigrateIntegration:
    """Integration with Azure Migrate for discovery and replication"""

    def __init__(self, credential: Optional[TokenCredential] = None):
        if credential is None:
            raise ValueError(
                "Credential is required. Use CachedCredentialFactory.create_credential() to get cached credentials.")
        self.credential = credential
        self._clients_cache: Dict[str, AzureMigrateApiClient] = {}

    def _get_migrate_client(self, subscription_id: str) -> AzureMigrateApiClient:
        """Get or create cached Azure Migrate client"""
        if subscription_id not in self._clients_cache:
            self._clients_cache[subscription_id] = AzureMigrateApiClient(
                self.credential,
                subscription_id
            )
        return self._clients_cache[subscription_id]

    def list_migrate_projects(
        self,
        subscription_id: str,
        resource_group: Optional[str] = None
    ) -> List[AzureMigrateProject]:
        """
        List Azure Migrate projects in subscription or resource group

        Args:
            subscription_id: Azure subscription ID
            resource_group: Optional resource group filter

        Returns:
            List of AzureMigrateProject objects
        """
        try:
            client = self._get_migrate_client(subscription_id)
            projects = []

            # List projects using REST API
            project_list = client.list_projects(resource_group=resource_group)

            for project in project_list:
                # Extract resource group from ID
                # ID format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Migrate/migrateProjects/{name}
                resource_id = project.get('id', '')
                parts = resource_id.split('/')
                rg_name = parts[4] if len(parts) > 4 else resource_group or ''

                projects.append(AzureMigrateProject(
                    name=project.get('name', ''),
                    resource_group=rg_name,
                    subscription_id=subscription_id,
                    location=project.get('location', ''),
                    project_id=resource_id
                ))

            return projects

        except Exception as e:
            console.print(
                f"[red]Error listing Azure Migrate projects: {str(e)}[/red]")
            return []

    def get_discovered_machines(
        self,
        project: AzureMigrateProject
    ) -> List[Dict]:
        """
        Get list of discovered machines in Azure Migrate project

        Args:
            project: AzureMigrateProject object

        Returns:
            List of discovered machine dictionaries
        """
        try:
            client = self._get_migrate_client(project.subscription_id)
            machines = []

            # Get discovered machines from the project using REST API
            discovered_machines = client.list_discovered_machines(
                project.resource_group,
                project.name
            )

            for machine in discovered_machines:
                
                properties = machine.get('properties', {})
                
                # Extract data from discoveryData, assessmentData, and migrationData
                discovery_data = properties.get('discoveryData', [])
                assessment_data = properties.get('assessmentData', [])
                migration_data = properties.get('migrationData', [])
                
                # Get machine details - prioritize migrationData, but always get IP from discoveryData
                machine_name = machine.get('name', '')
                display_name = machine_name
                os_info = None
                boot_type = None
                cores = None
                memory_mb = None
                disks = []
                ip_addresses = []
                fqdn = None
                
                # First priority: Extract from migrationData if available (migration-ready machines)
                if migration_data and len(migration_data) > 0:
                    latest_migration = migration_data[0]  # Use first item in migrationData
                    display_name = latest_migration.get('machineName', machine_name)
                    os_info = latest_migration.get('osName') or latest_migration.get('osType')
                    fqdn = latest_migration.get('fqdn')
                    ip_addresses = latest_migration.get('ipAddresses', [])
                    
                    # Extract boot type from extendedInfo if available
                    extended_info = latest_migration.get('extendedInfo', {})
                    boot_type = extended_info.get('bootType')
                    
                    # For migration data, we might not have detailed specs, so keep minimal info
                    # Migration data focuses on replication status rather than machine specs
                
                # Always check discoveryData for additional info (especially IP addresses and detailed specs)
                if discovery_data and len(discovery_data) > 0:
                    latest_discovery = discovery_data[0]  # Use first item in discoveryData
                    
                    # If we didn't get info from migrationData, use discoveryData as primary source
                    if not migration_data:
                        display_name = latest_discovery.get('machineName', machine_name)
                        os_info = latest_discovery.get('osName') or latest_discovery.get('osType')
                        fqdn = latest_discovery.get('fqdn')
                    
                    # Always get IP addresses from discoveryData (more reliable source)
                    discovery_ips = latest_discovery.get('ipAddresses', [])
                    if discovery_ips:
                        ip_addresses = discovery_ips
                    
                    # Get FQDN from discovery if not already set
                    if not fqdn:
                        fqdn = latest_discovery.get('fqdn')
                    
                    # Extract boot type from extendedInfo
                    extended_info = latest_discovery.get('extendedInfo', {})
                    if not boot_type:
                        boot_type = extended_info.get('bootType')
                    
                    # Extract memory and cores from memory details (only from discoveryData)
                    memory_details = extended_info.get('memoryDetails')
                    if memory_details:
                        try:
                            import json
                            memory_info = json.loads(memory_details)
                            memory_mb = memory_info.get('AllocatedMemoryInMB')
                            cores = memory_info.get('NumberOfProcessorCore')
                        except:
                            pass
                    
                    # Extract disk information (only from discoveryData)
                    disk_details = extended_info.get('diskDetails') or extended_info.get('disks')
                    if disk_details:
                        try:
                            import json
                            disks = json.loads(disk_details) if isinstance(disk_details, str) else disk_details
                        except:
                            disks = []
                
                # Add discovery status information
                machine_info = {
                    "name": machine_name,
                    "display_name": display_name,
                    "boot_type": boot_type,
                    "operating_system": os_info,
                    "cores": cores,
                    "memory_mb": memory_mb,
                    "disks": disks,
                    "ip_addresses": ip_addresses,  # IP addresses from discoveryData
                    "fqdn": fqdn,  # FQDN from discoveryData or migrationData
                    "id": machine.get('id', ''),
                    "discovery_records": len(discovery_data),
                    "assessment_records": len(assessment_data),
                    "migration_records": len(migration_data),
                    "migration_ready": len(migration_data) > 0,
                    "raw_properties": properties  # Keep full properties for debugging
                }
                
                machines.append(machine_info)

            return machines

        except Exception as e:
            console.print(
                f"[yellow]⚠ Error getting discovered machines: {str(e)}[/yellow]")
            return []



    def enable_replication(
        self,
        config: MigrationConfig,
        project: AzureMigrateProject,
        cache: ReplicationCache
    ) -> Dict:
        """
        Enable replication for a machine

        Args:
            config: MigrationConfig object
            project: AzureMigrateProject object
            cache: ReplicationCache configuration

        Returns:
            Dictionary with replication status
        """
        try:
            # This is a placeholder for the actual replication enablement
            # The actual implementation would use Azure Site Recovery APIs
            # which require additional SDK packages

            console.print(
                f"[yellow]⚠ Replication enablement is not yet implemented for '{config.machine_name}'[/yellow]"
            )

            return {
                "machine_name": config.machine_name,
                "status": "pending",
                "message": "Replication API integration pending",
                "project": project.name,
                "cache": cache.name
            }

        except Exception as e:
            console.print(f"[red]Error enabling replication: {str(e)}[/red]")
            return {
                "machine_name": config.machine_name,
                "status": "failed",
                "error": str(e)
            }


class RecoveryServicesIntegration:
    """Integration with Azure Site Recovery for replication"""

    def __init__(self, credential: Optional[TokenCredential] = None):
        if credential is None:
            raise ValueError(
                "Credential is required. Use CachedCredentialFactory.create_credential() to get cached credentials.")
        self.credential = credential

    def validate_recovery_vault_rbac(
        self,
        subscription_id: str,
        resource_group: str,
        vault_name: str,
        user_object_id: str
    ) -> ValidationResult:
        """
        Validate user has Contributor role on Recovery Services Vault

        Args:
            subscription_id: Azure subscription ID
            resource_group: Resource group name
            vault_name: Recovery Services Vault name
            user_object_id: User's object ID in Azure AD

        Returns:
            ValidationResult
        """
        try:
            from azure.mgmt.authorization import AuthorizationManagementClient
            from azure.mgmt.recoveryservices import RecoveryServicesClient

            # Get vault
            vault_client = RecoveryServicesClient(
                self.credential, subscription_id)
            vault = vault_client.vaults.get(resource_group, vault_name)

            # Check RBAC
            auth_client = AuthorizationManagementClient(
                self.credential, subscription_id)
            role_assignments = auth_client.role_assignments.list_for_scope(
                scope=vault.id, # pyright: ignore[reportArgumentType]
                filter=f"principalId eq '{user_object_id}'"
            )

            contributor_role_id = AZURE_ROLE_IDS["Contributor"]
            owner_role_id = AZURE_ROLE_IDS["Owner"]

            has_access = False
            for assignment in role_assignments:
                role_id = assignment.role_definition_id.split('/')[-1] # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
                if role_id in [contributor_role_id, owner_role_id]:
                    has_access = True
                    break

            if has_access:
                return ValidationResult(
                    stage=ValidationStage.RBAC_RECOVERY_VAULT,
                    passed=True,
                    message=f"User has Contributor/Owner access to Recovery Vault '{vault_name}'",
                    details={"vault_name": vault_name, "vault_id": vault.id}
                )
            else:
                return ValidationResult(
                    stage=ValidationStage.RBAC_RECOVERY_VAULT,
                    passed=False,
                    message=f"User does not have Contributor/Owner access to Recovery Vault '{vault_name}'",
                    details={"vault_name": vault_name}
                )

        except ResourceNotFoundError:
            return ValidationResult(
                stage=ValidationStage.RBAC_RECOVERY_VAULT,
                passed=False,
                message=f"Recovery Services Vault '{vault_name}' not found",
                details={"vault_name": vault_name,
                         "resource_group": resource_group}
            )
        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.RBAC_RECOVERY_VAULT,
                passed=False,
                message=f"Error validating Recovery Vault RBAC: {str(e)}",
                details={"error": str(e)}
            )
