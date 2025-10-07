"""
Configuration constants for Azure Bulk Migration Tool
Centralized location for all configuration values, regions, and validation rules
"""

# =============================================================================
# Azure Regions
# =============================================================================

AZURE_REGIONS = [
    # US Regions
    "eastus", "eastus2", "westus", "westus2", "westus3",
    "centralus", "northcentralus", "southcentralus", "westcentralus",

    # Canada
    "canadacentral", "canadaeast",

    # South America
    "brazilsouth", "brazilsoutheast",

    # Europe
    "northeurope", "westeurope",
    "uksouth", "ukwest",
    "francecentral", "francesouth",
    "germanywestcentral", "germanynorth",
    "switzerlandnorth", "switzerlandwest",
    "norwayeast", "norwaywest",
    "swedencentral", "swedensouth",

    # Asia Pacific
    "eastasia", "southeastasia",
    "australiaeast", "australiasoutheast", "australiacentral",
    "japaneast", "japanwest",
    "koreacentral", "koreasouth",
    "southindia", "centralindia", "westindia",

    # Middle East & Africa
    "uaenorth", "uaecentral",
    "southafricanorth", "southafricawest",

    # China (requires special account)
    "chinanorth", "chinaeast", "chinanorth2", "chinaeast2"
]

# =============================================================================
# Landing Zone Configuration Columns
# =============================================================================

LANDING_ZONE_CSV_COLUMNS = [
    "Subscription ID",
    "Migrate Project Name",
    "Appliance Type",
    "Appliance Name",
    "Region",
    "Cache Storage Account",
    "Migrate Project Subscription",
    "Migrate Resource Group"
]

LANDING_ZONE_OPTIONAL_COLUMNS = [
    "Recovery Vault Name"
]

# Backward compatibility aliases
LAYER1_CSV_COLUMNS = LANDING_ZONE_CSV_COLUMNS
LAYER1_OPTIONAL_COLUMNS = LANDING_ZONE_OPTIONAL_COLUMNS

# =============================================================================
# Servers (Machine) Configuration Columns
# =============================================================================

SERVERS_REQUIRED_COLUMNS = [
    "Target Machine",
    "Target Region",
    "Target Subscription",
    "Target RG",
    "Target VNet",
    "Target Subnet",
    "Target Machine SKU",
    "Target Disk Type"
]

SERVERS_OPTIONAL_COLUMNS = [
    "Source Machine",
    "Recovery Vault Name"
]

# Column mapping from Excel display names to internal model fields
SERVERS_COLUMN_MAPPING = {
    "Target Machine": "target_machine_name",
    "Target Region": "target_region",
    "Target Subscription": "target_subscription",
    "Target RG": "target_rg",
    "Target VNet": "target_vnet",
    "Target Subnet": "target_subnet",
    "Target Machine SKU": "target_machine_sku",
    "Target Disk Type": "target_disk_type",
    "Source Machine": "source_machine_name",
    "Recovery Vault Name": "recovery_vault_name"
}

# Backward compatibility aliases
LAYER2_REQUIRED_COLUMNS = SERVERS_REQUIRED_COLUMNS
LAYER2_OPTIONAL_COLUMNS = SERVERS_OPTIONAL_COLUMNS
LAYER2_COLUMN_MAPPING = SERVERS_COLUMN_MAPPING

# =============================================================================
# Azure RBAC Role IDs
# =============================================================================

AZURE_ROLE_IDS = {
    "Owner": "8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
    "Contributor": "b24988ac-6180-42a0-ab88-20f7382dd24c",
    "Reader": "acdd72a7-3385-48ef-bd42-f606fba81ae7",
    "User Access Administrator": "18d7d88d-d35e-4fb5-a5c3-7773c20a72d9",
}

# Required roles for different resources
REQUIRED_ROLES = {
    "resource_group": ["Owner", "Contributor"],
    "recovery_vault": ["Owner", "Contributor"],
    "subscription": ["Owner", "Contributor", "Reader"],
    "migrate_project": ["Owner", "Contributor"]
}

# =============================================================================
# Validation Thresholds
# =============================================================================

# Mock validator default success rate
DEFAULT_MOCK_SUCCESS_RATE = 0.9

# Quota thresholds (minimum available for warning)
QUOTA_WARNING_THRESHOLD = 10  # vCPUs
QUOTA_CRITICAL_THRESHOLD = 5  # vCPUs

# Appliance health check thresholds
APPLIANCE_CPU_WARNING = 80  # percent
APPLIANCE_MEMORY_WARNING = 85  # percent
APPLIANCE_DISK_WARNING = 90  # percent

# =============================================================================
# Storage Configuration
# =============================================================================

# Cache storage account naming rules
CACHE_STORAGE_NAME_MIN_LENGTH = 3
CACHE_STORAGE_NAME_MAX_LENGTH = 24
CACHE_STORAGE_ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"

# Valid storage SKUs for cache storage
VALID_CACHE_STORAGE_SKUS = [
    "Standard_LRS",
    "Standard_GRS",
    "Standard_RAGRS",
    "Premium_LRS"
]

# =============================================================================
# VM SKU Families
# =============================================================================

# Common VM SKU families for quota checking
VM_SKU_FAMILIES = [
    "standardDSv3Family",
    "standardESv3Family",
    "standardFSv2Family",
    "standardDv3Family",
    "standardEv3Family",
    "standardDSv2Family",
    "standardDv2Family",
    "standardB1sFamily",
    "standardB2sFamily",
    "standardB4msFamily",
]

# =============================================================================
# API Configuration
# =============================================================================

# Azure API versions
AZURE_API_VERSIONS = {
    "resource_groups": "2021-04-01",
    "virtual_networks": "2021-05-01",
    "storage_accounts": "2021-09-01",
    "compute": "2021-11-01",
    "migrate": "2020-01-01",
    "recovery_services": "2021-12-01"
}

# Azure Migrate API endpoints
MIGRATE_API_BASE = "https://management.azure.com"
MIGRATE_API_VERSION = "2020-01-01"

# =============================================================================
# Timeouts and Retries
# =============================================================================

# API call timeouts (seconds)
DEFAULT_TIMEOUT = 30
LONG_RUNNING_TIMEOUT = 300

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RETRY_BACKOFF = 2  # exponential backoff multiplier

# =============================================================================
# Output Formatting
# =============================================================================

# Table display limits
MAX_TABLE_ROWS_SUMMARY = 50
MAX_DETAIL_ITEMS = 100

# Truncate long strings in tables
MAX_STRING_LENGTH_TABLE = 50
MAX_STRING_LENGTH_DETAIL = 200

# =============================================================================
# Validation Rules
# =============================================================================

# Excel file size limits (MB)
MAX_EXCEL_SIZE_MB = 50

# Maximum number of machines to validate in one batch
MAX_MACHINES_PER_BATCH = 100

# Maximum number of projects to validate in one batch
MAX_PROJECTS_PER_BATCH = 50

# =============================================================================
# Mock Data Generation
# =============================================================================

# Mock appliance name patterns
MOCK_APPLIANCE_NAME_PATTERNS = [
    "VMwareReplicationAppliance{project}-{index:02d}",
    "HyperVAppliance{project}-{index:02d}",
    "PhysicalServerAppliance{project}-{index:02d}"
]

# Mock quota ranges (min, max available)
MOCK_QUOTA_RANGE = (10, 100)

# Mock storage account name generation
MOCK_STORAGE_PREFIX = "migcache"

# =============================================================================
# File Paths
# =============================================================================

# Default sample file names
SAMPLE_LANDING_ZONE_CSV = "tests/data/sample_migrate_projects.csv"
SAMPLE_LANDING_ZONE_JSON = "tests/data/sample_migrate_projects.json"
SAMPLE_SERVERS_EXCEL = "tests/data/sample_migration.xlsx"
TEMPLATE_LANDING_ZONE_CSV = "examples/template_migrate_projects.csv"

# Backward compatibility aliases
SAMPLE_LAYER1_CSV = SAMPLE_LANDING_ZONE_CSV
SAMPLE_LAYER1_JSON = SAMPLE_LANDING_ZONE_JSON
SAMPLE_LAYER2_EXCEL = SAMPLE_SERVERS_EXCEL
TEMPLATE_LAYER1_CSV = TEMPLATE_LANDING_ZONE_CSV

# =============================================================================
# Logging
# =============================================================================

# Log level for different components
LOG_LEVELS = {
    "validator": "INFO",
    "parser": "INFO",
    "api_client": "WARNING",
    "formatter": "INFO"
}

# =============================================================================
# Feature Flags
# =============================================================================

# Enable/disable features
FEATURES = {
    "auto_remediation": False,  # Auto-fix common issues
    "parallel_validation": True,  # Validate in parallel
    "cache_api_responses": True,  # Cache Azure API responses
    "detailed_logging": False,  # Verbose logging
    "html_reports": False,  # Generate HTML reports (future)
}
