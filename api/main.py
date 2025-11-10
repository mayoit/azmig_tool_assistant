"""
Main FastAPI application.
Configures routes, middleware, and application lifecycle.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import get_settings
from database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Azure Migration Tool API...")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Azure Migration Tool API...")


# Create FastAPI application
app = FastAPI(
    title="Azure Migration Tool API",
    description="REST API for Azure server migration validation and management",
    version="4.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": "4.0.0",
        "environment": settings.environment,
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Azure Migration Tool API",
        "version": "4.0.0",
        "docs": "/api/docs",
        "health": "/health",
    }


# Import and include routers
from routers import (
    auth, projects, servers, landing_zones, validations, 
    dashboard, landing_zone_upload, azure_auth, landing_zone_validation,
    azure_resources
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(servers.router, prefix="/api", tags=["Servers"])
app.include_router(landing_zones.router, prefix="/api", tags=["Landing Zones"])
app.include_router(landing_zone_upload.router, prefix="/api", tags=["Landing Zone Upload"])
app.include_router(validations.router, prefix="/api", tags=["Validations"])
app.include_router(azure_auth.router, prefix="/api", tags=["Azure Authentication"])
app.include_router(azure_resources.router, prefix="/api", tags=["Azure Resources"])
app.include_router(landing_zone_validation.router, tags=["Landing Zone Validation"])

# TODO: Add replication router in future phases
# from api.routers import replication
# app.include_router(replication.router, prefix="/api/replication", tags=["Replication"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
