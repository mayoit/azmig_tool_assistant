# API Quick Reference

**Version:** 4.0.0  
**Last Updated:** 2025-01-30  
**Total Endpoints:** 20

## Table of Contents
- [Authentication (6 endpoints)](#authentication)
- [Projects (5 endpoints)](#projects)
- [Servers (6 endpoints)](#servers)
- [Landing Zones (3 endpoints)](#landing-zones)
- [Validations (5 endpoints)](#validations)

## Base URL
```
http://localhost:8000
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Get Current User
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Projects

### List Projects
```bash
curl -X GET "http://localhost:8000/api/projects?page=1&page_size=10&status=active" \
  -H "Authorization: Bearer <access_token>"
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 50, max: 100)
- `status` (string): Filter by status (active, in_progress, completed, archived)
- `search` (string): Search in name and description

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Production Migration - Phase 1",
      "description": "Migrate 50 servers...",
      "status": "active",
      "azure_subscription_id": "12345678-1234-...",
      "owner_id": 1,
      "owner": {
        "id": 1,
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin"
      },
      "created_at": "2025-01-30T18:27:17.674870+00:00",
      "updated_at": null,
      "servers_count": 0,
      "validations_count": 0,
      "metadata_json": {
        "target_region": "East US",
        "server_count": 50
      }
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 10,
  "pages": 1
}
```

### Create Project
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Migration Project",
    "description": "Migrate dev servers to Azure",
    "azure_subscription_id": "87654321-4321-4321-4321-210987654321",
    "metadata_json": {
      "target_region": "West US 2",
      "environment": "development"
    }
  }'
```

### Get Project
```bash
curl -X GET http://localhost:8000/api/projects/1 \
  -H "Authorization: Bearer <access_token>"
```

### Update Project
```bash
curl -X PUT http://localhost:8000/api/projects/1 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Project Name",
    "status": "in_progress"
  }'
```

### Delete Project
```bash
curl -X DELETE http://localhost:8000/api/projects/1 \
  -H "Authorization: Bearer <access_token>"
```

**⚠️ Warning:** This will cascade delete all related data (servers, validations, etc.)

---

## Test Credentials

```
Admin:    admin@example.com / admin123
Operator: operator@example.com / operator123
Viewer:   viewer@example.com / viewer123
```

---

## Role-Based Access

| Endpoint | Viewer | Operator | Admin |
|----------|--------|----------|-------|
| GET /api/auth/me | ✅ | ✅ | ✅ |
| POST /api/auth/change-password | ✅ | ✅ | ✅ |
| GET /api/projects | ✅ (own only) | ✅ (own only) | ✅ (all) |
| POST /api/projects | ✅ | ✅ | ✅ |
| GET /api/projects/{id} | ✅ (own only) | ✅ (own only) | ✅ (all) |
| PUT /api/projects/{id} | ✅ (own only) | ✅ (own only) | ✅ (all) |
| DELETE /api/projects/{id} | ✅ (own only) | ✅ (own only) | ✅ (all) |

---

## Interactive API Documentation

Open in browser:
```
http://localhost:8000/api/docs
```

This provides:
- Complete API schema
- Try-it-out functionality
- Request/response examples
- Authentication support

---

## Servers

### List Servers for Project
```bash
curl -X GET "http://localhost:8000/api/projects/1/servers?page=1&page_size=50" \
  -H "Authorization: Bearer <access_token>"
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 50, max: 100)

### Upload Server Configurations (Excel)
```bash
curl -X POST "http://localhost:8000/api/projects/1/servers/upload?update_existing=true" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@servers.xlsx"
```

**Form Data:**
- `file`: Excel file (.xlsx)
- `update_existing` (bool): Update if server already exists (default: false)

**Excel Required Columns:**
| Column | Type | Example |
|--------|------|---------|
| Target Machine Name | String | "web-server-01" |
| Target Region | String | "eastus" |
| Target Subscription | UUID | "12345678-..." |
| Target RG | String | "migration-rg" |
| Target Vnet | String | "migration-vnet" |
| Target Subnet | String | "web-subnet" |
| Target Machine Sku | String | "Standard_D2s_v3" |
| Target Disk Type | Enum | "Premium_LRS" |

**Response:**
```json
{
  "servers_created": 5,
  "servers_updated": 2,
  "errors": []
}
```

### Create Single Server
```bash
curl -X POST http://localhost:8000/api/servers \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "target_machine_name": "web-server-01",
    "target_region": "eastus",
    "target_subscription": "12345678-1234-1234-1234-123456789abc",
    "target_resource_group": "migration-rg",
    "target_vnet": "migration-vnet",
    "target_subnet": "web-subnet",
    "target_machine_sku": "Standard_D2s_v3",
    "target_disk_type": "Premium_LRS"
  }'
```

### Get Server Details
```bash
curl -X GET http://localhost:8000/api/servers/1 \
  -H "Authorization: Bearer <access_token>"
```

### Update Server
```bash
curl -X PUT http://localhost:8000/api/servers/1 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "target_machine_sku": "Standard_D4s_v3",
    "target_disk_type": "Premium_LRS"
  }'
```

### Delete Server
```bash
curl -X DELETE http://localhost:8000/api/servers/1 \
  -H "Authorization: Bearer <access_token>"
```

---

## Landing Zones

### Get Landing Zone Configuration
```bash
curl -X GET http://localhost:8000/api/projects/1/landing-zone \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "id": 1,
  "project_id": 1,
  "migrate_project_name": "test-migrate-project",
  "migrate_project_rg": "test-migrate-rg",
  "migrate_project_subscription": "12345678-1234-1234-1234-123456789abc",
  "recovery_vault_name": "test-recovery-vault",
  "recovery_vault_rg": "test-vault-rg",
  "recovery_vault_subscription": "12345678-1234-1234-1234-123456789abc",
  "appliance_name": "test-appliance",
  "storage_account_cache": "testcachestorage",
  "created_at": "2025-01-30T10:00:00Z",
  "updated_at": "2025-01-30T10:00:00Z"
}
```

### Create/Update Landing Zone (Upsert)
```bash
curl -X POST http://localhost:8000/api/projects/1/landing-zone \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "migrate_project_name": "test-migrate-project",
    "migrate_project_rg": "test-migrate-rg",
    "migrate_project_subscription": "12345678-1234-1234-1234-123456789abc",
    "recovery_vault_name": "test-recovery-vault",
    "recovery_vault_rg": "test-vault-rg",
    "recovery_vault_subscription": "12345678-1234-1234-1234-123456789abc",
    "appliance_name": "test-appliance",
    "storage_account_cache": "testcachestorage"
  }'
```

**Note:** This endpoint will update existing configuration if it exists, or create new if it doesn't.

### Delete Landing Zone
```bash
curl -X DELETE http://localhost:8000/api/projects/1/landing-zone \
  -H "Authorization: Bearer <access_token>"
```

---

## Validations

### Trigger Validation Job
```bash
curl -X POST http://localhost:8000/api/projects/1/validate \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "job_id": 1,
  "message": "Validation job started",
  "status": "pending"
}
```

**Validation Workflow:**
1. Creates ValidationJob record with status=PENDING
2. Dispatches Celery task to background worker
3. Worker updates status to RUNNING
4. Executes Layer 1 (Landing Zone) validation
5. Executes Layer 2 (Servers) validation
6. Updates status to COMPLETED or FAILED
7. Stores results in database

### List Validation Jobs
```bash
curl -X GET "http://localhost:8000/api/projects/1/validations?page=1&page_size=10" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "project_id": 1,
      "status": "completed",
      "created_at": "2025-01-30T10:00:00Z",
      "started_at": "2025-01-30T10:00:05Z",
      "completed_at": "2025-01-30T10:02:30Z",
      "error_message": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "pages": 1
}
```

### Get Validation Job Status
```bash
curl -X GET http://localhost:8000/api/validations/1 \
  -H "Authorization: Bearer <access_token>"
```

**Statuses:**
- `pending` - Job created, waiting for worker
- `running` - Worker processing validation
- `completed` - Validation finished successfully
- `failed` - Validation failed (see error_message)

### Get Validation Results
```bash
curl -X GET http://localhost:8000/api/validations/1/results \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "job": {
    "id": 1,
    "project_id": 1,
    "status": "completed",
    "created_at": "2025-01-30T10:00:00Z",
    "completed_at": "2025-01-30T10:02:30Z"
  },
  "summary": {
    "total_validations": 15,
    "total_passed": 12,
    "total_failed": 3,
    "landing_zone": {
      "total": 5,
      "passed": 4,
      "failed": 1
    },
    "servers": {
      "total": 10,
      "passed": 8,
      "failed": 2
    }
  },
  "landing_zone_results": [
    {
      "id": 1,
      "project_id": 1,
      "validation_type": "migrate_project_access",
      "status": "passed",
      "message": "Azure Migrate project accessible",
      "details": "Project found in subscription",
      "created_at": "2025-01-30T10:01:00Z"
    }
  ],
  "server_results": [
    {
      "id": 1,
      "server_config_id": 1,
      "server_name": "web-server-01",
      "validation_type": "region_validation",
      "status": "passed",
      "message": "Region eastus is valid",
      "details": "Region exists and is accessible",
      "created_at": "2025-01-30T10:01:30Z"
    }
  ]
}
```

### Delete Validation Job
```bash
curl -X DELETE http://localhost:8000/api/validations/1 \
  -H "Authorization: Bearer <access_token>"
```

**Note:** Cannot delete jobs with status=RUNNING. Will return 400 Bad Request.

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "You don't have access to this project"
}
```

### 404 Not Found
```json
{
  "detail": "Project 999 not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## PowerShell Examples

See `test_api.ps1` for complete working examples of:
- User registration
- Login and token management
- Accessing protected endpoints
- Creating and managing projects
- Role-based access testing

Run tests:
```powershell
.\test_api.ps1
```

---

## Common Workflows

### 1. Register and Login New User
```powershell
# Register
$user = @{
    email = "newuser@example.com"
    password = "securepass123"
    full_name = "New User"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" `
    -Method POST -ContentType "application/json" -Body $user

# Login
$login = @{
    email = "newuser@example.com"
    password = "securepass123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method POST -ContentType "application/json" -Body $login

$token = $response.access_token
```

### 2. Create Project and List All Projects
```powershell
$headers = @{ Authorization = "Bearer $token" }

# Create project
$project = @{
    name = "My Project"
    description = "Test migration"
    azure_subscription_id = "12345678-1234-1234-1234-123456789012"
} | ConvertTo-Json

$newProject = Invoke-RestMethod -Uri "http://localhost:8000/api/projects" `
    -Method POST -Headers $headers -ContentType "application/json" -Body $project

# List all projects
$projects = Invoke-RestMethod -Uri "http://localhost:8000/api/projects" `
    -Method GET -Headers $headers
```

### 3. Refresh Access Token
```powershell
$refresh = @{
    refresh_token = $response.refresh_token
} | ConvertTo-Json

$newTokens = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/refresh" `
    -Method POST -ContentType "application/json" -Body $refresh

$token = $newTokens.access_token
```

---

## Database Seeding

To populate test data:
```bash
docker compose exec api python seed_data.py
```

This creates:
- 3 users (admin, operator, viewer)
- 3 sample projects
- Can be run multiple times (idempotent)

---

## Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "environment": "development"
}
```
