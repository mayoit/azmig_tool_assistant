# Web Application Migration Roadmap

## Overview
This document tracks the migration from CLI tool (v3.x) to web application (v4.0).

## Project Phases

### Phase 1: Database Layer (Weeks 1-2)
**Goal**: Set up PostgreSQL database with complete schema

- [ ] **1.1 Environment Setup**
  - [ ] Install PostgreSQL locally for development
  - [ ] Set up database connection configuration
  - [ ] Create database migration tool (Alembic)

- [ ] **1.2 Core Tables**
  - [ ] Create `users` table with authentication fields
  - [ ] Create `projects` table with ownership
  - [ ] Add indexes and constraints

- [ ] **1.3 Configuration Tables**
  - [ ] Create `landing_zone_configs` table
  - [ ] Create `server_configs` table
  - [ ] Add foreign key relationships

- [ ] **1.4 Results Tables**
  - [ ] Create `lz_validation_results` table with JSONB details
  - [ ] Create `server_validation_results` table
  - [ ] Create `replication_status` table

- [ ] **1.5 Supporting Tables**
  - [ ] Create `file_uploads` table for Excel tracking
  - [ ] Create `validation_jobs` table for background processing
  - [ ] Add all necessary indexes

- [ ] **1.6 Sample Data**
  - [ ] Create seed script with sample users
  - [ ] Add sample projects
  - [ ] Add sample server configurations

**Deliverables**:
- PostgreSQL database with complete schema
- Alembic migration scripts
- Seed data script
- Database documentation

---

### Phase 2: API Backend (Weeks 3-6)
**Goal**: Build FastAPI backend with all core endpoints

#### Week 3: Project Structure & Auth

- [ ] **2.1 FastAPI Setup**
  - [ ] Create FastAPI project structure
  - [ ] Set up SQLAlchemy 2.0 with async support
  - [ ] Configure CORS and middleware
  - [ ] Add environment configuration

- [ ] **2.2 Authentication**
  - [ ] Implement JWT token generation
  - [ ] Create `/api/v1/auth/register` endpoint
  - [ ] Create `/api/v1/auth/login` endpoint
  - [ ] Create `/api/v1/auth/refresh` endpoint
  - [ ] Add authentication dependency for protected routes
  - [ ] Implement password hashing (bcrypt)

- [ ] **2.3 Database Models (SQLAlchemy)**
  - [ ] Create User model
  - [ ] Create Project model
  - [ ] Create relationships and associations
  - [ ] Add model validation

#### Week 4: Core CRUD Operations

- [ ] **2.4 Projects API**
  - [ ] `GET /api/v1/projects` - List user's projects
  - [ ] `POST /api/v1/projects` - Create project
  - [ ] `GET /api/v1/projects/{id}` - Get project details
  - [ ] `PUT /api/v1/projects/{id}` - Update project
  - [ ] `DELETE /api/v1/projects/{id}` - Delete project
  - [ ] Add project ownership validation

- [ ] **2.5 Landing Zone API**
  - [ ] `GET /api/v1/projects/{id}/landing-zone` - Get LZ config
  - [ ] `POST /api/v1/projects/{id}/landing-zone` - Create/Update LZ config
  - [ ] Add LZ config validation
  - [ ] Create LandingZoneConfig SQLAlchemy model

- [ ] **2.6 Servers API**
  - [ ] `GET /api/v1/projects/{id}/servers` - List servers
  - [ ] `GET /api/v1/projects/{id}/servers/{server_id}` - Get server
  - [ ] `PUT /api/v1/projects/{id}/servers/{server_id}` - Update server
  - [ ] `DELETE /api/v1/projects/{id}/servers/{server_id}` - Delete server
  - [ ] Create ServerConfig SQLAlchemy model

#### Week 5: File Upload & Validator Integration

- [ ] **2.7 File Upload**
  - [ ] `POST /api/v1/projects/{id}/servers/upload` - Upload Excel
  - [ ] Integrate existing ExcelParser from CLI
  - [ ] Validate Excel structure
  - [ ] Bulk insert server configs to database
  - [ ] Save file metadata to `file_uploads` table
  - [ ] Store files in Azure Blob Storage (optional) or local filesystem

- [ ] **2.8 Validator Service Layer**
  - [ ] Create Azure credential factory for API context
  - [ ] Adapt LandingZoneValidatorWrapper for API use
  - [ ] Adapt ServersValidatorWrapper for API use
  - [ ] Create validator service that stores results in database
  - [ ] Add error handling and logging

#### Week 6: Background Jobs & Validation

- [ ] **2.9 Celery Setup**
  - [ ] Configure Celery with Redis broker
  - [ ] Create validation background tasks
  - [ ] Add job status tracking
  - [ ] Implement progress reporting

- [ ] **2.10 Validation Endpoints**
  - [ ] `POST /api/v1/projects/{id}/landing-zone/validate` - Trigger LZ validation (async)
  - [ ] `POST /api/v1/projects/{id}/servers/validate` - Trigger server validation (async)
  - [ ] `GET /api/v1/projects/{id}/jobs` - List validation jobs
  - [ ] `GET /api/v1/projects/{id}/jobs/{job_id}` - Get job status with progress
  - [ ] Add job cancellation support

- [ ] **2.11 Results Endpoints**
  - [ ] `GET /api/v1/projects/{id}/landing-zone/results` - Get LZ results
  - [ ] `GET /api/v1/projects/{id}/servers/results` - Get all server results
  - [ ] `GET /api/v1/projects/{id}/servers/{server_id}/results` - Get specific server results
  - [ ] Add result filtering and pagination

- [ ] **2.12 Replication Status**
  - [ ] `GET /api/v1/projects/{id}/replication` - Get all replication statuses
  - [ ] `POST /api/v1/projects/{id}/replication/refresh` - Refresh from Azure
  - [ ] Integrate with discovery validator's replication check
  - [ ] Store replication status in database

**Deliverables**:
- Complete FastAPI backend with all endpoints
- Celery workers for background validation
- API documentation (Swagger/OpenAPI auto-generated)
- Postman collection for API testing

---

### Phase 3: Frontend UI (Weeks 7-10)
**Goal**: Build React TypeScript UI with all features

#### Week 7: Setup & Authentication

- [ ] **3.1 React Project Setup**
  - [ ] Initialize Vite + React + TypeScript project
  - [ ] Install dependencies (React Router, React Query, Ant Design)
  - [ ] Set up folder structure
  - [ ] Configure environment variables

- [ ] **3.2 API Client**
  - [ ] Create Axios instance with interceptors
  - [ ] Add JWT token handling
  - [ ] Create type-safe API client functions
  - [ ] Add error handling and retry logic

- [ ] **3.3 Authentication UI**
  - [ ] Create Login page
  - [ ] Create Registration page
  - [ ] Implement auth context/hooks
  - [ ] Add token storage (localStorage)
  - [ ] Add auto-refresh on token expiry
  - [ ] Create protected route wrapper

- [ ] **3.4 Layout & Navigation**
  - [ ] Create main Layout component with sidebar
  - [ ] Create Header with user menu
  - [ ] Create Sidebar navigation
  - [ ] Add routing structure

#### Week 8: Projects & Landing Zone

- [ ] **3.5 Projects UI**
  - [ ] Create Projects list page
  - [ ] Create Project card component
  - [ ] Create "Create Project" modal
  - [ ] Add project edit functionality
  - [ ] Add project delete with confirmation
  - [ ] Create Project detail/dashboard page

- [ ] **3.6 Landing Zone UI**
  - [ ] Create Landing Zone configuration form
  - [ ] Add form validation
  - [ ] Create "Validate Landing Zone" button
  - [ ] Create LZ validation results display
  - [ ] Add validation status badges
  - [ ] Create detailed result cards for each validation type

#### Week 9: Servers & Excel Upload

- [ ] **3.7 Server Management**
  - [ ] Create Servers list page with table
  - [ ] Add server filtering and search
  - [ ] Create manual server add/edit form
  - [ ] Add server delete functionality
  - [ ] Create server detail view

- [ ] **3.8 Excel Upload**
  - [ ] Create drag-and-drop upload component
  - [ ] Add file validation (Excel only)
  - [ ] Show upload progress
  - [ ] Display upload results (success/errors)
  - [ ] Add "Download Template" button
  - [ ] Show upload history

- [ ] **3.9 Server Validation**
  - [ ] Create "Validate Servers" button/modal
  - [ ] Show validation progress in real-time
  - [ ] Create validation results table
  - [ ] Add column-based validation status (region, RG, VNet, etc.)
  - [ ] Create detailed validation result modal
  - [ ] Add export results to Excel/CSV

#### Week 10: Results & Replication

- [ ] **3.10 Validation Results Dashboard**
  - [ ] Create overall results summary cards
  - [ ] Add charts/graphs for validation statistics
  - [ ] Create filterable results table
  - [ ] Add "Re-run Validation" functionality
  - [ ] Show validation history

- [ ] **3.11 Replication Status**
  - [ ] Create Replication status page
  - [ ] Create replication status table
  - [ ] Add health indicators
  - [ ] Create "Refresh Status" button
  - [ ] Add replication timeline/history
  - [ ] Create replication detail modal

- [ ] **3.12 Background Jobs Monitoring**
  - [ ] Create validation jobs list
  - [ ] Show job progress bars
  - [ ] Add real-time updates (polling or WebSocket)
  - [ ] Add job cancellation
  - [ ] Show job logs/errors

**Deliverables**:
- Complete React UI with all features
- Responsive design
- User documentation
- UI/UX testing results

---

### Phase 4: Integration & Testing (Week 11)
**Goal**: End-to-end testing and optimization

- [ ] **4.1 Integration Testing**
  - [ ] Test complete user flow: Register → Create Project → Upload Servers → Validate
  - [ ] Test all CRUD operations
  - [ ] Test file upload with various Excel formats
  - [ ] Test validation with real Azure credentials
  - [ ] Test background job processing

- [ ] **4.2 Performance Testing**
  - [ ] Load test API endpoints
  - [ ] Test with large Excel files (1000+ servers)
  - [ ] Optimize database queries
  - [ ] Add database indexes where needed
  - [ ] Implement API response caching

- [ ] **4.3 Security Audit**
  - [ ] Review authentication implementation
  - [ ] Check SQL injection vulnerabilities
  - [ ] Validate input sanitization
  - [ ] Review CORS configuration
  - [ ] Check file upload security
  - [ ] Audit Azure credential handling

- [ ] **4.4 Bug Fixes**
  - [ ] Fix all identified bugs
  - [ ] Handle edge cases
  - [ ] Improve error messages
  - [ ] Add loading states

**Deliverables**:
- Test report
- Performance benchmark results
- Security audit report
- Bug fix log

---

### Phase 5: Deployment (Week 12)
**Goal**: Deploy to production

- [ ] **5.1 Containerization**
  - [ ] Create Dockerfile for API
  - [ ] Create Dockerfile for UI
  - [ ] Create Dockerfile for Celery worker
  - [ ] Create docker-compose.yml for local development
  - [ ] Optimize Docker images

- [ ] **5.2 Azure Resources**
  - [ ] Provision Azure Database for PostgreSQL
  - [ ] Provision Azure App Service (API)
  - [ ] Provision Azure App Service (UI) or Static Web App
  - [ ] Provision Azure Redis Cache
  - [ ] Provision Azure Blob Storage
  - [ ] Provision Azure Key Vault for secrets
  - [ ] Set up Azure Application Insights

- [ ] **5.3 CI/CD Pipeline**
  - [ ] Create GitHub Actions workflow for API
  - [ ] Create GitHub Actions workflow for UI
  - [ ] Add automated testing in pipeline
  - [ ] Add database migration step
  - [ ] Configure deployment slots (staging/production)

- [ ] **5.4 Monitoring & Logging**
  - [ ] Configure Application Insights logging
  - [ ] Set up alerts for errors
  - [ ] Create monitoring dashboard
  - [ ] Add health check endpoints

- [ ] **5.5 Documentation**
  - [ ] Update README with deployment instructions
  - [ ] Create API documentation
  - [ ] Create user guide for web UI
  - [ ] Create administrator guide
  - [ ] Document environment variables

**Deliverables**:
- Deployed application (staging & production)
- CI/CD pipeline
- Monitoring dashboard
- Complete documentation

---

## Success Criteria

- [ ] Users can create and manage multiple projects
- [ ] Excel upload works seamlessly with existing format
- [ ] Landing Zone validation executes and displays results correctly
- [ ] Server validation handles 500+ servers efficiently
- [ ] Replication status tracks and updates correctly
- [ ] Background jobs process without blocking UI
- [ ] Application is responsive and performant
- [ ] All security requirements met
- [ ] Deployed to Azure and accessible via HTTPS
- [ ] Documentation complete and accurate

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Existing validator logic doesn't work in API context | Gradual refactoring with extensive testing; keep CLI validators separate initially |
| Performance issues with large Excel files | Implement chunked processing, progress indicators, background jobs |
| Azure API rate limiting during validation | Implement request throttling, exponential backoff, job queuing |
| Complex state management in React | Use React Query for server state, minimize client state |
| Database schema changes | Use Alembic migrations, maintain backward compatibility |
| Security vulnerabilities | Regular security audits, dependency updates, penetration testing |

---

## Resources Needed

### Development
- Development environment with PostgreSQL, Redis
- Azure subscription for testing
- Sample data and test projects

### Tools
- VS Code with Python/TypeScript extensions
- Postman for API testing
- pgAdmin for database management
- Azure Storage Explorer

### Team (Recommended)
- Backend Developer (Python/FastAPI)
- Frontend Developer (React/TypeScript)
- DevOps Engineer (Azure deployment)
- QA Engineer (Testing)

---

## Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Database | 2 weeks | PostgreSQL schema, migrations, seed data |
| Phase 2: API | 4 weeks | Complete REST API with background jobs |
| Phase 3: Frontend | 4 weeks | React UI with all features |
| Phase 4: Testing | 1 week | Test reports, bug fixes |
| Phase 5: Deployment | 1 week | Production deployment |
| **Total** | **12 weeks** | **Production-ready web application** |

---

## Next Steps

1. Review and approve this roadmap
2. Set up development environment
3. Begin Phase 1: Database Layer
4. Schedule regular progress reviews (weekly)

**Start Date**: TBD  
**Target Launch**: TBD  
**Version**: 4.0.0
