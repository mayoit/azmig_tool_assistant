"""
Service layer for running Azure validations.

This wraps the existing validators from azmig_tool/validators/wrappers for use in Celery tasks.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path to import azmig_tool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from azure.identity import DefaultAzureCredential
from azmig_tool.validators.wrappers import LandingZoneValidatorWrapper, ServersValidatorWrapper
from azmig_tool.config.validation_config import get_validation_config
from azmig_tool.core.models import MigrateProjectConfig, MachineConfig

from database import SessionLocal
from models import (
    LandingZoneConfig,
    ServerConfig,
    LZValidationResult,
    ServerValidationResult,
    ValidationJob,
    ValidationStatus,
    ValidationEvent,
    ValidationResultStatus
)
from services.azure_auth_service import AzureAuthService


class ValidationService:
    """
    Service to run Azure validations using existing validators.
    """
    
    def __init__(self, db_session=None):
        """Initialize validation service."""
        self.db = db_session or SessionLocal()
        self.credential = None
        self.validation_config = get_validation_config()
        self.auth_service = AzureAuthService(self.db)
    
    def _get_credential(self, project_id: int):
        """
        Get Azure credential for a specific project.
        
        Uses project-specific authentication configuration.
        """
        try:
            credential, auth_info = self.auth_service.get_credential(project_id)
            return credential
        except Exception as e:
            # Log and re-raise - don't fall back to default credential
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get project {project_id} credential: {e}", exc_info=True)
            raise ValueError(f"Authentication failed for project {project_id}: {str(e)}")
    
    def _get_project_validation_settings(self, project_id: int) -> Dict[str, Any]:
        """
        Get validation settings for a project from metadata_json.
        
        Returns default settings if not configured.
        """
        from models import Project
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.metadata_json:
            return self._get_default_validation_settings()
        
        settings = project.metadata_json.get('validation_settings')
        if not settings:
            return self._get_default_validation_settings()
        
        return settings
    
    def _get_default_validation_settings(self) -> Dict[str, Any]:
        """Return default validation settings."""
        return {
            'global': {
                'fail_fast': False,
                'parallel_execution': True,
                'timeout_seconds': 300
            },
            'landing_zone': {
                'access_validation': {'enabled': True},
                'appliance_health': {'enabled': True},
                'storage_cache': {'enabled': True, 'auto_create_if_missing': True},
                'quota_validation': {'enabled': True}
            },
            'servers': {
                'region_validation': {'enabled': True},
                'resource_group_validation': {'enabled': True},
                'vnet_subnet_validation': {'enabled': True},
                'vm_sku_validation': {'enabled': True},
                'disk_type_validation': {'enabled': True},
                'discovery_validation': {'enabled': True},
                'rbac_validation': {'enabled': False}
            }
        }
    
    def _log_validation_event(
        self,
        job_id: int,
        project_id: int,
        event_name: str,
        event_category: str,
        validation_type: str,
        status: ValidationResultStatus,
        operation_status: str,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict] = None,
        error_message: Optional[str] = None,
        request_payload: Optional[Dict] = None,
        response_payload: Optional[Dict] = None,
        submitted_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        """
        Log a validation event to the validation_events table (Azure Activity Log style).
        
        Each individual validation action (Access, Appliance, Storage, Quota) logs an event.
        """
        duration_ms = None
        if submitted_at and completed_at:
            duration_ms = int((completed_at - submitted_at).total_seconds() * 1000)
        
        event = ValidationEvent(
            validation_job_id=job_id,
            project_id=project_id,
            event_name=event_name,
            event_category=event_category,
            validation_type=validation_type,
            resource_type=resource_type,
            resource_name=resource_name,
            status=status,
            operation_status=operation_status,
            message=message,
            details=details,
            error_message=error_message,
            request_payload=request_payload,
            response_payload=response_payload,
            event_timestamp=datetime.utcnow(),
            submitted_at=submitted_at,
            completed_at=completed_at,
            duration_ms=duration_ms
        )
        self.db.add(event)
    
    def validate_landing_zone(self, project_id: int, job_id: int) -> Dict[str, Any]:
        """
        Run landing zone (Layer 1) validation for a project.
        
        Validates all migrate projects stored in project.metadata_json['lz_migrate_projects'].
        Only runs validations that are enabled in validation settings.
        
        Args:
            project_id: Project ID to validate
            job_id: Validation job ID
            
        Returns:
            Dictionary with validation results
        """
        try:
            from models import Project
            
            # Get project with landing zone configs from metadata
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {
                    "success": False,
                    "error": "Project not found"
                }
            
            # Get validation settings
            validation_settings = self._get_project_validation_settings(project_id)
            lz_settings = validation_settings.get('landing_zone', {})
            
            # Get migrate projects from metadata
            migrate_projects = project.metadata_json.get('lz_migrate_projects', []) if project.metadata_json else []
            
            if not migrate_projects:
                return {
                    "success": False,
                    "error": "No landing zone migrate projects configured"
                }
            
            # Convert to MigrateProjectConfig list
            migrate_configs = []
            for mp in migrate_projects:
                # Get first app landing zone for region info (or default)
                # Support both camelCase and Title Case keys
                app_zones = mp.get('appLandingZones', mp.get('app_landing_zones', []))
                region = app_zones[0].get('Region', app_zones[0].get('region', 'eastus')) if app_zones else 'eastus'
                cache_storage = app_zones[0].get('Cache Storage Account', app_zones[0].get('cacheStorageAccount', '')) if app_zones else ''
                cache_rg = app_zones[0].get('Cache Storage Resource Group', app_zones[0].get('cacheStorageResourceGroup', '')) if app_zones else ''
                cache_subscription = app_zones[0].get('Subscription', app_zones[0].get('subscription', '')) if app_zones else ''
                
                config = MigrateProjectConfig(
                    subscription_id=mp.get('Migrate Project Subscription', mp.get('migrateProjectSubscription', '')),
                    migrate_project_name=mp.get('Migrate Project Name', mp.get('migrateProjectName', '')),
                    appliance_type=mp.get('Appliance Type', mp.get('applianceType', 'vmware')),
                    appliance_name=mp.get('Appliance Name', mp.get('applianceName', '')),
                    region=region,
                    cache_storage_account=cache_storage,
                    migrate_project_subscription=mp.get('Migrate Project Subscription', mp.get('migrateProjectSubscription', '')),
                    migrate_resource_group=mp.get('Migrate Resource Group', mp.get('migrateResourceGroup', '')),
                    cache_storage_resource_group=cache_rg,
                    cache_storage_subscription=cache_subscription,  # App landing zone subscription
                    recovery_vault_name=mp.get('Recovery Vault Name', mp.get('recoveryVaultName', ''))
                )
                migrate_configs.append(config)
            
            # Create validator with settings
            validator = LandingZoneValidatorWrapper(
                credential=self._get_credential(project_id),
                validation_config=self.validation_config
            )
            
            # Run validation
            report = validator.validate_all(migrate_configs)
            
            total_validations = 0
            passed = 0
            failed = 0
            
            # Process results for each migrate project
            for idx, project_result in enumerate(report.project_results):
                migrate_project_name = migrate_configs[idx].migrate_project_name if idx < len(migrate_configs) else f"Project {idx}"
                
                # Only store results for enabled validations
                validation_results = {}
                
                if lz_settings.get('access_validation', {}).get('enabled', True):
                    validation_results['access'] = project_result.access_result
                
                if lz_settings.get('appliance_health', {}).get('enabled', True):
                    validation_results['appliance'] = project_result.appliance_result
                
                if lz_settings.get('storage_cache', {}).get('enabled', True):
                    validation_results['storage'] = project_result.storage_result
                
                if lz_settings.get('quota_validation', {}).get('enabled', True):
                    validation_results['quota'] = project_result.quota_result
                
                # Log event for each validation action
                for validation_type, validation_result in validation_results.items():
                    if validation_result is None:
                        continue
                    
                    total_validations += 1
                    # Fix: Check for "OK" (uppercase) not "ok" (lowercase)
                    status_ok = validation_result.status.value == "OK"
                    if status_ok:
                        passed += 1
                    else:
                        failed += 1
                    
                    # Map validation type to human-readable event name
                    event_names = {
                        'access': 'Access & RBAC Validation',
                        'appliance': 'Appliance Health Check',
                        'storage': 'Storage Cache Validation',
                        'quota': 'Quota Availability Check'
                    }
                    
                    # Determine result status
                    result_status = ValidationResultStatus.PASSED if status_ok else ValidationResultStatus.FAILED
                    
                    # Extract details from validation result
                    result_message = getattr(validation_result, 'message', '')
                    result_details = getattr(validation_result, 'details', {})
                    
                    # Log the validation event (Azure Activity Log style)
                    validation_start = datetime.utcnow()
                    validation_end = datetime.utcnow()
                    
                    self._log_validation_event(
                        job_id=job_id,
                        project_id=project_id,
                        event_name=event_names.get(validation_type, validation_type.title() if validation_type else 'Unknown'),
                        event_category='landing_zone',
                        validation_type=validation_type,
                        status=result_status,
                        operation_status='Completed',
                        resource_type='MigrateProject',
                        resource_name=migrate_project_name,
                        message=result_message,
                        details={'validation_details': str(result_details)} if result_details else None,
                        request_payload={
                            'migrate_project': migrate_project_name,
                            'validation_type': validation_type,
                            'settings': lz_settings.get(f'{validation_type}_validation', {})
                        },
                        response_payload={
                            'status': validation_result.status.value,
                            'message': result_message,
                            'details': str(result_details) if result_details else None
                        },
                        submitted_at=validation_start,
                        completed_at=validation_end
                    )
                    
                    # Store in existing LZValidationResult table for backward compatibility
                    lz_result = LZValidationResult(
                        validation_job_id=job_id,
                        config_id=None,
                        validation_type=validation_type,
                        status="passed" if status_ok else "failed",
                        message=result_message,
                        details={'result': str(result_details)}
                    )
                    self.db.add(lz_result)
            
            # Update job progress
            job = self.db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
            if job:
                job.total_items = total_validations
                job.processed_items = total_validations
                job.passed_items = passed
                job.failed_items = failed
            
            self.db.commit()
            
            return {
                "success": True,
                "all_passed": failed == 0,
                "total_validations": total_validations,
                "passed": passed,
                "failed": failed,
                "migrate_projects_validated": len(migrate_configs)
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def validate_servers(self, project_id: int, job_id: int) -> Dict[str, Any]:
        """
        Run server (Layer 2) validation for a project.
        
        Only runs validations that are enabled in validation settings.
        
        Args:
            project_id: Project ID to validate
            job_id: Validation job ID
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Get validation settings
            validation_settings = self._get_project_validation_settings(project_id)
            server_settings = validation_settings.get('servers', {})
            
            # Get server configs
            server_configs = self.db.query(ServerConfig).filter(
                ServerConfig.project_id == project_id
            ).all()
            
            if not server_configs:
                return {
                    "success": True,  # Not an error if no servers configured yet
                    "warning": "No server configurations found",
                    "servers_validated": 0,
                    "total_validations": 0,
                    "passed": 0,
                    "failed": 0
                }
            
            # Convert to MachineConfig list
            migration_configs = []
            for server in server_configs:
                config = MachineConfig(
                    target_machine_name=server.target_machine_name,
                    target_region=server.target_region,
                    target_subscription=server.target_subscription,
                    target_rg=server.target_resource_group,
                    target_vnet=server.target_vnet,
                    target_subnet=server.target_subnet,
                    target_machine_sku=server.target_machine_sku,
                    target_disk_type=server.target_disk_type
                )
                migration_configs.append(config)
            
            # Create validator
            validator = ServersValidatorWrapper(
                credential=self._get_credential(project_id),
                validation_config=self.validation_config
            )
            
            # Run validation
            report = validator.validate_all_servers(migration_configs)
            
            # Store results in database
            total_validations = 0
            passed = 0
            failed = 0
            
            for server_config, server_result in zip(server_configs, report.server_results):
                # Only store results for enabled validations
                validation_results = {}
                
                if server_settings.get('region_validation', {}).get('enabled', True):
                    validation_results['region'] = server_result.region_result
                
                if server_settings.get('resource_group_validation', {}).get('enabled', True):
                    validation_results['resource_group'] = server_result.resource_group_result
                
                if server_settings.get('vnet_subnet_validation', {}).get('enabled', True):
                    validation_results['vnet'] = server_result.vnet_result
                
                if server_settings.get('vm_sku_validation', {}).get('enabled', True):
                    validation_results['vmsku'] = server_result.vmsku_result
                
                if server_settings.get('disk_type_validation', {}).get('enabled', True):
                    validation_results['disk'] = server_result.disk_result
                
                if server_settings.get('discovery_validation', {}).get('enabled', True):
                    validation_results['discovery'] = server_result.discovery_result
                
                if server_settings.get('rbac_validation', {}).get('enabled', False):
                    validation_results['rbac'] = server_result.rbac_result
                
                for validation_type, validation_result in validation_results.items():
                    if validation_result is None:
                        continue
                    
                    total_validations += 1
                    status_ok = validation_result.status.value == "ok"
                    if status_ok:
                        passed += 1
                    else:
                        failed += 1
                    
                    server_db_result = ServerValidationResult(
                        validation_job_id=job_id,
                        server_id=server_config.id,
                        validation_type=validation_type,
                        status="passed" if status_ok else "failed",
                        message=getattr(validation_result, 'message', ''),
                        details={'result': str(getattr(validation_result, 'details', ''))}
                    )
                    self.db.add(server_db_result)
            
            # Update job progress
            job = self.db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
            if job:
                job.total_items += total_validations
                job.processed_items += total_validations
                job.passed_items += passed
                job.failed_items += failed
            
            self.db.commit()
            
            return {
                "success": True,
                "servers_validated": len(server_configs),
                "total_validations": total_validations,
                "passed": passed,
                "failed": failed
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def close(self):
        """Close database session."""
        if self.db:
            self.db.close()
