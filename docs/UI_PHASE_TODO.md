# UI Phase Development Plan

## Overview
This document outlines the complete implementation plan for the Web UI Phase of the Azure Migration Tool Assistant. The UI will provide a modern, user-friendly interface for managing migration projects, uploading server configurations, monitoring validations, and viewing results.

## Technology Stack

### Frontend Framework
- **Primary**: React 18+ with TypeScript
- **Alternative**: Vue 3 with TypeScript
- **Rationale**: Component-based architecture, strong TypeScript support, large ecosystem

### UI Component Library
- **Recommended**: Material-UI (MUI) v5 or Ant Design
- **Features**: Pre-built components, theming, responsive design
- **Icons**: Material Icons or Ant Design Icons

### State Management
- **Global State**: Zustand or Redux Toolkit
- **Server State**: TanStack Query (React Query)
- **Form State**: React Hook Form with Zod validation

### Build Tools
- **Bundler**: Vite (fast HMR, modern tooling)
- **Package Manager**: pnpm (efficient, faster than npm)
- **Linting**: ESLint + Prettier
- **Testing**: Vitest + React Testing Library

### Additional Libraries
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **WebSocket**: Socket.io-client
- **Charts**: Recharts or Apache ECharts
- **Tables**: TanStack Table (React Table v8)
- **Date Handling**: date-fns
- **File Upload**: React Dropzone
- **Excel Export**: SheetJS (xlsx)
- **PDF Generation**: jsPDF or react-pdf

## Project Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── assets/
│   │   ├── images/
│   │   └── styles/
│   │       ├── theme.ts
│   │       └── global.css
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Navbar.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── SearchInput.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Toast.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── dashboard/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── RecentJobs.tsx
│   │   │   └── ValidationChart.tsx
│   │   ├── projects/
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── ProjectForm.tsx
│   │   │   ├── ProjectDetails.tsx
│   │   │   └── DeleteProjectModal.tsx
│   │   ├── landing-zones/
│   │   │   ├── LandingZoneForm.tsx
│   │   │   ├── LandingZoneDetails.tsx
│   │   │   └── LandingZoneStatus.tsx
│   │   ├── servers/
│   │   │   ├── ServerList.tsx
│   │   │   ├── ServerUpload.tsx
│   │   │   ├── ServerTable.tsx
│   │   │   ├── ServerDetails.tsx
│   │   │   └── BulkEditModal.tsx
│   │   ├── validations/
│   │   │   ├── ValidationJobList.tsx
│   │   │   ├── ValidationDetails.tsx
│   │   │   ├── ValidationResults.tsx
│   │   │   ├── RealtimeStatus.tsx
│   │   │   └── ResultsExport.tsx
│   │   └── reports/
│   │       ├── ReportsDashboard.tsx
│   │       ├── ValidationSummary.tsx
│   │       ├── ResourceInventory.tsx
│   │       └── ExportReportModal.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   ├── useValidations.ts
│   │   ├── useWebSocket.ts
│   │   ├── useDebounce.ts
│   │   └── usePagination.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.service.ts
│   │   ├── projects.service.ts
│   │   ├── servers.service.ts
│   │   ├── validations.service.ts
│   │   └── websocket.service.ts
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── projectStore.ts
│   │   └── uiStore.ts
│   ├── types/
│   │   ├── api.types.ts
│   │   ├── project.types.ts
│   │   ├── server.types.ts
│   │   └── validation.types.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   ├── constants.ts
│   │   └── helpers.ts
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ProjectsPage.tsx
│   │   ├── ProjectDetailsPage.tsx
│   │   ├── ServersPage.tsx
│   │   ├── ValidationsPage.tsx
│   │   ├── ReportsPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── App.tsx
│   ├── main.tsx
│   └── router.tsx
├── tests/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   └── utils/
├── .env.example
├── .eslintrc.js
├── .prettierrc
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Phase Implementation Plan

### Week 1: Project Setup & Foundation

#### Day 1-2: Project Initialization
- [ ] Create Vite + React + TypeScript project
  ```bash
  pnpm create vite frontend --template react-ts
  cd frontend
  pnpm install
  ```
- [ ] Install dependencies
  ```bash
  pnpm add react-router-dom @tanstack/react-query axios zustand
  pnpm add @mui/material @emotion/react @emotion/styled @mui/icons-material
  pnpm add react-hook-form zod @hookform/resolvers
  pnpm add date-fns recharts react-dropzone xlsx
  pnpm add socket.io-client
  pnpm add -D @types/node eslint prettier vitest @testing-library/react
  ```
- [ ] Configure ESLint and Prettier
- [ ] Set up folder structure
- [ ] Create .env files (.env.development, .env.production)
  ```env
  VITE_API_BASE_URL=http://localhost:8000
  VITE_WS_URL=ws://localhost:8000
  ```

#### Day 3-4: Base Infrastructure
- [ ] **API Client Setup** (`src/services/api.ts`)
  ```typescript
  import axios from 'axios';
  
  const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 30000,
  });
  
  // Request interceptor for auth token
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  
  // Response interceptor for error handling
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Handle token expiration
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );
  
  export default api;
  ```

- [ ] **Auth Store** (`src/store/authStore.ts`)
  ```typescript
  import { create } from 'zustand';
  import { persist } from 'zustand/middleware';
  
  interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    login: (username: string, password: string) => Promise<void>;
    logout: () => void;
    register: (data: RegisterData) => Promise<void>;
  }
  
  export const useAuthStore = create<AuthState>()(
    persist(
      (set) => ({
        user: null,
        token: null,
        isAuthenticated: false,
        login: async (username, password) => {
          const response = await api.post('/api/v1/auth/token', { username, password });
          const { access_token, user } = response.data;
          localStorage.setItem('access_token', access_token);
          set({ user, token: access_token, isAuthenticated: true });
        },
        logout: () => {
          localStorage.removeItem('access_token');
          set({ user: null, token: null, isAuthenticated: false });
        },
        register: async (data) => {
          await api.post('/api/v1/auth/register', data);
        },
      }),
      { name: 'auth-storage' }
    )
  );
  ```

- [ ] **Router Setup** (`src/router.tsx`)
  ```typescript
  import { createBrowserRouter } from 'react-router-dom';
  import ProtectedRoute from './components/auth/ProtectedRoute';
  import LoginPage from './pages/LoginPage';
  import DashboardPage from './pages/DashboardPage';
  // ... other imports
  
  export const router = createBrowserRouter([
    { path: '/login', element: <LoginPage /> },
    {
      path: '/',
      element: <ProtectedRoute />,
      children: [
        { index: true, element: <DashboardPage /> },
        { path: 'projects', element: <ProjectsPage /> },
        { path: 'projects/:id', element: <ProjectDetailsPage /> },
        { path: 'projects/:id/servers', element: <ServersPage /> },
        { path: 'projects/:id/validations', element: <ValidationsPage /> },
        { path: 'reports', element: <ReportsPage /> },
      ],
    },
    { path: '*', element: <NotFoundPage /> },
  ]);
  ```

- [ ] **Theme Configuration** (`src/assets/styles/theme.ts`)
  ```typescript
  import { createTheme } from '@mui/material/styles';
  
  export const theme = createTheme({
    palette: {
      primary: { main: '#0078D4' }, // Azure blue
      secondary: { main: '#50E6FF' },
      error: { main: '#E81123' },
      warning: { main: '#FFB900' },
      success: { main: '#107C10' },
    },
    typography: {
      fontFamily: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    },
  });
  ```

#### Day 5: Common Components
- [ ] Create reusable components:
  - [ ] **LoadingSpinner** (centered spinner for async operations)
  - [ ] **Card** (container component with elevation)
  - [ ] **Modal** (generic modal wrapper)
  - [ ] **Toast** (notification system using MUI Snackbar)
  - [ ] **Button** (styled button variants)
  - [ ] **SearchInput** (debounced search field)

### Week 2: Authentication & Layout

#### Day 1-2: Authentication UI
- [ ] **LoginForm Component** (`src/components/auth/LoginForm.tsx`)
  ```typescript
  import { useForm } from 'react-hook-form';
  import { zodResolver } from '@hookform/resolvers/zod';
  import { z } from 'zod';
  
  const loginSchema = z.object({
    username: z.string().min(1, 'Username is required'),
    password: z.string().min(1, 'Password is required'),
  });
  
  type LoginFormData = z.infer<typeof loginSchema>;
  
  export function LoginForm() {
    const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
      resolver: zodResolver(loginSchema),
    });
    
    const { login } = useAuthStore();
    const navigate = useNavigate();
    
    const onSubmit = async (data: LoginFormData) => {
      try {
        await login(data.username, data.password);
        navigate('/');
      } catch (error) {
        toast.error('Login failed. Please check your credentials.');
      }
    };
    
    return (
      <form onSubmit={handleSubmit(onSubmit)}>
        <TextField {...register('username')} error={!!errors.username} helperText={errors.username?.message} />
        <TextField {...register('password')} type="password" error={!!errors.password} helperText={errors.password?.message} />
        <Button type="submit">Login</Button>
      </form>
    );
  }
  ```

- [ ] **ProtectedRoute Component**
  ```typescript
  import { Navigate, Outlet } from 'react-router-dom';
  import { useAuthStore } from '../../store/authStore';
  
  export function ProtectedRoute() {
    const { isAuthenticated } = useAuthStore();
    
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />;
    }
    
    return <Outlet />;
  }
  ```

- [ ] **Login Page** with responsive design
- [ ] **Register Form** (optional for self-service)

#### Day 3-5: Application Layout
- [ ] **Navbar Component** (`src/components/common/Navbar.tsx`)
  - Logo and branding
  - User menu with logout
  - Breadcrumbs navigation
  - Notifications icon (future)

- [ ] **Sidebar Component** (`src/components/common/Sidebar.tsx`)
  ```typescript
  import { List, ListItem, ListItemButton, ListItemIcon, ListItemText } from '@mui/material';
  import { Dashboard, Folder, CloudUpload, CheckCircle, Assessment } from '@mui/icons-material';
  
  const menuItems = [
    { path: '/', label: 'Dashboard', icon: <Dashboard /> },
    { path: '/projects', label: 'Projects', icon: <Folder /> },
    { path: '/servers', label: 'Servers', icon: <CloudUpload /> },
    { path: '/validations', label: 'Validations', icon: <CheckCircle /> },
    { path: '/reports', label: 'Reports', icon: <Assessment /> },
  ];
  
  export function Sidebar() {
    const navigate = useNavigate();
    const location = useLocation();
    
    return (
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    );
  }
  ```

- [ ] **Main Layout Component** (combines Navbar + Sidebar + Content area)
- [ ] Responsive design (mobile drawer, desktop persistent sidebar)

### Week 3: Dashboard & Projects

#### Day 1-2: Dashboard Page
- [ ] **Dashboard Component** (`src/components/dashboard/Dashboard.tsx`)
  - Statistics cards (total projects, active validations, success rate)
  - Recent validation jobs table
  - Validation trends chart (line chart showing pass/fail over time)
  - Quick actions (Create Project, Upload Servers, Run Validation)

- [ ] **StatCard Component** (reusable metric display)
  ```typescript
  interface StatCardProps {
    title: string;
    value: number | string;
    icon: React.ReactNode;
    trend?: number; // percentage change
    color?: 'primary' | 'success' | 'error' | 'warning';
  }
  ```

- [ ] **RecentJobs Component** (mini table of latest validations)

- [ ] **ValidationChart Component** (using Recharts)
  ```typescript
  import { LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';
  
  export function ValidationChart({ data }: { data: ChartData[] }) {
    return (
      <LineChart width={600} height={300} data={data}>
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="passed" stroke="#107C10" />
        <Line type="monotone" dataKey="failed" stroke="#E81123" />
      </LineChart>
    );
  }
  ```

#### Day 3-5: Projects Management
- [ ] **ProjectList Component** (`src/components/projects/ProjectList.tsx`)
  - Grid or list view toggle
  - Search and filter (by status, date)
  - Pagination
  - Create new project button

- [ ] **ProjectCard Component**
  ```typescript
  interface ProjectCardProps {
    project: Project;
    onEdit: (id: number) => void;
    onDelete: (id: number) => void;
    onView: (id: number) => void;
  }
  
  export function ProjectCard({ project, onEdit, onDelete, onView }: ProjectCardProps) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6">{project.name}</Typography>
          <Typography color="text.secondary">{project.description}</Typography>
          <Box mt={2}>
            <Chip label={`${project.server_count} servers`} size="small" />
            <Chip label={project.is_active ? 'Active' : 'Inactive'} color={project.is_active ? 'success' : 'default'} size="small" />
          </Box>
        </CardContent>
        <CardActions>
          <Button size="small" onClick={() => onView(project.id)}>View</Button>
          <Button size="small" onClick={() => onEdit(project.id)}>Edit</Button>
          <Button size="small" color="error" onClick={() => onDelete(project.id)}>Delete</Button>
        </CardActions>
      </Card>
    );
  }
  ```

- [ ] **ProjectForm Component** (create/edit modal)
  ```typescript
  const projectSchema = z.object({
    name: z.string().min(3, 'Name must be at least 3 characters'),
    description: z.string().optional(),
    azure_subscription_id: z.string().uuid('Invalid subscription ID'),
  });
  
  type ProjectFormData = z.infer<typeof projectSchema>;
  ```

- [ ] **DeleteProjectModal** (confirmation dialog)

- [ ] **Projects Service** (`src/services/projects.service.ts`)
  ```typescript
  export const projectsService = {
    getAll: (params?: { page?: number; limit?: number; search?: string }) =>
      api.get('/api/v1/projects', { params }),
    
    getById: (id: number) =>
      api.get(`/api/v1/projects/${id}`),
    
    create: (data: ProjectCreate) =>
      api.post('/api/v1/projects', data),
    
    update: (id: number, data: ProjectUpdate) =>
      api.put(`/api/v1/projects/${id}`, data),
    
    delete: (id: number) =>
      api.delete(`/api/v1/projects/${id}`),
  };
  ```

### Week 4: Landing Zones & Server Upload

#### Day 1-2: Landing Zone Configuration
- [ ] **LandingZoneForm Component** (`src/components/landing-zones/LandingZoneForm.tsx`)
  - Form fields for all landing zone properties:
    - Migrate project details (name, RG, subscription)
    - Recovery vault details (name, RG, subscription)
    - Cache storage (account name, RG)
    - Appliance name
  - Form validation with Zod
  - Auto-save draft (localStorage)

- [ ] **LandingZoneDetails Component** (read-only view)
  - Display configured landing zone
  - Edit button
  - Status indicator (configured/not configured)

- [ ] **Landing Zone Service** (`src/services/landingZones.service.ts`)

#### Day 3-5: Server Upload
- [ ] **ServerUpload Component** (`src/components/servers/ServerUpload.tsx`)
  ```typescript
  import { useDropzone } from 'react-dropzone';
  
  export function ServerUpload({ projectId }: { projectId: number }) {
    const [uploadProgress, setUploadProgress] = useState(0);
    
    const onDrop = async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const response = await api.post(
          `/api/v1/projects/${projectId}/servers/upload`,
          formData,
          {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
              const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total!);
              setUploadProgress(percent);
            },
          }
        );
        
        toast.success(`Uploaded ${response.data.servers_created} servers`);
      } catch (error) {
        toast.error('Upload failed');
      }
    };
    
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      onDrop,
      accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
      maxFiles: 1,
    });
    
    return (
      <Box {...getRootProps()} sx={{ border: '2px dashed', p: 4, textAlign: 'center' }}>
        <input {...getInputProps()} />
        {isDragActive ? (
          <Typography>Drop the Excel file here...</Typography>
        ) : (
          <Typography>Drag and drop an Excel file, or click to select</Typography>
        )}
        {uploadProgress > 0 && <LinearProgress variant="determinate" value={uploadProgress} />}
      </Box>
    );
  }
  ```

- [ ] **ServerTable Component** (display uploaded servers)
  - Sortable columns
  - Filter by region, SKU, disk type
  - Bulk edit functionality
  - Export to Excel
  - Delete servers

- [ ] **ServerDetails Component** (edit single server)

- [ ] **BulkEditModal Component** (update multiple servers at once)

- [ ] **Servers Service** (`src/services/servers.service.ts`)

### Week 5: Validation Monitoring

#### Day 1-2: Validation Jobs List
- [ ] **ValidationJobList Component** (`src/components/validations/ValidationJobList.tsx`)
  - Table of all validation jobs
  - Filters: status, date range, project
  - Status badges (pending, running, completed, failed)
  - View details button
  - Trigger new validation button

- [ ] **Trigger Validation Modal**
  - Confirm validation parameters
  - Start validation job

- [ ] **Validations Service** (`src/services/validations.service.ts`)
  ```typescript
  export const validationsService = {
    getJobs: (projectId: number, params?: PaginationParams) =>
      api.get(`/api/v1/projects/${projectId}/validations`, { params }),
    
    getJobDetails: (jobId: number) =>
      api.get(`/api/v1/validations/${jobId}`),
    
    triggerValidation: (projectId: number) =>
      api.post(`/api/v1/projects/${projectId}/validations/trigger`),
    
    getResults: (jobId: number, params?: { stage?: string; passed?: boolean }) =>
      api.get(`/api/v1/validations/${jobId}/results`, { params }),
  };
  ```

#### Day 3-5: Real-Time Status & Results
- [ ] **WebSocket Hook** (`src/hooks/useWebSocket.ts`)
  ```typescript
  import { useEffect, useState } from 'react';
  import io from 'socket.io-client';
  
  export function useWebSocket(jobId: number) {
    const [status, setStatus] = useState<JobStatus | null>(null);
    const [socket, setSocket] = useState<any>(null);
    
    useEffect(() => {
      const ws = io(import.meta.env.VITE_WS_URL);
      
      ws.on('connect', () => {
        ws.emit('subscribe', { jobId });
      });
      
      ws.on('job_status', (data: JobStatus) => {
        setStatus(data);
      });
      
      setSocket(ws);
      
      return () => {
        ws.disconnect();
      };
    }, [jobId]);
    
    return { status, socket };
  }
  ```

- [ ] **RealtimeStatus Component** (`src/components/validations/RealtimeStatus.tsx`)
  ```typescript
  export function RealtimeStatus({ jobId }: { jobId: number }) {
    const { status } = useWebSocket(jobId);
    
    if (!status) return <LoadingSpinner />;
    
    return (
      <Card>
        <CardContent>
          <Typography variant="h6">Validation Progress</Typography>
          <LinearProgress
            variant="determinate"
            value={status.progress}
            color={status.status === 'failed' ? 'error' : 'primary'}
          />
          <Typography variant="body2" mt={1}>
            {status.message}
          </Typography>
          <Box mt={2}>
            <Chip label={status.status} color={getStatusColor(status.status)} />
            <Typography variant="caption" ml={2}>
              {status.progress}% complete
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }
  ```

- [ ] **ValidationResults Component** (`src/components/validations/ValidationResults.tsx`)
  - Filterable table (by validation stage, passed/failed)
  - Expandable rows for error details
  - Export results to CSV/Excel
  - Summary statistics (pass rate per stage)

- [ ] **ResultsExport Component**
  ```typescript
  import * as XLSX from 'xlsx';
  
  export function ResultsExport({ results }: { results: ValidationResult[] }) {
    const exportToExcel = () => {
      const worksheet = XLSX.utils.json_to_sheet(results);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Validation Results');
      XLSX.writeFile(workbook, `validation-results-${Date.now()}.xlsx`);
    };
    
    return (
      <Button startIcon={<Download />} onClick={exportToExcel}>
        Export to Excel
      </Button>
    );
  }
  ```

### Week 6: Reports & Analytics

#### Day 1-3: Reports Dashboard
- [ ] **ReportsDashboard Component** (`src/pages/ReportsPage.tsx`)
  - Date range selector
  - Project filter
  - Report type tabs (Summary, Inventory, Trends)

- [ ] **ValidationSummary Component**
  - Overall success rate chart (pie chart)
  - Stage-by-stage breakdown (bar chart)
  - Top 10 validation failures (horizontal bar chart)
  - Time-series trend (line chart)

- [ ] **ResourceInventory Component**
  - Servers by region (bar chart)
  - Servers by SKU (pie chart)
  - Disk type distribution (doughnut chart)
  - Table view with counts

- [ ] **Charts using Recharts**
  ```typescript
  import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
  
  export function ValidationSuccessChart({ data }: { data: ChartData }) {
    const chartData = [
      { name: 'Passed', value: data.passed },
      { name: 'Failed', value: data.failed },
    ];
    
    const COLORS = ['#107C10', '#E81123'];
    
    return (
      <PieChart width={400} height={400}>
        <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    );
  }
  ```

#### Day 4-5: Report Export
- [ ] **PDF Export** (using jsPDF)
  ```typescript
  import jsPDF from 'jspdf';
  import autoTable from 'jspdf-autotable';
  
  export function exportPDFReport(project: Project, data: ReportData) {
    const doc = new jsPDF();
    
    // Header
    doc.setFontSize(18);
    doc.text('Azure Migration Validation Report', 14, 22);
    doc.setFontSize(11);
    doc.text(`Project: ${project.name}`, 14, 30);
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 36);
    
    // Summary table
    autoTable(doc, {
      head: [['Metric', 'Value']],
      body: [
        ['Total Servers', data.totalServers],
        ['Validations Run', data.validationsRun],
        ['Success Rate', `${data.successRate}%`],
      ],
      startY: 45,
    });
    
    // Stage breakdown
    autoTable(doc, {
      head: [['Stage', 'Total', 'Passed', 'Failed', 'Pass Rate']],
      body: data.stages.map(s => [s.name, s.total, s.passed, s.failed, `${s.passRate}%`]),
      startY: (doc as any).lastAutoTable.finalY + 10,
    });
    
    doc.save(`report-${project.id}-${Date.now()}.pdf`);
  }
  ```

- [ ] **CSV Export** (using Papaparse or manual implementation)
- [ ] **Schedule Report Modal** (future: schedule recurring reports via email)

### Week 7: Polish & Testing

#### Day 1-2: UX Improvements
- [ ] Loading states for all async operations
- [ ] Error boundaries for component error handling
- [ ] Empty states (no projects, no servers, no validations)
- [ ] Confirmation dialogs for destructive actions
- [ ] Toast notifications for all user actions
- [ ] Keyboard shortcuts (e.g., Ctrl+K for search)
- [ ] Tooltips for complex fields

#### Day 3-4: Responsive Design
- [ ] Mobile layout testing (breakpoints: xs, sm, md, lg, xl)
- [ ] Touch-friendly UI elements
- [ ] Hamburger menu for mobile navigation
- [ ] Responsive tables (horizontal scroll or cards on mobile)
- [ ] Mobile-friendly forms (stacked layout)

#### Day 5: Testing
- [ ] **Unit Tests** (Vitest + React Testing Library)
  ```typescript
  // tests/components/ProjectCard.test.tsx
  import { render, screen, fireEvent } from '@testing-library/react';
  import { ProjectCard } from '../../src/components/projects/ProjectCard';
  
  describe('ProjectCard', () => {
    it('renders project name and description', () => {
      const project = { id: 1, name: 'Test Project', description: 'Test description' };
      render(<ProjectCard project={project} onEdit={() => {}} onDelete={() => {}} onView={() => {}} />);
      
      expect(screen.getByText('Test Project')).toBeInTheDocument();
      expect(screen.getByText('Test description')).toBeInTheDocument();
    });
    
    it('calls onDelete when delete button clicked', () => {
      const onDelete = vi.fn();
      const project = { id: 1, name: 'Test Project' };
      render(<ProjectCard project={project} onEdit={() => {}} onDelete={onDelete} onView={() => {}} />);
      
      fireEvent.click(screen.getByText('Delete'));
      expect(onDelete).toHaveBeenCalledWith(1);
    });
  });
  ```

- [ ] **Integration Tests** (test full workflows)
  - Login → Create Project → Upload Servers → Trigger Validation
  - View Results → Export Report

- [ ] **E2E Tests** (Playwright or Cypress)
  ```typescript
  // e2e/validation-workflow.spec.ts
  import { test, expect } from '@playwright/test';
  
  test('complete validation workflow', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    
    // Login
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Create project
    await page.click('text=Projects');
    await page.click('text=Create Project');
    await page.fill('input[name="name"]', 'E2E Test Project');
    await page.fill('input[name="azure_subscription_id"]', '12345678-1234-1234-1234-123456789012');
    await page.click('text=Create');
    
    // Upload servers
    await page.click('text=E2E Test Project');
    await page.click('text=Upload Servers');
    await page.setInputFiles('input[type="file"]', 'tests/fixtures/servers.xlsx');
    await expect(page.locator('text=Uploaded 3 servers')).toBeVisible();
    
    // Trigger validation
    await page.click('text=Trigger Validation');
    await page.click('text=Confirm');
    await expect(page.locator('text=Validation started')).toBeVisible();
  });
  ```

### Week 8: Deployment & Documentation

#### Day 1-2: Build & Optimization
- [ ] Production build optimization
  ```typescript
  // vite.config.ts
  export default defineConfig({
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui-vendor': ['@mui/material', '@emotion/react'],
            'charts-vendor': ['recharts'],
          },
        },
      },
    },
  });
  ```

- [ ] Code splitting for lazy loading
  ```typescript
  const DashboardPage = lazy(() => import('./pages/DashboardPage'));
  const ProjectsPage = lazy(() => import('./pages/ProjectsPage'));
  
  <Suspense fallback={<LoadingSpinner />}>
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/projects" element={<ProjectsPage />} />
    </Routes>
  </Suspense>
  ```

- [ ] Image optimization (compress assets)
- [ ] Bundle size analysis
  ```bash
  pnpm add -D rollup-plugin-visualizer
  pnpm build
  # Check dist/stats.html
  ```

#### Day 3: Docker Containerization
- [ ] **Dockerfile**
  ```dockerfile
  # Build stage
  FROM node:18-alpine AS builder
  WORKDIR /app
  COPY package.json pnpm-lock.yaml ./
  RUN npm install -g pnpm && pnpm install --frozen-lockfile
  COPY . .
  RUN pnpm build
  
  # Production stage
  FROM nginx:alpine
  COPY --from=builder /app/dist /usr/share/nginx/html
  COPY nginx.conf /etc/nginx/conf.d/default.conf
  EXPOSE 80
  CMD ["nginx", "-g", "daemon off;"]
  ```

- [ ] **nginx.conf**
  ```nginx
  server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
      try_files $uri $uri/ /index.html;
    }
    
    location /api {
      proxy_pass http://api:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
      proxy_pass http://api:8000;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
    }
  }
  ```

- [ ] **Update docker-compose.yml**
  ```yaml
  services:
    frontend:
      build: ./frontend
      ports:
        - "80:80"
      depends_on:
        - api
      environment:
        - VITE_API_BASE_URL=http://localhost:8000
  ```

#### Day 4-5: Documentation
- [ ] **README.md** for frontend
  ```markdown
  # Azure Migration Tool - Frontend
  
  ## Quick Start
  ```bash
  pnpm install
  pnpm dev
  ```
  
  ## Build
  ```bash
  pnpm build
  pnpm preview
  ```
  
  ## Environment Variables
  - `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:8000)
  - `VITE_WS_URL`: WebSocket URL (default: ws://localhost:8000)
  
  ## Project Structure
  - `src/components`: Reusable UI components
  - `src/pages`: Page-level components
  - `src/services`: API service layer
  - `src/store`: Global state management
  - `src/hooks`: Custom React hooks
  ```

- [ ] **Component Documentation** (Storybook - optional)
  ```bash
  pnpm add -D @storybook/react @storybook/addon-essentials
  ```

- [ ] **User Guide** (screenshots and walkthroughs)
  - How to create a project
  - How to upload servers
  - How to interpret validation results
  - How to generate reports

- [ ] **API Integration Guide** (for developers)

## Feature Checklist

### Core Features
- [ ] User authentication (login, logout, token refresh)
- [ ] Dashboard with statistics and charts
- [ ] Project CRUD operations
- [ ] Landing zone configuration
- [ ] Server bulk upload (Excel)
- [ ] Server list with filtering and sorting
- [ ] Validation job management
- [ ] Real-time validation status (WebSocket)
- [ ] Validation results viewer
- [ ] Export results (Excel, CSV)
- [ ] Reports and analytics
- [ ] PDF report generation

### UX Features
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Dark mode toggle (optional)
- [ ] Loading states and skeleton screens
- [ ] Error handling with user-friendly messages
- [ ] Toast notifications
- [ ] Confirmation dialogs
- [ ] Empty states
- [ ] Search and filters
- [ ] Pagination
- [ ] Breadcrumb navigation
- [ ] Keyboard shortcuts

### Advanced Features (Phase 3+)
- [ ] Multi-tenancy support (organizations/teams)
- [ ] User role management
- [ ] Audit log viewer
- [ ] Custom validation rules UI
- [ ] Scheduled validation management
- [ ] Webhook configuration
- [ ] Replication management UI
- [ ] Cost estimation calculator
- [ ] Drag-and-drop server ordering
- [ ] Bulk server editing
- [ ] Server tagging system
- [ ] Saved filters/views
- [ ] Collaborative features (comments, approvals)

## Performance Targets

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Lighthouse Score**: > 90
- **Bundle Size**: < 500KB (gzipped)
- **API Response Handling**: Show loading state within 100ms
- **Real-time Updates**: WebSocket message latency < 500ms

## Accessibility (a11y)

- [ ] WCAG 2.1 Level AA compliance
- [ ] Keyboard navigation support
- [ ] Screen reader compatibility (ARIA labels)
- [ ] Focus indicators
- [ ] Sufficient color contrast (4.5:1 minimum)
- [ ] Alt text for images
- [ ] Form labels and error messages

## Security Considerations

- [ ] XSS prevention (sanitize user inputs)
- [ ] CSRF protection (handled by backend)
- [ ] Secure token storage (httpOnly cookies or secure localStorage)
- [ ] Content Security Policy headers
- [ ] HTTPS enforcement in production
- [ ] API request authentication
- [ ] Rate limiting (handled by backend)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Testing Strategy

### Unit Tests (Vitest)
- Component rendering
- User interactions (click, input)
- Form validation
- Utility functions
- Custom hooks

### Integration Tests
- Multi-component workflows
- API integration
- State management
- Routing

### E2E Tests (Playwright)
- Critical user flows
- Cross-browser testing
- Mobile responsive testing

### Coverage Target: > 80%

## Deployment Options

### Option 1: Docker + Nginx (Recommended)
- Build static files
- Serve with Nginx
- Deploy to Azure Container Instances or Kubernetes

### Option 2: Static Hosting
- Build static files (`pnpm build`)
- Deploy to Azure Static Web Apps, Netlify, or Vercel
- Configure API proxy

### Option 3: Azure Storage Static Website
- Upload build artifacts to Azure Blob Storage
- Enable static website hosting
- Configure CDN

## Monitoring & Analytics (Optional)

- [ ] Application Insights integration
- [ ] Google Analytics
- [ ] Sentry for error tracking
- [ ] User behavior analytics (Hotjar, FullStory)

## Future Enhancements

- Progressive Web App (PWA) support
- Offline mode with service workers
- Push notifications
- Real-time collaboration (multiple users editing simultaneously)
- Advanced charting (custom date ranges, drill-down)
- CSV/JSON import for server configs
- Template library for common migrations
- AI-powered migration recommendations
- Integration with Azure DevOps (show pipeline status)
- Chatbot assistant for help

---

## Getting Started

1. **Install dependencies**:
   ```bash
   cd frontend
   pnpm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env.development
   # Edit .env.development with your API URL
   ```

3. **Start development server**:
   ```bash
   pnpm dev
   # Open http://localhost:5173
   ```

4. **Run tests**:
   ```bash
   pnpm test
   pnpm test:ui  # Open Vitest UI
   ```

5. **Build for production**:
   ```bash
   pnpm build
   pnpm preview  # Preview production build
   ```

## Questions & Support

For questions or issues, please refer to:
- Main project README.md
- API documentation at http://localhost:8000/docs
- User guide in docs/USER_GUIDE.md

---

**Last Updated**: October 31, 2025
**Status**: Ready for Implementation
**Estimated Duration**: 8 weeks (1 developer)
