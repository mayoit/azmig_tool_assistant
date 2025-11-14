export interface ServerConfig {
  id: number;
  project_id: number;
  target_machine_name: string;
  target_region: string;
  target_subscription: string;
  target_resource_group: string;
  target_vnet: string;
  target_subnet: string;
  target_machine_sku: string;
  target_disk_type: string;
  
  // Appliance selection - links to Landing Zone configuration
  appliance_id?: number | null;  // ID reference to LZ migrate project appliance
  
  // Auto-populated fields based on appliance_id (from Landing Zone)
  migrate_project_name?: string | null;
  appliance_name?: string | null;
  appliance_type?: string | null;
  recovery_vault_name?: string | null;
  cache_storage_account?: string | null;
  cache_storage_rg?: string | null;
  
  created_at: string;
  updated_at: string;
}

export interface ServerConfigCreate {
  target_machine_name: string;
  target_region: string;
  target_subscription: string;
  target_resource_group: string;
  target_vnet: string;
  target_subnet: string;
  target_machine_sku: string;
  target_disk_type: string;
  appliance_id?: number | null;
  migrate_project_name?: string | null;
  appliance_name?: string | null;
  appliance_type?: string | null;
  recovery_vault_name?: string | null;
  cache_storage_account?: string | null;
  cache_storage_rg?: string | null;
}

export interface ServerUploadResponse {
  servers_created: number;
  servers_updated: number;
  total_servers: number;
  warnings?: string[];
}

export interface MigrationSettings {
  allowed_regions: string[];
  allowed_vm_skus: string[];
  allowed_disk_types: string[];
}
