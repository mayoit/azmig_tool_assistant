"""
Pydantic schemas for landing zone configuration endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class LandingZoneConfigBase(BaseModel):
    """Base schema for landing zone configuration."""
    migrate_project_name: str = Field(..., min_length=1, max_length=255, description="Azure Migrate project name")
    migrate_project_rg: str = Field(..., min_length=1, max_length=255, description="Migrate project resource group")
    recovery_vault_name: str = Field(..., min_length=1, max_length=255, description="Recovery vault name")
    recovery_vault_rg: str = Field(..., min_length=1, max_length=255, description="Recovery vault resource group")
    cache_storage_account: str = Field(..., min_length=1, max_length=255, description="Cache storage account name")
    cache_storage_rg: str = Field(..., min_length=1, max_length=255, description="Cache storage resource group")
    appliance_name: str = Field(..., min_length=1, max_length=255, description="Appliance name")


class LandingZoneConfigCreate(LandingZoneConfigBase):
    """Schema for creating/updating a landing zone configuration."""
    pass


class LandingZoneConfigResponse(LandingZoneConfigBase):
    """Schema for landing zone configuration response."""
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Validation status fields
    validation_status: Optional[str] = Field(None, description="Latest validation status (PASSED/WARNING/FAILED/SKIPPED)")
    last_validated_at: Optional[datetime] = Field(None, description="Timestamp of last validation")
    validation_results: Optional[Dict[str, Any]] = Field(None, description="Detailed validation results")
    
    class Config:
        from_attributes = True
