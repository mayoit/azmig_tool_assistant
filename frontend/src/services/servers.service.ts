import api from './api';
import type { ServerConfig, ServerConfigCreate, ServerUploadResponse } from '../types/server.types';
import type { PaginationParams, PaginatedResponse } from '../types/api.types';

export const serversService = {
  getAll: async (projectId: number, params?: PaginationParams): Promise<PaginatedResponse<ServerConfig>> => {
    const response = await api.get(`/projects/${projectId}/servers`, {
      params: {
        page: params?.page ?? 1,
        page_size: params?.limit ?? 10,
      },
    });

    const data = response.data as {
      items: ServerConfig[];
      total: number;
      page: number;
      page_size: number;
      pages: number;
    };

    return {
      items: data.items,
      total: data.total,
      page: data.page,
      limit: data.page_size,
      pages: data.pages,
    };
  },

  create: async (projectId: number, serverData: ServerConfigCreate): Promise<ServerConfig> => {
    const response = await api.post('/servers', {
      project_id: projectId,
      ...serverData,
    });
    return response.data;
  },

  update: async (serverId: number, serverData: Partial<ServerConfigCreate>): Promise<ServerConfig> => {
    const response = await api.put(`/servers/${serverId}`, serverData);
    return response.data;
  },

  uploadExcel: async (projectId: number, file: File, updateExisting = false): Promise<ServerUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(`/projects/${projectId}/servers/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: {
        update_existing: updateExisting,
      },
    });
    return response.data;
  },

  delete: async (_projectId: number, serverId: number): Promise<void> => {
    await api.delete(`/servers/${serverId}`);
  },

  deleteAll: async (projectId: number): Promise<void> => {
    await api.delete(`/projects/${projectId}/servers`);
  },
};
