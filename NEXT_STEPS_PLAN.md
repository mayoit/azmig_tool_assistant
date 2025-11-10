# Azure Migration Tool - Next Development Steps

**Last Updated**: November 4, 2025  
**Current Status**: Validation system complete, UI foundation ready  
**Focus Area**: Completing critical user workflows (Weeks 2-3 of UI implementation)

---

## ✅ Current Completion Status

### Phase 1: Core Infrastructure (100% Complete)
- ✅ Backend API with validation engine
- ✅ PostgreSQL database with validation events
- ✅ Frontend scaffolding (React + TypeScript + MUI)
- ✅ Authentication & routing
- ✅ All validation bugs fixed (status mapping, cache storage subscription)
- ✅ ValidationEventLog component with Azure Activity Log-style UI

### Phase 2: Active Development
We're currently at **Week 1 complete** of the UI implementation plan.

---

## 🎯 Priority 1: Critical Path Tasks (Next 2 Weeks)

These tasks are **MUST-DO** for a functional MVP. They enable the complete end-to-end workflow.

### Task 1: Enhanced Server Management UI (Week 2, Days 1-4)
**Status**: 🟡 IN PROGRESS (ServersPage.tsx exists but incomplete)  
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 3-4 days  

#### Current State Analysis
- ✅ Basic ServersPage with search functionality
- ✅ File upload input with mutation
- ✅ Pagination and table display
- ❌ No drag-and-drop UI
- ❌ No advanced table features (sorting, filtering, bulk operations)
- ❌ No bulk edit capabilities

#### Implementation Steps

**Step 1.1**: Install Dependencies
```bash
npm install react-dropzone @tanstack/react-table
npm install --save-dev @types/react-dropzone
```

**Step 1.2**: Create ServerUploadZone Component
```tsx
// frontend/src/components/servers/ServerUploadZone.tsx
import { useDropzone } from 'react-dropzone';
import { Box, Typography, LinearProgress } from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';

interface ServerUploadZoneProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
  uploadProgress: number;
}

export default function ServerUploadZone({ 
  onUpload, 
  isUploading, 
  uploadProgress 
}: ServerUploadZoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
  });

  return (
    <Box
      {...getRootProps()}
      sx={{
        border: 2,
        borderStyle: 'dashed',
        borderColor: isDragActive ? 'primary.main' : 'grey.300',
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        cursor: 'pointer',
        bgcolor: isDragActive ? 'action.hover' : 'background.paper',
        transition: 'all 0.2s',
        '&:hover': {
          borderColor: 'primary.main',
          bgcolor: 'action.hover',
        },
      }}
    >
      <input {...getInputProps()} />
      <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
      <Typography variant="h6" gutterBottom>
        {isDragActive ? 'Drop the file here' : 'Drag & drop Excel file here'}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        or click to browse (supports .xlsx, .xls)
      </Typography>
      
      {isUploading && (
        <Box sx={{ mt: 3, width: '100%' }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            Uploading... {uploadProgress}%
          </Typography>
        </Box>
      )}
    </Box>
  );
}
```

**Step 1.3**: Create Advanced ServerTable Component
```tsx
// frontend/src/components/servers/ServerTable.tsx
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  IconButton,
  Tooltip,
  Box,
  TextField,
  TablePagination,
} from '@mui/material';
import { Edit, Delete, FileDownload } from '@mui/icons-material';
import type { ServerConfig } from '../../types/server.types';

interface ServerTableProps {
  data: ServerConfig[];
  onEdit: (server: ServerConfig) => void;
  onDelete: (serverId: number) => void;
  onBulkEdit: (serverIds: number[]) => void;
  onExport: () => void;
}

export default function ServerTable({
  data,
  onEdit,
  onDelete,
  onBulkEdit,
  onExport,
}: ServerTableProps) {
  const [rowSelection, setRowSelection] = React.useState({});

  const columns: ColumnDef<ServerConfig>[] = [
    {
      id: 'select',
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllRowsSelected()}
          indeterminate={table.getIsSomeRowsSelected()}
          onChange={table.getToggleAllRowsSelectedHandler()}
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
        />
      ),
    },
    {
      accessorKey: 'target_machine_name',
      header: 'Machine Name',
      cell: (info) => info.getValue(),
    },
    {
      accessorKey: 'target_region',
      header: 'Region',
      cell: (info) => info.getValue(),
    },
    {
      accessorKey: 'target_subscription',
      header: 'Subscription',
      cell: (info) => (
        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
          {String(info.getValue()).substring(0, 8)}...
        </Typography>
      ),
    },
    {
      accessorKey: 'target_resource_group',
      header: 'Resource Group',
      cell: (info) => info.getValue(),
    },
    {
      accessorKey: 'target_machine_sku',
      header: 'SKU',
      cell: (info) => info.getValue(),
    },
    {
      accessorKey: 'target_disk_type',
      header: 'Disk Type',
      cell: (info) => info.getValue(),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => onEdit(row.original)}>
              <Edit fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton size="small" color="error" onClick={() => onDelete(row.original.id)}>
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onRowSelectionChange: setRowSelection,
    state: {
      rowSelection,
    },
  });

  const selectedRowIds = Object.keys(rowSelection).map((id) => data[parseInt(id)].id);

  return (
    <Paper>
      {/* Bulk Actions Toolbar */}
      {selectedRowIds.length > 0 && (
        <Box sx={{ p: 2, bgcolor: 'action.selected', display: 'flex', gap: 2, alignItems: 'center' }}>
          <Typography variant="body2">
            {selectedRowIds.length} selected
          </Typography>
          <Button size="small" onClick={() => onBulkEdit(selectedRowIds)}>
            Bulk Edit
          </Button>
          <Button size="small" startIcon={<FileDownload />} onClick={onExport}>
            Export Selected
          </Button>
        </Box>
      )}

      <TableContainer>
        <Table>
          <TableHead>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableCell key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableHead>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} hover>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={data.length}
        page={table.getState().pagination.pageIndex}
        rowsPerPage={table.getState().pagination.pageSize}
        onPageChange={(_, page) => table.setPageIndex(page)}
        onRowsPerPageChange={(e) => table.setPageSize(Number(e.target.value))}
        rowsPerPageOptions={[10, 25, 50, 100]}
      />
    </Paper>
  );
}
```

**Step 1.4**: Create BulkEditModal Component
```tsx
// frontend/src/components/servers/BulkEditModal.tsx
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';

interface BulkEditModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (updates: Partial<ServerConfig>) => void;
  serverCount: number;
}

export default function BulkEditModal({
  open,
  onClose,
  onSubmit,
  serverCount,
}: BulkEditModalProps) {
  const [formData, setFormData] = React.useState({
    target_region: '',
    target_resource_group: '',
    target_vnet: '',
    target_subnet: '',
    target_machine_sku: '',
    target_disk_type: '',
  });

  const handleSubmit = () => {
    // Filter out empty fields
    const updates = Object.entries(formData).reduce((acc, [key, value]) => {
      if (value) acc[key] = value;
      return acc;
    }, {} as Partial<ServerConfig>);

    onSubmit(updates);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Bulk Edit Servers</DialogTitle>
      <DialogContent>
        <Alert severity="info" sx={{ mb: 2 }}>
          Editing {serverCount} servers. Only filled fields will be updated.
        </Alert>

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Region"
              value={formData.target_region}
              onChange={(e) => setFormData({ ...formData, target_region: e.target.value })}
              placeholder="Leave empty to keep current"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Resource Group"
              value={formData.target_resource_group}
              onChange={(e) => setFormData({ ...formData, target_resource_group: e.target.value })}
              placeholder="Leave empty to keep current"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="VNet"
              value={formData.target_vnet}
              onChange={(e) => setFormData({ ...formData, target_vnet: e.target.value })}
              placeholder="Leave empty to keep current"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Subnet"
              value={formData.target_subnet}
              onChange={(e) => setFormData({ ...formData, target_subnet: e.target.value })}
              placeholder="Leave empty to keep current"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="VM SKU"
              value={formData.target_machine_sku}
              onChange={(e) => setFormData({ ...formData, target_machine_sku: e.target.value })}
              placeholder="Leave empty to keep current"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Disk Type</InputLabel>
              <Select
                value={formData.target_disk_type}
                onChange={(e) => setFormData({ ...formData, target_disk_type: e.target.value })}
              >
                <MenuItem value="">Keep current</MenuItem>
                <MenuItem value="Standard_LRS">Standard LRS</MenuItem>
                <MenuItem value="Premium_LRS">Premium LRS</MenuItem>
                <MenuItem value="StandardSSD_LRS">Standard SSD LRS</MenuItem>
                <MenuItem value="UltraSSD_LRS">Ultra SSD LRS</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained">
          Update {serverCount} Servers
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

**Step 1.5**: Update ServersPage to Use New Components
- Replace current upload input with ServerUploadZone
- Replace current table with ServerTable
- Add BulkEditModal integration
- Add export functionality using xlsx library

**Acceptance Criteria**:
- [ ] Drag-and-drop upload zone with visual feedback
- [ ] Upload progress bar shows real-time percentage
- [ ] Advanced table with sorting, filtering, pagination
- [ ] Row selection with bulk operations
- [ ] Bulk edit modal updates multiple servers
- [ ] Export to Excel downloads filtered/selected servers

---

### Task 2: Validation Results Viewer with Export (Week 2, Days 5-7)
**Status**: 🟡 IN PROGRESS (ValidationsPage.tsx placeholder only)  
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 2-3 days  

#### Current State Analysis
- ✅ ValidationEventLog component complete and working
- ✅ Validation events API endpoint working
- ❌ ValidationsPage is just a placeholder
- ❌ No job list view
- ❌ No export functionality

#### Implementation Steps

**Step 2.1**: Install Export Dependencies
```bash
npm install xlsx file-saver
npm install --save-dev @types/file-saver
```

**Step 2.2**: Create ValidationJobList Component
```tsx
// frontend/src/components/validations/ValidationJobList.tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Collapse,
  Box,
  Typography,
} from '@mui/material';
import { ExpandMore, ExpandLess, FileDownload } from '@mui/icons-material';
import { format } from 'date-fns';
import ValidationEventLog from './ValidationEventLog';
import type { ValidationJob } from '../../types/validation.types';

interface ValidationJobListProps {
  jobs: ValidationJob[];
  onRefresh: () => void;
  onExport: (jobId: number) => void;
}

export default function ValidationJobList({ jobs, onRefresh, onExport }: ValidationJobListProps) {
  const [expandedRow, setExpandedRow] = React.useState<number | null>(null);

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'COMPLETED': return 'success';
      case 'RUNNING': return 'info';
      case 'FAILED': return 'error';
      case 'PENDING': return 'warning';
      default: return 'default';
    }
  };

  return (
    <>
      {jobs.map((job) => (
        <React.Fragment key={job.id}>
          <TableRow hover onClick={() => setExpandedRow(expandedRow === job.id ? null : job.id)}>
            <TableCell>
              <IconButton size="small">
                {expandedRow === job.id ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </TableCell>
            <TableCell>#{job.id}</TableCell>
            <TableCell>
              <Chip 
                label={job.status} 
                color={getStatusColor(job.status)} 
                size="small" 
              />
            </TableCell>
            <TableCell>{format(new Date(job.created_at), 'MMM d, yyyy HH:mm')}</TableCell>
            <TableCell>{job.completed_at ? format(new Date(job.completed_at), 'MMM d, yyyy HH:mm') : '-'}</TableCell>
            <TableCell>
              {job.passed}/{job.passed + job.failed} passed
            </TableCell>
            <TableCell>
              <IconButton size="small" onClick={(e) => { e.stopPropagation(); onExport(job.id); }}>
                <FileDownload />
              </IconButton>
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell colSpan={7} sx={{ py: 0 }}>
              <Collapse in={expandedRow === job.id} timeout="auto" unmountOnExit>
                <Box sx={{ py: 2 }}>
                  <ValidationEventLog 
                    serverValidations={[job]}
                    landingZoneValidations={[]}
                    onRefresh={onRefresh}
                    isLoading={false}
                  />
                </Box>
              </Collapse>
            </TableCell>
          </TableRow>
        </React.Fragment>
      ))}
    </>
  );
}
```

**Step 2.3**: Add Export Functionality
```tsx
// frontend/src/utils/exportValidation.ts
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import type { ValidationEvent } from '../types/validation.types';

export function exportValidationToExcel(events: ValidationEvent[], jobId: number) {
  const worksheetData = events.map(event => ({
    'Event ID': event.id,
    'Stage': event.stage,
    'Status': event.status,
    'Message': event.message,
    'Details': event.details || '',
    'Duration (ms)': event.duration_ms,
    'Timestamp': new Date(event.event_timestamp).toLocaleString(),
  }));

  const worksheet = XLSX.utils.json_to_sheet(worksheetData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Validation Results');

  // Auto-size columns
  const maxWidth = worksheetData.reduce((w, r) => Math.max(w, r.Message.length), 10);
  worksheet['!cols'] = [
    { wch: 10 }, // Event ID
    { wch: 20 }, // Stage
    { wch: 10 }, // Status
    { wch: maxWidth }, // Message
    { wch: 30 }, // Details
    { wch: 15 }, // Duration
    { wch: 20 }, // Timestamp
  ];

  const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
  const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  saveAs(blob, `validation-results-job-${jobId}-${Date.now()}.xlsx`);
}
```

**Step 2.4**: Update ValidationsPage
- Replace placeholder with ValidationJobList
- Add filters (status, date range)
- Add "Trigger Validation" button
- Integrate export functionality

**Acceptance Criteria**:
- [ ] Job list shows all validation jobs with status
- [ ] Clicking job row expands ValidationEventLog inline
- [ ] Export button downloads Excel with all event details
- [ ] Filters work for status and date range
- [ ] "Trigger Validation" starts new job and auto-navigates to results

---

### Task 3: Dashboard Implementation (Week 3, Days 1-4)
**Status**: 🟡 IN PROGRESS (DashboardPage exists with partial implementation)  
**Priority**: 🟡 HIGH  
**Estimated Time**: 3-4 days  

#### Current State Analysis
- ✅ DashboardPage skeleton with query hooks
- ✅ StatisticsCard component exists
- ✅ RecentJobs component exists
- ✅ ValidationChart component exists
- ⚠️ Dashboard service exists but backend endpoint might be missing
- ❌ Charts not implemented (ValidationChart placeholder)

#### Implementation Steps

**Step 3.1**: Verify/Create Backend Endpoint
```python
# api/routers/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import Project, ValidationJob, ServerConfig

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == 'active').count()
    total_servers = db.query(ServerConfig).count()
    total_validations = db.query(ValidationJob).count()
    
    # Calculate success rate
    completed_jobs = db.query(ValidationJob).filter(
        ValidationJob.status == 'COMPLETED'
    ).all()
    if completed_jobs:
        success_rate = sum(1 for job in completed_jobs if job.all_passed) / len(completed_jobs) * 100
    else:
        success_rate = 0
    
    # Recent jobs (last 10)
    recent_jobs = db.query(ValidationJob).order_by(
        ValidationJob.created_at.desc()
    ).limit(10).all()
    
    # Trend data (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    trend_jobs = db.query(ValidationJob).filter(
        ValidationJob.created_at >= thirty_days_ago
    ).all()
    
    # Group by date
    from collections import defaultdict
    trends = defaultdict(lambda: {'passed': 0, 'failed': 0})
    for job in trend_jobs:
        date_key = job.created_at.strftime('%Y-%m-%d')
        if job.all_passed:
            trends[date_key]['passed'] += 1
        else:
            trends[date_key]['failed'] += 1
    
    trend_data = [
        {'date': date, 'passed': counts['passed'], 'failed': counts['failed']}
        for date, counts in sorted(trends.items())
    ]
    
    return {
        'stats': {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'total_servers': total_servers,
            'total_validations': total_validations,
            'success_rate': round(success_rate, 1),
        },
        'recent_jobs': [
            {
                'id': job.id,
                'project_id': job.project_id,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'all_passed': job.all_passed,
            }
            for job in recent_jobs
        ],
        'trends': trend_data,
    }
```

**Step 3.2**: Install Chart Library
```bash
npm install recharts
npm install --save-dev @types/recharts
```

**Step 3.3**: Implement ValidationChart Component
```tsx
// frontend/src/components/dashboard/ValidationChart.tsx (update existing)
import { Card, CardContent, Typography } from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ValidationChartProps {
  trends: Array<{ date: string; passed: number; failed: number }>;
}

export default function ValidationChart({ trends }: ValidationChartProps) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Validation Trends (Last 30 Days)
        </Typography>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="passed" 
              stroke="#4caf50" 
              name="Passed" 
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="failed" 
              stroke="#f44336" 
              name="Failed" 
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

**Step 3.4**: Enhance StatisticsCard with Trends
```tsx
// Add trend indicator (optional enhancement)
<Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
  {trend !== undefined && trend !== 0 && (
    <>
      <TrendingUp color={trend > 0 ? 'success' : 'error'} fontSize="small" />
      <Typography variant="caption" color={trend > 0 ? 'success.main' : 'error.main'}>
        {trend > 0 ? '+' : ''}{trend}% from last week
      </Typography>
    </>
  )}
</Box>
```

**Acceptance Criteria**:
- [ ] Four stat cards display correct real-time data
- [ ] Stat cards auto-refresh every 30 seconds
- [ ] Recent jobs table shows last 10 validations with status
- [ ] Line chart displays pass/fail trends over 30 days
- [ ] All data loads from backend `/dashboard/stats` endpoint
- [ ] Loading states show skeletons, not blank cards

---

## 🎯 Priority 2: Reports & Analytics (Week 3, Days 5-7)

### Task 4: Reports Page with Charts & PDF Export
**Status**: ❌ NOT STARTED (ReportsPage.tsx is placeholder)  
**Priority**: 🟡 HIGH  
**Estimated Time**: 3-4 days  

#### Implementation Steps

**Step 4.1**: Install PDF Export Library
```bash
npm install jspdf jspdf-autotable
npm install --save-dev @types/jspdf
```

**Step 4.2**: Create Report Data Service
```typescript
// frontend/src/services/reports.service.ts
import api from './api';

export const reportsService = {
  async getValidationSummary(projectId: number, dateRange: { start: string; end: string }) {
    const response = await api.get(`/reports/validation-summary`, {
      params: { project_id: projectId, ...dateRange },
    });
    return response.data;
  },

  async getResourceInventory(projectId: number) {
    const response = await api.get(`/reports/resource-inventory`, {
      params: { project_id: projectId },
    });
    return response.data;
  },
};
```

**Step 4.3**: Create ValidationSummaryTab Component
```tsx
// frontend/src/components/reports/ValidationSummaryTab.tsx
import { Grid, Card, CardContent, Typography, Box } from '@mui/material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

interface ValidationSummaryTabProps {
  data: {
    total_validations: number;
    passed: number;
    failed: number;
    success_rate: number;
    stage_breakdown: Array<{ stage: string; passed: number; failed: number }>;
    common_failures: Array<{ message: string; count: number }>;
  };
}

export default function ValidationSummaryTab({ data }: ValidationSummaryTabProps) {
  const pieData = [
    { name: 'Passed', value: data.passed, color: '#4caf50' },
    { name: 'Failed', value: data.failed, color: '#f44336' },
  ];

  return (
    <Grid container spacing={3}>
      {/* Pie Chart */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Overall Pass/Fail Ratio</Typography>
            <PieChart width={400} height={300}>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {pieData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </CardContent>
        </Card>
      </Grid>

      {/* Bar Chart */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Pass Rate by Stage</Typography>
            <BarChart width={400} height={300} data={data.stage_breakdown}>
              <XAxis dataKey="stage" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="passed" fill="#4caf50" name="Passed" />
              <Bar dataKey="failed" fill="#f44336" name="Failed" />
            </BarChart>
          </CardContent>
        </Card>
      </Grid>

      {/* Common Failures Table */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Top 10 Most Common Failures</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Failure Message</TableCell>
                  <TableCell align="right">Occurrences</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.common_failures.slice(0, 10).map((failure, index) => (
                  <TableRow key={index}>
                    <TableCell>{failure.message}</TableCell>
                    <TableCell align="right">{failure.count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
```

**Step 4.4**: Create PDF Export Utility
```tsx
// frontend/src/utils/exportPDF.ts
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

export function exportReportToPDF(reportData: any, projectName: string) {
  const doc = new jsPDF();

  // Header
  doc.setFontSize(20);
  doc.text('Azure Migration Validation Report', 14, 20);
  
  doc.setFontSize(12);
  doc.text(`Project: ${projectName}`, 14, 30);
  doc.text(`Generated: ${new Date().toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })}`, 14, 37);

  // Summary Stats
  autoTable(doc, {
    head: [['Metric', 'Value']],
    body: [
      ['Total Validations', reportData.total_validations],
      ['Passed', reportData.passed],
      ['Failed', reportData.failed],
      ['Success Rate', `${reportData.success_rate}%`],
    ],
    startY: 45,
    theme: 'grid',
  });

  // Stage Breakdown
  autoTable(doc, {
    head: [['Stage', 'Total', 'Passed', 'Failed', 'Pass Rate']],
    body: reportData.stage_breakdown.map((stage: any) => [
      stage.stage,
      stage.passed + stage.failed,
      stage.passed,
      stage.failed,
      `${Math.round((stage.passed / (stage.passed + stage.failed)) * 100)}%`,
    ]),
    startY: (doc as any).lastAutoTable.finalY + 10,
    theme: 'grid',
  });

  // Common Failures
  autoTable(doc, {
    head: [['Failure Message', 'Count']],
    body: reportData.common_failures.slice(0, 10).map((f: any) => [f.message, f.count]),
    startY: (doc as any).lastAutoTable.finalY + 10,
    theme: 'grid',
  });

  doc.save(`validation-report-${projectName}-${Date.now()}.pdf`);
}
```

**Acceptance Criteria**:
- [ ] Validation Summary tab shows pie chart (pass/fail ratio)
- [ ] Bar chart displays pass rate per validation stage
- [ ] Table lists top 10 most common failures
- [ ] Resource Inventory tab shows server distribution by region/SKU
- [ ] Date range selector filters report data
- [ ] PDF export generates comprehensive multi-page report
- [ ] Excel export works for all data tables

---

## 🎯 Priority 3: UX Enhancements (Week 4)

### Task 5: Real-Time WebSocket Updates
**Status**: ❌ NOT STARTED  
**Priority**: 🟢 MEDIUM (Can defer to Week 5 if time-constrained)  
**Estimated Time**: 2-3 days  

**Note**: Requires backend WebSocket endpoint implementation first.

### Task 6: Loading States & Empty States
**Status**: 🟡 PARTIAL (Some loading spinners exist)  
**Priority**: 🟢 MEDIUM  
**Estimated Time**: 2 days  

#### Quick Wins
1. **Add Skeleton Screens** (replace CircularProgress)
```tsx
import { Skeleton } from '@mui/material';

{isLoading ? (
  <Stack spacing={1}>
    <Skeleton variant="rectangular" height={118} />
    <Skeleton variant="text" />
    <Skeleton variant="text" width="60%" />
  </Stack>
) : (
  <ProjectCard project={project} />
)}
```

2. **Create EmptyState Component**
```tsx
// frontend/src/components/common/EmptyState.tsx
import { Box, Typography, Button } from '@mui/material';
import { Inbox as InboxIcon } from '@mui/icons-material';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  message: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({ 
  icon = <InboxIcon />, 
  title, 
  message, 
  action 
}: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 8,
        textAlign: 'center',
      }}
    >
      <Box sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }}>
        {icon}
      </Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 400 }}>
        {message}
      </Typography>
      {action && (
        <Button variant="contained" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </Box>
  );
}
```

3. **Use EmptyState Across Pages**
```tsx
// In ProjectsPage.tsx
{projects.length === 0 && !isLoading && (
  <EmptyState
    title="No Projects Yet"
    message="Create your first migration project to get started with Azure migration validation."
    action={{ label: 'Create Project', onClick: () => setCreateModalOpen(true) }}
  />
)}
```

**Acceptance Criteria**:
- [ ] All async operations show skeleton screens (not just spinners)
- [ ] Empty states have helpful messages and call-to-action buttons
- [ ] Loading states preserve layout (no content shift)

---

## 📋 Summary of Immediate Actions

### This Week (Days 1-7)
**Focus**: Complete critical server management and validation results viewer

1. **Days 1-2**: Server Upload UI
   - Create ServerUploadZone with drag-and-drop
   - Add upload progress tracking
   - Test with sample Excel files

2. **Days 3-4**: Advanced Server Table
   - Implement ServerTable with TanStack Table
   - Add sorting, filtering, pagination
   - Create BulkEditModal

3. **Days 5-6**: Validation Results Viewer
   - Create ValidationJobList component
   - Add export to Excel functionality
   - Integrate filters (status, date)

4. **Day 7**: Testing & Polish
   - Test end-to-end server upload → validation → export workflow
   - Fix UI bugs
   - Add loading states

### Next Week (Days 8-14)
**Focus**: Dashboard and reporting

1. **Days 8-11**: Dashboard Implementation
   - Verify backend `/dashboard/stats` endpoint
   - Implement charts with Recharts
   - Add auto-refresh

2. **Days 12-14**: Reports Page
   - Create ValidationSummaryTab with charts
   - Implement PDF export
   - Create ResourceInventoryTab

---

## 🚀 MVP Readiness Checklist

To consider the UI **MVP complete**, we need:

- [X] Authentication & routing
- [X] Project management (create, edit, list)
- [X] Landing zone configuration upload
- [X] Validation settings editor
- [X] Validation event log display
- [ ] **Server upload with drag-and-drop** ← Task 1
- [ ] **Server table with bulk operations** ← Task 1
- [ ] **Validation results viewer with export** ← Task 2
- [ ] **Dashboard with stats and trends** ← Task 3
- [ ] **Reports with PDF export** ← Task 4
- [ ] Loading states and empty states
- [ ] Responsive design (mobile/tablet)

**Current Progress**: **60%** complete (6/11 critical features)  
**Estimated Time to MVP**: **10-12 working days** (2 weeks)

---

## 🔧 Optional Enhancements (Post-MVP)

These can be deferred to Phase 3 or handled incrementally:

1. ⚪ Real-time WebSocket for live validation updates (replace polling)
2. ⚪ Mobile optimization (bottom navigation, card views)
3. ⚪ Unit tests (Vitest + React Testing Library)
4. ⚪ E2E tests (Playwright)
5. ⚪ Performance optimization (code splitting, lazy loading)
6. ⚪ Remove backend debug logging (cleanup task)
7. ⚪ Azure AD authentication integration
8. ⚪ Multi-language support (i18n)

---

## 📦 Dependencies to Install

As we progress through tasks, install these packages:

```bash
# Week 2 (Server Management)
npm install react-dropzone @tanstack/react-table xlsx file-saver
npm install --save-dev @types/react-dropzone @types/file-saver

# Week 3 (Dashboard & Reports)
npm install recharts jspdf jspdf-autotable
npm install --save-dev @types/recharts @types/jspdf

# Week 4 (WebSocket - if time permits)
npm install socket.io-client
npm install --save-dev @types/socket.io-client

# Testing (Post-MVP)
npm install -D vitest @testing-library/react @testing-library/user-event jsdom
npm install -D @playwright/test
```

---

## 🎯 Success Metrics

We'll know the UI is ready for production when:

1. **Functional Completeness**: All core workflows work end-to-end
   - Upload servers → Configure landing zones → Run validation → View results → Export
   
2. **User Experience**: No major UX issues
   - < 2 second page load times
   - No blank screens (empty states everywhere)
   - Proper error messages (no generic "Something went wrong")
   
3. **Data Integrity**: Backend integration is stable
   - API calls succeed 99%+ of the time
   - Data persists correctly across page refreshes
   - No orphaned records or data loss

4. **Performance**: Acceptable under realistic load
   - Tables with 100+ servers render smoothly
   - Validation logs with 50+ events load quickly
   - Dashboard charts render without lag

---

## 🤝 Next Steps After This Plan

1. **Review this plan** - Confirm priorities and timeline
2. **Start Task 1** - Begin with ServerUploadZone component
3. **Daily progress check** - Track which acceptance criteria are met
4. **Adjust as needed** - If blockers appear, reprioritize tasks

**Ready to proceed?** Let me know if you want to:
- Start with Task 1 (Server Management)
- Adjust priorities
- Add/remove tasks
- Get more detailed implementation guidance for any component
