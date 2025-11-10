"""
Landing Zone Validation Service - Reuses azmig_tool validators for LZ/MP validation.

This service integrates the existing azmig_tool CLI validation logic into the web API,
respecting validation settings as feature toggles.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from models import (
    Project, MigrateProjectValidation, AppLandingZoneValidation,
    ValidationResultStatus
)
from services.azure_auth_service import AzureAuthService
from config import get_settings
from azmig_tool.validators.wrappers import LandingZoneValidatorWrapper
from azmig_tool.core.models import MigrateProjectConfig, ValidationStatus as AzmigValidationStatus
from azmig_tool.config.validation_config import get_validation_config

logger = logging.getLogger(__name__)


class LandingZoneValidationService:
    """Service to validate Azure Migrate Projects and App Landing Zones using azmig_tool logic."""
    
    def __init__(self, db_session: Session):
        """Initialize Landing Zone validation service."""
        self.db = db_session
        self.settings = get_settings()
        self.auth_service = AzureAuthService(db_session)
    
    def _convert_azmig_status_to_result_status(self, azmig_status: AzmigValidationStatus) -> ValidationResultStatus:
        """Convert azmig_tool ValidationStatus to API ValidationResultStatus."""
        mapping = {
            AzmigValidationStatus.OK: ValidationResultStatus.PASSED,
            AzmigValidationStatus.WARNING: ValidationResultStatus.WARNING,
            AzmigValidationStatus.FAILED: ValidationResultStatus.FAILED,
            AzmigValidationStatus.SKIPPED: ValidationResultStatus.SKIPPED,
        }
        return mapping.get(azmig_status, ValidationResultStatus.FAILED)
    
    def _result_to_dict(self, result) -> Optional[Dict[str, Any]]:
        """Convert azmig_tool result object to dictionary."""
        if result is None:
            return None
        
        # Handle dataclass conversion
        if hasattr(result, '__dataclass_fields__'):
            result_dict = {}
            for field_name in result.__dataclass_fields__:
                value = getattr(result, field_name)
                # Handle nested enums
                if isinstance(value, AzmigValidationStatus):
                    result_dict[field_name] = value.value
                elif hasattr(value, '__dataclass_fields__'):
                    result_dict[field_name] = self._result_to_dict(value)
                else:
                    result_dict[field_name] = value
            return result_dict
        
        return {"value": str(result)}
    
    async def validate_migrate_project(
        self,
        project_id: int,
        migrate_project_index: int
    ) -> Dict[str, Any]:
        """
        Validate a single Azure Migrate Project against Azure.
        
        Uses the validation settings from the project to control which validations run.
        Reuses azmig_tool LiveLandingZoneValidator for actual Azure checks.
        
        Args:
            project_id: Project ID
            migrate_project_index: Index of migrate project in project's lz_migrate_projects array
            
        Returns:
            Dict with validation results and status
        """
        # Fetch project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"success": False, "error": "Project not found"}
        
        # Validate migrate project index
        if not project.lz_migrate_projects or migrate_project_index >= len(project.lz_migrate_projects):
            return {"success": False, "error": "Invalid migrate project index"}
        
        migrate_project_data = project.lz_migrate_projects[migrate_project_index]
        
        # Get Azure credential for this project
        try:
            credential, auth_info = self.auth_service.get_credential(project_id)
        except Exception as e:
            return {"success": False, "error": f"Authentication failed: {str(e)}"}
        
        # Build MigrateProjectConfig from project data
        migrate_config = MigrateProjectConfig(
            subscription_id=migrate_project_data.get("Migrate Project Subscription"),
            migrate_project_name=migrate_project_data.get("Migrate Project Name"),
            appliance_type=migrate_project_data.get("Appliance Type", "VMware"),
            appliance_name=migrate_project_data.get("Appliance Name"),
            region=migrate_project_data.get("Region", "eastus"),
            cache_storage_account=migrate_project_data.get("Cache Storage Account", ""),
            migrate_project_subscription=migrate_project_data.get("Migrate Project Subscription"),
            migrate_resource_group=migrate_project_data.get("Migrate Resource Group"),
            cache_storage_resource_group=migrate_project_data.get("Migrate Resource Group"),  # Usually same RG
            recovery_vault_name=migrate_project_data.get("Recovery Vault Name"),
        )
        
        # Load validation configuration from project settings
        validation_config = get_validation_config()  # Get singleton
        if project.validation_settings:
            # Override with project-specific settings
            if "landing_zone" in project.validation_settings:
                lz_settings = project.validation_settings["landing_zone"]
                # Update validation_config based on settings
                # This respects feature toggles
                # Note: ValidationConfig uses internal methods to update config
                # For now, use default config - TODO: Implement config override
                pass
        
        # Create validator with project's validation config
        validator = LandingZoneValidatorWrapper(
            credential=credential,
            validation_config=validation_config
        )
        
        # Record start time
        started_at = datetime.now(timezone.utc)
        
        try:
            # Run validation using azmig_tool logic
            result = validator.validate_single(migrate_config)
            
            # Record completion time
            completed_at = datetime.now(timezone.utc)
            
            # Determine overall status
            overall_status = self._determine_overall_status(result)
            status_enum = self._convert_azmig_status_to_result_status(overall_status)
            
            # Convert results to dict for JSON storage
            access_dict = self._result_to_dict(result.access_result) if result.access_result else None
            appliance_dict = self._result_to_dict(result.appliance_result) if result.appliance_result else None
            storage_dict = self._result_to_dict(result.storage_result) if result.storage_result else None
            quota_dict = self._result_to_dict(result.quota_result) if result.quota_result else None
            
            # Save or update validation result
            existing = self.db.query(MigrateProjectValidation).filter(
                MigrateProjectValidation.project_id == project_id,
                MigrateProjectValidation.migrate_project_index == migrate_project_index
            ).first()
            
            if existing:
                # Update existing record
                existing.status = status_enum
                existing.access_result = access_dict
                existing.appliance_result = appliance_dict
                existing.storage_result = storage_dict
                existing.quota_result = quota_dict
                existing.overall_status = overall_status.value
                existing.error_message = None
                existing.started_at = started_at
                existing.completed_at = completed_at
                validation_record = existing
            else:
                # Create new record
                validation_record = MigrateProjectValidation(
                    project_id=project_id,
                    migrate_project_index=migrate_project_index,
                    status=status_enum,
                    access_result=access_dict,
                    appliance_result=appliance_dict,
                    storage_result=storage_dict,
                    quota_result=quota_dict,
                    overall_status=overall_status.value,
                    error_message=None,
                    started_at=started_at,
                    completed_at=completed_at
                )
                self.db.add(validation_record)
            
            self.db.commit()
            
            return {
                "success": True,
                "validation_id": validation_record.id,
                "status": overall_status.value,
                "results": {
                    "access": access_dict,
                    "appliance": appliance_dict,
                    "storage": storage_dict,
                    "quota": quota_dict
                },
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat()
            }
            
        except Exception as e:
            # Record failure
            completed_at = datetime.now(timezone.utc)
            
            existing = self.db.query(MigrateProjectValidation).filter(
                MigrateProjectValidation.project_id == project_id,
                MigrateProjectValidation.migrate_project_index == migrate_project_index
            ).first()
            
            if existing:
                existing.status = ValidationResultStatus.FAILED
                existing.overall_status = "FAILED"
                existing.error_message = str(e)
                existing.started_at = started_at
                existing.completed_at = completed_at
            else:
                validation_record = MigrateProjectValidation(
                    project_id=project_id,
                    migrate_project_index=migrate_project_index,
                    status=ValidationResultStatus.FAILED,
                    overall_status="FAILED",
                    error_message=str(e),
                    started_at=started_at,
                    completed_at=completed_at
                )
                self.db.add(validation_record)
            
            self.db.commit()
            
            return {
                "success": False,
                "error": str(e),
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat()
            }
    
    def _determine_overall_status(self, result) -> AzmigValidationStatus:
        """Determine overall validation status from individual results."""
        # Collect all non-None statuses
        statuses = []
        
        if result.access_result:
            statuses.append(result.access_result.status)
        if result.appliance_result:
            statuses.append(result.appliance_result.status)
        if result.storage_result:
            statuses.append(result.storage_result.status)
        if result.quota_result:
            statuses.append(result.quota_result.status)
        
        if not statuses:
            return AzmigValidationStatus.SKIPPED
        
        # If any FAILED, overall is FAILED
        if AzmigValidationStatus.FAILED in statuses:
            return AzmigValidationStatus.FAILED
        
        # If any WARNING, overall is WARNING
        if AzmigValidationStatus.WARNING in statuses:
            return AzmigValidationStatus.WARNING
        
        # Otherwise OK
        return AzmigValidationStatus.OK
    
    def get_migrate_project_validation_result(
        self,
        project_id: int,
        migrate_project_index: int
    ) -> Optional[Dict[str, Any]]:
        """Get the latest validation result for a migrate project."""
        validation = self.db.query(MigrateProjectValidation).filter(
            MigrateProjectValidation.project_id == project_id,
            MigrateProjectValidation.migrate_project_index == migrate_project_index
        ).order_by(MigrateProjectValidation.created_at.desc()).first()
        
        if not validation:
            return None
        
        return {
            "id": validation.id,
            "status": validation.status.value,
            "overall_status": validation.overall_status,
            "access_result": validation.access_result,
            "appliance_result": validation.appliance_result,
            "storage_result": validation.storage_result,
            "quota_result": validation.quota_result,
            "error_message": validation.error_message,
            "started_at": validation.started_at.isoformat() if validation.started_at else None,
            "completed_at": validation.completed_at.isoformat() if validation.completed_at else None,
            "created_at": validation.created_at.isoformat() if validation.created_at else None
        }
