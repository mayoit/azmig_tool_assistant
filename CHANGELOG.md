# Changelog

All notable changes to the Azure Bulk Migration Tool will be documented in this file.

## [1.0.0-dev] - 2025-10-07

### 🏗️ Initial Development Release

**Status:** In Development - This is the initial architecture and feature set.

#### Module Structure

```
azmig_tool/
├── clients/          # Azure API clients
│   ├── migrate_client.py
│   └── site_recovery_client.py
├── config/           # Configuration parsing
│   └── parsers.py
├── formatters/       # Output formatting
│   └── table_formatter.py
├── base/             # Core validation logic
│   ├── landing_zone/
│   │   └── validator.py
│   └── server/
│       └── validator.py
├── live/             # Live mode (Azure)
│   └── live_mode.py
└── mock/             # Mock mode (offline)
    └── mock_mode.py
```

### Added

- **Core Features**
  - Two-layer validation (Landing Zone + Servers)
  - Interactive wizard workflow
  - YAML-based validation configuration
  - Excel-based server configuration
  - Multi-authentication support (6 methods)
  - Rich CLI interface with progress indicators
  
- **Latest Improvements (October 2025)**
  - ✅ **Enhanced Appliance Detection**: Multi-strategy API approach with Resource Graph integration
  - ✅ **Simplified Architecture**: Removed mock/live mode complexity for unified Azure integration
  - ✅ **Better Error Handling**: Azure API error reporting with trace IDs and retry mechanisms
  - ✅ **Storage Account Flexibility**: Added separate cache storage resource group field for dedicated storage accounts
  - ✅ **Subscription Accuracy**: Fixed appliance detection to use correct migrate project subscription and resource group
  
- **Modular Architecture**
  - Purpose-specific modules: clients/, config/, formatters/, base/
  - Clear naming: Landing Zone/Server terminology
  - Flexible import patterns
  - Well-organized code structure

- **Validation Features**
  - Landing Zone validation (RBAC, Appliance, Storage, Quota)
  - Server validation (Region, RG, VNet, SKU, Disk, Discovery, RBAC)
  - Subnet IP availability validation
  - Subnet delegation detection
  - Validation profiles (full, quick, rbac_only, resource_only)

- **Documentation**
  - Comprehensive user guide
  - Installation guide with troubleshooting
  - Quick reference guide
  - Architecture documentation
  - Roadmap for future features

### Technical Details

- Python 3.9+ required
- Uses Azure SDK for Python
- REST API integration for Azure Migrate
- Rich library for CLI interface
- Supports 6 authentication methods

---

**Note:** This changelog follows [Keep a Changelog](https://keepachangelog.com/) format.

Future enhancements and planned features are tracked in [ROADMAP.md](docs/ROADMAP.md).
