# Web Application Architecture

## Overview
Transformation of Azure Migration Tool from CLI to a three-tier web application.

## Architecture Tiers

### 1. Database Tier (PostgreSQL)

#### Database Schema

```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects (Base entity - all operations scoped to projects)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    azure_subscription_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- active, archived, completed
    UNIQUE(owner_id, name)
);

-- Landing Zone Configurations
CREATE TABLE landing_zone_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    migrate_project_name VARCHAR(255) NOT NULL,
    migrate_project_rg VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(100) NOT NULL,
    recovery_vault_name VARCHAR(255),
    recovery_vault_rg VARCHAR(255),
    cache_storage_account VARCHAR(255),
    cache_storage_rg VARCHAR(255),
    appliance_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Server Configurations (from Excel uploads)
CREATE TABLE server_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    target_machine_name VARCHAR(255) NOT NULL,
    target_region VARCHAR(100) NOT NULL,
    target_subscription VARCHAR(100) NOT NULL,
    target_rg VARCHAR(255) NOT NULL,
    target_vnet VARCHAR(255) NOT NULL,
    target_subnet VARCHAR(255) NOT NULL,
    target_machine_sku VARCHAR(100),
    target_disk_type VARCHAR(50),
    source_machine_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, target_machine_name)
);

-- Validation Results (Landing Zone)
CREATE TABLE lz_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    lz_config_id UUID REFERENCES landing_zone_configs(id) ON DELETE CASCADE,
    validation_type VARCHAR(100) NOT NULL, -- access, appliance, storage, quota
    status VARCHAR(50) NOT NULL, -- ok, warning, failed
    message TEXT,
    details JSONB, -- Store full validation details
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation Results (Servers)
CREATE TABLE server_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    server_config_id UUID REFERENCES server_configs(id) ON DELETE CASCADE,
    validation_type VARCHAR(100) NOT NULL, -- region, rg, vnet, sku, disk, discovery, rbac
    status VARCHAR(50) NOT NULL, -- ok, warning, failed
    message TEXT,
    details JSONB,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Replication Status Tracking
CREATE TABLE replication_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    server_config_id UUID REFERENCES server_configs(id) ON DELETE CASCADE,
    is_enabled BOOLEAN DEFAULT false,
    replication_state VARCHAR(100), -- Protected, Protecting, ProtectionFailed, etc.
    replication_health VARCHAR(50), -- Normal, Warning, Critical
    vault_name VARCHAR(255),
    fabric_name VARCHAR(255),
    protection_container VARCHAR(255),
    last_sync_time TIMESTAMP,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File Uploads (Excel files)
CREATE TABLE file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50), -- excel_servers, csv_landing_zone, json_landing_zone
    file_path TEXT, -- Path to stored file
    file_size BIGINT,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP,
    error_message TEXT
);

-- Validation Jobs (Background processing)
CREATE TABLE validation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    job_type VARCHAR(100) NOT NULL, -- landing_zone_validation, server_validation
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    progress INTEGER DEFAULT 0, -- Percentage 0-100
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_lz_configs_project ON landing_zone_configs(project_id);
CREATE INDEX idx_server_configs_project ON server_configs(project_id);
CREATE INDEX idx_lz_validation_project ON lz_validation_results(project_id);
CREATE INDEX idx_server_validation_project ON server_validation_results(project_id);
CREATE INDEX idx_replication_project ON replication_status(project_id);
CREATE INDEX idx_validation_jobs_project ON validation_jobs(project_id);
CREATE INDEX idx_validation_jobs_status ON validation_jobs(status);
```

### 2. API Tier (Python - FastAPI)

#### Technology Stack
- **Framework**: FastAPI (async, high performance)
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT tokens + OAuth2
- **Background Jobs**: Celery + Redis
- **File Storage**: Local filesystem or Azure Blob Storage
- **API Documentation**: Auto-generated Swagger/OpenAPI

#### Project Structure
```
azmig_web/
├── api/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── dependencies.py            # Shared dependencies (auth, db)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py              # Auth endpoints
│   │   ├── jwt.py                 # JWT token handling
│   │   └── models.py              # Auth data models
│   ├── projects/
│   │   ├── __init__.py
│   │   ├── router.py              # Project CRUD endpoints
│   │   ├── models.py              # Project Pydantic models
│   │   └── service.py             # Business logic
│   ├── landing_zone/
│   │   ├── __init__.py
│   │   ├── router.py              # LZ config & validation endpoints
│   │   ├── models.py
│   │   └── service.py
│   ├── servers/
│   │   ├── __init__.py
│   │   ├── router.py              # Server config & validation
│   │   ├── models.py
│   │   ├── service.py
│   │   └── upload.py              # Excel file upload handling
│   ├── validations/
│   │   ├── __init__.py
│   │   ├── router.py              # Validation execution endpoints
│   │   ├── tasks.py               # Celery background tasks
│   │   └── executor.py            # Reuse existing validators
│   ├── replication/
│   │   ├── __init__.py
│   │   ├── router.py              # Replication status endpoints
│   │   └── service.py
│   └── utils/
│       ├── __init__.py
│       └── azure_client_factory.py # Azure credential management
├── database/
│   ├── __init__.py
│   ├── base.py                    # SQLAlchemy base
│   ├── session.py                 # Database session management
│   └── models/
│       ├── __init__.py
│       ├── user.py
│       ├── project.py
│       ├── landing_zone.py
│       ├── server.py
│       ├── validation_result.py
│       └── replication.py
├── validators/                     # Reuse from CLI tool
│   ├── __init__.py
│   ├── core/                      # Keep existing validators
│   └── wrappers/                  # Keep existing wrappers
├── workers/
│   ├── __init__.py
│   ├── celery_app.py              # Celery configuration
│   └── tasks.py                   # Background validation tasks
└── config.py                       # App configuration
```

#### Key API Endpoints

```python
# Authentication
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me

# Projects
GET    /api/v1/projects                    # List user's projects
POST   /api/v1/projects                    # Create project
GET    /api/v1/projects/{project_id}       # Get project details
PUT    /api/v1/projects/{project_id}       # Update project
DELETE /api/v1/projects/{project_id}       # Delete project

# Landing Zone (Project-scoped)
GET    /api/v1/projects/{project_id}/landing-zone              # Get LZ config
POST   /api/v1/projects/{project_id}/landing-zone              # Create/Update LZ config
POST   /api/v1/projects/{project_id}/landing-zone/validate     # Trigger LZ validation
GET    /api/v1/projects/{project_id}/landing-zone/results      # Get LZ validation results

# Servers (Project-scoped)
GET    /api/v1/projects/{project_id}/servers                   # List servers
POST   /api/v1/projects/{project_id}/servers/upload            # Upload Excel file
GET    /api/v1/projects/{project_id}/servers/{server_id}       # Get server config
PUT    /api/v1/projects/{project_id}/servers/{server_id}       # Update server
DELETE /api/v1/projects/{project_id}/servers/{server_id}       # Delete server
POST   /api/v1/projects/{project_id}/servers/validate          # Trigger server validation
GET    /api/v1/projects/{project_id}/servers/results           # Get server validation results
GET    /api/v1/projects/{project_id}/servers/{server_id}/results # Get specific server results

# Validation Jobs
GET    /api/v1/projects/{project_id}/jobs                      # List validation jobs
GET    /api/v1/projects/{project_id}/jobs/{job_id}             # Get job status
DELETE /api/v1/projects/{project_id}/jobs/{job_id}             # Cancel job

# Replication Status
GET    /api/v1/projects/{project_id}/replication               # Get all replication statuses
GET    /api/v1/projects/{project_id}/replication/{server_id}   # Get server replication status
POST   /api/v1/projects/{project_id}/replication/refresh       # Refresh replication status
```

#### Sample API Implementation

```python
# api/projects/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db, get_current_user
from .models import ProjectCreate, ProjectUpdate, ProjectResponse
from .service import ProjectService
from database.models.user import User

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects owned by the current user"""
    service = ProjectService(db)
    return service.get_user_projects(current_user.id)

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    service = ProjectService(db)
    return service.create_project(project, current_user.id)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    service = ProjectService(db)
    project = service.get_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

```python
# api/servers/upload.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import pandas as pd
from io import BytesIO

from ..dependencies import get_db, get_current_user
from .service import ServerService
from database.models.user import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/servers", tags=["servers"])

@router.post("/upload")
async def upload_servers(
    project_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload Excel file with server configurations"""
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # Validate Excel structure (reuse existing parser logic)
        from azmig_tool.config.parsers import ExcelParser
        parser = ExcelParser(file_path=None)  # Modified to accept DataFrame
        configs = parser.parse_dataframe(df)
        
        # Save to database
        service = ServerService(db)
        result = service.bulk_create_servers(project_id, configs, current_user.id)
        
        # Save file record
        from database.models.file_upload import FileUpload
        file_record = FileUpload(
            project_id=project_id,
            filename=file.filename,
            file_type='excel_servers',
            file_size=len(contents),
            uploaded_by=current_user.id,
            processed=True
        )
        db.add(file_record)
        db.commit()
        
        return {
            "message": f"Successfully uploaded {len(configs)} servers",
            "file_id": str(file_record.id),
            "servers_created": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
```

```python
# validations/tasks.py - Celery background tasks
from celery import Task
from uuid import UUID
from sqlalchemy.orm import Session

from workers.celery_app import celery_app
from database.session import get_db_session
from database.models.validation_job import ValidationJob
from validators.wrappers.landing_zone_wrapper import LandingZoneValidatorWrapper
from validators.wrappers.servers_wrapper import ServersValidatorWrapper

@celery_app.task(bind=True)
def run_landing_zone_validation(self: Task, job_id: str, project_id: str, lz_config_id: str):
    """Background task for landing zone validation"""
    db = next(get_db_session())
    
    try:
        # Update job status
        job = db.query(ValidationJob).filter_by(id=UUID(job_id)).first()
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Get LZ config from database
        from database.models.landing_zone import LandingZoneConfig
        lz_config = db.query(LandingZoneConfig).filter_by(id=UUID(lz_config_id)).first()
        
        # Run validation using existing validator
        from azure.identity import DefaultAzureCredential
        validator = LandingZoneValidatorWrapper(DefaultAzureCredential())
        
        # Convert DB model to validation config
        from azmig_tool.core.models import MigrateProjectConfig
        config = MigrateProjectConfig(
            migrate_project_name=lz_config.migrate_project_name,
            resource_group=lz_config.migrate_project_rg,
            subscription_id=lz_config.subscription_id,
            # ... other fields
        )
        
        results = validator.validate_project(config)
        
        # Save results to database
        from database.models.validation_result import LZValidationResult
        for validation_type, result in results.items():
            db_result = LZValidationResult(
                project_id=UUID(project_id),
                lz_config_id=UUID(lz_config_id),
                validation_type=validation_type,
                status=result.status,
                message=result.message,
                details=result.to_dict()
            )
            db.add(db_result)
        
        # Update job status
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.progress = 100
        job.result = {"validations_run": len(results)}
        db.commit()
        
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()
```

### 3. UI Tier (React/TypeScript)

#### Technology Stack
- **Framework**: React 18 with TypeScript
- **State Management**: React Query (TanStack Query) for API data
- **Routing**: React Router v6
- **UI Components**: Ant Design or Material-UI
- **Forms**: React Hook Form
- **File Upload**: react-dropzone
- **Tables**: TanStack Table (React Table v8)
- **Charts**: Recharts or Chart.js
- **Build Tool**: Vite

#### Project Structure
```
azmig-ui/
├── public/
├── src/
│   ├── api/
│   │   ├── client.ts              # Axios instance with auth
│   │   ├── projects.ts            # Project API calls
│   │   ├── landingZone.ts
│   │   ├── servers.ts
│   │   ├── validations.ts
│   │   └── replication.ts
│   ├── components/
│   │   ├── common/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── projects/
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── CreateProjectModal.tsx
│   │   │   └── ProjectSettings.tsx
│   │   ├── landingZone/
│   │   │   ├── LandingZoneForm.tsx
│   │   │   ├── LZValidationResults.tsx
│   │   │   └── LZValidationCard.tsx
│   │   ├── servers/
│   │   │   ├── ServerList.tsx
│   │   │   ├── ServerUpload.tsx    # Excel upload
│   │   │   ├── ServerForm.tsx
│   │   │   ├── ServerValidationResults.tsx
│   │   │   └── ValidationStatusBadge.tsx
│   │   ├── replication/
│   │   │   ├── ReplicationDashboard.tsx
│   │   │   ├── ReplicationStatusTable.tsx
│   │   │   └── ReplicationHealthBadge.tsx
│   │   └── validations/
│   │       ├── ValidationJobsList.tsx
│   │       ├── ValidationProgress.tsx
│   │       └── ValidationDetailsModal.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ProjectsPage.tsx
│   │   ├── ProjectDetailPage.tsx
│   │   ├── LandingZonePage.tsx
│   │   ├── ServersPage.tsx
│   │   ├── ValidationResultsPage.tsx
│   │   └── ReplicationPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   ├── useServers.ts
│   │   └── useValidations.ts
│   ├── types/
│   │   ├── project.ts
│   │   ├── server.ts
│   │   ├── validation.ts
│   │   └── replication.ts
│   ├── utils/
│   │   ├── auth.ts
│   │   └── formatters.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── routes.tsx
├── package.json
├── tsconfig.json
└── vite.config.ts
```

#### Key UI Features

**1. Project-Centric Navigation**
```typescript
// Project Dashboard showing:
// - Project overview card
// - Quick stats (servers count, validation status, replication status)
// - Navigation tabs: Landing Zone | Servers | Validation Results | Replication
```

**2. Excel Upload Interface**
```typescript
// ServerUpload.tsx
import { Upload } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

export const ServerUpload: React.FC<{ projectId: string }> = ({ projectId }) => {
  const uploadServers = useUploadServers(projectId);
  
  return (
    <Upload.Dragger
      accept=".xlsx,.xls"
      customRequest={async ({ file }) => {
        const formData = new FormData();
        formData.append('file', file);
        await uploadServers.mutateAsync(formData);
      }}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">Click or drag Excel file to upload</p>
      <p className="ant-upload-hint">
        Upload server configuration Excel file
      </p>
    </Upload.Dragger>
  );
};
```

**3. Validation Results Dashboard**
```typescript
// ValidationResultsPage.tsx
export const ValidationResultsPage: React.FC = () => {
  const { projectId } = useParams();
  const { data: lzResults } = useLZValidationResults(projectId);
  const { data: serverResults } = useServerValidationResults(projectId);
  
  return (
    <div>
      <h1>Validation Results</h1>
      
      {/* Landing Zone Results */}
      <Card title="Landing Zone Validation">
        <ValidationStatusGrid results={lzResults} />
      </Card>
      
      {/* Server Results Table */}
      <Card title="Server Validation Results">
        <Table
          dataSource={serverResults}
          columns={[
            { title: 'Server Name', dataIndex: 'serverName' },
            { title: 'Region', dataIndex: 'region', render: (val, record) => 
              <ValidationBadge status={record.regionStatus} text={val} />
            },
            { title: 'Resource Group', dataIndex: 'resourceGroup', render: (val, record) => 
              <ValidationBadge status={record.rgStatus} text={val} />
            },
            // ... other validation columns
          ]}
        />
      </Card>
    </div>
  );
};
```

**4. Real-time Validation Progress**
```typescript
// Use WebSocket or polling for job status
const { data: job } = useQuery(
  ['validation-job', jobId],
  () => getValidationJob(projectId, jobId),
  { refetchInterval: 2000, enabled: job?.status === 'running' }
);

<Progress percent={job?.progress} status={job?.status === 'failed' ? 'exception' : 'active'} />
```

## Migration Strategy

### Phase 1: Database Setup
1. Create PostgreSQL database
2. Run schema migrations
3. Seed initial data (admin user, sample project)

### Phase 2: API Development
1. Set up FastAPI project structure
2. Implement authentication (JWT)
3. Create project CRUD endpoints
4. Migrate validator logic to API services
5. Implement file upload endpoints
6. Set up Celery for background jobs
7. Add WebSocket for real-time updates

### Phase 3: UI Development
1. Set up React project with TypeScript
2. Implement authentication flow
3. Create project management UI
4. Build Excel upload interface
5. Create validation results dashboards
6. Add replication status monitoring

### Phase 4: Integration & Testing
1. End-to-end testing
2. Performance optimization
3. Security audit
4. Documentation

### Phase 5: Deployment
1. Containerize with Docker
2. Set up CI/CD pipeline
3. Deploy to Azure App Service or AKS
4. Configure monitoring and logging

## Deployment Architecture

```
Azure Resources:
├── Azure App Service (API + UI)
├── Azure Database for PostgreSQL
├── Azure Redis Cache (Celery broker)
├── Azure Blob Storage (File uploads)
├── Azure Key Vault (Secrets)
└── Azure Application Insights (Monitoring)
```

## Next Steps

Would you like me to:
1. Start implementing the database models?
2. Set up the FastAPI project structure?
3. Create the React UI boilerplate?
4. Begin with a specific feature (e.g., project CRUD + Excel upload)?

Let me know which part you'd like to tackle first!
