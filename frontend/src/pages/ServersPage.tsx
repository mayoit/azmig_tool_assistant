import React, { useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  InputAdornment,
  TextField,
  Typography,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { projectsService } from '../services/projects.service';
import { serversService } from '../services/servers.service';
import type { ServerConfig } from '../types/server.types';
import type { PaginatedResponse } from '../types/api.types';
import EditableServerTable from '../components/servers/EditableServerTable';

export default function ServersPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const projectId = id ? Number(id) : undefined;

  const [searchTerm, setSearchTerm] = useState('');
  const [updateExisting, setUpdateExisting] = useState(false);
  const [uploadFeedback, setUploadFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const {
    data: project,
    isLoading: projectLoading,
    error: projectError,
  } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsService.getById(projectId!),
    enabled: !!projectId,
  });

  const {
    data: serverData,
    isLoading: serversLoading,
    error: serversError,
  } = useQuery<PaginatedResponse<ServerConfig>>({
    queryKey: ['servers', projectId],
    queryFn: () =>
      serversService.getAll(projectId!, {
        page: 1,
        limit: 100, // Get more servers for inline editing
      }),
    enabled: !!projectId,
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, updateExisting: shouldUpdate }: { file: File; updateExisting: boolean }) =>
      serversService.uploadExcel(projectId!, file, shouldUpdate),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['servers', projectId] });
      setUploadFeedback({
        type: 'success',
        message: `Upload complete. Created ${result.servers_created}, updated ${result.servers_updated}. Total servers: ${result.total_servers}.`,
      });
    },
    onError: () => {
      setUploadFeedback({ type: 'error', message: 'Failed to upload servers. Please verify the file format and try again.' });
    },
  });

  const createServerMutation = useMutation({
    mutationFn: (data: Partial<ServerConfig>) =>
      serversService.create(projectId!, {
        target_machine_name: data.target_machine_name || '',
        target_region: data.target_region || '',
        target_subscription: data.target_subscription || '',
        target_resource_group: data.target_resource_group || '',
        target_vnet: data.target_vnet || '',
        target_subnet: data.target_subnet || '',
        target_machine_sku: data.target_machine_sku || '',
        target_disk_type: data.target_disk_type || '',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers', projectId] });
      setUploadFeedback({ type: 'success', message: 'Server created successfully.' });
    },
    onError: () => {
      setUploadFeedback({ type: 'error', message: 'Failed to create server.' });
    },
  });

  const updateServerMutation = useMutation({
    mutationFn: ({ serverId, data }: { serverId: number; data: Partial<ServerConfig> }) =>
      serversService.update(serverId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers', projectId] });
      setUploadFeedback({ type: 'success', message: 'Server updated successfully.' });
    },
    onError: () => {
      setUploadFeedback({ type: 'error', message: 'Failed to update server.' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (serverId: number) => serversService.delete(projectId!, serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers', projectId] });
      setUploadFeedback({ type: 'success', message: 'Server deleted successfully.' });
    },
    onError: () => {
      setUploadFeedback({ type: 'error', message: 'Failed to delete server.' });
    },
  });

  const deleteAllMutation = useMutation({
    mutationFn: () => serversService.deleteAll(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers', projectId] });
      setUploadFeedback({ type: 'success', message: 'All servers deleted successfully.' });
    },
    onError: () => {
      setUploadFeedback({ type: 'error', message: 'Failed to delete servers. Please try again.' });
    },
  });

  const filteredServers = useMemo(() => {
    const items: ServerConfig[] = serverData?.items ?? [];
    if (!searchTerm) {
      return items;
    }

    const normalized = searchTerm.toLowerCase();
    return items.filter((server) =>
      server.target_machine_name.toLowerCase().includes(normalized) ||
      server.target_region.toLowerCase().includes(normalized) ||
      server.target_resource_group.toLowerCase().includes(normalized)
    );
  }, [serverData, searchTerm]);

  // Extract landing zone appliances with logging
  const landingZoneAppliances = useMemo(() => {
    console.log('[ServersPage] Computing landingZoneAppliances...');
    console.log('[ServersPage] project:', project);
    console.log('[ServersPage] project?.metadata_json:', project?.metadata_json);
    
    // Only use metadata_json as the single source of truth
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const appliances = (project?.metadata_json as any)?.lz_migrate_projects || [];
    
    console.log('[ServersPage] Computed appliances:', appliances);
    return appliances;
  }, [project]);

  const availableSubscriptions = useMemo(() => {
    if (!project) {
      return [] as Array<[string, string]>;
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const allZones = ((project.metadata_json as any)?.lz_migrate_projects || []).flatMap((mp: any) => {
      const zones = mp.app_landing_zones || mp.appLandingZones || [];
      return zones
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((zone: any) => {
          const subId = zone.subscriptionId || zone['Subscription ID'];
          const subName = zone.subscriptionName || zone['Subscription Name'] || subId;
          return subId ? [subId, subName] as [string, string] : null;
        })
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .filter((item: any) => item !== null);
    });

    const uniqueSubs = new Map<string, string>();
    allZones.forEach(([id, name]: [string, string]) => {
      if (!uniqueSubs.has(id)) {
        uniqueSubs.set(id, name);
      }
    });

    return Array.from(uniqueSubs.entries());
  }, [project]);

  const availableRegions = useMemo(() => {
    if (!project) {
      return [] as string[];
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const projectSettings = (project.metadata_json?.project_settings as any) || {};
    return (projectSettings.allowed_regions as string[]) || [];
  }, [project]);

  const availableVMSkus = useMemo(() => {
    if (!project) {
      return [] as string[];
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const projectSettings = (project.metadata_json?.project_settings as any) || {};
    return (projectSettings.allowed_vm_skus as string[]) || [];
  }, [project]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && projectId) {
      uploadMutation.mutate({ file, updateExisting });
      event.target.value = '';
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleDeleteAll = () => {
    if (window.confirm('This will delete all servers for this project. Continue?')) {
      deleteAllMutation.mutate();
    }
  };

  if (!projectId) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          Invalid project. Please navigate from the Projects list.
        </Alert>
        <Button onClick={() => navigate('/projects')}>Back to Projects</Button>
      </Box>
    );
  }

  if (projectLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (projectError || !project) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          Unable to load project details.
        </Alert>
        <Button onClick={() => navigate('/projects')}>Back to Projects</Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Server Inventory
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage migration servers for {project.name}
          </Typography>
        </Box>
        <Button variant="outlined" onClick={() => navigate(`/projects/${projectId}`)}>
          Back to Project
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
            <Button
              variant="contained"
              startIcon={<CloudUploadIcon />}
              onClick={handleUploadClick}
              disabled={uploadMutation.isPending || deleteAllMutation.isPending}
            >
              Upload Excel
            </Button>
            <input
              type="file"
              accept=".xlsx,.xls"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileSelect}
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={updateExisting}
                  onChange={(event) => setUpdateExisting(event.target.checked)}
                />
              }
              label="Update existing servers"
            />

            <Button
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDeleteAll}
              disabled={deleteAllMutation.isPending || (serverData?.total ?? 0) === 0}
            >
              Delete All
            </Button>
          </Box>

          <TextField
            placeholder="Search by machine, region, or resource group..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ maxWidth: 400 }}
          />
        </CardContent>
      </Card>

      {uploadFeedback && (
        <Alert
          severity={uploadFeedback.type}
          sx={{ mb: 3 }}
          onClose={() => setUploadFeedback(null)}
        >
          {uploadFeedback.message}
        </Alert>
      )}

      {serversError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Unable to load servers. Please try again.
        </Alert>
      )}

      {serversLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      ) : (
        <EditableServerTable
          servers={filteredServers}
          onAddServer={async (data) => {
            console.log('[ServersPage] Project object:', project);
            console.log('[ServersPage] project.lz_migrate_projects:', project?.lz_migrate_projects);
            console.log('[ServersPage] project.metadata_json:', project?.metadata_json);
            await createServerMutation.mutateAsync(data);
          }}
          onUpdateServer={async (serverId, updates) => {
            await updateServerMutation.mutateAsync({ serverId, data: updates });
          }}
          onDeleteServer={async (serverId) => {
            await deleteMutation.mutateAsync(serverId);
          }}
          isLoading={serversLoading}
          availableSubscriptions={availableSubscriptions}
          availableRegions={availableRegions}
          landingZoneAppliances={landingZoneAppliances}
          availableVMSkus={availableVMSkus}
        />
      )}
    </Box>
  );
}
