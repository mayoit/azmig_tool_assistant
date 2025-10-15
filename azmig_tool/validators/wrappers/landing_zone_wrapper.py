"""
Landing Zone Validator Wrapper

Orchestrates core validators for landing zone validation:
- Access validation (RBAC and permissions)
- Appliance health validation
- Storage cache validation  
- Quota validation

Handles configuration-driven validation execution and result aggregation.
"""
from typing import List, Optional, Any
from dataclasses import dataclass, field
from azure.core.credentials import TokenCredential

from ...core.models import (
    MigrateProjectConfig,
    ProjectReadinessResult,
    LandingZoneValidationReport,
    ValidationStatus
)
from ...config.validation_config import ValidationConfig
from ..core import (
    AccessValidator,
    ApplianceValidator,
    StorageValidator,
    QuotaValidator
)


@dataclass
class LandingZoneValidationContext:
    """Context for landing zone validation execution"""
    configs: List[MigrateProjectConfig]
    validation_config: ValidationConfig
    credential: TokenCredential
    parallel_execution: bool = False


class LandingZoneValidatorWrapper:
    """
    Wrapper validator that orchestrates landing zone validation
    
    Coordinates core validators based on validation configuration:
    - Only runs enabled validations
    - Respects fail-fast settings
    - Aggregates results into comprehensive report
    - Handles parallel execution when configured
    """

    def __init__(self, credential: TokenCredential, validation_config: ValidationConfig):
        """
        Initialize landing zone validator wrapper

        Args:
            credential: Azure token credential for API calls
            validation_config: Validation configuration settings
        """
        self.credential = credential
        self.validation_config = validation_config
        
        # Initialize core validators
        self.access_validator = AccessValidator(credential)
        self.appliance_validator = ApplianceValidator(credential)
        self.storage_validator = StorageValidator(credential)
        self.quota_validator = QuotaValidator(credential)

    def validate_all(self, configs: List[MigrateProjectConfig]) -> LandingZoneValidationReport:
        """
        Validate all landing zone configurations

        Args:
            configs: List of migrate project configurations

        Returns:
            LandingZoneValidationReport with aggregated results
        """
        report = LandingZoneValidationReport()
        
        for config in configs:
            project_result = self._validate_single_project(config)
            report.add_result(project_result)
            
            # Check fail-fast setting
            if (self.validation_config.is_fail_fast_enabled() and 
                not project_result.is_ready()):
                break

        return report

    def _validate_single_project(self, config: MigrateProjectConfig) -> ProjectReadinessResult:
        """
        Validate a single migrate project configuration

        Args:
            config: Migrate project configuration

        Returns:
            ProjectReadinessResult with validation details
        """
        result = ProjectReadinessResult(config=config)

        try:
            # Access validation (RBAC and permissions)
            if self.validation_config.is_access_validation_enabled():
                result.access_result = self.access_validator.validate(config)
                
                if (self.validation_config.is_fail_fast_enabled() and 
                    result.access_result and result.access_result.status == ValidationStatus.FAILED):
                    return result

            # Appliance health validation
            if self.validation_config.is_appliance_health_enabled():
                result.appliance_result = self.appliance_validator.validate(config)
                
                if (self.validation_config.is_fail_fast_enabled() and 
                    result.appliance_result and result.appliance_result.status == ValidationStatus.FAILED):
                    return result

            # Storage cache validation
            if self.validation_config.is_storage_cache_enabled():
                auto_create = self.validation_config.should_auto_create_storage()
                result.storage_result = self.storage_validator.validate(config, auto_create)
                
                if (self.validation_config.is_fail_fast_enabled() and 
                    result.storage_result and result.storage_result.status == ValidationStatus.FAILED):
                    return result

            # Quota validation
            if self.validation_config.is_quota_validation_enabled():
                result.quota_result = self.quota_validator.validate(config)

        except Exception as e:
            # Handle any unexpected errors during validation
            result.overall_status = ValidationStatus.FAILED
            # Add error information to the result if needed

        return result

    def validate_single(self, config: MigrateProjectConfig) -> ProjectReadinessResult:
        """
        Validate a single migrate project configuration

        Args:
            config: Migrate project configuration

        Returns:
            ProjectReadinessResult with validation details
        """
        return self._validate_single_project(config)

    def check_prerequisites(self) -> List[str]:
        """
        Check prerequisites for landing zone validation

        Returns:
            List of prerequisite issues (empty if all good)
        """
        issues = []

        # Check credential validity
        try:
            token = self.credential.get_token("https://management.azure.com/.default")
            if not token:
                issues.append("Invalid or expired Azure credentials")
        except Exception:
            issues.append("Unable to authenticate with Azure")

        # Check validation configuration
        if not self.validation_config:
            issues.append("Validation configuration not loaded")

        return issues

    def get_enabled_validations(self) -> List[str]:
        """
        Get list of enabled validation types

        Returns:
            List of enabled validation type names
        """
        enabled = []

        if self.validation_config.is_access_validation_enabled():
            enabled.append("access_validation")
        if self.validation_config.is_appliance_health_enabled():
            enabled.append("appliance_health")
        if self.validation_config.is_storage_cache_enabled():
            enabled.append("storage_cache")
        if self.validation_config.is_quota_validation_enabled():
            enabled.append("quota_validation")

        return enabled

    # Backward compatibility methods for wizard.py
    def validate_access(self, config: MigrateProjectConfig) -> Optional[Any]:
        """
        Validate access permissions for a single project (backward compatibility)
        
        Args:
            config: Migrate project configuration
            
        Returns:
            Validation result or None if validation is disabled
        """
        if not self.validation_config.is_access_validation_enabled():
            return None
            
        return self.access_validator.validate(config)

    def validate_appliance_health(self, config: MigrateProjectConfig) -> Optional[Any]:
        """
        Validate appliance health for a single project (backward compatibility)
        
        Args:
            config: Migrate project configuration
            
        Returns:
            Validation result or None if validation is disabled
        """
        if not self.validation_config.is_appliance_health_enabled():
            return None
            
        return self.appliance_validator.validate(config)

    def validate_storage_cache(self, config: MigrateProjectConfig) -> Optional[Any]:
        """
        Validate storage cache for a single project (backward compatibility)
        
        Args:
            config: Migrate project configuration
            
        Returns:
            Validation result or None if validation is disabled
        """
        if not self.validation_config.is_storage_cache_enabled():
            return None
            
        auto_create = self.validation_config.should_auto_create_storage()
        return self.storage_validator.validate(config, auto_create)

    def validate_quota(self, config: MigrateProjectConfig) -> Optional[Any]:
        """
        Validate quota for a single project (backward compatibility)
        
        Args:
            config: Migrate project configuration
            
        Returns:
            Validation result or None if validation is disabled
        """
        if not self.validation_config.is_quota_validation_enabled():
            return None
            
        return self.quota_validator.validate(config)