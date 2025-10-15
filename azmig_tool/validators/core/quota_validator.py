"""
Quota Validator - vCPU quota validation

Handles validation of Azure compute quotas:
- vCPU availability by VM family
- Current usage vs limits
- Quota recommendations for migration planning
"""
from typing import List, Dict, Optional
from azure.core.credentials import TokenCredential
from azure.mgmt.compute import ComputeManagementClient

from ...core.models import (
    MigrateProjectConfig,
    QuotaValidationResult,
    ValidationStatus,
    QuotaInfo
)


class QuotaValidator:
    """
    Validates vCPU quota availability for Azure Migrate operations
    
    Checks:
    - Current vCPU usage by VM family
    - Total quota limits per family
    - Available quota for new deployments
    - Provides recommendations for quota increases if needed
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize quota validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._compute_clients = {}

    def _get_compute_client(self, subscription_id: str) -> ComputeManagementClient:
        """Get or create cached ComputeManagementClient"""
        if subscription_id not in self._compute_clients:
            self._compute_clients[subscription_id] = ComputeManagementClient(
                self.credential, subscription_id
            )
        return self._compute_clients[subscription_id]

    def validate(
        self,
        config: MigrateProjectConfig,
        required_vcpus_by_family: Optional[Dict[str, int]] = None
    ) -> QuotaValidationResult:
        """
        Validate vCPU quota availability in target region

        Args:
            config: Migrate project configuration
            required_vcpus_by_family: Required vCPUs per VM family (optional)

        Returns:
            QuotaValidationResult with quota details and recommendations
        """
        try:
            compute_client = self._get_compute_client(config.subscription_id)

            # Get usage information for the target region
            usages = compute_client.usage.list(config.region)

            quotas: List[QuotaInfo] = []
            insufficient_families = []
            recommended_skus = []

            # VM family to SKU mapping for recommendations
            family_to_skus = self._get_family_sku_mapping()

            for usage in usages:
                family_name = usage.name.value

                # Only process vCPU-related quotas
                if family_name and self._is_vcpu_quota(family_name):
                    quota_info = self._process_quota_usage(usage, config)
                    quotas.append(quota_info)

                    # Check if sufficient for requirements
                    if required_vcpus_by_family and family_name in required_vcpus_by_family:
                        required = required_vcpus_by_family[family_name]
                        if not quota_info.is_sufficient(required):
                            insufficient_families.append(family_name)
                            
                            # Add SKU recommendations for this family
                            if family_name in family_to_skus:
                                for sku in family_to_skus[family_name]:
                                    if sku not in recommended_skus:
                                        recommended_skus.append(sku)

            # Determine overall status and message
            status, message = self._determine_quota_status(insufficient_families, config.region)

            return QuotaValidationResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=status,
                quotas=quotas,
                insufficient_families=insufficient_families,
                recommended_skus=recommended_skus[:5],  # Limit to top 5 recommendations
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

    def _is_vcpu_quota(self, family_name: str) -> bool:
        """Check if quota name represents vCPU quota"""
        if not family_name:
            return False
        family_lower = family_name.lower()
        return 'cores' in family_lower or 'vcpus' in family_lower

    def _process_quota_usage(self, usage, config: MigrateProjectConfig) -> QuotaInfo:
        """
        Process raw usage data into QuotaInfo object

        Args:
            usage: Azure usage data object
            config: Project configuration

        Returns:
            QuotaInfo with quota details
        """
        family_name = usage.name.value
        current_usage = usage.current_value
        total_quota = usage.limit
        available = total_quota - current_usage

        return QuotaInfo(
            subscription_id=config.subscription_id,
            region=config.region,
            family=family_name,
            total_quota=total_quota,
            current_usage=current_usage,
            available=available
        )

    def _get_family_sku_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of VM families to recommended SKUs"""
        return {
            "standardDSv3Family": ["Standard_D2s_v3", "Standard_D4s_v3", "Standard_D8s_v3"],
            "standardESv3Family": ["Standard_E2s_v3", "Standard_E4s_v3", "Standard_E8s_v3"],
            "standardFSv2Family": ["Standard_F2s_v2", "Standard_F4s_v2", "Standard_F8s_v2"],
            "standardBSFamily": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"],
            "standardDFamily": ["Standard_D2_v2", "Standard_D3_v2", "Standard_D4_v2"]
        }

    def _determine_quota_status(self, insufficient_families: List[str], region: str) -> tuple[ValidationStatus, str]:
        """
        Determine overall quota validation status

        Args:
            insufficient_families: List of families with insufficient quota
            region: Target region name

        Returns:
            Tuple of (ValidationStatus, descriptive message)
        """
        if insufficient_families:
            return (
                ValidationStatus.WARNING,
                f"Insufficient quota for {len(insufficient_families)} VM family(ies)"
            )
        else:
            return (
                ValidationStatus.OK,
                f"Sufficient quota available in {region}"
            )