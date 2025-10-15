"""
VM SKU Validator - Azure Virtual Machine SKU validation

Handles validation of Azure VM SKUs:
- SKU availability in target region
- SKU specifications and capabilities
- SKU pricing tier validation
- Premium storage support
- Nested virtualization support
"""
from typing import Optional, Dict, Any, List
from azure.core.credentials import TokenCredential
from azure.mgmt.compute import ComputeManagementClient

from ...core.models import (
    MachineConfig,
    VMSkuValidationResult,
    ValidationStatus,
    VMSkuInfo
)


class VMSkuValidator:
    """
    Validates Azure VM SKU availability and specifications
    
    Checks:
    - SKU exists and is available in target region
    - SKU meets minimum requirements for migration
    - SKU supports required features (premium storage, etc.)
    - SKU family and generation compatibility
    - Cost optimization recommendations
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize VM SKU validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._compute_clients = {}
        self._sku_cache = {}

    def _get_compute_client(self, subscription_id: str) -> ComputeManagementClient:
        """Get or create cached ComputeManagementClient"""
        if subscription_id not in self._compute_clients:
            self._compute_clients[subscription_id] = ComputeManagementClient(
                self.credential, subscription_id
            )
        return self._compute_clients[subscription_id]

    def validate(self, config: MachineConfig) -> VMSkuValidationResult:
        """
        Validate VM SKU configuration

        Args:
            config: Machine configuration with target SKU

        Returns:
            VMSkuValidationResult with validation details
        """
        try:
            compute_client = self._get_compute_client(config.target_subscription)

            # Get available VM sizes in target region
            cache_key = f"{config.target_subscription}_{config.target_region}"
            
            if cache_key not in self._sku_cache:
                vm_sizes = list(compute_client.virtual_machine_sizes.list(config.target_region))
                self._sku_cache[cache_key] = vm_sizes
            else:
                vm_sizes = self._sku_cache[cache_key]

            # Find the target SKU
            target_sku = None
            sku_lower = config.target_machine_sku.lower() if config.target_machine_sku else ""

            for vm_size in vm_sizes:
                if vm_size.name and vm_size.name.lower() == sku_lower:
                    target_sku = vm_size
                    break

            if not target_sku:
                # Get alternative SKU suggestions
                suggestions = self._get_sku_suggestions(vm_sizes, config.target_machine_sku)
                
                return VMSkuValidationResult(
                    machine_name=config.target_machine_name,
                    target_sku=config.target_machine_sku,
                    region=config.target_region,
                    subscription_id=config.target_subscription,
                    status=ValidationStatus.FAILED,
                    is_available=False,
                    sku_info=None,
                    supports_premium_storage=False,
                    supports_nested_virtualization=False,
                    message=f"VM SKU '{config.target_machine_sku}' is not available in region '{config.target_region}'",
                    suggested_skus=suggestions,
                    cost_optimization_notes=[]
                )

            # Extract SKU information
            sku_info = self._get_sku_info(target_sku)

            # Check premium storage support
            supports_premium = self._check_premium_storage_support(config.target_machine_sku)

            # Check nested virtualization support
            supports_nested = self._check_nested_virtualization_support(config.target_machine_sku)

            # Generate cost optimization recommendations
            cost_notes = self._get_cost_optimization_notes(target_sku, vm_sizes)

            # Generate alternative SKU suggestions for optimization
            suggestions = self._get_optimization_suggestions(target_sku, vm_sizes)

            # Determine validation status
            warnings = []
            if sku_info.vcpus < 2:
                warnings.append("SKU has less than 2 vCPUs which may impact performance")
            if sku_info.memory_mb < 4096:  # Less than 4GB
                warnings.append("SKU has less than 4GB RAM which may be insufficient")
            if not supports_premium and config.target_disk_type == "Premium_LRS":
                warnings.append("SKU does not support premium storage but premium disk type is specified")

            if warnings:
                status = ValidationStatus.WARNING
                message = f"SKU '{config.target_machine_sku}' is available but has concerns: {'; '.join(warnings)}"
            else:
                status = ValidationStatus.OK
                message = f"VM SKU '{config.target_machine_sku}' is available and suitable for migration"

            return VMSkuValidationResult(
                machine_name=config.target_machine_name,
                target_sku=config.target_machine_sku,
                region=config.target_region,
                subscription_id=config.target_subscription,
                status=status,
                is_available=True,
                sku_info=sku_info,
                supports_premium_storage=supports_premium,
                supports_nested_virtualization=supports_nested,
                message=message,
                suggested_skus=suggestions,
                cost_optimization_notes=cost_notes
            )

        except Exception as e:
            return VMSkuValidationResult(
                machine_name=config.target_machine_name,
                target_sku=config.target_machine_sku,
                region=config.target_region,
                subscription_id=config.target_subscription,
                status=ValidationStatus.FAILED,
                is_available=False,
                sku_info=None,
                supports_premium_storage=False,
                supports_nested_virtualization=False,
                message=f"Error validating VM SKU: {str(e)}",
                suggested_skus=[],
                cost_optimization_notes=[]
            )

    def _get_sku_info(self, vm_size) -> VMSkuInfo:
        """
        Extract SKU information from Azure VM size object

        Args:
            vm_size: Azure VM size object

        Returns:
            VMSkuInfo with SKU specifications
        """
        return VMSkuInfo(
            name=vm_size.name,
            vcpus=vm_size.number_of_cores or 0,
            memory_mb=vm_size.memory_in_mb or 0,
            max_data_disks=vm_size.max_data_disk_count or 0,
            temp_disk_size_mb=vm_size.os_disk_size_in_mb or 0
        )

    def _check_premium_storage_support(self, sku_name: str) -> bool:
        """
        Check if SKU supports premium storage

        Args:
            sku_name: VM SKU name

        Returns:
            True if premium storage is supported
        """
        if not sku_name:
            return False

        # SKUs that support premium storage typically have 's' in the name
        # This is a simplified check - in practice would query Azure APIs
        sku_lower = sku_name.lower()
        premium_indicators = ['s_', '_s', 'ds', 'es', 'fs', 'gs', 'ls', 'ms']
        
        return any(indicator in sku_lower for indicator in premium_indicators)

    def _check_nested_virtualization_support(self, sku_name: str) -> bool:
        """
        Check if SKU supports nested virtualization

        Args:
            sku_name: VM SKU name

        Returns:
            True if nested virtualization is supported
        """
        if not sku_name:
            return False

        # SKUs that support nested virtualization
        # This is a simplified check - in practice would query Azure APIs
        sku_lower = sku_name.lower()
        nested_families = ['dv3', 'ev3', 'dv4', 'ev4', 'dv5', 'ev5', 'dasv4', 'easv4']
        
        return any(family in sku_lower for family in nested_families)

    def _get_sku_suggestions(self, vm_sizes: List[Any], original_sku: Optional[str]) -> List[str]:
        """
        Get alternative SKU suggestions when original is not available

        Args:
            vm_sizes: List of available VM sizes in region
            original_sku: The originally requested SKU

        Returns:
            List of suggested alternative SKUs
        """
        suggestions = []
        
        # Common fallback SKUs
        fallback_skus = [
            "Standard_D2s_v3", "Standard_D4s_v3", "Standard_D2_v2",
            "Standard_B2s", "Standard_B2ms", "Standard_F2s_v2"
        ]

        for fallback in fallback_skus:
            for vm_size in vm_sizes:
                if vm_size.name and vm_size.name.lower() == fallback.lower():
                    if fallback not in suggestions:
                        suggestions.append(fallback)
                    break
                    
        return suggestions[:3]  # Return top 3 suggestions

    def _get_optimization_suggestions(self, current_sku, vm_sizes: List[Any]) -> List[str]:
        """
        Get cost/performance optimization suggestions

        Args:
            current_sku: Current VM size object
            vm_sizes: List of available VM sizes

        Returns:
            List of optimization suggestions
        """
        suggestions = []
        current_vcpus = current_sku.number_of_cores or 0
        current_memory = current_sku.memory_in_mb or 0

        # Look for similar but more cost-effective options
        for vm_size in vm_sizes:
            if not vm_size.name:
                continue
                
            # Find SKUs with similar specs but different families
            if (vm_size.number_of_cores == current_vcpus and 
                vm_size.memory_in_mb == current_memory and
                vm_size.name != current_sku.name):
                
                # Prefer newer generations and B-series for cost optimization
                if ('_v4' in vm_size.name.lower() or 
                    '_v5' in vm_size.name.lower() or 
                    vm_size.name.lower().startswith('standard_b')):
                    suggestions.append(vm_size.name)

        return suggestions[:2]  # Return top 2 optimization suggestions

    def _get_cost_optimization_notes(self, current_sku, vm_sizes: List[Any]) -> List[str]:
        """
        Generate cost optimization recommendations

        Args:
            current_sku: Current VM size object
            vm_sizes: List of available VM sizes

        Returns:
            List of cost optimization notes
        """
        notes = []

        # Check if B-series might be suitable for burstable workloads
        if current_sku.number_of_cores <= 4:
            notes.append("Consider B-series SKUs for variable workloads to reduce costs")

        # Check for newer generation SKUs
        current_name = current_sku.name or ""
        if '_v2' in current_name.lower():
            notes.append("Consider upgrading to v3, v4, or v5 generation for better price/performance")

        # Check for spot instance eligibility
        if current_sku.number_of_cores >= 2:
            notes.append("Consider Azure Spot instances for non-production workloads")

        return notes[:3]  # Return top 3 notes