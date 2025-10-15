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
    "Migrate Project Subscription",
    "Migrate Resource Group", 
    "Migrate Project Name",
    "Appliance Type",
    "Appliance Name",
    "APP Subscription ID",
    "APP TARGET REGION",
    "Cache Storage Resource Group",
    "Cache Storage Account"
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
    "Target Disk Type",
    "Migrate Project Name"
]

SERVERS_OPTIONAL_COLUMNS = [
    # Recovery vault will be auto-discovered from migrate project
]

# Column mapping from Excel display names to internal model fields
SERVERS_COLUMN_MAPPING = {
    "Target Machine": "machine_name",
    "Target Subscription": "target_subscription",
    "Target Region": "target_region",
    "Target RG": "target_rg",
    "Target VNet": "target_vnet",
    "Target Subnet": "target_subnet",
    "Target Machine SKU": "target_machine_sku",
    "Target Disk Type": "target_disk_type",
    "Migrate Project Name": "migrate_project_name"
}

# Backward compatibility aliases
LAYER2_REQUIRED_COLUMNS = SERVERS_REQUIRED_COLUMNS
LAYER2_OPTIONAL_COLUMNS = SERVERS_OPTIONAL_COLUMNS
LAYER2_COLUMN_MAPPING = SERVERS_COLUMN_MAPPING

# =============================================================================
# Consolidated (Combined Landing Zone + Servers) Configuration
# =============================================================================

# Consolidated columns combine both landing zone and server information in one Excel file
CONSOLIDATED_REQUIRED_COLUMNS = LANDING_ZONE_CSV_COLUMNS + SERVERS_REQUIRED_COLUMNS
CONSOLIDATED_OPTIONAL_COLUMNS = LANDING_ZONE_OPTIONAL_COLUMNS + SERVERS_OPTIONAL_COLUMNS
CONSOLIDATED_COLUMN_MAPPING = {**SERVERS_COLUMN_MAPPING}  # For now, use servers mapping

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

# Quota thresholds (minimum available for warning)
QUOTA_WARNING_THRESHOLD = 10  # vCPUs
QUOTA_CRITICAL_THRESHOLD = 5  # vCPUs

# Appliance health check thresholds (currently used by validators)
APPLIANCE_CPU_WARNING = 80  # percent
APPLIANCE_MEMORY_WARNING = 85  # percent
APPLIANCE_DISK_WARNING = 90  # percent

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
# Validation Rules
# =============================================================================

# Maximum number of machines to validate in one batch
MAX_MACHINES_PER_BATCH = 100

# Maximum number of projects to validate in one batch
MAX_PROJECTS_PER_BATCH = 50

# Mock validator default success rate (Used by mock validators)
DEFAULT_MOCK_SUCCESS_RATE = 0.9

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


