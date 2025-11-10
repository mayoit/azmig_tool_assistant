"""
API endpoints for Landing Zone validation.

Provides endpoints to validate Azure Migrate Projects and App Landing Zones.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from database import get_db
from services.landing_zone_validation_service import LandingZoneValidationService
from models import Project


router = APIRouter(prefix="/api/projects", tags=["landing-zone-validation"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ValidateMigrateProjectRequest(BaseModel):
    """Request to validate a migrate project"""
    force_revalidate: bool = False  # Re-run even if recent validation exists


class ValidateMigrateProjectResponse(BaseModel):
    """Response from migrate project validation"""
    success: bool
    validation_id: Optional[int] = None
    status: Optional[str] = None
    error: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/{project_id}/landing-zones/migrate-projects/{migrate_project_index}/validate",
    response_model=ValidateMigrateProjectResponse,
    summary="Validate Azure Migrate Project",
    description="Validates a migrate project against Azure using azmig_tool logic. "
                "Respects validation settings as feature toggles."
)
async def validate_migrate_project(
    project_id: int,
    migrate_project_index: int,
    request: ValidateMigrateProjectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Validate a migrate project against Azure.
    
    This endpoint:
    1. Authenticates with Azure using project's auth settings
    2. Runs validations based on project's validation settings (feature toggles)
    3. Stores results in the database
    4. Returns validation status
    
    Validations include:
    - Access validation (RBAC on migrate project, recovery vault, subscription)
    - Appliance health (connectivity, health status, alerts)
    - Storage cache (storage account exists, region, permissions)
    - Quota validation (vCPU usage, limits, availability)
    """
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Validate migrate project index
    if not project.lz_migrate_projects or migrate_project_index >= len(project.lz_migrate_projects):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid migrate project index: {migrate_project_index}"
        )
    
    # Create service
    validation_service = LandingZoneValidationService(db)
    
    # Check if recent validation exists (within 1 hour)
    if not request.force_revalidate:
        existing_result = validation_service.get_migrate_project_validation_result(
            project_id, migrate_project_index
        )
        if existing_result:
            # Return cached result if recent
            from datetime import datetime, timezone, timedelta
            if existing_result.get("completed_at"):
                completed_at = datetime.fromisoformat(existing_result["completed_at"])
                if datetime.now(timezone.utc) - completed_at < timedelta(hours=1):
                    return ValidateMigrateProjectResponse(
                        success=True,
                        validation_id=existing_result["id"],
                        status=existing_result["overall_status"],
                        results={
                            "access": existing_result["access_result"],
                            "appliance": existing_result["appliance_result"],
                            "storage": existing_result["storage_result"],
                            "quota": existing_result["quota_result"]
                        },
                        started_at=existing_result["started_at"],
                        completed_at=existing_result["completed_at"]
                    )
    
    # Run validation (async)
    result = await validation_service.validate_migrate_project(
        project_id, migrate_project_index
    )
    
    return ValidateMigrateProjectResponse(**result)


@router.get(
    "/{project_id}/landing-zones/migrate-projects/{migrate_project_index}/validation-result",
    summary="Get Migrate Project Validation Result",
    description="Retrieves the latest validation result for a migrate project"
)
def get_migrate_project_validation_result(
    project_id: int,
    migrate_project_index: int,
    db: Session = Depends(get_db)
):
    """Get the latest validation result for a migrate project."""
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    validation_service = LandingZoneValidationService(db)
    result = validation_service.get_migrate_project_validation_result(
        project_id, migrate_project_index
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No validation result found for this migrate project"
        )
    
    return result
