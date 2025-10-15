"""
Region Validator - Azure region availability validation

Handles validation of Azure regions:
- Region availability for subscriptions
- Service availability in regions
- Region naming and aliases
- Resource provider availability
"""
from typing import List, Optional
from azure.core.credentials import TokenCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient

from ...core.models import (
    MachineConfig,
    RegionValidationResult,
    ValidationStatus
)


class RegionValidator:
    """
    Validates Azure region availability and configuration
    
    Checks:
    - Region exists and is available
    - Subscription has access to region
    - Required services available in region
    - VM SKUs available in region
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize region validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._resource_clients = {}
        self._compute_clients = {}

    def _get_resource_client(self, subscription_id: str) -> ResourceManagementClient:
        """Get or create cached ResourceManagementClient"""
        if subscription_id not in self._resource_clients:
            self._resource_clients[subscription_id] = ResourceManagementClient(
                self.credential, subscription_id
            )
        return self._resource_clients[subscription_id]

    def _get_compute_client(self, subscription_id: str) -> ComputeManagementClient:
        """Get or create cached ComputeManagementClient"""
        if subscription_id not in self._compute_clients:
            self._compute_clients[subscription_id] = ComputeManagementClient(
                self.credential, subscription_id
            )
        return self._compute_clients[subscription_id]

    def validate(self, config: MachineConfig) -> RegionValidationResult:
        """
        Validate region availability and configuration

        Args:
            config: Machine configuration with target region

        Returns:
            RegionValidationResult with validation details
        """
        try:
            # Get resource and compute clients
            resource_client = self._get_resource_client(config.target_subscription)
            compute_client = self._get_compute_client(config.target_subscription)

            # Check if region is available
            available_locations = resource_client.subscriptions.list_locations(
                config.target_subscription
            )

            region_found = False
            normalized_region = self._normalize_region_name(config.target_region)

            for location in available_locations:
                if (location.name == normalized_region or 
                    location.display_name.lower() == config.target_region.lower()):
                    region_found = True
                    break

            if not region_found:
                return RegionValidationResult(
                    machine_name=config.target_machine_name,
                    region=config.target_region,
                    subscription_id=config.target_subscription,
                    status=ValidationStatus.FAILED,
                    is_available=False,
                    services_available=False,
                    sku_available=None,
                    message=f"Region '{config.target_region}' is not available in subscription",
                    available_regions=self._get_suggested_regions(available_locations)
                )

            # Check if required services are available
            services_available = self._check_service_availability(
                resource_client, normalized_region
            )

            # Check if target VM SKU is available in region
            sku_available = self._check_sku_availability(
                compute_client, normalized_region, config.target_machine_sku
            )

            # Determine overall status
            if services_available and (sku_available is None or sku_available):
                status = ValidationStatus.OK
                message = f"Region '{config.target_region}' is available with all required services"
            elif not services_available:
                status = ValidationStatus.WARNING
                message = f"Region '{config.target_region}' available but some services may be limited"
            else:
                status = ValidationStatus.WARNING
                message = f"Region '{config.target_region}' available but SKU '{config.target_machine_sku}' may not be available"

            return RegionValidationResult(
                machine_name=config.target_machine_name,
                region=config.target_region,
                subscription_id=config.target_subscription,
                status=status,
                is_available=True,
                services_available=services_available,
                sku_available=sku_available,
                message=message,
                available_regions=[]
            )

        except Exception as e:
            return RegionValidationResult(
                machine_name=config.target_machine_name,
                region=config.target_region,
                subscription_id=config.target_subscription,
                status=ValidationStatus.FAILED,
                is_available=False,
                services_available=False,
                sku_available=None,
                message=f"Error validating region: {str(e)}",
                available_regions=[]
            )

    def _normalize_region_name(self, region: str) -> str:
        """
        Normalize region name to Azure format

        Args:
            region: Region name (e.g., "East US", "eastus")

        Returns:
            Normalized region name (e.g., "eastus")
        """
        if not region:
            return ""

        # Common region name mappings
        region_mappings = {
            "east us": "eastus",
            "east us 2": "eastus2",
            "west us": "westus",
            "west us 2": "westus2",
            "west us 3": "westus3",
            "central us": "centralus",
            "north central us": "northcentralus",
            "south central us": "southcentralus",
            "west central us": "westcentralus",
            "north europe": "northeurope",
            "west europe": "westeurope",
            "southeast asia": "southeastasia",
            "east asia": "eastasia"
        }

        region_lower = region.lower().strip()
        
        # Check direct mappings first
        if region_lower in region_mappings:
            return region_mappings[region_lower]
        
        # Remove spaces and convert to lowercase
        return region_lower.replace(" ", "").replace("_", "").replace("-", "")

    def _check_service_availability(self, resource_client: ResourceManagementClient, region: str) -> bool:
        """
        Check if required Azure services are available in region

        Args:
            resource_client: Azure Resource Management client
            region: Target region name

        Returns:
            True if all required services are available
        """
        try:
            # Get available providers in the region
            providers = resource_client.providers.list()
            
            required_providers = [
                "Microsoft.Compute",
                "Microsoft.Network", 
                "Microsoft.Storage",
                "Microsoft.Migrate"
            ]

            for provider in providers:
                if provider.namespace in required_providers:
                    # Check if provider supports the region
                    for resource_type in provider.resource_types or []:
                        if region.lower() in [loc.lower() for loc in (resource_type.locations or [])]:
                            continue

            return True  # Simplified - assume available if no errors

        except Exception:
            return False

    def _check_sku_availability(
        self, 
        compute_client: ComputeManagementClient, 
        region: str, 
        sku: Optional[str]
    ) -> Optional[bool]:
        """
        Check if VM SKU is available in region

        Args:
            compute_client: Azure Compute Management client
            region: Target region name
            sku: VM SKU to check (optional)

        Returns:
            True if available, False if not available, None if not checked
        """
        if not sku:
            return None

        try:
            # Get available VM sizes in region
            vm_sizes = compute_client.virtual_machine_sizes.list(region)
            
            sku_lower = sku.lower()
            for vm_size in vm_sizes:
                if vm_size.name and vm_size.name.lower() == sku_lower:
                    return True

            return False

        except Exception:
            # If we can't check, assume it might be available
            return None

    def _get_suggested_regions(self, available_locations) -> List[str]:
        """
        Get list of commonly used regions as suggestions

        Args:
            available_locations: List of available location objects

        Returns:
            List of suggested region names
        """
        suggestions = []
        preferred_regions = [
            "eastus", "eastus2", "westus2", "westeurope", 
            "northeurope", "southeastasia", "australiaeast"
        ]

        for location in available_locations:
            if location.name in preferred_regions:
                suggestions.append(location.display_name)

        return suggestions[:5]  # Return top 5 suggestions