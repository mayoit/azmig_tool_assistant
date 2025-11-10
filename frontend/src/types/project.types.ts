export interface LandingZoneAppZone {
  subscriptionId: string;
  subscriptionName?: string;  // Display name for the subscription
  region: string;
  cacheStorageAccount: string;
  cacheStorageResourceGroup: string;
  allowedSkus?: string[];
  isNewResource?: boolean;
}

export interface MigrationSettings {
  allowed_regions: string[];
  allowed_vm_skus: string[];
  allowed_disk_types: string[];
}

export interface LandingZoneMigrateProject {
  id?: number;  // Database ID for server appliance reference
  migrateProjectSubscription: string;
  migrateResourceGroup: string;
  migrateProjectName: string;
  applianceType?: string;
  applianceName: string;
  recoveryVaultName: string;
  appLandingZones: LandingZoneAppZone[];
}

export interface ValidationSettings {
  global: {
    fail_fast: boolean;
    parallel_execution: boolean;
    timeout_seconds: number;
  };
  landing_zone: {
    access_validation: {
      enabled: boolean;
      checks: {
        migrate_project_rbac: {
          enabled: boolean;
        };
        recovery_vault_rbac: {
          enabled: boolean;
        };
        subscription_rbac: {
          enabled: boolean;
        };
      };
    };
    access_validation_checks: {
      migrate_project_rbac: {
        enabled: boolean;
      };
      recovery_vault_rbac: {
        enabled: boolean;
      };
      subscription_rbac: {
        enabled: boolean;
      };
    };
    appliance_health: {
      enabled: boolean;
    };
    storage_cache: {
      enabled: boolean;
      auto_create_if_missing: boolean;
    };
    quota_validation: {
      enabled: boolean;
    };
  };
  servers: {
    region_validation: {
      enabled: boolean;
    };
    resource_group_validation: {
      enabled: boolean;
    };
    vnet_subnet_validation: {
      enabled: boolean;
    };
    vm_sku_validation: {
      enabled: boolean;
    };
    disk_type_validation: {
      enabled: boolean;
    };
    discovery_validation: {
      enabled: boolean;
    };
    rbac_validation: {
      enabled: boolean;
    };
  };
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  azure_tenant_id: string;  // Changed from azure_subscription_id - each project belongs to a tenant
  status: 'active' | 'in_progress' | 'completed' | 'archived';
  metadata_json?: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
  owner_id: number;
  owner?: {
    id: number;
    email: string;
    full_name?: string;
    role: string;
    is_active: boolean;
    created_at: string;
    last_login?: string;
  };
  servers_count: number;
  validations_count: number;
  lz_migrate_projects?: LandingZoneMigrateProject[];  // Each landing zone has its own subscriptionId
  landing_zone?: LandingZoneConfig;
  validation_settings?: ValidationSettings;
  migration_settings?: MigrationSettings;
  auth_method?: string;  // azure_cli, service_principal, managed_identity
}

export interface ProjectCreate {
  name: string;
  description?: string;
  azure_tenant_id: string;  // Changed from azure_subscription_id - required tenant ID
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  azure_tenant_id?: string;  // Changed from azure_subscription_id
  is_active?: boolean;
}

export interface LandingZoneConfig {
  id: number;
  project_id: number;
  migrate_project_name: string;
  migrate_project_rg: string;
  recovery_vault_name: string;
  recovery_vault_rg: string;
  cache_storage_account: string;
  cache_storage_rg: string;
  appliance_name: string;
  created_at: string;
  updated_at: string;
}

export interface LandingZoneCreate {
  migrate_project_name: string;
  migrate_project_rg: string;
  recovery_vault_name: string;
  recovery_vault_rg: string;
  cache_storage_account: string;
  cache_storage_rg: string;
  appliance_name: string;
}
