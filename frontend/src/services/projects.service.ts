import api from './api';
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  LandingZoneCreate,
  LandingZoneConfig,
  LandingZoneMigrateProject,
  LandingZoneAppZone,
} from '../types/project.types';
import type { PaginationParams, PaginatedResponse } from '../types/api.types';

const readString = (source: Record<string, unknown>, keys: string[], fallback = ''): string => {
  for (const key of keys) {
    const value = source[key];
    if (value !== undefined && value !== null) {
      return String(value);
    }
  }
  return fallback;
};

const mapLandingZoneAppZones = (rawZones: unknown): LandingZoneAppZone[] => {
  if (!Array.isArray(rawZones)) {
    return [];
  }

  return rawZones.map((zone) => {
    const record = (zone ?? {}) as Record<string, unknown>;
    return {
      subscriptionId: readString(record, ['Subscription ID', 'subscription_id', 'subscriptionId']),
      cacheStorageAccount: readString(record, ['Cache Storage Account', 'cache_storage_account', 'cacheStorageAccount']),
      region: readString(record, ['Region', 'region']),
      cacheStorageResourceGroup: readString(
        record,
        ['Cache Storage Resource Group', 'cache_storage_resource_group', 'cacheStorageResourceGroup']
      ),
    };
  });
};

const mapLandingZoneProjects = (candidate: unknown): LandingZoneMigrateProject[] => {
  if (!Array.isArray(candidate)) {
    return [];
  }

  return candidate.map((item) => {
    const record = (item ?? {}) as Record<string, unknown>;
    const appZonesCandidate = record['app_landing_zones'] ?? record['appLandingZones'];

    const migrateProjectSubscription = readString(
      record,
      ['Migrate Project Subscription', 'migrate_project_subscription', 'migrateProjectSubscription']
    );
    const migrateResourceGroup = readString(record, ['Migrate Resource Group', 'migrate_resource_group', 'migrateResourceGroup']);
    const migrateProjectName = readString(record, ['Migrate Project Name', 'migrate_project_name', 'migrateProjectName']);
    const applianceType = readString(record, ['Appliance Type', 'appliance_type', 'applianceType']);
    const applianceName = readString(record, ['Appliance Name', 'appliance_name', 'applianceName']);
    const recoveryVaultName = readString(record, ['Recovery Vault Name', 'recovery_vault_name', 'recoveryVaultName']);

    return {
      migrateProjectSubscription,
      migrateResourceGroup,
      migrateProjectName,
      applianceType: applianceType || undefined,
      applianceName,
      recoveryVaultName,
      appLandingZones: mapLandingZoneAppZones(appZonesCandidate),
    };
  });
};

const normalizeProject = (project: Project): Project => {
  const normalized: Project = { ...project };
  const rawCandidate = (project as unknown as { lz_migrate_projects?: unknown }).lz_migrate_projects;
  const metadata = project.metadata_json as Record<string, unknown> | undefined;
  const metadataCandidate = metadata
    ? ((metadata as unknown) as { lz_migrate_projects?: unknown }).lz_migrate_projects
    : undefined;

  const projects = mapLandingZoneProjects(rawCandidate ?? metadataCandidate);
  normalized.lz_migrate_projects = projects;

  return normalized;
};

export const projectsService = {
  getAll: async (params?: PaginationParams): Promise<PaginatedResponse<Project>> => {
    const response = await api.get('/projects', { params });
    const data = response.data as PaginatedResponse<Project>;
    return {
      ...data,
      items: data.items.map((project) => normalizeProject(project)),
    };
  },

  getById: async (id: number): Promise<Project> => {
    const response = await api.get(`/projects/${id}`);
    return normalizeProject(response.data as Project);
  },

  create: async (data: ProjectCreate): Promise<Project> => {
    const response = await api.post('/projects', data);
    return response.data;
  },

  update: async (id: number, data: ProjectUpdate): Promise<Project> => {
    const response = await api.put(`/projects/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/projects/${id}`);
  },

  getLandingZone: async (projectId: number): Promise<LandingZoneConfig | null> => {
    try {
      const response = await api.get(`/projects/${projectId}/landing-zone`);
      return response.data;
    } catch (error: unknown) {
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          return null;
        }
      }
      throw error;
    }
  },

  createLandingZone: async (projectId: number, data: LandingZoneCreate): Promise<LandingZoneConfig> => {
    const response = await api.post(`/projects/${projectId}/landing-zone`, data);
    return response.data;
  },

  updateLandingZone: async (projectId: number, data: Partial<LandingZoneCreate>): Promise<LandingZoneConfig> => {
    const response = await api.put(`/projects/${projectId}/landing-zone`, data);
    return response.data;
  },
};
