"""
API endpoints for server configurations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import pandas as pd
import io

from database import get_db
from models import User, ServerConfig, Project
from schemas.server import (
    ServerConfigCreate,
    ServerConfigUpdate,
    ServerConfigResponse,
    ServerConfigListResponse,
    ExcelUploadResponse
)
from utils.security import get_current_user

router = APIRouter()


@router.get("/projects/{project_id}/servers", response_model=ServerConfigListResponse)
async def list_servers(
    project_id: int,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all servers for a project with pagination.
    
    - **project_id**: Project ID to list servers for
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 100)
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
    
    # Query servers
    query = db.query(ServerConfig).filter(ServerConfig.project_id == project_id)
    total = query.count()
    
    # Calculate pagination
    offset = (page - 1) * page_size
    pages = (total + page_size - 1) // page_size
    
    # Fetch servers
    servers = query.order_by(ServerConfig.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "items": servers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.post("/projects/{project_id}/servers/upload", response_model=ExcelUploadResponse)
async def upload_servers_excel(
    project_id: int,
    file: UploadFile = File(...),
    update_existing: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload Excel file with server configurations.
    
    - **project_id**: Project ID to upload servers for
    - **file**: Excel file (.xlsx) with server configurations
    - **update_existing**: If True, update existing servers by name
    
    **Required Excel columns:**
    - Target Machine Name
    - Target Region
    - Target Subscription
    - Target RG
    - Target Vnet
    - Target Subnet
    - Target Machine Sku
    - Target Disk Type
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
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_columns = [
            "Target Machine Name",
            "Target Region",
            "Target Subscription",
            "Target RG",
            "Target Vnet",
            "Target Subnet",
            "Target Machine Sku",
            "Target Disk Type"
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Process rows
        servers_created = 0
        servers_updated = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row["Target Machine Name"]):
                    continue
                
                # Check if server exists
                existing_server = db.query(ServerConfig).filter(
                    ServerConfig.project_id == project_id,
                    ServerConfig.target_machine_name == row["Target Machine Name"]
                ).first()
                
                if existing_server and update_existing:
                    # Update existing server
                    existing_server.target_region = str(row["Target Region"])
                    existing_server.target_subscription = str(row["Target Subscription"])
                    existing_server.target_resource_group = str(row["Target RG"])
                    existing_server.target_vnet = str(row["Target Vnet"])
                    existing_server.target_subnet = str(row["Target Subnet"])
                    existing_server.target_machine_sku = str(row["Target Machine Sku"])
                    existing_server.target_disk_type = str(row["Target Disk Type"])
                    servers_updated += 1
                elif not existing_server:
                    # Create new server
                    new_server = ServerConfig(
                        project_id=project_id,
                        target_machine_name=str(row["Target Machine Name"]),
                        target_region=str(row["Target Region"]),
                        target_subscription=str(row["Target Subscription"]),
                        target_resource_group=str(row["Target RG"]),
                        target_vnet=str(row["Target Vnet"]),
                        target_subnet=str(row["Target Subnet"]),
                        target_machine_sku=str(row["Target Machine Sku"]),
                        target_disk_type=str(row["Target Disk Type"])
                    )
                    db.add(new_server)
                    servers_created += 1
                else:
                    errors.append(f"Row {idx + 2}: Server '{row['Target Machine Name']}' already exists (use update_existing=true to update)")
                    
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        # Commit all changes
        db.commit()
        
        return {
            "message": f"Successfully processed {servers_created + servers_updated} servers",
            "servers_created": servers_created,
            "servers_updated": servers_updated,
            "errors": errors
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like missing columns)
        raise
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse Excel file: {str(e)}"
        )
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"Excel upload error: {error_detail}")  # Debug logging
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Excel file: {error_detail}"
        )


@router.post("/servers", response_model=ServerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new server configuration.
    """
    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == server_data.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {server_data.project_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    # Check for duplicate server name in project
    existing = db.query(ServerConfig).filter(
        ServerConfig.project_id == server_data.project_id,
        ServerConfig.target_machine_name == server_data.target_machine_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server '{server_data.target_machine_name}' already exists in this project"
        )
    
    # Create server
    new_server = ServerConfig(**server_data.dict())
    db.add(new_server)
    db.commit()
    db.refresh(new_server)
    
    return new_server


@router.get("/servers/{server_id}", response_model=ServerConfigResponse)
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific server configuration by ID.
    """
    server = db.query(ServerConfig).filter(ServerConfig.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found"
        )
    
    # Check permissions via project
    project = db.query(Project).filter(Project.id == server.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this server"
        )
    
    return server


@router.put("/servers/{server_id}", response_model=ServerConfigResponse)
async def update_server(
    server_id: int,
    server_data: ServerConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a server configuration.
    """
    server = db.query(ServerConfig).filter(ServerConfig.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found"
        )
    
    # Check permissions via project
    project = db.query(Project).filter(Project.id == server.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this server"
        )
    
    # Update fields
    update_data = server_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)
    
    db.commit()
    db.refresh(server)
    
    return server


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a server configuration.
    """
    server = db.query(ServerConfig).filter(ServerConfig.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found"
        )
    
    # Check permissions via project
    project = db.query(Project).filter(Project.id == server.project_id).first()
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this server"
        )
    
    db.delete(server)
    db.commit()
    
    return None
