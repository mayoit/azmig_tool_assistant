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
}

export interface ServerUploadResponse {
  servers_created: number;
  servers_updated: number;
  total_servers: number;
}
