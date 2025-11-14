"""
Pydantic schemas for project-related endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from models import ProjectStatus
from schemas.auth import UserResponse


class ProjectBase(BaseModel):
    """Base schema for project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    azure_tenant_id: str = Field(..., description="Azure tenant (directory) ID - required for project")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="Additional metadata including landing zones with subscriptions")
    # Azure authentication fields (optional on create)
    auth_method: Optional[str] = Field(
        None, description="Authentication method: azure_cli, service_principal, or managed_identity"
    )


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    # Inherits Azure auth fields from ProjectBase
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    azure_tenant_id: Optional[str] = Field(None, description="Azure tenant (directory) ID")
    metadata_json: Optional[Dict[str, Any]] = None
    # Azure authentication fields (all optional)
    auth_method: Optional[str] = Field(
        None, description="Authentication method: azure_cli, service_principal, or managed_identity"
    )


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: int
    status: ProjectStatus
    owner_id: int
    owner: Optional[UserResponse] = None
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Azure authentication fields
    azure_tenant_id: Optional[str] = Field(None, description="Azure tenant (directory) ID")
    auth_method: Optional[str] = Field(None, description="Authentication method: azure_cli, service_principal, or managed_identity")
    auth_token_expires_at: Optional[datetime] = Field(None, description="Token expiration timestamp")
    
    # Counts (computed fields)
    servers_count: Optional[int] = Field(None, description="Number of servers in project")
    validations_count: Optional[int] = Field(None, description="Number of validations")
    lz_migrate_projects: Optional[List[Dict[str, Any]]] = Field(
        None, description="Validated Azure Migrate projects grouped with landing zones (each with subscriptionId)"
    )
    validation_settings: Optional[Dict[str, Any]] = Field(
        None, description="Validation configuration settings for the project"
    )
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for paginated project list."""
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int
