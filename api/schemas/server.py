"""
Pydantic schemas for server configuration endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ServerConfigBase(BaseModel):
    """Base schema for server configuration."""
    target_machine_name: str = Field(..., min_length=1, max_length=255, description="Target machine name")
    target_region: str = Field(..., min_length=1, max_length=100, description="Target Azure region")
    target_subscription: str = Field(..., description="Target Azure subscription ID")
    target_resource_group: str = Field(..., min_length=1, max_length=255, description="Target resource group")
    target_vnet: str = Field(..., min_length=1, max_length=255, description="Target virtual network")
    target_subnet: str = Field(..., min_length=1, max_length=255, description="Target subnet")
    target_machine_sku: str = Field(..., min_length=1, max_length=100, description="Target VM SKU")
    target_disk_type: str = Field(..., min_length=1, max_length=50, description="Target disk type")


class ServerConfigCreate(ServerConfigBase):
    """Schema for creating a server configuration."""
    project_id: int = Field(..., description="Project ID this server belongs to")


class ServerConfigUpdate(BaseModel):
    """Schema for updating a server configuration."""
    target_machine_name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_region: Optional[str] = Field(None, min_length=1, max_length=100)
    target_subscription: Optional[str] = None
    target_resource_group: Optional[str] = Field(None, min_length=1, max_length=255)
    target_vnet: Optional[str] = Field(None, min_length=1, max_length=255)
    target_subnet: Optional[str] = Field(None, min_length=1, max_length=255)
    target_machine_sku: Optional[str] = Field(None, min_length=1, max_length=100)
    target_disk_type: Optional[str] = Field(None, min_length=1, max_length=50)


class ServerConfigResponse(ServerConfigBase):
    """Schema for server configuration response."""
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ServerConfigListResponse(BaseModel):
    """Schema for paginated server list."""
    items: list[ServerConfigResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ExcelUploadResponse(BaseModel):
    """Schema for Excel upload response."""
    message: str
    servers_created: int
    servers_updated: int
    errors: list[str] = []
