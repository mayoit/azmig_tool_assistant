/**
 * API functions for Landing Zone validation
 */

import api from '../services/api';

export interface ValidateMigrateProjectRequest {
  force_revalidate?: boolean;
}

export interface ValidationResult {
  success: boolean;
  validation_id?: number;
  status?: string;
  error?: string;
  results?: {
    access?: object;
    appliance?: object;
    storage?: object;
    quota?: object;
  };
  started_at?: string;
  completed_at?: string;
}

export interface MigrateProjectValidationResult {
  id: number;
  status: string;
  overall_status: string;
  access_result?: object;
  appliance_result?: object;
  storage_result?: object;
  quota_result?: object;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
}

/**
 * Validate a migrate project against Azure
 */
export const validateMigrateProject = async (
  projectId: number,
  migrateProjectIndex: number,
  forceRevalidate: boolean = false
): Promise<ValidationResult> => {
  const response = await api.post<ValidationResult>(
    `/projects/${projectId}/landing-zones/migrate-projects/${migrateProjectIndex}/validate`,
    { force_revalidate: forceRevalidate }
  );
  return response.data;
};

/**
 * Get the latest validation result for a migrate project
 */
export const getMigrateProjectValidationResult = async (
  projectId: number,
  migrateProjectIndex: number
): Promise<MigrateProjectValidationResult> => {
  const response = await api.get<MigrateProjectValidationResult>(
    `/projects/${projectId}/landing-zones/migrate-projects/${migrateProjectIndex}/validation-result`
  );
  return response.data;
};
