import api from './api';
import { projectsService } from './projects.service';
import type { LandingZoneConfig, LandingZoneCreate, Project } from '../types/project.types';
import type { PaginationParams, PaginatedResponse } from '../types/api.types';

export const landingZonesService = {
  // Get all projects with their landing zone status
  getAllProjects: async (params?: PaginationParams): Promise<PaginatedResponse<Project>> => {
    return projectsService.getAll(params);
  },

  // Get landing zone for a specific project
  getByProjectId: async (projectId: number): Promise<LandingZoneConfig> => {
    const response = await api.get(`/projects/${projectId}/landing-zone`);
    return response.data;
  },

  // Create or update landing zone for a project
  createOrUpdate: async (projectId: number, data: LandingZoneCreate): Promise<LandingZoneConfig> => {
    const response = await api.post(`/projects/${projectId}/landing-zone`, data);
    return response.data;
  },

  // Delete landing zone for a project
  delete: async (projectId: number): Promise<void> => {
    await api.delete(`/projects/${projectId}/landing-zone`);
  },
};
