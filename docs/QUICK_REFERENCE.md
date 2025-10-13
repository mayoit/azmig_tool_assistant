# Azure Bulk Migration Tool - Quick Reference Guide

This guide provides a quick reference for all interactive prompts, options, and required inputs.

---

## Command Line Entry Points

| Command | Description |
|---------|-------------|
| `azmig` | Interactive Azure migration tool |
| `azmig --help` | Display help information |
| `azmig --create-default-config` | Create default config |
| `azmig --non-interactive` | Non-interactive mode |

---

## Operation Types

| # | Operation | Required Files | Auth Required | Description |
|---|-----------|----------------|----------------------|-------------|
| 1 | Landing Zone Validation | LZ file (CSV/JSON) | ✓ Yes | Validates Azure Migrate project readiness |
| 2 | Server Validation | Excel file | ✓ Yes | Validates individual server configurations |
| 3 | Enable Replication | Excel file | ✓ Yes | Enables replication for validated servers |
| 4 | Configure Validations | None | ✗ No | Interactive validation config editor |
| 5 | Full Migration Wizard | LZ + Excel files | ✓ Yes | Complete end-to-end workflow |

---

## Landing Zone File Requirements

### Required Fields (8)

| Field | Example | Description |
|-------|---------|-------------|
| `subscription_id` | `12345678-1234-1234-1234-123456789012` | Azure subscription GUID |
| `resource_group` | `migrate-rg-eastus` | Resource group name |
| `migrate_project_name` | `MigrateProject-EastUS` | Azure Migrate project name |
| `recovery_vault_name` | `RecoveryVault-EastUS` | Recovery Services vault name |
| `region` | `eastus` | Azure region |
| `cache_storage_account` | `cachestorage001` | Cache storage account name |
| `appliance_name` | `MigrateAppliance-VMware-EastUS` | Azure Migrate appliance name |
| `virtualization_type` | `vmware` | Source platform type |

### Virtualization Types

| Value | Description | Use Case |
|-------|-------------|----------|
| `vmware` | VMware vSphere | VMware ESXi servers |
| `hyperv` | Microsoft Hyper-V | Hyper-V hosts |
| `physical` | Physical/Other | Physical servers, AWS EC2, GCP, Xen, etc. |

### File Formats

**CSV Example:**
```csv
subscription_id,resource_group,migrate_project_name,recovery_vault_name,region,cache_storage_account,appliance_name,virtualization_type
12345678-1234-1234-1234-123456789012,migrate-rg-eastus,MigrateProject-EastUS,RecoveryVault-EastUS,eastus,cachestorage001,MigrateAppliance-VMware-EastUS,vmware
```

**JSON Example:**
```json
[
  {
    "subscription_id": "12345678-1234-1234-1234-123456789012",
    "resource_group": "migrate-rg-eastus",
    "migrate_project_name": "MigrateProject-EastUS",
    "recovery_vault_name": "RecoveryVault-EastUS",
    "region": "eastus",
    "cache_storage_account": "cachestorage001",
    "appliance_name": "MigrateAppliance-VMware-EastUS",
    "virtualization_type": "vmware"
  }
]
```

**Template Files:**
- `examples/template_landing_zones.csv`
- `examples/template_landing_zones.json`

---

## Servers Excel File Requirements

### Required Columns

| Column | Example | Description |
|--------|---------|-------------|
| `source_machine_name` | `WebServer01` | Source server hostname |
| `target_vm_name` | `webapp-vm-01` | Target Azure VM name |
| `target_resource_group` | `prod-web-rg` | Target resource group |
| `target_region` | `eastus` | Target Azure region |
| `target_vnet` | `prod-vnet` | Target virtual network |
| `target_subnet` | `web-subnet` | Target subnet |
| `target_vm_size` | `Standard_D2s_v3` | Target VM SKU |
| `target_disk_type` | `Premium_LRS` | Disk type |

### Common File Locations

The tool automatically searches for:
- `servers.xlsx`
- `migration.xlsx`
- `tests/data/sample_migration.xlsx`

**Template File:**
- `examples/servers.csv` (can be converted to Excel)

---

## Project Validation Settings

Azure Migration Tool uses **project-persistent validation settings** that are saved with each migration project. Settings are configured once per project and automatically applied to all validations.

### Configuration Management
- **Per-Project**: Settings are saved in `project.json` 
- **Interactive Editor**: Modify settings via wizard interface
- **Preset Profiles**: Default, Quick, and Full validation profiles
- **Persistent**: No need to reconfigure for each session

---

## Validation Configuration

### Landing Zone Validations

| Validation | Config Key | Default | Description |
|------------|-----------|---------|-------------|
| Access Validation (RBAC) | `landing_zone.access_validation.enabled` | `true` | Checks RBAC permissions |
| Appliance Health | `landing_zone.appliance_health.enabled` | `true` | Validates appliance status |
| Storage Cache | `landing_zone.storage_cache.enabled` | `true` | Checks cache storage account |
| Quota Validation | `landing_zone.quota_validation.enabled` | `true` | Verifies quota availability |

### Server Validations

| Validation | Config Key | Default | Description |
|------------|-----------|---------|-------------|
| Region Validation | `servers.region_validation.enabled` | `true` | Validates target region |
| Resource Group | `servers.resource_group_validation.enabled` | `true` | Checks resource group exists |
| VNet/Subnet | `servers.vnet_subnet_validation.enabled` | `true` | Validates network config |
| VM SKU | `servers.vm_sku_validation.enabled` | `true` | Checks SKU availability |
| Disk Type | `servers.disk_type_validation.enabled` | `true` | Validates disk type |
| Discovery Status | `servers.discovery_validation.enabled` | `true` | Checks server discovered |
| RBAC Permissions | `servers.rbac_validation.enabled` | `true` | Validates permissions |

### Global Settings

| Setting | Config Key | Default | Description |
|---------|-----------|---------|-------------|
| Fail Fast | `global.fail_fast` | `false` | Stop on first error |
| Parallel Execution | `global.parallel_execution` | `false` | Run validations in parallel |
| Timeout | `global.timeout_seconds` | `300` | Validation timeout (seconds) |
| Retry Enabled | `global.retry_on_failure.enabled` | `false` | Retry on failure |
| Max Retries | `global.retry_on_failure.max_retries` | `3` | Maximum retry attempts |
| Retry Delay | `global.retry_on_failure.retry_delay_seconds` | `5` | Delay between retries |

---

## Authentication Methods

| # | Method | Description | Required Parameters |
|---|--------|-------------|---------------------|
| 1 | `azure_cli` | Azure CLI login | None (uses existing login) |
| 2 | `managed_identity` | VM/AKS identity | `client_id` (optional) |
| 3 | `service_principal` | App registration | `tenant_id`, `client_id`, `client_secret` |
| 4 | `interactive` | Browser flow | None (browser popup) |
| 5 | `device_code` | Device flow | None (device code displayed) |
| 6 | `default` | Auto-detect | None (tries multiple methods) |

---

## Common Workflows

### Workflow 1: Quick Configuration Test

```bash
# Start interactive tool
azmig

# Prompts:
# Select: 4 (Configure Validations)
# Config: Y (Create default)
# Profile: 2 (Quick)
# Landing Zone Validations: [Y/n for each]
# Server Validations: [Y/n for each]
# Save: Y

# Result: Configuration created successfully
```

### Workflow 2: Production Server Validation

```bash
# Start Azure validation
azmig

# Prompts:
# Select: 2 (Server Validation)
# Auth: 1 (azure_cli)
# Config: Y (Use existing validation_config.yaml)
# Profile: 1 (Full)
# Excel: servers.xlsx
# Export JSON: Y → results.json
# Proceed: Y

# Result: Azure validation with JSON export
```

### Workflow 3: Configure Validations Only

```bash
# Start configuration wizard
azmig

# Prompts:
# Select: 4 (Configure Validations)
# Config exists: N → Create default
# Landing Zone Validations: [Y/n for each]
# Server Validations: [Y/n for each]
# Global Settings: [Y/n for each]
# Save: Y → validation_config.yaml

# Result: validation_config.yaml created, tool exits
```

### Workflow 4: Full Migration Wizard

```bash
# Start full migration wizard
azmig

# Prompts:
# Select: 5 (Full Wizard)
# Auth: 3 (service_principal)
# Tenant ID: [enter]
# Client ID: [enter]
# Client Secret: [enter]
# Config: Y (Create default)
# Profile: 1 (Full)
# LZ File: template_landing_zones.csv
# Excel: migration.xlsx
# Export JSON: Y → migration_results.json
# Proceed: Y

# Result: Three-phase migration execution
# Phase 1: Landing Zone Validation
# Phase 2: Server Validation
# Phase 3: Enable Replication
```

---

## Prompt Responses

### Yes/No Prompts

| Prompt Pattern | Default | Meaning |
|----------------|---------|---------|
| `[Y/n]` | Yes | Press Enter for Yes, type 'n' for No |
| `[y/N]` | No | Press Enter for No, type 'y' for Yes |

### Choice Prompts

| Prompt Pattern | Example | Usage |
|----------------|---------|-------|
| `[1/2/3/4/5]` | Select operation | Enter number to choose |
| `(default: 5)` | Default choice | Press Enter to use default |

---

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `File not found` | Path incorrect or file missing | Verify file path and existence |
| `--operation required in non-interactive mode` | Missing CLI parameter | Provide `--operation` flag or remove `--non-interactive` |
| `Authentication failed` | Invalid credentials | Check auth method and credentials |
| `AttributeError: ... has no attribute ...` | Code bug | Report issue or check for updates |

---

## Export Options

### JSON Export

When prompted `Export results to JSON? [y/N]`:

- **Yes**: Results saved to specified JSON file
- **No**: Results displayed on screen only
- **Default filename**: `migration_results.json`

### JSON Output Structure

```json
{
  "operation": "lz_validation",
  "timestamp": "2025-10-06T10:30:00Z",
  "azure_integration": true,
  "results": [
    {
      "landing_zone": "LZ-EastUS",
      "status": "success",
      "validations": {
        "subscription_access": "passed",
        "migrate_project": "passed",
        "recovery_vault": "passed",
        "appliance_health": "passed",
        "cache_storage": "passed",
        "quota": "passed",
        "rbac": "passed"
      },
      "issues": []
    }
  ],
  "summary": {
    "total": 2,
    "passed": 2,
    "failed": 0,
    "warnings": 0
  }
}
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Accept default or submit input |
| `Ctrl+C` | Cancel/Exit tool |
| `y` or `n` | Yes or No response |
| `1-5` | Select numbered option |

---

## Tips & Best Practices

### 1. Start with Configuration
```bash
# Always configure validations first
azmig
# Select: 4 (Configure Validations)
```

### 2. Use Templates
- Copy template files from `examples/` directory
- Modify with your actual data
- Validate format before using

### 3. Configure Project Validation Settings
```bash
# Use wizard to manage project settings
azmig
# Project settings are saved automatically
# Modify via validation settings editor
```

### 4. Use Preset Profiles for Different Scenarios
- **Development**: Quick profile (minimal validations)
- **UAT**: Default profile (balanced validation)
- **Production**: Full profile (comprehensive validation)

### 5. Export Results for Documentation
- Always export JSON for production runs
- Keep JSON files for audit trail
- Use JSON for reporting and analysis

### 6. Authentication Best Practices
- **Development**: Use `azure_cli` (easiest)
- **CI/CD**: Use `service_principal`
- **Azure VMs**: Use `managed_identity`
- **Interactive**: Use `interactive` or `device_code`

---

## File Locations

### Input Files
- Landing Zone templates: `examples/template_landing_zones.{csv,json}`
- Server template: `examples/servers.csv`
- Validation config: `validation_config.yaml` (root directory)

### Output Files
- JSON exports: Current directory (or specified path)
- Logs: `validation.log` (if enabled in config)
- Created configs: Current directory (or specified path)

---

## Getting Help

### In-Tool Help
```bash
# Show help
azmig --help
```

### Documentation
- **Interactive Guide**: `docs/INTERACTIVE_GUIDE.md`
- **Features**: `docs/FEATURES.md`
- **Sequence Diagram**: `docs/SEQUENCE_DIAGRAM.md`
- **Flowchart**: `docs/FLOWCHART.md`
- **Installation**: `docs/INSTALLATION.md`

### Common Issues
1. **"Could not find platform independent libraries"** - Ignore (Python warning, doesn't affect functionality)
2. **File not found** - Use absolute paths or ensure file exists
3. **Authentication failed** - Verify credentials and auth method
4. **Config errors** - Recreate with `--create-default-config`

---

## Summary Cheat Sheet

```
QUICK START:
1. azmig                           → Start interactive tool
2. Select operation (1-5)          → Choose what to do
3. Follow prompts                  → Enter required info
4. Review summary                  → Verify before execution
5. Proceed                         → Execute operation

COMMON COMMANDS:
azmig                              → Interactive tool
azmig --help                       → Show help
azmig --create-default-config      → Create config
azmig --non-interactive            → Non-interactive mode

OPERATIONS:
1 = Landing Zone Validation
2 = Server Validation
3 = Enable Replication
4 = Configure Validations
5 = Full Migration Wizard

PROFILES:
1 = full (all validations)
2 = quick (fast validation)
3 = rbac_only (permissions)
4 = resource_only (infrastructure)
5 = default (standard)

AUTHENTICATION (Live Mode):
1 = azure_cli
2 = managed_identity
3 = service_principal
4 = interactive
5 = device_code
6 = default (auto)
```

---

Last Updated: October 6, 2025
Version: 1.0.0-dev
