"""
Azure Resources Service for discovering Azure infrastructure.

Provides API to fetch subscriptions, resource groups, VNets, and subnets
using authenticated Azure credentials.
"""

import logging
from typing import List, Dict, Any, Optional
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import AzureError
from sqlalchemy.orm import Session

from models import Project
from services.azure_auth_service import AzureAuthService

logger = logging.getLogger(__name__)


class AzureResourcesService:
    """Service to discover Azure resources via ARM APIs."""
    
    def __init__(self, db_session: Session):
        """Initialize Azure resources service."""
        self.db = db_session
        self.auth_service = AzureAuthService(db_session)
    
    def _get_credential(self, project_id: int):
        """Get Azure credential for a project."""
        try:
            # get_credential returns a tuple: (credential, auth_info)
            credential, auth_info = self.auth_service.get_credential(project_id)
            if not credential:
                raise ValueError("No authentication configured for this project")
            logger.debug(f"Retrieved credential for project {project_id} using method: {auth_info.get('method')}")
            return credential
        except Exception as e:
            logger.error(f"Failed to get credential for project {project_id}: {e}")
            raise
    
    def get_subscriptions(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get list of Azure subscriptions accessible by the authenticated principal.
        
        Args:
            project_id: Project ID with configured authentication
            
        Returns:
            List of subscription objects with id, name, and state
        """
        try:
            credential = self._get_credential(project_id)
            subscription_client = SubscriptionClient(credential)
            
            subscriptions = []
            for sub in subscription_client.subscriptions.list():
                subscriptions.append({
                    "subscription_id": sub.subscription_id,
                    "display_name": sub.display_name,
                    "state": sub.state,
                    "tenant_id": sub.tenant_id,
                })
            
            logger.info(f"Found {len(subscriptions)} subscriptions for project {project_id}")
            return subscriptions
            
        except AzureError as e:
            logger.error(f"Azure API error fetching subscriptions: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching subscriptions for project {project_id}: {e}")
            raise
    
    def get_resource_groups(
        self, 
        project_id: int, 
        subscription_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of resource groups in a subscription.
        
        Args:
            project_id: Project ID with configured authentication
            subscription_id: Target Azure subscription ID
            
        Returns:
            List of resource group objects with name, location, and id
        """
        try:
            credential = self._get_credential(project_id)
            resource_client = ResourceManagementClient(credential, subscription_id)
            
            resource_groups = []
            for rg in resource_client.resource_groups.list():
                resource_groups.append({
                    "name": rg.name,
                    "location": rg.location,
                    "id": rg.id,
                    "tags": rg.tags or {},
                })
            
            logger.info(f"Found {len(resource_groups)} resource groups in subscription {subscription_id}")
            return resource_groups
            
        except AzureError as e:
            logger.error(f"Azure API error fetching resource groups: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching resource groups: {e}")
            raise
    
    def get_vnets(
        self, 
        project_id: int, 
        subscription_id: str,
        resource_group_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of Virtual Networks in a subscription or resource group.
        
        Args:
            project_id: Project ID with configured authentication
            subscription_id: Target Azure subscription ID
            resource_group_name: Optional resource group to filter VNets
            
        Returns:
            List of VNet objects with name, location, address space, and resource group
        """
        try:
            credential = self._get_credential(project_id)
            network_client = NetworkManagementClient(credential, subscription_id)
            
            vnets = []
            
            if resource_group_name:
                # List VNets in specific resource group
                vnet_list = network_client.virtual_networks.list(resource_group_name)
            else:
                # List all VNets in subscription
                vnet_list = network_client.virtual_networks.list_all()
            
            for vnet in vnet_list:
                # Extract resource group from resource ID
                rg_name = vnet.id.split('/')[4] if '/' in vnet.id else None
                
                vnets.append({
                    "name": vnet.name,
                    "location": vnet.location,
                    "resource_group": rg_name,
                    "address_space": vnet.address_space.address_prefixes if vnet.address_space else [],
                    "id": vnet.id,
                })
            
            logger.info(f"Found {len(vnets)} VNets in subscription {subscription_id}")
            return vnets
            
        except AzureError as e:
            logger.error(f"Azure API error fetching VNets: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching VNets: {e}")
            raise
    
    def get_subnets(
        self,
        project_id: int,
        subscription_id: str,
        resource_group_name: str,
        vnet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of subnets in a specific Virtual Network.
        
        Args:
            project_id: Project ID with configured authentication
            subscription_id: Target Azure subscription ID
            resource_group_name: Resource group containing the VNet
            vnet_name: Virtual Network name
            
        Returns:
            List of subnet objects with name, address prefix, and id
        """
        try:
            credential = self._get_credential(project_id)
            network_client = NetworkManagementClient(credential, subscription_id)
            
            subnets = []
            for subnet in network_client.subnets.list(resource_group_name, vnet_name):
                subnets.append({
                    "name": subnet.name,
                    "address_prefix": subnet.address_prefix,
                    "id": subnet.id,
                    "available_ips": subnet.available_ip_address_count,
                })
            
            logger.info(f"Found {len(subnets)} subnets in VNet {vnet_name}")
            return subnets
            
        except AzureError as e:
            logger.error(f"Azure API error fetching subnets: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching subnets: {e}")
            raise
    
    def get_locations(self, project_id: int, subscription_id: str) -> List[Dict[str, Any]]:
        """
        Get list of available Azure locations for a subscription.
        
        Args:
            project_id: Project ID with configured authentication
            subscription_id: Target Azure subscription ID
            
        Returns:
            List of location objects with name, display name, and region
        """
        try:
            credential = self._get_credential(project_id)
            subscription_client = SubscriptionClient(credential)
            
            locations = []
            for location in subscription_client.subscriptions.list_locations(subscription_id):
                locations.append({
                    "name": location.name,
                    "display_name": location.display_name,
                    "regional_display_name": location.regional_display_name,
                })
            
            logger.info(f"Found {len(locations)} locations for subscription {subscription_id}")
            return locations
            
        except AzureError as e:
            logger.error(f"Azure API error fetching locations: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching locations: {e}")
            raise
    
    def get_storage_accounts(
        self,
        project_id: int,
        subscription_id: str,
        resource_group_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of storage accounts in a subscription or resource group.
        
        Args:
            project_id: Project ID with configured authentication
            subscription_id: Target Azure subscription ID
            resource_group_name: Optional resource group to filter storage accounts
            
        Returns:
            List of storage account objects with name, location, kind, and SKU
        """
        try:
            credential = self._get_credential(project_id)
            storage_client = StorageManagementClient(credential, subscription_id)
            
            storage_accounts = []
            
            if resource_group_name:
                # List storage accounts in specific resource group
                account_list = storage_client.storage_accounts.list_by_resource_group(resource_group_name)
            else:
                # List all storage accounts in subscription
                account_list = storage_client.storage_accounts.list()
            
            for account in account_list:
                # Extract resource group from resource ID
                rg_name = account.id.split('/')[4] if '/' in account.id else None
                
                storage_accounts.append({
                    "name": account.name,
                    "location": account.location,
                    "resource_group": rg_name,
                    "kind": account.kind,
                    "sku_name": account.sku.name if account.sku else None,
                    "sku_tier": account.sku.tier if account.sku else None,
                    "id": account.id,
                })
            
            logger.info(f"Found {len(storage_accounts)} storage accounts in subscription {subscription_id}")
            return storage_accounts
            
        except AzureError as e:
            logger.error(f"Azure API error fetching storage accounts: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching storage accounts: {e}")
            raise

    def get_migrate_projects(
        self,
        project_id: int,
        subscription_id: str,
        resource_group_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of Azure Migrate projects in a resource group.
        
        Args:
            project_id: Project ID with configured authentication
            subscription_id: Target Azure subscription ID
            resource_group_name: Resource group containing migrate projects
            
        Returns:
            List of migrate project objects with name, location, and properties
        """
        try:
            credential = self._get_credential(project_id)
            
            # Use ResourceManagementClient to list migrate projects
            resource_client = ResourceManagementClient(credential, subscription_id)
            
            migrate_projects = []
            
            # Azure Migrate projects can have multiple resource types:
            # - Microsoft.Migrate/assessmentProjects (legacy)
            # - Microsoft.Migrate/migrateProjects (current)
            # List all resources and filter for Migrate types
            all_resources = resource_client.resources.list_by_resource_group(resource_group_name)
            
            for resource in all_resources:
                # Check if resource type contains 'Migrate' and matches known project types
                if resource.type and 'Microsoft.Migrate/' in resource.type:
                    if any(project_type in resource.type.lower() for project_type in ['assessmentproject', 'migrateproject']):
                        migrate_projects.append({
                            "name": resource.name,
                            "location": resource.location,
                            "id": resource.id,
                            "type": resource.type,
                        })
                        logger.debug(f"Found migrate project: {resource.name} (type: {resource.type})")
            
            logger.info(f"Found {len(migrate_projects)} migrate projects in {resource_group_name}")
            return migrate_projects
            
        except AzureError as e:
            logger.error(f"Azure API error fetching migrate projects: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching migrate projects: {e}")
            raise

    def get_migrate_appliances(
        self,
        project_id: int,
        subscription_id: str,
        resource_group_name: str,
        migrate_project_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of Azure Migrate appliances for a specific migrate project.
        
        Args:
            project_id: Project ID with configured authentication
            subscription_id: Target Azure subscription ID
            resource_group_name: Resource group containing the migrate project
            migrate_project_name: Name of the migrate project
            
        Returns:
            List of appliance objects with name, type, and health status
        """
        try:
            credential = self._get_credential(project_id)
            resource_client = ResourceManagementClient(credential, subscription_id)
            
            appliances = []
            
            # List all resources in the resource group and filter for appliance types
            # Azure Migrate appliances can be of types:
            # - Microsoft.OffAzure/VMwareSites (VMware)
            # - Microsoft.OffAzure/HyperVSites (Hyper-V)
            # - Microsoft.OffAzure/ServerSites (Physical servers)
            # - Microsoft.Migrate/assessmentProjects/vmwarecollectors
            # - Microsoft.Migrate/assessmentProjects/hypervcollectors
            
            all_resources = resource_client.resources.list_by_resource_group(resource_group_name)
            
            for resource in all_resources:
                if not resource.type:
                    continue
                    
                resource_type = resource.type.lower()
                appliance_type = None
                
                # Determine appliance type based on resource type
                if 'vmware' in resource_type:
                    appliance_type = 'VMware'
                elif 'hyperv' in resource_type:
                    appliance_type = 'Hyper-V'
                elif 'server' in resource_type or 'physical' in resource_type:
                    appliance_type = 'Physical'
                
                # Include if it's an appliance-related resource
                if appliance_type or 'collector' in resource_type or 'site' in resource_type:
                    # Additional check: ensure it's related to Azure Migrate
                    if 'microsoft.offazure' in resource_type or 'microsoft.migrate' in resource_type:
                        appliances.append({
                            "name": resource.name,
                            "appliance_type": appliance_type or 'Unknown',
                            "resource_type": resource.type,
                            "location": resource.location,
                            "id": resource.id,
                        })
                        logger.debug(f"Found appliance: {resource.name} (type: {appliance_type}, resource_type: {resource.type})")
            
            logger.info(f"Found {len(appliances)} appliances in {resource_group_name}")
            return appliances
            
        except AzureError as e:
            logger.error(f"Azure API error fetching migrate appliances: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching migrate appliances: {e}")
            raise
