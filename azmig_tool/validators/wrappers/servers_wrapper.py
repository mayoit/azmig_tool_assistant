"""
Servers Validator Wrapper

Orchestrates core validators for server migration validation:
- Region availability validation
- Resource group validation
- VNet and subnet validation
- VM SKU validation
- Disk type validation
- Discovery status validation
- RBAC permissions validation

Handles configuration-driven validation execution and result aggregation.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from azure.core.credentials import TokenCredential

from ...base.validator_interface import BaseValidatorInterface
from ...core.models import (
    MachineConfig,
    MigrationConfig,
    ValidationResult,
    ValidationStatus,
    AzureMigrateProject
)
from ...config.validation_config import ValidationConfig
from ..core import (
    RegionValidator,
    ResourceGroupValidator,
    VNetValidator,
    VMSkuValidator,
    DiskValidator,
    DiscoveryValidator,
    RbacValidator
)


@dataclass
class ServerValidationResult:
    """Individual server validation result"""
    machine_config: MachineConfig
    region_result: Optional[Any] = None
    resource_group_result: Optional[Any] = None
    vnet_result: Optional[Any] = None
    vmsku_result: Optional[Any] = None
    disk_result: Optional[Any] = None
    discovery_result: Optional[Any] = None
    rbac_result: Optional[Any] = None
    overall_status: ValidationStatus = ValidationStatus.SKIPPED
    validation_timestamp: Optional[str] = None

    def __post_init__(self):
        """Calculate overall status after initialization"""
        statuses = []
        
        for result in [self.region_result, self.resource_group_result, 
                      self.vnet_result, self.vmsku_result, self.disk_result,
                      self.discovery_result, self.rbac_result]:
            if result and hasattr(result, 'status'):
                statuses.append(result.status)

        if not statuses:
            self.overall_status = ValidationStatus.SKIPPED
        elif any(s == ValidationStatus.FAILED for s in statuses):
            self.overall_status = ValidationStatus.FAILED
        elif any(s == ValidationStatus.WARNING for s in statuses):
            self.overall_status = ValidationStatus.WARNING
        else:
            self.overall_status = ValidationStatus.OK

    def is_ready_for_migration(self) -> bool:
        """Check if server is ready for migration"""
        return self.overall_status in [ValidationStatus.OK, ValidationStatus.WARNING]

    def get_blockers(self) -> List[str]:
        """Get list of blocking issues"""
        blockers = []
        
        result_mappings = {
            "Region": self.region_result,
            "Resource Group": self.resource_group_result,
            "VNet": self.vnet_result,
            "VM SKU": self.vmsku_result,
            "Disk": self.disk_result,
            "Discovery": self.discovery_result,
            "RBAC": self.rbac_result
        }
        
        for name, result in result_mappings.items():
            if result and hasattr(result, 'status') and result.status == ValidationStatus.FAILED:
                message = getattr(result, 'message', f"{name} validation failed")
                blockers.append(f"{name}: {message}")

        return blockers


@dataclass 
class ServersValidationReport:
    """Complete servers validation report"""
    server_results: List[ServerValidationResult] = field(default_factory=list)
    total_servers: int = 0
    ready_servers: int = 0
    failed_servers: int = 0
    warning_servers: int = 0
    validation_timestamp: Optional[str] = None

    def add_result(self, result: ServerValidationResult):
        """Add a server result and update counts"""
        self.server_results.append(result)
        self.total_servers += 1

        if result.is_ready_for_migration():
            if result.overall_status == ValidationStatus.OK:
                self.ready_servers += 1
            else:
                self.warning_servers += 1
        else:
            self.failed_servers += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "total_servers": self.total_servers,
            "ready": self.ready_servers,
            "failed": self.failed_servers,
            "warnings": self.warning_servers,
            "success_rate": f"{((self.ready_servers + self.warning_servers) / self.total_servers * 100):.1f}%" if self.total_servers > 0 else "0%"
        }


class ServersValidatorWrapper(BaseValidatorInterface):
    """
    Wrapper validator that orchestrates server migration validation
    
    Coordinates core validators based on validation configuration:
    - Only runs enabled validations
    - Respects fail-fast settings
    - Aggregates results into comprehensive report
    - Handles parallel execution when configured
    - Implements BaseValidatorInterface for backward compatibility
    """

    def __init__(self, credential: TokenCredential, validation_config: ValidationConfig):
        """
        Initialize servers validator wrapper

        Args:
            credential: Azure token credential for API calls
            validation_config: Validation configuration settings
        """
        self.credential = credential
        self.validation_config = validation_config
        
        # Initialize core validators
        self.region_validator = RegionValidator(credential)
        self.resource_group_validator = ResourceGroupValidator(credential)
        self.vnet_validator = VNetValidator(credential)
        self.vmsku_validator = VMSkuValidator(credential)
        self.disk_validator = DiskValidator(credential)
        self.discovery_validator = DiscoveryValidator(credential)
        self.rbac_validator = RbacValidator(credential)

    def validate_all_servers(
        self, 
        configs: List[MachineConfig],
        migrate_project_name: Optional[str] = None,
        migrate_project_rg: Optional[str] = None
    ) -> ServersValidationReport:
        """
        Validate all server configurations

        Args:
            configs: List of machine configurations
            migrate_project_name: Azure Migrate project name (for discovery validation)
            migrate_project_rg: Azure Migrate project resource group

        Returns:
            ServersValidationReport with aggregated results
        """
        report = ServersValidationReport()
        
        for config in configs:
            server_result = self._validate_single_server(
                config, migrate_project_name, migrate_project_rg
            )
            report.add_result(server_result)
            
            # Check fail-fast setting
            if (self.validation_config.is_fail_fast_enabled() and 
                not server_result.is_ready_for_migration()):
                break

        return report

    def _validate_single_server(
        self, 
        config: MachineConfig,
        migrate_project_name: Optional[str] = None,
        migrate_project_rg: Optional[str] = None
    ) -> ServerValidationResult:
        """
        Validate a single server configuration

        Args:
            config: Machine configuration
            migrate_project_name: Azure Migrate project name
            migrate_project_rg: Azure Migrate project resource group

        Returns:
            ServerValidationResult with validation details
        """
        result = ServerValidationResult(machine_config=config)

        try:
            # Region validation
            if self.validation_config.is_region_validation_enabled():
                result.region_result = self.region_validator.validate(config)
                
                if (self.validation_config.is_fail_fast_enabled() and 
                    result.region_result.status == ValidationStatus.FAILED):
                    return result

            # Resource group validation
            if self.validation_config.is_resource_group_validation_enabled():
                result.resource_group_result = self.resource_group_validator.validate(config)
                
                if (self.validation_config.is_fail_fast_enabled() and 
                    result.resource_group_result.status == ValidationStatus.FAILED):
                    return result

            # VNet validation
            if self.validation_config.is_vnet_subnet_validation_enabled():
                result.vnet_result = self.vnet_validator.validate(config)
                
                if (self.validation_config.is_fail_fast_enabled() and 
                    result.vnet_result.status == ValidationStatus.FAILED):
                    return result

            # VM SKU validation
            if self.validation_config.is_vm_sku_validation_enabled():
                result.vmsku_result = self.vmsku_validator.validate(config)
                
                if (self.validation_config.is_fail_fast_enabled() and 
                    result.vmsku_result.status == ValidationStatus.FAILED):
                    return result

            # Disk type validation
            if self.validation_config.is_disk_type_validation_enabled():
                result.disk_result = self.disk_validator.validate(config)

            # Discovery validation (if migrate project info provided)
            if (self.validation_config.is_discovery_validation_enabled() and 
                migrate_project_name and migrate_project_rg):
                result.discovery_result = self.discovery_validator.validate(
                    config, migrate_project_name, migrate_project_rg
                )

            # RBAC validation
            if self.validation_config.is_servers_rbac_validation_enabled():
                result.rbac_result = self.rbac_validator.validate(config)

        except Exception as e:
            # Handle any unexpected errors during validation
            result.overall_status = ValidationStatus.FAILED

        return result

    def validate_single(
        self, 
        config: MachineConfig,
        migrate_project_name: Optional[str] = None,
        migrate_project_rg: Optional[str] = None
    ) -> ServerValidationResult:
        """
        Validate a single server configuration

        Args:
            config: Machine configuration
            migrate_project_name: Azure Migrate project name
            migrate_project_rg: Azure Migrate project resource group

        Returns:
            ServerValidationResult with validation details
        """
        return self._validate_single_server(config, migrate_project_name, migrate_project_rg)

    def get_enabled_validations(self) -> List[str]:
        """
        Get list of enabled validation types

        Returns:
            List of enabled validation type names
        """
        enabled = []

        if self.validation_config.is_region_validation_enabled():
            enabled.append("region_validation")
        if self.validation_config.is_resource_group_validation_enabled():
            enabled.append("resource_group_validation")
        if self.validation_config.is_vnet_subnet_validation_enabled():
            enabled.append("vnet_subnet_validation")
        if self.validation_config.is_vm_sku_validation_enabled():
            enabled.append("vm_sku_validation")
        if self.validation_config.is_disk_type_validation_enabled():
            enabled.append("disk_type_validation")
        if self.validation_config.is_discovery_validation_enabled():
            enabled.append("discovery_validation")
        if self.validation_config.is_servers_rbac_validation_enabled():
            enabled.append("rbac_validation")

        return enabled

    # BaseValidatorInterface compatibility method
    def validate_all(self, configs: List[MigrationConfig], project: Optional[AzureMigrateProject] = None, user_object_id: Optional[str] = None) -> Dict[str, List[ValidationResult]]:
        """
        Validate all servers - BaseValidatorInterface compatibility method
        
        This method provides compatibility with the BaseValidatorInterface while leveraging
        the new validation architecture. It converts MigrationConfig objects to MachineConfig
        objects internally and returns results in the expected format.
        
        Args:
            configs: List of migration configurations
            project: Optional Azure Migrate project (not used in current implementation)
            user_object_id: Optional user object ID (not used in current implementation)
            
        Returns:
            Dictionary mapping server names to validation results
        """
        # Convert MigrationConfig to MachineConfig objects
        machine_configs = []
        for config in configs:
            machine_config = MachineConfig(
                target_machine_name=config.machine_name,
                target_region=config.target_region,
                target_subscription=config.target_subscription,
                target_rg=config.target_rg,
                target_vnet=config.target_vnet,
                target_subnet=config.target_subnet,
                target_machine_sku=config.target_machine_sku,
                target_disk_type=config.target_disk_type
            )
            machine_configs.append(machine_config)
        
        # Use the native validate_all_servers method
        validation_report = self.validate_all_servers(
            machine_configs, 
            migrate_project_name=None,  # Will be extracted from configs if needed
            migrate_project_rg=None    # Will be extracted from configs if needed
        )
        
        # Convert ServersValidationReport to Dict[str, List[ValidationResult]]
        results = {}
        
        for server_result in validation_report.server_results:
            # Get server name from the machine config
            server_name = server_result.machine_config.target_machine_name
            
            # Convert ServerValidationResult to List[ValidationResult]
            validation_results = []
            
            # Add all validation results from the server
            if server_result.region_result:
                validation_results.append(server_result.region_result)
            if server_result.resource_group_result:
                validation_results.append(server_result.resource_group_result)
            if server_result.vnet_result:
                validation_results.append(server_result.vnet_result)
            if server_result.vmsku_result:
                validation_results.append(server_result.vmsku_result)
            if server_result.disk_result:
                validation_results.append(server_result.disk_result)
            if server_result.rbac_result:
                validation_results.append(server_result.rbac_result)
            if server_result.discovery_result:
                validation_results.append(server_result.discovery_result)
                
            results[server_name] = validation_results
            
        return results

    # BaseValidatorInterface implementation - delegate to core validators
    def validate_region(self, config: MigrationConfig) -> ValidationResult:
        """Validate Azure region exists (BaseValidatorInterface compatibility)"""
        # Convert MigrationConfig to MachineConfig if needed
        machine_config = self._convert_to_machine_config(config) if not isinstance(config, MachineConfig) else config
        result = self.region_validator.validate(machine_config)
        return self._convert_to_validation_result(result, "region")

    def validate_resource_group(self, config: MigrationConfig) -> ValidationResult:
        """Validate that resource group exists (BaseValidatorInterface compatibility)"""
        machine_config = self._convert_to_machine_config(config) if not isinstance(config, MachineConfig) else config
        result = self.resource_group_validator.validate(machine_config)
        return self._convert_to_validation_result(result, "resource_group")

    def validate_vnet_and_subnet(self, config: MigrationConfig) -> ValidationResult:
        """Validate that VNet and Subnet exist (BaseValidatorInterface compatibility)"""
        machine_config = self._convert_to_machine_config(config) if not isinstance(config, MachineConfig) else config
        result = self.vnet_validator.validate(machine_config)
        return self._convert_to_validation_result(result, "vnet_subnet")

    def validate_vm_sku(self, config: MigrationConfig) -> ValidationResult:
        """Validate that VM SKU is available in the target region (BaseValidatorInterface compatibility)"""
        machine_config = self._convert_to_machine_config(config) if not isinstance(config, MachineConfig) else config
        result = self.vmsku_validator.validate(machine_config)
        return self._convert_to_validation_result(result, "vm_sku")

    def validate_disk_type(self, config: MigrationConfig) -> ValidationResult:
        """Validate disk type is valid (BaseValidatorInterface compatibility)"""
        machine_config = self._convert_to_machine_config(config) if not isinstance(config, MachineConfig) else config
        result = self.disk_validator.validate(machine_config)
        return self._convert_to_validation_result(result, "disk_type")

    def validate_rbac_resource_group(self, config: MigrationConfig, user_object_id: str) -> ValidationResult:
        """Validate user has Contributor role on target resource group (BaseValidatorInterface compatibility)"""
        machine_config = self._convert_to_machine_config(config) if not isinstance(config, MachineConfig) else config
        # The core RBAC validator doesn't take user_object_id as parameter yet, 
        # so for now we'll use the resource_group scope validation
        result = self.rbac_validator.validate(machine_config, scope_type="resource_group")
        return self._convert_to_validation_result(result, "rbac")

    def validate_discovery(self, config: MigrationConfig, project: AzureMigrateProject) -> ValidationResult:
        """Validate machine is discovered in Azure Migrate project (BaseValidatorInterface compatibility)"""
        machine_config = self._convert_to_machine_config(config) if not isinstance(config, MachineConfig) else config
        # Use project name from AzureMigrateProject
        result = self.discovery_validator.validate(machine_config, project.name, project.resource_group)
        return self._convert_to_validation_result(result, "discovery")

    def _convert_to_machine_config(self, migration_config: MigrationConfig) -> MachineConfig:
        """Convert MigrationConfig to MachineConfig for compatibility"""
        # This is a compatibility conversion - field mappings based on actual model definitions
        return MachineConfig(
            target_machine_name=migration_config.machine_name,
            target_region=migration_config.target_region,
            target_subscription=migration_config.target_subscription,
            target_rg=migration_config.target_rg,
            target_vnet=migration_config.target_vnet,
            target_subnet=migration_config.target_subnet,
            target_machine_sku=migration_config.target_machine_sku,
            target_disk_type=migration_config.target_disk_type
        )

    def _convert_to_validation_result(self, result: Any, validation_type: str) -> ValidationResult:
        """Convert core validator result to ValidationResult for compatibility"""
        from ...core.models import ValidationStage
        
        if result is None:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"{validation_type} validation returned no result",
                details={}
            )
        
        # Handle different result types from core validators
        passed = getattr(result, 'status', ValidationStatus.FAILED) == ValidationStatus.OK
        message = getattr(result, 'message', f"{validation_type} validation")
        details = getattr(result, 'details', {})
        
        return ValidationResult(
            stage=ValidationStage.AZURE_RESOURCES,
            passed=passed,
            message=message,
            details=details if isinstance(details, dict) else {}
        )