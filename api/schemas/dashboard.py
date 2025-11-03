"""
Dashboard-related Pydantic schemas.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DashboardStats(BaseModel):
    """Dashboard statistics summary."""
    total_projects: int
    active_projects: int
    total_servers: int
    total_validations: int
    
    class Config:
        from_attributes = True


class RecentValidationJob(BaseModel):
    """Recent validation job summary for dashboard."""
    id: int
    project_id: int
    project_name: str
    status: str
    job_type: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ValidationTrend(BaseModel):
    """Validation trend data point."""
    date: str  # ISO format date (YYYY-MM-DD)
    passed: int
    failed: int
    total: int
    
    class Config:
        from_attributes = True


class DashboardData(BaseModel):
    """Complete dashboard data."""
    stats: DashboardStats
    recent_jobs: List[RecentValidationJob]
    trends: List[ValidationTrend]
