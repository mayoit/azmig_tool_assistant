import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Divider,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Chip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Refresh as ResetIcon,
} from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';

interface ValidationSettings {
  global: {
    fail_fast: boolean;
    parallel_execution: boolean;
    timeout_seconds: number;
  };
  landing_zone: {
    access_validation: {
      enabled: boolean;
      checks: {
        migrate_project_rbac: { enabled: boolean };
        recovery_vault_rbac: { enabled: boolean };
        subscription_rbac: { enabled: boolean };
      };
    };
    appliance_health: { enabled: boolean };
    storage_cache: { enabled: boolean; auto_create_if_missing: boolean };
    quota_validation: { enabled: boolean };
  };
  servers: {
    region_validation: { enabled: boolean };
    resource_group_validation: { enabled: boolean };
    vnet_subnet_validation: { enabled: boolean };
    vm_sku_validation: { enabled: boolean };
    disk_type_validation: { enabled: boolean };
    discovery_validation: { enabled: boolean };
    rbac_validation: { enabled: boolean };
  };
}

interface ValidationSettingsEditorProps {
  projectId: number;
  initialSettings: ValidationSettings | null;
}

const defaultSettings: ValidationSettings = {
  global: {
    fail_fast: false,
    parallel_execution: true,
    timeout_seconds: 300,
  },
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
    rbac_validation: { enabled: false },
  },
};

export default function ValidationSettingsEditor({
  projectId,
  initialSettings,
}: ValidationSettingsEditorProps) {
  const queryClient = useQueryClient();
  const [settings, setSettings] = useState<ValidationSettings>(
    initialSettings || defaultSettings
  );
  const [saveSuccess, setSaveSuccess] = useState(false);

  const saveMutation = useMutation({
    mutationFn: async (newSettings: ValidationSettings) => {
      // Fetch current project to get existing metadata_json
      const response = await api.get(`/projects/${projectId}`);
      const currentProject = response.data;
      
      // Merge new settings with existing metadata_json
      await api.put(`/projects/${projectId}`, {
        metadata_json: {
          ...currentProject.metadata_json,
          validation_settings: newSettings,
        },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  const handleSave = () => {
    saveMutation.mutate(settings);
  };

  const handleReset = () => {
    setSettings(initialSettings || defaultSettings);
  };

  const updateGlobal = (field: keyof ValidationSettings['global'], value: any) => {
    setSettings((prev) => ({
      ...prev,
      global: { ...prev.global, [field]: value },
    }));
  };

  const updateLandingZone = (field: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      landing_zone: { ...prev.landing_zone, [field]: value },
    }));
  };

  const updateServers = (field: keyof ValidationSettings['servers'], value: any) => {
    setSettings((prev) => ({
      ...prev,
      servers: { ...prev.servers, [field]: value },
    }));
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Validation Configuration</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<ResetIcon />}
            onClick={handleReset}
            disabled={saveMutation.isPending}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={saveMutation.isPending}
          >
            {saveMutation.isPending ? 'Saving...' : 'Save Settings'}
          </Button>
        </Box>
      </Box>

      {saveSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Validation settings saved successfully!
        </Alert>
      )}

      {saveMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to save settings. Please try again.
        </Alert>
      )}

      <Stack spacing={2}>
        {/* Global Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="subtitle1" fontWeight="medium">
                Global Settings
              </Typography>
              <Chip
                label="Core Configuration"
                size="small"
                color="primary"
                variant="outlined"
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.global.fail_fast}
                    onChange={(e) => updateGlobal('fail_fast', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Fail Fast</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Stop validation on first failure
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.global.parallel_execution}
                    onChange={(e) => updateGlobal('parallel_execution', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Parallel Execution</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Run validations concurrently for faster results
                    </Typography>
                  </Box>
                }
              />
              <TextField
                label="Timeout (seconds)"
                type="number"
                value={settings.global.timeout_seconds}
                onChange={(e) => updateGlobal('timeout_seconds', parseInt(e.target.value))}
                helperText="Maximum time for each validation check"
                sx={{ maxWidth: 300 }}
              />
            </Stack>
          </AccordionDetails>
        </Accordion>

        {/* Landing Zone Validations */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="subtitle1" fontWeight="medium">
                Landing Zone Validations
              </Typography>
              <Chip
                label={`${Object.values(settings.landing_zone).filter((v: any) => v.enabled).length} Enabled`}
                size="small"
                color="success"
                variant="outlined"
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={3}>
              {/* Access Validation */}
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.landing_zone.access_validation.enabled}
                      onChange={(e) =>
                        updateLandingZone('access_validation', {
                          ...settings.landing_zone.access_validation,
                          enabled: e.target.checked,
                        })
                      }
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        Access Validation (RBAC)
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Verify user permissions on Azure resources
                      </Typography>
                    </Box>
                  }
                />
                {settings.landing_zone.access_validation.enabled && (
                  <Box sx={{ ml: 4, mt: 1, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      RBAC Checks:
                    </Typography>
                    <Stack spacing={1} sx={{ mt: 1 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            size="small"
                            checked={settings.landing_zone.access_validation.checks.migrate_project_rbac.enabled}
                            onChange={(e) =>
                              updateLandingZone('access_validation', {
                                ...settings.landing_zone.access_validation,
                                checks: {
                                  ...settings.landing_zone.access_validation.checks,
                                  migrate_project_rbac: { enabled: e.target.checked },
                                },
                              })
                            }
                          />
                        }
                        label={<Typography variant="caption">Migrate Project RBAC</Typography>}
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            size="small"
                            checked={settings.landing_zone.access_validation.checks.recovery_vault_rbac.enabled}
                            onChange={(e) =>
                              updateLandingZone('access_validation', {
                                ...settings.landing_zone.access_validation,
                                checks: {
                                  ...settings.landing_zone.access_validation.checks,
                                  recovery_vault_rbac: { enabled: e.target.checked },
                                },
                              })
                            }
                          />
                        }
                        label={<Typography variant="caption">Recovery Vault RBAC</Typography>}
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            size="small"
                            checked={settings.landing_zone.access_validation.checks.subscription_rbac.enabled}
                            onChange={(e) =>
                              updateLandingZone('access_validation', {
                                ...settings.landing_zone.access_validation,
                                checks: {
                                  ...settings.landing_zone.access_validation.checks,
                                  subscription_rbac: { enabled: e.target.checked },
                                },
                              })
                            }
                          />
                        }
                        label={<Typography variant="caption">Subscription RBAC</Typography>}
                      />
                    </Stack>
                  </Box>
                )}
              </Box>

              <Divider />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.landing_zone.appliance_health.enabled}
                    onChange={(e) =>
                      updateLandingZone('appliance_health', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      Appliance Health
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Check Azure Migrate appliance status
                    </Typography>
                  </Box>
                }
              />

              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.landing_zone.storage_cache.enabled}
                      onChange={(e) =>
                        updateLandingZone('storage_cache', {
                          ...settings.landing_zone.storage_cache,
                          enabled: e.target.checked,
                        })
                      }
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        Storage Cache Validation
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Verify cache storage account exists and is accessible
                      </Typography>
                    </Box>
                  }
                />
                {settings.landing_zone.storage_cache.enabled && (
                  <FormControlLabel
                    sx={{ ml: 4 }}
                    control={
                      <Switch
                        size="small"
                        checked={settings.landing_zone.storage_cache.auto_create_if_missing}
                        onChange={(e) =>
                          updateLandingZone('storage_cache', {
                            ...settings.landing_zone.storage_cache,
                            auto_create_if_missing: e.target.checked,
                          })
                        }
                      />
                    }
                    label={
                      <Typography variant="caption">Auto-create if missing</Typography>
                    }
                  />
                )}
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.landing_zone.quota_validation.enabled}
                    onChange={(e) =>
                      updateLandingZone('quota_validation', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      Quota Validation
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Check subscription quotas and limits
                    </Typography>
                  </Box>
                }
              />
            </Stack>
          </AccordionDetails>
        </Accordion>

        {/* Server Validations */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="subtitle1" fontWeight="medium">
                Server Validations
              </Typography>
              <Chip
                label={`${Object.values(settings.servers).filter((v: any) => v.enabled).length} Enabled`}
                size="small"
                color="info"
                variant="outlined"
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.servers.region_validation.enabled}
                    onChange={(e) =>
                      updateServers('region_validation', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Region Validation</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Verify target region is valid and available
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.servers.resource_group_validation.enabled}
                    onChange={(e) =>
                      updateServers('resource_group_validation', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Resource Group Validation</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Check if resource group exists or can be created
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.servers.vnet_subnet_validation.enabled}
                    onChange={(e) =>
                      updateServers('vnet_subnet_validation', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">VNet/Subnet Validation</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Verify virtual network and subnet configuration
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.servers.vm_sku_validation.enabled}
                    onChange={(e) =>
                      updateServers('vm_sku_validation', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">VM SKU Validation</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Check if VM size is available in target region
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.servers.disk_type_validation.enabled}
                    onChange={(e) =>
                      updateServers('disk_type_validation', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Disk Type Validation</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Verify disk type compatibility
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.servers.discovery_validation.enabled}
                    onChange={(e) =>
                      updateServers('discovery_validation', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Discovery Validation</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Check if servers are discovered in Azure Migrate
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.servers.rbac_validation.enabled}
                    onChange={(e) =>
                      updateServers('rbac_validation', { enabled: e.target.checked })
                    }
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Server RBAC Validation</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Verify permissions on target server resources
                    </Typography>
                  </Box>
                }
              />
            </Stack>
          </AccordionDetails>
        </Accordion>
      </Stack>
    </Box>
  );
}
