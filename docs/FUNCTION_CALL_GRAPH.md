# Azure Migration Tool - Function Call Graph

## Overview
This document provides visual representation of function call relationships in the Azure Migration Tool, showing how functions interact across different modules.

## Application Entry Points

```
CLI Entry Point:
main() 
├── parse_args()
├── validate_args()
└── AzureMigrationWizard()
    └── run_wizard()
```

## Main Workflow Call Graphs

### 1. CLI Wizard Workflow

```
AzureMigrationWizard.run_wizard()
├── run_migration_type_selection()
├── run_project_selection()
│   └── AzureMigrateApiClient.get_migrate_projects()
├── run_cache_selection()
├── [Validation Type Selection]
├── run_file_upload_and_validation_*()
│   └── ConfigParser.parse()
│       ├── _detect_file_type()
│       ├── _parse_csv() / _parse_json() / _parse_excel()
│       └── validate_file_exists()
├── run_landing_zone_validation_workflow() OR
├── run_azure_validations()
│   └── ServersValidator.validate_all()
└── run_replication_workflow()
    └── AzureMigrateIntegration.enable_replication()
```

### 2. Configuration Parsing Call Graph

```
ConfigParser.parse()
├── _detect_file_type()
├── validate_file_exists()
└── [Based on file type:]
    ├── _parse_csv()
    │   ├── pandas.read_csv()
    │   ├── _validate_csv_columns()
    │   └── _create_migrate_project_configs()
    ├── _parse_json()
    │   ├── json.load()
    │   └── _create_migrate_project_configs()
    └── _parse_excel()
        ├── detect_excel_format()
        │   └── pandas.read_excel()
        ├── validate_layer2_structure() OR
        ├── validate_consolidated_structure()
        └── _create_migration_configs() OR
            _create_consolidated_configs()
```

### 3. Azure API Client Call Graph

```
AzureMigrateApiClient
├── search_machines_by_name()
│   ├── get() [Direct machine API]
│   ├── _add_discovery_status()
│   └── [Fallback] list_discovered_machines()
├── search_machines_by_name_cached()
│   ├── list_discovered_machines(use_cache=True)
│   └── _add_discovery_status()
├── list_discovered_machines()
│   ├── list_all()
│   └── [Caching logic]
├── get_migrate_projects()
│   └── list_all()
└── get_migration_appliances()
    ├── post() [Resource Graph API]
    └── _parse_resource_graph_appliances()
```

### 4. Server Validation Call Graph

```
ServersValidator.validate_all()
├── [For each config and enabled validation:]
├── validate_region()
│   ├── _get_compute_client()
│   └── Azure Locations API
├── validate_resource_group()
│   ├── _get_resource_client()
│   └── Resource Groups API
├── validate_vnet_and_subnet()
│   ├── _get_network_client()
│   └── Virtual Networks API
├── validate_vm_sku()
│   ├── _get_compute_client()
│   └── Resource SKUs API
├── validate_disk_type()
│   └── [Disk compatibility logic]
├── validate_rbac_resource_group()
│   ├── _get_authorization_client()
│   └── Role Assignments API
└── validate_discovery()
    ├── AzureMigrateApiClient.search_machines_by_name()
    └── [Migration readiness check]
```

### 5. Landing Zone Validation Call Graph

```
LandingZoneValidator.validate_project()
├── validate_access()
│   ├── _get_authorization_client()
│   ├── Role Assignments API
│   └── [Multiple RBAC checks]
├── validate_appliance_health()
│   ├── AzureMigrateApiClient.get_migration_appliances()
│   └── [Health assessment logic]
├── validate_storage_cache()
│   ├── _get_storage_client()
│   ├── Storage Accounts API
│   └── [Auto-creation if enabled]
└── validate_quota()
    ├── _get_compute_client()
    ├── Usage API
    └── [Quota calculation]
```

### 6. Consolidated Validation Call Graph

```
ConsolidatedValidator.validate_all()
├── _extract_unique_lz_configs()
│   └── _get_project_key()
├── [For each unique LZ config:]
│   └── LandingZoneValidator.validate_project()
├── [For each server config:]
│   └── ServersValidator.validate_all()
└── [Results aggregation]
```

### 7. Intelligent Validation Call Graph

```
IntelligentServerValidator.validate_servers_with_project_matching()
├── ConfigParser.parse()
├── _match_servers_to_projects()
│   ├── [For each server:]
│   └── _find_best_project_match()
│       ├── _get_discovered_machines()
│       │   └── AzureMigrateIntegration.get_discovered_machines()
│       ├── AzureMigrateApiClient.search_machines_by_name()
│       └── _extract_ip_address()
└── [For each matched project:]
    └── ServersValidator.validate_all()
```

## Cross-Module Dependencies

### Authentication Flow
```
CLI/Wizard
├── CachedCredentialFactory.create_credential()
│   ├── [Based on auth method:]
│   ├── AzureCliCredential()
│   ├── ClientSecretCredential()
│   └── ManagedIdentityCredential()
└── [Pass credential to:]
    ├── AzureMigrateApiClient()
    ├── ServersValidator()
    ├── LandingZoneValidator()
    └── IntelligentServerValidator()
```

### Validation Configuration Flow
```
get_validation_config() [Singleton]
├── ValidationConfig.__init__()
├── [Profile resolution]
└── [Used by all validators:]
    ├── ServersValidator.is_*_validation_enabled()
    ├── LandingZoneValidator.is_*_validation_enabled()
    └── ConsolidatedValidator
```

### Azure Client Management
```
Azure Management Clients (Cached):
├── ServersValidator
│   ├── _get_resource_client()
│   ├── _get_compute_client()
│   └── _get_network_client()
├── LandingZoneValidator
│   ├── _get_resource_client()
│   ├── _get_storage_client()
│   ├── _get_authorization_client()
│   └── _get_compute_client()
└── [Shared caching mechanism]
```

### Data Flow Through System
```
Input Files (CSV/JSON/Excel)
└── ConfigParser
    └── MigrationConfig / MigrateProjectConfig objects
        └── Validators
            └── ValidationResult objects
                └── MachineValidationReport / ProjectReadinessResult
                    └── EnhancedTableFormatter
                        └── Rich Console Output
```

## Error Handling Flow

### API Error Handling
```
Azure API Calls
├── HttpResponseError
│   ├── [Status code analysis]
│   ├── [Retry logic for transient errors]
│   └── ValidationResult(passed=False)
├── ResourceNotFoundError
│   └── ValidationResult(passed=False, specific message)
└── General Exception
    └── ValidationResult(passed=False, error details)
```

### Validation Error Propagation
```
Individual Validation Method
└── ValidationResult
    └── MachineValidationReport / ProjectReadinessResult
        └── Wizard Display
            ├── EnhancedTableFormatter
            └── Console Output with Rich formatting
```

## Performance Optimization Call Paths

### Caching Mechanisms
```
1. Azure Client Caching:
   Validators._get_*_client() → Cache lookup → Reuse existing clients

2. Machine Discovery Caching:
   AzureMigrateApiClient.list_discovered_machines(use_cache=True)
   └── Internal cache → Avoid repeated API calls

3. Credential Caching:
   CachedCredentialFactory → Token reuse → Avoid re-authentication

4. Project Deduplication:
   ConsolidatedValidator._extract_unique_lz_configs()
   └── Avoid duplicate project validations
```

### Bulk Operations
```
ServersValidator.validate_all()
├── [Single credential for all validations]
├── [Cached Azure clients]
├── [Batched API calls where possible]
└── [Parallel processing potential]
```

## Integration Points

### External Dependencies
```
Azure SDK Clients:
├── ResourceManagementClient
├── ComputeManagementClient  
├── NetworkManagementClient
├── StorageManagementClient
├── AuthorizationManagementClient
└── Custom REST API calls

Data Processing:
├── pandas (Excel/CSV parsing)
├── json (JSON parsing)
└── pathlib (File operations)

UI/Output:
├── rich (Console formatting)
├── argparse (CLI parsing)
└── typing (Type annotations)
```

### API Endpoints Used
```
Azure REST APIs:
├── /subscriptions/{id}/resourceGroups/{rg}/providers/Microsoft.Migrate/
│   ├── migrateProjects/{project}/machines/{machine}
│   ├── migrateProjects/{project}/machines
│   └── migrateProjects
├── /subscriptions/{id}/providers/Microsoft.Resources/
│   └── resourceGroups, locations, subscriptions
├── /subscriptions/{id}/providers/Microsoft.Compute/
│   └── skus, usage
├── /subscriptions/{id}/providers/Microsoft.Network/
│   └── virtualNetworks, subnets
├── /subscriptions/{id}/providers/Microsoft.Storage/
│   └── storageAccounts
└── /subscriptions/{id}/providers/Microsoft.Authorization/
    └── roleAssignments, roleDefinitions
```

This call graph documentation complements the function reference by showing how all the pieces fit together in the application's execution flow.