# Phase 1 Quick Reference

## Essential Commands

### Start/Stop Services
```powershell
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart specific service
docker compose restart api

# View service status
docker compose ps

# View logs
docker compose logs -f api
docker compose logs -f db
```

### Database Operations
```powershell
# Access PostgreSQL
docker compose exec db psql -U azmig_user -d azmig_db

# List tables
docker compose exec db psql -U azmig_user -d azmig_db -c "\dt"

# View table structure
docker compose exec db psql -U azmig_user -d azmig_db -c "\d users"

# Run SQL query
docker compose exec db psql -U azmig_user -d azmig_db -c "SELECT * FROM users;"
```

### Alembic Migrations
```powershell
# Create new migration
docker compose exec api alembic revision --autogenerate -m "Description"

# Apply migrations
docker compose exec api alembic upgrade head

# Rollback one migration
docker compose exec api alembic downgrade -1

# View migration history
docker compose exec api alembic history

# View current revision
docker compose exec api alembic current
```

### API Testing
```powershell
# Health check
curl http://localhost:8000/health

# View API docs
start http://localhost:8000/api/docs

# View alternative docs
start http://localhost:8000/api/redoc

# Root endpoint
curl http://localhost:8000/
```

### Container Management
```powershell
# Enter API container
docker compose exec api bash

# Enter database container
docker compose exec db bash

# View container logs
docker compose logs api --tail 50

# Follow logs in real-time
docker compose logs -f api
```

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| API Health | http://localhost:8000/health | Health check endpoint |
| API Docs | http://localhost:8000/api/docs | Interactive API documentation (Swagger) |
| API Redoc | http://localhost:8000/api/redoc | Alternative API documentation |
| PostgreSQL | localhost:5432 | Database connection (use DB client) |
| Redis | localhost:6379 | Redis connection (use Redis client) |

## Database Connection

### Using DBeaver/pgAdmin
```
Host: localhost
Port: 5432
Database: azmig_db
Username: azmig_user
Password: (check .env file - DB_PASSWORD)
```

### Connection String
```
postgresql://azmig_user:YOUR_PASSWORD@localhost:5432/azmig_db
```

## Common Tasks

### Add Sample Data
```sql
-- Connect to database first
docker compose exec db psql -U azmig_user -d azmig_db

-- Insert test user
INSERT INTO users (email, hashed_password, full_name, role, is_active)
VALUES ('admin@example.com', '$2b$12$...', 'Admin User', 'admin', true);

-- Insert test project
INSERT INTO projects (name, description, status, azure_subscription_id, owner_id)
VALUES ('Test Migration', 'Test project', 'active', 'sub-123', 1);
```

### Reset Database
```powershell
# WARNING: This deletes all data!

# Stop API
docker compose stop api celery_worker celery_beat

# Rollback all migrations
docker compose exec api alembic downgrade base

# Reapply migrations
docker compose exec api alembic upgrade head

# Restart API
docker compose start api celery_worker celery_beat
```

### Rebuild After Code Changes
```powershell
# Rebuild API container
docker compose up -d --build api

# Or rebuild all
docker compose up -d --build
```

## Troubleshooting

### API Not Responding
```powershell
# Check if container is running
docker compose ps

# View API logs
docker compose logs api --tail 50

# Restart API
docker compose restart api
```

### Database Connection Failed
```powershell
# Check if database is healthy
docker compose ps db

# View database logs
docker compose logs db --tail 50

# Verify password in .env matches DB_PASSWORD
cat .env | Select-String DB_PASSWORD
```

### Migration Errors
```powershell
# Check current migration status
docker compose exec api alembic current

# View migration history
docker compose exec api alembic history

# Manually mark current state (if out of sync)
docker compose exec api alembic stamp head
```

## Environment Variables

Edit `.env` file to change:
- `DB_PASSWORD` - PostgreSQL password
- `REDIS_PASSWORD` - Redis password
- `SECRET_KEY` - JWT secret key (must be 32+ characters)
- `DEBUG` - Enable debug mode (true/false)
- `ENVIRONMENT` - Environment name (development/production)
- `AZURE_*` - Azure credentials (optional for Phase 1)

After changing `.env`, restart services:
```powershell
docker compose down
docker compose up -d
```

## Next Steps (Phase 2)

1. Create `api/routers/` directory
2. Implement authentication endpoints (`/api/auth/`)
3. Implement CRUD endpoints (`/api/projects/`, `/api/servers/`)
4. Set up Celery workers for background validation
5. Create API tests

See `WEB_APP_MIGRATION_ROADMAP.md` for complete Phase 2 plan.
