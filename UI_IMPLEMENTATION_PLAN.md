# UI Implementation Plan - Prioritized Roadmap

## Current Status ✅

### Completed Features
1. **Core Infrastructure** (Week 1 - 100% Complete)
   - ✅ Vite + React 18 + TypeScript setup
   - ✅ Material-UI v5 theming (Azure blue palette)
   - ✅ Zustand state management (auth, UI stores)
   - ✅ Axios API client with JWT interceptors
   - ✅ React Router v6 with protected routes
   - ✅ All service layer implementations (projects, servers, validations)
   - ✅ TypeScript type definitions (100% coverage)

2. **Layout & Navigation**
   - ✅ MainLayout with responsive Navbar + Sidebar
   - ✅ Mobile drawer + desktop persistent sidebar
   - ✅ Route guards (ProtectedRoute, PublicRoute)
   - ✅ Common components (LoadingSpinner, Toast, Modal, ConfirmDialog)

3. **Authentication**
   - ✅ LoginPage with form validation
   - ✅ JWT token management
   - ✅ Auto-logout on 401 errors

4. **Project Management** (Partially Complete)
   - ✅ ProjectsPage with search and create
   - ✅ ProjectDetailsPage with 5 tabs (Overview, Landing Zones, Azure Auth, Servers, Validations)
   - ✅ MigrateProjectFormModal for landing zone configuration
   - ✅ AppLandingZoneModal for app landing zones
   - ✅ ValidationSettingsEditor for validation config
   - ⚠️ **3 TODOs remaining** (edit modal, validation logic, landing zone data fetch)

5. **Validation Features**
   - ✅ ValidationEventLog component (hierarchical job/event display)
   - ✅ Azure Activity Log-style UI with accordions
   - ✅ Auto-refresh for running jobs
   - ✅ All validation status bugs fixed (status mapping, cache storage subscription)

### In-Progress / Incomplete Features
- ⏳ **ServersPage**: Search exists, but missing upload UI and table features
- ⏳ **ValidationsPage**: Basic structure, needs results viewer
- ⏳ **DashboardPage**: Placeholder only
- ⏳ **ReportsPage**: Placeholder only
- ⏳ **LandingZonesPage**: Basic list, needs enhancement

---

## Priority 1: Critical User Flows (Next 2 Weeks)

### Week 2: Server Management & Validation Results

#### 🎯 Task 1: Complete Server Upload & Management UI
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 3-4 days  
**Complexity**: Medium  

**Subtasks**:
1. **Drag-and-Drop Excel Upload** (`ServersPage.tsx`)
   ```tsx
   import { useDropzone } from 'react-dropzone';
   
   const onDrop = async (files: File[]) => {
     const formData = new FormData();
     formData.append('file', files[0]);
     
     try {
       const response = await serversService.uploadBulk(projectId, formData, {
         onUploadProgress: (e) => setProgress(Math.round((e.loaded * 100) / e.total))
       });
       toast.success(`Uploaded ${response.data.servers_created} servers`);
     } catch (error) {
       toast.error('Upload failed');
     }
   };
   ```

2. **Server Data Table with TanStack Table**
   - Sortable columns (Machine Name, Region, SKU, Disk Type, Status)
   - Multi-column filtering
   - Pagination controls (10/25/50/100 per page)
   - Row selection for bulk operations
   - Export to Excel button

3. **Bulk Edit Modal**
   - Select multiple servers via checkboxes
   - Update common fields (Region, RG, VNet, Subnet, SKU, Disk Type)
   - Validation before saving
   - Optimistic UI updates

**Files to Create/Modify**:
- `frontend/src/pages/ServersPage.tsx` (enhance existing)
- `frontend/src/components/servers/ServerUploadZone.tsx` (new)
- `frontend/src/components/servers/ServerTable.tsx` (new)
- `frontend/src/components/servers/BulkEditModal.tsx` (new)
- `frontend/src/components/servers/ServerDetailsModal.tsx` (new)

**Dependencies**:
```bash
npm install @tanstack/react-table @tanstack/react-table-devtools
```

**Acceptance Criteria**:
- [ ] User can drag-and-drop Excel file with live progress bar
- [ ] Server table displays all uploaded servers with sorting/filtering
- [ ] Bulk edit updates multiple servers at once
- [ ] Export downloads current filtered results as Excel
- [ ] Error handling shows validation issues from backend

---

#### 🎯 Task 2: Build Validation Results Viewer with Export
**Priority**: 🔴 CRITICAL  
**Estimated Time**: 2-3 days  
**Complexity**: Low-Medium  

**Subtasks**:
1. **ValidationJobList Component**
   - Table of all validation jobs for project
   - Status badges (PENDING, RUNNING, COMPLETED, FAILED)
   - Filters: status, date range
   - "View Results" button → opens ValidationEventLog
   - "Trigger Validation" button → starts new job

2. **Enhanced ValidationEventLog** (already exists, needs tweaks)
   - Add stage filter dropdown (All, Access, Appliance, Storage, Quota)
   - Add pass/fail filter (All, Passed, Failed)
   - Add "Export Results" button

3. **Results Export Functionality**
   ```tsx
   import * as XLSX from 'xlsx';
   
   const exportToExcel = (events: ValidationEvent[]) => {
     const worksheet = XLSX.utils.json_to_sheet(events.map(e => ({
       Stage: e.stage,
       Status: e.status,
       Message: e.message,
       Duration: e.duration_ms + 'ms',
       Timestamp: new Date(e.event_timestamp).toLocaleString()
     })));
     
     const workbook = XLSX.utils.book_new();
     XLSX.utils.book_append_sheet(workbook, worksheet, 'Results');
     XLSX.writeFile(workbook, `validation-results-${jobId}.xlsx`);
   };
   ```

**Files to Create/Modify**:
- `frontend/src/pages/ValidationsPage.tsx` (enhance existing)
- `frontend/src/components/validations/ValidationJobList.tsx` (new)
- `frontend/src/components/validations/ValidationEventLog.tsx` (add export button)
- `frontend/src/components/validations/TriggerValidationModal.tsx` (new)

**Acceptance Criteria**:
- [ ] ValidationJobList shows all jobs with status and timestamp
- [ ] Clicking job row expands ValidationEventLog
- [ ] Export button downloads Excel with all events
- [ ] Stage/status filters work correctly
- [ ] "Trigger Validation" starts new job and updates UI

---

### Week 3: Dashboard & Reporting

#### 🎯 Task 3: Implement Dashboard with Charts & Statistics
**Priority**: 🟡 HIGH  
**Estimated Time**: 3-4 days  
**Complexity**: Medium  

**Subtasks**:
1. **Stat Cards Row** (top of dashboard)
   ```tsx
   <Grid container spacing={3}>
     <StatCard 
       title="Total Projects" 
       value={stats.total_projects} 
       icon={<FolderIcon />} 
       trend={+12} 
       color="primary" 
     />
     <StatCard 
       title="Active Validations" 
       value={stats.active_validations} 
       icon={<PlayArrowIcon />} 
       color="success" 
     />
     <StatCard 
       title="Success Rate" 
       value={`${stats.success_rate}%`} 
       icon={<CheckCircleIcon />} 
       color={stats.success_rate > 80 ? 'success' : 'warning'} 
     />
     <StatCard 
       title="Total Servers" 
       value={stats.total_servers} 
       icon={<StorageIcon />} 
       color="info" 
     />
   </Grid>
   ```

2. **Recent Validation Jobs Table**
   - Last 10 validation jobs across all projects
   - Columns: Project Name, Job ID, Status, Started, Duration
   - "View All" link → navigates to ValidationsPage

3. **Validation Trend Chart** (Recharts)
   - Line chart: Pass vs Fail count over last 30 days
   - X-axis: Date
   - Y-axis: Validation count
   - Two lines: Passed (green), Failed (red)

**Files to Create/Modify**:
- `frontend/src/pages/DashboardPage.tsx` (replace placeholder)
- `frontend/src/components/dashboard/StatCard.tsx` (new)
- `frontend/src/components/dashboard/RecentJobsTable.tsx` (new)
- `frontend/src/components/dashboard/ValidationTrendChart.tsx` (new)

**API Endpoints Needed**:
```typescript
// New endpoint to add to backend
GET /api/v1/dashboard/stats
Response: {
  total_projects: number,
  active_validations: number,
  success_rate: number,
  total_servers: number,
  recent_jobs: Job[],
  trend_data: { date: string, passed: number, failed: number }[]
}
```

**Acceptance Criteria**:
- [ ] Four stat cards display correct aggregated data
- [ ] Recent jobs table shows last 10 validations
- [ ] Trend chart visualizes pass/fail over time
- [ ] All data auto-refreshes every 30 seconds

---

#### 🎯 Task 4: Create Reports & Analytics Module
**Priority**: 🟡 HIGH  
**Estimated Time**: 3-4 days  
**Complexity**: High  

**Subtasks**:
1. **Report Type Tabs**
   - Validation Summary
   - Resource Inventory
   - Compliance Report (custom rules - future)

2. **Validation Summary Tab**
   - Pie chart: Overall pass/fail ratio
   - Bar chart: Pass rate per validation stage
   - Table: Top 10 most common failures
   - Date range selector (last 7/30/90 days, custom)

3. **Resource Inventory Tab**
   - Bar chart: Server count by region
   - Pie chart: Server count by VM SKU
   - Doughnut chart: Disk type distribution
   - Data table with totals

4. **PDF Export**
   ```tsx
   import jsPDF from 'jspdf';
   import autoTable from 'jspdf-autotable';
   
   const exportPDF = (reportData: ReportData, projectName: string) => {
     const doc = new jsPDF();
     
     // Header
     doc.setFontSize(18);
     doc.text('Azure Migration Validation Report', 14, 22);
     doc.setFontSize(11);
     doc.text(`Project: ${projectName}`, 14, 30);
     doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 36);
     
     // Summary stats table
     autoTable(doc, {
       head: [['Metric', 'Value']],
       body: [
         ['Total Validations', reportData.total_validations],
         ['Success Rate', `${reportData.success_rate}%`],
         ['Total Servers', reportData.total_servers],
       ],
       startY: 45,
     });
     
     // Stage breakdown table
     autoTable(doc, {
       head: [['Stage', 'Total', 'Passed', 'Failed', 'Pass Rate']],
       body: reportData.stages.map(s => [
         s.name, s.total, s.passed, s.failed, `${s.pass_rate}%`
       ]),
       startY: (doc as any).lastAutoTable.finalY + 10,
     });
     
     doc.save(`report-${projectName}-${Date.now()}.pdf`);
   };
   ```

**Files to Create/Modify**:
- `frontend/src/pages/ReportsPage.tsx` (replace placeholder)
- `frontend/src/components/reports/ValidationSummaryTab.tsx` (new)
- `frontend/src/components/reports/ResourceInventoryTab.tsx` (new)
- `frontend/src/components/reports/ExportReportButton.tsx` (new)

**Dependencies**:
```bash
npm install jspdf jspdf-autotable
npm install --save-dev @types/jspdf
```

**Acceptance Criteria**:
- [ ] Date range selector filters report data
- [ ] Charts display correct aggregated data
- [ ] PDF export generates comprehensive report
- [ ] Excel export works for all report tables

---

## Priority 2: Enhanced UX & Polish (Next 1-2 Weeks)

### Week 4: Real-Time Features & UX Improvements

#### 🎯 Task 5: Add Real-Time WebSocket Status Updates
**Priority**: 🟢 MEDIUM  
**Estimated Time**: 2-3 days  
**Complexity**: Medium  

**Subtasks**:
1. **useWebSocket Custom Hook**
   ```tsx
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
       
       return () => ws.disconnect();
     }, [jobId]);
     
     return { status, socket };
   }
   ```

2. **Replace Polling in ValidationEventLog**
   - Remove `setInterval` auto-refresh
   - Use `useWebSocket(jobId)` hook
   - Update UI immediately on WebSocket message
   - Show live progress percentage

**Backend Task** (required first):
```python
# api/websocket.py - Implement WebSocket endpoint
from fastapi import WebSocket

@app.websocket("/ws/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: int):
    await manager.connect(websocket, job_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
```

**Files to Create/Modify**:
- `frontend/src/hooks/useWebSocket.ts` (new)
- `frontend/src/components/validations/ValidationEventLog.tsx` (replace polling)
- `api/websocket.py` (new backend file)

**Acceptance Criteria**:
- [ ] WebSocket connects when validation job starts
- [ ] Progress updates appear in real-time (no refresh needed)
- [ ] Connection auto-reconnects on disconnect
- [ ] Multiple users can watch same job simultaneously

---

#### 🎯 Task 6: Improve UX with Loading States & Empty States
**Priority**: 🟢 MEDIUM  
**Estimated Time**: 2 days  
**Complexity**: Low  

**Subtasks**:
1. **Skeleton Screens for Async Data**
   ```tsx
   import { Skeleton } from '@mui/material';
   
   {isLoading ? (
     <Stack spacing={2}>
       <Skeleton variant="rectangular" height={60} />
       <Skeleton variant="rectangular" height={60} />
       <Skeleton variant="rectangular" height={60} />
     </Stack>
   ) : (
     <DataTable data={projects} />
   )}
   ```

2. **Empty State Illustrations**
   - No projects: "Create your first migration project"
   - No servers: "Upload server configurations to begin"
   - No validations: "Run your first validation"
   - Use Material Icons + centered text

3. **Enhanced Toast Notifications**
   - Success: Green with checkmark icon
   - Error: Red with error icon, show error details
   - Warning: Yellow with warning icon
   - Info: Blue with info icon
   - Auto-dismiss after 5 seconds (error: 10 seconds)

**Files to Modify**:
- `frontend/src/pages/ProjectsPage.tsx` (add empty state)
- `frontend/src/pages/ServersPage.tsx` (add empty state + skeleton)
- `frontend/src/pages/ValidationsPage.tsx` (add empty state)
- `frontend/src/components/common/Toast.tsx` (enhance styling)
- `frontend/src/components/common/EmptyState.tsx` (new reusable component)

**Acceptance Criteria**:
- [ ] All async operations show skeleton screens while loading
- [ ] Empty states display helpful messages and CTAs
- [ ] Toasts appear with correct icons and colors
- [ ] Destructive actions show confirmation dialogs

---

#### 🎯 Task 7: Implement Responsive Design & Mobile Optimization
**Priority**: 🟢 MEDIUM  
**Estimated Time**: 2-3 days  
**Complexity**: Medium  

**Subtasks**:
1. **Test All Breakpoints**
   - xs (mobile): < 600px
   - sm (tablet): 600-900px
   - md (small laptop): 900-1200px
   - lg (desktop): 1200-1536px
   - xl (large desktop): > 1536px

2. **Mobile-Optimized Tables**
   - Horizontal scroll on mobile
   - Card view option for mobile (instead of table)
   - Touch-friendly row selection

3. **Form Layout Adjustments**
   - Stack form fields vertically on mobile
   - Larger touch targets (min 44px)
   - Mobile-friendly date pickers

4. **Navigation Enhancements**
   - Hamburger menu already works (Sidebar drawer)
   - Add bottom navigation bar for mobile (optional)
   - Breadcrumbs collapse on small screens

**Files to Modify**:
- `frontend/src/components/servers/ServerTable.tsx` (responsive table)
- `frontend/src/components/projects/ProjectFormModal.tsx` (mobile form layout)
- `frontend/src/components/layout/Navbar.tsx` (responsive breadcrumbs)

**Acceptance Criteria**:
- [ ] All pages usable on mobile (iPhone/Android)
- [ ] Tables scroll horizontally or switch to card view
- [ ] Forms stack vertically on small screens
- [ ] Touch targets are at least 44x44px

---

## Priority 3: Testing & Optimization (Next 1-2 Weeks)

### Week 5: Testing, Performance, & Documentation

#### 🎯 Task 8: Add Unit & Integration Tests
**Priority**: 🟡 HIGH (for production)  
**Estimated Time**: 3-4 days  
**Complexity**: Medium  

**Subtasks**:
1. **Component Tests (Vitest + React Testing Library)**
   ```tsx
   // tests/components/StatCard.test.tsx
   import { render, screen } from '@testing-library/react';
   import { StatCard } from '../../src/components/dashboard/StatCard';
   
   describe('StatCard', () => {
     it('renders title and value', () => {
       render(<StatCard title="Total Projects" value={42} icon={<div />} />);
       expect(screen.getByText('Total Projects')).toBeInTheDocument();
       expect(screen.getByText('42')).toBeInTheDocument();
     });
     
     it('shows positive trend in green', () => {
       const { container } = render(<StatCard title="Test" value={10} trend={15} />);
       expect(container.querySelector('.trend-up')).toHaveStyle('color: green');
     });
   });
   ```

2. **Service Tests (Mock Axios)**
   ```tsx
   // tests/services/projects.service.test.ts
   import { vi } from 'vitest';
   import api from '../../src/services/api';
   import { projectsService } from '../../src/services/projects.service';
   
   vi.mock('../../src/services/api');
   
   describe('projectsService', () => {
     it('fetches all projects', async () => {
       const mockProjects = [{ id: 1, name: 'Test' }];
       (api.get as any).mockResolvedValue({ data: mockProjects });
       
       const result = await projectsService.getAll();
       expect(result.data).toEqual(mockProjects);
       expect(api.get).toHaveBeenCalledWith('/api/v1/projects', { params: {} });
     });
   });
   ```

3. **E2E Tests (Playwright)**
   ```typescript
   // e2e/validation-workflow.spec.ts
   import { test, expect } from '@playwright/test';
   
   test('complete validation workflow', async ({ page }) => {
     // Login
     await page.goto('http://localhost:5173/login');
     await page.fill('input[name="username"]', 'admin');
     await page.fill('input[name="password"]', 'admin123');
     await page.click('button[type="submit"]');
     
     // Navigate to project
     await page.click('text=Projects');
     await page.click('text=Test Project');
     
     // Trigger validation
     await page.click('text=Validations');
     await page.click('button:has-text("Trigger Validation")');
     await page.click('button:has-text("Confirm")');
     
     // Wait for completion
     await expect(page.locator('text=Validation completed')).toBeVisible({ timeout: 60000 });
   });
   ```

**Dependencies**:
```bash
npm install -D vitest @testing-library/react @testing-library/user-event jsdom
npm install -D @playwright/test
npx playwright install
```

**Acceptance Criteria**:
- [ ] >80% code coverage for components
- [ ] All services have unit tests
- [ ] E2E tests cover critical user flows
- [ ] CI/CD pipeline runs tests on every commit

---

#### 🎯 Task 9: Optimize Build & Performance
**Priority**: 🟡 HIGH (for production)  
**Estimated Time**: 2 days  
**Complexity**: Medium  

**Subtasks**:
1. **Code Splitting with React.lazy**
   ```tsx
   // src/App.tsx
   import { lazy, Suspense } from 'react';
   
   const DashboardPage = lazy(() => import('./pages/DashboardPage'));
   const ProjectsPage = lazy(() => import('./pages/ProjectsPage'));
   const ReportsPage = lazy(() => import('./pages/ReportsPage'));
   
   <Suspense fallback={<LoadingSpinner />}>
     <Routes>
       <Route path="/" element={<DashboardPage />} />
       <Route path="/projects" element={<ProjectsPage />} />
       <Route path="/reports" element={<ReportsPage />} />
     </Routes>
   </Suspense>
   ```

2. **Manual Chunks Configuration**
   ```typescript
   // vite.config.ts
   export default defineConfig({
     build: {
       rollupOptions: {
         output: {
           manualChunks: {
             'react-vendor': ['react', 'react-dom', 'react-router-dom'],
             'ui-vendor': ['@mui/material', '@emotion/react', '@emotion/styled'],
             'charts-vendor': ['recharts'],
             'data-vendor': ['@tanstack/react-query', '@tanstack/react-table'],
           },
         },
       },
     },
   });
   ```

3. **Bundle Size Analysis**
   ```bash
   npm install -D rollup-plugin-visualizer
   npm run build
   # Open dist/stats.html in browser
   ```

4. **Error Boundaries**
   ```tsx
   // src/components/common/ErrorBoundary.tsx
   class ErrorBoundary extends React.Component {
     state = { hasError: false, error: null };
     
     static getDerivedStateFromError(error) {
       return { hasError: true, error };
     }
     
     render() {
       if (this.state.hasError) {
         return (
           <Box textAlign="center" p={4}>
             <Typography variant="h5">Something went wrong</Typography>
             <Button onClick={() => window.location.reload()}>Reload</Button>
           </Box>
         );
       }
       return this.props.children;
     }
   }
   ```

**Files to Create/Modify**:
- `frontend/vite.config.ts` (add chunk config)
- `frontend/src/App.tsx` (add lazy loading)
- `frontend/src/components/common/ErrorBoundary.tsx` (new)

**Performance Targets**:
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Bundle size < 500KB (gzipped)
- [ ] Lighthouse score > 90

---

#### 🎯 Task 10: Document Frontend Architecture & User Guide
**Priority**: 🟢 MEDIUM  
**Estimated Time**: 2 days  
**Complexity**: Low  

**Subtasks**:
1. **Frontend README.md**
   - Quick start guide
   - Environment variables
   - Build instructions
   - Testing commands
   - Project structure overview

2. **Component Documentation**
   - JSDoc comments for all components
   - Props interfaces documented
   - Usage examples

3. **User Guide with Screenshots**
   - How to create a project
   - How to upload servers
   - How to run validations
   - How to view reports
   - Troubleshooting section

**Files to Create**:
- `frontend/README.md` (new)
- `docs/UI_USER_GUIDE.md` (new)
- `docs/UI_COMPONENT_LIBRARY.md` (new)

**Acceptance Criteria**:
- [ ] README has clear quick start instructions
- [ ] All components have JSDoc comments
- [ ] User guide has screenshots for each workflow
- [ ] Troubleshooting section covers common issues

---

## Priority 4: Backend Cleanup (Optional)

#### 🎯 Task 11: Remove Debug Logging from Backend
**Priority**: ⚪ LOW (optional)  
**Estimated Time**: 30 minutes  
**Complexity**: Low  

**Files to Modify**:
- `api/services/validation_service.py` (remove lines 203-211)
- `azmig_tool/validators/core/storage_validator.py` (remove lines 79-85)

**Acceptance Criteria**:
- [ ] Debug logging statements removed
- [ ] No functional changes to validation logic
- [ ] Celery worker logs cleaner

---

## Summary & Timeline

### High-Level Timeline (6 weeks total)

| Week | Focus Area | Key Deliverables |
|------|-----------|------------------|
| Week 2 | Server Management | ServerUpload, ServerTable, BulkEdit, ValidationResults |
| Week 3 | Dashboard & Reports | StatCards, Charts, PDF Export |
| Week 4 | Real-Time & UX | WebSocket, Empty States, Responsive Design |
| Week 5 | Testing | Unit tests, Integration tests, E2E tests |
| Week 6 | Performance & Docs | Code splitting, Bundle optimization, Documentation |

### Critical Path (Must-Do)
1. ✅ **Server Upload & Management** (Week 2) - Enables end-to-end workflow
2. ✅ **Validation Results Viewer** (Week 2) - Completes core feature set
3. ✅ **Dashboard** (Week 3) - Provides user overview and metrics
4. ✅ **Reports** (Week 3) - Enables data export and analysis

### Nice-to-Have (Can Defer)
- 🟢 Real-time WebSocket (can use polling short-term)
- 🟢 PDF reports (Excel export sufficient initially)
- 🟢 Mobile optimization (focus desktop first)
- 🟢 Unit tests (can be added incrementally)

### MVP Definition (Weeks 2-3 only)
If time is constrained, focus on:
1. ✅ Server Upload with Excel drag-and-drop
2. ✅ Server Table with filtering/sorting
3. ✅ Validation Results Viewer with export
4. ✅ Basic Dashboard with stat cards
5. ⚠️ Skip: WebSocket, PDF export, mobile optimization, tests

---

## Dependencies & Risks

### External Dependencies
- ✅ Backend API (Phase 2) - **COMPLETE**
- ⏳ WebSocket endpoint - **NEEDS IMPLEMENTATION** (for Task 5)
- ⏳ Dashboard stats endpoint - **NEEDS IMPLEMENTATION** (for Task 3)

### Technical Risks
1. **Node.js Version**: Current v21.0.0 vs required v22.12+
   - **Mitigation**: Use Docker for local dev
   
2. **Bundle Size**: Adding Recharts + jsPDF may increase size
   - **Mitigation**: Implement code splitting early
   
3. **WebSocket Complexity**: Backend implementation needed
   - **Mitigation**: Start with polling, add WebSocket later

### Resource Assumptions
- **1 developer** (full-time on UI)
- **Backend support** (for new endpoints)
- **Testing environment** (Docker containers running)

---

## Next Actions (Immediate)

### This Week (Start Now)
1. 🎯 **Start Task 1**: Server Upload & Management
   - Create `ServerUploadZone.tsx` component
   - Implement drag-and-drop with react-dropzone
   - Add progress bar for upload tracking
   
2. 🎯 **Start Task 2**: Validation Results Viewer
   - Create `ValidationJobList.tsx` component
   - Add export button to `ValidationEventLog.tsx`
   - Test Excel export with sample data

### Blockers to Resolve
- [ ] Upgrade Node.js to v22.12+ OR use Docker exclusively
- [ ] Confirm backend WebSocket implementation timeline
- [ ] Get sample Excel files for upload testing

### Questions for Stakeholders
1. Is PDF export required for MVP, or is Excel sufficient?
2. Can we defer mobile optimization to Phase 4?
3. What's the minimum acceptable test coverage for production?
4. Do we need Azure AD integration, or is basic auth OK?

---

**Document Version**: 1.0  
**Last Updated**: Week 1 Complete (Current)  
**Next Review**: After Week 2 Tasks Complete
