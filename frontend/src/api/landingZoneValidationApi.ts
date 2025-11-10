import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

interface ValidationResult {
  status: string;
  message?: string;
  details?: string;
}

interface MigrateProjectValidation {
  id: number;
  project_id: number;
  migrate_project_index: number;
  status: string;
  overall_status: string;
  access_result?: ValidationResult;
  appliance_result?: ValidationResult;
  storage_result?: ValidationResult;
  quota_result?: ValidationResult;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

interface ValidateMigrateProjectRequest {
  force_revalidate?: boolean;
}

interface ValidateMigrateProjectResponse {
  success: boolean;
  validation_id?: number;
  status?: string;
  error?: string;
  results?: {
    access?: ValidationResult;
    appliance?: ValidationResult;
    storage?: ValidationResult;
    quota?: ValidationResult;
  };
  started_at?: string;
  completed_at?: string;
}

export function useValidateMigrateProject(projectId: number, migrateProjectIndex: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: ValidateMigrateProjectRequest = {}) => {
      const { data } = await api.post<ValidateMigrateProjectResponse>(
        `/projects/${projectId}/landing-zones/migrate-projects/${migrateProjectIndex}/validate`,
        request
      );
      return data;
    },
    onSuccess: () => {
      // Invalidate and refetch validation results
      queryClient.invalidateQueries({ 
        queryKey: ['migrateProjectValidation', projectId, migrateProjectIndex] 
      });
      queryClient.invalidateQueries({ 
        queryKey: ['landingZoneValidations', projectId] 
      });
    },
  });
}

export function useMigrateProjectValidationResult(
  projectId: number, 
  migrateProjectIndex: number,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: ['migrateProjectValidation', projectId, migrateProjectIndex],
    queryFn: async () => {
      const { data } = await api.get<MigrateProjectValidation>(
        `/projects/${projectId}/landing-zones/migrate-projects/${migrateProjectIndex}/validation-result`
      );
      return data;
    },
    enabled,
    retry: false,
  });
}

export function useLandingZoneValidations(projectId: number) {
  return useQuery({
    queryKey: ['landingZoneValidations', projectId],
    queryFn: async () => {
      // For now, we'll fetch all migrate project validations
      // Later we can add a dedicated endpoint to get all LZ validations
      const { data } = await api.get<MigrateProjectValidation[]>(
        `/projects/${projectId}/landing-zones/validations`
      );
      return data;
    },
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
    retry: false,
  });
}
