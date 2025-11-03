# Azure Migration Tool - Docker Setup

## Quick Start Guide

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v2+
- Git

### Initial Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd azmig_tool_assistant
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file** with your configuration:
   - Set secure passwords for `DB_PASSWORD` and `REDIS_PASSWORD`
   - Generate a random `SECRET_KEY` (min 32 characters)
   - Optionally add Azure credentials

4. **Start all services**:
   ```bash
   docker-compose up -d
   ```

5. **Check service health**:
   ```bash
   docker-compose ps
   ```

6. **View logs**:
   ```bash
   docker-compose logs -f
   ```

### Service Access

Once running, access the services at:

- **API Documentation**: http://localhost:8000/api/docs
- **API Health Check**: http://localhost:8000/health
- **Frontend (Vue.js)**: http://localhost:5173
- **PostgreSQL**: localhost:5432 (use credentials from .env)
- **Redis**: localhost:6379

### Database Migrations

1. **Create initial migration**:
   ```bash
   docker-compose exec api alembic revision --autogenerate -m "Initial schema"
   ```

2. **Apply migrations**:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

3. **Rollback migration**:
   ```bash
   docker-compose exec api alembic downgrade -1
   ```

### Development Workflow

#### API Development
```bash
# Watch API logs
docker-compose logs -f api

# Restart API after code changes (if needed)
docker-compose restart api

# Access API container shell
docker-compose exec api bash

# Run tests
docker-compose exec api pytest
```

#### Frontend Development
```bash
# Watch frontend logs
docker-compose logs -f frontend

# Restart frontend
docker-compose restart frontend

# Access frontend container shell
docker-compose exec frontend sh

# Install new npm package
docker-compose exec frontend npm install <package-name>
```

#### Database Operations
```bash
# Access PostgreSQL shell
docker-compose exec db psql -U azmig_user -d azmig_db

# Backup database
docker-compose exec db pg_dump -U azmig_user azmig_db > backup.sql

# Restore database
docker-compose exec -T db psql -U azmig_user azmig_db < backup.sql

# View database logs
docker-compose logs -f db
```

#### Celery Workers
```bash
# Watch worker logs
docker-compose logs -f celery_worker

# Restart workers
docker-compose restart celery_worker celery_beat

# Check task queue in Redis
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} LLEN celery
```

### Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild containers after Dockerfile changes
docker-compose up -d --build

# View running containers
docker-compose ps

# View all logs
docker-compose logs

# Follow logs for specific service
docker-compose logs -f api

# Scale Celery workers
docker-compose up -d --scale celery_worker=3
```

### Troubleshooting

#### Database connection issues
```bash
# Check if database is healthy
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### API not starting
```bash
# Check API logs for errors
docker-compose logs api

# Verify environment variables
docker-compose exec api env | grep DATABASE_URL

# Check database connectivity
docker-compose exec api python -c "from api.database import engine; print(engine.url)"
```

#### Frontend build errors
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild node_modules
docker-compose exec frontend rm -rf node_modules package-lock.json
docker-compose exec frontend npm install
```

#### Port conflicts
If ports are already in use:
1. Edit `docker-compose.yml`
2. Change port mappings (e.g., "8001:8000" for API)
3. Restart services

### Production Deployment

For production, use the nginx reverse proxy:

```bash
# Start with production profile
docker-compose --profile production up -d

# Generate SSL certificates (example with certbot)
# Add SSL configuration to nginx/conf.d/default.conf
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes data!)
docker-compose down -v

# Stop specific service
docker-compose stop api
```

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL password | `azmig_secure_password` |
| `REDIS_PASSWORD` | Redis password | `redis_secure_password` |
| `SECRET_KEY` | JWT secret key | (must set) |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription | (optional) |
| `AZURE_CLIENT_ID` | Service principal ID | (optional) |
| `AZURE_CLIENT_SECRET` | Service principal secret | (optional) |
| `ENVIRONMENT` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `true` |

### Next Steps

1. **Phase 2**: Implement API endpoints (auth, projects, servers, etc.)
2. **Phase 3**: Build Vue.js frontend
3. **Phase 4**: Integration testing
4. **Phase 5**: Deploy to Azure

For detailed architecture, see `docs/WEB_APP_ARCHITECTURE.md`.
