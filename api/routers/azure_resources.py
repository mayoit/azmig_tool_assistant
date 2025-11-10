"""
API endpoints for Azure resource discovery.

Provides endpoints to fetch subscriptions, resource groups, VNets, and subnets
for authenticated Azure projects.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Project, User
from services.azure_resources_service import AzureResourcesService
from utils.security import get_current_user


router = APIRouter(prefix="/projects", tags=["azure-resources"])


@router.get("/{project_id}/azure/subscriptions")
async def get_subscriptions(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of Azure subscriptions accessible with configured credentials.
    
    Requires:
    - Project must have Azure authentication configured
    - User must have access to the project
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
    
    try:
        resources_service = AzureResourcesService(db)
        subscriptions = resources_service.get_subscriptions(project_id)
        return {"subscriptions": subscriptions, "count": len(subscriptions)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subscriptions: {str(e)}"
        )


@router.get("/{project_id}/azure/resource-groups")
async def get_resource_groups(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of resource groups in a subscription.
    
    Requires:
    - Project must have Azure authentication configured
    - User must have access to the project
    - subscription_id query parameter
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
    
    try:
        resources_service = AzureResourcesService(db)
        resource_groups = resources_service.get_resource_groups(project_id, subscription_id)
        return {"resource_groups": resource_groups, "count": len(resource_groups)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch resource groups: {str(e)}"
        )


@router.get("/{project_id}/azure/vnets")
async def get_vnets(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    resource_group: Optional[str] = Query(None, description="Optional resource group filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of Virtual Networks in a subscription or resource group.
    
    Requires:
    - Project must have Azure authentication configured
    - User must have access to the project
    - subscription_id query parameter
    
    Optional:
    - resource_group: Filter VNets by resource group
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
    
    try:
        resources_service = AzureResourcesService(db)
        vnets = resources_service.get_vnets(project_id, subscription_id, resource_group)
        return {"vnets": vnets, "count": len(vnets)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch VNets: {str(e)}"
        )


@router.get("/{project_id}/azure/subnets")
async def get_subnets(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    resource_group: str = Query(..., description="Resource group name"),
    vnet_name: str = Query(..., description="Virtual Network name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of subnets in a specific Virtual Network.
    
    Requires:
    - Project must have Azure authentication configured
    - User must have access to the project
    - subscription_id, resource_group, and vnet_name query parameters
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
    
    try:
        resources_service = AzureResourcesService(db)
        subnets = resources_service.get_subnets(
            project_id, 
            subscription_id, 
            resource_group, 
            vnet_name
        )
        return {"subnets": subnets, "count": len(subnets)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subnets: {str(e)}"
        )


@router.get("/{project_id}/azure/locations")
async def get_locations(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available Azure locations for a subscription.
    
    Requires:
    - Project must have Azure authentication configured
    - User must have access to the project
    - subscription_id query parameter
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
    
    try:
        resources_service = AzureResourcesService(db)
        locations = resources_service.get_locations(project_id, subscription_id)
        return {"locations": locations, "count": len(locations)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch locations: {str(e)}"
        )


@router.get("/{project_id}/azure/storage-accounts")
async def get_storage_accounts(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    resource_group: Optional[str] = Query(None, description="Optional resource group filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of storage accounts in a subscription or resource group.
    
    Requires:
    - Project must have Azure authentication configured
    - User must have access to the project
    - subscription_id query parameter
    
    Optional:
    - resource_group: Filter storage accounts by resource group
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
    
    try:
        resources_service = AzureResourcesService(db)
        storage_accounts = resources_service.get_storage_accounts(
            project_id, 
            subscription_id, 
            resource_group
        )
        return {"storage_accounts": storage_accounts, "count": len(storage_accounts)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch storage accounts: {str(e)}"
        )


@router.get("/{project_id}/azure/storage-accounts")
async def get_storage_accounts(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    resource_group: Optional[str] = Query(None, description="Optional resource group filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of storage accounts in a subscription or resource group.
    
    Requires:
    - Project must have Azure authentication configured
    - User must have access to the project
    - subscription_id query parameter
    
    Optional:
    - resource_group: Filter storage accounts by resource group
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
    
    try:
        resources_service = AzureResourcesService(db)
        storage_accounts = resources_service.get_storage_accounts(
            project_id, 
            subscription_id, 
            resource_group
        )
        return {"storage_accounts": storage_accounts, "count": len(storage_accounts)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch storage accounts: {str(e)}"
        )


@router.get("/{project_id}/azure/storage-accounts")
async def get_storage_accounts(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    resource_group: Optional[str] = Query(None, description="Optional resource group filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of storage accounts in a subscription or resource group.
    
    Requires:
    - Project must have Azure authentication configured
    - User must have access to the project
    - subscription_id query parameter
    
    Optional:
    - resource_group: Filter storage accounts by resource group
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
    
    try:
        resources_service = AzureResourcesService(db)
        storage_accounts = resources_service.get_storage_accounts(
            project_id, 
            subscription_id, 
            resource_group
        )
        return {"storage_accounts": storage_accounts, "count": len(storage_accounts)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch storage accounts: {str(e)}"
        )


@router.get("/{project_id}/azure/migrate-projects")
async def get_migrate_projects(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    resource_group: str = Query(..., description="Resource group containing migrate projects"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of Azure Migrate projects in a resource group."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")
    
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this project")
    
    try:
        resources_service = AzureResourcesService(db)
        migrate_projects = resources_service.get_migrate_projects(project_id, subscription_id, resource_group)
        return {"migrate_projects": migrate_projects, "count": len(migrate_projects)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch migrate projects: {str(e)}")


@router.get("/{project_id}/azure/migrate-appliances")
async def get_migrate_appliances(
    project_id: int,
    subscription_id: str = Query(..., description="Target Azure subscription ID"),
    resource_group: str = Query(..., description="Resource group containing the migrate project"),
    migrate_project_name: str = Query(..., description="Name of the Azure Migrate project"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of Azure Migrate appliances for a specific migrate project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")
    
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this project")
    
    try:
        resources_service = AzureResourcesService(db)
        appliances = resources_service.get_migrate_appliances(project_id, subscription_id, resource_group, migrate_project_name)
        return {"appliances": appliances, "count": len(appliances)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch migrate appliances: {str(e)}")
