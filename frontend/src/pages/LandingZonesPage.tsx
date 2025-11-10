import { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  Button,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Stack,
} from '@mui/material';
import {
  Search as SearchIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { landingZonesService } from '../services/landingZones.service';
import type { Project, LandingZoneMigrateProject } from '../types/project.types';

export default function LandingZonesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [selectedMigrateProjects, setSelectedMigrateProjects] = useState<LandingZoneMigrateProject[]>([]);

  // Fetch all projects
  const { data: projectsData, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: () => landingZonesService.getAllProjects(),
  });

  const projects = projectsData?.items || [];

  // Filter projects by search term
  const filteredProjects = projects.filter((project) => {
    const normalizedSearch = searchTerm.toLowerCase();
    return (
      project.name.toLowerCase().includes(normalizedSearch) ||
      project.azure_tenant_id.toLowerCase().includes(normalizedSearch)
    );
  });

  const handleViewDetails = (project: Project) => {
    const migrateProjects = project.lz_migrate_projects ?? [];
    setSelectedProject(project);
    setSelectedMigrateProjects(migrateProjects);
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    setSelectedProject(null);
    setSelectedMigrateProjects([]);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Landing Zones
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure Azure Migrate and Site Recovery landing zones for your projects
          </Typography>
        </Box>
      </Box>

      {/* Search */}
      <Box sx={{ mb: 3 }}>
        <TextField
          placeholder="Search by project name or subscription ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          fullWidth
        />
      </Box>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load projects. Please try again.
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Empty State */}
      {!isLoading && projects.length === 0 && (
        <Alert severity="info">
          No projects found. Create a project first to configure landing zones.
        </Alert>
      )}

      {/* Projects Table */}
      {!isLoading && filteredProjects.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Project Name</TableCell>
                <TableCell>Subscription ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Landing Zone Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredProjects.map((project) => {
                const migrateProjects = project.lz_migrate_projects ?? [];
                const hasLandingZone = migrateProjects.length > 0;
                const landingZoneLabel = hasLandingZone
                  ? `Configured (${migrateProjects.length})`
                  : 'Not Configured';

                return (
                  <TableRow key={project.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {project.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                        {project.azure_tenant_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={project.status.replace('_', ' ').toUpperCase()}
                        size="small"
                        color={
                          project.status === 'active'
                            ? 'success'
                            : project.status === 'in_progress'
                            ? 'warning'
                            : project.status === 'completed'
                            ? 'info'
                            : 'error'
                        }
                      />
                    </TableCell>
                    <TableCell>
                      {hasLandingZone ? (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label={landingZoneLabel}
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                      ) : (
                        <Chip
                          icon={<CancelIcon />}
                          label="Not Configured"
                          size="small"
                          color="warning"
                          variant="outlined"
                        />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {hasLandingZone ? (
                        <Button size="small" variant="outlined" onClick={() => handleViewDetails(project)}>
                          View Details
                        </Button>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No landing zone data
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* No Results */}
      {!isLoading && projects.length > 0 && filteredProjects.length === 0 && (
        <Alert severity="info">No projects match your search criteria.</Alert>
      )}

      {/* Details Dialog */}
      {selectedProject && (
        <Dialog open={detailsOpen} onClose={handleCloseDetails} fullWidth maxWidth="md">
          <DialogTitle>{selectedProject.name} Landing Zones</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Tenant ID
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {selectedProject.azure_tenant_id}
                </Typography>
              </Box>

              {selectedMigrateProjects.length === 0 ? (
                <Alert severity="info">No landing zone configuration found for this project.</Alert>
              ) : (
                selectedMigrateProjects.map((migrateProject, index) => (
                  <Box key={`${migrateProject.migrateProjectName}-${index}`}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="subtitle1" fontWeight="medium">
                        {migrateProject.migrateProjectName || `Landing Zone ${index + 1}`}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Appliance: {migrateProject.applianceType ?? migrateProject.applianceName ?? 'N/A'}
                      </Typography>
                    </Stack>
                    <Stack spacing={1}>
                      <Typography variant="body2">
                        Migrate Subscription: {migrateProject.migrateProjectSubscription || 'N/A'}
                      </Typography>
                      <Typography variant="body2">
                        Migrate Resource Group: {migrateProject.migrateResourceGroup || 'N/A'}
                      </Typography>
                      <Typography variant="body2">
                        Recovery Vault: {migrateProject.recoveryVaultName || 'N/A'}
                      </Typography>
                      {migrateProject.appLandingZones?.length ? (
                        <Box>
                          <Typography variant="body2" fontWeight="medium" gutterBottom>
                            Application Landing Zones
                          </Typography>
                          <Stack spacing={1}>
                            {migrateProject.appLandingZones.map((zone, zoneIndex) => (
                              <Box key={`${zone.subscriptionId}-${zoneIndex}`} sx={{ pl: 1 }}>
                                <Typography variant="body2">
                                  Subscription: {zone.subscriptionId || 'N/A'}
                                </Typography>
                                <Typography variant="body2">
                                  Region: {zone.region || 'N/A'}
                                </Typography>
                                <Typography variant="body2">
                                  Cache Storage: {zone.cacheStorageAccount || 'N/A'}
                                </Typography>
                                <Typography variant="body2">
                                  Cache RG: {zone.cacheStorageResourceGroup || 'N/A'}
                                </Typography>
                                {zoneIndex < migrateProject.appLandingZones.length - 1 && <Divider sx={{ mt: 1 }} />}
                              </Box>
                            ))}
                          </Stack>
                        </Box>
                      ) : (
                        <Typography variant="body2">No application landing zones linked.</Typography>
                      )}
                    </Stack>
                    {index < selectedMigrateProjects.length - 1 && <Divider sx={{ mt: 2 }} />}
                  </Box>
                ))
              )}
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDetails}>Close</Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
}
