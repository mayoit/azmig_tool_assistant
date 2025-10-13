# Azure Migration Tool - Function Reference Documentation

## Overview
This document provides comprehensive technical documentation for all functions in the Azure Migration Tool, including their purpose, parameters, return values, and call relationships.

## Table of Contents
- [Core CLI Functions](#core-cli-functions)
- [Configuration Management](#configuration-management)
- [Azure API Clients](#azure-api-clients)
- [Validation Framework](#validation-framework)
- [Interactive Wizard](#interactive-wizard)
- [Data Models & Utilities](#data-models--utilities)
- [Authentication & Credentials](#authentication--credentials)
- [Formatters & Output](#formatters--output)

---

## Core CLI Functions

### `azmig_tool/cli.py`

#### `main()`
**Purpose**: Entry point for the CLI application
**Parameters**: None (uses sys.argv)
**Returns**: None (exits with status code)
**Called by**: Command line interface
**Calls**: `parse_args()`, wizard functions

#### `parse_args()`
**Purpose**: Parse command line arguments and validate options
**Parameters**: None
**Returns**: `argparse.Namespace` - Parsed arguments
**Called by**: `main()`
**Calls**: `argparse.ArgumentParser` methods

#### `validate_args(args)`
**Purpose**: Validate command line argument combinations
**Parameters**: 
- `args: argparse.Namespace` - Parsed CLI arguments
**Returns**: `bool` - True if valid, False otherwise
**Called by**: `main()`
**Calls**: Various validation helper functions

---

## Configuration Management

### `azmig_tool/config/parsers.py`

#### `ConfigParser.__init__(config_path: str)`
**Purpose**: Initialize unified configuration parser for CSV/JSON/Excel files
**Parameters**:
- `config_path: str` - Path to configuration file
**Returns**: None
**Called by**: Wizard, CLI functions
**Calls**: `_detect_file_type()`

#### `ConfigParser._detect_file_type()`
**Purpose**: Auto-detect file type (CSV, JSON, Excel) from file extension
**Parameters**: None (uses self.config_path)
**Returns**: `str` - File type ('csv', 'json', 'excel')
**Called by**: `__init__()`
**Calls**: `pathlib.Path.suffix`

#### `ConfigParser.parse()`
**Purpose**: Parse configuration file based on detected type
**Parameters**: None
**Returns**: `Tuple[bool, List[Union[MigrateProjectConfig, MigrationConfig]], List[ValidationResult]]`
**Called by**: Wizard functions, CLI
**Calls**: `_parse_csv()`, `_parse_json()`, `_parse_excel()`

#### `ConfigParser._parse_csv()`
**Purpose**: Parse CSV files for landing zone configurations
**Parameters**: None
**Returns**: `Tuple[bool, List[MigrateProjectConfig], str]`
**Called by**: `parse()`
**Calls**: `pandas.read_csv()`, `_validate_csv_columns()`

#### `ConfigParser._parse_json()`
**Purpose**: Parse JSON files for landing zone configurations
**Parameters**: None
**Returns**: `Tuple[bool, List[MigrateProjectConfig], str]`
**Called by**: `parse()`
**Calls**: `json.load()`, validation methods

#### `ConfigParser._parse_excel()`
**Purpose**: Parse Excel files (servers or consolidated format)
**Parameters**: None
**Returns**: `Tuple[bool, List[MigrationConfig], List[ValidationResult]]`
**Called by**: `parse()`
**Calls**: `detect_excel_format()`, format-specific parsers

#### `ConfigParser.detect_excel_format()`
**Purpose**: Detect Excel format (consolidated vs servers-only)
**Parameters**: None
**Returns**: `str` - Format type ('consolidated', 'servers', 'unknown')
**Called by**: `_parse_excel()`
**Calls**: `pandas.read_excel()`, column analysis

#### `ConfigParser.validate_file_exists()`
**Purpose**: Validate that configuration file exists and is readable
**Parameters**: None
**Returns**: `ValidationResult`
**Called by**: All parse methods
**Calls**: `pathlib.Path.exists()`

### `azmig_tool/config/validation_config.py`

#### `ValidationConfig.__init__(config_data: Dict)`
**Purpose**: Initialize validation configuration with settings
**Parameters**:
- `config_data: Dict` - Configuration dictionary
**Returns**: None
**Called by**: `get_validation_config()`
**Calls**: Profile resolution methods

#### `ValidationConfig.is_*_validation_enabled()`
**Purpose**: Check if specific validation is enabled (multiple methods)
**Parameters**: None
**Returns**: `bool` - True if validation enabled
**Called by**: Validators, wizard functions
**Calls**: Profile and setting resolution

#### `get_validation_config()`
**Purpose**: Singleton factory for validation configuration
**Parameters**: None
**Returns**: `ValidationConfig` - Global configuration instance
**Called by**: All validators, wizard
**Calls**: `ValidationConfig.__init__()`

---

## Azure API Clients

### `azmig_tool/clients/azure_client.py`

#### `AzureRestApiClient.__init__(credential, subscription_id)`
**Purpose**: Initialize REST API client for Azure management operations
**Parameters**:
- `credential: TokenCredential` - Azure authentication credential
- `subscription_id: str` - Target Azure subscription ID
**Returns**: None
**Called by**: Validators, wizard
**Calls**: Credential validation

#### `AzureRestApiClient.get(path, api_version, params)`
**Purpose**: Execute GET request to Azure REST API
**Parameters**:
- `path: str` - API endpoint path
- `api_version: str` - Azure API version
- `params: Dict` - Query parameters (optional)
**Returns**: `Dict[str, Any]` - API response JSON
**Called by**: All API methods
**Calls**: `requests.get()`, authentication headers

#### `AzureRestApiClient.post(path, data, api_version)`
**Purpose**: Execute POST request to Azure REST API
**Parameters**:
- `path: str` - API endpoint path
- `data: Dict` - Request body data
- `api_version: str` - Azure API version
**Returns**: `Dict[str, Any]` - API response JSON
**Called by**: Resource creation methods
**Calls**: `requests.post()`, authentication headers

#### `AzureRestApiClient.list_all(path, api_version, params)`
**Purpose**: List all resources with automatic pagination handling
**Parameters**:
- `path: str` - API endpoint path
- `api_version: str` - Azure API version
- `params: Dict` - Query parameters (optional)
**Returns**: `List[Dict[str, Any]]` - All paginated results
**Called by**: Resource listing methods
**Calls**: `get()`, pagination logic

#### `AzureMigrateApiClient.search_machines_by_name(resource_group, project_name, machine_name)`
**Purpose**: Search for specific machine by name using direct machine API
**Parameters**:
- `resource_group: str` - Resource group name
- `project_name: str` - Azure Migrate project name  
- `machine_name: str` - Machine name to search
**Returns**: `List[Dict[str, Any]]` - Matching machines
**Called by**: Validators, discovery functions
**Calls**: `get()`, fallback to `list_discovered_machines()`

#### `AzureMigrateApiClient.search_machines_by_name_cached(resource_group, project_name, machine_name)`
**Purpose**: Cached version of machine search for bulk operations
**Parameters**: Same as `search_machines_by_name()`
**Returns**: `List[Dict[str, Any]]` - Matching machines from cache
**Called by**: Bulk validation operations
**Calls**: `list_discovered_machines()` with caching

#### `AzureMigrateApiClient.list_discovered_machines(resource_group, project_name, use_cache)`
**Purpose**: List all discovered machines in Azure Migrate project
**Parameters**:
- `resource_group: str` - Resource group name
- `project_name: str` - Project name
- `use_cache: bool` - Use cached results if available
**Returns**: `List[Dict[str, Any]]` - All discovered machines
**Called by**: Machine search functions, validators
**Calls**: `list_all()`, caching logic

#### `AzureMigrateApiClient._add_discovery_status(machine)`
**Purpose**: Add discovery status metadata to machine record
**Parameters**:
- `machine: Dict[str, Any]` - Machine record from Azure API
**Returns**: `Dict[str, Any]` - Machine with discovery status added
**Called by**: Machine search methods
**Calls**: Data analysis of migrationData/discoveryData

#### `AzureMigrateApiClient.get_migrate_projects(resource_group)`
**Purpose**: Get all Azure Migrate projects in resource group
**Parameters**:
- `resource_group: str` - Resource group name
**Returns**: `List[Dict[str, Any]]` - Migrate projects
**Called by**: Project discovery, wizard
**Calls**: `list_all()`

#### `AzureMigrateApiClient.get_migration_appliances(subscription_id, project_name)`
**Purpose**: Get migration appliances using Resource Graph query
**Parameters**:
- `subscription_id: str` - Subscription ID
- `project_name: str` - Project name (optional filter)
**Returns**: `List[Dict[str, Any]]` - Migration appliances
**Called by**: Appliance validation
**Calls**: `post()` to Resource Graph API

#### `AzureMigrateApiClient._parse_resource_graph_appliances(graph_result)`
**Purpose**: Parse Resource Graph response into appliance format
**Parameters**:
- `graph_result: Dict[str, Any]` - Resource Graph API response
**Returns**: `List[Dict[str, Any]]` - Parsed appliances
**Called by**: `get_migration_appliances()`
**Calls**: Data transformation logic

### `azmig_tool/clients/azure_migrate_client.py`

#### `AzureMigrateIntegration.__init__(credential)`
**Purpose**: Initialize Azure Migrate integration for discovery operations
**Parameters**:
- `credential: TokenCredential` - Azure authentication credential
**Returns**: None
**Called by**: Validators, intelligent validator
**Calls**: Credential caching

#### `AzureMigrateIntegration.get_discovered_machines(subscription_id, resource_group, project_name)`
**Purpose**: Get discovered machines with enhanced machine information
**Parameters**:
- `subscription_id: str` - Subscription ID
- `resource_group: str` - Resource group name
- `project_name: str` - Project name
**Returns**: `List[Dict[str, Any]]` - Enhanced machine records
**Called by**: Discovery validation, intelligent validator
**Calls**: `AzureMigrateApiClient.list_discovered_machines()`, `_parse_machine_details()`

#### `AzureMigrateIntegration._parse_machine_details(machines)`
**Purpose**: Parse and enhance machine details from Azure Migrate data
**Parameters**:
- `machines: List[Dict]` - Raw machines from Azure API
**Returns**: `List[Dict[str, Any]]` - Enhanced machine records
**Called by**: `get_discovered_machines()`
**Calls**: JSON parsing, data extraction

#### `AzureMigrateIntegration.enable_replication(config, project, cache)`
**Purpose**: Enable replication for a machine (placeholder implementation)
**Parameters**:
- `config: MigrationConfig` - Machine configuration
- `project: AzureMigrateProject` - Project info
- `cache: ReplicationCache` - Cache configuration
**Returns**: `Dict[str, Any]` - Replication result
**Called by**: Replication workflow
**Calls**: Placeholder logic (to be implemented)

#### `RecoveryServicesIntegration.__init__(credential)`
**Purpose**: Initialize Recovery Services integration
**Parameters**:
- `credential: TokenCredential` - Azure authentication credential
**Returns**: None
**Called by**: RBAC validation functions
**Calls**: Credential validation

#### `RecoveryServicesIntegration.validate_recovery_vault_rbac(subscription_id, resource_group, vault_name, user_object_id)`
**Purpose**: Validate user has Contributor role on Recovery Services Vault
**Parameters**:
- `subscription_id: str` - Subscription ID
- `resource_group: str` - Resource group name
- `vault_name: str` - Recovery vault name
- `user_object_id: str` - User's Azure AD object ID
**Returns**: `ValidationResult` - RBAC validation result
**Called by**: Landing zone RBAC validation
**Calls**: Azure Authorization Management API

---

## Validation Framework

### `azmig_tool/base/validator_interface.py`

#### `BaseValidatorInterface.__init__(validation_config)`
**Purpose**: Abstract base class for machine-level validators
**Parameters**:
- `validation_config: ValidationConfig` - Validation settings (optional)
**Returns**: None
**Called by**: Concrete validator implementations
**Calls**: `get_validation_config()`

#### `BaseValidatorInterface.validate_region(config)` (Abstract)
**Purpose**: Validate Azure region exists and is accessible
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Validation result
**Called by**: Validation workflows
**Calls**: Implemented by concrete validators

#### `BaseValidatorInterface.validate_resource_group(config)` (Abstract)
**Purpose**: Validate resource group exists in subscription
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Validation result
**Called by**: Validation workflows
**Calls**: Implemented by concrete validators

#### `BaseValidatorInterface.validate_vnet_and_subnet(config)` (Abstract)
**Purpose**: Validate VNet and subnet configuration
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Validation result
**Called by**: Validation workflows
**Calls**: Implemented by concrete validators

#### `BaseValidatorInterface.validate_vm_sku(config)` (Abstract)
**Purpose**: Validate VM SKU availability in region
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Validation result
**Called by**: Validation workflows
**Calls**: Implemented by concrete validators

#### `BaseValidatorInterface.validate_disk_type(config)` (Abstract)
**Purpose**: Validate disk type compatibility
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Validation result
**Called by**: Validation workflows
**Calls**: Implemented by concrete validators

#### `BaseValidatorInterface.validate_rbac_resource_group(config, project, user_object_id)` (Abstract)
**Purpose**: Validate RBAC permissions on target resource group
**Parameters**:
- `config: MigrationConfig` - Machine configuration
- `project: AzureMigrateProject` - Project info
- `user_object_id: str` - User's Azure AD object ID
**Returns**: `ValidationResult` - RBAC validation result
**Called by**: RBAC validation workflows
**Calls**: Implemented by concrete validators

#### `BaseValidatorInterface.validate_discovery(config, project)` (Abstract)
**Purpose**: Validate machine is discovered in Azure Migrate
**Parameters**:
- `config: MigrationConfig` - Machine configuration
- `project: AzureMigrateProject` - Project info
**Returns**: `ValidationResult` - Discovery validation result
**Called by**: Discovery workflows
**Calls**: Implemented by concrete validators

#### `BaseValidatorInterface.validate_all(configs, project, user_object_id)` (Abstract)
**Purpose**: Validate all configurations with specified validations enabled
**Parameters**:
- `configs: List[MigrationConfig]` - Machine configurations
- `project: AzureMigrateProject` - Project info
- `user_object_id: str` - User's Azure AD object ID (optional)
**Returns**: `List[MachineValidationReport]` - Validation reports
**Called by**: Validation orchestration
**Calls**: Individual validation methods

### `azmig_tool/base/landing_zone_interface.py`

#### `BaseLandingZoneInterface.__init__(validation_config)`
**Purpose**: Abstract base class for project-level validation
**Parameters**:
- `validation_config: ValidationConfig` - Validation settings (optional)
**Returns**: None
**Called by**: Landing zone validator implementations
**Calls**: `get_validation_config()`

#### `BaseLandingZoneInterface.validate_access(config)` (Abstract)
**Purpose**: Validate access permissions for Azure Migrate project
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
**Returns**: `AccessValidationResult` - Access validation result
**Called by**: Landing zone validation workflow
**Calls**: Implemented by concrete validators

#### `BaseLandingZoneInterface.validate_appliance_health(config)` (Abstract)
**Purpose**: Validate migration appliance health and connectivity
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
**Returns**: `ApplianceHealthResult` - Appliance health result
**Called by**: Landing zone validation workflow
**Calls**: Implemented by concrete validators

#### `BaseLandingZoneInterface.validate_storage_cache(config, auto_create)` (Abstract)
**Purpose**: Validate cache storage account configuration
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
- `auto_create: bool` - Whether to auto-create missing storage
**Returns**: `StorageCacheResult` - Storage validation result
**Called by**: Landing zone validation workflow
**Calls**: Implemented by concrete validators

#### `BaseLandingZoneInterface.validate_quota(config)` (Abstract)
**Purpose**: Validate subscription quotas for migration
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
**Returns**: `QuotaValidationResult` - Quota validation result
**Called by**: Landing zone validation workflow
**Calls**: Implemented by concrete validators

#### `BaseLandingZoneInterface.validate_project(config)` (Abstract)
**Purpose**: Comprehensive project readiness validation
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
**Returns**: `ProjectReadinessResult` - Complete project validation
**Called by**: Project validation orchestration
**Calls**: All individual validation methods

### `azmig_tool/validators/servers_validator.py`

#### `ServersValidator.__init__(credential, validation_config)`
**Purpose**: Initialize live Azure API validator for server configurations
**Parameters**:
- `credential: TokenCredential` - Azure authentication credential
- `validation_config: ValidationConfig` - Validation settings (optional)
**Returns**: None
**Called by**: Validation workflows, consolidated validator
**Calls**: `BaseValidatorInterface.__init__()`

#### `ServersValidator._get_resource_client(subscription_id)`
**Purpose**: Get cached Azure Resource Management client
**Parameters**:
- `subscription_id: str` - Target subscription ID
**Returns**: `ResourceManagementClient` - Azure resource client
**Called by**: Validation methods
**Calls**: Client caching logic

#### `ServersValidator._get_compute_client(subscription_id)`
**Purpose**: Get cached Azure Compute Management client
**Parameters**:
- `subscription_id: str` - Target subscription ID
**Returns**: `ComputeManagementClient` - Azure compute client
**Called by**: SKU and compute validation
**Calls**: Client caching logic

#### `ServersValidator._get_network_client(subscription_id)`
**Purpose**: Get cached Azure Network Management client
**Parameters**:
- `subscription_id: str` - Target subscription ID
**Returns**: `NetworkManagementClient` - Azure network client
**Called by**: VNet/subnet validation
**Calls**: Client caching logic

#### `ServersValidator.validate_region(config)`
**Purpose**: Validate Azure region exists and is accessible
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Region validation result
**Called by**: `validate_all()`, individual validation calls
**Calls**: `_get_compute_client()`, Azure Locations API

#### `ServersValidator.validate_resource_group(config)`
**Purpose**: Validate target resource group exists in subscription
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Resource group validation result
**Called by**: `validate_all()`, individual validation calls
**Calls**: `_get_resource_client()`, Resource Groups API

#### `ServersValidator.validate_vnet_and_subnet(config)`
**Purpose**: Validate VNet exists and subnet is available
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Network validation result
**Called by**: `validate_all()`, individual validation calls
**Calls**: `_get_network_client()`, Virtual Networks API

#### `ServersValidator.validate_vm_sku(config)`
**Purpose**: Validate VM SKU is available in target region
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - SKU validation result
**Called by**: `validate_all()`, individual validation calls
**Calls**: `_get_compute_client()`, Resource SKUs API

#### `ServersValidator.validate_disk_type(config)`
**Purpose**: Validate disk type is supported in region
**Parameters**:
- `config: MigrationConfig` - Machine configuration
**Returns**: `ValidationResult` - Disk type validation result
**Called by**: `validate_all()`, individual validation calls
**Calls**: Disk type compatibility logic

#### `ServersValidator.validate_rbac_resource_group(config, project, user_object_id)`
**Purpose**: Validate user has required permissions on target resource group
**Parameters**:
- `config: MigrationConfig` - Machine configuration
- `project: AzureMigrateProject` - Project info
- `user_object_id: str` - User's Azure AD object ID
**Returns**: `ValidationResult` - RBAC validation result
**Called by**: `validate_all()` when RBAC validation enabled
**Calls**: Azure Authorization Management API

#### `ServersValidator.validate_discovery(config, project)`
**Purpose**: Validate machine is discovered and migration-ready in Azure Migrate
**Parameters**:
- `config: MigrationConfig` - Machine configuration
- `project: AzureMigrateProject` - Project info
**Returns**: `ValidationResult` - Discovery validation result
**Called by**: `validate_all()`, discovery workflows
**Calls**: `AzureMigrateApiClient.search_machines_by_name()`

#### `ServersValidator.validate_all(configs, project, user_object_id)`
**Purpose**: Execute all enabled validations for machine configurations
**Parameters**:
- `configs: List[MigrationConfig]` - Machine configurations to validate
- `project: AzureMigrateProject` - Azure Migrate project info
- `user_object_id: str` - User's Azure AD object ID (optional)
**Returns**: `List[MachineValidationReport]` - Validation reports for all machines
**Called by**: Validation orchestration, wizard
**Calls**: All individual validation methods based on configuration

### `azmig_tool/validators/landing_zone_validator.py`

#### `LandingZoneValidator.__init__(credential, validation_config)`
**Purpose**: Initialize live Azure API validator for landing zone configurations
**Parameters**:
- `credential: TokenCredential` - Azure authentication credential
- `validation_config: ValidationConfig` - Validation settings (optional)
**Returns**: None
**Called by**: Landing zone workflows, consolidated validator
**Calls**: `BaseLandingZoneInterface.__init__()`

#### `LandingZoneValidator._get_resource_client(subscription_id)`
**Purpose**: Get cached Azure Resource Management client
**Parameters**:
- `subscription_id: str` - Target subscription ID
**Returns**: `ResourceManagementClient` - Azure resource client
**Called by**: Validation methods
**Calls**: Client caching logic

#### `LandingZoneValidator._get_storage_client(subscription_id)`
**Purpose**: Get cached Azure Storage Management client
**Parameters**:
- `subscription_id: str` - Target subscription ID
**Returns**: `StorageManagementClient` - Azure storage client
**Called by**: Storage validation methods
**Calls**: Client caching logic

#### `LandingZoneValidator._get_authorization_client(subscription_id)`
**Purpose**: Get cached Azure Authorization Management client
**Parameters**:
- `subscription_id: str` - Target subscription ID
**Returns**: `AuthorizationManagementClient` - Azure authorization client
**Called by**: RBAC validation methods
**Calls**: Client caching logic

#### `LandingZoneValidator._get_compute_client(subscription_id)`
**Purpose**: Get cached Azure Compute Management client
**Parameters**:
- `subscription_id: str` - Target subscription ID
**Returns**: `ComputeManagementClient` - Azure compute client
**Called by**: Quota validation methods
**Calls**: Client caching logic

#### `LandingZoneValidator.validate_access(config)`
**Purpose**: Validate access permissions for Azure Migrate project and related resources
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
**Returns**: `AccessValidationResult` - Comprehensive access validation
**Called by**: `validate_project()`, access validation workflows
**Calls**: Multiple RBAC validation methods, Azure Authorization API

#### `LandingZoneValidator.validate_appliance_health(config)`
**Purpose**: Validate migration appliance health, connectivity and status
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
**Returns**: `ApplianceHealthResult` - Appliance health assessment
**Called by**: `validate_project()`, appliance validation workflows
**Calls**: `AzureMigrateApiClient.get_migration_appliances()`, health analysis

#### `LandingZoneValidator.validate_storage_cache(config, auto_create_if_missing)`
**Purpose**: Validate cache storage account exists and is properly configured
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
- `auto_create_if_missing: bool` - Whether to create missing storage account
**Returns**: `StorageCacheResult` - Storage cache validation result
**Called by**: `validate_project()`, storage validation workflows
**Calls**: `_get_storage_client()`, Storage Accounts API, auto-creation logic

#### `LandingZoneValidator.validate_quota(config)`
**Purpose**: Validate subscription has sufficient quotas for migration
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
**Returns**: `QuotaValidationResult` - Quota validation result
**Called by**: `validate_project()`, quota validation workflows
**Calls**: `_get_compute_client()`, Usage API, quota calculation

#### `LandingZoneValidator.validate_project(config)`
**Purpose**: Comprehensive validation of Azure Migrate project readiness
**Parameters**:
- `config: MigrateProjectConfig` - Project configuration
**Returns**: `ProjectReadinessResult` - Complete project readiness assessment
**Called by**: Project validation orchestration, wizard
**Calls**: All individual validation methods based on configuration settings

### `azmig_tool/validators/consolidated_validator.py`

#### `ConsolidatedValidator.__init__(credential, validation_config)`
**Purpose**: Initialize consolidated validator that combines landing zone and server validation
**Parameters**:
- `credential: TokenCredential` - Azure authentication credential
- `validation_config: ValidationConfig` - Validation settings (optional)
**Returns**: None
**Called by**: Consolidated validation workflows
**Calls**: `LandingZoneValidator()`, `ServersValidator()` initialization

#### `ConsolidatedValidator._extract_unique_lz_configs(configs)`
**Purpose**: Extract unique landing zone configurations to avoid duplicate validations
**Parameters**:
- `configs: List[ConsolidatedMigrationConfig]` - Consolidated configurations
**Returns**: `Dict[str, MigrateProjectConfig]` - Unique project configurations by key
**Called by**: `validate_all()`
**Calls**: Configuration analysis and deduplication logic

#### `ConsolidatedValidator._get_project_key(config)`
**Purpose**: Generate unique key for project configuration for deduplication
**Parameters**:
- `config: Union[MigrateProjectConfig, ProjectReadinessResult]` - Project config or result
**Returns**: `str` - Unique project identifier key
**Called by**: `_extract_unique_lz_configs()`, result lookup
**Calls**: String formatting of project identifiers

#### `ConsolidatedValidator.validate_all(configs)`
**Purpose**: Execute comprehensive validation of consolidated configurations
**Parameters**:
- `configs: List[ConsolidatedMigrationConfig]` - All configurations to validate
**Returns**: `Dict[str, Any]` - Complete validation results with summary
**Called by**: Consolidated validation orchestration
**Calls**: `_extract_unique_lz_configs()`, `lz_validator.validate_project()`, `server_validator.validate_all()`

#### `ConsolidatedValidator.validate_single(config)`
**Purpose**: Validate a single consolidated configuration
**Parameters**:
- `config: ConsolidatedMigrationConfig` - Single configuration to validate
**Returns**: `Dict[str, Any]` - Validation results for single config
**Called by**: Single configuration validation workflows
**Calls**: `validate_all()` with single item list

---

## Interactive Wizard

### `azmig_tool/wizard.py`

#### `AzureMigrationWizard.__init__(credential)`
**Purpose**: Initialize interactive migration wizard with Azure credentials
**Parameters**:
- `credential: TokenCredential` - Azure authentication credential
**Returns**: None
**Called by**: CLI main function
**Calls**: Credential validation, client initialization

#### `AzureMigrationWizard.run_migration_type_selection()`
**Purpose**: Step 1 - Interactive selection of migration type (New vs Patch)
**Parameters**: None
**Returns**: `str` - Selected migration type
**Called by**: `run_wizard()`
**Calls**: `Prompt.ask()`, console output

#### `AzureMigrationWizard.run_project_selection()`
**Purpose**: Step 2 - Interactive Azure Migrate project selection
**Parameters**: None
**Returns**: `AzureMigrateProject` - Selected project configuration
**Called by**: `run_wizard()`
**Calls**: `AzureMigrateApiClient.get_migrate_projects()`, interactive prompts

#### `AzureMigrationWizard.run_cache_selection(project)`
**Purpose**: Step 5 - Interactive replication cache configuration
**Parameters**:
- `project: AzureMigrateProject` - Selected project
**Returns**: `ReplicationCache` - Cache configuration
**Called by**: `run_wizard()`
**Calls**: Storage account discovery, interactive prompts

#### `AzureMigrationWizard.run_file_upload_and_validation_lz(validation_choice, file_path)`
**Purpose**: Step 3 - Upload and validate landing zone configuration file
**Parameters**:
- `validation_choice: str` - Type of validation ('landing_zone')
- `file_path: str` - Path to configuration file
**Returns**: `Tuple[List[MigrateProjectConfig], str]` - Parsed configs and file path
**Called by**: Landing zone validation workflows
**Calls**: `ConfigParser.parse()`, validation display

#### `AzureMigrationWizard.run_file_upload_and_validation_servers(validation_choice, file_path)`
**Purpose**: Step 3 - Upload and validate server configuration file
**Parameters**:
- `validation_choice: str` - Type of validation ('servers')
- `file_path: str` - Path to configuration file
**Returns**: `Tuple[List[MigrationConfig], str]` - Parsed configs and file path
**Called by**: Server validation workflows
**Calls**: `ConfigParser.parse()`, validation display

#### `AzureMigrationWizard.run_azure_validations(configs, project)`
**Purpose**: Step 6 - Execute Azure resource validations for server configurations
**Parameters**:
- `configs: List[MigrationConfig]` - Server configurations
- `project: AzureMigrateProject` - Selected project
**Returns**: `List[MachineValidationReport]` - Validation results
**Called by**: Server validation workflows
**Calls**: `ServersValidator.validate_all()`, user object ID resolution

#### `AzureMigrationWizard.run_landing_zone_validation_workflow(lz_configs, validation_choice, file_path)`
**Purpose**: Step 4 - Execute landing zone validation workflow
**Parameters**:
- `lz_configs: List[MigrateProjectConfig]` - Landing zone configurations
- `validation_choice: str` - Validation type
- `file_path: str` - Configuration file path
**Returns**: None (displays results)
**Called by**: Landing zone validation orchestration
**Calls**: `LandingZoneValidator.validate_project()`, result display

#### `AzureMigrationWizard.run_replication_workflow(validation_reports, project, cache)`
**Purpose**: Step 6 - Enable replication for validated machines
**Parameters**:
- `validation_reports: List[MachineValidationReport]` - Validation results
- `project: AzureMigrateProject` - Target project
- `cache: ReplicationCache` - Cache configuration
**Returns**: None (displays results)
**Called by**: Replication orchestration
**Calls**: `AzureMigrateIntegration.enable_replication()`, progress tracking

#### `AzureMigrationWizard.run_wizard()`
**Purpose**: Main wizard orchestration - runs complete interactive workflow
**Parameters**: None
**Returns**: None
**Called by**: CLI main function
**Calls**: All wizard step methods in sequence

#### `AzureMigrationWizard.run_intelligent_server_validation(file_path)`
**Purpose**: Step 4 - Intelligent server validation with project matching
**Parameters**:
- `file_path: str` - Path to server configuration file
**Returns**: None (displays results)
**Called by**: Intelligent validation workflows
**Calls**: `IntelligentServerValidator.validate_servers_with_project_matching()`

---

## Data Models & Utilities

### `azmig_tool/models.py`

#### Dataclass Models
**Purpose**: Define data structures for configuration and results
**Models Include**:
- `MigrationConfig` - Server migration configuration
- `MigrateProjectConfig` - Landing zone project configuration  
- `ConsolidatedMigrationConfig` - Combined LZ + server configuration
- `ValidationResult` - Individual validation result
- `MachineValidationReport` - Complete machine validation report
- `ProjectReadinessResult` - Landing zone validation result
- `AccessValidationResult` - Access permission validation result
- `ApplianceHealthResult` - Migration appliance health result
- `StorageCacheResult` - Storage cache validation result
- `QuotaValidationResult` - Subscription quota validation result
- `AzureMigrateProject` - Azure Migrate project information
- `ReplicationCache` - Replication cache configuration
- `MachineDiscoveryInfo` - Machine discovery information

#### Enum Classes
**Purpose**: Define constants and enumerated values
**Enums Include**:
- `ValidationStage` - Validation stage identifiers
- `ValidationStatus` - Validation status values
- `ApplianceType` - Migration appliance types
- `DiskType` - Disk type options
- `ApplianceHealth` - Appliance health status

### `azmig_tool/constants.py`

#### Column Definitions
**Purpose**: Define required and optional columns for different file formats

#### `LANDING_ZONE_CSV_COLUMNS`
**Purpose**: Required columns for landing zone CSV files
**Values**: List of required column names for project configuration
**Used by**: CSV parsers, validation logic

#### `SERVERS_REQUIRED_COLUMNS`  
**Purpose**: Required columns for server configuration files
**Values**: List of required column names for machine configuration
**Used by**: Excel parsers, validation logic

#### `CONSOLIDATED_REQUIRED_COLUMNS`
**Purpose**: Required columns for consolidated template files  
**Values**: Combined list of LZ and server columns
**Used by**: Consolidated Excel parsing

#### `COLUMN_MAPPING`
**Purpose**: Mapping from display names to internal field names
**Values**: Dictionary mapping Excel columns to dataclass fields
**Used by**: Configuration parsing and transformation

#### API Version Constants
**Purpose**: Define Azure API versions for different services
**Used by**: Azure API clients for version consistency

---

## Authentication & Credentials

### `azmig_tool/auth.py`

#### `CachedCredentialFactory.create_credential(auth_method, **kwargs)`
**Purpose**: Factory method to create and cache Azure credentials
**Parameters**:
- `auth_method: str` - Authentication method ('azure_cli', 'service_principal', etc.)
- `**kwargs` - Method-specific parameters
**Returns**: `TokenCredential` - Cached Azure credential
**Called by**: CLI authentication, wizard initialization
**Calls**: Credential-specific creation methods, caching logic

#### `CachedCredentialFactory.get_cached_credential(cache_key)`
**Purpose**: Retrieve existing cached credential
**Parameters**:
- `cache_key: str` - Unique identifier for cached credential
**Returns**: `Optional[TokenCredential]` - Cached credential if exists
**Called by**: `create_credential()`, credential reuse logic
**Calls**: Cache lookup

#### `CachedCredentialFactory.clear_cache()`
**Purpose**: Clear all cached credentials
**Parameters**: None
**Returns**: None
**Called by**: Authentication reset, cleanup operations
**Calls**: Cache clearing logic

### `azmig_tool/interactive_prompts.py`

#### `get_auth_method_interactive()`
**Purpose**: Interactive prompt for authentication method selection
**Parameters**: None
**Returns**: `str` - Selected authentication method
**Called by**: Wizard when authentication not specified
**Calls**: `Prompt.ask()`, validation logic

#### `get_subscription_id_interactive(credential)`
**Purpose**: Interactive prompt for subscription selection
**Parameters**:
- `credential: TokenCredential` - Azure credential for subscription listing
**Returns**: `str` - Selected subscription ID
**Called by**: Wizard when subscription not specified
**Calls**: Azure Subscription API, interactive selection

#### `get_file_path_interactive(file_type)`
**Purpose**: Interactive prompt for configuration file selection
**Parameters**:
- `file_type: str` - Type of file being requested
**Returns**: `str` - Selected file path
**Called by**: Wizard file selection steps
**Calls**: File dialog or path input prompts

---

## Formatters & Output

### `azmig_tool/formatters/table_formatter.py`

#### `EnhancedTableFormatter.create_validation_summary_table(validation_reports)`
**Purpose**: Create formatted table for validation results summary
**Parameters**:
- `validation_reports: List[MachineValidationReport]` - Validation results to display
**Returns**: `Table` - Rich formatted table
**Called by**: Wizard result display, CLI output
**Calls**: Rich table creation, formatting logic

#### `EnhancedTableFormatter.create_project_readiness_table(project_result)`
**Purpose**: Create formatted table for project readiness results
**Parameters**:
- `project_result: ProjectReadinessResult` - Project validation result
**Returns**: `Table` - Rich formatted table
**Called by**: Landing zone result display
**Calls**: Rich table creation, status formatting

#### `EnhancedTableFormatter.create_machine_details_table(machines)`
**Purpose**: Create formatted table for discovered machine details
**Parameters**:
- `machines: List[Dict]` - Machine information to display
**Returns**: `Table` - Rich formatted table
**Called by**: Machine discovery displays
**Calls**: Rich table creation, data formatting

#### `EnhancedTableFormatter.format_validation_status(status)`
**Purpose**: Format validation status with appropriate colors and symbols
**Parameters**:
- `status: ValidationStatus` - Status to format
**Returns**: `str` - Formatted status string with colors
**Called by**: Table creation methods
**Calls**: Rich markup formatting

#### `EnhancedTableFormatter.format_boolean_result(value)`
**Purpose**: Format boolean values with appropriate symbols and colors
**Parameters**:
- `value: bool` - Boolean value to format
**Returns**: `str` - Formatted boolean with symbols
**Called by**: Table formatting methods
**Calls**: Rich markup formatting

---

## Intelligent Validation

### `azmig_tool/intelligent_validator.py`

#### `IntelligentServerValidator.__init__(credential)`
**Purpose**: Initialize intelligent validator with project matching capabilities
**Parameters**:
- `credential: TokenCredential` - Azure authentication credential
**Returns**: None
**Called by**: Intelligent validation workflows
**Calls**: Azure client initialization

#### `IntelligentServerValidator.validate_servers_with_project_matching(servers_config_path)`
**Purpose**: Validate servers with automatic Azure Migrate project matching
**Parameters**:
- `servers_config_path: str` - Path to server configuration file
**Returns**: `List[MachineValidationReport]` - Validation reports with project matching
**Called by**: Wizard intelligent validation workflow
**Calls**: `_match_servers_to_projects()`, `ServersValidator.validate_all()`

#### `IntelligentServerValidator._match_servers_to_projects(servers)`
**Purpose**: Match server configurations to appropriate Azure Migrate projects
**Parameters**:
- `servers: List[MigrationConfig]` - Server configurations to match
**Returns**: `Dict[str, List[MigrationConfig]]` - Servers grouped by matched project
**Called by**: `validate_servers_with_project_matching()`
**Calls**: `_find_best_project_match()`, project discovery

#### `IntelligentServerValidator._find_best_project_match(server)`
**Purpose**: Find the best Azure Migrate project match for a server
**Parameters**:
- `server: MigrationConfig` - Server configuration to match
**Returns**: `Optional[AzureMigrateProject]` - Best matching project or None
**Called by**: `_match_servers_to_projects()`
**Calls**: `_get_discovered_machines()`, machine search logic

#### `IntelligentServerValidator._get_discovered_machines(subscription_id, project_key)`
**Purpose**: Get discovered machines for a project with caching
**Parameters**:
- `subscription_id: str` - Subscription ID
- `project_key: str` - Project identifier key
**Returns**: `List[Dict]` - Discovered machines in project
**Called by**: `_find_best_project_match()`
**Calls**: `AzureMigrateIntegration.get_discovered_machines()`, caching

#### `IntelligentServerValidator._extract_ip_address(machine)`
**Purpose**: Extract IP address from machine discovery data
**Parameters**:
- `machine: Dict` - Machine record from Azure Migrate
**Returns**: `Optional[str]` - Extracted IP address or None
**Called by**: Machine matching logic
**Calls**: Data parsing of discoveryData section

---

This documentation provides comprehensive coverage of all functions in the Azure Migration Tool, their purposes, parameters, return values, and call relationships. Each function is categorized by its role in the application architecture, making it easier to understand the overall system design and function interdependencies.