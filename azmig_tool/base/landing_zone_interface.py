"""
Landing Zone Validator Interface - Contract for project-level validation

This interface defines the contract for Azure Migrate project readiness validation.
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..models import (
    MigrateProjectConfig,
    AccessValidationResult,
    ApplianceHealthResult,
    StorageCacheResult,
    QuotaValidationResult,
    ProjectReadinessResult,
    ValidationStatus
)
from ..config.validation_config import ValidationConfig, get_validation_config


class BaseLandingZoneInterface(ABC):
    """
    Base interface for Landing Zone (Azure Migrate Project) validators.

    This validator checks project-level readiness before machine-level validation.
    """

    def __init__(self, validation_config: Optional[ValidationConfig] = None):
        """
        Initialize validator with optional validation configuration

        Args:
            validation_config: Validation configuration (loads default if not provided)
        """
        self.validation_config = validation_config or get_validation_config()

    @abstractmethod
    def validate_access(self, config: MigrateProjectConfig) -> AccessValidationResult:
        """
        Validate access and permissions for Azure Migrate project

        Checks:
        - Contributor role on Azure Migrate project
        - Contributor role on Recovery Vault (if specified)
        - Reader role on subscription

        Args:
            config: Project configuration

        Returns:
            AccessValidationResult with permission details
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def validate_storage_cache(self, config: MigrateProjectConfig) -> StorageCacheResult:
        """
        Validate cache storage account for replication

        Checks:
        - Storage account exists
        - Located in correct region
        - Proper access permissions

        Args:
            config: Project configuration

        Returns:
            StorageCacheResult with storage account validation details
        """
        pass

    @abstractmethod
    def validate_quota(self, config: MigrateProjectConfig) -> QuotaValidationResult:
        """
        Validate vCPU quota availability in target region

        Checks:
        - Current vCPU usage
        - Quota limits
        - Available quota for migration

        Args:
            config: Project configuration

        Returns:
            QuotaValidationResult with quota details
        """
        pass

    def validate_project(self, config: MigrateProjectConfig) -> ProjectReadinessResult:
        """
        Run all enabled project-level validations

        This method orchestrates all Landing Zone validations based on the
        validation configuration settings.

        Implements fail-fast logic: If access validation fails (subscription not found,
        no permissions), remaining validations are skipped since they would also fail.

        Args:
            config: Project configuration

        Returns:
            ProjectReadinessResult with all validation results
        """
        # Initialize results as None
        access_result = None
        appliance_result = None
        storage_result = None
        quota_result = None

        # Run access validation first (critical check)
        if self.validation_config.is_access_validation_enabled():
            access_result = self.validate_access(config)

            # Fail-fast: If access validation failed critically (subscription not found),
            # skip remaining validations as they will also fail
            if access_result and access_result.status == ValidationStatus.FAILED:
                # Check if the error is about subscription not found or no access
                error_message = access_result.message.lower()
                if ('subscription' in error_message and ('not found' in error_message or 'could not be found' in error_message)) or \
                   ('subscriptionnotfound' in error_message.replace(' ', '')):
                    # Critical failure - subscription doesn't exist or no access
                    # Skip all other validations
                    return ProjectReadinessResult(
                        config=config,
                        access_result=access_result,
                        appliance_result=None,
                        storage_result=None,
                        quota_result=None
                    )

        # Continue with remaining validations only if access check passed or wasn't critical
        if self.validation_config.is_appliance_health_enabled():
            appliance_result = self.validate_appliance_health(config)

        if self.validation_config.is_storage_cache_enabled():
            storage_result = self.validate_storage_cache(config)

        if self.validation_config.is_quota_validation_enabled():
            quota_result = self.validate_quota(config)

        return ProjectReadinessResult(
            config=config,
            access_result=access_result,
            appliance_result=appliance_result,
            storage_result=storage_result,
            quota_result=quota_result
        )
