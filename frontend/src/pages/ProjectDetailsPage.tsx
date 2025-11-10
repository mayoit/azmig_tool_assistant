import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Divider,
  Stack,
  Input,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import {
  Edit as EditIcon,
  CloudQueue as CloudIcon,
  Storage as StorageIcon,
  Dns as DnsIcon,
  CheckCircle as CheckCircleIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsService } from '../services/projects.service';
import { format } from 'date-fns';
import MigrateProjectFormModal from '../components/landingZones/MigrateProjectFormModal';
import MigrateProjectAccordion from '../components/landingZones/MigrateProjectAccordion';
import AppLandingZoneModal from '../components/landingZones/AppLandingZoneModal';
import SettingsEditor from '../components/settings/SettingsEditor';
import ValidationEventLog from '../components/validations/ValidationEventLog';
import AzureAuthConfig from '../components/AzureAuthConfig';
import { validationsService } from '../services/validations.service';
import { validateMigrateProject } from '../api/landingZoneValidation';
import api from '../services/api';
import type { ValidationSettings } from '../types/project.types';
import EditableServerTable from '../components/servers/EditableServerTable';
import { serversService } from '../services/servers.service';

// Normalize validation settings to ensure all required properties exist
function normalizeValidationSettings(settings: ValidationSettings | undefined | null): ValidationSettings | null {
  if (!settings) return null;

  // Type to handle backward compatibility with old schema
  type LegacyValidationSettings = Partial<ValidationSettings> & {
    landing_zone?: Partial<ValidationSettings['landing_zone']> & {
      access_validation?: { enabled: boolean; checks?: ValidationSettings['landing_zone']['access_validation']['checks'] };
    };
  };

  const legacySettings = settings as LegacyValidationSettings;

  // Deep merge with default structure to ensure all nested properties exist
  return {
    global: {
      fail_fast: legacySettings.global?.fail_fast ?? false,
      parallel_execution: legacySettings.global?.parallel_execution ?? true,
      timeout_seconds: legacySettings.global?.timeout_seconds ?? 300,
    },
    landing_zone: {
      access_validation: {
        enabled: legacySettings.landing_zone?.access_validation?.enabled ?? true,
        checks: {
          migrate_project_rbac: {
            enabled: legacySettings.landing_zone?.access_validation?.checks?.migrate_project_rbac?.enabled ?? true,
          },
          recovery_vault_rbac: {
            enabled: legacySettings.landing_zone?.access_validation?.checks?.recovery_vault_rbac?.enabled ?? true,
          },
          subscription_rbac: {
            enabled: legacySettings.landing_zone?.access_validation?.checks?.subscription_rbac?.enabled ?? true,
          },
        },
      },
      access_validation_checks: {
        migrate_project_rbac: {
          enabled: legacySettings.landing_zone?.access_validation_checks?.migrate_project_rbac?.enabled ?? true,
        },
        recovery_vault_rbac: {
          enabled: legacySettings.landing_zone?.access_validation_checks?.recovery_vault_rbac?.enabled ?? true,
        },
        subscription_rbac: {
          enabled: legacySettings.landing_zone?.access_validation_checks?.subscription_rbac?.enabled ?? true,
        },
      },
      appliance_health: {
        enabled: legacySettings.landing_zone?.appliance_health?.enabled ?? true,
      },
      storage_cache: {
        enabled: legacySettings.landing_zone?.storage_cache?.enabled ?? true,
        auto_create_if_missing: legacySettings.landing_zone?.storage_cache?.auto_create_if_missing ?? true,
      },
      quota_validation: {
        enabled: legacySettings.landing_zone?.quota_validation?.enabled ?? true,
      },
    },
    servers: {
      region_validation: {
        enabled: legacySettings.servers?.region_validation?.enabled ?? true,
      },
      resource_group_validation: {
        enabled: legacySettings.servers?.resource_group_validation?.enabled ?? true,
      },
      vnet_subnet_validation: {
        enabled: legacySettings.servers?.vnet_subnet_validation?.enabled ?? true,
      },
      vm_sku_validation: {
        enabled: legacySettings.servers?.vm_sku_validation?.enabled ?? true,
      },
      disk_type_validation: {
        enabled: legacySettings.servers?.disk_type_validation?.enabled ?? true,
      },
      discovery_validation: {
        enabled: legacySettings.servers?.discovery_validation?.enabled ?? true,
      },
      rbac_validation: {
        enabled: legacySettings.servers?.rbac_validation?.enabled ?? false,
      },
    },
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `project-tab-${index}`,
    'aria-controls': `project-tabpanel-${index}`,
  };
}

export default function ProjectDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState(0);
  const projectId = id ? Number(id) : undefined;
  const [isLandingZoneModalOpen, setLandingZoneModalOpen] = useState(false);
  const [editMigrateProjectIndex, setEditMigrateProjectIndex] = useState<number | null>(null);
  const [addZoneModalOpen, setAddZoneModalOpen] = useState(false);
  const [selectedProjectIndex, setSelectedProjectIndex] = useState<number | null>(null);
  const [deleteProjectIndex, setDeleteProjectIndex] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [runningValidation, setRunningValidation] = useState(false);
  const queryClient = useQueryClient();

  // Fetch servers for the Servers tab
  const {
    data: serversData,
    isLoading: serversLoading,
    refetch: refetchServers,
  } = useQuery({
    queryKey: ['servers', projectId],
    queryFn: () => serversService.getAll(projectId!, { page: 1, limit: 100 }),
    enabled: !!projectId && currentTab === 3,
  });

  // Fetch project details
  const {
    data: project,
    isLoading: projectLoading,
    error: projectError,
  } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsService.getById(projectId!),
    enabled: !!projectId,
  });

  // Extract project settings from metadata_json
  const project_settings = (project?.metadata_json?.project_settings as {
    allowed_regions: string[];
    allowed_vm_skus: string[];
    disk_types: string[];
    redundancy_types: string[];
  } | undefined) || null;

  // Fetch validation jobs
  const {
    data: validationJobs,
    isLoading: validationsLoading,
  } = useQuery({
    queryKey: ['validations', projectId],
    queryFn: () => validationsService.getJobs(projectId!, { page: 1, limit: 10 }),
    enabled: !!projectId,
  });

  // Fetch auth status
  const {
    data: authStatus,
    isLoading: authStatusLoading,
  } = useQuery({
    queryKey: ['authStatus', projectId],
    queryFn: async () => {
      const response = await api.get(`/projects/${projectId}/auth/status`);
      return response.data;
    },
    enabled: !!projectId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Run validation mutation
  const runValidationMutation = useMutation({
    mutationFn: () => validationsService.triggerValidation(projectId!),
    onSuccess: () => {
      setRunningValidation(false);
      queryClient.invalidateQueries({ queryKey: ['validations', projectId] });
      setCurrentTab(4); // Switch to Validations tab
    },
    onError: (error: unknown) => {
      setRunningValidation(false);
      console.error('Failed to run validation:', error);
    },
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post(`/projects/${projectId}/landing-zones/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: () => {
      setUploadSuccess(true);
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      setTimeout(() => setUploadSuccess(false), 5000);
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error && 'response' in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to upload file'
        : 'Failed to upload file';
      setUploadError(errorMessage);
      setUploadSuccess(false);
    },
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleEdit = () => {
    // TODO: Open edit modal
    console.log('Edit project:', id);
  };

  const handleBack = () => {
    navigate('/projects');
  };

  // Handler for adding application landing zone
  const handleAddZone = (projectIndex: number) => {
    setSelectedProjectIndex(projectIndex);
    setAddZoneModalOpen(true);
  };

  // Handler for submitting new application landing zone
  const handleSubmitZone = async (zoneData: {
    subscriptionId: string;
    subscriptionName?: string;
    region: string;
    cacheStorageAccount: string;
    cacheStorageResourceGroup: string;
    allowedSkus?: string[];
  }) => {
    if (selectedProjectIndex === null || !project) return;

    const currentProjects = project.lz_migrate_projects || [];
    const updatedProjects = [...currentProjects];
    const targetProject = updatedProjects[selectedProjectIndex];

    if (!targetProject.appLandingZones) {
      targetProject.appLandingZones = [];
    }

    // Add new zone with proper field mapping including subscription name
    targetProject.appLandingZones.push({
      subscriptionId: zoneData.subscriptionId,
      subscriptionName: zoneData.subscriptionName,
      cacheStorageAccount: zoneData.cacheStorageAccount,
      region: zoneData.region,
      cacheStorageResourceGroup: zoneData.cacheStorageResourceGroup,
      allowedSkus: zoneData.allowedSkus || [],
    });

    try {
      // Preserve all metadata when updating - don't overwrite other fields
      const currentMetadata = project.metadata_json || {};
      await api.put(`/projects/${projectId}`, {
        metadata_json: {
          ...currentMetadata,
          lz_migrate_projects: updatedProjects,
        },
      });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      setAddZoneModalOpen(false);
      setSelectedProjectIndex(null);
    } catch (error) {
      console.error('Failed to add landing zone:', error);
    }
  };

  // Handler for deleting application landing zone
  const handleDeleteZone = async (projectIndex: number, zoneIndex: number) => {
    if (!project) return;

    const currentProjects = project.lz_migrate_projects || [];
    const updatedProjects = [...currentProjects];
    const targetProject = updatedProjects[projectIndex];

    if (targetProject.appLandingZones) {
      targetProject.appLandingZones.splice(zoneIndex, 1);
    }

    try {
      // Preserve all metadata when updating
      const currentMetadata = project.metadata_json || {};
      await api.put(`/projects/${projectId}`, {
        metadata_json: {
          ...currentMetadata,
          lz_migrate_projects: updatedProjects,
        },
      });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    } catch (error) {
      console.error('Failed to delete landing zone:', error);
    }
  };

  // Handler for deleting migrate project
  const handleDeleteProject = async (projectIndex: number) => {
    if (!project) return;

    const currentProjects = project.lz_migrate_projects || [];
    const updatedProjects = currentProjects.filter((_, index) => index !== projectIndex);

    try {
      // Preserve all metadata when updating
      const currentMetadata = project.metadata_json || {};
      await api.put(`/projects/${projectId}`, {
        metadata_json: {
          ...currentMetadata,
          lz_migrate_projects: updatedProjects,
        },
      });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      setDeleteProjectIndex(null);
    } catch (error) {
      console.error('Failed to delete migrate project:', error);
    }
  };

  // Handler for validation
  const handleValidate = async (projectIndex: number, zoneIndices: number[]) => {
    // TODO: Implement validation logic
    console.log('Validating project', projectIndex, 'zones', zoneIndices);
    alert(`Validation will be implemented: Project ${projectIndex}, Zones: ${zoneIndices.join(', ')}`);
  };

  // Handler for migrate project validation
  const handleValidateMigrateProject = async (projectIndex: number) => {
    if (!project) return;
    
    try {
      const result = await validateMigrateProject(project.id, projectIndex, false);
      
      if (result.success) {
        // Refetch project to get updated validation status
        queryClient.invalidateQueries({ queryKey: ['project', id] });
        alert(`Validation completed: ${result.status}`);
      } else {
        alert(`Validation failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Validation error:', error);
      alert('Validation failed. Please check your Azure authentication and try again.');
    }
  };

  const handleRunValidation = () => {
    setRunningValidation(true);
    runValidationMutation.mutate();
  };

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
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load project details. The project may not exist.
        </Alert>
        <Button onClick={handleBack}>Back to Projects</Button>
      </Box>
    );
  }

  const statusColors = {
    active: 'success',
    in_progress: 'warning',
    completed: 'info',
    archived: 'error',
  } as const;

  const migrateProjects = project.lz_migrate_projects ?? [];
  const hasMigrateProjects = migrateProjects.length > 0;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', overflow: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 3, flexShrink: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h4" gutterBottom fontWeight="bold">
              {project.name}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Chip
                label={project.status.replace('_', ' ').toUpperCase()}
                color={statusColors[project.status as keyof typeof statusColors]}
                size="small"
              />
              <Typography variant="body2" color="text.secondary">
                Created {format(new Date(project.created_at), 'MMM d, yyyy')}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={handleEdit}
            >
              Edit Project
            </Button>
            <Button
              variant="text"
              onClick={handleBack}
            >
              Back to Projects
            </Button>
          </Box>
        </Box>

        {project.description && (
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            {project.description}
          </Typography>
        )}

        {/* Quick Stats */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: 2,
          }}
        >
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CloudIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Tenant ID
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                {project.azure_tenant_id}
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <DnsIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Servers
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight="bold">
                {project.servers_count || 0}
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CheckCircleIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Validations
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight="bold">
                {project.validations_count || 0}
              </Typography>
            </CardContent>
          </Card>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <StorageIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
              </Box>
              <Chip
                label={project.status.replace('_', ' ').toUpperCase()}
                color={statusColors[project.status as keyof typeof statusColors]}
                size="small"
              />
            </CardContent>
          </Card>
        </Box>
      </Box>

  {/* Tabs */}
  <Paper sx={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: '70vh', overflow: 'visible' }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          aria-label="project details tabs"
          sx={{ borderBottom: 1, borderColor: 'divider', flexShrink: 0 }}
        >
          <Tab label="Overview" {...a11yProps(0)} />
          <Tab label="Landing Zones" {...a11yProps(1)} />
          <Tab label="Settings" {...a11yProps(2)} />
          <Tab label="Servers" {...a11yProps(3)} />
          <Tab label="Validations" {...a11yProps(4)} />
        </Tabs>

  {/* Scrollable Tab Content */}
  <Box sx={{ flex: 1, minHeight: '60vh', overflow: 'auto' }}>
        <TabPanel value={currentTab} index={0}>
          {/* Overview Tab */}
          <Box sx={{ px: 3 }}>
            <Typography variant="h6" gutterBottom>
              Project Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  md: 'repeat(2, 1fr)',
                },
                gap: 3,
              }}
            >
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Project Name
                </Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {project.name}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Azure Tenant ID
                </Typography>
                <Typography variant="body1" sx={{ fontFamily: 'monospace', mb: 2 }}>
                  {project.azure_tenant_id}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Status
                </Typography>
                <Chip
                  label={project.status.replace('_', ' ').toUpperCase()}
                  color={statusColors[project.status as keyof typeof statusColors]}
                  size="small"
                  sx={{ mb: 2 }}
                />
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Description
                </Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {project.description || 'No description provided'}
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Created At
                </Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {format(new Date(project.created_at), 'PPpp')}
                </Typography>

                {project.updated_at && (
                  <>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Last Updated
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                      {format(new Date(project.updated_at), 'PPpp')}
                    </Typography>
                  </>
                )}
              </Box>
            </Box>

            <Box sx={{ mt: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Typography variant="h6">
                  Azure Authentication
                </Typography>
                {!authStatusLoading && authStatus?.configured && (
                  <Chip
                    label={authStatus.token_valid ? 'Authenticated' : 'Token Expired'}
                    color={authStatus.token_valid ? 'success' : 'warning'}
                    size="small"
                    icon={<CheckCircleIcon />}
                  />
                )}
                {!authStatusLoading && !authStatus?.configured && (
                  <Chip
                    label="Not Configured"
                    color="default"
                    size="small"
                  />
                )}
              </Box>
              <Divider sx={{ mb: 2 }} />
              <AzureAuthConfig 
                projectId={project.id.toString()} 
                tenantId={project.azure_tenant_id}
              />
            </Box>

            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" gutterBottom>
                Migration Progress
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Alert severity="info">
                Migration progress tracking is coming soon. This will show the status of your servers,
                landing zones, and validation results.
              </Alert>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          {/* Landing Zones Tab */}
          <Box sx={{ px: 3 }}>
            <Typography variant="h6" gutterBottom>
              Landing Zone Migrate Projects
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {uploadSuccess && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Landing zone configuration uploaded successfully!
              </Alert>
            )}
            
            {uploadError && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setUploadError(null)}>
                {uploadError}
              </Alert>
            )}
            
            {!hasMigrateProjects && (
              <Alert severity="info" sx={{ mb: 3 }}>
                No landing zone migrate projects found. Upload a CSV or JSON file with landing zone validation results.
              </Alert>
            )}

            <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
              <Button
                variant="contained"
                component="label"
                startIcon={<UploadIcon />}
                disabled={uploadMutation.isPending}
              >
                {uploadMutation.isPending ? 'Uploading...' : 'Upload Landing Zone File'}
                <Input
                  type="file"
                  onChange={handleFileUpload}
                  sx={{ display: 'none' }}
                  inputProps={{ accept: '.csv,.json' }}
                />
              </Button>
              <Typography variant="body2" color="text.secondary">
                or
              </Typography>
              <Button
                variant="outlined"
                onClick={() => {
                  setEditMigrateProjectIndex(null);
                  setLandingZoneModalOpen(true);
                }}
              >
                Add Manually
              </Button>
              <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                Upload formats: CSV, JSON
              </Typography>
            </Box>

            {hasMigrateProjects && (
              <Stack spacing={2}>
                {migrateProjects.map((migrateProject, index) => (
                  <MigrateProjectAccordion
                    key={`${migrateProject.migrateProjectName}-${index}`}
                    migrateProject={migrateProject}
                    index={index}
                    onEdit={(idx) => {
                      setEditMigrateProjectIndex(idx);
                      setLandingZoneModalOpen(true);
                    }}
                    onDelete={(idx) => setDeleteProjectIndex(idx)}
                    onValidate={handleValidate}
                    onValidateMigrateProject={handleValidateMigrateProject}
                    onDeleteZone={handleDeleteZone}
                    onAddZone={handleAddZone}
                  />
                ))}
              </Stack>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={currentTab} index={2}>
          {/* Settings Tab (Combined Project Settings + Validation Settings) */}
          <Box sx={{ px: 3 }}>
            <SettingsEditor
              projectId={project.id}
              projectSettings={(project.metadata_json?.project_settings as {
                allowed_regions: string[];
                allowed_vm_skus: string[];
                disk_types: string[];
                redundancy_types: string[];
              } | undefined) || null}
              validationSettings={normalizeValidationSettings(project.validation_settings) || {
                global: { fail_fast: false, parallel_execution: true, timeout_seconds: 300 },
                landing_zone: {
                  access_validation: {
                    enabled: true,
                    checks: {
                      migrate_project_rbac: { enabled: true },
                      recovery_vault_rbac: { enabled: true },
                      subscription_rbac: { enabled: true },
                    },
                  },
                  appliance_health: { enabled: true },
                  storage_cache: { enabled: true, auto_create_if_missing: true },
                  quota_validation: { enabled: true },
                },
                servers: {
                  region_validation: { enabled: true },
                  resource_group_validation: { enabled: true },
                  vnet_subnet_validation: { enabled: true },
                  vm_sku_validation: { enabled: true },
                  disk_type_validation: { enabled: true },
                  discovery_validation: { enabled: true },
                  rbac_validation: { enabled: true },
                },
              }}
            />
          </Box>
        </TabPanel>

        <TabPanel value={currentTab} index={3}>
          {/* Servers Tab */}
          <Box sx={{ px: 3 }}>
            <Typography variant="h6" gutterBottom>
              Server Inventory
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <EditableServerTable
              servers={serversData?.items || []}
              onAddServer={async (data) => {
                await serversService.create(projectId!, {
                  target_machine_name: data.target_machine_name || '',
                  target_subscription: data.target_subscription || '',
                  target_region: data.target_region || '',
                  target_resource_group: data.target_resource_group || '',
                  target_vnet: data.target_vnet || '',
                  target_subnet: data.target_subnet || '',
                  target_machine_sku: data.target_machine_sku || 'Standard_DS2_v2',
                  target_disk_type: data.target_disk_type || 'Premium_LRS',
                  appliance_id: data.appliance_id,
                  cache_storage_account: data.cache_storage_account,
                  cache_storage_rg: data.cache_storage_rg,
                });
                refetchServers();
              }}
              onUpdateServer={async (serverId, updates) => {
                await serversService.update(serverId, updates);
                refetchServers();
              }}
              onDeleteServer={async (serverId) => {
                await serversService.delete(projectId!, serverId);
                refetchServers();
              }}
              isLoading={serversLoading}
              availableSubscriptions={
                // Extract unique subscriptions from landing zones with [id, name] tuples
                // Handle both camelCase and snake_case property names
                (() => {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const allZones = ((project.metadata_json as any)?.lz_migrate_projects || []).flatMap((mp: any) => {
                    // Handle both app_landing_zones and appLandingZones
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
                  
                  // Deduplicate by subscription ID
                  const uniqueSubs = new Map<string, string>();
                  allZones.forEach(([id, name]) => {
                    if (!uniqueSubs.has(id)) {
                      uniqueSubs.set(id, name);
                    }
                  });
                  
                  // Convert back to array of tuples
                  return Array.from(uniqueSubs.entries());
                })()
              }
              availableRegions={
                (() => {
                  // Debug: Log the project metadata to understand structure
                  console.log('🔍 Project metadata_json:', project.metadata_json);
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  console.log('🔍 Project settings:', (project.metadata_json?.project_settings as any));
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const regions = ((project.metadata_json?.project_settings as any)?.allowed_regions as string[]) || [];
                  console.log('🔍 Available regions:', regions);
                  return regions;
                })()
              }
              landingZoneAppliances={
                // Only use metadata_json as the single source of truth
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (project.metadata_json as any)?.lz_migrate_projects || []
              }
            />
            
            <Box sx={{ mt: 3, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Advanced server management
              </Typography>
              <Button 
                variant="outlined" 
                onClick={() => navigate(`/projects/${project.id}/servers`)}
                sx={{ mt: 1 }}
              >
                Open Full Server Management Workspace
              </Button>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={currentTab} index={4}>
          {/* Validations Tab - Redesigned */}
          <Box sx={{ px: 3, pb: 3 }}>
            {/* Header Section with Gradient */}
            <Paper 
              elevation={0} 
              sx={{ 
                p: 3, 
                mb: 3, 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                borderRadius: 2,
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h5" fontWeight="bold" gutterBottom>
                    Validation History
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Track and monitor validation runs for your migration project
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleRunValidation}
                  disabled={
                    runningValidation || 
                    runValidationMutation.isPending || 
                    !authStatus?.configured || 
                    !authStatus?.token_valid
                  }
                  startIcon={runningValidation || runValidationMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <CheckCircleIcon />}
                  sx={{
                    bgcolor: 'white',
                    color: '#667eea',
                    '&:hover': {
                      bgcolor: 'rgba(255, 255, 255, 0.9)',
                    },
                    '&:disabled': {
                      bgcolor: 'rgba(255, 255, 255, 0.3)',
                      color: 'rgba(255, 255, 255, 0.6)',
                    },
                  }}
                >
                  {runningValidation || runValidationMutation.isPending ? 'Starting...' : 'Run New Validation'}
                </Button>
              </Box>
            </Paper>

            {/* Authentication Status Warning */}
            {!authStatusLoading && (!authStatus?.configured || !authStatus?.token_valid) && (
              <Alert 
                severity="warning" 
                sx={{ 
                  mb: 3,
                  borderRadius: 2,
                  '& .MuiAlert-message': { width: '100%' },
                }}
              >
                <Box>
                  {!authStatus?.configured ? (
                    <>
                      <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                        Authentication Required
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        Please configure Azure authentication in the Overview tab before running validations.
                      </Typography>
                    </>
                  ) : !authStatus?.token_valid ? (
                    <>
                      <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                        Token Expired
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        Your authentication token has expired. Please re-authenticate in the Overview tab.
                      </Typography>
                    </>
                  ) : null}
                  <Button 
                    size="small" 
                    variant="outlined" 
                    color="warning"
                    onClick={() => setCurrentTab(0)}
                  >
                    Go to Overview
                  </Button>
                </Box>
              </Alert>
            )}

            {runValidationMutation.isError && (
              <Alert 
                severity="error" 
                sx={{ mb: 3, borderRadius: 2 }}
              >
                <Typography variant="subtitle2" fontWeight="bold">
                  Validation Failed
                </Typography>
                <Typography variant="body2">
                  Failed to start validation job. Please try again.
                </Typography>
              </Alert>
            )}

            {/* Validation Results */}
            {validationsLoading ? (
              <Paper sx={{ p: 4, textAlign: 'center', borderRadius: 2 }}>
                <CircularProgress size={40} />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Loading validation history...
                </Typography>
              </Paper>
            ) : (
              <Paper sx={{ borderRadius: 2, overflow: 'hidden' }}>
                <ValidationEventLog 
                  serverValidations={validationJobs?.items || []}
                  landingZoneValidations={[]} // TODO: Fetch from API
                  onRefresh={() => {
                    queryClient.invalidateQueries({ queryKey: ['validations', projectId] });
                  }}
                  isLoading={validationsLoading}
                />
              </Paper>
            )}
          </Box>
        </TabPanel>
      </Box>
      </Paper>

      <MigrateProjectFormModal
        open={isLandingZoneModalOpen}
        onClose={() => {
          setLandingZoneModalOpen(false);
          setEditMigrateProjectIndex(null);
        }}
        projectId={project.id}
        projectName={project.name}
        editMode={editMigrateProjectIndex !== null}
        editIndex={editMigrateProjectIndex ?? undefined}
        projectSettings={project_settings}
        isAuthenticated={authStatus?.configured && authStatus?.token_valid || false}
        initialData={
          editMigrateProjectIndex !== null && migrateProjects[editMigrateProjectIndex]
            ? {
                migrateProjectSubscription: migrateProjects[editMigrateProjectIndex].migrateProjectSubscription || '',
                migrateResourceGroup: migrateProjects[editMigrateProjectIndex].migrateResourceGroup || '',
                migrateProjectName: migrateProjects[editMigrateProjectIndex].migrateProjectName || '',
                applianceName: migrateProjects[editMigrateProjectIndex].applianceName || '',
                appLandingZones: (migrateProjects[editMigrateProjectIndex].appLandingZones || []).map(zone => ({
                  subscriptionId: zone.subscriptionId || '',
                  region: zone.region || '',
                  cacheStorageAccount: zone.cacheStorageAccount || '',
                  cacheStorageResourceGroup: zone.cacheStorageResourceGroup || '',
                  isNewResource: zone.isNewResource || false,
                  allowedSkus: zone.allowedSkus || [],
                })),
              }
            : undefined
        }
      />

      <AppLandingZoneModal
        open={addZoneModalOpen}
        onClose={() => {
          setAddZoneModalOpen(false);
          setSelectedProjectIndex(null);
        }}
        onSubmit={handleSubmitZone}
        projectName={
          selectedProjectIndex !== null && migrateProjects[selectedProjectIndex]
            ? migrateProjects[selectedProjectIndex].migrateProjectName || 'Unknown Project'
            : 'Unknown Project'
        }
        projectSettings={project_settings}
        projectId={project.id}
        isAuthenticated={authStatus?.configured && authStatus?.token_valid || false}
      />

      <Dialog
        open={deleteProjectIndex !== null}
        onClose={() => setDeleteProjectIndex(null)}
      >
        <DialogTitle>Delete Migrate Project</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this migrate project?{' '}
            {deleteProjectIndex !== null && migrateProjects[deleteProjectIndex] && (
              <strong>{migrateProjects[deleteProjectIndex].migrateProjectName}</strong>
            )}
            <br /><br />
            This will remove the project and all its application landing zones. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteProjectIndex(null)}>Cancel</Button>
          <Button
            onClick={() => {
              if (deleteProjectIndex !== null) {
                handleDeleteProject(deleteProjectIndex);
              }
            }}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
