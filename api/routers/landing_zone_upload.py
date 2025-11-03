"""
API endpoint for uploading landing zone configuration files (CSV/JSON).
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import csv
import io

from database import get_db
from models import User, Project
from utils.security import get_current_user

router = APIRouter()


def parse_landing_zone_csv(content: str) -> List[Dict[str, Any]]:
    """Parse landing zone CSV file and return list of migrate projects."""
    reader = csv.DictReader(io.StringIO(content))
    
    # Group rows by migrate project
    projects_dict: Dict[str, Dict[str, Any]] = {}
    
    for row in reader:
        migrate_project_name = row.get('Migrate Project Name', '')
        
        if not migrate_project_name:
            continue
            
        if migrate_project_name not in projects_dict:
            projects_dict[migrate_project_name] = {
                'Migrate Project Subscription': row.get('Migrate Project Subscription', ''),
                'Migrate Resource Group': row.get('Migrate Resource Group', ''),
                'Migrate Project Name': migrate_project_name,
                'Appliance Type': row.get('Appliance Type', ''),
                'Appliance Name': row.get('Appliance Name', ''),
                'Recovery Vault Name': row.get('Recovery Vault Name', ''),
                'app_landing_zones': []
            }
        
        # Add application landing zone if subscription ID is present
        subscription_id = row.get('Subscription ID', '')
        if subscription_id:
            app_zone = {
                'Subscription ID': subscription_id,
                'Cache Storage Account': row.get('Cache Storage Account', ''),
                'Region': row.get('Region', ''),
                'Cache Storage Resource Group': row.get('Cache Storage Resource Group', '')
            }
            projects_dict[migrate_project_name]['app_landing_zones'].append(app_zone)
    
    return list(projects_dict.values())


def parse_landing_zone_json(content: str) -> List[Dict[str, Any]]:
    """Parse landing zone JSON file and return list of migrate projects."""
    data = json.loads(content)
    
    # Handle both array and single object
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Check if it's wrapped in a key
        if 'lz_migrate_projects' in data:
            return data['lz_migrate_projects']
        else:
            return [data]
    else:
        raise ValueError("Invalid JSON format")


@router.post("/projects/{project_id}/landing-zones/upload")
async def upload_landing_zone_config(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload landing zone configuration file (CSV or JSON).
    
    Updates the project's metadata_json with lz_migrate_projects data.
    
    **Supported formats:**
    - CSV with columns: Migrate Project Name, Migrate Project Subscription, etc.
    - JSON array of migrate project objects
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
    
    # Read file content
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    
    # Parse based on file extension
    filename = file.filename or ""
    try:
        if filename.endswith('.csv'):
            lz_migrate_projects = parse_landing_zone_csv(content_str)
        elif filename.endswith('.json'):
            lz_migrate_projects = parse_landing_zone_json(content_str)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Please upload CSV or JSON file."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {str(e)}"
        )
    
    # Update project metadata
    if project.metadata_json is None:
        project.metadata_json = {}
    
    project.metadata_json['lz_migrate_projects'] = lz_migrate_projects
    
    # Mark as updated
    from datetime import datetime
    project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return {
        "message": "Landing zone configuration uploaded successfully",
        "project_id": project.id,
        "migrate_projects_count": len(lz_migrate_projects)
    }
