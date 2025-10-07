"""
Azure resource validators for migration configurations
"""
from typing import List, Optional, Dict
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..models import MigrationConfig, ValidationResult, ValidationStage
from ..constants import AZURE_REGIONS, AZURE_ROLE_IDS

console = Console()


class AzureValidator:
    """Validate Azure resources for migration"""

    def __init__(self, credential: Optional[DefaultAzureCredential] = None):
        self.credential = credential or DefaultAzureCredential()
        self._clients_cache: Dict[str, any] = {}

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

    def _get_network_client(self, subscription_id: str) -> NetworkManagementClient:
        """Get or create cached NetworkManagementClient"""
        key = f"network_{subscription_id}"
        if key not in self._clients_cache:
            self._clients_cache[key] = NetworkManagementClient(
                self.credential, subscription_id
            )
        return self._clients_cache[key]

    def _get_auth_client(self, subscription_id: str) -> AuthorizationManagementClient:
        """Get or create cached AuthorizationManagementClient"""
        key = f"auth_{subscription_id}"
        if key not in self._clients_cache:
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
                message=f"Region '{config.target_region}' is valid",
                details={"region": region}
            )
        else:
            return ValidationResult(
                stage=ValidationStage.AZURE_REGION,
                passed=False,
                message=f"Invalid region '{config.target_region}'. Must be a valid Azure region.",
                details={"region": region,
                         "valid_regions": AZURE_REGIONS[:10]}
            )

    def validate_resource_group(self, config: MigrationConfig) -> ValidationResult:
        """Validate that resource group exists"""
        try:
            client = self._get_resource_client(config.target_subscription)
            rg = client.resource_groups.get(config.target_rg)

            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=True,
                message=f"Resource group '{config.target_rg}' exists in subscription",
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
                message=f"Resource group '{config.target_rg}' not found in subscription '{config.target_subscription}'",
                details={"resource_group": config.target_rg}
            )
        except HttpResponseError as e:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"Error accessing resource group: {e.message}",
                details={"error": str(e)}
            )
        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"Unexpected error validating resource group: {str(e)}",
                details={"error": str(e)}
            )

    def validate_vnet_and_subnet(self, config: MigrationConfig) -> ValidationResult:
        """Validate that VNet and Subnet exist"""
        try:
            client = self._get_network_client(config.target_subscription)

            # Get VNet
            vnet = client.virtual_networks.get(
                config.target_rg, config.target_vnet)

            # Check if subnet exists in VNet
            subnet_found = False
            for subnet in vnet.subnets:
                if subnet.name == config.target_subnet:
                    subnet_found = True
                    return ValidationResult(
                        stage=ValidationStage.AZURE_RESOURCES,
                        passed=True,
                        message=f"VNet '{config.target_vnet}' and Subnet '{config.target_subnet}' exist",
                        details={
                            "vnet": config.target_vnet,
                            "subnet": config.target_subnet,
                            "subnet_prefix": subnet.address_prefix,
                            "vnet_id": vnet.id
                        }
                    )

            if not subnet_found:
                available_subnets = [s.name for s in vnet.subnets]
                return ValidationResult(
                    stage=ValidationStage.AZURE_RESOURCES,
                    passed=False,
                    message=f"Subnet '{config.target_subnet}' not found in VNet '{config.target_vnet}'",
                    details={
                        "vnet": config.target_vnet,
                        "requested_subnet": config.target_subnet,
                        "available_subnets": available_subnets
                    }
                )

        except ResourceNotFoundError:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"VNet '{config.target_vnet}' not found in resource group '{config.target_rg}'",
                details={"vnet": config.target_vnet, "rg": config.target_rg}
            )
        except HttpResponseError as e:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"Error accessing VNet: {e.message}",
                details={"error": str(e)}
            )
        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.AZURE_RESOURCES,
                passed=False,
                message=f"Unexpected error validating VNet/Subnet: {str(e)}",
                details={"error": str(e)}
            )

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
                            message=f"VM SKU '{config.target_machine_sku}' has restrictions in region '{region}'",
                            details={
                                "sku": config.target_machine_sku,
                                "region": region,
                                "restrictions": restriction_info
                            }
                        )

                    return ValidationResult(
                        stage=ValidationStage.DISK_AND_SKU,
                        passed=True,
                        message=f"VM SKU '{config.target_machine_sku}' is available in region '{region}'",
                        details={
                            "sku": config.target_machine_sku,
                            "region": region,
                            "capabilities": {c.name: c.value for c in sku.capabilities} if sku.capabilities else {}
                        }
                    )

            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=False,
                message=f"VM SKU '{config.target_machine_sku}' not available in region '{region}'",
                details={"sku": config.target_machine_sku, "region": region}
            )

        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=False,
                message=f"Error validating VM SKU: {str(e)}",
                details={"error": str(e)}
            )

    def validate_disk_type(self, config: MigrationConfig) -> ValidationResult:
        """Validate disk type is valid"""
        from ..models import DiskType

        valid_types = [dt.value for dt in DiskType]

        if config.target_disk_type in valid_types:
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=True,
                message=f"Disk type '{config.target_disk_type}' is valid",
                details={"disk_type": config.target_disk_type}
            )
        else:
            return ValidationResult(
                stage=ValidationStage.DISK_AND_SKU,
                passed=False,
                message=f"Invalid disk type '{config.target_disk_type}'. Must be one of: {', '.join(valid_types)}",
                details={"disk_type": config.target_disk_type,
                         "valid_types": valid_types}
            )

    def validate_rbac_resource_group(self, config: MigrationConfig, user_object_id: str) -> ValidationResult:
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
                    message=f"User has Contributor/Owner access to resource group '{config.target_rg}'",
                    details={
                        "resource_group": config.target_rg,
                        "user_object_id": user_object_id,
                        "has_contributor": True
                    }
                )
            else:
                return ValidationResult(
                    stage=ValidationStage.RBAC_TARGET_RG,
                    passed=False,
                    message=f"User does not have Contributor/Owner access to resource group '{config.target_rg}'",
                    details={
                        "resource_group": config.target_rg,
                        "user_object_id": user_object_id,
                        "assigned_roles": assigned_roles
                    }
                )

        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.RBAC_TARGET_RG,
                passed=False,
                message=f"Error validating RBAC for resource group: {str(e)}",
                details={"error": str(e)}
            )

    def validate_all(
        self,
        configs: List[MigrationConfig],
        skip_rbac: bool = False,
        user_object_id: Optional[str] = None
    ) -> Dict[str, List[ValidationResult]]:
        """
        Validate all configurations and return results

        Returns:
            Dictionary mapping machine name to list of validation results
        """
        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            task = progress.add_task(
                "[cyan]Validating configurations...",
                total=len(configs)
            )

            for config in configs:
                machine_results = []

                # Stage 1: Excel structure (already done)
                # Stage 2: Region validation
                machine_results.append(self.validate_region(config))

                # Stage 3: Resource validation
                machine_results.append(self.validate_resource_group(config))
                machine_results.append(self.validate_vnet_and_subnet(config))

                # Stage 4: Disk and SKU validation
                machine_results.append(self.validate_disk_type(config))
                machine_results.append(self.validate_vm_sku(config))

                # Stage 6: RBAC validation (if not skipped)
                if not skip_rbac and user_object_id:
                    machine_results.append(
                        self.validate_rbac_resource_group(
                            config, user_object_id)
                    )

                results[config.target_machine_name] = machine_results
                progress.advance(task)

        return results
