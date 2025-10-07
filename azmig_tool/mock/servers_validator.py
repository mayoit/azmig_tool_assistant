"""
Mock Servers Validator - Simulates validation without Azure API calls
"""
import random
from typing import Optional
from ..base.validator_interface import BaseValidatorInterface
from ..models import (
    MigrationConfig,
    ValidationResult,
    ValidationStage,
    AzureMigrateProject,
    DiskType
)
from ..constants import AZURE_REGIONS, DEFAULT_MOCK_SUCCESS_RATE
from ..config.validation_config import ValidationConfig


class MockServersValidator(BaseValidatorInterface):
    """Mock validator for offline testing"""

    def __init__(self, success_rate: float = DEFAULT_MOCK_SUCCESS_RATE, validation_config: Optional[ValidationConfig] = None):
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

    def validate_region(self, config: MigrationConfig) -> ValidationResult:
        """Mock: Validate Azure region"""
        region = config.target_region.lower().replace(" ", "")

        if region in AZURE_REGIONS:
            return ValidationResult(
                stage=ValidationStage.AZURE_REGION,
                passed=True,
                message=f"✓ Region '{config.target_region}' is valid",
                details={"region": region, "mode": "mock"}
            )
        else:
            return ValidationResult(
                stage=ValidationStage.AZURE_REGION,
                passed=False,
                message=f"✗ Invalid region '{config.target_region}'",
                details={
                    "region": region,
                    "mode": "mock",
                    "valid_regions_sample": AZURE_REGIONS[:5]
                }
            )

    def validate_resource_group(self, config: MigrationConfig) -> ValidationResult:
        """Mock: Validate resource group exists"""
        # Simulate: RGs with "invalid" or "bad" in name fail
        if "invalid" in config.target_rg.lower() or "bad" in config.target_rg.lower():
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Resource group '{config.target_rg}' not found (mock)",
                details={"resource_group": config.target_rg, "mode": "mock"}
            )

        return ValidationResult(
            stage=ValidationStage.AZURE_RESOURCES,
            passed=True,
            message=f"✓ Resource group '{config.target_rg}' exists (mock)",
            details={
                "resource_group": config.target_rg,
                "location": config.target_region,
                "mode": "mock"
            }
        )

    def validate_vnet_and_subnet(self, config: MigrationConfig) -> ValidationResult:
        """Mock: Validate VNet and Subnet exist with capacity and delegation checks"""
        # Simulate: VNets with "invalid" in name fail
        if "invalid" in config.target_vnet.lower():
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ VNet '{config.target_vnet}' not found (mock)",
                details={
                    "vnet": config.target_vnet,
                    "mode": "mock"
                }
            )

        # Simulate: Subnets with "invalid" in name fail
        if "invalid" in config.target_subnet.lower():
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Subnet '{config.target_subnet}' not found in VNet '{config.target_vnet}' (mock)",
                details={
                    "vnet": config.target_vnet,
                    "subnet": config.target_subnet,
                    "mode": "mock"
                }
            )

        # Simulate: Subnets with "delegated" in name are delegated to SQL MI
        if "delegated" in config.target_subnet.lower():
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Subnet '{config.target_subnet}' is delegated to 'Microsoft.Sql/managedInstances' and cannot host VMs (mock)",
                details={
                    "vnet": config.target_vnet,
                    "subnet": config.target_subnet,
                    "is_delegated": True,
                    "delegation_service": "Microsoft.Sql/managedInstances",
                    "error": "Delegated subnets cannot host regular virtual machines",
                    "mode": "mock"
                }
            )

        # Simulate: Subnets with "full" in name have no IPs available
        if "full" in config.target_subnet.lower():
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Subnet '{config.target_subnet}' has insufficient IP addresses. Available: 0, Required: 1 (mock)",
                details={
                    "vnet": config.target_vnet,
                    "subnet": config.target_subnet,
                    "subnet_prefix": "10.0.1.0/28",
                    "total_ips": 16,
                    "azure_reserved_ips": 5,
                    "used_ips": 11,
                    "available_ips": 0,
                    "required_ips": 1,
                    "error": "Insufficient IP addresses in subnet",
                    "mode": "mock"
                }
            )

        # Mock: Successful validation with IP availability
        return ValidationResult(
            stage=ValidationStage.AZURE_RESOURCES,
            passed=True,
            message=f"✓ VNet '{config.target_vnet}' and Subnet '{config.target_subnet}' are valid (Available IPs: 246) (mock)",
            details={
                "vnet": config.target_vnet,
                "subnet": config.target_subnet,
                "subnet_prefix": "10.0.1.0/24",  # Mock data
                "is_delegated": False,
                "delegation_service": None,
                "total_ips": 256,
                "azure_reserved_ips": 5,
                "available_ips": 246,
                "used_ips": 5,
                "mode": "mock"
            }
        )

    def validate_vm_sku(self, config: MigrationConfig) -> ValidationResult:
        """Mock: Validate VM SKU availability"""
        # Simulate: SKUs with "invalid" in name fail
        if "invalid" in config.target_machine_sku.lower():
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=False,
                message=f"✗ VM SKU '{config.target_machine_sku}' not available in region '{config.target_region}' (mock)",
                details={
                    "sku": config.target_machine_sku,
                    "region": config.target_region,
                    "mode": "mock"
                }
            )

        # Simulate: Standard SKUs always pass
        return ValidationResult(
            stage=ValidationStage.DISK_AND_SKU,
            passed=True,
            message=f"✓ VM SKU '{config.target_machine_sku}' is available in region '{config.target_region}' (mock)",
            details={
                "sku": config.target_machine_sku,
                "region": config.target_region,
                "cores": 4,  # Mock data
                "memory_gb": 16,  # Mock data
                "mode": "mock"
            }
        )

    def validate_disk_type(self, config: MigrationConfig) -> ValidationResult:
        """Mock: Validate disk type"""
        valid_types = [dt.value for dt in DiskType]

        if config.target_disk_type in valid_types:
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=True,
                message=f"✓ Disk type '{config.target_disk_type}' is valid (mock)",
                details={"disk_type": config.target_disk_type, "mode": "mock"}
            )
        else:
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=False,
                message=f"✗ Invalid disk type '{config.target_disk_type}'. Must be one of: {', '.join(valid_types)} (mock)",
                details={
                    "disk_type": config.target_disk_type,
                    "valid_types": valid_types,
                    "mode": "mock"
                }
            )

    def validate_rbac_resource_group(
        self,
        config: MigrationConfig,
        user_object_id: str
    ) -> ValidationResult:
        """Mock: Validate RBAC on resource group"""
        # Simulate: Random success based on success_rate
        if self._should_pass():
            return ValidationResult(
                stage=ValidationStage.RBAC_TARGET_RG,
                passed=True,
                message=f"✓ User has Contributor access to resource group '{config.target_rg}' (mock)",
                details={
                    "resource_group": config.target_rg,
                    "user_object_id": user_object_id,
                    "role": "Contributor",
                    "mode": "mock"
                }
            )
        else:
            return ValidationResult(
                stage=ValidationStage.RBAC_TARGET_RG,
                passed=False,
                message=f"✗ User does not have Contributor access to resource group '{config.target_rg}' (mock)",
                details={
                    "resource_group": config.target_rg,
                    "user_object_id": user_object_id,
                    "mode": "mock"
                }
            )

    def validate_discovery(
        self,
        config: MigrationConfig,
        project: AzureMigrateProject
    ) -> ValidationResult:
        """Mock: Validate machine discovery in Azure Migrate"""
        search_name = config.source_machine_name or config.target_machine_name

        # Simulate: Machines with "notfound" in name fail
        if "notfound" in search_name.lower():
            return ValidationResult(
                stage=ValidationStage.MIGRATE_DISCOVERY,
                passed=False,
                message=f"✗ Machine '{search_name}' not found in Azure Migrate project '{project.name}' (mock)",
                details={
                    "machine_name": search_name,
                    "project": project.name,
                    "mode": "mock"
                }
            )

        return ValidationResult(
            stage=ValidationStage.MIGRATE_DISCOVERY,
            passed=True,
            message=f"✓ Machine '{search_name}' found in Azure Migrate project '{project.name}' (mock)",
            details={
                "machine_name": search_name,
                "project": project.name,
                "os": "Windows Server 2019",  # Mock data
                "cores": 4,  # Mock data
                "memory_mb": 16384,  # Mock data
                "mode": "mock"
            }
        )
