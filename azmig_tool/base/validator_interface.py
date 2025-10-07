"""
Base Validator Interface - Contract for servers (machine-level) validation

This interface defines the contract that both Mock and Live validators must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..models import MigrationConfig, ValidationResult, AzureMigrateProject
from ..config.validation_config import ValidationConfig, get_validation_config


class BaseValidatorInterface(ABC):
    """Abstract base class for machine-level validators"""

    def __init__(self, validation_config: Optional[ValidationConfig] = None):
        """
        Initialize validator with optional validation configuration

        Args:
            validation_config: Validation configuration (loads default if not provided)
        """
        self.validation_config = validation_config or get_validation_config()

    @abstractmethod
    def validate_region(self, config: MigrationConfig) -> ValidationResult:
        """
        Validate Azure region exists

        Args:
            config: Migration configuration

        Returns:
            ValidationResult with pass/fail status
        """
        pass

    @abstractmethod
    def validate_resource_group(self, config: MigrationConfig) -> ValidationResult:
        """
        Validate that resource group exists

        Args:
            config: Migration configuration

        Returns:
            ValidationResult with pass/fail status
        """
        pass

    @abstractmethod
    def validate_vnet_and_subnet(self, config: MigrationConfig) -> ValidationResult:
        """
        Validate that VNet and Subnet exist

        Args:
            config: Migration configuration

        Returns:
            ValidationResult with pass/fail status
        """
        pass

    @abstractmethod
    def validate_vm_sku(self, config: MigrationConfig) -> ValidationResult:
        """
        Validate that VM SKU is available in the target region

        Args:
            config: Migration configuration

        Returns:
            ValidationResult with pass/fail status
        """
        pass

    @abstractmethod
    def validate_disk_type(self, config: MigrationConfig) -> ValidationResult:
        """
        Validate disk type is valid

        Args:
            config: Migration configuration

        Returns:
            ValidationResult with pass/fail status
        """
        pass

    @abstractmethod
    def validate_rbac_resource_group(
        self,
        config: MigrationConfig,
        user_object_id: str
    ) -> ValidationResult:
        """
        Validate user has Contributor role on target resource group

        Args:
            config: Migration configuration
            user_object_id: Azure AD user object ID

        Returns:
            ValidationResult with pass/fail status
        """
        pass

    @abstractmethod
    def validate_discovery(
        self,
        config: MigrationConfig,
        project: AzureMigrateProject
    ) -> ValidationResult:
        """
        Validate machine is discovered in Azure Migrate project

        Args:
            config: Migration configuration
            project: Azure Migrate project information

        Returns:
            ValidationResult with pass/fail status
        """
        pass

    def validate_all(
        self,
        configs: List[MigrationConfig],
        project: Optional[AzureMigrateProject] = None,
        user_object_id: Optional[str] = None
    ) -> Dict[str, List[ValidationResult]]:
        """
        Run all enabled validations for a list of migration configurations

        Args:
            configs: List of migration configurations to validate
            project: Azure Migrate project (optional)
            user_object_id: User's Azure AD object ID (optional)

        Returns:
            Dictionary mapping machine names to their validation results
        """
        results = {}

        for config in configs:
            machine_results = []

            # Region validation
            if self.validation_config.is_region_validation_enabled():
                machine_results.append(self.validate_region(config))

            # Resource Group validation
            if self.validation_config.is_resource_group_validation_enabled():
                machine_results.append(self.validate_resource_group(config))

            # VNet/Subnet validation
            if self.validation_config.is_vnet_subnet_validation_enabled():
                machine_results.append(self.validate_vnet_and_subnet(config))

            # VM SKU validation
            if self.validation_config.is_vm_sku_validation_enabled():
                machine_results.append(self.validate_vm_sku(config))

            # Disk Type validation
            if self.validation_config.is_disk_type_validation_enabled():
                machine_results.append(self.validate_disk_type(config))

            # Discovery validation (requires project)
            if self.validation_config.is_discovery_validation_enabled() and project:
                machine_results.append(
                    self.validate_discovery(config, project))

            # RBAC validation (requires user_object_id)
            if self.validation_config.is_rbac_validation_enabled() and user_object_id:
                machine_results.append(
                    self.validate_rbac_resource_group(config, user_object_id)
                )

            results[config.target_machine_name] = machine_results

        return results
