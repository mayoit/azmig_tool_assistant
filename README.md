# Azure Migration Tool 🚀

A comprehensive Python CLI tool for bulk server migration from on-premises to Azure using Azure Migrate and Site Recovery. Features live Azure integration with intelligent validation and project matching.

## ✨ Features

- **🏗️ Two-Layer Validation**: Landing Zone (project-level) and Servers (machine-level) validation
- **🧠 Intelligent Validation**: Automatic server-to-project matching with discovery integration
- **☁️ Live Azure Integration**: Real-time validation against Azure APIs
- **📊 Rich Reporting**: Comprehensive validation results with detailed insights
- **⚙️ Configuration-Driven**: Flexible validation profiles and customizable rules
- **🔒 Secure Authentication**: Multiple auth methods (Azure CLI, Service Principal, Managed Identity)
- **📈 Progress Tracking**: Real-time validation progress with detailed status updates

## 📋 Requirements

- **Python**: 3.9 or higher
- **Azure Access**: Valid Azure credentials with appropriate permissions
- **Network**: Outbound HTTPS access to Azure APIs
- **Permissions**: Minimum Reader on subscription, Contributor on target resources

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/azmig_tool_assistant.git
cd azmig_tool_assistant

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install the tool
pip install -e .
```

### Basic Usage

```bash
# Interactive wizard (recommended for first-time users)
azmig

# Direct validation with Excel file
azmig validate --excel-file migration_servers.xlsx

# Landing zone validation with CSV
azmig validate --csv-file migrate_projects.csv --type landing-zone

# Use specific validation profile
azmig validate --excel-file servers.xlsx --profile quick
```

## 📝 Input File Formats

### Landing Zone Configuration (CSV/JSON)
Required fields for Azure Migrate project validation:

| Field | Description | Example |
|-------|-------------|---------|
| migrate_project_name | Azure Migrate project name | `MyMigrationProject` |
| migrate_resource_group | Resource group containing project | `rg-migration` |
| migrate_project_subscription | Subscription ID | `12345678-1234-5678-9012-123456789012` |
| region | Target Azure region | `East US` |
| appliance_name | Azure Migrate appliance name | `MigrationAppliance01` |

### Server Configuration (Excel)
Required columns for machine-level validation:

| Column | Description | Example |
|--------|-------------|---------|
| Target Machine Name | Server name in target environment | `web-server-01` |
| Target Region | Target Azure region | `East US` |
| Target Subscription | Target subscription ID | `12345678-1234-5678-9012-123456789012` |
| Target RG | Target resource group | `rg-production` |
| Target Vnet | Target virtual network | `vnet-prod` |
| Target Subnet | Target subnet | `subnet-web` |
| Target Machine Sku | Target VM SKU | `Standard_D4s_v3` |
| Target Disk Type | Target disk type | `Premium_LRS` |

## 🔧 Configuration

### Validation Configuration (`validation_config.yaml`)

```yaml
# Active validation profile
active_profile: "default"

# Global settings
global:
  fail_fast: false           # Stop on first validation failure
  parallel_execution: true   # Run validations concurrently
  timeout_seconds: 300      # API call timeout

# Landing zone validations
landing_zone:
  access_validation:
    enabled: true
    checks:
      migrate_project_rbac: {enabled: true}
      recovery_vault_rbac: {enabled: true}
  appliance_health: {enabled: true}
  storage_cache: {enabled: true, auto_create_if_missing: false}
  quota_validation: {enabled: true}

# Server validations  
servers:
  region_validation: {enabled: true}
  resource_group_validation: {enabled: true}
  vnet_subnet_validation: {enabled: true}
  vm_sku_validation: {enabled: true}
  disk_type_validation: {enabled: true}
  discovery_validation: {enabled: true}
  rbac_validation: {enabled: true}

# Validation profiles
profiles:
  quick:
    overrides:
      servers.rbac_validation.enabled: false
      servers.discovery_validation.enabled: false
  
  full:
    # All validations enabled (default)
    
  rbac_only:
    overrides:
      servers.region_validation.enabled: false
      servers.vnet_subnet_validation.enabled: false
```

## 🔐 Authentication

### Azure CLI Authentication (Recommended)
```bash
# Login with Azure CLI
az login

# Verify access
az account show

# Run validation
azmig validate --excel-file servers.xlsx
```

### Service Principal Authentication
```bash
# Set environment variables
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"

# Run validation
azmig validate --excel-file servers.xlsx --auth-method service_principal
```

### Managed Identity Authentication (Azure VMs)
```bash
# On Azure VM with managed identity
azmig validate --excel-file servers.xlsx --auth-method managed_identity
```

## 📊 Sample Output

### Landing Zone Validation Results
```
🏗️ Landing Zone Validation Summary
┌─────────────────────┬────────┬────────────────────────┐
│ Project Name        │ Status │ Issues                 │
├─────────────────────┼────────┼────────────────────────┤
│ MigrationProject01  │ ✅ Ready│ 0 issues              │
│ MigrationProject02  │ ⚠️ Issues│ Missing cache storage │
│ MigrationProject03  │ ❌ Failed│ Insufficient quotas   │
└─────────────────────┴────────┴────────────────────────┘
```

### Server Validation Results
```
🖥️ Servers Validation Summary  
┌─────────────────┬──────────────┬─────────────┬────────┐
│ Machine Name    │ Target Region│ Validations │ Status │
├─────────────────┼──────────────┼─────────────┼────────┤
│ web-server-01   │ East US      │ 7✅ 0❌    │ ✅ Ready│
│ app-server-02   │ West US 2    │ 6✅ 1❌    │ ⚠️ Issues│
│ db-server-03    │ Central US   │ 4✅ 3❌    │ ❌ Failed│
└─────────────────┴──────────────┴─────────────┴────────┘
```

### Intelligent Validation Results
```
🧠 Intelligent Validation Summary
┌─────────────────────┬───────┬────────┐
│ Metric              │ Count │ Status │
├─────────────────────┼───────┼────────┤
│ Total Servers       │     5 │        │
│ Project Matches     │     4 │ 4/5    │
│ Discovered Machines │     3 │ 3/5    │  
│ Migration Ready     │     3 │ 3/5    │
└─────────────────────┴───────┴────────┘
```

## 🎯 Validation Types

### Landing Zone Validation
- ✅ **Access Validation**: RBAC permissions for Azure Migrate and Site Recovery
- ✅ **Appliance Health**: Azure Migrate appliance status and connectivity  
- ✅ **Storage Cache**: Cache storage account validation and auto-creation
- ✅ **Quota Validation**: vCPU and resource quotas in target regions

### Server Validation  
- ✅ **Region Validation**: Target Azure region availability
- ✅ **Resource Group**: Target resource group existence and access
- ✅ **Network Validation**: VNet and subnet configuration
- ✅ **VM SKU Validation**: Target VM SKU availability and compatibility
- ✅ **Disk Validation**: Disk type and configuration validation
- ✅ **Discovery Validation**: Machine discovery status in Azure Migrate
- ✅ **RBAC Validation**: Machine-specific access permissions

### Intelligent Validation (Advanced)
- 🧠 **Project Matching**: Automatic server-to-project association
- 🧠 **Discovery Integration**: Live Azure Migrate discovery status  
- 🧠 **Cross-Subscription**: Handle complex enterprise scenarios
- 🧠 **Enhanced Reporting**: Detailed insights and recommendations

## 🔧 Command Line Options

### Global Options
```bash
azmig [OPTIONS] COMMAND [ARGS]...

Options:
  --auth-method [azure_cli|service_principal|managed_identity]
                        Azure authentication method
  --profile TEXT        Validation profile (default, quick, full, rbac_only)
  --non-interactive     Run without interactive prompts
  --debug              Enable debug logging
  --help               Show help message
```

### Validation Commands
```bash
# Validate with Excel file (servers)
azmig validate --excel-file FILE [--profile PROFILE]

# Validate with CSV file (landing zone)  
azmig validate --csv-file FILE --type landing-zone

# Validate with JSON file (landing zone)
azmig validate --json-file FILE --type landing-zone

# Intelligent validation (combines both layers)
azmig validate --excel-file FILE --intelligent

# Custom validation config
azmig validate --excel-file FILE --config custom_config.yaml
```

### Interactive Mode
```bash
# Launch interactive wizard
azmig

# Launch with specific authentication
azmig --auth-method service_principal
```

## 📁 Project Structure

```
azmig_tool/
├── core/              # Core business logic and models
├── interface/         # CLI, wizard, and user interaction
├── utils/             # Authentication utilities
├── management/        # Project and template management
├── config/            # Configuration parsing and validation
├── validators/        # Validation engine with core validators and wrappers
│   ├── core/          # Individual resource validators (region, vnet, vmsku, etc.)
│   └── wrappers/      # Orchestration wrappers (landing zone, servers, intelligent)
├── clients/           # Azure API clients (Azure Migrate, Resource Manager)
└── base/              # Base interfaces and contracts
```

## 🚨 Common Issues & Solutions

### Authentication Issues
```bash
# Issue: "Authentication failed"
# Solution: Re-login with Azure CLI
az login --tenant YOUR_TENANT_ID

# Issue: "Insufficient permissions"
# Solution: Ensure user has required roles:
# - Reader on subscription
# - Contributor on target resource groups
```

### Validation Errors
```bash
# Issue: "Resource not found"  
# Solution: Verify resource names and subscription access

# Issue: "Quota exceeded"
# Solution: Request quota increase in Azure portal

# Issue: "Network configuration invalid"
# Solution: Verify VNet/subnet names and regions match
```

### Performance Issues
```bash
# Issue: Slow validation
# Solution: Use quick profile for faster results
azmig validate --excel-file servers.xlsx --profile quick

# Issue: API throttling
# Solution: Tool automatically retries with backoff
```

## 📖 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - Technical architecture and design patterns
- **[Installation Guide](docs/INSTALLATION.md)** - Detailed installation steps (coming soon)
- **[User Guide](docs/USER_GUIDE.md)** - Complete usage guide (coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)  
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See [docs/](docs/) folder for detailed guides
- **Issues**: Report bugs and feature requests on GitHub Issues
- **Architecture**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details

## 🏷️ Version History

- **v3.0.0**: Major architecture refactor with organized folder structure and intelligent validation
- **v2.x.x**: Enhanced Azure integration and validation profiles
- **v1.x.x**: Initial release with basic validation capabilities

---

**Made with ❤️ for Azure Migration Projects**
