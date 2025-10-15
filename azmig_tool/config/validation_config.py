"""
Validation Configuration Loader (Backward Compatibility)

⚠️  LEGACY SYSTEM - For backward compatibility only
    Primary validation settings are now managed via ValidationSettings model (see models.py)
    This module exists to support existing code that references ValidationConfig

This module loads and provides access to legacy validation configuration settings
that allow users to enable/disable specific validation checks.

For new development, use:
- ValidationSettings model for project-persistent validation configuration
- Project-level settings that are saved with Azure Migrate project data
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ValidationConfig:
    """
    Holds validation configuration settings

    ⚠️  LEGACY CLASS - For backward compatibility only
        Use ValidationSettings model (see models.py) for new development

    This class provides basic validation configuration functionality for
    existing code that still references the old validation config system.
    """
    config_data: Dict[str, Any] = field(default_factory=dict)

    def apply_profile(self, profile_name: str) -> bool:
        """
        Apply a validation profile to current configuration
        
        Args:
            profile_name: Name of the profile to apply
            
        Returns:
            True if profile was applied successfully, False otherwise
        """
        if "profiles" not in self.config_data:
            return False
            
        profiles = self.config_data.get("profiles", {})
        if profile_name not in profiles:
            return False
            
        profile_config = profiles[profile_name]
        
        # Apply profile overrides
        if "overrides" in profile_config:
            for key_path, value in profile_config["overrides"].items():
                self._set_nested_value(key_path, value)
                
        return True
    
    def _set_nested_value(self, key_path: str, value: Any):
        """
        Set a nested dictionary value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., "landing_zone.access_validation.enabled")
            value: Value to set
        """
        keys = key_path.split(".")
        data = self.config_data
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
            
        # Set the final value
        data[keys[-1]] = value

    def _get_nested_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a nested dictionary value using dot notation

        Args:
            key_path: Dot-separated path (e.g., "landing_zone.access_validation.enabled")
            default: Default value if key not found

        Returns:
            Value at the key path or default
        """
        keys = key_path.split(".")
        data = self.config_data

        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return default

        return data

    # ========================================================================
    # Landing Zone Validation Settings
    # ========================================================================

    def is_access_validation_enabled(self) -> bool:
        """Check if Landing Zone access validation is enabled"""
        return self._get_nested_value("landing_zone.access_validation.enabled", True)

    def is_migrate_project_rbac_enabled(self) -> bool:
        """Check if migrate project RBAC check is enabled"""
        return self._get_nested_value(
            "landing_zone.access_validation.checks.migrate_project_rbac.enabled", True
        )

    def is_recovery_vault_rbac_enabled(self) -> bool:
        """Check if recovery vault RBAC check is enabled"""
        return self._get_nested_value(
            "landing_zone.access_validation.checks.recovery_vault_rbac.enabled", True
        )

    def is_subscription_rbac_enabled(self) -> bool:
        """Check if subscription RBAC check is enabled"""
        return self._get_nested_value(
            "landing_zone.access_validation.checks.subscription_rbac.enabled", True
        )

    def is_appliance_health_enabled(self) -> bool:
        """Check if appliance health validation is enabled"""
        return self._get_nested_value("landing_zone.appliance_health.enabled", True)

    def is_storage_cache_enabled(self) -> bool:
        """Check if storage cache validation is enabled"""
        return self._get_nested_value("landing_zone.storage_cache.enabled", True)

    def should_auto_create_storage(self) -> bool:
        """Check if storage account should be auto-created"""
        return self._get_nested_value(
            "landing_zone.storage_cache.auto_create_if_missing", False
        )

    def is_quota_validation_enabled(self) -> bool:
        """Check if quota validation is enabled"""
        return self._get_nested_value("landing_zone.quota_validation.enabled", True)

    # ========================================================================
    # Servers (Machine-Level) Validation Settings
    # ========================================================================

    def is_region_validation_enabled(self) -> bool:
        """Check if region validation is enabled"""
        return self._get_nested_value("servers.region_validation.enabled", True)

    def is_resource_group_validation_enabled(self) -> bool:
        """Check if resource group validation is enabled"""
        return self._get_nested_value("servers.resource_group_validation.enabled", True)

    def is_vnet_subnet_validation_enabled(self) -> bool:
        """Check if VNet/Subnet validation is enabled"""
        return self._get_nested_value("servers.vnet_subnet_validation.enabled", True)

    def is_vm_sku_validation_enabled(self) -> bool:
        """Check if VM SKU validation is enabled"""
        return self._get_nested_value("servers.vm_sku_validation.enabled", True)

    def is_disk_type_validation_enabled(self) -> bool:
        """Check if disk type validation is enabled"""
        return self._get_nested_value("servers.disk_type_validation.enabled", True)

    def is_discovery_validation_enabled(self) -> bool:
        """Check if discovery validation is enabled"""
        return self._get_nested_value("servers.discovery_validation.enabled", True)

    def is_servers_rbac_validation_enabled(self) -> bool:
        """Check if servers RBAC validation is enabled"""
        return self._get_nested_value("servers.rbac_validation.enabled", True)

    # ========================================================================
    # Global Settings
    # ========================================================================

    def is_fail_fast_enabled(self) -> bool:
        """Check if fail-fast mode is enabled"""
        return self._get_nested_value("global.fail_fast", False)

    def is_parallel_execution_enabled(self) -> bool:
        """Check if parallel execution is enabled"""
        return self._get_nested_value("global.parallel_execution", False)

    def get_timeout_seconds(self) -> int:
        """Get validation timeout in seconds"""
        return self._get_nested_value("global.timeout_seconds", 300)

    def is_retry_enabled(self) -> bool:
        """Check if retry on failure is enabled"""
        return self._get_nested_value("global.retry_on_failure.enabled", False)

    def get_max_retries(self) -> int:
        """Get maximum number of retries"""
        return self._get_nested_value("global.retry_on_failure.max_retries", 3)

    def get_retry_delay_seconds(self) -> int:
        """Get retry delay in seconds"""
        return self._get_nested_value("global.retry_on_failure.retry_delay_seconds", 5)

    def get_logging_level(self) -> str:
        """Get logging level"""
        return self._get_nested_value("global.logging.level", "INFO")

    def should_log_to_file(self) -> bool:
        """Check if logging to file is enabled"""
        return self._get_nested_value("global.logging.log_to_file", False)

    def get_log_file_path(self) -> str:
        """Get log file path"""
        return self._get_nested_value("global.logging.log_file_path", "validation.log")


class ValidationConfigLoader:
    """
    Loads validation configuration from YAML file

    ⚠️  LEGACY CLASS - For backward compatibility only
        Use ValidationSettings model (see models.py) for new development

    This class provides functionality to load legacy validation_config.yaml files
    for existing code that still references the old validation config system.
    """

    DEFAULT_CONFIG_FILENAME = "validation_config.yaml"

    @staticmethod
    def load(config_path: Optional[str] = None) -> ValidationConfig:
        """
        Load validation configuration from file

        Args:
            config_path: Path to config file. If None, searches for default config.

        Returns:
            ValidationConfig object

        Raises:
            FileNotFoundError: If config file not found
            yaml.YAMLError: If config file is invalid YAML
        """
        # Determine config file path
        if config_path is None:
            config_path = ValidationConfigLoader._find_default_config()

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Validation config file not found: {config_path}\n"
                f"Please create a '{ValidationConfigLoader.DEFAULT_CONFIG_FILENAME}' "
                f"file or specify a custom path."
            )

        # Load YAML config
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        if config_data is None:
            config_data = {}

        return ValidationConfig(config_data=config_data)

    @staticmethod
    def _find_default_config() -> str:
        """
        Find default validation config file

        Searches in:
        1. Current working directory
        2. Package root directory
        3. User home directory

        Returns:
            Path to config file
        """
        search_paths = [
            # Current working directory
            Path.cwd() / ValidationConfigLoader.DEFAULT_CONFIG_FILENAME,
            # Package root (parent of azmig_tool directory)
            Path(__file__).parent.parent /
            ValidationConfigLoader.DEFAULT_CONFIG_FILENAME,
            # User home directory
            Path.home() / ".azmig" / ValidationConfigLoader.DEFAULT_CONFIG_FILENAME,
        ]

        for path in search_paths:
            if path.exists():
                return str(path)

        # Return path to package root as default (even if doesn't exist)
        return str(search_paths[1])

    @staticmethod
    def create_default_config(output_path: Optional[str] = None) -> str:
        """
        Create a default validation config file

        Args:
            output_path: Path where to create config file. If None, uses default location.

        Returns:
            Path to created config file
        """
        if output_path is None:
            output_path = ValidationConfigLoader._find_default_config()

        # Check if file already exists
        if os.path.exists(output_path):
            raise FileExistsError(
                f"Validation config file already exists: {output_path}\n"
                f"Delete it first or specify a different output path."
            )

        # Get default config template from package
        template_path = Path(__file__).parent.parent / \
            ValidationConfigLoader.DEFAULT_CONFIG_FILENAME

        if template_path.exists() and str(template_path) != output_path:
            # Copy template to output path
            import shutil
            shutil.copy(str(template_path), output_path)
        else:
            # Create minimal default config
            default_config = {
                "landing_zone": {
                    "access_validation": {"enabled": True},
                    "appliance_health": {"enabled": True},
                    "storage_cache": {"enabled": True},
                    "quota_validation": {"enabled": True}
                },
                "servers": {
                    "region_validation": {"enabled": True},
                    "resource_group_validation": {"enabled": True},
                    "vnet_subnet_validation": {"enabled": True},
                    "vm_sku_validation": {"enabled": True},
                    "disk_type_validation": {"enabled": True},
                    "discovery_validation": {"enabled": True},
                    "rbac_validation": {"enabled": True}
                },
                "global": {
                    "fail_fast": False,
                    "parallel_execution": False
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False)

        return output_path


# Singleton instance for easy access
_config_instance: Optional[ValidationConfig] = None


def get_validation_config(config_path: Optional[str] = None, force_reload: bool = False) -> ValidationConfig:
    """
    Get validation configuration (singleton pattern)

    Args:
        config_path: Path to config file (only used on first load or force_reload)
        force_reload: Force reload config from file

    Returns:
        ValidationConfig object
    """
    global _config_instance

    if _config_instance is None or force_reload:
        _config_instance = ValidationConfigLoader.load(config_path)

    return _config_instance


def reset_validation_config():
    """Reset the singleton config instance (useful for testing)"""
    global _config_instance
    _config_instance = None
