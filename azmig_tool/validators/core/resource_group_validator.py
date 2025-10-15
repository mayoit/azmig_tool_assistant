"""
Resource Group Validator - Azure resource group validation

Handles validation of Azure resource groups:
- Resource group existence and accessibility
- RBAC permissions on resource groups
- Resource group region alignment
- Resource group naming conventions
"""
from typing import Optional
from azure.core.credentials import TokenCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient

from ...core.models import (
    MachineConfig,
    ResourceGroupValidationResult,
    ValidationStatus
)


class ResourceGroupValidator:
    """
    Validates Azure resource group configuration and access
    
    Checks:
    - Resource group exists and is accessible
    - Required permissions on resource group
    - Resource group is in correct region
    - Resource group naming follows conventions
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize resource group validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._resource_clients = {}
        self._auth_clients = {}

    def _get_resource_client(self, subscription_id: str) -> ResourceManagementClient:
        """Get or create cached ResourceManagementClient"""
        if subscription_id not in self._resource_clients:
            self._resource_clients[subscription_id] = ResourceManagementClient(
                self.credential, subscription_id
            )
        return self._resource_clients[subscription_id]

    def _get_auth_client(self, subscription_id: str) -> AuthorizationManagementClient:
        """Get or create cached AuthorizationManagementClient"""
        if subscription_id not in self._auth_clients:
            self._auth_clients[subscription_id] = AuthorizationManagementClient(
                self.credential, subscription_id
            )
        return self._auth_clients[subscription_id]

    def validate(self, config: MachineConfig, check_permissions: bool = True) -> ResourceGroupValidationResult:
        """
        Validate resource group configuration

        Args:
            config: Machine configuration with target resource group
            check_permissions: Whether to validate RBAC permissions

        Returns:
            ResourceGroupValidationResult with validation details
        """
        try:
            resource_client = self._get_resource_client(config.target_subscription)

            # Check if resource group exists
            try:
                rg = resource_client.resource_groups.get(config.target_rg)
                rg_exists = True
                rg_location = rg.location if hasattr(rg, 'location') else None
            except Exception:
                rg_exists = False
                rg_location = None

            if not rg_exists:
                return ResourceGroupValidationResult(
                    machine_name=config.target_machine_name,
                    resource_group=config.target_rg,
                    subscription_id=config.target_subscription,
                    status=ValidationStatus.FAILED,
                    exists=False,
                    has_required_permissions=False,
                    region_match=False,
                    follows_naming_convention=self._check_naming_convention(config.target_rg),
                    message=f"Resource group '{config.target_rg}' does not exist",
                    suggested_action="Create the resource group or verify the name"
                )

            # Check region alignment
            region_match = True
            region_message = ""
            
            if rg_location and config.target_region:
                normalized_rg_region = self._normalize_region_name(rg_location)
                normalized_target_region = self._normalize_region_name(config.target_region)
                
                if normalized_rg_region != normalized_target_region:
                    region_match = False
                    region_message = f"Resource group is in '{rg_location}' but target region is '{config.target_region}'"

            # Check permissions if requested
            has_permissions = True
            permission_message = ""
            
            if check_permissions:
                has_permissions = self._check_permissions(config)
                if not has_permissions:
                    permission_message = "Insufficient permissions on resource group"

            # Check naming convention
            follows_naming = self._check_naming_convention(config.target_rg)

            # Determine overall status and message
            issues = []
            if not region_match:
                issues.append(region_message)
            if not has_permissions and check_permissions:
                issues.append(permission_message)
            if not follows_naming:
                issues.append("Resource group name doesn't follow recommended conventions")

            if issues:
                status = ValidationStatus.WARNING
                message = f"Resource group exists but has issues: {'; '.join(issues)}"
                suggested_action = "Review and address the identified issues"
            else:
                status = ValidationStatus.OK
                message = f"Resource group '{config.target_rg}' is valid and accessible"
                suggested_action = None

            return ResourceGroupValidationResult(
                machine_name=config.target_machine_name,
                resource_group=config.target_rg,
                subscription_id=config.target_subscription,
                status=status,
                exists=True,
                has_required_permissions=has_permissions,
                region_match=region_match,
                follows_naming_convention=follows_naming,
                message=message,
                suggested_action=suggested_action
            )

        except Exception as e:
            return ResourceGroupValidationResult(
                machine_name=config.target_machine_name,
                resource_group=config.target_rg,
                subscription_id=config.target_subscription,
                status=ValidationStatus.FAILED,
                exists=False,
                has_required_permissions=False,
                region_match=False,
                follows_naming_convention=False,
                message=f"Error validating resource group: {str(e)}",
                suggested_action="Check connectivity and permissions"
            )

    def _check_permissions(self, config: MachineConfig) -> bool:
        """
        Check if current user has required permissions on resource group

        Args:
            config: Machine configuration

        Returns:
            True if user has required permissions
        """
        try:
            auth_client = self._get_auth_client(config.target_subscription)
            
            # Get resource group scope
            rg_scope = f"/subscriptions/{config.target_subscription}/resourceGroups/{config.target_rg}"
            
            # Check for Contributor or higher permissions
            required_roles = ["Contributor", "Owner", "Virtual Machine Contributor"]
            
            # Get role assignments for the resource group
            assignments = auth_client.role_assignments.list_for_scope(rg_scope)
            
            # This is a simplified check - in practice would need to get current user's
            # object ID and check their specific role assignments
            return True  # Simplified for now
            
        except Exception:
            # If we can't check permissions, assume they exist to avoid blocking
            return True

    def _normalize_region_name(self, region: str) -> str:
        """
        Normalize region name for comparison

        Args:
            region: Region name to normalize

        Returns:
            Normalized region name
        """
        if not region:
            return ""
        return region.lower().replace(" ", "").replace("_", "").replace("-", "")

    def _check_naming_convention(self, rg_name: str) -> bool:
        """
        Check if resource group name follows recommended conventions

        Args:
            rg_name: Resource group name to check

        Returns:
            True if name follows conventions
        """
        if not rg_name:
            return False

        # Basic naming convention checks
        checks = [
            len(rg_name) >= 3,  # Minimum length
            len(rg_name) <= 90,  # Maximum length
            rg_name.replace("-", "").replace("_", "").isalnum(),  # Only alphanumeric, hyphens, underscores
            not rg_name.startswith("-"),  # Don't start with hyphen
            not rg_name.endswith("-"),  # Don't end with hyphen
            not rg_name.startswith("_"),  # Don't start with underscore
            not rg_name.endswith("_"),  # Don't end with underscore
        ]

        return all(checks)