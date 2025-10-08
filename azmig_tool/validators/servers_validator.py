"""
Servers Validator - Azure API validation
"""
from typing import Optional, Dict, Any
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from ..base.validator_interface import BaseValidatorInterface
from ..models import (
    MigrationConfig,
    ValidationResult,
    ValidationStage,
    AzureMigrateProject,
    DiskType
)
from ..constants import AZURE_REGIONS, AZURE_ROLE_IDS
from ..config.validation_config import ValidationConfig


class ServersValidator(BaseValidatorInterface):
    """Validator using Azure APIs"""

    def __init__(self, credential: Optional[DefaultAzureCredential] = None, validation_config: Optional[ValidationConfig] = None):
        """
        Initialize validator

        Args:
            credential: Azure credential (uses DefaultAzureCredential if not provided)
            validation_config: Validation configuration (loads default if not provided)
        """
        super().__init__(validation_config)
        self.credential = credential or DefaultAzureCredential()
        self._clients_cache: Dict[str, Any] = {}

    def _get_resource_client(self, subscription_id: str) -> ResourceManagementClient:
        """Get or create cached ResourceManagementClient"""
        key = f"resource_{subscription_id}"
        if key not in self._clients_cache:
            self._clients_cache[key] = ResourceManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def _get_compute_client(self, subscription_id: str) -> ComputeManagementClient:
        """Get or create cached ComputeManagementClient"""
        key = f"compute_{subscription_id}"
        if key not in self._clients_cache:
            self._clients_cache[key] = ComputeManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def _get_network_client(self, subscription_id: str):
        """Get or create cached NetworkManagementClient"""
        key = f"network_{subscription_id}"
        if key not in self._clients_cache:
            from azure.mgmt.network import NetworkManagementClient
            self._clients_cache[key] = NetworkManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def _get_auth_client(self, subscription_id: str):
        """Get or create cached AuthorizationManagementClient"""
        key = f"auth_{subscription_id}"
        if key not in self._clients_cache:
            from azure.mgmt.authorization import AuthorizationManagementClient
            self._clients_cache[key] = AuthorizationManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def validate_region(self, config: MigrationConfig) -> ValidationResult:
        """Validate Azure region exists"""
        region = config.target_region.lower().replace(" ", "")

        if region in AZURE_REGIONS:
            return ValidationResult(
                stage=ValidationStage.AZURE_REGION,
                passed=True,
                message=f"✓ Region '{config.target_region}' is valid",
                details={"region": region}
            )
        else:
            return ValidationResult(
                stage=ValidationStage.AZURE_REGION,
                passed=False,
                message=f"✗ Invalid region '{config.target_region}'. Must be a valid Azure region.",
                details={
                    "region": region,
                    "valid_regions_sample": AZURE_REGIONS[:10]
                }
            )

    def validate_resource_group(self, config: MigrationConfig) -> ValidationResult:
        """Validate that resource group exists"""
        try:
            client = self._get_resource_client(config.target_subscription)
            rg = client.resource_groups.get(config.target_rg)

            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=True,
                message=f"✓ Resource group '{config.target_rg}' exists in subscription",
                details={
                    "resource_group": config.target_rg,
                    "location": rg.location,
                    "id": rg.id
                }
            )
        except ResourceNotFoundError:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Resource group '{config.target_rg}' not found in subscription '{config.target_subscription}'",
                details={
                    "resource_group": config.target_rg,
                    "subscription": config.target_subscription,

                }
            )
        except HttpResponseError as e:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Error accessing resource group: {e.message}",
                details={"error": str(e)}
            )
        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Unexpected error validating resource group: {str(e)}",
                details={"error": str(e)}
            )

    def validate_vnet_and_subnet(self, config: MigrationConfig) -> ValidationResult:
        """Validate that VNet and Subnet exist with capacity and delegation checks"""
        try:
            client = self._get_network_client(config.target_subscription)

            # Get VNet
            vnet = client.virtual_networks.get(
                config.target_rg, config.target_vnet)

            # Check if subnet exists in VNet
            for subnet in vnet.subnets:
                if subnet.name == config.target_subnet:
                    # Validate subnet delegation
                    delegation_result = self._validate_subnet_delegation(
                        subnet)
                    if not delegation_result["can_host_vms"]:
                        return ValidationResult(
                            stage=ValidationStage.AZURE_RESOURCES,
                            passed=False,
                            message=f"✗ Subnet '{config.target_subnet}' is delegated to '{delegation_result['delegation_service']}' and cannot host VMs",
                            details={
                                "vnet": config.target_vnet,
                                "subnet": config.target_subnet,
                                "is_delegated": True,
                                "delegation_service": delegation_result["delegation_service"],
                                "error": "Delegated subnets cannot host regular virtual machines",

                            }
                        )

                    # Validate IP availability (check for at least 1 IP needed)
                    ip_availability = self._validate_ip_availability(
                        client, config.target_rg, config.target_vnet,
                        config.target_subnet, subnet, required_ips=1
                    )

                    if not ip_availability["has_capacity"]:
                        return ValidationResult(
                            stage=ValidationStage.AZURE_RESOURCES,
                            passed=False,
                            message=f"✗ Subnet '{config.target_subnet}' has insufficient IP addresses. Available: {ip_availability['available_ips']}, Required: {ip_availability['required_ips']}",
                            details={
                                "vnet": config.target_vnet,
                                "subnet": config.target_subnet,
                                "subnet_prefix": subnet.address_prefix,
                                "total_ips": ip_availability["total_ips"],
                                "azure_reserved_ips": ip_availability["azure_reserved"],
                                "used_ips": ip_availability["used_ips"],
                                "available_ips": ip_availability["available_ips"],
                                "required_ips": ip_availability["required_ips"],
                                "error": "Insufficient IP addresses in subnet",

                            }
                        )

                    # All validations passed
                    return ValidationResult(
                        stage=ValidationStage.AZURE_RESOURCES,
                        passed=True,
                        message=f"✓ VNet '{config.target_vnet}' and Subnet '{config.target_subnet}' are valid (Available IPs: {ip_availability['available_ips']})",
                        details={
                            "vnet": config.target_vnet,
                            "subnet": config.target_subnet,
                            "subnet_prefix": subnet.address_prefix,
                            "vnet_id": vnet.id,
                            "is_delegated": delegation_result["is_delegated"],
                            "delegation_service": delegation_result["delegation_service"],
                            "total_ips": ip_availability["total_ips"],
                            "available_ips": ip_availability["available_ips"],
                            "used_ips": ip_availability["used_ips"],

                        }
                    )

            # Subnet not found
            available_subnets = [s.name for s in vnet.subnets]
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Subnet '{config.target_subnet}' not found in VNet '{config.target_vnet}'",
                details={
                    "vnet": config.target_vnet,
                    "requested_subnet": config.target_subnet,
                    "available_subnets": available_subnets,

                }
            )

        except ResourceNotFoundError:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ VNet '{config.target_vnet}' not found in resource group '{config.target_rg}'",
                details={
                    "vnet": config.target_vnet,
                    "rg": config.target_rg,

                }
            )
        except HttpResponseError as e:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Error accessing VNet: {e.message}",
                details={"error": str(e)}
            )
        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"✗ Unexpected error validating VNet/Subnet: {str(e)}",
                details={"error": str(e)}
            )

    def _validate_subnet_delegation(self, subnet) -> Dict[str, Any]:
        """
        Validate subnet is not delegated to incompatible services

        Delegated subnets cannot host regular VMs:
        - Microsoft.Sql/managedInstances (SQL Managed Instance)
        - Microsoft.Web/serverFarms (App Service)
        - Microsoft.ContainerInstance/containerGroups
        - Microsoft.Netapp/volumes (Azure NetApp Files)
        - Microsoft.DBforPostgreSQL/flexibleServers
        - Microsoft.DBforMySQL/flexibleServers
        - Microsoft.MachineLearningServices/workspaces
        - And others...

        Returns:
            dict with:
            - is_delegated: bool
            - delegation_service: str or None
            - can_host_vms: bool
        """
        if not subnet.delegations or len(subnet.delegations) == 0:
            return {
                "is_delegated": False,
                "delegation_service": None,
                "can_host_vms": True
            }

        # Subnet is delegated
        delegation_service = subnet.delegations[0].service_name if subnet.delegations else None

        return {
            "is_delegated": True,
            "delegation_service": delegation_service,
            "can_host_vms": False  # Delegated subnets cannot host regular VMs
        }

    def _validate_ip_availability(
        self,
        network_client,
        resource_group: str,
        vnet_name: str,
        subnet_name: str,
        subnet,
        required_ips: int = 1
    ) -> Dict[str, Any]:
        """
        Check IP address availability in subnet

        Azure reserves 5 IPs in every subnet:
        - .0: Network address
        - .1: Default gateway
        - .2, .3: Azure DNS
        - .255: Broadcast address (for /24 and larger)

        Args:
            network_client: NetworkManagementClient
            resource_group: Resource group name
            vnet_name: VNet name
            subnet_name: Subnet name
            subnet: Subnet object
            required_ips: Number of IPs needed (default: 1)

        Returns:
            dict with:
            - total_ips: Total IPs in subnet
            - azure_reserved: Azure reserved IPs (5)
            - used_ips: Currently used IPs
            - available_ips: Available IPs
            - required_ips: Required IPs
            - has_capacity: bool
        """
        import ipaddress

        # Calculate total IPs from CIDR
        network = ipaddress.ip_network(subnet.address_prefix, strict=False)
        total_ips = network.num_addresses

        # Azure reserves 5 IPs in every subnet
        azure_reserved = 5

        # Count used IPs from IP configurations
        used_ips = 0
        if subnet.ip_configurations:
            used_ips = len(subnet.ip_configurations)

        # Calculate available IPs
        available_ips = total_ips - azure_reserved - used_ips

        # Check if we have capacity
        has_capacity = available_ips >= required_ips

        return {
            "total_ips": total_ips,
            "azure_reserved": azure_reserved,
            "used_ips": used_ips,
            "available_ips": available_ips,
            "required_ips": required_ips,
            "has_capacity": has_capacity
        }

    def validate_vm_sku(self, config: MigrationConfig) -> ValidationResult:
        """Validate that VM SKU is available in the target region"""
        try:
            client = self._get_compute_client(config.target_subscription)
            region = config.target_region.lower().replace(" ", "")

            # List available SKUs for the region
            skus = client.resource_skus.list(filter=f"location eq '{region}'")

            # Find the requested SKU
            for sku in skus:
                if sku.resource_type == "virtualMachines" and sku.name == config.target_machine_sku:
                    # Check if SKU has restrictions
                    if sku.restrictions:
                        restriction_info = [
                            f"{r.type}: {r.reason_code}" for r in sku.restrictions]
                        return ValidationResult(
                            stage=ValidationStage.DISK_AND_SKU,
                            passed=False,
                            message=f"✗ VM SKU '{config.target_machine_sku}' has restrictions in region '{region}'",
                            details={
                                "sku": config.target_machine_sku,
                                "region": region,
                                "restrictions": restriction_info,

                            }
                        )

                    return ValidationResult(
                        stage=ValidationStage.DISK_AND_SKU,
                        passed=True,
                        message=f"✓ VM SKU '{config.target_machine_sku}' is available in region '{region}'",
                        details={
                            "sku": config.target_machine_sku,
                            "region": region,
                            "capabilities": {c.name: c.value for c in sku.capabilities} if sku.capabilities else {},

                        }
                    )

            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=False,
                message=f"✗ VM SKU '{config.target_machine_sku}' not available in region '{region}'",
                details={
                    "sku": config.target_machine_sku,
                    "region": region,

                }
            )

        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=False,
                message=f"✗ Error validating VM SKU: {str(e)}",
                details={"error": str(e)}
            )

    def validate_disk_type(self, config: MigrationConfig) -> ValidationResult:
        """Validate disk type is valid"""
        valid_types = [dt.value for dt in DiskType]

        if config.target_disk_type in valid_types:
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=True,
                message=f"✓ Disk type '{config.target_disk_type}' is valid",
                details={"disk_type": config.target_disk_type}
            )
        else:
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=False,
                message=f"✗ Invalid disk type '{config.target_disk_type}'. Must be one of: {', '.join(valid_types)}",
                details={
                    "disk_type": config.target_disk_type,
                    "valid_types": valid_types,

                }
            )

    def validate_rbac_resource_group(
        self,
        config: MigrationConfig,
        user_object_id: str
    ) -> ValidationResult:
        """Validate user has Contributor role on target resource group"""
        try:
            auth_client = self._get_auth_client(config.target_subscription)
            resource_client = self._get_resource_client(
                config.target_subscription)

            # Get resource group
            rg = resource_client.resource_groups.get(config.target_rg)
            scope = rg.id

            # List role assignments for the user on this RG
            role_assignments = auth_client.role_assignments.list_for_scope(
                scope=scope,
                filter=f"principalId eq '{user_object_id}'"
            )

            # Check for Contributor role (or Owner)
            contributor_role_id = AZURE_ROLE_IDS["Contributor"]
            owner_role_id = AZURE_ROLE_IDS["Owner"]

            has_access = False
            assigned_roles = []

            for assignment in role_assignments:
                role_id = assignment.role_definition_id.split('/')[-1]
                assigned_roles.append(role_id)
                if role_id in [contributor_role_id, owner_role_id]:
                    has_access = True
                    break

            if has_access:
                return ValidationResult(
                    stage=ValidationStage.RBAC_TARGET_RG,
                    passed=True,
                    message=f"✓ User has Contributor/Owner access to resource group '{config.target_rg}'",
                    details={
                        "resource_group": config.target_rg,
                        "user_object_id": user_object_id,
                        "has_contributor": True,

                    }
                )
            else:
                return ValidationResult(
                    stage=ValidationStage.RBAC_TARGET_RG,
                    passed=False,
                    message=f"✗ User does not have Contributor/Owner access to resource group '{config.target_rg}'",
                    details={
                        "resource_group": config.target_rg,
                        "user_object_id": user_object_id,
                        "assigned_roles": assigned_roles,

                    }
                )

        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.RBAC_TARGET_RG,
                passed=False,
                message=f"✗ Error validating RBAC for resource group: {str(e)}",
                details={"error": str(e)}
            )

    def validate_discovery(
        self,
        config: MigrationConfig,
        project: AzureMigrateProject
    ) -> ValidationResult:
        """Validate that source machine is discovered in Azure Migrate project"""
        try:
            from ..clients.azure_client import AzureMigrateApiClient

            client = AzureMigrateApiClient(
                self.credential, project.subscription_id)
            search_name = config.source_machine_name or config.target_machine_name

            # Get discovered machines from the project using REST API
            discovered_machines = client.list_discovered_machines(
                project.resource_group,
                project.name
            )

            # Search for machine
            for machine in discovered_machines:
                properties = machine.get('properties', {})
                machine_name = machine.get('name', '')
                display_name = properties.get('displayName', machine_name)

                if (machine_name.lower() == search_name.lower() or
                        display_name.lower() == search_name.lower()):
                    return ValidationResult(
                        stage=ValidationStage.MIGRATE_DISCOVERY,
                        passed=True,
                        message=f"✓ Machine '{search_name}' found in Azure Migrate project '{project.name}'",
                        details={
                            "machine_name": search_name,
                            "project": project.name,
                            "machine_id": machine.get('id', ''),
                            "os": properties.get('operatingSystemType') or properties.get('operatingSystemName'),
                            "cores": properties.get('numberOfCores') or properties.get('cores'),
                            "memory_mb": properties.get('megabytesOfMemory') or properties.get('memoryInMB'),

                        }
                    )

            # Machine not found
            return ValidationResult(
                stage=ValidationStage.MIGRATE_DISCOVERY,
                passed=False,
                message=f"✗ Machine '{search_name}' not found in Azure Migrate project '{project.name}'",
                details={
                    "machine_name": search_name,
                    "project": project.name,

                }
            )

        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.MIGRATE_DISCOVERY,
                passed=False,
                message=f"✗ Error validating machine discovery: {str(e)}",
                details={"error": str(e)}
            )
