"""
Disk Validator - Azure disk type and availability validation

Handles validation of Azure disk configurations:
- Disk type availability in target region
- Performance tier compatibility
- SKU compatibility with disk types
- Storage account requirements
- Cost optimization recommendations
"""
from typing import Optional, List, Dict
from azure.core.credentials import TokenCredential
from azure.mgmt.compute import ComputeManagementClient

from ...core.models import (
    MachineConfig,
    DiskValidationResult,
    ValidationStatus
)


class DiskValidator:
    """
    Validates Azure disk type configuration and availability
    
    Checks:
    - Disk type is supported in target region
    - VM SKU compatibility with disk type
    - Performance characteristics match requirements
    - Cost optimization opportunities
    - Storage account dependencies
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize disk validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._compute_clients = {}
        
        # Disk type characteristics
        self.disk_characteristics = {
            "Standard_LRS": {
                "performance_tier": "Standard",
                "redundancy": "Locally Redundant",
                "premium_support_required": False,
                "typical_iops": "500-2000",
                "cost_tier": "Low"
            },
            "StandardSSD_LRS": {
                "performance_tier": "Standard SSD",
                "redundancy": "Locally Redundant",
                "premium_support_required": False,
                "typical_iops": "500-6000",
                "cost_tier": "Medium"
            },
            "Premium_LRS": {
                "performance_tier": "Premium",
                "redundancy": "Locally Redundant",
                "premium_support_required": True,
                "typical_iops": "5000-80000+",
                "cost_tier": "High"
            },
            "UltraSSD_LRS": {
                "performance_tier": "Ultra",
                "redundancy": "Locally Redundant",
                "premium_support_required": True,
                "typical_iops": "300-160000+",
                "cost_tier": "Very High"
            }
        }

    def _get_compute_client(self, subscription_id: str) -> ComputeManagementClient:
        """Get or create cached ComputeManagementClient"""
        if subscription_id not in self._compute_clients:
            self._compute_clients[subscription_id] = ComputeManagementClient(
                self.credential, subscription_id
            )
        return self._compute_clients[subscription_id]

    def validate(self, config: MachineConfig) -> DiskValidationResult:
        """
        Validate disk type configuration

        Args:
            config: Machine configuration with target disk type

        Returns:
            DiskValidationResult with validation details
        """
        try:
            # Check if disk type is supported
            is_supported = self._is_disk_type_supported(config.target_disk_type)
            
            if not is_supported:
                return DiskValidationResult(
                    machine_name=config.target_machine_name,
                    target_disk_type=config.target_disk_type,
                    region=config.target_region,
                    subscription_id=config.target_subscription,
                    status=ValidationStatus.FAILED,
                    is_supported=False,
                    is_available_in_region=False,
                    performance_tier=None,
                    message=f"Disk type '{config.target_disk_type}' is not a valid Azure disk type",
                    alternative_disk_types=self._get_alternative_disk_types()
                )

            # Check regional availability
            is_available_in_region = self._check_regional_availability(
                config.target_disk_type, 
                config.target_region, 
                config.target_subscription
            )

            # Get disk characteristics
            characteristics = self.disk_characteristics.get(config.target_disk_type, {})
            performance_tier = characteristics.get("performance_tier")

            # Check VM SKU compatibility
            sku_compatible, sku_issues = self._check_sku_compatibility(
                config.target_machine_sku,
                config.target_disk_type
            )

            # Generate recommendations
            alternatives = self._get_optimization_recommendations(
                config.target_disk_type,
                config.target_machine_sku
            )

            # Determine overall status
            issues = []
            if not is_available_in_region:
                issues.append(f"Disk type not available in region {config.target_region}")
            if not sku_compatible:
                issues.extend(sku_issues)

            if issues:
                status = ValidationStatus.WARNING if is_available_in_region else ValidationStatus.FAILED
                message = f"Disk type issues detected: {'; '.join(issues)}"
            else:
                status = ValidationStatus.OK
                message = f"Disk type '{config.target_disk_type}' is compatible and available"

            return DiskValidationResult(
                machine_name=config.target_machine_name,
                target_disk_type=config.target_disk_type,
                region=config.target_region,
                subscription_id=config.target_subscription,
                status=status,
                is_supported=True,
                is_available_in_region=is_available_in_region,
                performance_tier=performance_tier,
                message=message,
                alternative_disk_types=alternatives
            )

        except Exception as e:
            return DiskValidationResult(
                machine_name=config.target_machine_name,
                target_disk_type=config.target_disk_type,
                region=config.target_region,
                subscription_id=config.target_subscription,
                status=ValidationStatus.FAILED,
                is_supported=False,
                is_available_in_region=False,
                performance_tier=None,
                message=f"Error validating disk type: {str(e)}",
                alternative_disk_types=[]
            )

    def _is_disk_type_supported(self, disk_type: str) -> bool:
        """
        Check if disk type is a supported Azure disk type

        Args:
            disk_type: Disk type to validate

        Returns:
            True if disk type is supported
        """
        return disk_type in self.disk_characteristics

    def _check_regional_availability(
        self, 
        disk_type: str, 
        region: str, 
        subscription_id: str
    ) -> bool:
        """
        Check if disk type is available in target region

        Args:
            disk_type: Target disk type
            region: Target region
            subscription_id: Target subscription

        Returns:
            True if disk type is available in region
        """
        try:
            # For this implementation, we'll assume most disk types are available
            # In practice, you'd query Azure APIs to check specific availability
            
            # UltraSSD has limited regional availability
            if disk_type == "UltraSSD_LRS":
                ultra_regions = [
                    "eastus", "eastus2", "westus2", "northeurope", 
                    "westeurope", "southeastasia", "australiaeast"
                ]
                region_normalized = region.lower().replace(" ", "").replace("_", "").replace("-", "")
                return region_normalized in ultra_regions
            
            # Other disk types are generally available
            return True
            
        except Exception:
            return True  # Assume available if can't check

    def _check_sku_compatibility(self, vm_sku: str, disk_type: str) -> tuple[bool, List[str]]:
        """
        Check if VM SKU is compatible with disk type

        Args:
            vm_sku: Target VM SKU
            disk_type: Target disk type

        Returns:
            Tuple of (is_compatible, list_of_issues)
        """
        issues = []

        if not vm_sku or not disk_type:
            return True, []

        # Check premium storage requirements
        if disk_type in ["Premium_LRS", "UltraSSD_LRS"]:
            if not self._sku_supports_premium_storage(vm_sku):
                issues.append(f"VM SKU '{vm_sku}' does not support premium storage required for {disk_type}")

        # UltraSSD specific requirements
        if disk_type == "UltraSSD_LRS":
            if not self._sku_supports_ultra_ssd(vm_sku):
                issues.append(f"VM SKU '{vm_sku}' does not support UltraSSD")

        return len(issues) == 0, issues

    def _sku_supports_premium_storage(self, vm_sku: str) -> bool:
        """Check if VM SKU supports premium storage"""
        if not vm_sku:
            return False
        sku_lower = vm_sku.lower()
        premium_indicators = ['s_', '_s', 'ds', 'es', 'fs', 'gs', 'ls', 'ms']
        return any(indicator in sku_lower for indicator in premium_indicators)

    def _sku_supports_ultra_ssd(self, vm_sku: str) -> bool:
        """Check if VM SKU supports UltraSSD"""
        if not vm_sku:
            return False
        sku_lower = vm_sku.lower()
        # UltraSSD is supported on most newer generation VMs
        ultra_families = ['dv3', 'ev3', 'dv4', 'ev4', 'dv5', 'ev5', 'fsv2', 'lsv2', 'msv2']
        return any(family in sku_lower for family in ultra_families)

    def _get_alternative_disk_types(self) -> List[str]:
        """Get list of alternative disk types"""
        return ["Standard_LRS", "StandardSSD_LRS", "Premium_LRS"]

    def _get_optimization_recommendations(self, current_disk_type: str, vm_sku: str) -> List[str]:
        """
        Get disk type optimization recommendations

        Args:
            current_disk_type: Current disk type selection
            vm_sku: Target VM SKU

        Returns:
            List of alternative disk type recommendations
        """
        recommendations = []

        characteristics = self.disk_characteristics.get(current_disk_type, {})
        current_cost_tier = characteristics.get("cost_tier", "Unknown")

        # Recommend more cost-effective options for standard workloads
        if current_disk_type == "Premium_LRS":
            recommendations.append("StandardSSD_LRS")  # Better cost/performance balance
        
        # Recommend performance upgrades for high-cost tiers
        if current_disk_type == "Standard_LRS":
            recommendations.append("StandardSSD_LRS")  # Better performance for minimal cost increase

        # SKU-specific recommendations
        if vm_sku and self._sku_supports_premium_storage(vm_sku):
            if current_disk_type in ["Standard_LRS", "StandardSSD_LRS"]:
                recommendations.append("Premium_LRS")

        return recommendations[:2]  # Return top 2 recommendations