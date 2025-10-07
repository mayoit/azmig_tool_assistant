"""
Mock Landing Zone Validator - Simulates Azure Migrate project validation without API calls

This validator simulates all Landing Zone validation checks for offline testing.
"""
import random
from typing import List, Dict, Optional

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


class MockLandingZoneValidator(BaseLandingZoneInterface):
    """
    Mock validator for offline testing of Landing Zone (Project Readiness) validations.

    Features:
    - Configurable success rate for testing different scenarios
    - Realistic simulation of Azure Migrate project checks
    - No Azure connectivity required

    Usage:
        validator = MockLandingZoneValidator(success_rate=0.8)
        result = validator.validate_project(config)
    """

    def __init__(self, success_rate: float = 0.9, validation_config: Optional[ValidationConfig] = None):
        """
        Initialize mock validator

        Args:
            success_rate: Probability of validations passing (0.0 to 1.0)
            validation_config: Validation configuration (loads default if not provided)
        """
        super().__init__(validation_config)
        self.success_rate = success_rate

    def _should_pass(self) -> bool:
        """Randomly determine if validation should pass based on success_rate"""
        return random.random() < self.success_rate

    def validate_access(self, config: MigrateProjectConfig) -> AccessValidationResult:
        """
        Mock access validation - simulates RBAC permission checks

        Simulates checking:
        - Contributor role on Azure Migrate project
        - Contributor role on Recovery Vault (if specified)
        - Reader role on subscription
        """
        # Simulate permission checks
        has_migrate = self._should_pass()
        has_vault = self._should_pass() if config.recovery_vault_name else True
        has_reader = self._should_pass()

        all_passed = has_migrate and has_vault and has_reader

        status = ValidationStatus.OK if all_passed else ValidationStatus.FAILED
        message = "All required permissions validated" if all_passed else "Missing required permissions"

        if not has_migrate:
            message = f"No Contributor access to Migrate project '{config.migrate_project_name}'"
        elif not has_vault:
            message = f"No Contributor access to Recovery Vault '{config.recovery_vault_name}'"
        elif not has_reader:
            message = f"No Reader access to subscription '{config.subscription_id}'"

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

    def validate_appliance_health(self, config: MigrateProjectConfig) -> ApplianceHealthResult:
        """
        Mock appliance health validation - simulates replication appliance monitoring

        Simulates:
        - Finding 1-3 appliances per project
        - Random health statuses (Healthy, Warning, Unhealthy, Critical)
        - Realistic alerts for unhealthy appliances
        """
        # Simulate finding 1-3 appliances
        appliance_count = random.randint(1, 3)
        appliances = []
        unhealthy_count = 0

        for i in range(appliance_count):
            # Random health status weighted towards healthy
            health_statuses = [
                HealthStatus.HEALTHY, HealthStatus.HEALTHY, HealthStatus.HEALTHY,
                HealthStatus.WARNING, HealthStatus.UNHEALTHY
            ]
            health = random.choice(health_statuses)

            if health in [HealthStatus.UNHEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]:
                unhealthy_count += 1

            # Generate realistic alerts based on health
            alerts = []
            if health == HealthStatus.UNHEALTHY:
                alerts = [
                    "Appliance not communicating",
                    "Last heartbeat > 24 hours ago"
                ]
            elif health == HealthStatus.WARNING:
                alerts = ["High memory usage detected"]
            elif health == HealthStatus.CRITICAL:
                alerts = [
                    "Appliance offline",
                    "Critical service failure",
                    "Immediate attention required"
                ]

            appliance = ApplianceInfo(
                name=f"{config.appliance_name}-{i+1}" if appliance_count > 1 else config.appliance_name,
                health_status=health,
                appliance_type=config.appliance_type_enum,
                subscription_id=config.subscription_id,
                resource_group=config.migrate_resource_group,
                region=config.region,
                alerts=alerts,
                last_heartbeat="2024-10-06T10:30:00Z" if health == HealthStatus.HEALTHY else "2024-10-04T08:15:00Z",
                version="5.0.1"
            )
            appliances.append(appliance)

        # Determine overall status
        if unhealthy_count == 0:
            status = ValidationStatus.OK
        elif unhealthy_count < appliance_count:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAILED

        message = f"Found {appliance_count} appliance(s)"
        if unhealthy_count > 0:
            message += f", {unhealthy_count} need(s) attention"

        return ApplianceHealthResult(
            subscription_id=config.subscription_id,
            status=status,
            appliances=appliances,
            unhealthy_count=unhealthy_count,
            message=message
        )

    def validate_storage_cache(self, config: MigrateProjectConfig, auto_create: bool = False) -> StorageCacheResult:
        """
        Mock storage cache validation - simulates cache storage account checks

        Simulates:
        - Storage account existence check
        - SKU validation (Standard_LRS)
        - Auto-creation if requested
        """
        # Simulate storage account check (80% exist by default)
        exists = random.random() < 0.8 or not config.cache_storage_account

        if not config.cache_storage_account:
            # No storage account specified
            status = ValidationStatus.WARNING
            message = "No cache storage account specified"
            storage_info = None
        elif exists:
            # Storage account exists
            status = ValidationStatus.OK
            message = f"Cache storage account '{config.cache_storage_account}' found"
            storage_info = StorageCacheInfo(
                account_name=config.cache_storage_account,
                subscription_id=config.subscription_id,
                resource_group=config.migrate_resource_group,
                region=config.region,
                sku="Standard_LRS",
                exists=True,
                created_by_tool=False
            )
        else:
            # Storage account doesn't exist
            status = ValidationStatus.FAILED
            message = f"Cache storage account '{config.cache_storage_account}' not found"
            storage_info = None

            if auto_create:
                # Simulate creation
                storage_info = StorageCacheInfo(
                    account_name=config.cache_storage_account,
                    subscription_id=config.subscription_id,
                    resource_group=config.migrate_resource_group,
                    region=config.region,
                    sku="Standard_LRS",
                    exists=True,
                    created_by_tool=True
                )
                status = ValidationStatus.OK
                message = f"Created cache storage account '{config.cache_storage_account}' (simulated)"

        return StorageCacheResult(
            subscription_id=config.subscription_id,
            region=config.region,
            status=status,
            storage_info=storage_info,
            message=message,
            auto_created=auto_create and not exists
        )

    def validate_quota(
        self,
        config: MigrateProjectConfig,
        required_vcpus_by_family: Optional[Dict[str, int]] = None
    ) -> QuotaValidationResult:
        """
        Mock quota validation - simulates vCPU quota checks

        Simulates:
        - Quota availability for common VM families
        - Current usage vs total quota
        - Recommendations for alternative SKUs when insufficient
        """
        if required_vcpus_by_family is None:
            required_vcpus_by_family = {}

        quotas = []
        insufficient_families = []
        recommended_skus = []

        # Common VM families with SKU options
        common_families = {
            "standardDSv3Family": {"D2s_v3": 2, "D4s_v3": 4, "D8s_v3": 8},
            "standardESv3Family": {"E2s_v3": 2, "E4s_v3": 4, "E8s_v3": 8},
            "standardFSv2Family": {"F2s_v2": 2, "F4s_v2": 4, "F8s_v2": 8},
            "standardBSFamily": {"B2s": 2, "B2ms": 2, "B4ms": 4},
            "standardDFamily": {"D2_v2": 2, "D3_v2": 4, "D4_v2": 8}
        }

        # If no requirements specified, check common families
        if not required_vcpus_by_family:
            required_vcpus_by_family = {
                family: 10 for family in list(common_families.keys())[:3]}

        for family, required in required_vcpus_by_family.items():
            # Simulate quota check with realistic values
            total_quota = random.randint(20, 100)
            current_usage = random.randint(0, int(total_quota * 0.7))
            available = total_quota - current_usage

            quota_info = QuotaInfo(
                subscription_id=config.subscription_id,
                region=config.region,
                family=family,
                total_quota=total_quota,
                current_usage=current_usage,
                available=available
            )
            quotas.append(quota_info)

            if not quota_info.is_sufficient(required):
                insufficient_families.append(family)
                # Suggest alternative SKUs from the same or other families
                if family in common_families:
                    for sku, vcpus in common_families[family].items():
                        if vcpus <= available and sku not in recommended_skus:
                            recommended_skus.append(f"{sku} ({vcpus} vCPUs)")

                # Also suggest from other families if needed
                if len(recommended_skus) < 3:
                    for other_family, skus in common_families.items():
                        if other_family != family:
                            for sku, vcpus in skus.items():
                                if sku not in recommended_skus:
                                    recommended_skus.append(
                                        f"{sku} ({vcpus} vCPUs)")
                                    if len(recommended_skus) >= 3:
                                        break

        status = ValidationStatus.OK if len(
            insufficient_families) == 0 else ValidationStatus.WARNING

        if len(insufficient_families) > 0:
            message = f"Insufficient quota for {len(insufficient_families)} VM family(ies)"
        else:
            message = f"Sufficient quota available in {config.region}"

        return QuotaValidationResult(
            subscription_id=config.subscription_id,
            region=config.region,
            status=status,
            quotas=quotas,
            insufficient_families=insufficient_families,
            # Limit to top 5 recommendations
            recommended_skus=recommended_skus[:5],
            message=message
        )

    def create_cache_storage_account(self, config: MigrateProjectConfig) -> StorageCacheResult:
        """
        Mock storage account creation - simulates creating a cache storage account

        Simulates:
        - Storage account name generation (if not provided)
        - Account creation with Standard_LRS SKU
        - Success confirmation
        """
        # Generate storage account name if not provided
        storage_name = config.cache_storage_account
        if not storage_name:
            # Generate name: stmigcache<region><random>
            region_short = config.region[:6].replace('-', '')
            storage_name = f"stmigcache{region_short}{random.randint(1000, 9999)}"

        storage_info = StorageCacheInfo(
            account_name=storage_name,
            subscription_id=config.subscription_id,
            resource_group=config.migrate_resource_group,
            region=config.region,
            sku="Standard_LRS",
            exists=True,
            created_by_tool=True
        )

        return StorageCacheResult(
            subscription_id=config.subscription_id,
            region=config.region,
            status=ValidationStatus.OK,
            storage_info=storage_info,
            message=f"Created storage account '{storage_name}' (mock mode)",
            auto_created=True
        )
