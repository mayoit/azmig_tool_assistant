import api from './api';
import type { ValidationJob, ValidationResult } from '../types/validation.types';
import type { PaginationParams, PaginatedResponse } from '../types/api.types';

export const validationsService = {
  getJobs: async (projectId: number, params?: PaginationParams): Promise<PaginatedResponse<ValidationJob>> => {
    const response = await api.get(`/api/projects/${projectId}/validations`, { params });
    return response.data;
  },

  getJobDetails: async (jobId: number): Promise<ValidationJob> => {
    const response = await api.get(`/api/validations/${jobId}`);
    return response.data;
  },

  triggerValidation: async (projectId: number): Promise<ValidationJob> => {
    const response = await api.post(`/api/projects/${projectId}/validate`);
    return response.data;
  },

  getResults: async (
    jobId: number,
    params?: { stage?: string; passed?: boolean } & PaginationParams
  ): Promise<PaginatedResponse<ValidationResult>> => {
    const response = await api.get(`/api/validations/${jobId}/results`, { params });
    return response.data;
  },

  exportResults: async (jobId: number, format: 'csv' | 'xlsx' = 'xlsx'): Promise<Blob> => {
    const response = await api.get(`/api/validations/${jobId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },
};
