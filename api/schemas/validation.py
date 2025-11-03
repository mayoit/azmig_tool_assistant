"""
Pydantic schemas for validation endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import ValidationStatus


class ValidationJobResponse(BaseModel):
    """Schema for validation job response."""
    id: int
    project_id: int
    status: ValidationStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class ValidationResultBase(BaseModel):
    """Base schema for validation result."""
    validation_type: str
    status: str
    message: str
    details: Optional[str]


class LZValidationResultResponse(ValidationResultBase):
    """Schema for landing zone validation result."""
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ServerValidationResultResponse(ValidationResultBase):
    """Schema for server validation result."""
    id: int
    server_config_id: int
    server_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ValidationResultsResponse(BaseModel):
    """Schema for complete validation results."""
    job: ValidationJobResponse
    landing_zone_results: List[LZValidationResultResponse]
    server_results: List[ServerValidationResultResponse]
    summary: Dict[str, Any]


class ValidationJobListResponse(BaseModel):
    """Schema for paginated validation job list."""
    items: List[ValidationJobResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ValidationTriggerResponse(BaseModel):
    """Schema for validation trigger response."""
    job_id: int
    message: str
    status: ValidationStatus
