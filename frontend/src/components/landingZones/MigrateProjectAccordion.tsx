import { useState } from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Typography,
  IconButton,
  Chip,
  Button,
  Checkbox,
  Stack,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as ValidateIcon,
  MoreVert as MoreVertIcon,
  Add as AddIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

interface AppLandingZone {
  subscriptionId?: string;
  region?: string;
  cacheStorageAccount?: string;
  cacheStorageResourceGroup?: string;
}

interface MigrateProject {
  migrateProjectSubscription?: string;
  migrateResourceGroup?: string;
  migrateProjectName?: string;
  applianceType?: string;
  applianceName?: string;
  recoveryVaultName?: string;
  appLandingZones?: AppLandingZone[];
}

interface MigrateProjectAccordionProps {
  migrateProject: MigrateProject;
  index: number;
  onEdit: (index: number) => void;
  onDelete: (index: number) => void;
  onValidate: (projectIndex: number, zoneIndices: number[]) => void;
  onValidateMigrateProject?: (projectIndex: number) => Promise<void>;
  onDeleteZone: (projectIndex: number, zoneIndex: number) => void;
  onAddZone: (projectIndex: number) => void;
  validationStatus?: {
    status?: string;
    lastValidatedAt?: string;
    isValidating?: boolean;
  };
}

export default function MigrateProjectAccordion({
  migrateProject,
  index,
  onEdit,
  onDelete,
  onValidate,
  onValidateMigrateProject,
  onDeleteZone,
  onAddZone,
  validationStatus,
}: MigrateProjectAccordionProps) {
  const [selectedZones, setSelectedZones] = useState<number[]>([]);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleValidateMigrateProject = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!onValidateMigrateProject) return;
    
    setIsValidating(true);
    try {
      await onValidateMigrateProject(index);
    } finally {
      setIsValidating(false);
    }
  };

  const getValidationStatusIcon = () => {
    if (isValidating || validationStatus?.isValidating) {
      return <CircularProgress size={16} />;
    }
    
    switch (validationStatus?.status) {
      case 'OK':
      case 'PASSED':
        return <CheckIcon fontSize="small" color="success" />;
      case 'FAILED':
        return <ErrorIcon fontSize="small" color="error" />;
      case 'WARNING':
        return <WarningIcon fontSize="small" color="warning" />;
      default:
        return null;
    }
  };

  const handleSelectZone = (zoneIndex: number) => {
    setSelectedZones((prev) =>
      prev.includes(zoneIndex)
        ? prev.filter((i) => i !== zoneIndex)
        : [...prev, zoneIndex]
    );
  };

  const handleSelectAll = () => {
    if (selectedZones.length === (migrateProject.appLandingZones?.length || 0)) {
      setSelectedZones([]);
    } else {
      setSelectedZones(
        Array.from({ length: migrateProject.appLandingZones?.length || 0 }, (_, i) => i)
      );
    }
  };

  const handleValidateSelected = () => {
    onValidate(index, selectedZones);
    setSelectedZones([]);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const zones = migrateProject.appLandingZones || [];
  const allSelected = selectedZones.length === zones.length && zones.length > 0;
  const someSelected = selectedZones.length > 0 && selectedZones.length < zones.length;

  return (
    <Accordion>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          '&:hover': { backgroundColor: 'action.hover' },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle1" fontWeight="medium">
              {migrateProject.migrateProjectName || 'Unnamed Project'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {migrateProject.migrateResourceGroup} • {zones.length} Landing Zone{zones.length !== 1 ? 's' : ''}
            </Typography>
          </Box>
          <Chip
            label={migrateProject.applianceName || 'No Appliance'}
            size="small"
            color="primary"
            variant="outlined"
          />
          {validationStatus?.status && (
            <Tooltip title={`Validation: ${validationStatus.status}${validationStatus.lastValidatedAt ? ` (${new Date(validationStatus.lastValidatedAt).toLocaleString()})` : ''}`}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {getValidationStatusIcon()}
              </Box>
            </Tooltip>
          )}
          <Tooltip title="Validate Migrate Project">
            <IconButton
              size="small"
              onClick={handleValidateMigrateProject}
              disabled={isValidating || validationStatus?.isValidating || !onValidateMigrateProject}
              color="primary"
            >
              <ValidateIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onEdit(index);
            }}
          >
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleMenuOpen(e);
            }}
          >
            <MoreVertIcon fontSize="small" />
          </IconButton>
        </Box>
      </AccordionSummary>

      <AccordionDetails>
        <Stack spacing={2}>
          {/* Migrate Project Details */}
          <Box
            sx={{
              p: 2,
              borderRadius: 1,
              backgroundColor: 'background.default',
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Migrate Project Details
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1, mt: 1 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Subscription
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {migrateProject.migrateProjectSubscription || 'N/A'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Resource Group
                </Typography>
                <Typography variant="body2">{migrateProject.migrateResourceGroup || 'N/A'}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Recovery Vault
                </Typography>
                <Typography variant="body2">{migrateProject.recoveryVaultName || 'N/A'}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Appliance Type
                </Typography>
                <Typography variant="body2">{migrateProject.applianceType || 'N/A'}</Typography>
              </Box>
            </Box>
          </Box>

          {/* Application Landing Zones */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Checkbox
                  checked={allSelected}
                  indeterminate={someSelected}
                  onChange={handleSelectAll}
                  size="small"
                />
                <Typography variant="subtitle2">
                  Application Landing Zones ({zones.length})
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {selectedZones.length > 0 && (
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<ValidateIcon />}
                    onClick={handleValidateSelected}
                  >
                    Validate {selectedZones.length} Zone{selectedZones.length !== 1 ? 's' : ''}
                  </Button>
                )}
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => onAddZone(index)}
                >
                  Add Zone
                </Button>
              </Box>
            </Box>

            {zones.length === 0 ? (
              <Box
                sx={{
                  p: 3,
                  textAlign: 'center',
                  border: 1,
                  borderStyle: 'dashed',
                  borderColor: 'divider',
                  borderRadius: 1,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  No application landing zones. Click "Add Zone" to create one.
                </Typography>
              </Box>
            ) : (
              <Stack spacing={1}>
                {zones.map((zone, zoneIndex) => (
                  <Box
                    key={zoneIndex}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      p: 1.5,
                      border: 1,
                      borderColor: selectedZones.includes(zoneIndex) ? 'primary.main' : 'divider',
                      borderRadius: 1,
                      backgroundColor: selectedZones.includes(zoneIndex)
                        ? 'action.selected'
                        : 'background.paper',
                      transition: 'all 0.2s',
                      '&:hover': {
                        borderColor: 'primary.main',
                        backgroundColor: 'action.hover',
                      },
                    }}
                  >
                    <Checkbox
                      checked={selectedZones.includes(zoneIndex)}
                      onChange={() => handleSelectZone(zoneIndex)}
                      size="small"
                    />
                    <Box
                      sx={{
                        flex: 1,
                        display: 'grid',
                        gridTemplateColumns: 'repeat(4, 1fr)',
                        gap: 2,
                      }}
                    >
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Region
                        </Typography>
                        <Typography variant="body2" fontWeight="medium">
                          {zone.region || 'N/A'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Subscription
                        </Typography>
                        <Tooltip title={zone.subscriptionId || 'N/A'}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {zone.subscriptionId || 'N/A'}
                          </Typography>
                        </Tooltip>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Cache Storage
                        </Typography>
                        <Typography variant="body2">{zone.cacheStorageAccount || 'N/A'}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Cache RG
                        </Typography>
                        <Typography variant="body2">{zone.cacheStorageResourceGroup || 'N/A'}</Typography>
                      </Box>
                    </Box>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => onDeleteZone(index, zoneIndex)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Stack>
            )}
          </Box>
        </Stack>
      </AccordionDetails>

      {/* More Menu */}
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem
          onClick={() => {
            handleMenuClose();
            onEdit(index);
          }}
        >
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit Project</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleMenuClose();
            onDelete(index);
          }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText sx={{ color: 'error.main' }}>Delete Project</ListItemText>
        </MenuItem>
      </Menu>
    </Accordion>
  );
}
