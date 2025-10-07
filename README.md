# 🛠️ Azure Bulk Migration Tool

[![Python 3.8+](https://img.shields.io/badge/## 📖 Docu## 📖 D---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[USER_GUIDE.md](docs/USER_GUIDE.md)** 🌟 | **Complete guide with features, workflows, and diagrams - START HERE** |
| **[INSTALLATION.md](docs/INSTALLATION.md)** | Complete installation guide with troubleshooting |
| **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** 📋 | Command quick reference |
| **[DOCUMENTATION_SUMMARY.md](docs/DOCUMENTATION_SUMMARY.md)** | Overview of all documentation |
| **[ROADMAP.md](docs/ROADMAP.md)** | Future enhancements and development roadmap |

---| Document | Description |
|----------|-------------|
| **[INTERACTIVE_GUIDE.md](docs/INTERACTIVE_GUIDE.md)** 🌟 | **NEW:** Step-by-step interactive wizard guide |
| **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** 📋 | **NEW:** Quick reference for prompts, options, and workflows |
| **[SEQUENCE_DIAGRAM.md](docs/SEQUENCE_DIAGRAM.md)** 📊 | **NEW:** Complete sequence diagrams for all flows |
| **[FLOWCHART.md](docs/FLOWCHART.md)** 🔄 | **NEW:** Mermaid flowcharts for visual reference |
| **[INSTALLATION.md](docs/INSTALLATION.md)** | Complete installation guide with troubleshooting |
| **[FEATURES.md](docs/FEATURES.md)** | Comprehensive feature documentation and validation configuration |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical architecture and design patterns |
| **[ROADMAP.md](docs/ROADMAP.md)** | Future enhancements and development roadmap |n

| Document | Description |
|----------|-------------|
| **[INTERACTIVE_GUIDE.md](docs/INTERACTIVE_GUIDE.md)** 🌟 | **NEW:** Step-by-step interactive wizard guide |
| **[INSTALLATION.md](docs/INSTALLATION.md)** | Complete installation guide with troubleshooting |
| **[FEATURES.md](docs/FEATURES.md)** | Comprehensive feature documentation and validation configuration |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical architecture and design patterns |
| **[ROADMAP.md](docs/ROADMAP.md)** | Future enhancements and development roadmap |.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-3.0.0-green.svg)](https://github.com/atef-aziz/azmig_tool)

A comprehensive CLI tool for **bulk migrating servers from on-premises data centers to Azure** using Azure Migrate and Azure Site Recovery.

## ✨ Key Features

- 🎯 **Interactive Wizard** 🌟 **NEW** - Guided step-by-step workflow with smart prompts
- 🎯 **Two-Layer Validation** - Landing Zone (project-level) + Servers (machine-level)
- ⚙️ **Configurable Validations** - YAML-based configuration with profiles
- 🔐 **Flexible Authentication** - 6 authentication methods (Azure CLI, Managed Identity, Service Principal, etc.)
- 📊 **Excel-Based Configuration** - Simple spreadsheet format
- 🧙 **Operation Modes** - Landing Zone validation, Server validation, Replication, or Full wizard
- 🧪 **Mock Mode** - Test offline without Azure connectivity
- ☁️ **Live Mode** - Full Azure integration with real-time validation
- 📦 **Batch Processing** - Validate multiple servers simultaneously
- 🎨 **Rich CLI Interface** - Color-coded output with progress indicators

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/atef-aziz/azmig_tool.git
cd azmig_tool_package

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install
pip install -r requirements.txt
pip install -e .
```

**📖 Detailed instructions:** [INSTALLATION.md](docs/INSTALLATION.md)

### Basic Usage

**🌟 NEW: Interactive Wizard (Simplest)**
```bash
# Just run the tool - it guides you through everything!
azmig --live

# Or start in mock mode for offline testing
azmig --mock
```

The wizard interactively prompts for:
- ✓ Authentication method (Live mode)
- ✓ Operation type (validation, replication, etc.)
- ✓ File paths (Excel, CSV, JSON)
- ✓ Validation configuration
- ✓ Export options

**Traditional CLI (Advanced)**
```bash
# Test in Mock Mode
azmig --mock --excel tests/data/sample_migration.xlsx

# Run in Live Mode with all parameters
az login
azmig --live \
      --auth-method azure_cli \
      --operation server_validation \
      --excel migration.xlsx \
      --validation-profile full
```

**📖 Complete interactive guide:** [INTERACTIVE_GUIDE.md](docs/INTERACTIVE_GUIDE.md)

---

## � Documentation

| Document | Description |
|----------|-------------|
| **[INSTALLATION.md](docs/INSTALLATION.md)** | Complete installation guide with troubleshooting |
| **[FEATURES.md](docs/FEATURES.md)** | Comprehensive feature documentation and validation configuration |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical architecture and design patterns |
| **[ROADMAP.md](docs/ROADMAP.md)** | Future enhancements and development roadmap |

---

## 🎯 Key Capabilities

### Two-Layer Validation

**Landing Zone (Project-Level):**
- ✓ RBAC permissions (Migrate Project, Recovery Vault, Subscription)
- ✓ Appliance health and connectivity
- ✓ Cache storage account
- ✓ vCPU quota availability

**Servers (Machine-Level):**
- ✓ Azure region validation
- ✓ Resource group existence
- ✓ VNet/Subnet configuration
- ✓ VM SKU availability
- ✓ Disk type compatibility
- ✓ Azure Migrate discovery status
- ✓ RBAC permissions on target resources

### Validation Profiles

| Profile | Description | Use Case |
|---------|-------------|----------|
| `full` | All validations enabled | Production migrations |
| `quick` | Fast validation, skip time-consuming checks | Development/testing |
| `rbac_only` | Permission checks only | Access verification |
| `resource_only` | Infrastructure checks only | Resource readiness |

**📖 Learn more:** [FEATURES.md - Validation Profiles](docs/FEATURES.md#validation-profiles)

---

## 💻 CLI Options

### Interactive Mode (Recommended)

```bash
# Start interactive wizard
azmig --live          # Live mode with prompts
azmig --mock          # Mock mode with prompts
azmig                 # Prompts for mode selection
```

### Traditional CLI Mode

```bash
azmig [OPTIONS]

Core Options:
  --live                    Run in live Azure mode
  --mock                    Run in mock/simulation mode
  --non-interactive         Disable prompts (requires all parameters)

Operation Options:
  --operation TYPE          Operation type:
                           - lz_validation: Landing Zone validation only
                           - server_validation: Server validation only  
                           - replication: Enable replication
                           - configure_validations: Interactive config editor
                           - full_wizard: Complete workflow (default)

Authentication (Live Mode):
  --auth-method METHOD      azure_cli | managed_identity | service_principal |
                           interactive | device_code | default
  --tenant-id ID           Azure tenant ID
  --client-id ID           Client/application ID  
  --client-secret SECRET   Client secret

Files:
  --excel PATH             Path to Excel mapping file
  --lz-file PATH           Path to Landing Zone CSV/JSON file
  --validation-config PATH Path to validation YAML
  --validation-profile NAME Validation profile (quick|full|rbac_only|resource_only)

Output:
  --export-json PATH       Export results to JSON
  --create-default-config  Create default validation_config.yaml

Help:
  -h, --help               Show help message
```

**📖 See examples:** [INTERACTIVE_GUIDE.md](docs/INTERACTIVE_GUIDE.md)

---

## 📋 Excel Configuration

**Required Columns:**
- `target_machine_name` - Azure VM name
- `target_region` - Azure region (e.g., `eastus`)
- `target_subscription` - Subscription ID
- `target_rg` - Resource group name
- `target_vnet` - Virtual network name
- `target_subnet` - Subnet name
- `target_machine_sku` - VM SKU (e.g., `Standard_D4s_v3`)
- `target_disk_type` - Disk type (e.g., `Premium_LRS`)

**Sample Template:**

| target_machine_name | target_region | target_rg | target_vnet | target_subnet | target_machine_sku | target_disk_type |
|---------------------|---------------|-----------|-------------|---------------|--------------------|------------------|
| web-server-01 | eastus | migration-rg | migration-vnet | default | Standard_D4s_v3 | Premium_LRS |
| db-server-01 | eastus | migration-rg | migration-vnet | database | Standard_E8s_v3 | Premium_LRS |

**📖 Full requirements:** [FEATURES.md - Excel Configuration](docs/FEATURES.md#excel-based-configuration)

---

## 🔐 Authentication & Permissions

**Authentication Methods:**
The tool supports **6 authentication methods** similar to Azure CLI:

1. **Azure CLI** - `az login` (Recommended for development)
2. **Managed Identity** - System or user-assigned (Best for production)
3. **Service Principal** - Client ID + Secret (Best for automation/CI-CD)
4. **Interactive Browser** - Opens browser for sign-in
5. **Device Code** - For SSH/remote sessions
6. **Default Chain** - Auto-detects best method

**Usage Examples:**
```bash
# Azure CLI (recommended)
az login
azmig --live --auth-method azure_cli --excel servers.xlsx

# Managed Identity (on Azure VM/App Service)
azmig --live --auth-method managed_identity --excel servers.xlsx

# Service Principal (automation)
azmig --live --auth-method service_principal \
    --tenant-id "xxx" --client-id "yyy" --client-secret "zzz" \
    --excel servers.xlsx

# Let tool prompt for method
azmig --live --excel servers.xlsx
```

**Required Permissions:**
- **Reader** on subscription
- **Contributor** on Azure Migrate project
- **Contributor** on Recovery Services Vault
- **Contributor** on target resource groups

**📖 Complete authentication guide:** [INSTALLATION.md - Azure Authentication](docs/INSTALLATION.md#azure-authentication)

---

## 🐛 Troubleshooting

**Common issues and solutions:**

| Issue | Solution |
|-------|----------|
| Excel file not found | Verify file path, use absolute paths |
| Invalid Azure region | Check spelling (e.g., `eastus` not `East US`) |
| VM SKU not available | Check availability: `az vm list-skus --location <region>` |
| RBAC validation failed | Request Contributor access, verify login |

**� Complete guide:** [INSTALLATION.md - Troubleshooting](docs/INSTALLATION.md#troubleshooting)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Check [ROADMAP.md](docs/ROADMAP.md) for planned features
2. Open an issue to discuss your idea
3. Fork the repository
4. Create a feature branch
5. Submit a pull request

**📖 Development setup:** [INSTALLATION.md - Development Setup](docs/INSTALLATION.md#development-setup)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/atef-aziz/azmig_tool/issues)
- **Discussions:** [GitHub Discussions](https://github.com/atef-aziz/azmig_tool/discussions)
- **Email:** atef.aziz@example.com

---

## 🚀 What's New in v1.0.0

### Development Release 🏗️

- ✅ **Modular structure** - Purpose-specific modules: `clients/`, `config/`, `formatters/`, `base/`
- ✅ **Clear naming** - Landing Zone/Server terminology for better clarity
- ✅ **Flexible imports** - Multiple import patterns supported
- ✅ **Well-organized** - Clean separation of concerns across modules

### Module Structure

```python
# ✅ RECOMMENDED Import Patterns
from azmig_tool.clients import AzureMigrateClient, AzureSiteRecoveryClient
from azmig_tool.config import ConfigParser, LandingZoneConfigParser
from azmig_tool.formatters import TableFormatter
from azmig_tool.base import LandingZoneValidator, ServerValidator

# Alternative imports (also supported)
from azmig_tool.config import Layer1ConfigParser  # Alias for backward compatibility
from azmig_tool.formatters import format_layer1_results  # Alias for backward compatibility
```

### Getting Started

**Multiple import patterns supported** for flexibility. Use the recommended patterns above for best practices.

**📖 Complete user guide:** [USER_GUIDE.md](docs/USER_GUIDE.md)

**📖 See full changelog:** [CHANGELOG.md](CHANGELOG.md)

**📖 Architecture overview:** [ARCHITECTURE.md](ARCHITECTURE.md)

**📖 Future plans:** [ROADMAP.md](docs/ROADMAP.md)

---

**Version:** 1.0.0-dev  
**Status:** In Development  
**Made with ❤️ for Azure Migrations**
