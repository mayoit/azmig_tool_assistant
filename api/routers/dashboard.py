"""
API endpoints for dashboard statistics and data.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta

from database import get_db
from models import User, Project, ProjectStatus, ValidationJob, ValidationStatus, ServerConfig, LZValidationResult, ServerValidationResult
from schemas.dashboard import DashboardData, DashboardStats, RecentValidationJob, ValidationTrend
from utils.security import get_current_user

router = APIRouter()


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard data including stats, recent jobs, and validation trends.
    """
    # Get statistics
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == ProjectStatus.ACTIVE).count()
    total_servers = db.query(ServerConfig).count()
    total_validations = db.query(ValidationJob).count()
    
    stats = DashboardStats(
        total_projects=total_projects,
        active_projects=active_projects,
        total_servers=total_servers,
        total_validations=total_validations
    )
    
    # Get recent validation jobs (last 10)
    recent_jobs_query = (
        db.query(
            ValidationJob.id,
            ValidationJob.project_id,
            Project.name.label('project_name'),
            ValidationJob.status,
            ValidationJob.job_type,
            ValidationJob.created_at,
            ValidationJob.completed_at
        )
        .join(Project, ValidationJob.project_id == Project.id)
        .order_by(ValidationJob.created_at.desc())
        .limit(10)
    )
    
    recent_jobs = [
        RecentValidationJob(
            id=job.id,
            project_id=job.project_id,
            project_name=job.project_name,
            status=job.status,
            job_type=job.job_type,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
        for job in recent_jobs_query.all()
    ]
    
    # Get validation trends for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Query validation results grouped by date
    trends_query = (
        db.query(
            func.date(ValidationJob.created_at).label('date'),
            func.count(case((ValidationJob.status == ValidationStatus.COMPLETED, 1))).label('passed'),
            func.count(case((ValidationJob.status == ValidationStatus.FAILED, 1))).label('failed'),
            func.count(ValidationJob.id).label('total')
        )
        .filter(ValidationJob.created_at >= thirty_days_ago)
        .group_by(func.date(ValidationJob.created_at))
        .order_by(func.date(ValidationJob.created_at))
    )
    
    trends = [
        ValidationTrend(
            date=trend.date.isoformat() if trend.date else "",
            passed=trend.passed or 0,
            failed=trend.failed or 0,
            total=trend.total or 0
        )
        for trend in trends_query.all()
    ]
    
    return DashboardData(
        stats=stats,
        recent_jobs=recent_jobs,
        trends=trends
    )
