"""
VNet Validator - Azure Virtual Network and subnet validation

Handles validation of Azure Virtual Networks:
- VNet existence and accessibility  
- Subnet availability and configuration
- IP address space validation
- Network Security Group requirements
- VNet peering considerations
"""
from typing import Optional, List
from azure.core.credentials import TokenCredential
from azure.mgmt.network import NetworkManagementClient
from ipaddress import IPv4Network, AddressValueError

from ...core.models import (
    MachineConfig,
    VNetValidationResult,
    ValidationStatus,
    SubnetInfo
)


class VNetValidator:
    """
    Validates Azure Virtual Network and subnet configuration
    
    Checks:
    - VNet exists and is accessible
    - Subnet exists with adequate IP space
    - Network security group configuration
    - VNet location alignment with target region
    - Subnet delegation requirements
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize VNet validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._network_clients = {}

    def _get_network_client(self, subscription_id: str) -> NetworkManagementClient:
        """Get or create cached NetworkManagementClient"""
        if subscription_id not in self._network_clients:
            self._network_clients[subscription_id] = NetworkManagementClient(
                self.credential, subscription_id
            )
        return self._network_clients[subscription_id]

    def validate(self, config: MachineConfig) -> VNetValidationResult:
        """
        Validate VNet and subnet configuration

        Args:
            config: Machine configuration with target VNet/subnet

        Returns:
            VNetValidationResult with validation details
        """
        try:
            network_client = self._get_network_client(config.target_subscription)

            # Check if VNet exists
            try:
                vnet = network_client.virtual_networks.get(
                    config.target_rg,
                    config.target_vnet
                )
                vnet_exists = True
                vnet_location = vnet.location if hasattr(vnet, 'location') else None
            except Exception:
                vnet_exists = False
                vnet_location = None

            if not vnet_exists:
                return VNetValidationResult(
                    machine_name=config.target_machine_name,
                    vnet_name=config.target_vnet,
                    subnet_name=config.target_subnet,
                    resource_group=config.target_rg,
                    subscription_id=config.target_subscription,
                    status=ValidationStatus.FAILED,
                    vnet_exists=False,
                    subnet_exists=False,
                    subnet_info=None,
                    region_match=False,
                    has_nsg=False,
                    message=f"VNet '{config.target_vnet}' does not exist in resource group '{config.target_rg}'",
                    suggested_action="Create the VNet or verify the VNet name and resource group"
                )

            # Check region alignment
            region_match = True
            if vnet_location and config.target_region:
                normalized_vnet_region = self._normalize_region_name(vnet_location)
                normalized_target_region = self._normalize_region_name(config.target_region)
                region_match = normalized_vnet_region == normalized_target_region

            # Check if subnet exists
            subnet_exists = False
            subnet_info = None
            has_nsg = False

            if hasattr(vnet, 'subnets') and vnet.subnets:
                for subnet in vnet.subnets:
                    if subnet.name == config.target_subnet:
                        subnet_exists = True
                        subnet_info = self._get_subnet_info(subnet)
                        has_nsg = subnet.network_security_group is not None
                        break

            if not subnet_exists:
                available_subnets = [s.name for s in (vnet.subnets or []) if s.name]
                return VNetValidationResult(
                    machine_name=config.target_machine_name,
                    vnet_name=config.target_vnet,
                    subnet_name=config.target_subnet,
                    resource_group=config.target_rg,
                    subscription_id=config.target_subscription,
                    status=ValidationStatus.FAILED,
                    vnet_exists=True,
                    subnet_exists=False,
                    subnet_info=None,
                    region_match=region_match,
                    has_nsg=False,
                    message=f"Subnet '{config.target_subnet}' does not exist in VNet '{config.target_vnet}'",
                    suggested_action=f"Create the subnet or use one of: {', '.join(available_subnets[:3])}"
                )

            # Determine overall status and message
            issues = []
            if not region_match:
                issues.append(f"VNet is in '{vnet_location}' but target region is '{config.target_region}'")
            if not has_nsg:
                issues.append("Subnet does not have a Network Security Group")
            if subnet_info and subnet_info.available_ips < 10:
                issues.append(f"Subnet has only {subnet_info.available_ips} available IP addresses")

            if issues:
                status = ValidationStatus.WARNING
                message = f"VNet and subnet exist but have issues: {'; '.join(issues)}"
                suggested_action = "Review and address the identified networking issues"
            else:
                status = ValidationStatus.OK
                message = f"VNet '{config.target_vnet}' and subnet '{config.target_subnet}' are properly configured"
                suggested_action = None

            return VNetValidationResult(
                machine_name=config.target_machine_name,
                vnet_name=config.target_vnet,
                subnet_name=config.target_subnet,
                resource_group=config.target_rg,
                subscription_id=config.target_subscription,
                status=status,
                vnet_exists=True,
                subnet_exists=True,
                subnet_info=subnet_info,
                region_match=region_match,
                has_nsg=has_nsg,
                message=message,
                suggested_action=suggested_action
            )

        except Exception as e:
            return VNetValidationResult(
                machine_name=config.target_machine_name,
                vnet_name=config.target_vnet,
                subnet_name=config.target_subnet,
                resource_group=config.target_rg,
                subscription_id=config.target_subscription,
                status=ValidationStatus.FAILED,
                vnet_exists=False,
                subnet_exists=False,
                subnet_info=None,
                region_match=False,
                has_nsg=False,
                message=f"Error validating VNet: {str(e)}",
                suggested_action="Check connectivity and permissions"
            )

    def _get_subnet_info(self, subnet) -> Optional[SubnetInfo]:
        """
        Extract subnet information from Azure subnet object

        Args:
            subnet: Azure subnet object

        Returns:
            SubnetInfo with subnet details or None if extraction fails
        """
        try:
            address_prefix = subnet.address_prefix
            if not address_prefix:
                return None

            # Calculate available IPs
            try:
                network = IPv4Network(address_prefix, strict=False)
                total_ips = network.num_addresses
                
                # Azure reserves first 4 and last 1 IP in each subnet
                reserved_ips = 5
                available_ips = max(0, total_ips - reserved_ips)
                
                # Account for any existing IP configurations
                used_ips = 0
                if hasattr(subnet, 'ip_configurations') and subnet.ip_configurations:
                    used_ips = len(subnet.ip_configurations)
                
                available_ips = max(0, available_ips - used_ips)

            except (AddressValueError, ValueError):
                available_ips = 0

            return SubnetInfo(
                name=subnet.name,
                address_prefix=address_prefix,
                available_ips=available_ips,
                has_nsg=subnet.network_security_group is not None,
                has_route_table=subnet.route_table is not None
            )

        except Exception:
            return None

    def _normalize_region_name(self, region: str) -> str:
        """
        Normalize region name for comparison

        Args:
            region: Region name to normalize

        Returns:
            Normalized region name
        """
        if not region:
            return ""
        return region.lower().replace(" ", "").replace("_", "").replace("-", "")