"""
Projects router for CRUD operations on migration projects.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from database import get_db
from models import User, Project, ServerConfig, ValidationJob, ProjectStatus
from schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
)
from utils.security import get_current_user, require_admin
from utils.default_migration_settings import get_default_migration_settings

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all projects for the current user.
    
    Supports pagination, filtering by status, and text search.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **status**: Filter by project status
    - **search**: Search text in project name or description
    """
    # Build base query
    query = db.query(Project)
    
    # Non-admin users only see their own projects
    if current_user.role != "admin":
        query = query.filter(Project.owner_id == current_user.id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Project.status == status_filter)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Project.name.ilike(search_pattern)) |
            (Project.description.ilike(search_pattern))
        )
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    offset = (page - 1) * page_size
    pages = (total + page_size - 1) // page_size
    
    # Fetch projects
    projects = query.order_by(Project.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Add computed fields
    project_responses = []
    for project in projects:
        project_dict = ProjectResponse.from_orm(project).dict()
        
        # Count servers
        servers_count = db.query(func.count(ServerConfig.id)).filter(
            ServerConfig.project_id == project.id
        ).scalar()
        project_dict["servers_count"] = servers_count
        
        # Count validation jobs
        validations_count = db.query(func.count(ValidationJob.id)).filter(
            ValidationJob.project_id == project.id
        ).scalar()
        project_dict["validations_count"] = validations_count
        project_dict["lz_migrate_projects"] = project.lz_migrate_projects
        project_dict["validation_settings"] = project.validation_settings
        
        project_responses.append(ProjectResponse(**project_dict))
    
    return {
        "items": project_responses,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new migration project.
    
    - **name**: Project name (required)
    - **description**: Project description (optional)
    - **azure_tenant_id**: Azure tenant ID (required)
    - **metadata_json**: Additional metadata (optional)
    """
    # Create new project
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        azure_tenant_id=project_data.azure_tenant_id,
        metadata_json=project_data.metadata_json,
        status=ProjectStatus.ACTIVE,
        owner_id=current_user.id,
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific project by ID.
    
    Users can only access their own projects unless they are admin.
    """
    # Fetch project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    # Add computed fields
    project_dict = ProjectResponse.from_orm(project).dict()
    
    servers_count = db.query(func.count(ServerConfig.id)).filter(
        ServerConfig.project_id == project.id
    ).scalar()
    project_dict["servers_count"] = servers_count
    
    validations_count = db.query(func.count(ValidationJob.id)).filter(
        ValidationJob.project_id == project.id
    ).scalar()
    project_dict["validations_count"] = validations_count
    project_dict["lz_migrate_projects"] = project.lz_migrate_projects
    project_dict["validation_settings"] = project.validation_settings
    
    return ProjectResponse(**project_dict)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a project.
    
    Users can only update their own projects unless they are admin.
    """
    # Fetch project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    # Update fields
    update_data = project_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project.
    
    This will cascade delete all related data (servers, validations, etc.).
    Only project owner or admin can delete.
    """
    # Fetch project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    # Delete project (cascade will handle related data)
    db.delete(project)
    db.commit()
    
    return None


@router.get("/{project_id}/migration-settings")
async def get_migration_settings(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get project migration settings (allowed regions, VM SKUs, disk types).
    Returns default settings if not configured.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    metadata = project.metadata_json or {}
    migration_settings = metadata.get('migration_settings', get_default_migration_settings())
    
    return migration_settings


@router.put("/{project_id}/migration-settings")
async def update_migration_settings(
    project_id: int,
    settings: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update project migration settings.
    Validates that at least one region is configured.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    # Validate settings structure
    if not isinstance(settings.get('allowed_regions'), list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="allowed_regions must be an array"
        )
    if not isinstance(settings.get('allowed_vm_skus'), list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="allowed_vm_skus must be an array"
        )
    if not isinstance(settings.get('allowed_disk_types'), list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="allowed_disk_types must be an array"
        )
    
    # Validate at least one region
    if len(settings['allowed_regions']) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one region is required"
        )
    
    # Update metadata
    metadata = project.metadata_json or {}
    metadata['migration_settings'] = settings
    project.metadata_json = metadata
    
    db.commit()
    db.refresh(project)
    
    return settings
