"""
API endpoints for Azure authentication management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from database import get_db
from models import Project, User
from services.azure_auth_service import AzureAuthService
from utils.security import get_current_user
from schemas.azure_auth import (
    AzureAuthConfigRequest,
    AzureAuthStatusResponse,
    AzureAuthTestResponse,
)


router = APIRouter(prefix="/projects", tags=["azure-auth"])


@router.post("/{project_id}/auth/configure", status_code=status.HTTP_200_OK)
async def configure_authentication(
    project_id: int,
    config: AzureAuthConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Configure Azure authentication for a project.
    
    Supported auth methods:
    - service_principal: Requires client_id and client_secret in credentials
    - managed_identity: Optional client_id in credentials
    - user_login: Interactive authentication (for development)
    """
    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Check permissions (only admin or project owner can configure auth)
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to configure authentication for this project"
        )
    
    # Configure authentication
    auth_service = AzureAuthService(db)
    result = auth_service.configure_project_auth(
        project_id=project_id,
        tenant_id=config.tenant_id,
        auth_method=config.auth_method,
        credentials=config.credentials
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to configure authentication")
        )
    
    return result


@router.post("/{project_id}/auth/test", response_model=AzureAuthTestResponse)
async def test_authentication(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test Azure authentication for a project.
    
    This will attempt to authenticate and cache the token if successful.
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
    
    # Test authentication
    auth_service = AzureAuthService(db)
    result = auth_service.test_authentication(project_id)
    
    return AzureAuthTestResponse(**result)


@router.get("/{project_id}/auth/status")
async def get_auth_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get authentication status for a project.
    
    Returns configuration details and token validity.
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
    
    # Get auth status
    auth_service = AzureAuthService(db)
    return auth_service.get_auth_status(project_id)


@router.post("/{project_id}/auth/refresh")
async def refresh_token(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh the authentication token for a project.
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
    
    # Refresh token
    auth_service = AzureAuthService(db)
    result = auth_service.refresh_token(project_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to refresh token")
        )
    
    return result


@router.post("/{project_id}/auth/device-code")
async def initiate_device_code_auth(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate device code authentication flow for User Login method.
    
    Returns device code, user code, and verification URL for user to complete authentication.
    User must visit the URL and enter the code to complete authentication.
    Poll the /auth/status endpoint to check when authentication completes.
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
    
    # Verify auth method is user_login
    if project.auth_method != 'user_login':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device code authentication is only available for 'user_login' auth method"
        )
    
    if not project.azure_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not configured for this project"
        )
    
    # Initiate device code flow
    auth_service = AzureAuthService(db)
    result = auth_service.initiate_device_code_flow(project_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to initiate device code authentication")
        )
    
    return result


@router.post("/{project_id}/auth/poll-device-code")
async def poll_device_code_auth(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Poll for device code authentication completion.
    
    Call this endpoint after initiating device code flow to check if user has completed authentication.
    Returns success=True with token info when authentication completes.
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
    
    # Get flow data from project metadata
    import json
    metadata = project.metadata_json or {}
    flow_info = metadata.get("device_code_flow")
    
    if not flow_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active device code flow found. Please initiate authentication first."
        )
    
    try:
        from msal import PublicClientApplication
        
        app = PublicClientApplication(
            client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46",
            authority=f"https://login.microsoftonline.com/{project.azure_tenant_id}"
        )
        
        # Try to acquire token with the flow data
        result = app.acquire_token_by_device_flow(flow_info["flow_data"])
        
        if "access_token" in result:
            # Success! Cache the token
            auth_service = AzureAuthService(db)
            from azure.core.credentials import AccessToken
            from datetime import timezone
            
            token = AccessToken(
                token=result["access_token"],
                expires_on=int(result["expires_in"]) + int(datetime.now(timezone.utc).timestamp())
            )
            auth_service._cache_token(project, token)
            
            # Clear the flow data from metadata
            metadata.pop("device_code_flow", None)
            project.metadata_json = metadata
            db.commit()
            
            return {
                "success": True,
                "message": "Authentication completed successfully",
                "token_expires_at": project.auth_token_expires_at.isoformat() if project.auth_token_expires_at else None
            }
        elif "error" in result:
            if result["error"] == "authorization_pending":
                # User hasn't completed authentication yet
                return {
                    "success": False,
                    "pending": True,
                    "message": "Waiting for user to complete authentication"
                }
            elif result["error"] == "expired_token":
                # Device code expired
                metadata.pop("device_code_flow", None)
                project.metadata_json = metadata
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Device code expired. Please initiate authentication again."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("error_description", f"Authentication failed: {result['error']}")
                )
        else:
            return {
                "success": False,
                "pending": True,
                "message": "Authentication in progress"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to poll device code status: {str(e)}"
        )

