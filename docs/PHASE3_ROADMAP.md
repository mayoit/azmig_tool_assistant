# Phase 3 Development Roadmap

## Overview
This document outlines the Phase 3 development plan for the Azure Migration Tool Assistant. Phase 3 focuses on advanced features, enterprise capabilities, and production hardening after the successful completion of Phase 2 (API backend with 8/9 E2E tests passing).

## Phase 3A: Foundation & Multi-Tenancy (Weeks 1-2)

### 1. Multi-Tenancy Architecture
**Goal**: Support multiple organizations/teams with isolated data

**Database Schema**:
```sql
-- New tables
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50), -- owner, admin, member, viewer
    joined_at TIMESTAMP DEFAULT NOW()
);

-- Update existing tables
ALTER TABLE projects ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE projects ADD COLUMN team_id INTEGER REFERENCES teams(id);
ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
```

**API Endpoints**:
- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/organizations` - List user's organizations
- `GET /api/v1/organizations/{org_id}` - Get organization details
- `PUT /api/v1/organizations/{org_id}` - Update organization
- `POST /api/v1/organizations/{org_id}/teams` - Create team
- `GET /api/v1/organizations/{org_id}/teams` - List teams
- `POST /api/v1/teams/{team_id}/members` - Add team member
- `DELETE /api/v1/teams/{team_id}/members/{user_id}` - Remove member

**Implementation**:
```python
# api/routers/organizations.py
from fastapi import APIRouter, Depends
from api.auth import get_current_user
from api.models import Organization, Team

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])

@router.post("")
async def create_organization(org: OrganizationCreate, user: User = Depends(get_current_user)):
    # Create org, add user as owner
    pass

@router.get("")
async def list_organizations(user: User = Depends(get_current_user)):
    # Return orgs where user is member
    pass
```

**RBAC Enhancement**:
```python
# api/auth.py - Enhanced permission checks
def check_organization_access(user: User, org_id: int, required_role: str = "member"):
    """Verify user has required role in organization"""
    pass

def check_team_access(user: User, team_id: int, required_role: str = "member"):
    """Verify user has required role in team"""
    pass

def check_project_access(user: User, project_id: int, required_permission: str = "read"):
    """Verify user can access project through org/team membership"""
    pass
```

### 2. Audit Logging
**Goal**: Track all system changes for compliance and debugging

**Database Schema**:
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    action VARCHAR(100) NOT NULL, -- create_project, update_server, delete_config
    resource_type VARCHAR(50), -- project, server, landing_zone
    resource_id INTEGER,
    changes JSONB, -- {"old": {...}, "new": {...}}
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

**Implementation**:
```python
# api/services/audit_service.py
from api.models import AuditLog

def log_action(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    changes: dict = None,
    ip_address: str = None,
    user_agent: str = None
):
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit)
    db.commit()
```

**Usage Pattern**:
```python
# api/routers/projects.py
from api.services.audit_service import log_action

@router.post("")
async def create_project(project: ProjectCreate, request: Request, user: User = Depends(get_current_user)):
    new_project = Project(**project.dict())
    db.add(new_project)
    db.commit()
    
    # Audit log
    log_action(
        db=db,
        user_id=user.id,
        action="create_project",
        resource_type="project",
        resource_id=new_project.id,
        changes={"new": project.dict()},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return new_project
```

**API Endpoints**:
- `GET /api/v1/audit-logs` - List audit logs (filtered by org, user, date range)
- `GET /api/v1/audit-logs/export` - Export logs as CSV/JSON

### 3. API Rate Limiting
**Goal**: Prevent abuse and ensure fair resource usage

**Implementation**:
```python
# api/middleware/rate_limit.py
from fastapi import Request, HTTPException
from redis import Redis
import time

redis_client = Redis(host='redis', port=6379, decode_responses=True)

async def rate_limit_middleware(request: Request, call_next):
    user_id = request.state.user.id if hasattr(request.state, 'user') else 'anonymous'
    key = f"rate_limit:{user_id}:{request.url.path}"
    
    # Sliding window: 100 requests per minute
    now = int(time.time())
    window = 60
    limit = 100
    
    # Add current request
    redis_client.zadd(key, {now: now})
    redis_client.expire(key, window)
    
    # Count requests in window
    count = redis_client.zcount(key, now - window, now)
    
    if count > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(limit - count)
    response.headers["X-RateLimit-Reset"] = str(now + window)
    
    return response
```

## Phase 3B: Real-Time Features (Weeks 3-5)

### 4. WebSocket Status Updates
**Goal**: Real-time validation job progress without polling

**Implementation**:
```python
# api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}  # job_id -> websockets
    
    async def connect(self, websocket: WebSocket, job_id: int):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, job_id: int):
        self.active_connections[job_id].discard(websocket)
    
    async def broadcast(self, job_id: int, message: dict):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: int):
    await manager.connect(websocket, job_id)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
```

**Celery Integration**:
```python
# api/workers/tasks.py
from api.websocket import manager

@celery_app.task
def validate_servers_task(job_id: int, project_id: int):
    # ... validation logic
    
    # Send progress updates
    asyncio.run(manager.broadcast(job_id, {
        "type": "progress",
        "job_id": job_id,
        "status": "running",
        "progress": 25,
        "message": "Validating landing zone..."
    }))
    
    # ... more validation
    
    asyncio.run(manager.broadcast(job_id, {
        "type": "progress",
        "job_id": job_id,
        "status": "running",
        "progress": 75,
        "message": "Validating 50/100 servers..."
    }))
```

### 5. Custom Validation Rules Engine
**Goal**: Allow users to define custom validation rules without code changes

**Database Schema**:
```sql
CREATE TABLE validation_rules (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50), -- naming_convention, tag_policy, region_whitelist
    config JSONB, -- Rule-specific configuration
    is_active BOOLEAN DEFAULT TRUE,
    severity VARCHAR(20) DEFAULT 'warning', -- info, warning, error
    created_at TIMESTAMP DEFAULT NOW()
);

-- Example rule configs
-- Naming convention: {"pattern": "^vm-[a-z]{3}-[0-9]{3}$", "applies_to": "server_name"}
-- Tag policy: {"required_tags": ["environment", "cost_center", "owner"]}
-- Region whitelist: {"allowed_regions": ["eastus", "westus2"]}
```

**Rule Engine**:
```python
# api/services/rule_engine.py
from typing import List, Dict, Any
import re

class RuleEngine:
    def validate_naming_convention(self, value: str, pattern: str) -> bool:
        return bool(re.match(pattern, value))
    
    def validate_tags(self, tags: Dict[str, str], required: List[str]) -> bool:
        return all(tag in tags for tag in required)
    
    def validate_region(self, region: str, allowed: List[str]) -> bool:
        return region in allowed
    
    def evaluate_rule(self, rule: ValidationRule, resource: dict) -> dict:
        """Evaluate a single rule against a resource"""
        if rule.rule_type == "naming_convention":
            passed = self.validate_naming_convention(
                resource.get("name", ""),
                rule.config["pattern"]
            )
            return {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "passed": passed,
                "severity": rule.severity,
                "message": f"Name must match pattern: {rule.config['pattern']}" if not passed else None
            }
        # ... other rule types
    
    def evaluate_all_rules(self, organization_id: int, resource: dict, resource_type: str) -> List[dict]:
        """Evaluate all active rules for an organization"""
        rules = db.query(ValidationRule).filter(
            ValidationRule.organization_id == organization_id,
            ValidationRule.is_active == True
        ).all()
        
        results = []
        for rule in rules:
            if rule.config.get("applies_to") == resource_type:
                results.append(self.evaluate_rule(rule, resource))
        
        return results
```

**Integration with Validation Service**:
```python
# api/services/validation_service.py
from api.services.rule_engine import RuleEngine

def validate_servers_with_custom_rules(project_id: int, server_configs: List[ServerConfig]):
    project = db.query(Project).filter(Project.id == project_id).first()
    rule_engine = RuleEngine()
    
    for server in server_configs:
        # Run azmig_tool validations
        azure_results = run_azure_validations(server)
        
        # Run custom rules
        custom_results = rule_engine.evaluate_all_rules(
            organization_id=project.organization_id,
            resource=server.dict(),
            resource_type="server"
        )
        
        # Combine results
        all_results = azure_results + custom_results
        save_validation_results(server.id, all_results)
```

### 6. Scheduled Validations
**Goal**: Automatically run validations on a schedule (nightly, weekly, etc.)

**Database Schema**:
```sql
CREATE TABLE validation_schedules (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    schedule_type VARCHAR(20), -- cron, interval
    schedule_config JSONB, -- {"cron": "0 2 * * *"} or {"interval_hours": 24}
    is_active BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Celery Beat Configuration**:
```python
# api/workers/celery_config.py
from celery.schedules import crontab
from api.models import ValidationSchedule

# Dynamic schedule loading
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    schedules = db.query(ValidationSchedule).filter(ValidationSchedule.is_active == True).all()
    
    for schedule in schedules:
        if schedule.schedule_type == "cron":
            # Parse cron expression
            cron_parts = schedule.schedule_config["cron"].split()
            sender.add_periodic_task(
                crontab(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day_of_month=cron_parts[2],
                    month_of_year=cron_parts[3],
                    day_of_week=cron_parts[4]
                ),
                validate_servers_task.s(project_id=schedule.project_id),
                name=f"scheduled-validation-{schedule.id}"
            )
        elif schedule.schedule_type == "interval":
            sender.add_periodic_task(
                schedule.schedule_config["interval_hours"] * 3600,
                validate_servers_task.s(project_id=schedule.project_id),
                name=f"scheduled-validation-{schedule.id}"
            )
```

**API Endpoints**:
- `POST /api/v1/projects/{project_id}/schedules` - Create schedule
- `GET /api/v1/projects/{project_id}/schedules` - List schedules
- `PUT /api/v1/schedules/{schedule_id}` - Update schedule
- `DELETE /api/v1/schedules/{schedule_id}` - Delete schedule

### 7. Reporting & Analytics
**Goal**: Generate comprehensive reports and dashboards

**Report Types**:
1. **Validation Summary Report**: Success rate, common failures, trend over time
2. **Resource Inventory Report**: Server counts by region, SKU, disk type
3. **Cost Estimation Report**: Azure pricing estimates based on configurations
4. **Compliance Report**: Custom rule violations, security findings

**Implementation**:
```python
# api/services/report_service.py
from sqlalchemy import func
from datetime import datetime, timedelta
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class ReportService:
    def generate_validation_summary(self, project_id: int, start_date: datetime, end_date: datetime):
        """Generate validation summary statistics"""
        jobs = db.query(ValidationJob).filter(
            ValidationJob.project_id == project_id,
            ValidationJob.created_at.between(start_date, end_date)
        ).all()
        
        total_jobs = len(jobs)
        successful_jobs = sum(1 for j in jobs if j.status == "completed")
        failed_jobs = sum(1 for j in jobs if j.status == "failed")
        
        # Aggregate validation results
        results = db.query(
            ServerValidationResult.validation_stage,
            func.count(ServerValidationResult.id).label("count"),
            func.sum(func.cast(ServerValidationResult.passed, Integer)).label("passed")
        ).join(ValidationJob).filter(
            ValidationJob.project_id == project_id,
            ValidationJob.created_at.between(start_date, end_date)
        ).group_by(ServerValidationResult.validation_stage).all()
        
        return {
            "summary": {
                "total_jobs": total_jobs,
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": successful_jobs / total_jobs if total_jobs > 0 else 0
            },
            "validation_breakdown": [
                {
                    "stage": r.validation_stage,
                    "total": r.count,
                    "passed": r.passed,
                    "pass_rate": r.passed / r.count if r.count > 0 else 0
                }
                for r in results
            ]
        }
    
    def generate_pdf_report(self, project_id: int, report_data: dict, output_path: str):
        """Generate PDF report using ReportLab"""
        c = canvas.Canvas(output_path, pagesize=letter)
        c.drawString(100, 750, f"Validation Report - Project {project_id}")
        c.drawString(100, 730, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Summary section
        y = 700
        c.drawString(100, y, "Summary:")
        y -= 20
        for key, value in report_data["summary"].items():
            c.drawString(120, y, f"{key}: {value}")
            y -= 15
        
        # Validation breakdown
        y -= 20
        c.drawString(100, y, "Validation Breakdown:")
        y -= 20
        for stage in report_data["validation_breakdown"]:
            c.drawString(120, y, f"{stage['stage']}: {stage['passed']}/{stage['total']} passed ({stage['pass_rate']:.1%})")
            y -= 15
        
        c.save()
```

**API Endpoints**:
- `GET /api/v1/projects/{project_id}/reports/summary` - Validation summary JSON
- `GET /api/v1/projects/{project_id}/reports/inventory` - Resource inventory JSON
- `POST /api/v1/projects/{project_id}/reports/export` - Export report as PDF/CSV

## Phase 3C: Advanced Features (Weeks 6-8)

### 8. Replication Management
**Goal**: Manage Azure Site Recovery replication operations

**Database Schema**:
```sql
CREATE TABLE replication_configs (
    id SERIAL PRIMARY KEY,
    server_id INTEGER REFERENCES server_configs(id),
    replication_status VARCHAR(50), -- not_started, in_progress, protected, failed
    recovery_point_objective_minutes INTEGER,
    app_consistent_snapshot_frequency_minutes INTEGER,
    last_sync TIMESTAMP,
    protection_state JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Implementation**:
```python
# api/services/replication_service.py
from azure.mgmt.recoveryservices import RecoveryServicesClient
from azure.mgmt.recoveryservicessiterecovery import SiteRecoveryManagementClient

class ReplicationService:
    def __init__(self, credential, subscription_id: str):
        self.recovery_client = RecoveryServicesClient(credential, subscription_id)
        self.site_recovery_client = SiteRecoveryManagementClient(credential, subscription_id)
    
    def enable_replication(self, server_config: ServerConfig, landing_zone: LandingZoneConfig):
        """Enable Azure Site Recovery replication for a server"""
        # Configure replication settings
        replication_params = {
            "properties": {
                "policyId": landing_zone.recovery_vault_policy_id,
                "providerSpecificDetails": {
                    "instanceType": "AzureToAzure",
                    "fabricObjectId": server_config.source_vm_id,
                    "recoveryAzureNetworkId": server_config.target_vnet_id,
                    "recoveryAzureSubnetId": server_config.target_subnet_id,
                    "recoveryResourceGroupId": server_config.target_resource_group_id
                }
            }
        }
        
        # Enable replication
        operation = self.site_recovery_client.replication_protected_items.create(
            vault_name=landing_zone.recovery_vault_name,
            resource_group_name=landing_zone.recovery_vault_rg,
            fabric_name=landing_zone.azure_region,
            protection_container_name="default",
            replicated_protected_item_name=server_config.target_machine_name,
            input=replication_params
        )
        
        return operation.result()
    
    def get_replication_status(self, server_config: ServerConfig, landing_zone: LandingZoneConfig):
        """Get current replication status"""
        protected_item = self.site_recovery_client.replication_protected_items.get(
            vault_name=landing_zone.recovery_vault_name,
            resource_group_name=landing_zone.recovery_vault_rg,
            fabric_name=landing_zone.azure_region,
            protection_container_name="default",
            replicated_protected_item_name=server_config.target_machine_name
        )
        
        return {
            "replication_health": protected_item.properties.replication_health,
            "protection_state": protected_item.properties.protection_state,
            "active_location": protected_item.properties.active_location,
            "last_successful_failover": protected_item.properties.last_successful_failover_time,
            "last_successful_test_failover": protected_item.properties.last_successful_test_failover_time
        }
    
    def trigger_failover(self, server_config: ServerConfig, landing_zone: LandingZoneConfig, failover_type: str = "test"):
        """Trigger test or planned failover"""
        failover_params = {
            "properties": {
                "failoverDirection": "PrimaryToRecovery" if failover_type == "planned" else "RecoveryToPrimary",
                "providerSpecificDetails": {
                    "instanceType": "AzureToAzure"
                }
            }
        }
        
        operation = self.site_recovery_client.replication_protected_items.test_failover(
            vault_name=landing_zone.recovery_vault_name,
            resource_group_name=landing_zone.recovery_vault_rg,
            fabric_name=landing_zone.azure_region,
            protection_container_name="default",
            replicated_protected_item_name=server_config.target_machine_name,
            failover_input=failover_params
        )
        
        return operation.result()
```

**API Endpoints**:
- `POST /api/v1/servers/{server_id}/replication/enable` - Enable replication
- `GET /api/v1/servers/{server_id}/replication/status` - Get status
- `POST /api/v1/servers/{server_id}/replication/test-failover` - Test failover
- `POST /api/v1/servers/{server_id}/replication/failover` - Planned failover
- `POST /api/v1/servers/{server_id}/replication/commit` - Commit failover
- `POST /api/v1/servers/{server_id}/replication/disable` - Disable replication

### 9. Integrations

#### Webhooks
**Goal**: Notify external systems of validation events

**Database Schema**:
```sql
CREATE TABLE webhooks (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    secret VARCHAR(255), -- For HMAC signature
    events TEXT[], -- ["validation.completed", "validation.failed"]
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE webhook_deliveries (
    id SERIAL PRIMARY KEY,
    webhook_id INTEGER REFERENCES webhooks(id),
    event_type VARCHAR(100),
    payload JSONB,
    response_status INTEGER,
    response_body TEXT,
    delivered_at TIMESTAMP DEFAULT NOW()
);
```

**Implementation**:
```python
# api/services/webhook_service.py
import hmac
import hashlib
import httpx

class WebhookService:
    async def send_webhook(self, webhook: Webhook, event_type: str, payload: dict):
        """Send webhook notification"""
        # Create signature
        signature = hmac.new(
            webhook.secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Event-Type": event_type
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                # Log delivery
                delivery = WebhookDelivery(
                    webhook_id=webhook.id,
                    event_type=event_type,
                    payload=payload,
                    response_status=response.status_code,
                    response_body=response.text[:1000]
                )
                db.add(delivery)
                db.commit()
                
                return response.status_code == 200
            except Exception as e:
                # Log failed delivery
                delivery = WebhookDelivery(
                    webhook_id=webhook.id,
                    event_type=event_type,
                    payload=payload,
                    response_status=0,
                    response_body=str(e)
                )
                db.add(delivery)
                db.commit()
                return False
    
    async def notify_validation_completed(self, job_id: int):
        """Send notifications for completed validation"""
        job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
        project = db.query(Project).filter(Project.id == job.project_id).first()
        
        webhooks = db.query(Webhook).filter(
            Webhook.organization_id == project.organization_id,
            Webhook.is_active == True,
            Webhook.events.contains(["validation.completed"])
        ).all()
        
        payload = {
            "event": "validation.completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "job_id": job.id,
                "project_id": job.project_id,
                "status": job.status,
                "duration_seconds": (job.updated_at - job.created_at).total_seconds()
            }
        }
        
        for webhook in webhooks:
            await self.send_webhook(webhook, "validation.completed", payload)
```

#### Slack Integration
```python
# api/integrations/slack.py
from slack_sdk.webhook import WebhookClient

def send_slack_notification(webhook_url: str, job: ValidationJob):
    client = WebhookClient(webhook_url)
    
    message = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "✅ Validation Completed" if job.status == "completed" else "❌ Validation Failed"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Project:*\n{job.project.name}"},
                    {"type": "mrkdwn", "text": f"*Job ID:*\n{job.id}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{job.status}"},
                    {"type": "mrkdwn", "text": f"*Duration:*\n{(job.updated_at - job.created_at).total_seconds()}s"}
                ]
            }
        ]
    }
    
    client.send(message)
```

## Phase 3D: Security & Performance (Weeks 9-10)

### 10. Enhanced Security

#### Azure AD Integration
```python
# api/auth_azure_ad.py
from msal import ConfidentialClientApplication

class AzureADAuth:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.app = ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret
        )
    
    def verify_token(self, token: str):
        """Verify Azure AD token"""
        # Decode and verify JWT
        pass
    
    def get_user_info(self, token: str):
        """Get user info from Azure AD"""
        pass
```

#### API Key Management
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    prefix VARCHAR(10) NOT NULL, -- First 8 chars for display
    scopes TEXT[], -- ["read:projects", "write:servers"]
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 11. Performance Optimization

#### Redis Caching
```python
# api/services/cache_service.py
from redis import Redis
import pickle

redis_client = Redis(host='redis', port=6379)

def cache_get(key: str):
    """Get cached value"""
    value = redis_client.get(key)
    return pickle.loads(value) if value else None

def cache_set(key: str, value: any, ttl: int = 3600):
    """Set cached value with TTL"""
    redis_client.setex(key, ttl, pickle.dumps(value))

def cache_invalidate(pattern: str):
    """Invalidate cache by pattern"""
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)

# Usage
@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    cache_key = f"project:{project_id}"
    
    # Try cache first
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    # Query database
    project = db.query(Project).filter(Project.id == project_id).first()
    
    # Cache result
    cache_set(cache_key, project, ttl=300)
    
    return project
```

#### Database Query Optimization
```python
# Add indexes
CREATE INDEX idx_server_configs_project ON server_configs(project_id);
CREATE INDEX idx_validation_results_job ON server_validation_results(job_id);
CREATE INDEX idx_validation_jobs_status ON validation_jobs(status);

# Query optimization examples
from sqlalchemy.orm import joinedload

# Eager loading to avoid N+1 queries
projects = db.query(Project).options(
    joinedload(Project.landing_zone),
    joinedload(Project.servers)
).all()

# Pagination with count optimization
from sqlalchemy import func

total = db.query(func.count(Project.id)).scalar()
projects = db.query(Project).offset(skip).limit(limit).all()
```

## Phase 3E: Enterprise Features (Weeks 11-12)

### 12. Web Dashboard (React/Vue)

**Architecture**:
```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── ProjectList.tsx
│   │   ├── ServerUpload.tsx
│   │   ├── ValidationResults.tsx
│   │   └── RealtimeStatus.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── websocket.ts
│   ├── store/
│   │   ├── projects.ts
│   │   ├── validations.ts
│   │   └── auth.ts
│   └── App.tsx
├── package.json
└── vite.config.ts
```

**Key Features**:
1. **Dashboard**: Project overview, validation statistics, recent jobs
2. **Project Management**: Create, edit, delete projects
3. **Server Upload**: Drag-and-drop Excel upload with progress
4. **Validation Monitoring**: Real-time job status via WebSocket
5. **Results Viewer**: Filterable table, export capabilities
6. **Reports**: Interactive charts, PDF generation

**Sample Component**:
```typescript
// src/components/RealtimeStatus.tsx
import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export function RealtimeStatus({ jobId }: { jobId: number }) {
  const [status, setStatus] = useState({ progress: 0, message: '' });
  const ws = useWebSocket(`ws://localhost:8000/ws/jobs/${jobId}`);
  
  useEffect(() => {
    ws.onMessage((data) => {
      setStatus({ progress: data.progress, message: data.message });
    });
  }, [ws]);
  
  return (
    <div>
      <div className="progress-bar" style={{ width: `${status.progress}%` }} />
      <p>{status.message}</p>
    </div>
  );
}
```

## Implementation Timeline

### Phase 3A: Foundation (Weeks 1-2)
- [ ] Multi-tenancy database schema
- [ ] Organization/team management APIs
- [ ] Enhanced RBAC middleware
- [ ] Audit logging system
- [ ] API rate limiting

### Phase 3B: Real-Time (Weeks 3-5)
- [ ] WebSocket infrastructure
- [ ] Custom validation rules engine
- [ ] Celery Beat scheduled validations
- [ ] Report generation service
- [ ] PDF export

### Phase 3C: Advanced (Weeks 6-8)
- [ ] Azure Site Recovery integration
- [ ] Replication management APIs
- [ ] Webhook system
- [ ] Slack/Teams integrations
- [ ] Azure DevOps pipeline integration

### Phase 3D: Security (Weeks 9-10)
- [ ] Azure AD authentication
- [ ] API key management
- [ ] Redis caching layer
- [ ] Database query optimization
- [ ] Horizontal scaling setup

### Phase 3E: UI (Weeks 11-12)
- [ ] React/Vue dashboard setup
- [ ] Project management UI
- [ ] Server upload with drag-drop
- [ ] Real-time validation monitoring
- [ ] Interactive reports and charts

## Testing Strategy

### Unit Tests
```python
# tests/test_rule_engine.py
def test_naming_convention_validation():
    engine = RuleEngine()
    assert engine.validate_naming_convention("vm-prod-001", r"^vm-[a-z]+-[0-9]{3}$") == True
    assert engine.validate_naming_convention("invalid-name", r"^vm-[a-z]+-[0-9]{3}$") == False
```

### Integration Tests
```python
# tests/test_webhooks.py
async def test_webhook_delivery():
    webhook = create_test_webhook()
    service = WebhookService()
    
    success = await service.send_webhook(webhook, "test.event", {"data": "test"})
    assert success == True
    
    # Verify delivery logged
    delivery = db.query(WebhookDelivery).filter(WebhookDelivery.webhook_id == webhook.id).first()
    assert delivery.response_status == 200
```

### E2E Tests
```bash
# tests/test_phase3_e2e.ps1
# Test multi-tenancy workflow
$org = Invoke-RestMethod -Method POST -Uri "$API_URL/organizations" -Body $orgData
$team = Invoke-RestMethod -Method POST -Uri "$API_URL/organizations/$($org.id)/teams" -Body $teamData

# Test scheduled validation
$schedule = Invoke-RestMethod -Method POST -Uri "$API_URL/projects/$PROJECT_ID/schedules" -Body $scheduleData

# Test WebSocket connection
# (Use wscat or similar tool)
```

## Deployment Considerations

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: azmig-tool-api
spec:
  replicas: 3  # Horizontal scaling
  template:
    spec:
      containers:
      - name: api
        image: azmig-tool:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
```

### High Availability
- PostgreSQL: Primary-replica setup with automatic failover
- Redis: Redis Sentinel or Redis Cluster
- Celery: Multiple worker instances
- API: Load balancer with health checks

### Monitoring
```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram

validation_counter = Counter('validations_total', 'Total validations', ['status'])
validation_duration = Histogram('validation_duration_seconds', 'Validation duration')

@validation_duration.time()
def validate_servers_task(job_id: int):
    # ... validation logic
    validation_counter.labels(status='success').inc()
```

## Success Metrics

- **Performance**: API response time < 200ms (p95), validation throughput > 1000 servers/hour
- **Reliability**: 99.9% uptime, < 0.1% validation job failures
- **Adoption**: > 80% of users use custom rules, > 50% use scheduled validations
- **Scalability**: Support 10,000+ servers per project, 100+ concurrent users

## Documentation Requirements

- API reference (OpenAPI/Swagger)
- User guide for custom rules and schedules
- Integration guide for webhooks and APIs
- Security best practices
- Deployment guide (Docker, Kubernetes, Azure)

---

**Note**: This roadmap is flexible. Prioritize features based on user feedback and business needs. Each phase can be adjusted or reordered as requirements evolve.
