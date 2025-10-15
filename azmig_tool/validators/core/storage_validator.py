"""
Storage Validator - Cache storage account validation

Handles validation of Azure Storage accounts used for migration caching:
- Storage account existence and accessibility
- Region consistency validation
- Storage SKU validation
- Auto-creation capabilities
"""
from azure.core.credentials import TokenCredential
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import ResourceNotFoundError

from ...core.models import (
    MigrateProjectConfig,
    StorageCacheResult,
    ValidationStatus,
    StorageCacheInfo
)


class StorageValidator:
    """
    Validates cache storage accounts for Azure Migrate operations
    
    Checks:
    - Storage account existence
    - Region alignment with migrate project
    - Storage SKU appropriateness
    - Can auto-create missing storage accounts
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize storage validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._storage_clients = {}

    def _get_storage_client(self, subscription_id: str) -> StorageManagementClient:
        """Get or create cached StorageManagementClient"""
        if subscription_id not in self._storage_clients:
            self._storage_clients[subscription_id] = StorageManagementClient(
                self.credential, subscription_id
            )
        return self._storage_clients[subscription_id]

    def validate(self, config: MigrateProjectConfig, auto_create: bool = False) -> StorageCacheResult:
        """
        Validate cache storage account for replication

        Args:
            config: Migrate project configuration
            auto_create: If True, create storage account if missing

        Returns:
            StorageCacheResult with storage validation details
        """
        try:
            # Check if storage account is specified
            if not config.cache_storage_account:
                return StorageCacheResult(
                    subscription_id=config.subscription_id,
                    region=config.region,
                    status=ValidationStatus.WARNING,
                    storage_info=None,
                    message="No cache storage account specified",
                    auto_created=False
                )

            storage_client = self._get_storage_client(config.subscription_id)

            # Check if storage account exists
            try:
                storage_account = storage_client.storage_accounts.get_properties(
                    config.cache_storage_resource_group,
                    config.cache_storage_account
                )
                
                return self._validate_existing_storage(storage_account, config)

            except ResourceNotFoundError:
                # Storage account doesn't exist
                if auto_create:
                    return self._create_storage_account(config)
                else:
                    return StorageCacheResult(
                        subscription_id=config.subscription_id,
                        region=config.region,
                        status=ValidationStatus.FAILED,
                        storage_info=None,
                        message=f"Cache storage account '{config.cache_storage_account}' not found",
                        auto_created=False
                    )

        except Exception as e:
            return StorageCacheResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=ValidationStatus.FAILED,
                storage_info=None,
                message=f"Error validating storage cache: {str(e)}",
                auto_created=False
            )

    def _validate_existing_storage(self, storage_account, config: MigrateProjectConfig) -> StorageCacheResult:
        """
        Validate an existing storage account

        Args:
            storage_account: Azure storage account object
            config: Project configuration

        Returns:
            StorageCacheResult with validation details
        """
        # Validate region alignment
        storage_region = storage_account.location.lower().replace(' ', '')
        config_region = config.region.lower().replace(' ', '')
        
        if storage_region != config_region:
            return StorageCacheResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=ValidationStatus.WARNING,
                storage_info=StorageCacheInfo(
                    account_name=config.cache_storage_account,
                    subscription_id=config.subscription_id,
                    resource_group=config.cache_storage_resource_group,
                    region=storage_account.location,
                    sku=storage_account.sku.name if storage_account.sku else "Unknown",
                    exists=True,
                    created_by_tool=False
                ),
                message=f"Storage account exists but in different region ({storage_account.location} vs {config.region})",
                auto_created=False
            )

        # Storage account is valid
        return StorageCacheResult(
            subscription_id=config.subscription_id,
            region=config.region,
            status=ValidationStatus.OK,
            storage_info=StorageCacheInfo(
                account_name=config.cache_storage_account,
                subscription_id=config.subscription_id,
                resource_group=config.cache_storage_resource_group,
                region=storage_account.location,
                sku=storage_account.sku.name if storage_account.sku else "Unknown",
                exists=True,
                created_by_tool=False
            ),
            message=f"Cache storage account '{config.cache_storage_account}' validated",
            auto_created=False
        )

    def _create_storage_account(self, config: MigrateProjectConfig) -> StorageCacheResult:
        """
        Create cache storage account for Azure Migrate replication

        Args:
            config: Project configuration

        Returns:
            StorageCacheResult with creation status
        """
        try:
            from azure.mgmt.storage.models import (
                StorageAccountCreateParameters,
                Sku,
                Kind
            )

            storage_client = self._get_storage_client(config.subscription_id)

            # Generate storage account name if not provided
            storage_name = config.cache_storage_account
            if not storage_name:
                region_short = config.region[:6].replace('-', '')
                import random
                storage_name = f"stmigcache{region_short}{random.randint(1000, 9999)}"

            # Create storage account with recommended settings
            create_params = StorageAccountCreateParameters(
                sku=Sku(name="Standard_LRS"),  # Recommended for cache storage
                kind=Kind.STORAGE_V2,
                location=config.region,
                tags={
                    "Purpose": "Azure Migrate Cache",
                    "CreatedBy": "azmig_tool"
                }
            )

            # Start async creation
            poller = storage_client.storage_accounts.begin_create(
                config.cache_storage_resource_group,
                storage_name,
                create_params
            )

            # Wait for completion
            storage_account = poller.result()

            storage_info = StorageCacheInfo(
                account_name=storage_name,
                subscription_id=config.subscription_id,
                resource_group=config.cache_storage_resource_group,
                region=storage_account.location,
                sku=storage_account.sku.name if storage_account.sku else "Unknown",
                exists=True,
                created_by_tool=True
            )

            return StorageCacheResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=ValidationStatus.OK,
                storage_info=storage_info,
                message=f"Created cache storage account '{storage_name}'",
                auto_created=True
            )

        except Exception as e:
            return StorageCacheResult(
                subscription_id=config.subscription_id,
                region=config.region,
                status=ValidationStatus.FAILED,
                storage_info=None,
                message=f"Error creating storage account: {str(e)}",
                auto_created=False
            )