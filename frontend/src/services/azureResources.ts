/**
 * Azure Resources Service
 * Provides API calls to fetch Azure subscriptions, resource groups, VNets, and subnets
 */

import api from './api';

export interface AzureSubscription {
  subscription_id: string;
  display_name: string;
  state: string;
  tenant_id: string;
}

export interface AzureResourceGroup {
  name: string;
  location: string;
  id: string;
  tags: Record<string, string>;
}

export interface AzureVNet {
  name: string;
  location: string;
  resource_group: string;
  address_space: string[];
  id: string;
}

export interface AzureSubnet {
  name: string;
  address_prefix: string;
  id: string;
  available_ips: number;
}

export interface AzureLocation {
  name: string;
  display_name: string;
  regional_display_name: string;
}

export interface AzureStorageAccount {
  name: string;
  location: string;
  resource_group: string;
  kind: string;
  sku_name: string;
  sku_tier: string;
  id: string;
}

export interface AzureMigrateProject {
  name: string;
  location: string;
  id: string;
  properties: Record<string, any>;
}

export interface AzureMigrateAppliance {
  name: string;
  type: string;
  properties: {
    health_status?: string;
    service_principal_identity_details?: Record<string, any>;
  };
}

class AzureResourcesService {
  /**
   * Get list of Azure subscriptions for a project
   */
  async getSubscriptions(projectId: number): Promise<AzureSubscription[]> {
    const response = await api.get(`/projects/${projectId}/azure/subscriptions`);
    return response.data.subscriptions;
  }

  /**
   * Get list of resource groups in a subscription
   */
  async getResourceGroups(
    projectId: number,
    subscriptionId: string
  ): Promise<AzureResourceGroup[]> {
    const response = await api.get(`/projects/${projectId}/azure/resource-groups`, {
      params: { subscription_id: subscriptionId },
    });
    return response.data.resource_groups;
  }

  /**
   * Get list of VNets in a subscription or resource group
   */
  async getVNets(
    projectId: number,
    subscriptionId: string,
    resourceGroup?: string
  ): Promise<AzureVNet[]> {
    const params: Record<string, string> = { subscription_id: subscriptionId };
    if (resourceGroup) {
      params.resource_group = resourceGroup;
    }
    
    const response = await api.get(`/projects/${projectId}/azure/vnets`, { params });
    return response.data.vnets;
  }

  /**
   * Get list of subnets in a VNet
   */
  async getSubnets(
    projectId: number,
    subscriptionId: string,
    resourceGroup: string,
    vnetName: string
  ): Promise<AzureSubnet[]> {
    const response = await api.get(`/projects/${projectId}/azure/subnets`, {
      params: {
        subscription_id: subscriptionId,
        resource_group: resourceGroup,
        vnet_name: vnetName,
      },
    });
    return response.data.subnets;
  }

  /**
   * Get list of available Azure locations for a subscription
   */
  async getLocations(
    projectId: number,
    subscriptionId: string
  ): Promise<AzureLocation[]> {
    const response = await api.get(`/projects/${projectId}/azure/locations`, {
      params: { subscription_id: subscriptionId },
    });
    return response.data.locations;
  }

  /**
   * Get list of storage accounts in a subscription or resource group
   */
  async getStorageAccounts(
    projectId: number,
    subscriptionId: string,
    resourceGroup?: string
  ): Promise<AzureStorageAccount[]> {
    const params: Record<string, string> = { subscription_id: subscriptionId };
    if (resourceGroup) {
      params.resource_group = resourceGroup;
    }
    
    const response = await api.get(`/projects/${projectId}/azure/storage-accounts`, { params });
    return response.data.storage_accounts;
  }

  /**
   * Get list of Azure Migrate projects in a resource group
   */
  async getMigrateProjects(
    projectId: number,
    subscriptionId: string,
    resourceGroup: string
  ): Promise<Array<{ name: string; location: string; id: string; type: string }>> {
    const response = await api.get(`/projects/${projectId}/azure/migrate-projects`, {
      params: {
        subscription_id: subscriptionId,
        resource_group: resourceGroup,
      },
    });
    return response.data.migrate_projects;
  }

  /**
   * Get list of Azure Migrate appliances for a migrate project
   */
  async getMigrateAppliances(
    projectId: number,
    subscriptionId: string,
    resourceGroup: string,
    migrateProjectName: string
  ): Promise<Array<{ name: string; appliance_type: string; resource_type: string; location: string; id: string }>> {
    const response = await api.get(`/projects/${projectId}/azure/migrate-appliances`, {
      params: {
        subscription_id: subscriptionId,
        resource_group: resourceGroup,
        migrate_project_name: migrateProjectName,
      },
    });
    return response.data.appliances;
  }
}

export default new AzureResourcesService();
