"""
Service layer for running Azure validations.

This wraps the existing validators from azmig_tool/validators/wrappers for use in Celery tasks.
"""

import sys
import os
from typing import Dict, List, Any
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
    ValidationStatus
)


class ValidationService:
    """
    Service to run Azure validations using existing validators.
    """
    
    def __init__(self, db_session=None):
        """Initialize validation service."""
        self.db = db_session or SessionLocal()
        self.credential = None
        self.validation_config = get_validation_config()
    
    def _get_credential(self):
        """Get Azure credential (cached)."""
        if self.credential is None:
            self.credential = DefaultAzureCredential()
        return self.credential
    
    def validate_landing_zone(self, project_id: int, job_id: int) -> Dict[str, Any]:
        """
        Run landing zone (Layer 1) validation for a project.
        
        Args:
            project_id: Project ID to validate
            job_id: Validation job ID
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Get landing zone config
            lz_config = self.db.query(LandingZoneConfig).filter(
                LandingZoneConfig.project_id == project_id
            ).first()
            
            if not lz_config:
                return {
                    "success": False,
                    "error": "Landing zone configuration not found"
                }
            
            # Convert to MigrateProjectConfig
            # Note: Using project's subscription for all resources
            # Region should be extracted from migrate project name or defaulted
            migrate_config = MigrateProjectConfig(
                subscription_id=lz_config.project.azure_subscription_id,
                migrate_project_name=lz_config.migrate_project_name,
                appliance_type="vmware",  # Default - could be enhanced to store in DB
                appliance_name=lz_config.appliance_name,
                region="eastus",  # Default region - should match migrate project location
                cache_storage_account=lz_config.cache_storage_account,
                migrate_project_subscription=lz_config.project.azure_subscription_id,
                migrate_resource_group=lz_config.migrate_project_rg,
                cache_storage_resource_group=lz_config.cache_storage_rg,
                recovery_vault_name=lz_config.recovery_vault_name
            )
            
            # Create validator
            validator = LandingZoneValidatorWrapper(
                credential=self._get_credential(),
                validation_config=self.validation_config
            )
            
            # Run validation
            report = validator.validate_all([migrate_config])
            
            # Get the first (and only) project result
            if not report.project_results:
                return {
                    "success": False,
                    "error": "No validation results returned"
                }
            
            result = report.project_results[0]
            
            # Map individual results to database
            validation_results = {
                "access": result.access_result,
                "appliance": result.appliance_result,
                "storage": result.storage_result,
                "quota": result.quota_result
            }
            
            total_validations = 0
            passed = 0
            failed = 0
            
            for validation_type, validation_result in validation_results.items():
                if validation_result is None:
                    continue
                    
                total_validations += 1
                status_ok = validation_result.status.value == "ok"
                if status_ok:
                    passed += 1
                else:
                    failed += 1
                
                lz_result = LZValidationResult(
                    validation_job_id=job_id,
                    project_id=project_id,
                    validation_type=validation_type,
                    status="passed" if status_ok else "failed",
                    message=getattr(validation_result, 'message', ''),
                    details=str(getattr(validation_result, 'details', ''))
                )
                self.db.add(lz_result)
            
            self.db.commit()
            
            return {
                "success": True,
                "all_passed": result.is_ready(),
                "total_validations": total_validations,
                "passed": passed,
                "failed": failed
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_servers(self, project_id: int, job_id: int) -> Dict[str, Any]:
        """
        Run server (Layer 2) validation for a project.
        
        Args:
            project_id: Project ID to validate
            job_id: Validation job ID
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Get server configs
            server_configs = self.db.query(ServerConfig).filter(
                ServerConfig.project_id == project_id
            ).all()
            
            if not server_configs:
                return {
                    "success": False,
                    "error": "No server configurations found"
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
                credential=self._get_credential(),
                validation_config=self.validation_config
            )
            
            # Run validation
            report = validator.validate_all_servers(migration_configs)
            
            # Store results in database
            total_validations = 0
            passed = 0
            failed = 0
            
            for server_config, server_result in zip(server_configs, report.server_results):
                # Map individual results to database
                validation_results = {
                    "region": server_result.region_result,
                    "resource_group": server_result.resource_group_result,
                    "vnet": server_result.vnet_result,
                    "vmsku": server_result.vmsku_result,
                    "disk": server_result.disk_result,
                    "discovery": server_result.discovery_result,
                    "rbac": server_result.rbac_result
                }
                
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
                        server_config_id=server_config.id,
                        validation_type=validation_type,
                        status="passed" if status_ok else "failed",
                        message=getattr(validation_result, 'message', ''),
                        details=str(getattr(validation_result, 'details', ''))
                    )
                    self.db.add(server_db_result)
            
            self.db.commit()
            
            return {
                "success": True,
                "servers_validated": len(server_configs),
                "total_validations": total_validations,
                "passed": passed,
                "failed": failed
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def close(self):
        """Close database session."""
        if self.db:
            self.db.close()
