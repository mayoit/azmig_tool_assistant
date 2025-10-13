# Azure Migration Tool - Function Index by Module

## Quick Reference Index

This document provides a quick lookup index for finding specific functions organized by module and functionality.

---

## 🚀 Core Application Functions

### CLI Entry Points (`azmig_tool/cli.py`)
- `main()` - Application entry point
- `parse_args()` - Command line argument parsing
- `validate_args(args)` - Argument validation
- `setup_logging(debug)` - Logging configuration
- `handle_non_interactive_mode(args)` - Non-interactive execution

---

## 📁 Configuration & File Processing

### Configuration Parsing (`azmig_tool/config/parsers.py`)
#### Core Parser Functions
- `ConfigParser.__init__(config_path)` - Initialize parser
- `ConfigParser.parse()` - Main parsing entry point
- `ConfigParser._detect_file_type()` - Auto-detect file format

#### Format-Specific Parsers
- `ConfigParser._parse_csv()` - CSV file parsing
- `ConfigParser._parse_json()` - JSON file parsing  
- `ConfigParser._parse_excel()` - Excel file parsing
- `ConfigParser.detect_excel_format()` - Excel format detection

#### Excel Template Handlers
- `ExcelParser.validate_layer2_structure()` - Server template validation
- `ConsolidatedExcelParser.validate_consolidated_structure()` - Combined template validation
- `ExcelParser._create_migration_configs()` - Server config creation
- `ConsolidatedExcelParser._create_consolidated_configs()` - Combined config creation

#### Validation Functions
- `ConfigParser.validate_file_exists()` - File existence check
- `ConfigParser._validate_csv_columns()` - CSV column validation
- `ConfigParser._validate_required_fields()` - Required field validation

### Validation Configuration (`azmig_tool/config/validation_config.py`)
#### Configuration Management
- `ValidationConfig.__init__(config_data)` - Initialize validation settings
- `get_validation_config()` - Singleton configuration factory
- `ValidationConfig._resolve_profile_overrides()` - Profile resolution

#### Validation Checks (is_*_enabled methods)
- `ValidationConfig.is_region_validation_enabled()` - Region validation toggle
- `ValidationConfig.is_resource_group_validation_enabled()` - RG validation toggle
- `ValidationConfig.is_vnet_subnet_validation_enabled()` - Network validation toggle
- `ValidationConfig.is_vm_sku_validation_enabled()` - SKU validation toggle
- `ValidationConfig.is_disk_type_validation_enabled()` - Disk validation toggle
- `ValidationConfig.is_rbac_validation_enabled()` - RBAC validation toggle
- `ValidationConfig.is_discovery_validation_enabled()` - Discovery validation toggle
- `ValidationConfig.is_access_validation_enabled()` - Access validation toggle
- `ValidationConfig.is_appliance_health_enabled()` - Appliance health toggle
- `ValidationConfig.is_storage_cache_enabled()` - Storage cache toggle
- `ValidationConfig.is_quota_validation_enabled()` - Quota validation toggle

---

## ☁️ Azure API Integration

### Core Azure Client (`azmig_tool/clients/azure_client.py`)
#### HTTP Operations
- `AzureRestApiClient.__init__(credential, subscription_id)` - Initialize REST client
- `AzureRestApiClient.get(path, api_version, params)` - GET requests
- `AzureRestApiClient.post(path, data, api_version)` - POST requests
- `AzureRestApiClient.put(path, data, api_version)` - PUT requests
- `AzureRestApiClient.delete(path, api_version)` - DELETE requests

#### Pagination & Utilities
- `AzureRestApiClient.list_all(path, api_version, params)` - Paginated listing
- `AzureRestApiClient._add_api_version(url, api_version)` - URL parameter handling
- `AzureRestApiClient._handle_pagination(initial_response)` - Pagination logic

#### Azure Migrate Specific Operations
- `AzureMigrateApiClient.search_machines_by_name(rg, project, machine)` - Direct machine search
- `AzureMigrateApiClient.search_machines_by_name_cached(rg, project, machine)` - Cached machine search
- `AzureMigrateApiClient.list_discovered_machines(rg, project, use_cache)` - List all machines
- `AzureMigrateApiClient._add_discovery_status(machine)` - Add discovery metadata
- `AzureMigrateApiClient.get_migrate_projects(resource_group)` - List migrate projects
- `AzureMigrateApiClient.get_migration_appliances(subscription, project)` - Get appliances
- `AzureMigrateApiClient._parse_resource_graph_appliances(result)` - Parse appliance data

### Azure Migrate Integration (`azmig_tool/clients/azure_migrate_client.py`)
#### Machine Discovery
- `AzureMigrateIntegration.__init__(credential)` - Initialize integration
- `AzureMigrateIntegration.get_discovered_machines(sub, rg, project)` - Enhanced machine discovery
- `AzureMigrateIntegration._parse_machine_details(machines)` - Parse machine data

#### Replication Management
- `AzureMigrateIntegration.enable_replication(config, project, cache)` - Enable replication
- `RecoveryServicesIntegration.__init__(credential)` - Initialize recovery services
- `RecoveryServicesIntegration.validate_recovery_vault_rbac(sub, rg, vault, user_id)` - Vault RBAC check

---

## ✅ Validation Framework

### Base Interfaces
#### Server Validation Interface (`azmig_tool/base/validator_interface.py`)
- `BaseValidatorInterface.__init__(validation_config)` - Base validator init
- `BaseValidatorInterface.validate_region(config)` - Abstract region validation
- `BaseValidatorInterface.validate_resource_group(config)` - Abstract RG validation
- `BaseValidatorInterface.validate_vnet_and_subnet(config)` - Abstract network validation
- `BaseValidatorInterface.validate_vm_sku(config)` - Abstract SKU validation
- `BaseValidatorInterface.validate_disk_type(config)` - Abstract disk validation
- `BaseValidatorInterface.validate_rbac_resource_group(config, project, user_id)` - Abstract RBAC validation
- `BaseValidatorInterface.validate_discovery(config, project)` - Abstract discovery validation
- `BaseValidatorInterface.validate_all(configs, project, user_id)` - Abstract bulk validation
- `BaseValidatorInterface.validate_machine_config(config)` - Abstract single machine validation

#### Landing Zone Interface (`azmig_tool/base/landing_zone_interface.py`)
- `BaseLandingZoneInterface.__init__(validation_config)` - Base LZ validator init
- `BaseLandingZoneInterface.validate_access(config)` - Abstract access validation
- `BaseLandingZoneInterface.validate_appliance_health(config)` - Abstract appliance validation
- `BaseLandingZoneInterface.validate_storage_cache(config, auto_create)` - Abstract storage validation
- `BaseLandingZoneInterface.validate_quota(config)` - Abstract quota validation
- `BaseLandingZoneInterface.validate_project(config)` - Abstract project validation

### Concrete Validators
#### Server Validator (`azmig_tool/validators/servers_validator.py`)
##### Initialization & Client Management
- `ServersValidator.__init__(credential, validation_config)` - Initialize server validator
- `ServersValidator._get_resource_client(subscription_id)` - Get cached resource client
- `ServersValidator._get_compute_client(subscription_id)` - Get cached compute client
- `ServersValidator._get_network_client(subscription_id)` - Get cached network client

##### Individual Validations
- `ServersValidator.validate_region(config)` - Live region validation
- `ServersValidator.validate_resource_group(config)` - Live RG validation
- `ServersValidator.validate_vnet_and_subnet(config)` - Live network validation
- `ServersValidator.validate_vm_sku(config)` - Live SKU validation
- `ServersValidator.validate_disk_type(config)` - Live disk validation
- `ServersValidator.validate_rbac_resource_group(config, project, user_id)` - Live RBAC validation
- `ServersValidator.validate_discovery(config, project)` - Live discovery validation

##### Orchestration
- `ServersValidator.validate_all(configs, project, user_id)` - Execute all validations
- `ServersValidator.validate_machine_config(config)` - Single machine validation

#### Landing Zone Validator (`azmig_tool/validators/landing_zone_validator.py`)
##### Initialization & Client Management
- `LandingZoneValidator.__init__(credential, validation_config)` - Initialize LZ validator
- `LandingZoneValidator._get_resource_client(subscription_id)` - Get cached resource client
- `LandingZoneValidator._get_storage_client(subscription_id)` - Get cached storage client
- `LandingZoneValidator._get_authorization_client(subscription_id)` - Get cached auth client
- `LandingZoneValidator._get_compute_client(subscription_id)` - Get cached compute client

##### Individual Validations
- `LandingZoneValidator.validate_access(config)` - Live access validation
- `LandingZoneValidator.validate_appliance_health(config)` - Live appliance validation
- `LandingZoneValidator.validate_storage_cache(config, auto_create)` - Live storage validation
- `LandingZoneValidator.validate_quota(config)` - Live quota validation

##### Orchestration
- `LandingZoneValidator.validate_project(config)` - Complete project validation

#### Consolidated Validator (`azmig_tool/validators/consolidated_validator.py`)
- `ConsolidatedValidator.__init__(credential, validation_config)` - Initialize consolidated validator
- `ConsolidatedValidator._extract_unique_lz_configs(configs)` - Extract unique projects
- `ConsolidatedValidator._get_project_key(config)` - Generate project key
- `ConsolidatedValidator.validate_all(configs)` - Validate consolidated configs
- `ConsolidatedValidator.validate_single(config)` - Single consolidated validation

---

## 🧠 Intelligent Validation

### Intelligent Server Validator (`azmig_tool/intelligent_validator.py`)
#### Main Operations
- `IntelligentServerValidator.__init__(credential)` - Initialize intelligent validator
- `IntelligentServerValidator.validate_servers_with_project_matching(path)` - Main validation with matching

#### Project Matching Logic
- `IntelligentServerValidator._match_servers_to_projects(servers)` - Match servers to projects
- `IntelligentServerValidator._find_best_project_match(server)` - Find best project match
- `IntelligentServerValidator._calculate_match_score(server, project, machines)` - Calculate match score

#### Machine Discovery
- `IntelligentServerValidator._get_discovered_machines(sub_id, project_key)` - Get cached discovered machines
- `IntelligentServerValidator._extract_ip_address(machine)` - Extract IP from machine data
- `IntelligentServerValidator._normalize_machine_name(name)` - Normalize machine names

---

## 🎯 Interactive Wizard

### Main Wizard (`azmig_tool/wizard.py`)
#### Initialization & Main Flow
- `AzureMigrationWizard.__init__(credential)` - Initialize wizard
- `AzureMigrationWizard.run_wizard()` - Main wizard orchestration

#### Interactive Steps
- `AzureMigrationWizard.run_migration_type_selection()` - Step 1: Migration type
- `AzureMigrationWizard.run_project_selection()` - Step 2: Project selection
- `AzureMigrationWizard.run_cache_selection(project)` - Step 5: Cache selection

#### Validation Workflows
- `AzureMigrationWizard.run_file_upload_and_validation_lz(validation_choice, file_path)` - LZ validation workflow
- `AzureMigrationWizard.run_file_upload_and_validation_servers(validation_choice, file_path)` - Server validation workflow
- `AzureMigrationWizard.run_azure_validations(configs, project)` - Execute Azure validations
- `AzureMigrationWizard.run_landing_zone_validation_workflow(configs, choice, path)` - LZ validation orchestration
- `AzureMigrationWizard.run_intelligent_server_validation(file_path)` - Intelligent validation

#### Replication & Results
- `AzureMigrationWizard.run_replication_workflow(reports, project, cache)` - Replication workflow
- `AzureMigrationWizard._display_validation_summary(reports)` - Display validation results
- `AzureMigrationWizard._display_project_readiness(result)` - Display project results

---

## 🔐 Authentication & Security

### Credential Management (`azmig_tool/auth.py`)
- `CachedCredentialFactory.create_credential(auth_method, **kwargs)` - Create cached credential
- `CachedCredentialFactory.get_cached_credential(cache_key)` - Get existing credential
- `CachedCredentialFactory._generate_cache_key(auth_method, **kwargs)` - Generate cache key
- `CachedCredentialFactory.clear_cache()` - Clear credential cache

### Interactive Authentication (`azmig_tool/interactive_prompts.py`)
- `get_auth_method_interactive()` - Interactive auth method selection
- `get_subscription_id_interactive(credential)` - Interactive subscription selection
- `get_file_path_interactive(file_type)` - Interactive file selection
- `get_user_object_id_interactive(credential)` - Interactive user ID resolution
- `confirm_action_interactive(message)` - Interactive confirmation prompts

---

## 🎨 Output & Formatting

### Table Formatting (`azmig_tool/formatters/table_formatter.py`)
#### Result Display Tables
- `EnhancedTableFormatter.create_validation_summary_table(reports)` - Validation summary table
- `EnhancedTableFormatter.create_project_readiness_table(result)` - Project readiness table
- `EnhancedTableFormatter.create_machine_details_table(machines)` - Machine details table
- `EnhancedTableFormatter.create_appliance_health_table(appliances)` - Appliance health table

#### Formatting Utilities
- `EnhancedTableFormatter.format_validation_status(status)` - Format status with colors
- `EnhancedTableFormatter.format_boolean_result(value)` - Format boolean with symbols
- `EnhancedTableFormatter.format_datetime(dt)` - Format datetime strings
- `EnhancedTableFormatter.truncate_text(text, max_length)` - Truncate long text

---

## 📊 Data Models & Utilities

### Core Models (`azmig_tool/models.py`)
#### Data Classes (Constructors)
- `MigrationConfig.__init__()` - Server migration configuration
- `MigrateProjectConfig.__init__()` - Landing zone configuration
- `ConsolidatedMigrationConfig.__init__()` - Combined configuration
- `ValidationResult.__init__()` - Individual validation result
- `MachineValidationReport.__init__()` - Machine validation report
- `ProjectReadinessResult.__init__()` - Project validation result
- `AzureMigrateProject.__init__()` - Azure Migrate project info
- `ReplicationCache.__init__()` - Replication cache configuration

#### Utility Methods
- `MachineValidationReport.is_valid()` - Check if machine passed all validations
- `MachineValidationReport.get_failure_summary()` - Get failure summary
- `ProjectReadinessResult.is_ready()` - Check if project is ready
- `ValidationResult.is_passed()` - Check if validation passed

### Constants & Configuration (`azmig_tool/constants.py`)
#### Column Definitions
- `LANDING_ZONE_CSV_COLUMNS` - Required LZ CSV columns
- `SERVERS_REQUIRED_COLUMNS` - Required server columns
- `CONSOLIDATED_REQUIRED_COLUMNS` - Required consolidated columns
- `COLUMN_MAPPING` - Column name to field mapping

#### API Constants
- `AZURE_API_VERSIONS` - Azure API version constants
- `DEFAULT_REGIONS` - Default Azure regions list
- `APPLIANCE_TYPES` - Migration appliance type mappings

---

## 🔧 Utility Functions

### File Operations
- `pathlib.Path` operations for file handling
- `pandas` operations for Excel/CSV processing
- `json` operations for JSON processing

### Error Handling
- Azure API error handling and retry logic
- Validation error aggregation and reporting
- User-friendly error message formatting

### Caching & Performance
- Azure client caching mechanisms
- Machine discovery result caching
- Credential reuse and management

---

## Function Usage Patterns

### Common Initialization Pattern
```python
# Most classes follow this pattern:
def __init__(self, credential: TokenCredential, validation_config: Optional[ValidationConfig] = None):
    self.credential = credential
    self.validation_config = validation_config or get_validation_config()
```

### Validation Method Pattern
```python
# All validation methods follow this signature:
def validate_*(self, config: Union[MigrationConfig, MigrateProjectConfig]) -> ValidationResult:
    # Implementation
    return ValidationResult(stage=ValidationStage.*, passed=bool, message=str, details=dict)
```

### Client Caching Pattern
```python
# Client caching follows this pattern:
def _get_*_client(self, subscription_id: str) -> *ManagementClient:
    cache_key = f"*_{subscription_id}"
    if cache_key not in self._clients_cache:
        self._clients_cache[cache_key] = *ManagementClient(credential=self.credential, subscription_id=subscription_id)
    return self._clients_cache[cache_key]
```

This index provides quick access to any function in the system, organized by module and functionality area.