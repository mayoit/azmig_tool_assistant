# Production Deployment Guide

## MVP Features (Current Release)
- ✅ User authentication (Login/Logout)
- ✅ Dashboard with real-time statistics (4 cards)
- ✅ Responsive layout with dark mode
- ⏳ Other features show "coming soon" (Projects, Servers, Validations, Reports)

---

## Quick Start (Production)

### Prerequisites
- Docker & Docker Compose installed
- `.env` file configured (see below)

### 1. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DB_PASSWORD=your_secure_db_password_here

# Redis
REDIS_PASSWORD=your_secure_redis_password_here

# API Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your_long_random_secret_key_minimum_32_characters

# Azure Credentials (optional - for validation features)
AZURE_SUBSCRIPTION_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
```

**Generate a secure SECRET_KEY**:
```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32
```

### 2. Build and Start Production Stack

```bash
# Build all images
docker compose -f docker-compose.prod.yml build

# Start all services in detached mode
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### 3. Initialize Database

```bash
# Run database migrations
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Create initial admin user (optional)
docker compose -f docker-compose.prod.yml exec api python -m scripts.create_admin
```

### 4. Access Application

- **Frontend**: http://localhost
- **API Docs**: http://localhost/docs
- **API ReDoc**: http://localhost/redoc
- **Health Check**: http://localhost/health

### 5. Default Login Credentials

After running the seed script:
- **Email**: admin@example.com
- **Password**: admin123

**⚠️ IMPORTANT**: Change the admin password immediately after first login!

---

## Service Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Nginx    │ :80 (Reverse Proxy)
│  (Alpine)   │
└──────┬──────┘
       │
       ├─────────────► /            → Frontend Static Files (React)
       ├─────────────► /api/        → Backend API (FastAPI)
       └─────────────► /ws/         → WebSocket (future)
       
┌──────────────────────────────────────────────────────────┐
│                     Backend Services                      │
├──────────────┬──────────────┬──────────────┬────────────┤
│ FastAPI API  │ Celery Worker│ Celery Beat  │            │
│   :8000      │ (Background) │ (Scheduler)  │            │
└──────┬───────┴──────┬───────┴──────┬───────┘            │
       │              │              │                     │
       ▼              ▼              ▼                     │
┌──────────────┐ ┌────────────────────────┐              │
│  PostgreSQL  │ │       Redis            │              │
│   :5432      │ │      :6379             │              │
└──────────────┘ └────────────────────────┘              │
└──────────────────────────────────────────────────────────┘
```

---

## Monitoring & Logs

### View Logs for Specific Service
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# API only
docker compose -f docker-compose.prod.yml logs -f api

# Frontend/Nginx
docker compose -f docker-compose.prod.yml logs -f nginx

# Celery worker
docker compose -f docker-compose.prod.yml logs -f celery_worker
```

### Check Service Health
```bash
# Check all containers
docker compose -f docker-compose.prod.yml ps

# Health check endpoint
curl http://localhost/health

# API health
curl http://localhost/api/health
```

### Database Access
```bash
# Connect to PostgreSQL
docker compose -f docker-compose.prod.yml exec db psql -U azmig_user -d azmig_db

# Backup database
docker compose -f docker-compose.prod.yml exec db pg_dump -U azmig_user azmig_db > backup.sql

# Restore database
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T db psql -U azmig_user -d azmig_db
```

---

## Stopping & Cleanup

### Stop Services
```bash
# Stop all services (keeps data)
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (DELETES DATA!)
docker compose -f docker-compose.prod.yml down -v

# Stop and remove images
docker compose -f docker-compose.prod.yml down --rmi all
```

### Restart Services
```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart api
```

---

## Updating the Application

### 1. Pull Latest Code
```bash
git pull origin main
```

### 2. Rebuild and Deploy
```bash
# Rebuild changed services
docker compose -f docker-compose.prod.yml build

# Restart with new images
docker compose -f docker-compose.prod.yml up -d

# Run database migrations if needed
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

---

## Troubleshooting

### Issue: Cannot connect to frontend

**Check**:
```bash
# Is Nginx running?
docker compose -f docker-compose.prod.yml ps nginx

# Check Nginx logs
docker compose -f docker-compose.prod.yml logs nginx

# Test Nginx config
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Issue: API returns 502 Bad Gateway

**Check**:
```bash
# Is API running?
docker compose -f docker-compose.prod.yml ps api

# Check API logs
docker compose -f docker-compose.prod.yml logs api

# Check database connection
docker compose -f docker-compose.prod.yml exec api python -c "from database import engine; print(engine)"
```

### Issue: Login fails with 401

**Check**:
```bash
# Verify SECRET_KEY is set
docker compose -f docker-compose.prod.yml exec api env | grep SECRET_KEY

# Check if user exists in database
docker compose -f docker-compose.prod.yml exec db psql -U azmig_user -d azmig_db -c "SELECT id, email, is_active FROM users;"
```

### Issue: Celery tasks not running

**Check**:
```bash
# Is Celery worker running?
docker compose -f docker-compose.prod.yml ps celery_worker

# Check worker logs
docker compose -f docker-compose.prod.yml logs celery_worker

# Check Redis connection
docker compose -f docker-compose.prod.yml exec redis redis-cli -a your_redis_password ping
```

---

## Production Recommendations

### Security
- [ ] Change all default passwords (DB, Redis, admin user)
- [ ] Generate strong SECRET_KEY (min 32 characters)
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up firewall rules
- [ ] Use environment-specific `.env` files (don't commit to git)
- [ ] Regularly update Docker images

### Performance
- [ ] Configure appropriate API workers (default: 4)
- [ ] Set up database connection pooling
- [ ] Enable Nginx caching for static files
- [ ] Configure CDN for frontend assets (optional)

### Monitoring
- [ ] Set up log aggregation (ELK, Grafana, etc.)
- [ ] Configure health check alerts
- [ ] Monitor disk space for volumes
- [ ] Set up database backups (automated)

### Backup Strategy
```bash
# Daily database backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U azmig_user azmig_db > backups/db_backup_$DATE.sql
gzip backups/db_backup_$DATE.sql

# Keep only last 7 days
find backups/ -name "db_backup_*.sql.gz" -mtime +7 -delete
```

---

## Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| **Frontend** | Vite dev server (HMR) | Static build + Nginx |
| **API** | `--reload` flag | Multiple workers |
| **Compose File** | `docker-compose.yml` | `docker-compose.prod.yml` |
| **DEBUG** | `true` | `false` |
| **Ports** | Multiple exposed | Only 80/443 |
| **Volumes** | Source code mounted | Built into image |

---

## Next Steps

1. **Test the MVP**:
   - Log in with test credentials
   - Verify dashboard statistics load correctly
   - Test dark mode toggle
   - Check responsive design on mobile

2. **Week 3 Development** (next phase):
   - Build ProjectList, ProjectForm, DeleteModal
   - Add RecentJobsTable to dashboard
   - Implement ValidationTrendsChart
   - Deploy updated version

3. **Production Deployment Options**:
   - **Azure App Service**: Use Azure Container Registry
   - **Azure Container Apps**: Managed container platform
   - **Azure Kubernetes Service (AKS)**: For large scale
   - **On-Premises**: Deploy to existing infrastructure

---

## Support

For issues or questions:
- Check logs: `docker compose -f docker-compose.prod.yml logs -f`
- Review `DEPLOYMENT_READINESS.md` for feature status
- See `docs/` folder for detailed documentation

**Version**: v4.0.0-mvp  
**Last Updated**: October 31, 2025
