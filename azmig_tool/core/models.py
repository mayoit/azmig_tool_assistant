"""
Data models for Azure Bulk Migration Tool

This module contains all data models for both:
- Layer 1 (Landing Zone / Project Readiness) validation
- Layer 2 (Machine-Level) validation
"""
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


# ============================================================================
# LAYER 2: Machine-Level Validation Models
# ============================================================================

class DiskType(str, Enum):
    """Valid Azure disk types"""
    STANDARD_LRS = "Standard_LRS"
    PREMIUM_LRS = "Premium_LRS"
    STANDARDSSD_LRS = "StandardSSD_LRS"
    PREMIUM_ZRS = "Premium_ZRS"
    STANDARDSSD_ZRS = "StandardSSD_ZRS"


class MigrationType(str, Enum):
    """Migration type selection"""
    NEW_BATCH = "new"
    PATCH_EXISTING = "patch"


class ValidationStage(str, Enum):
    """Validation stages for machine-level checks"""
    EXCEL_STRUCTURE = "excel_structure"
    AZURE_REGION = "azure_region"
    AZURE_RESOURCES = "azure_resources"
    DISK_AND_SKU = "disk_and_sku"
    MIGRATE_DISCOVERY = "migrate_discovery"
    RBAC_TARGET_RG = "rbac_target_rg"
    RBAC_RECOVERY_VAULT = "rbac_recovery_vault"
    LANDING_ZONE_DEPENDENCY = "landing_zone_dependency"
    # Intelligent validation stages
    PROJECT_MATCHING = "project_matching"
    MACHINE_DISCOVERY = "machine_discovery"
    CACHE_STORAGE = "cache_storage"
    RECOVERY_VAULT = "recovery_vault"
    CONFIGURATION_VALIDATION = "configuration_validation"


# ============================================================================
# LAYER 1: Landing Zone / Project Readiness Models
# ============================================================================

class ApplianceType(str, Enum):
    """Azure Migrate appliance types"""
    VMWARE = "VMware"
    HYPERV = "HyperV"
    PHYSICAL = "Physical"
    AGENTLESS = "Agentless"
    AGENT_BASED = "Agent-based"
    OTHER = "Other"


class HealthStatus(str, Enum):
    """Appliance health status"""
    HEALTHY = "Healthy"
    WARNING = "Warning"
    UNHEALTHY = "Unhealthy"
    CRITICAL = "Critical"
    UNKNOWN = "Unknown"


class ValidationStatus(str, Enum):
    """Validation status for Layer 1 checks"""
    OK = "OK"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class MigrationConfig:
    """Configuration for a single machine migration"""
    machine_name: str  # Single machine name (same for source and target)
    target_region: str
    target_subscription: str
    target_rg: str
    target_vnet: str
    target_subnet: str
    target_machine_sku: str
    target_disk_type: str
    migrate_project_name: str  # Required for intelligent matching with landing zone configs

    # Note: Recovery vault info is retrieved from migrate project during LZ validation

    def __post_init__(self):
        """Validate basic field formats"""
        # Validate disk type
        if self.target_disk_type not in [dt.value for dt in DiskType]:
            raise ValueError(
                f"Invalid disk type: {self.target_disk_type}. "
                f"Must be one of {[dt.value for dt in DiskType]}"
            )


@dataclass
class ConsolidatedMigrationConfig:
    """Consolidated configuration for both Landing Zone and Server migration"""
    # Landing Zone fields (from MigrateProjectConfig)
    migrate_project_subscription: str  # Subscription where Migrate project resides
    migrate_project_name: str
    appliance_type: str
    appliance_name: str
    cache_storage_account: str
    cache_storage_resource_group: str
    migrate_resource_group: str

    # Server migration fields (from MigrationConfig)
    machine_name: str  # Single machine name (same for source and target)
    target_region: str
    target_subscription: str
    target_rg: str
    target_vnet: str
    target_subnet: str
    target_machine_sku: str
    target_disk_type: str

    # Note: Recovery vault info is retrieved from migrate project during LZ validation

    def __post_init__(self):
        """Validate basic field formats"""
        # Normalize region
        self.target_region = self.target_region.lower().strip()

        # Validate disk type
        if self.target_disk_type not in [dt.value for dt in DiskType]:
            raise ValueError(
                f"Invalid disk type: {self.target_disk_type}. "
                f"Must be one of {[dt.value for dt in DiskType]}"
            )

    @property
    def appliance_type_enum(self) -> ApplianceType:
        """Convert appliance type string to enum"""
        type_map = {
            "vmware": ApplianceType.VMWARE,
            "hyperv": ApplianceType.HYPERV,
            "physical": ApplianceType.PHYSICAL,
            "agentless": ApplianceType.AGENTLESS,
            "agent-based": ApplianceType.AGENT_BASED,
            "agent based": ApplianceType.AGENT_BASED,
            "other": ApplianceType.OTHER
        }
        return type_map.get(self.appliance_type.lower().strip(), ApplianceType.OTHER)

    def to_migrate_project_config(self) -> 'MigrateProjectConfig':
        """Extract Landing Zone configuration"""
        return MigrateProjectConfig(
            subscription_id=self.target_subscription,  # Use target subscription for project
            migrate_project_name=self.migrate_project_name,
            appliance_type=self.appliance_type,
            appliance_name=self.appliance_name,
            region=self.target_region,
            cache_storage_account=self.cache_storage_account,
            cache_storage_resource_group=self.cache_storage_resource_group,
            migrate_project_subscription=self.migrate_project_subscription,
            migrate_resource_group=self.migrate_resource_group
        )

    def to_migration_config(self) -> 'MigrationConfig':
        """Extract Server migration configuration"""
        return MigrationConfig(
            machine_name=self.machine_name,
            target_region=self.target_region,
            target_subscription=self.target_subscription,
            target_rg=self.target_rg,
            target_vnet=self.target_vnet,
            target_subnet=self.target_subnet,
            target_machine_sku=self.target_machine_sku,
            target_disk_type=self.target_disk_type,
            migrate_project_name=self.migrate_project_name
        )


@dataclass
class ValidationResult:
    """Result of a validation stage"""
    stage: ValidationStage
    passed: bool
    message: str
    details: Optional[dict] = None


@dataclass
class MachineDiscoveryInfo:
    """Information about machine discovery status in Azure Migrate"""
    machine_name: str
    discovered: bool
    ip_address: Optional[str] = None
    datacenter_location: Optional[str] = None
    os_type: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_mb: Optional[int] = None
    disk_count: Optional[int] = None
    last_seen: Optional[str] = None
    discovery_source: Optional[str] = None  # appliance name


@dataclass
class MachineValidationReport:
    """Validation report for a single machine"""
    config: MigrationConfig
    validations: List[ValidationResult]
    overall_status: str  # "PASSED", "FAILED", "WARNING"
    # Intelligent validation fields
    discovery_info: Optional[MachineDiscoveryInfo] = None
    matched_project: Optional[str] = None  # Project name that was matched
    cache_storage: Optional[str] = None  # Cache storage account name
    recovery_vault: Optional[str] = None  # Recovery vault name

    def is_valid(self) -> bool:
        """Check if all validations passed"""
        return all(v.passed for v in self.validations)

    def get_failed_validations(self) -> List[ValidationResult]:
        """Get list of failed validations"""
        return [v for v in self.validations if not v.passed]


@dataclass
class AzureMigrateProject:
    """Azure Migrate project information"""
    name: str
    resource_group: str
    subscription_id: str
    location: str
    project_id: Optional[str] = None


@dataclass
class ReplicationCache:
    """Azure Site Recovery cache/staging configuration"""
    name: str
    resource_group: str
    storage_account: str
    subscription_id: str


# ============================================================================
# LAYER 1: Landing Zone Configuration & Info Models
# ============================================================================

@dataclass
class MigrateProjectConfig:
    """Configuration for Azure Migrate project readiness validation"""
    subscription_id: str
    migrate_project_name: str
    appliance_type: str  # Will be converted to ApplianceType enum
    appliance_name: str
    region: str
    cache_storage_account: str
    migrate_project_subscription: str  # Subscription where Migrate project resides
    migrate_resource_group: str
    cache_storage_resource_group: str  # Resource group for cache storage account
    # Auto-discovered from migrate project, but accepting from CSV for compatibility
    recovery_vault_name: Optional[str] = None

    # Optional fields - recovery vault will be auto-discovered from migrate project

    def __post_init__(self):
        """Validate and normalize data"""
        self.region = self.region.lower().strip()
        self.subscription_id = self.subscription_id.strip()

    @property
    def appliance_type_enum(self) -> ApplianceType:
        """Convert appliance type string to enum"""
        type_map = {
            "vmware": ApplianceType.VMWARE,
            "hyperv": ApplianceType.HYPERV,
            "physical": ApplianceType.PHYSICAL,
            "agentless": ApplianceType.AGENTLESS,
            "agent-based": ApplianceType.AGENT_BASED,
            "agent based": ApplianceType.AGENT_BASED,
            "other": ApplianceType.OTHER
        }
        return type_map.get(self.appliance_type.lower().strip(), ApplianceType.OTHER)


@dataclass
class ApplianceInfo:
    """Information about an Azure Migrate appliance"""
    name: str
    health_status: HealthStatus
    appliance_type: ApplianceType
    subscription_id: str
    resource_group: str
    region: str
    alerts: List[str] = field(default_factory=list)
    last_heartbeat: Optional[str] = None
    version: Optional[str] = None

    def needs_attention(self) -> bool:
        """Check if appliance needs attention"""
        return self.health_status in [HealthStatus.UNHEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL] or len(self.alerts) > 0


@dataclass
class StorageCacheInfo:
    """Information about cache storage account"""
    account_name: str
    subscription_id: str
    resource_group: str
    region: str
    sku: str = "Standard_LRS"
    exists: bool = False
    created_by_tool: bool = False


@dataclass
class QuotaInfo:
    """vCPU quota information for a region"""
    subscription_id: str
    region: str
    family: str  # e.g., "standardDSv3Family"
    total_quota: int
    current_usage: int
    available: int

    def is_sufficient(self, required_vcpus: int) -> bool:
        """Check if quota is sufficient for required vCPUs"""
        return self.available >= required_vcpus


# ============================================================================
# LAYER 1: Landing Zone Validation Result Models
# ============================================================================

@dataclass
class AccessValidationResult:
    """Result of access and permissions validation"""
    subscription_id: str
    migrate_project_name: str
    status: ValidationStatus
    has_contributor_migrate_project: bool = False
    has_contributor_recovery_vault: bool = False
    has_reader_subscription: bool = False
    message: str = ""
    details: dict = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if all required permissions are present"""
        return (self.has_contributor_migrate_project and
                self.has_reader_subscription and
                self.status == ValidationStatus.OK)


@dataclass
class ApplianceHealthResult:
    """Result of appliance health validation"""
    subscription_id: str
    status: ValidationStatus
    appliances: List[ApplianceInfo] = field(default_factory=list)
    unhealthy_count: int = 0
    message: str = ""

    def get_unhealthy_appliances(self) -> List[ApplianceInfo]:
        """Get list of unhealthy appliances"""
        return [a for a in self.appliances if a.needs_attention()]


@dataclass
class StorageCacheResult:
    """Result of storage cache validation"""
    subscription_id: str
    region: str
    status: ValidationStatus
    storage_info: Optional[StorageCacheInfo] = None
    message: str = ""
    auto_created: bool = False


@dataclass
class QuotaValidationResult:
    """Result of quota validation"""
    subscription_id: str
    region: str
    status: ValidationStatus
    quotas: List[QuotaInfo] = field(default_factory=list)
    insufficient_families: List[str] = field(default_factory=list)
    recommended_skus: List[str] = field(default_factory=list)
    message: str = ""

    def has_sufficient_quota(self) -> bool:
        """Check if quota is sufficient"""
        return len(self.insufficient_families) == 0


@dataclass
class ProjectReadinessResult:
    """Consolidated result for a single Azure Migrate project"""
    config: MigrateProjectConfig
    access_result: Optional[AccessValidationResult] = None
    appliance_result: Optional[ApplianceHealthResult] = None
    storage_result: Optional[StorageCacheResult] = None
    quota_result: Optional[QuotaValidationResult] = None
    overall_status: ValidationStatus = ValidationStatus.SKIPPED
    validation_timestamp: Optional[str] = None

    def __post_init__(self):
        """Calculate overall status after initialization"""
        statuses = []

        if self.access_result:
            statuses.append(self.access_result.status)

        if self.appliance_result:
            statuses.append(self.appliance_result.status)

        if self.storage_result:
            statuses.append(self.storage_result.status)

        if self.quota_result:
            statuses.append(self.quota_result.status)

        if not statuses:
            self.overall_status = ValidationStatus.SKIPPED
        elif any(s == ValidationStatus.FAILED for s in statuses):
            self.overall_status = ValidationStatus.FAILED
        elif any(s == ValidationStatus.WARNING for s in statuses):
            self.overall_status = ValidationStatus.WARNING
        else:
            self.overall_status = ValidationStatus.OK

    def is_ready(self) -> bool:
        """Check if project is ready for migration"""
        if not (self.access_result and self.access_result.is_valid()):
            return False
        if not (self.storage_result and self.storage_result.status == ValidationStatus.OK):
            return False
        return self.overall_status == ValidationStatus.OK

    def get_blockers(self) -> List[str]:
        """Get list of blocking issues"""
        blockers = []

        if self.access_result and not self.access_result.is_valid():
            blockers.append(f"Access: {self.access_result.message}")

        if self.appliance_result and self.appliance_result.status == ValidationStatus.FAILED:
            blockers.append(f"Appliance: {self.appliance_result.message}")

        if self.storage_result and self.storage_result.status == ValidationStatus.FAILED:
            blockers.append(f"Storage: {self.storage_result.message}")

        if self.quota_result and not self.quota_result.has_sufficient_quota():
            blockers.append(f"Quota: {self.quota_result.message}")

        return blockers


@dataclass
class LandingZoneValidationReport:
    """Complete Landing Zone validation report"""
    project_results: List[ProjectReadinessResult] = field(default_factory=list)
    total_projects: int = 0
    ready_projects: int = 0
    failed_projects: int = 0
    warning_projects: int = 0
    validation_timestamp: Optional[str] = None

    def add_result(self, result: ProjectReadinessResult):
        """Add a project result and update counts"""
        self.project_results.append(result)
        self.total_projects += 1

        if result.is_ready():
            self.ready_projects += 1
        elif result.overall_status == ValidationStatus.FAILED:
            self.failed_projects += 1
        elif result.overall_status == ValidationStatus.WARNING:
            self.warning_projects += 1

    def get_summary(self) -> dict:
        """Get summary statistics"""
        return {
            "total_projects": self.total_projects,
            "ready": self.ready_projects,
            "failed": self.failed_projects,
            "warnings": self.warning_projects,
            "success_rate": f"{(self.ready_projects / self.total_projects * 100):.1f}%" if self.total_projects > 0 else "0%"
        }


@dataclass
class MachineConfig:
    """Configuration for individual machine validation (alias for MigrationConfig)"""
    target_machine_name: str
    target_region: str  
    target_subscription: str
    target_rg: str
    target_vnet: str
    target_subnet: str
    target_machine_sku: str
    target_disk_type: str


@dataclass 
class RegionValidationResult:
    """Result of region validation"""
    machine_name: str
    region: str
    subscription_id: str
    status: ValidationStatus
    is_available: bool
    services_available: bool
    sku_available: Optional[bool]
    message: str
    available_regions: List[str] = field(default_factory=list)


@dataclass
class ResourceGroupValidationResult:
    """Result of resource group validation"""
    machine_name: str
    resource_group: str
    subscription_id: str
    status: ValidationStatus
    exists: bool
    has_required_permissions: bool
    region_match: bool
    follows_naming_convention: bool
    message: str
    suggested_action: Optional[str] = None


@dataclass
class SubnetInfo:
    """Subnet information"""
    name: str
    address_prefix: str
    available_ips: int
    has_nsg: bool
    has_route_table: bool


@dataclass
class VNetValidationResult:
    """Result of VNet validation"""
    machine_name: str
    vnet_name: str
    subnet_name: str
    resource_group: str
    subscription_id: str
    status: ValidationStatus
    vnet_exists: bool
    subnet_exists: bool
    subnet_info: Optional[SubnetInfo]
    region_match: bool
    has_nsg: bool
    message: str
    suggested_action: Optional[str] = None


@dataclass
class VMSkuInfo:
    """VM SKU information"""
    name: str
    vcpus: int
    memory_mb: int
    max_data_disks: int
    temp_disk_size_mb: int


@dataclass
class VMSkuValidationResult:
    """Result of VM SKU validation"""
    machine_name: str
    target_sku: str
    region: str
    subscription_id: str
    status: ValidationStatus
    is_available: bool
    sku_info: Optional[VMSkuInfo]
    supports_premium_storage: bool
    supports_nested_virtualization: bool
    message: str
    suggested_skus: List[str] = field(default_factory=list)
    cost_optimization_notes: List[str] = field(default_factory=list)


@dataclass
class DiskValidationResult:
    """Result of disk validation"""
    machine_name: str
    target_disk_type: str
    region: str
    subscription_id: str
    status: ValidationStatus
    is_supported: bool
    is_available_in_region: bool
    performance_tier: Optional[str]
    message: str
    alternative_disk_types: List[str] = field(default_factory=list)


@dataclass
class DiscoveryValidationResult:
    """Result of discovery validation"""
    machine_name: str
    migrate_project: str
    subscription_id: str
    status: ValidationStatus
    is_discovered: bool
    message: str
    last_heartbeat: Optional[str] = None
    discovery_status: Optional[str] = None
    suggested_action: Optional[str] = None


@dataclass
class RbacValidationResult:
    """Result of RBAC validation"""
    machine_name: str
    resource_scope: str
    subscription_id: str
    status: ValidationStatus
    has_required_permissions: bool
    message: str
    missing_permissions: List[str] = field(default_factory=list)
    current_roles: List[str] = field(default_factory=list)
    suggested_action: Optional[str] = None


# Backward compatibility alias
Layer1ValidationReport = LandingZoneValidationReport
