import React, { useState, useEffect } from 'react';
import {
  DataGrid,
  GridRowModes,
  GridActionsCellItem,
  GridRowEditStopReasons,
} from '@mui/x-data-grid';
import type {
  GridColDef,
  GridRowModesModel,
  GridEventListener,
  GridRowId,
  GridRowModel,
} from '@mui/x-data-grid';
import {
  Box,
  Button,
  Typography,
  Alert,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Close';
import { serversService } from '../../services/servers.service';
import type { ServerConfig } from '../../types/server.types';

interface ServerTableProps {
  projectId: number;
}

type ServerRow = Partial<Omit<ServerConfig, 'id'>> & {
  id: number | string;
  isNew?: boolean;
};

const ServerTable: React.FC<ServerTableProps> = ({ projectId }) => {
  const [rows, setRows] = useState<ServerRow[]>([]);
  const [rowModesModel, setRowModesModel] = useState<GridRowModesModel>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [totalRows, setTotalRows] = useState(0);

  const loadServers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await serversService.getAll(projectId, {
        page: page + 1,
        limit: pageSize,
      });
      setRows(response.items);
      setTotalRows(response.total);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to load servers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServers();
  }, [projectId, page, pageSize]);

  const handleRowEditStop: GridEventListener<'rowEditStop'> = (params, event) => {
    if (params.reason === GridRowEditStopReasons.rowFocusOut) {
      event.defaultMuiPrevented = true;
    }
  };

  const handleEditClick = (id: GridRowId) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.Edit } });
  };

  const handleSaveClick = (id: GridRowId) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.View } });
  };

  const handleDeleteClick = (id: GridRowId) => async () => {
    const row = rows.find((r) => r.id === id);
    if (row?.isNew) {
      // Just remove from local state if not yet saved
      setRows(rows.filter((r) => r.id !== id));
      return;
    }

    try {
      await serversService.delete(projectId, id as number);
      setRows(rows.filter((r) => r.id !== id));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete server');
    }
  };

  const handleCancelClick = (id: GridRowId) => () => {
    const row = rows.find((r) => r.id === id);
    if (row?.isNew) {
      setRows(rows.filter((r) => r.id !== id));
      return;
    }

    setRowModesModel({
      ...rowModesModel,
      [id]: { mode: GridRowModes.View, ignoreModifications: true },
    });
  };

  const processRowUpdate = async (newRow: GridRowModel): Promise<GridRowModel> => {
    const updatedRow = { ...newRow } as ServerRow;

    try {
      if (updatedRow.isNew) {
        // Create new server
        const created = await serversService.create(projectId, {
          target_machine_name: updatedRow.target_machine_name || '',
          target_resource_group: updatedRow.target_resource_group || '',
          target_vnet: updatedRow.target_vnet || '',
          target_subnet: updatedRow.target_subnet || '',
          target_region: updatedRow.target_region || '',
          target_subscription: updatedRow.target_subscription || '',
          target_machine_sku: updatedRow.target_machine_sku || '',
          target_disk_type: updatedRow.target_disk_type || '',
        });
        
        setRows(rows.map((row) => (row.id === updatedRow.id ? created : row)));
        return created;
      } else {
        // Update existing server
        const updated = await serversService.update(updatedRow.id as number, {
          target_machine_name: updatedRow.target_machine_name,
          target_resource_group: updatedRow.target_resource_group,
          target_vnet: updatedRow.target_vnet,
          target_subnet: updatedRow.target_subnet,
          target_region: updatedRow.target_region,
          target_subscription: updatedRow.target_subscription,
          target_machine_sku: updatedRow.target_machine_sku,
          target_disk_type: updatedRow.target_disk_type,
        });
        
        setRows(rows.map((row) => (row.id === updatedRow.id ? updated : row)));
        return updated;
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save server');
      throw err;
    }
  };

  const handleRowModesModelChange = (newRowModesModel: GridRowModesModel) => {
    setRowModesModel(newRowModesModel);
  };

  const handleAddClick = () => {
    const newId = `new-${Date.now()}`;
    const newRow: ServerRow = {
      id: newId,
      target_machine_name: '',
      target_resource_group: '',
      target_vnet: '',
      target_subnet: '',
      target_region: '',
      target_subscription: '',
      target_machine_sku: '',
      target_disk_type: '',
      isNew: true,
    };
    
    setRows((oldRows) => [newRow, ...oldRows]);
    setRowModesModel((oldModel) => ({
      ...oldModel,
      [newId]: { mode: GridRowModes.Edit, fieldToFocus: 'target_machine_name' },
    }));
  };

  const columns: GridColDef[] = [
    {
      field: 'target_machine_name',
      headerName: 'Target Machine',
      flex: 1,
      minWidth: 150,
      editable: true,
    },
    {
      field: 'target_resource_group',
      headerName: 'Target RG',
      flex: 1,
      minWidth: 150,
      editable: true,
    },
    {
      field: 'target_vnet',
      headerName: 'Target VNet',
      flex: 1,
      minWidth: 150,
      editable: true,
    },
    {
      field: 'target_subnet',
      headerName: 'Target Subnet',
      flex: 1,
      minWidth: 150,
      editable: true,
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 100,
      cellClassName: 'actions',
      getActions: ({ id }) => {
        const isInEditMode = rowModesModel[id]?.mode === GridRowModes.Edit;

        if (isInEditMode) {
          return [
            <GridActionsCellItem
              icon={<SaveIcon />}
              label="Save"
              onClick={handleSaveClick(id)}
            />,
            <GridActionsCellItem
              icon={<CancelIcon />}
              label="Cancel"
              onClick={handleCancelClick(id)}
              color="inherit"
            />,
          ];
        }

        return [
          <GridActionsCellItem
            icon={<EditIcon />}
            label="Edit"
            onClick={handleEditClick(id)}
            color="inherit"
          />,
          <GridActionsCellItem
            icon={<DeleteIcon />}
            label="Delete"
            onClick={handleDeleteClick(id)}
            color="inherit"
          />,
        ];
      },
    },
  ];

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Servers</Typography>
        <Button
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleAddClick}
          variant="contained"
        >
          Add Server
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ height: 500, width: '100%' }}>
        <DataGrid
          rows={rows}
          columns={columns}
          editMode="row"
          rowModesModel={rowModesModel}
          onRowModesModelChange={handleRowModesModelChange}
          onRowEditStop={handleRowEditStop}
          processRowUpdate={processRowUpdate}
          loading={loading}
          pageSizeOptions={[5, 10, 25, 50]}
          paginationMode="server"
          rowCount={totalRows}
          paginationModel={{ page, pageSize }}
          onPaginationModelChange={(model) => {
            setPage(model.page);
            setPageSize(model.pageSize);
          }}
          sx={{
            '& .actions': {
              color: 'text.secondary',
            },
            '& .textPrimary': {
              color: 'text.primary',
            },
          }}
        />
      </Box>
    </Box>
  );
};

export default ServerTable;
