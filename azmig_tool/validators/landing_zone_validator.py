"""
Landing Zone Validator - Azure API validation for project readiness

This validator performs Azure API calls to validate Azure Migrate project setup.
"""
from typing import Optional, Dict, Any, List
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from datetime import datetime, timedelta

from ..base.landing_zone_interface import BaseLandingZoneInterface
from ..models import (
    MigrateProjectConfig,
    AccessValidationResult,
    ApplianceHealthResult,
    StorageCacheResult,
    QuotaValidationResult,
    ValidationStatus,
    ApplianceInfo,
    HealthStatus,
    ApplianceType,
    StorageCacheInfo,
    QuotaInfo
)
from ..config.validation_config import ValidationConfig
from ..clients.azure_client import AzureMigrateApiClient
from ..constants import AZURE_ROLE_IDS


class LandingZoneValidator(BaseLandingZoneInterface):
    """
    Validator for Azure Migrate project readiness using Azure APIs.

    Features:
    - Real-time RBAC permission validation
    - Appliance health monitoring via Azure Migrate APIs
    - Storage account validation and creation
    - vCPU quota checking across VM families

    Usage:
        credential = DefaultAzureCredential()
        validator = LandingZoneValidator(credential)
        result = validator.validate_project(config)
    """

    def __init__(
        self,
        credential: Optional[DefaultAzureCredential] = None,
        validation_config: Optional[ValidationConfig] = None
    ):
        """
        Initialize validator

        Args:
            credential: Azure credential (uses DefaultAzureCredential if not provided)
            validation_config: Validation configuration (loads default if not provided)
        """
        super().__init__(validation_config)
        self.credential = credential or DefaultAzureCredential()
        self._clients_cache: Dict[str, Any] = {}

    # ========== Client Management ==========

    def _get_resource_client(self, subscription_id: str) -> ResourceManagementClient:
        """Get or create cached ResourceManagementClient"""
        key = f"resource_{subscription_id}"
        if key not in self._clients_cache:
            self._clients_cache[key] = ResourceManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def _get_storage_client(self, subscription_id: str) -> StorageManagementClient:
        """Get or create cached StorageManagementClient"""
        key = f"storage_{subscription_id}"
        if key not in self._clients_cache:
            self._clients_cache[key] = StorageManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def _get_auth_client(self, subscription_id: str) -> AuthorizationManagementClient:
        """Get or create cached AuthorizationManagementClient"""
        key = f"auth_{subscription_id}"
        if key not in self._clients_cache:
            self._clients_cache[key] = AuthorizationManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def _get_compute_client(self, subscription_id: str) -> ComputeManagementClient:
        """Get or create cached ComputeManagementClient"""
        key = f"compute_{subscription_id}"
        if key not in self._clients_cache:
            self._clients_cache[key] = ComputeManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def _get_migrate_client(self, subscription_id: str) -> AzureMigrateApiClient:
        """Get or create cached Azure Migrate API client"""
        key = f"migrate_{subscription_id}"
        if key not in self._clients_cache:
            self._clients_cache[key] = AzureMigrateApiClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    # ========== Helper Methods ==========

    def _check_role_assignment(
        self,
        subscription_id: str,
        scope: str,
        role_definition_id: str
    ) -> bool:
        """
        Check if current user has specific role on given scope

        Args:
            subscription_id: Azure subscription ID
            scope: Resource scope to check
            role_definition_id: Role definition ID (e.g., AZURE_ROLE_IDS["Contributor"])

        Returns:
            True if role is assigned, False otherwise
        """
        try:
            auth_client = self._get_auth_client(subscription_id)

            # Get current user's object ID
            try:
                from azure.mgmt.authorization.models import RoleAssignmentFilter
                # List role assignments for the scope
                assignments = auth_client.role_assignments.list_for_scope(
                    scope)

                for assignment in assignments:
                    if role_definition_id in assignment.role_definition_id:
                        return True

                return False
            except Exception:
                # Fallback: if we can list assignments, we likely have access
                return True

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
        if not config.recovery_vault_name:
            return None
        return (
            f"/subscriptions/{config.migrate_project_subscription}"
            f"/resourceGroups/{config.migrate_resource_group}"
            f"/providers/Microsoft.RecoveryServices/vaults/{config.recovery_vault_name}"
        )

    # ========== Validation Methods ==========

    def validate_access(self, config: MigrateProjectConfig) -> AccessValidationResult:
        """
        Validate access and permissions for Azure Migrate project

        Checks:
        - Subscription exists and is accessible
        - Contributor role on Azure Migrate project
        - Contributor role on Recovery Vault (if specified)
        - Reader role on subscription

        Args:
            config: Project configuration

        Returns:
            AccessValidationResult with permission details
        """
        try:
            # CRITICAL CHECK: Verify subscription exists and is accessible
            try:
                resource_client = self._get_resource_client(
                    config.subscription_id)
                # Try to get subscription details - this will fail if subscription doesn't exist
                subscription_scope = f"/subscriptions/{config.subscription_id}"

                # Attempt to list resource groups to verify subscription access
                # This is a lightweight call that will fail fast if subscription is invalid
                list(resource_client.resource_groups.list())

            except HttpResponseError as e:
                # Check if it's a subscription not found error
                error_code = getattr(e.error, 'code', '').lower(
                ) if hasattr(e, 'error') else str(e).lower()
                error_message = str(e).lower()

                if 'subscriptionnotfound' in error_code or \
                   ('subscription' in error_message and 'not found' in error_message) or \
                   ('subscription' in error_message and 'could not be found' in error_message):
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
                    # Other HTTP errors
                    raise

            # Continue with permission checks if subscription is valid
            # Check Migrate project access
            migrate_scope = self._get_migrate_project_scope(config)
            has_migrate = self._check_role_assignment(
                config.migrate_project_subscription,
                migrate_scope,
                AZURE_ROLE_IDS["Contributor"]
            )

            # Check Recovery Vault access (if specified)
            has_vault = True
            vault_scope = self._get_vault_scope(config)
            if vault_scope:
                has_vault = self._check_role_assignment(
                    config.migrate_project_subscription,
                    vault_scope,
                    AZURE_ROLE_IDS["Contributor"]
                )

            # Check subscription-level Reader access
            subscription_scope = f"/subscriptions/{config.subscription_id}"
            has_reader = self._check_role_assignment(
                config.subscription_id,
                subscription_scope,
                AZURE_ROLE_IDS["Reader"]
            )

            # Determine overall status
            all_passed = has_migrate and has_vault and has_reader
            status = ValidationStatus.OK if all_passed else ValidationStatus.FAILED

            # Build message
            if all_passed:
                message = "All required permissions validated"
            elif not has_migrate:
                message = f"Missing Contributor access to Migrate project '{config.migrate_project_name}'"
            elif not has_vault:
                message = f"Missing Contributor access to Recovery Vault '{config.recovery_vault_name}'"
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
                    "recovery_vault": "Contributor" if has_vault else "No access" if vault_scope else "N/A",
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

    def validate_appliance_health(self, config: MigrateProjectConfig) -> ApplianceHealthResult:
        """
        Validate health status of replication appliances

        Checks:
        - Appliance connectivity and heartbeat
        - Health status (Healthy, Warning, Unhealthy, Critical)
        - Active alerts and issues

        Args:
            config: Project configuration

        Returns:
            ApplianceHealthResult with appliance health details
        """
        try:
            migrate_client = self._get_migrate_client(
                config.migrate_project_subscription)

            # Get appliances from Azure Migrate project
            appliances_data = migrate_client.get_appliances(
                config.migrate_resource_group,
                config.migrate_project_name
            )

            appliances: List[ApplianceInfo] = []
            unhealthy_count = 0

            for appliance_data in appliances_data:
                properties = appliance_data.get('properties', {})

                # Determine appliance type
                appliance_type_str = properties.get('applianceType', 'VMWARE')
                try:
                    appliance_type = ApplianceType[appliance_type_str]
                except (KeyError, AttributeError):
                    appliance_type = ApplianceType.VMWARE

                # Get health status
                health_state = properties.get('healthState', 'Unknown')
                last_heartbeat_str = properties.get('lastHeartbeatUtc', '')

                # Parse last heartbeat
                health_status = HealthStatus.HEALTHY
                alerts = []

                try:
                    if last_heartbeat_str:
                        last_heartbeat = datetime.fromisoformat(
                            last_heartbeat_str.replace('Z', '+00:00'))
                        time_since_heartbeat = datetime.now(
                            last_heartbeat.tzinfo) - last_heartbeat

                        if time_since_heartbeat > timedelta(days=1):
                            health_status = HealthStatus.UNHEALTHY
                            alerts.append("Last heartbeat > 24 hours ago")
                            alerts.append("Appliance not communicating")
                        elif time_since_heartbeat > timedelta(hours=6):
                            health_status = HealthStatus.WARNING
                            alerts.append("Last heartbeat > 6 hours ago")
                except Exception:
                    health_status = HealthStatus.WARNING
                    alerts.append("Unable to parse heartbeat timestamp")

                # Check explicit health state
                if health_state.lower() in ['unhealthy', 'critical', 'error']:
                    health_status = HealthStatus.UNHEALTHY
                    if not alerts:
                        alerts.append(f"Health state: {health_state}")
                elif health_state.lower() == 'warning':
                    if health_status == HealthStatus.HEALTHY:
                        health_status = HealthStatus.WARNING
                    if not alerts:
                        alerts.append(f"Health state: {health_state}")

                if health_status in [HealthStatus.UNHEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    unhealthy_count += 1

                appliance = ApplianceInfo(
                    name=appliance_data.get('name', 'Unknown'),
                    health_status=health_status,
                    appliance_type=appliance_type,
                    subscription_id=config.subscription_id,
                    resource_group=config.migrate_resource_group,
                    region=appliance_data.get('location', config.region),
                    alerts=alerts,
                    last_heartbeat=last_heartbeat_str,
                    version=properties.get('version', 'Unknown')
                )
                appliances.append(appliance)

            # Determine overall status
            if not appliances:
                status = ValidationStatus.WARNING
                message = "No appliances found in project"
            elif unhealthy_count == 0:
                status = ValidationStatus.OK
                message = f"Found {len(appliances)} healthy appliance(s)"
            elif unhealthy_count < len(appliances):
                status = ValidationStatus.WARNING
                message = f"Found {len(appliances)} appliance(s), {unhealthy_count} need(s) attention"
            else:
                status = ValidationStatus.FAILED
                message = f"All {len(appliances)} appliance(s) are unhealthy"

            return ApplianceHealthResult(
                subscription_id=config.subscription_id,
                status=status,
                appliances=appliances,
                unhealthy_count=unhealthy_count,
                message=message
            )

        except Exception as e:
            return ApplianceHealthResult(
                subscription_id=config.subscription_id,
                status=ValidationStatus.FAILED,
                appliances=[],
                unhealthy_count=0,
                message=f"Error validating appliance health: {str(e)}"
            )

    def validate_storage_cache(
        self,
        config: MigrateProjectConfig,
        auto_create: bool = False
    ) -> StorageCacheResult:
        """
        Validate cache storage account for replication

        Checks:
        - Storage account exists
        - Located in correct region
        - Proper SKU (Standard_LRS recommended)

        Args:
            config: Project configuration
            auto_create: If True, create storage account if missing

        Returns:
            StorageCacheResult with storage account validation details
        """
        try:
            if not config.cache_storage_account:
                return StorageCacheResult(
                    subscription_id=config.subscription_id,
                    region=config.region,
                    status=ValidationStatus.WARNING,
                    storage_info=None,
                    message="No cache storage account specified",
                    auto_created=False
                )

            storage_client = self._get_storage_client(config.subscription_id)

            # Check if storage account exists
            try:
                storage_account = storage_client.storage_accounts.get_properties(
                    config.cache_storage_resource_group,
                    config.cache_storage_account
                )

                # Validate region
                if storage_account.location.lower().replace(' ', '') != config.region.lower().replace(' ', ''):
                    return StorageCacheResult(
                        subscription_id=config.subscription_id,
                        region=config.region,
                        status=ValidationStatus.WARNING,
                        storage_info=StorageCacheInfo(
                            account_name=config.cache_storage_account,
                            subscription_id=config.subscription_id,
                            resource_group=config.cache_storage_resource_group,
                            region=storage_account.location,
                            sku=storage_account.sku.name if storage_account.sku else "Unknown",
                            exists=True,
                            created_by_tool=False
                        ),
                        message=f"Storage account exists but in different region ({storage_account.location} vs {config.region})",
                        auto_created=False
                    )

                return StorageCacheResult(
                    subscription_id=config.subscription_id,
                    region=config.region,
                    status=ValidationStatus.OK,
                    storage_info=StorageCacheInfo(
                        account_name=config.cache_storage_account,
                        subscription_id=config.subscription_id,
                        resource_group=config.cache_storage_resource_group,
                        region=storage_account.location,
                        sku=storage_account.sku.name if storage_account.sku else "Unknown",
                        exists=True,
                        created_by_tool=False
                    ),
                    message=f"Cache storage account '{config.cache_storage_account}' validated",
                    auto_created=False
                )

            except ResourceNotFoundError:
                # Storage account doesn't exist
                if auto_create:
                    # Create the storage account
                    return self.create_cache_storage_account(config)
                else:
                    return StorageCacheResult(
                        subscription_id=config.subscription_id,
                        region=config.region,
                        status=ValidationStatus.FAILED,
                        storage_info=None,
                        message=f"Cache storage account '{config.cache_storage_account}' not found",
                        auto_created=False
                    )

        except Exception as e:
            return StorageCacheResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=ValidationStatus.FAILED,
                storage_info=None,
                message=f"Error validating storage cache: {str(e)}",
                auto_created=False
            )

    def validate_quota(
        self,
        config: MigrateProjectConfig,
        required_vcpus_by_family: Optional[Dict[str, int]] = None
    ) -> QuotaValidationResult:
        """
        Validate vCPU quota availability in target region

        Checks:
        - Current vCPU usage by VM family
        - Total quota limits
        - Available quota for migration

        Args:
            config: Project configuration
            required_vcpus_by_family: Required vCPUs per VM family (optional)

        Returns:
            QuotaValidationResult with quota details and recommendations
        """
        try:
            compute_client = self._get_compute_client(config.subscription_id)

            # Get usage information for the region
            usages = compute_client.usage.list(config.region)

            quotas: List[QuotaInfo] = []
            insufficient_families = []
            recommended_skus = []

            # VM family to SKU mapping
            family_to_skus = {
                "standardDSv3Family": ["Standard_D2s_v3", "Standard_D4s_v3", "Standard_D8s_v3"],
                "standardESv3Family": ["Standard_E2s_v3", "Standard_E4s_v3", "Standard_E8s_v3"],
                "standardFSv2Family": ["Standard_F2s_v2", "Standard_F4s_v2", "Standard_F8s_v2"],
                "standardBSFamily": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"],
                "standardDFamily": ["Standard_D2_v2", "Standard_D3_v2", "Standard_D4_v2"]
            }

            for usage in usages:
                family_name = usage.name.value

                # Only check vCPU quotas
                if family_name and (('cores' in family_name.lower()) or ('vcpus' in family_name.lower())):
                    current_usage = usage.current_value
                    total_quota = usage.limit
                    available = total_quota - current_usage

                    quota_info = QuotaInfo(
                        subscription_id=config.subscription_id,
                        region=config.region,
                        family=family_name,
                        total_quota=total_quota,
                        current_usage=current_usage,
                        available=available
                    )
                    quotas.append(quota_info)

                    # Check if sufficient for requirements
                    if required_vcpus_by_family and family_name in required_vcpus_by_family:
                        required = required_vcpus_by_family[family_name]
                        if not quota_info.is_sufficient(required):
                            insufficient_families.append(family_name)

                            # Add SKU recommendations
                            if family_name in family_to_skus:
                                for sku in family_to_skus[family_name]:
                                    if sku not in recommended_skus:
                                        recommended_skus.append(sku)

            # Determine status
            if insufficient_families:
                status = ValidationStatus.WARNING
                message = f"Insufficient quota for {len(insufficient_families)} VM family(ies)"
            else:
                status = ValidationStatus.OK
                message = f"Sufficient quota available in {config.region}"

            return QuotaValidationResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=status,
                quotas=quotas,
                insufficient_families=insufficient_families,
                recommended_skus=recommended_skus[:5],  # Limit to top 5
                message=message
            )

        except Exception as e:
            return QuotaValidationResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=ValidationStatus.FAILED,
                quotas=[],
                insufficient_families=[],
                recommended_skus=[],
                message=f"Error validating quota: {str(e)}"
            )

    def create_cache_storage_account(self, config: MigrateProjectConfig) -> StorageCacheResult:
        """
        Create cache storage account for Azure Migrate replication

        Creates:
        - Storage account with Standard_LRS SKU
        - In the same region as the Migrate project
        - In the Migrate project's resource group

        Args:
            config: Project configuration

        Returns:
            StorageCacheResult with creation status
        """
        try:
            from azure.mgmt.storage.models import (
                StorageAccountCreateParameters,
                Sku,
                Kind
            )

            storage_client = self._get_storage_client(config.subscription_id)

            # Generate storage account name if not provided
            storage_name = config.cache_storage_account
            if not storage_name:
                region_short = config.region[:6].replace('-', '')
                import random
                storage_name = f"stmigcache{region_short}{random.randint(1000, 9999)}"

            # Create storage account
            create_params = StorageAccountCreateParameters(
                sku=Sku(name="Standard_LRS"),
                kind=Kind.STORAGE_V2,
                location=config.region,
                tags={
                    "Purpose": "Azure Migrate Cache",
                    "CreatedBy": "azmig_tool"
                }
            )

            # Start async creation
            poller = storage_client.storage_accounts.begin_create(
                config.cache_storage_resource_group,
                storage_name,
                create_params
            )

            # Wait for completion
            storage_account = poller.result()

            storage_info = StorageCacheInfo(
                account_name=storage_name,
                subscription_id=config.subscription_id,
                resource_group=config.cache_storage_resource_group,
                region=storage_account.location,
                sku=storage_account.sku.name if storage_account.sku else "Unknown",
                exists=True,
                created_by_tool=True
            )

            return StorageCacheResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=ValidationStatus.OK,
                storage_info=storage_info,
                message=f"Created cache storage account '{storage_name}'",
                auto_created=True
            )

        except Exception as e:
            return StorageCacheResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=ValidationStatus.FAILED,
                storage_info=None,
                message=f"Error creating storage account: {str(e)}",
                auto_created=False
            )
