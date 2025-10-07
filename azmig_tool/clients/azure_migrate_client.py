"""
Azure Migrate integration for discovery and replication enablement
"""
from typing import List, Optional, Dict
from azure.identity import DefaultAzureCredential
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

    def __init__(self, credential: Optional[DefaultAzureCredential] = None):
        self.credential = credential or DefaultAzureCredential()
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

                machines.append({
                    "name": machine.get('name', ''),
                    "display_name": properties.get('displayName', machine.get('name', '')),
                    "boot_type": properties.get('bootType'),
                    "operating_system": properties.get('operatingSystemType') or properties.get('operatingSystemName'),
                    "cores": properties.get('numberOfCores') or properties.get('cores'),
                    "memory_mb": properties.get('megabytesOfMemory') or properties.get('memoryInMB'),
                    "disks": properties.get('disks', []),
                    "id": machine.get('id', '')
                })

            return machines

        except Exception as e:
            console.print(
                f"[yellow]⚠ Error getting discovered machines: {str(e)}[/yellow]")
            return []

    def validate_machine_discovered(
        self,
        config: MigrationConfig,
        project: AzureMigrateProject
    ) -> ValidationResult:
        """
        Validate that source machine is discovered in Azure Migrate project

        Args:
            config: MigrationConfig object
            project: AzureMigrateProject to search in

        Returns:
            ValidationResult
        """
        try:
            discovered_machines = self.get_discovered_machines(project)

            # Use source_machine_name if provided, otherwise use target_machine_name
            search_name = config.source_machine_name or config.target_machine_name

            # Search for machine in discovered list
            found_machine = None
            for machine in discovered_machines:
                if (machine['name'].lower() == search_name.lower() or
                        machine.get('display_name', '').lower() == search_name.lower()):
                    found_machine = machine
                    break

            if found_machine:
                return ValidationResult(
                    stage=ValidationStage.MIGRATE_DISCOVERY,
                    passed=True,
                    message=f"Machine '{search_name}' found in Azure Migrate project '{project.name}'",
                    details={
                        "machine_name": search_name,
                        "project": project.name,
                        "machine_id": found_machine['id'],
                        "os": found_machine.get('operating_system'),
                        "cores": found_machine.get('cores'),
                        "memory_mb": found_machine.get('memory_mb')
                    }
                )
            else:
                available_machines = [m['name']
                                      for m in discovered_machines[:10]]
                return ValidationResult(
                    stage=ValidationStage.MIGRATE_DISCOVERY,
                    passed=False,
                    message=f"Machine '{search_name}' not found in Azure Migrate project '{project.name}'",
                    details={
                        "machine_name": search_name,
                        "project": project.name,
                        "discovered_count": len(discovered_machines),
                        "sample_machines": available_machines
                    }
                )

        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.MIGRATE_DISCOVERY,
                passed=False,
                message=f"Error validating machine discovery: {str(e)}",
                details={"error": str(e)}
            )

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
                f"[yellow]⚠ Replication enablement is not yet implemented for '{config.target_machine_name}'[/yellow]"
            )

            return {
                "machine_name": config.target_machine_name,
                "status": "pending",
                "message": "Replication API integration pending",
                "project": project.name,
                "cache": cache.name
            }

        except Exception as e:
            console.print(f"[red]Error enabling replication: {str(e)}[/red]")
            return {
                "machine_name": config.target_machine_name,
                "status": "failed",
                "error": str(e)
            }


class RecoveryServicesIntegration:
    """Integration with Azure Site Recovery for replication"""

    def __init__(self, credential: Optional[DefaultAzureCredential] = None):
        self.credential = credential or DefaultAzureCredential()

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
                scope=vault.id,
                filter=f"principalId eq '{user_object_id}'"
            )

            contributor_role_id = AZURE_ROLE_IDS["Contributor"]
            owner_role_id = AZURE_ROLE_IDS["Owner"]

            has_access = False
            for assignment in role_assignments:
                role_id = assignment.role_definition_id.split('/')[-1]
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
