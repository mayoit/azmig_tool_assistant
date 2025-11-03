"""
API endpoints for landing zone configurations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, LandingZoneConfig, Project
from schemas.landing_zone import (
    LandingZoneConfigCreate,
    LandingZoneConfigResponse
)
from utils.security import get_current_user

router = APIRouter()


@router.get("/projects/{project_id}/landing-zone", response_model=LandingZoneConfigResponse)
async def get_landing_zone(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get landing zone configuration for a project.
    
    Landing zone has one-to-one relationship with project.
    """
    # Verify project exists and user has access
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
    
    # Get landing zone config
    lz_config = db.query(LandingZoneConfig).filter(
        LandingZoneConfig.project_id == project_id
    ).first()
    
    if not lz_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Landing zone configuration not found for project {project_id}"
        )
    
    return lz_config


@router.post("/projects/{project_id}/landing-zone", response_model=LandingZoneConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_landing_zone(
    project_id: int,
    lz_data: LandingZoneConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update landing zone configuration for a project.
    
    If landing zone already exists, it will be updated.
    """
    # Verify project exists and user has access
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
    
    # Check if landing zone already exists
    existing_lz = db.query(LandingZoneConfig).filter(
        LandingZoneConfig.project_id == project_id
    ).first()
    
    if existing_lz:
        # Update existing landing zone
        for field, value in lz_data.dict().items():
            setattr(existing_lz, field, value)
        db.commit()
        db.refresh(existing_lz)
        return existing_lz
    else:
        # Create new landing zone
        new_lz = LandingZoneConfig(
            project_id=project_id,
            **lz_data.dict()
        )
        db.add(new_lz)
        db.commit()
        db.refresh(new_lz)
        return new_lz


@router.delete("/projects/{project_id}/landing-zone", status_code=status.HTTP_204_NO_CONTENT)
async def delete_landing_zone(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete landing zone configuration for a project.
    """
    # Verify project exists and user has access
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
    
    # Get landing zone config
    lz_config = db.query(LandingZoneConfig).filter(
        LandingZoneConfig.project_id == project_id
    ).first()
    
    if not lz_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Landing zone configuration not found for project {project_id}"
        )
    
    db.delete(lz_config)
    db.commit()
    
    return None
