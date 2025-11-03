# Azure Migration Tool - Docker Deployment Guide

## Quick Start

### 1. Build and Start All Services
```powershell
# Build and start all containers (database, redis, api, frontend, celery workers)
docker compose up --build -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f api
docker compose logs -f frontend
```

### 2. Initialize Database (First Time Only)
```powershell
# Run database migrations
docker compose exec api alembic upgrade head

# (Optional) Seed initial data
docker compose exec api python seed_data.py
```

### 3. Access the Application
- **Frontend (React UI)**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000
- **Nginx Reverse Proxy** (if using `--profile production`): http://localhost

### 4. Stop Services
```powershell
# Stop all containers
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v
```

## Service Overview

| Service | Container Name | Port | Purpose |
|---------|---------------|------|---------|
| PostgreSQL | azmig_postgres | 5432 | Database |
| Redis | azmig_redis | 6379 | Task queue & cache |
| FastAPI | azmig_api | 8000 | Backend API |
| React | azmig_frontend | 5173 | Frontend UI |
| Celery Worker | azmig_celery_worker | - | Background tasks |
| Celery Beat | azmig_celery_beat | - | Scheduled tasks |
| Nginx | azmig_nginx | 80, 443 | Reverse proxy (production profile) |

## Development Workflow

### Hot Reload
Both frontend and backend support hot reload:
- **Frontend**: Vite HMR automatically reloads on file changes
- **Backend**: Uvicorn `--reload` flag restarts on Python file changes

### Running Commands Inside Containers
```powershell
# Access API container shell
docker compose exec api bash

# Run Alembic migrations
docker compose exec api alembic revision --autogenerate -m "Add new table"
docker compose exec api alembic upgrade head

# Access database
docker compose exec db psql -U azmig_user -d azmig_db

# View Redis data
docker compose exec redis redis-cli -a redis_secure_password_change_me

# Frontend package management
docker compose exec frontend npm install <package>
docker compose exec frontend npm run build
```

### View Container Status
```powershell
# List running containers
docker compose ps

# View resource usage
docker compose stats

# Inspect a specific service
docker compose inspect api
```

## Environment Configuration

### .env File
Update `.env` with your settings:

```properties
# Database
DB_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_redis_password

# API Security
SECRET_KEY=your-super-secret-key-min-32-characters

# Azure Credentials (optional)
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Environment
ENVIRONMENT=development
DEBUG=true
```

## Troubleshooting

### Container Won't Start
```powershell
# Check container logs
docker compose logs api

# Rebuild without cache
docker compose build --no-cache api
docker compose up -d api
```

### Database Connection Issues
```powershell
# Check database health
docker compose exec db pg_isready -U azmig_user -d azmig_db

# Reset database
docker compose down -v
docker compose up -d db
docker compose exec api alembic upgrade head
```

### Frontend Build Errors
```powershell
# Clear node_modules and rebuild
docker compose down frontend
docker compose build --no-cache frontend
docker compose up -d frontend
```

### Port Conflicts
If ports 5432, 6379, 8000, or 5173 are already in use:
1. Stop conflicting services
2. Or update `docker-compose.yml` to use different ports:
   ```yaml
   ports:
     - "5433:5432"  # Use 5433 on host instead of 5432
   ```

## Production Deployment

### Using Nginx Reverse Proxy
```powershell
# Start with production profile
docker compose --profile production up -d

# Access via Nginx
# Frontend: http://localhost
# API: http://localhost/api
```

### Production Build
For production deployment, update:
1. `frontend/.env.production` - Set production API URLs
2. `.env` - Use strong passwords and secrets
3. Consider using managed databases (Azure PostgreSQL, Redis Cache)

### SSL/TLS (Production)
Update `nginx/conf.d/default.conf` to add SSL certificates:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of config
}
```

## Monitoring & Logs

### Real-time Logs
```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api
```

### Health Checks
```powershell
# API health
curl http://localhost:8000/health

# Database health
docker compose exec db pg_isready -U azmig_user

# Redis health
docker compose exec redis redis-cli -a redis_secure_password_change_me ping
```

## Data Persistence

Data is persisted in Docker volumes:
- `postgres_data`: Database files
- `redis_data`: Redis persistence
- `uploads`: User-uploaded files (Excel, etc.)

To backup:
```powershell
# Backup database
docker compose exec db pg_dump -U azmig_user azmig_db > backup.sql

# Backup uploads
docker compose cp azmig_api:/app/uploads ./uploads_backup
```

To restore:
```powershell
# Restore database
cat backup.sql | docker compose exec -T db psql -U azmig_user -d azmig_db

# Restore uploads
docker compose cp ./uploads_backup/. azmig_api:/app/uploads
```

## Next Steps

1. **Week 2**: Continue with authentication UI and layout enhancements
2. **Testing**: Run tests inside containers
   ```powershell
   docker compose exec api pytest
   docker compose exec frontend npm test
   ```
3. **CI/CD**: Set up GitHub Actions for automated builds and deployments
