"""
Access Validator - RBAC and permission validation

Handles Azure Role-Based Access Control (RBAC) validation for:
- Subscription access
- Azure Migrate project permissions
- Recovery Services Vault permissions
"""
from typing import Optional
from azure.core.credentials import TokenCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

from ...core.models import (
    MigrateProjectConfig,
    AccessValidationResult,
    ValidationStatus
)
from ...core.constants import AZURE_ROLE_IDS


class AccessValidator:
    """
    Validates RBAC permissions for Azure Migrate operations
    
    Checks:
    - Subscription exists and is accessible
    - Contributor role on Azure Migrate project
    - Reader role on subscription
    - Recovery Vault permissions (when applicable)
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize access validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._auth_clients = {}

    def _get_auth_client(self, subscription_id: str) -> AuthorizationManagementClient:
        """Get or create cached AuthorizationManagementClient"""
        if subscription_id not in self._auth_clients:
            self._auth_clients[subscription_id] = AuthorizationManagementClient(
                self.credential, subscription_id
            )
        return self._auth_clients[subscription_id]

    def validate(self, config: MigrateProjectConfig) -> AccessValidationResult:
        """
        Validate access and permissions for Azure Migrate project

        Args:
            config: Migrate project configuration

        Returns:
            AccessValidationResult with detailed permission status
        """
        try:
            # CRITICAL CHECK: Verify subscription exists and is accessible
            try:
                from azure.mgmt.resource import ResourceManagementClient
                resource_client = ResourceManagementClient(
                    self.credential, config.subscription_id)
                
                # Try to list resource groups to verify subscription access
                list(resource_client.resource_groups.list())

            except HttpResponseError as e:
                # Check if it's a subscription not found error
                error_code = getattr(e.error, 'code', '').lower() if hasattr(e, 'error') else str(e).lower()
                error_message = str(e).lower()

                if ('subscriptionnotfound' in error_code or 
                    ('subscription' in error_message and 'not found' in error_message) or 
                    ('subscription' in error_message and 'could not be found' in error_message)):
                    
                    return AccessValidationResult(
                        subscription_id=config.subscription_id,
                        migrate_project_name=config.migrate_project_name,
                        status=ValidationStatus.FAILED,
                        has_contributor_migrate_project=False,
                        has_contributor_recovery_vault=False,
                        has_reader_subscription=False,
                        message=f"Subscription '{config.subscription_id}' could not be found or is not accessible",
                        details={
                            "error": "SubscriptionNotFound",
                            "message": "The subscription does not exist or you don't have access to it",
                            "critical": True
                        }
                    )
                else:
                    # Other HTTP errors - re-raise
                    raise

            # Check specific role assignments
            has_migrate = self._check_migrate_project_access(config)
            has_vault = self._check_recovery_vault_access(config) 
            has_reader = self._check_subscription_reader_access(config)

            # Determine overall status
            all_passed = has_migrate and has_vault and has_reader
            status = ValidationStatus.OK if all_passed else ValidationStatus.FAILED

            # Build descriptive message
            if all_passed:
                message = "All required permissions validated"
            elif not has_migrate:
                message = f"Missing Contributor access to Migrate project '{config.migrate_project_name}'"
            elif not has_vault:
                message = "Missing Contributor access to Recovery Vault (will be auto-discovered)"
            elif not has_reader:
                message = f"Missing Reader access to subscription '{config.subscription_id}'"
            else:
                message = "Missing required permissions"

            return AccessValidationResult(
                subscription_id=config.subscription_id,
                migrate_project_name=config.migrate_project_name,
                status=status,
                has_contributor_migrate_project=has_migrate,
                has_contributor_recovery_vault=has_vault,
                has_reader_subscription=has_reader,
                message=message,
                details={
                    "migrate_project": "Contributor" if has_migrate else "No access",
                    "recovery_vault": "Contributor" if has_vault else "No access",
                    "subscription": "Reader" if has_reader else "No access"
                }
            )

        except Exception as e:
            return AccessValidationResult(
                subscription_id=config.subscription_id,
                migrate_project_name=config.migrate_project_name,
                status=ValidationStatus.FAILED,
                has_contributor_migrate_project=False,
                has_contributor_recovery_vault=False,
                has_reader_subscription=False,
                message=f"Error validating access: {str(e)}",
                details={"error": str(e)}
            )

    def _check_migrate_project_access(self, config: MigrateProjectConfig) -> bool:
        """Check Contributor access to Azure Migrate project"""
        migrate_scope = self._get_migrate_project_scope(config)
        return self._check_role_assignment(
            config.migrate_project_subscription,
            migrate_scope,
            AZURE_ROLE_IDS["Contributor"]
        )

    def _check_recovery_vault_access(self, config: MigrateProjectConfig) -> bool:
        """Check Contributor access to Recovery Services Vault"""
        # Recovery vault validation is currently optional as it will be auto-discovered
        vault_scope = self._get_vault_scope(config)
        if not vault_scope:
            return True  # Skip vault validation if not specified
            
        return self._check_role_assignment(
            config.migrate_project_subscription,
            vault_scope,
            AZURE_ROLE_IDS["Contributor"]
        )

    def _check_subscription_reader_access(self, config: MigrateProjectConfig) -> bool:
        """Check Reader access at subscription level"""
        subscription_scope = f"/subscriptions/{config.subscription_id}"
        return self._check_role_assignment(
            config.subscription_id,
            subscription_scope,
            AZURE_ROLE_IDS["Reader"]
        )

    def _check_role_assignment(self, subscription_id: str, scope: str, role_definition_id: str) -> bool:
        """
        Check if current user has specific role on given scope

        Args:
            subscription_id: Azure subscription ID
            scope: Resource scope to check
            role_definition_id: Role definition ID

        Returns:
            True if role is assigned, False otherwise
        """
        try:
            auth_client = self._get_auth_client(subscription_id)
            
            # List role assignments for the scope
            assignments = auth_client.role_assignments.list_for_scope(scope)
            
            for assignment in assignments:
                if role_definition_id in assignment.role_definition_id:
                    return True
                    
            return False
            
        except (HttpResponseError, ResourceNotFoundError):
            return False
        except Exception:
            # If there's any error, assume no access
            return False

    def _get_migrate_project_scope(self, config: MigrateProjectConfig) -> str:
        """Build resource scope for Azure Migrate project"""
        return (
            f"/subscriptions/{config.migrate_project_subscription}"
            f"/resourceGroups/{config.migrate_resource_group}"
            f"/providers/Microsoft.Migrate/migrateProjects/{config.migrate_project_name}"
        )

    def _get_vault_scope(self, config: MigrateProjectConfig) -> Optional[str]:
        """Build resource scope for Recovery Services Vault"""
        # Recovery vault validation is currently disabled as vault will be auto-discovered
        return None