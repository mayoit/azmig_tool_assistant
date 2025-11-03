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
  IconButton,
  InputAdornment,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Tooltip,
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

export default function ServersPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const projectId = id ? Number(id) : undefined;

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
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
    queryKey: ['servers', projectId, page, rowsPerPage],
    queryFn: () =>
      serversService.getAll(projectId!, {
        page: page + 1,
        limit: rowsPerPage,
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

  const handleDelete = (serverId: number) => {
    if (window.confirm('Are you sure you want to delete this server?')) {
      deleteMutation.mutate(serverId);
    }
  };

  const handleDeleteAll = () => {
    if (window.confirm('This will delete all servers for this project. Continue?')) {
      deleteAllMutation.mutate();
    }
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
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
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Region</TableCell>
                  <TableCell>Subscription</TableCell>
                  <TableCell>Resource Group</TableCell>
                  <TableCell>VNet / Subnet</TableCell>
                  <TableCell>SKU</TableCell>
                  <TableCell>Disk Type</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredServers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography variant="body2" color="text.secondary">
                        {searchTerm ? 'No servers match your search criteria.' : 'No servers uploaded yet.'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredServers.map((server: ServerConfig) => (
                    <TableRow key={server.id} hover>
                      <TableCell>{server.target_machine_name}</TableCell>
                      <TableCell>{server.target_region}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {server.target_subscription}
                        </Typography>
                      </TableCell>
                      <TableCell>{server.target_resource_group}</TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {server.target_vnet} / {server.target_subnet}
                        </Typography>
                      </TableCell>
                      <TableCell>{server.target_machine_sku}</TableCell>
                      <TableCell>{server.target_disk_type}</TableCell>
                      <TableCell align="right">
                        <Tooltip title="Delete server">
                          <span>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDelete(server.id)}
                              disabled={deleteMutation.isPending}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={serverData?.total ?? 0}
            page={page}
            rowsPerPage={rowsPerPage}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            rowsPerPageOptions={[5, 10, 25, 50]}
          />
        </Paper>
      )}
    </Box>
  );
}
