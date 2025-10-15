"""
Project management models for Azure Bulk Migration Tool

This module handles project-based workflow where each migration batch
is organized in its own project folder with saved authentication and configuration.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import json
import os
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status types"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class AuthMethod(str, Enum):
    """Authentication methods"""
    AZURE_CLI = "azure_cli"
    MANAGED_IDENTITY = "managed_identity"
    SERVICE_PRINCIPAL = "service_principal"
    INTERACTIVE = "interactive"
    DEVICE_CODE = "device_code"
    DEFAULT = "default"


@dataclass
class ProjectAuthConfig:
    """Authentication configuration for a project"""
    auth_method: AuthMethod
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    # Note: We don't store client_secret for security - user will be prompted
    subscription_id: Optional[str] = None
    created_at: Optional[str] = None
    # Token caching for interactive authentication
    cached_token: Optional[str] = None
    token_expires_at: Optional[str] = None
    refresh_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "auth_method": self.auth_method.value,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "subscription_id": self.subscription_id,
            "created_at": self.created_at or datetime.now().isoformat(),
            "cached_token": self.cached_token,
            "token_expires_at": self.token_expires_at,
            "refresh_token": self.refresh_token
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectAuthConfig':
        """Create from dictionary"""
        return cls(
            auth_method=AuthMethod(data["auth_method"]),
            tenant_id=data.get("tenant_id"),
            client_id=data.get("client_id"),
            subscription_id=data.get("subscription_id"),
            created_at=data.get("created_at"),
            cached_token=data.get("cached_token"),
            token_expires_at=data.get("token_expires_at"),
            refresh_token=data.get("refresh_token")
        )

    def cache_token(self, access_token: str, expires_at: datetime, refresh_token: Optional[str] = None):
        """Cache authentication token in project configuration"""
        self.cached_token = access_token
        self.token_expires_at = expires_at.isoformat()
        self.refresh_token = refresh_token

    def is_token_valid(self) -> bool:
        """Check if cached token is still valid"""
        if not self.cached_token or not self.token_expires_at:
            return False

        try:
            expires_at = datetime.fromisoformat(self.token_expires_at)
            # Consider token valid if it expires more than 5 minutes from now
            return expires_at > datetime.now().replace(microsecond=0) + timedelta(minutes=5)
        except (ValueError, AttributeError):
            return False

    def clear_token_cache(self):
        """Clear cached authentication token"""
        self.cached_token = None
        self.token_expires_at = None
        self.refresh_token = None


@dataclass
class ValidationSettings:
    """Validation configuration settings for a project"""
    # Global settings
    fail_fast: bool = False
    parallel_execution: bool = False
    timeout_seconds: int = 300

    # Landing Zone validations
    lz_access_validation: bool = True
    lz_migrate_project_rbac: bool = True
    lz_recovery_vault_rbac: bool = True
    lz_subscription_rbac: bool = True
    lz_appliance_health: bool = True
    lz_storage_cache: bool = True
    lz_quota_validation: bool = True
    lz_auto_create_storage: bool = False

    # Server validations
    server_region_validation: bool = True
    server_resource_group_validation: bool = True
    server_vnet_subnet_validation: bool = True
    server_vm_sku_validation: bool = True
    server_disk_type_validation: bool = True
    server_discovery_validation: bool = True
    server_rbac_validation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "global": {
                "fail_fast": self.fail_fast,
                "parallel_execution": self.parallel_execution,
                "timeout_seconds": self.timeout_seconds
            },
            "landing_zone": {
                "access_validation": {"enabled": self.lz_access_validation},
                "access_validation_checks": {
                    "migrate_project_rbac": {"enabled": self.lz_migrate_project_rbac},
                    "recovery_vault_rbac": {"enabled": self.lz_recovery_vault_rbac},
                    "subscription_rbac": {"enabled": self.lz_subscription_rbac}
                },
                "appliance_health": {"enabled": self.lz_appliance_health},
                "storage_cache": {
                    "enabled": self.lz_storage_cache,
                    "auto_create_if_missing": self.lz_auto_create_storage
                },
                "quota_validation": {"enabled": self.lz_quota_validation}
            },
            "servers": {
                "region_validation": {"enabled": self.server_region_validation},
                "resource_group_validation": {"enabled": self.server_resource_group_validation},
                "vnet_subnet_validation": {"enabled": self.server_vnet_subnet_validation},
                "vm_sku_validation": {"enabled": self.server_vm_sku_validation},
                "disk_type_validation": {"enabled": self.server_disk_type_validation},
                "discovery_validation": {"enabled": self.server_discovery_validation},
                "rbac_validation": {"enabled": self.server_rbac_validation}
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationSettings':
        """Create from dictionary (backward compatible)"""
        global_config = data.get("global", {})
        lz_config = data.get("landing_zone", {})
        server_config = data.get("servers", {})
        lz_checks = lz_config.get("access_validation_checks", {})
        storage_config = lz_config.get("storage_cache", {})

        return cls(
            # Global settings
            fail_fast=global_config.get("fail_fast", False),
            parallel_execution=global_config.get("parallel_execution", False),
            timeout_seconds=global_config.get("timeout_seconds", 300),

            # Landing Zone settings
            lz_access_validation=lz_config.get(
                "access_validation", {}).get("enabled", True),
            lz_migrate_project_rbac=lz_checks.get(
                "migrate_project_rbac", {}).get("enabled", True),
            lz_recovery_vault_rbac=lz_checks.get(
                "recovery_vault_rbac", {}).get("enabled", True),
            lz_subscription_rbac=lz_checks.get(
                "subscription_rbac", {}).get("enabled", True),
            lz_appliance_health=lz_config.get(
                "appliance_health", {}).get("enabled", True),
            lz_storage_cache=storage_config.get("enabled", True),
            lz_quota_validation=lz_config.get(
                "quota_validation", {}).get("enabled", True),
            lz_auto_create_storage=storage_config.get(
                "auto_create_if_missing", False),

            # Server settings
            server_region_validation=server_config.get(
                "region_validation", {}).get("enabled", True),
            server_resource_group_validation=server_config.get(
                "resource_group_validation", {}).get("enabled", True),
            server_vnet_subnet_validation=server_config.get(
                "vnet_subnet_validation", {}).get("enabled", True),
            server_vm_sku_validation=server_config.get(
                "vm_sku_validation", {}).get("enabled", True),
            server_disk_type_validation=server_config.get(
                "disk_type_validation", {}).get("enabled", True),
            server_discovery_validation=server_config.get(
                "discovery_validation", {}).get("enabled", True),
            server_rbac_validation=server_config.get(
                "rbac_validation", {}).get("enabled", True)
        )

    @classmethod
    def create_default(cls) -> 'ValidationSettings':
        """Create default validation settings"""
        return cls()

    @classmethod
    def create_quick_profile(cls) -> 'ValidationSettings':
        """Create quick validation profile (fewer checks)"""
        return cls(
            lz_migrate_project_rbac=False,
            lz_recovery_vault_rbac=False,
            lz_subscription_rbac=False,
            server_rbac_validation=False,
            server_discovery_validation=False
        )

    @classmethod
    def create_full_profile(cls) -> 'ValidationSettings':
        """Create full validation profile (all checks enabled)"""
        return cls(
            fail_fast=False,
            parallel_execution=True
        )


@dataclass
class ProjectConfig:
    """Configuration for a migration project"""
    project_name: str
    project_path: Path
    migration_type: str  # "new" or "patch"
    status: ProjectStatus
    auth_config: ProjectAuthConfig
    created_at: str
    updated_at: str
    description: Optional[str] = None

    # File tracking
    lz_validation_files: List[str] = field(default_factory=list)
    server_validation_files: List[str] = field(default_factory=list)

    # Validation results metadata
    last_lz_validation: Optional[str] = None
    last_server_validation: Optional[str] = None

    # Validated LZ configuration data (to avoid re-entry during server validation)
    # Stores successfully validated migrate projects with grouped app landing zones
    lz_migrate_projects: List[Dict[str, Any]] = field(
        default_factory=list)  # Grouped structure with app_landing_zones

    # Validation configuration settings (persistent per project)
    validation_settings: ValidationSettings = field(
        default_factory=ValidationSettings.create_default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "project_name": self.project_name,
            "project_path": str(self.project_path),
            "migration_type": self.migration_type,
            "status": self.status.value,
            "auth_config": self.auth_config.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "description": self.description,
            "lz_validation_files": self.lz_validation_files,
            "server_validation_files": self.server_validation_files,
            "last_lz_validation": self.last_lz_validation,
            "last_server_validation": self.last_server_validation,
            "lz_migrate_projects": self.lz_migrate_projects,
            "validation_settings": self.validation_settings.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Create from dictionary"""
        return cls(
            project_name=data["project_name"],
            project_path=Path(data["project_path"]),
            migration_type=data["migration_type"],
            status=ProjectStatus(data["status"]),
            auth_config=ProjectAuthConfig.from_dict(data["auth_config"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            description=data.get("description"),
            lz_validation_files=data.get("lz_validation_files", []),
            server_validation_files=data.get("server_validation_files", []),
            last_lz_validation=data.get("last_lz_validation"),
            last_server_validation=data.get("last_server_validation"),
            lz_migrate_projects=data.get("lz_migrate_projects", []),
            validation_settings=ValidationSettings.from_dict(
                data.get("validation_settings", {}))
        )

    @property
    def lz_folder(self) -> Path:
        """Path to Landing Zone validation files"""
        return self.project_path / "landing_zone"

    @property
    def servers_folder(self) -> Path:
        """Path to server validation files"""
        return self.project_path / "servers"

    @property
    def results_folder(self) -> Path:
        """Path to validation results"""
        return self.project_path / "results"

    @property
    def config_file(self) -> Path:
        """Path to project configuration file"""
        return self.project_path / "project.json"


class ProjectManager:
    """Manages migration projects and their configurations"""

    def __init__(self, workspace_root: Optional[Path] = None):
        """Initialize project manager with workspace root"""
        self.workspace_root = workspace_root or Path.cwd() / "migration_projects"
        self.workspace_root.mkdir(exist_ok=True)

    def list_projects(self) -> List[ProjectConfig]:
        """List all existing projects"""
        projects = []

        if not self.workspace_root.exists():
            return projects

        for project_dir in self.workspace_root.iterdir():
            if project_dir.is_dir():
                config_file = project_dir / "project.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        projects.append(ProjectConfig.from_dict(data))
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        # Skip invalid project configurations
                        continue

        return sorted(projects, key=lambda p: p.updated_at, reverse=True)

    def create_project(
        self,
        project_name: str,
        auth_config: ProjectAuthConfig,
        description: Optional[str] = None
    ) -> ProjectConfig:
        """Create a new migration project"""
        # Sanitize project name for directory
        safe_name = "".join(c for c in project_name if c.isalnum()
                            or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')

        project_path = self.workspace_root / safe_name

        # Ensure unique project path
        counter = 1
        original_path = project_path
        while project_path.exists():
            project_path = Path(f"{original_path}_{counter}")
            counter += 1

        # Create project structure
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "landing_zone").mkdir(exist_ok=True)
        (project_path / "servers").mkdir(exist_ok=True)
        (project_path / "results").mkdir(exist_ok=True)

        # Create project configuration
        now = datetime.now().isoformat()
        project_config = ProjectConfig(
            project_name=project_name,
            project_path=project_path,
            migration_type="new",
            status=ProjectStatus.CREATED,
            auth_config=auth_config,
            created_at=now,
            updated_at=now,
            description=description
        )

        # Save project configuration
        self.save_project(project_config)

        return project_config

    def save_project(self, project: ProjectConfig) -> None:
        """Save project configuration"""
        project.updated_at = datetime.now().isoformat()

        with open(project.config_file, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, indent=2)

    def load_project(self, project_path: Path) -> Optional[ProjectConfig]:
        """Load project configuration from path"""
        config_file = project_path / "project.json"

        if not config_file.exists():
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectConfig.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def update_project_status(self, project: ProjectConfig, status: ProjectStatus) -> None:
        """Update project status"""
        project.status = status
        self.save_project(project)

    def update_project_tenant_id(self, project: ProjectConfig, tenant_id: str) -> None:
        """Update project's tenant ID in auth config"""
        project.auth_config.tenant_id = tenant_id
        self.save_project(project)

    def update_validation_settings(self, project: ProjectConfig, validation_settings: ValidationSettings) -> None:
        """Update project's validation settings"""
        project.validation_settings = validation_settings
        self.save_project(project)

    def add_validation_file(
        self,
        project: ProjectConfig,
        file_path: str,
        validation_type: str
    ) -> None:
        """Add a validation file to project tracking"""
        if validation_type == "lz" and file_path not in project.lz_validation_files:
            project.lz_validation_files.append(file_path)
            project.last_lz_validation = datetime.now().isoformat()
        elif validation_type == "server" and file_path not in project.server_validation_files:
            project.server_validation_files.append(file_path)
            project.last_server_validation = datetime.now().isoformat()

        self.save_project(project)

    def get_project_by_name(self, name: str) -> Optional[ProjectConfig]:
        """Get project by name"""
        projects = self.list_projects()
        for project in projects:
            if project.project_name.lower() == name.lower():
                return project
        return None

    def add_validated_lz_config(
        self,
        project: ProjectConfig,
        lz_config_data: Dict[str, str]
    ) -> None:
        """Add successfully validated LZ configuration to project with improved grouping structure

        Args:
            project: Project configuration
            lz_config_data: Dictionary with LZ fields matching CSV structure
        """
        migrate_project_name = lz_config_data.get("Migrate Project Name")
        migrate_project_subscription = lz_config_data.get(
            "Migrate Project Subscription")

        # Find existing migrate project entry or create new one
        existing_project = None
        for mp in project.lz_migrate_projects:
            if (mp.get("Migrate Project Name") == migrate_project_name and
                    mp.get("Migrate Project Subscription") == migrate_project_subscription):
                existing_project = mp
                break

        if not existing_project:
            # Create new migrate project entry with the improved structure
            existing_project = {
                "Migrate Project Subscription": migrate_project_subscription,
                "Migrate Resource Group": lz_config_data.get("Migrate Resource Group", ""),
                "Migrate Project Name": migrate_project_name,
                "Appliance Type": lz_config_data.get("Appliance Type", ""),
                "Appliance Name": lz_config_data.get("Appliance Name", ""),
                "Recovery Vault Name": lz_config_data.get("Recovery Vault Name", ""),
                "app_landing_zones": []
            }
            project.lz_migrate_projects.append(existing_project)

        # Add the application landing zone (cache storage) to this migrate project
        app_lz = {
            "Subscription ID": lz_config_data.get("Subscription ID"),
            "Cache Storage Account": lz_config_data.get("Cache Storage Account", ""),
            "Region": lz_config_data.get("Region"),
            "Cache Storage Resource Group": lz_config_data.get("Cache Storage Resource Group", "")
        }

        # Check if this app landing zone already exists (avoid duplicates)
        existing_app_lz = None
        for alz in existing_project["app_landing_zones"]:
            if (alz.get("Subscription ID") == app_lz["Subscription ID"] and
                alz.get("Cache Storage Account") == app_lz["Cache Storage Account"] and
                    alz.get("Region") == app_lz["Region"]):
                existing_app_lz = alz
                break

        if not existing_app_lz:
            existing_project["app_landing_zones"].append(app_lz)

        # Update timestamp and save
        project.last_lz_validation = datetime.now().isoformat()
        self.save_project(project)

    def get_validated_lz_configs(self, project: ProjectConfig) -> Dict[str, Any]:
        """Get all validated LZ configurations for this project"""
        return {
            "migrate_projects": project.lz_migrate_projects
        }

    def has_validated_lz_configs(self, project: ProjectConfig) -> bool:
        """Check if project has any validated LZ configurations"""
        return len(project.lz_migrate_projects) > 0

    def is_appliance_already_validated(self, project: ProjectConfig, appliance_name: str, migrate_project_name: str) -> bool:
        """Check if a specific appliance is already validated in the project"""
        for mp in project.lz_migrate_projects:
            if (mp.get("Migrate Project Name") == migrate_project_name and
                    mp.get("Appliance Name") == appliance_name):
                return True
        return False

    def is_cache_storage_already_validated(self, project: ProjectConfig, storage_account: str, subscription_id: str) -> bool:
        """Check if a specific cache storage account is already validated in the project"""
        for mp in project.lz_migrate_projects:
            for alz in mp.get("app_landing_zones", []):
                if (alz.get("Cache Storage Account") == storage_account and
                        alz.get("Subscription ID") == subscription_id):
                    return True
        return False

    def is_migrate_project_already_validated(self, project: ProjectConfig, migrate_project_name: str, subscription: str) -> bool:
        """Check if a specific migrate project is already validated"""
        for mp in project.lz_migrate_projects:
            if (mp.get("Migrate Project Name") == migrate_project_name and
                    mp.get("Migrate Project Subscription") == subscription):
                return True
        return False

    def get_validated_component_info(self, project: ProjectConfig, component_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get information about a previously validated component"""
        if component_type == "appliance":
            appliance_name = kwargs.get("appliance_name")
            migrate_project_name = kwargs.get("migrate_project_name")
            for mp in project.lz_migrate_projects:
                if (mp.get("Migrate Project Name") == migrate_project_name and
                        mp.get("Appliance Name") == appliance_name):
                    return {
                        "appliance_name": mp.get("Appliance Name"),
                        "appliance_type": mp.get("Appliance Type"),
                        "migrate_project": mp.get("Migrate Project Name"),
                        "validated_at": project.last_lz_validation
                    }

        elif component_type == "cache_storage":
            storage_account = kwargs.get("storage_account")
            subscription_id = kwargs.get("subscription_id")
            for mp in project.lz_migrate_projects:
                for alz in mp.get("app_landing_zones", []):
                    if (alz.get("Cache Storage Account") == storage_account and
                            alz.get("Subscription ID") == subscription_id):
                        return {
                            "storage_account": alz.get("Cache Storage Account"),
                            "resource_group": alz.get("Cache Storage Resource Group"),
                            "region": alz.get("Region"),
                            "subscription": alz.get("Subscription ID"),
                            "validated_at": project.last_lz_validation
                        }

        return None
