"""
API endpoints for validation jobs and results.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from database import get_db
from models import (
    User, Project, ValidationJob, ValidationStatus,
    LZValidationResult, ServerValidationResult, ServerConfig,
    ValidationEvent
)
from schemas.validation import (
    ValidationJobResponse,
    ValidationResultsResponse,
    ValidationJobListResponse,
    ValidationTriggerResponse,
    LZValidationResultResponse,
    ServerValidationResultResponse
)
from utils.security import get_current_user
from workers.tasks import run_validation

router = APIRouter()


@router.post("/projects/{project_id}/validate", response_model=ValidationTriggerResponse)
async def trigger_validation(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger async validation job for a project.
    
    This will run both landing zone (Layer 1) and servers (Layer 2) validations.
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
    
    # Create validation job
    new_job = ValidationJob(
        project_id=project_id,
        job_type="full",
        status=ValidationStatus.PENDING,
        created_by_id=current_user.id
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Trigger Celery task (async)
    run_validation.delay(new_job.id)
    
    return {
        "job_id": new_job.id,
        "message": "Validation job started",
        "status": ValidationStatus.PENDING
    }


@router.get("/projects/{project_id}/validations", response_model=ValidationJobListResponse)
async def list_validations(
    project_id: int,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List validation jobs for a project.
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
    
    # Validate pagination
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be 1-100")
    
    # Query validation jobs
    query = db.query(ValidationJob).filter(ValidationJob.project_id == project_id)
    total = query.count()
    
    # Calculate pagination
    offset = (page - 1) * page_size
    pages = (total + page_size - 1) // page_size
    
    # Fetch jobs
    jobs = query.order_by(ValidationJob.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "items": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/validations/{job_id}", response_model=ValidationJobResponse)
async def get_validation_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get validation job status.
    """
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation job {job_id} not found"
        )
    
    # Check permissions via project
    project = db.query(Project).filter(Project.id == job.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this validation job"
        )
    
    return job


@router.get("/validations/{job_id}/events")
async def get_validation_events(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed validation event log for a job (Azure Activity Log style).
    
    Returns individual events for each validation action (Access, Appliance, Storage, Quota)
    with start/completion timestamps, request details, and results.
    """
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation job {job_id} not found"
        )
    
    # Check permissions via project
    project = db.query(Project).filter(Project.id == job.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this validation job"
        )
    
    # Get all validation events for this job, ordered by timestamp
    events = db.query(ValidationEvent).filter(
        ValidationEvent.validation_job_id == job_id
    ).order_by(ValidationEvent.event_timestamp.desc()).all()
    
    return {
        "job_id": job_id,
        "total_events": len(events),
        "events": events
    }


@router.get("/validations/{job_id}/results", response_model=ValidationResultsResponse)
async def get_validation_results(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed validation results for a job.
    """
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation job {job_id} not found"
        )
    
    # Check permissions via project
    project = db.query(Project).filter(Project.id == job.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this validation job"
        )
    
    # Get landing zone results
    lz_results = db.query(LZValidationResult).filter(
        LZValidationResult.validation_job_id == job_id
    ).all()
    
    # Get server results with server names
    server_results_raw = db.query(
        ServerValidationResult,
        ServerConfig.target_machine_name
    ).join(
        ServerConfig,
        ServerValidationResult.server_id == ServerConfig.id
    ).filter(
        ServerValidationResult.validation_job_id == job_id
    ).all()
    
    # Format server results
    server_results = []
    for result, server_name in server_results_raw:
        result_dict = ServerValidationResultResponse.from_orm(result).dict()
        result_dict["server_name"] = server_name
        server_results.append(ServerValidationResultResponse(**result_dict))
    
    # Calculate summary
    lz_passed = sum(1 for r in lz_results if r.status == "passed")
    lz_failed = sum(1 for r in lz_results if r.status == "failed")
    server_passed = sum(1 for r in server_results_raw if r[0].status == "passed")
    server_failed = sum(1 for r in server_results_raw if r[0].status == "failed")
    
    summary = {
        "total_validations": len(lz_results) + len(server_results_raw),
        "total_passed": lz_passed + server_passed,
        "total_failed": lz_failed + server_failed,
        "landing_zone": {
            "total": len(lz_results),
            "passed": lz_passed,
            "failed": lz_failed
        },
        "servers": {
            "total": len(server_results_raw),
            "passed": server_passed,
            "failed": server_failed
        }
    }
    
    return {
        "job": job,
        "landing_zone_results": lz_results,
        "server_results": server_results,
        "summary": summary
    }


@router.delete("/validations/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_validation_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a validation job and all its results.
    
    Note: Cannot delete jobs that are currently running.
    """
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation job {job_id} not found"
        )
    
    # Check permissions via project
    project = db.query(Project).filter(Project.id == job.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this validation job"
        )
    
    # Prevent deletion of running jobs
    if job.status == ValidationStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running validation job"
        )
    
    # Delete job (cascade will delete results)
    db.delete(job)
    db.commit()
    
    return None
