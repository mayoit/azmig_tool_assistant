import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Chip,
  Stack,
  Alert,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Save as SaveIcon,
  Refresh as ResetIcon,
} from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';

interface ProjectSettings {
  allowed_regions: string[];
  allowed_vm_skus: string[];
  disk_types: string[];
  redundancy_types: string[];
}

interface ProjectSettingsEditorProps {
  projectId: number;
  initialSettings: ProjectSettings | null;
}

const defaultSettings: ProjectSettings = {
  allowed_regions: ['uksouth', 'ukwest', 'eastus', 'westus', 'northeurope', 'westeurope'],
  allowed_vm_skus: [
    'Standard_DS1_v2',
    'Standard_DS2_v2',
    'Standard_DS3_v2',
    'Standard_D2s_v3',
    'Standard_D4s_v3',
    'Standard_D8s_v3',
    'Standard_E2s_v3',
    'Standard_E4s_v3',
  ],
  disk_types: ['Premium_LRS', 'Standard_LRS', 'StandardSSD_LRS', 'UltraSSD_LRS'],
  redundancy_types: ['LRS', 'GRS', 'ZRS', 'GZRS', 'RA-GRS', 'RA-GZRS'],
};

export default function ProjectSettingsEditor({
  projectId,
  initialSettings,
}: ProjectSettingsEditorProps) {
  const queryClient = useQueryClient();
  const [settings, setSettings] = useState<ProjectSettings>(
    initialSettings || defaultSettings
  );
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [newRegion, setNewRegion] = useState('');
  const [newSku, setNewSku] = useState('');
  const [newDiskType, setNewDiskType] = useState('');
  const [newRedundancy, setNewRedundancy] = useState('');

  useEffect(() => {
    if (initialSettings) {
      setSettings(initialSettings);
    }
  }, [initialSettings]);

  const saveMutation = useMutation({
    mutationFn: async (newSettings: ProjectSettings) => {
      // Fetch current project to get existing metadata_json
      const response = await api.get(`/projects/${projectId}`);
      const currentProject = response.data;
      
      // Merge new settings with existing metadata_json
      await api.put(`/projects/${projectId}`, {
        metadata_json: {
          ...currentProject.metadata_json,
          project_settings: newSettings,
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

  const handleAddRegion = () => {
    if (newRegion.trim() && !settings.allowed_regions.includes(newRegion.trim())) {
      setSettings({
        ...settings,
        allowed_regions: [...settings.allowed_regions, newRegion.trim()],
      });
      setNewRegion('');
    }
  };

  const handleDeleteRegion = (region: string) => {
    setSettings({
      ...settings,
      allowed_regions: settings.allowed_regions.filter((r) => r !== region),
    });
  };

  const handleAddSku = () => {
    if (newSku.trim() && !settings.allowed_vm_skus.includes(newSku.trim())) {
      setSettings({
        ...settings,
        allowed_vm_skus: [...settings.allowed_vm_skus, newSku.trim()],
      });
      setNewSku('');
    }
  };

  const handleDeleteSku = (sku: string) => {
    setSettings({
      ...settings,
      allowed_vm_skus: settings.allowed_vm_skus.filter((s) => s !== sku),
    });
  };

  const handleAddDiskType = () => {
    if (newDiskType.trim() && !settings.disk_types.includes(newDiskType.trim())) {
      setSettings({
        ...settings,
        disk_types: [...settings.disk_types, newDiskType.trim()],
      });
      setNewDiskType('');
    }
  };

  const handleDeleteDiskType = (diskType: string) => {
    setSettings({
      ...settings,
      disk_types: settings.disk_types.filter((d) => d !== diskType),
    });
  };

  const handleAddRedundancy = () => {
    if (newRedundancy.trim() && !settings.redundancy_types.includes(newRedundancy.trim())) {
      setSettings({
        ...settings,
        redundancy_types: [...settings.redundancy_types, newRedundancy.trim()],
      });
      setNewRedundancy('');
    }
  };

  const handleDeleteRedundancy = (redundancy: string) => {
    setSettings({
      ...settings,
      redundancy_types: settings.redundancy_types.filter((r) => r !== redundancy),
    });
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Project Settings</Typography>
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
          Project settings saved successfully!
        </Alert>
      )}

      {saveMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to save settings. Please try again.
        </Alert>
      )}

      <Stack spacing={3}>
        {/* Allowed Regions */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
              Allowed Regions
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Specify which Azure regions are allowed for migration. These regions will be used to
              validate Landing Zones and Server configurations.
            </Typography>

            <TextField
              fullWidth
              size="small"
              label="Add New Region"
              placeholder="e.g., uksouth, eastus"
              value={newRegion}
              onChange={(e) => setNewRegion(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleAddRegion();
                }
              }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={handleAddRegion} edge="end" disabled={!newRegion.trim()}>
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {settings.allowed_regions.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No regions configured
                </Typography>
              ) : (
                settings.allowed_regions.map((region) => (
                  <Chip
                    key={region}
                    label={region}
                    onDelete={() => handleDeleteRegion(region)}
                    color="primary"
                    variant="outlined"
                  />
                ))
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Allowed VM SKUs */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
              Allowed VM SKUs
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Define which Azure VM sizes are permitted for server migration.
            </Typography>

            <TextField
              fullWidth
              size="small"
              label="Add New VM SKU"
              placeholder="e.g., Standard_DS2_v2"
              value={newSku}
              onChange={(e) => setNewSku(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleAddSku();
                }
              }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={handleAddSku} edge="end" disabled={!newSku.trim()}>
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {settings.allowed_vm_skus.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No VM SKUs configured
                </Typography>
              ) : (
                settings.allowed_vm_skus.map((sku) => (
                  <Chip
                    key={sku}
                    label={sku}
                    onDelete={() => handleDeleteSku(sku)}
                    color="secondary"
                    variant="outlined"
                  />
                ))
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Disk Types */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
              Disk Types
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Specify allowed disk types for server storage configuration.
            </Typography>

            <TextField
              fullWidth
              size="small"
              label="Add New Disk Type"
              placeholder="e.g., Premium_LRS, StandardSSD_LRS"
              value={newDiskType}
              onChange={(e) => setNewDiskType(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleAddDiskType();
                }
              }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleAddDiskType}
                      edge="end"
                      disabled={!newDiskType.trim()}
                    >
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {settings.disk_types.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No disk types configured
                </Typography>
              ) : (
                settings.disk_types.map((diskType) => (
                  <Chip
                    key={diskType}
                    label={diskType}
                    onDelete={() => handleDeleteDiskType(diskType)}
                    color="info"
                    variant="outlined"
                  />
                ))
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Redundancy Types */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
              Redundancy Types
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Define allowed storage redundancy options (LRS, GRS, ZRS, etc.).
            </Typography>

            <TextField
              fullWidth
              size="small"
              label="Add New Redundancy Type"
              placeholder="e.g., LRS, GRS, ZRS"
              value={newRedundancy}
              onChange={(e) => setNewRedundancy(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleAddRedundancy();
                }
              }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleAddRedundancy}
                      edge="end"
                      disabled={!newRedundancy.trim()}
                    >
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {settings.redundancy_types.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No redundancy types configured
                </Typography>
              ) : (
                settings.redundancy_types.map((redundancy) => (
                  <Chip
                    key={redundancy}
                    label={redundancy}
                    onDelete={() => handleDeleteRedundancy(redundancy)}
                    color="success"
                    variant="outlined"
                  />
                ))
              )}
            </Box>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
