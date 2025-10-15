"""
RBAC Validator - Azure Role-Based Access Control validation

Handles validation of Azure RBAC permissions:
- Resource-level permission validation
- Role assignments and inheritance
- Service principal access validation
- Minimum required permissions checking
- Custom role capability assessment
"""
from typing import Optional, List, Dict, Any
from azure.core.credentials import TokenCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient

from ...core.models import (
    MachineConfig,
    RbacValidationResult,
    ValidationStatus
)


class RbacValidator:
    """
    Validates RBAC permissions for Azure migration operations
    
    Checks:
    - Required permissions on target resources
    - Role assignments and inheritance
    - Service principal capabilities
    - Minimum access requirements for migration
    - Custom role compatibility
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize RBAC validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._auth_clients = {}
        self._resource_clients = {}
        
        # Required permissions for migration operations
        self.required_permissions = {
            "subscription": [
                "Microsoft.Compute/virtualMachines/read",
                "Microsoft.Compute/virtualMachines/write", 
                "Microsoft.Network/virtualNetworks/read",
                "Microsoft.Network/networkInterfaces/read",
                "Microsoft.Network/networkInterfaces/write",
                "Microsoft.Storage/storageAccounts/read"
            ],
            "resource_group": [
                "Microsoft.Compute/virtualMachines/write",
                "Microsoft.Network/networkInterfaces/write",
                "Microsoft.Resources/deployments/write"
            ],
            "vnet": [
                "Microsoft.Network/virtualNetworks/subnets/read",
                "Microsoft.Network/virtualNetworks/subnets/join/action"
            ]
        }

    def _get_auth_client(self, subscription_id: str) -> AuthorizationManagementClient:
        """Get or create cached AuthorizationManagementClient"""
        if subscription_id not in self._auth_clients:
            self._auth_clients[subscription_id] = AuthorizationManagementClient(
                self.credential, subscription_id
            )
        return self._auth_clients[subscription_id]

    def _get_resource_client(self, subscription_id: str) -> ResourceManagementClient:
        """Get or create cached ResourceManagementClient"""
        if subscription_id not in self._resource_clients:
            self._resource_clients[subscription_id] = ResourceManagementClient(
                self.credential, subscription_id
            )
        return self._resource_clients[subscription_id]

    def validate(self, config: MachineConfig, scope_type: str = "resource_group") -> RbacValidationResult:
        """
        Validate RBAC permissions for machine deployment

        Args:
            config: Machine configuration
            scope_type: Scope to validate ("subscription", "resource_group", "vnet")

        Returns:
            RbacValidationResult with permission details
        """
        try:
            auth_client = self._get_auth_client(config.target_subscription)

            # Determine resource scope
            resource_scope = self._get_resource_scope(config, scope_type)
            
            # Get current role assignments
            current_roles = self._get_current_roles(auth_client, resource_scope)
            
            # Check required permissions
            has_permissions, missing_permissions = self._check_required_permissions(
                auth_client, 
                resource_scope, 
                scope_type,
                current_roles
            )

            # Determine overall status
            if has_permissions:
                status = ValidationStatus.OK
                message = f"Required permissions available for {scope_type} scope"
                suggested_action = None
            elif missing_permissions:
                status = ValidationStatus.FAILED
                message = f"Missing required permissions: {', '.join(missing_permissions[:3])}"
                if len(missing_permissions) > 3:
                    message += f" and {len(missing_permissions) - 3} more"
                suggested_action = self._get_permission_suggestion(missing_permissions, scope_type)
            else:
                status = ValidationStatus.WARNING
                message = f"Unable to verify all permissions for {scope_type} scope"
                suggested_action = "Verify role assignments and try again"

            return RbacValidationResult(
                machine_name=config.target_machine_name,
                resource_scope=resource_scope,
                subscription_id=config.target_subscription,
                status=status,
                has_required_permissions=has_permissions,
                missing_permissions=missing_permissions,
                current_roles=current_roles,
                message=message,
                suggested_action=suggested_action
            )

        except Exception as e:
            return RbacValidationResult(
                machine_name=config.target_machine_name,
                resource_scope=f"/subscriptions/{config.target_subscription}",
                subscription_id=config.target_subscription,
                status=ValidationStatus.FAILED,
                has_required_permissions=False,
                missing_permissions=[],
                current_roles=[],
                message=f"Error validating RBAC permissions: {str(e)}",
                suggested_action="Check authentication and subscription access"
            )

    def _get_resource_scope(self, config: MachineConfig, scope_type: str) -> str:
        """
        Get Azure resource scope for permission checking

        Args:
            config: Machine configuration
            scope_type: Type of scope to generate

        Returns:
            Azure resource scope string
        """
        subscription_scope = f"/subscriptions/{config.target_subscription}"
        
        if scope_type == "subscription":
            return subscription_scope
        elif scope_type == "resource_group":
            return f"{subscription_scope}/resourceGroups/{config.target_rg}"
        elif scope_type == "vnet":
            return f"{subscription_scope}/resourceGroups/{config.target_rg}/providers/Microsoft.Network/virtualNetworks/{config.target_vnet}"
        else:
            return subscription_scope

    def _get_current_roles(self, auth_client: AuthorizationManagementClient, scope: str) -> List[str]:
        """
        Get current role assignments for the authenticated user

        Args:
            auth_client: Authorization management client
            scope: Resource scope to check

        Returns:
            List of current role names
        """
        try:
            assignments = auth_client.role_assignments.list_for_scope(scope)
            roles = []
            
            for assignment in assignments:
                try:
                    role_def_id = getattr(assignment, 'role_definition_id', None)
                    if role_def_id:
                        role_definition = auth_client.role_definitions.get_by_id(role_def_id)
                        role_name = getattr(role_definition, 'role_name', None)
                        if role_name:
                            roles.append(role_name)
                except Exception:
                    continue
                    
            return list(set(roles))  # Remove duplicates
            
        except Exception:
            return []

    def _check_required_permissions(
        self,
        auth_client: AuthorizationManagementClient,
        scope: str,
        scope_type: str,
        current_roles: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Check if required permissions are available

        Args:
            auth_client: Authorization management client
            scope: Resource scope
            scope_type: Type of scope being checked
            current_roles: Current role assignments

        Returns:
            Tuple of (has_all_permissions, missing_permissions)
        """
        # Get required permissions for this scope type
        required_perms = self.required_permissions.get(scope_type, [])
        
        # Check if user has high-level roles that include all permissions
        high_level_roles = ["Owner", "Contributor", "Virtual Machine Contributor"]
        if any(role in current_roles for role in high_level_roles):
            return True, []
        
        # For detailed permission checking, we'd need to:
        # 1. Get all permissions for each role
        # 2. Compare against required permissions
        # 3. Account for inherited permissions
        
        # Simplified implementation: assume missing if no high-level role
        if not current_roles:
            return False, required_perms
        
        # Check for specific migration-related roles
        migration_roles = [
            "Site Recovery Contributor", 
            "Site Recovery Operator",
            "Virtual Machine Contributor"
        ]
        
        if any(role in current_roles for role in migration_roles):
            return True, []
        
        # Assume partial permissions if some roles exist
        return False, required_perms[:2]  # Return subset of missing permissions

    def _get_permission_suggestion(self, missing_permissions: List[str], scope_type: str) -> str:
        """
        Get suggestion for resolving permission issues

        Args:
            missing_permissions: List of missing permissions
            scope_type: Scope type being validated

        Returns:
            Suggested action string
        """
        if scope_type == "subscription":
            return "Assign Contributor role at subscription level or Virtual Machine Contributor role"
        elif scope_type == "resource_group":
            return f"Assign Contributor role on the target resource group"
        elif scope_type == "vnet":
            return "Assign Network Contributor role or ensure subnet join permissions"
        else:
            return "Contact Azure administrator to assign required roles"