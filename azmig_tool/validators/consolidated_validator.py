"""
Consolidated Validator - Combines Landing Zone and Server validation
This validator processes consolidated templates that include both Landing Zone and Server configurations
"""
from typing import List, Dict, Optional, Any
from azure.identity import DefaultAzureCredential

from ..models import (
    ConsolidatedMigrationConfig,
    MigrateProjectConfig,
    MigrationConfig,
    ProjectReadinessResult,
    MachineValidationReport,
    ValidationResult,
    ValidationStage
)
from ..config.validation_config import ValidationConfig, get_validation_config
from .landing_zone_validator import LandingZoneValidator
from .servers_validator import ServersValidator


class ConsolidatedValidator:
    """
    Validator that processes consolidated configurations containing both 
    Landing Zone and Server information, running validations in proper sequence
    """

    def __init__(self, credential: Optional[DefaultAzureCredential] = None, 
                 validation_config: Optional[ValidationConfig] = None):
        """
        Initialize consolidated validator

        Args:
            credential: Azure credential (uses DefaultAzureCredential if not provided)
            validation_config: Validation configuration (loads default if not provided)
        """
        self.credential = credential or DefaultAzureCredential()
        self.validation_config = validation_config or get_validation_config()
        
        # Initialize sub-validators
        self.lz_validator = LandingZoneValidator(credential, validation_config)
        self.server_validator = ServersValidator(credential, validation_config)

    def validate_all(self, configs: List[ConsolidatedMigrationConfig]) -> Dict[str, Any]:
        """
        Validate all consolidated configurations
        First runs Landing Zone validation, then Server validation

        Args:
            configs: List of consolidated configurations

        Returns:
            Dictionary containing both LZ and Server validation results
        """
        results = {
            'landing_zone_results': [],
            'server_results': [],
            'summary': {
                'total_configs': len(configs),
                'lz_passed': 0,
                'lz_failed': 0,
                'server_passed': 0,
                'server_failed': 0
            }
        }

        # Extract unique Landing Zone configurations
        lz_configs_map = self._extract_unique_lz_configs(configs)
        lz_configs = list(lz_configs_map.values())

        # Step 1: Validate Landing Zones first
        print(f"[blue]Step 1: Validating {len(lz_configs)} unique Landing Zone configurations[/blue]")
        
        lz_results = []
        for lz_config in lz_configs:
            lz_result = self.lz_validator.validate_project(lz_config)
            lz_results.append(lz_result)
            results['landing_zone_results'].append(lz_result)
            
            if lz_result.is_ready():
                results['summary']['lz_passed'] += 1
            else:
                results['summary']['lz_failed'] += 1

        # Create LZ results lookup by project key
        lz_results_lookup = {
            self._get_project_key(r.config): r for r in lz_results
        }

        # Step 2: Validate Servers (only if LZ validation passed or warnings only)
        print(f"\n[blue]Step 2: Validating {len(configs)} server configurations[/blue]")
        
        for config in configs:
            project_key = self._get_project_key_from_consolidated(config)
            lz_result = lz_results_lookup.get(project_key)
            
            # Check if we should proceed with server validation
            if lz_result and (lz_result.is_ready() or 
                             lz_result.overall_status.value != 'FAILED'):
                
                # Convert to server config and validate using individual validation methods
                server_config = config.to_migration_config()
                server_results = self.server_validator.validate_all([server_config])
                
                # Get the validation results for this machine
                machine_validations = server_results.get(server_config.target_machine_name, [])
                
                # Create a machine validation report
                overall_status = "PASSED" if all(v.passed for v in machine_validations) else "FAILED"
                server_result = MachineValidationReport(
                    config=server_config,
                    validations=machine_validations,
                    overall_status=overall_status
                )
                results['server_results'].append(server_result)
                
                if server_result.is_valid():
                    results['summary']['server_passed'] += 1
                else:
                    results['summary']['server_failed'] += 1
            else:
                # Create a failed result for skipped server validation
                server_config = config.to_migration_config()
                skip_reason = f"Skipped due to Landing Zone validation failure: {project_key}"
                if lz_result:
                    skip_reason += f" - {', '.join(lz_result.get_blockers())}"
                
                skipped_result = MachineValidationReport(
                    config=server_config,
                    validations=[ValidationResult(
                        stage=ValidationStage.LANDING_ZONE_DEPENDENCY,
                        passed=False,
                        message=skip_reason
                    )],
                    overall_status="FAILED"
                )
                results['server_results'].append(skipped_result)
                results['summary']['server_failed'] += 1

        return results

    def _extract_unique_lz_configs(self, configs: List[ConsolidatedMigrationConfig]) -> Dict[str, MigrateProjectConfig]:
        """
        Extract unique Landing Zone configurations from consolidated configs
        
        Args:
            configs: List of consolidated configurations
            
        Returns:
            Dictionary mapping project keys to unique MigrateProjectConfig objects
        """
        lz_configs_map = {}
        
        for config in configs:
            project_key = self._get_project_key_from_consolidated(config)
            if project_key not in lz_configs_map:
                lz_configs_map[project_key] = config.to_migrate_project_config()
                
        return lz_configs_map

    def _get_project_key(self, lz_config: MigrateProjectConfig) -> str:
        """Generate unique key for Landing Zone project"""
        return f"{lz_config.migrate_project_subscription}_{lz_config.migrate_project_name}_{lz_config.region}"

    def _get_project_key_from_consolidated(self, config: ConsolidatedMigrationConfig) -> str:
        """Generate unique key for Landing Zone project from consolidated config"""
        return f"{config.migrate_project_subscription}_{config.migrate_project_name}_{config.target_region}"

    def validate_single(self, config: ConsolidatedMigrationConfig) -> Dict[str, Any]:
        """
        Validate a single consolidated configuration
        
        Args:
            config: Single consolidated configuration
            
        Returns:
            Dictionary containing both LZ and Server validation results
        """
        return self.validate_all([config])