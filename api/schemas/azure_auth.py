"""
Pydantic schemas for Azure authentication endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AzureAuthConfigRequest(BaseModel):
    """Schema for configuring Azure authentication."""
    tenant_id: str = Field(..., description="Azure tenant (directory) ID")
    auth_method: str = Field(..., description="Authentication method: service_principal, managed_identity, or user_login")
    credentials: Optional[Dict[str, Any]] = Field(None, description="Auth credentials (encrypted before storage)")


class AzureAuthStatusResponse(BaseModel):
    """Schema for Azure authentication status response."""
    configured: bool = Field(..., description="Whether authentication is configured")
    auth_method: Optional[str] = Field(None, description="Current authentication method")
    tenant_id: Optional[str] = Field(None, description="Azure tenant ID")
    token_valid: bool = Field(False, description="Whether cached token is valid")
    token_expires_at: Optional[datetime] = Field(None, description="Token expiration timestamp")
    
    class Config:
        from_attributes = True


class AzureAuthTestResponse(BaseModel):
    """Schema for authentication test response."""
    success: bool = Field(..., description="Whether authentication test succeeded")
    message: str = Field(..., description="Test result message")
