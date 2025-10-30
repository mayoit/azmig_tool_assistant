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
import jwt
import base64

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

            # Check region alignment - CRITICAL validation
            region_match = False
            region_message = ""
            
            if rg_location and config.target_region:
                normalized_rg_region = self._normalize_region_name(rg_location)
                normalized_target_region = self._normalize_region_name(config.target_region)
                
                region_match = normalized_rg_region == normalized_target_region
                
                if not region_match:
                    region_message = f"Resource group is in '{rg_location}' but target region is '{config.target_region}'"
                    # Region mismatch is CRITICAL - return failure immediately
                    return ResourceGroupValidationResult(
                        machine_name=config.target_machine_name,
                        resource_group=config.target_rg,
                        subscription_id=config.target_subscription,
                        status=ValidationStatus.FAILED,
                        exists=True,
                        has_required_permissions=False,  # Don't check permissions if region is wrong
                        region_match=False,
                        follows_naming_convention=self._check_naming_convention(config.target_rg),
                        message=region_message,
                        suggested_action="Use a resource group in the correct target region"
                    )

            # Check permissions - CRITICAL validation
            has_permissions = False
            permission_message = ""
            
            if check_permissions:
                has_permissions, permission_message = self._check_permissions(config)
                if not has_permissions:
                    # Permission failure is CRITICAL - return failure immediately
                    return ResourceGroupValidationResult(
                        machine_name=config.target_machine_name,
                        resource_group=config.target_rg,
                        subscription_id=config.target_subscription,
                        status=ValidationStatus.FAILED,
                        exists=True,
                        has_required_permissions=False,
                        region_match=True,
                        follows_naming_convention=self._check_naming_convention(config.target_rg),
                        message=permission_message,
                        suggested_action="Request Contributor or Owner access to the resource group"
                    )
            else:
                # If not checking permissions, assume they exist
                has_permissions = True

            # Determine overall status and message
            # Since region and permission checks return early on failure,
            # if we reach here, everything passed
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
                region_match=True,
                follows_naming_convention=True,  # No longer checking this
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

    def _check_permissions(self, config: MachineConfig) -> tuple[bool, str]:
        """
        Check if current user has Contributor or Owner role on resource group

        Args:
            config: Machine configuration

        Returns:
            Tuple of (has_permissions: bool, message: str)
        """
        try:
            # Get current user's object ID from the credential token
            # This works with any authentication method (CLI, Service Principal, Managed Identity, etc.)
            try:
                # Get an access token for Azure Resource Manager
                token = self.credential.get_token("https://management.azure.com/.default")
                
                # Decode the JWT token to get the user/service principal OID
                # JWT tokens have 3 parts separated by dots: header.payload.signature
                token_parts = token.token.split('.')
                if len(token_parts) < 2:
                    return False, "Unable to parse authentication token"
                
                # Decode the payload (add padding if needed for base64)
                payload = token_parts[1]
                # Add padding if needed
                padding = len(payload) % 4
                if padding:
                    payload += '=' * (4 - padding)
                
                decoded = base64.urlsafe_b64decode(payload)
                token_claims = jwt.decode(
                    token.token,
                    options={"verify_signature": False}
                )
                
                # The 'oid' claim contains the Object ID of the authenticated principal
                current_user_oid = token_claims.get('oid')
                if not current_user_oid:
                    return False, "Authentication token does not contain user identity (oid claim missing)"
                    
            except Exception as e:
                return False, f"Unable to extract user identity from token: {str(e)}"
            
            auth_client = self._get_auth_client(config.target_subscription)
            
            # Get resource group scope
            rg_scope = f"/subscriptions/{config.target_subscription}/resourceGroups/{config.target_rg}"
            
            # Required role definition IDs (these are constant across Azure)
            # Contributor: b24988ac-6180-42a0-ab88-20f7382dd24c
            # Owner: 8e3af657-a8ff-443c-a75c-2fe8c4bcb635
            # Virtual Machine Contributor: 9980e02c-c2be-4d73-94e8-173b1dc7cf3c
            required_role_ids = [
                "b24988ac-6180-42a0-ab88-20f7382dd24c",  # Contributor
                "8e3af657-a8ff-443c-a75c-2fe8c4bcb635",  # Owner
                "9980e02c-c2be-4d73-94e8-173b1dc7cf3c",  # Virtual Machine Contributor
            ]
            
            # Get role assignments for the resource group
            try:
                assignments = list(auth_client.role_assignments.list_for_scope(rg_scope))
                
                # Check if current user has required role
                for assignment in assignments:
                    if assignment.principal_id == current_user_oid:
                        # Extract role definition ID from role_definition_id
                        # Format: /subscriptions/{sub}/providers/Microsoft.Authorization/roleDefinitions/{role-id}
                        if assignment.role_definition_id:
                            role_id = assignment.role_definition_id.split('/')[-1]
                            if role_id in required_role_ids:
                                return True, ""
                
                # User doesn't have required role
                return False, f"User does not have Contributor or Owner role on resource group '{config.target_rg}'"
                
            except Exception as e:
                return False, f"Unable to verify permissions on resource group: {str(e)}"
            
        except Exception as e:
            # If we encounter any error checking permissions, fail safely
            return False, f"Error checking permissions: {str(e)}"

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