@# Changelog

All notable changes to the Azure Bulk Migration Tool will be documented in this file.

## [4.0.0] - 2025-XX-XX (Planned)

### 🚀 Major Architectural Change: CLI to Web Application

**Breaking Change**: Complete transformation from command-line tool to three-tier web application.

#### New Three-Tier Architecture

**1. Database Tier (PostgreSQL)**
- Persistent storage for projects, configurations, and validation results
- Tables: users, projects, landing_zone_configs, server_configs, validation_results, replication_status
- Full schema documentation in `docs/WEB_APP_ARCHITECTURE.md`

**2. API Tier (Python - FastAPI)**
- RESTful API with JWT authentication
- Reuses existing validator logic as API services
- Background job processing with Celery + Redis
- Excel file upload and processing
- Project-scoped operations
- WebSocket support for real-time validation progress

**3. UI Tier (React + TypeScript)**
- Modern web interface with Ant Design components
- Project-centric navigation
- Excel drag-and-drop upload
- Real-time validation dashboards
- Replication status monitoring
- Interactive validation results tables

#### Key Features
- **Project Management**: Create, organize, and manage multiple migration projects
- **Excel Upload**: Drag-and-drop server configuration Excel files
- **Background Validation**: Long-running validations processed asynchronously
- **Real-time Progress**: Live updates on validation job status
- **Historical Results**: Persistent storage of all validation results
- **Multi-user Support**: User authentication and project ownership
- **Replication Tracking**: Monitor replication status for all servers

#### API Endpoints (Preview)
```
GET/POST   /api/v1/projects
GET/PUT    /api/v1/projects/{id}/landing-zone
POST       /api/v1/projects/{id}/servers/upload
POST       /api/v1/projects/{id}/servers/validate
GET        /api/v1/projects/{id}/replication
```

#### Deployment
- Containerized with Docker
- Azure App Service or AKS deployment
- Azure Database for PostgreSQL
- Azure Blob Storage for file uploads
- Azure Application Insights for monitoring

See `docs/WEB_APP_ARCHITECTURE.md` for complete architectural details.

---

## [3.0.1] - 2025-01-XX

### ✨ New Features

#### Replication Status Warning
- **DiscoveryValidator** now checks if replication is already enabled for a machine
- Displays warning with replication state if machine already has replication configured
- Prevents accidental re-configuration of already protected machines
- Provides clear guidance to disable replication first before re-enabling

### 🧹 Codebase Cleanup

#### Removed Modules (~2,200 lines)
- **intelligent_validator.py** (480 lines) - Replaced by `validators/wrappers/intelligent_servers_wrapper.py`
- **formatters/** module (323+ lines) - Formatting now handled directly in validators using Rich library
  - `formatters/__init__.py`
  - `formatters/table_formatter.py` (EnhancedTableFormatter class)
- **utils/error_context.py** (365 lines) - ErrorContext/ErrorCategory/ErrorContextBuilder classes (never used)
- **utils/retry_logic.py** (389 lines) - RetryConfig/RetryHandler classes (planned feature, never implemented)
- **utils/progress_tracker.py** (349 lines) - ValidationCheckpoint/ProgressTracker classes (never integrated)

#### Updated Files
- **azmig_tool/__init__.py** - Removed formatters imports and exports
- **README.md** - Updated project structure and removed retry logic from features list
- **docs/ARCHITECTURE.md** - Removed all references to deleted modules, fixed documentation corruption

#### Impact
- Simplified codebase with only actively-used modules
- Reduced maintenance burden
- Cleaner API surface in `__init__.py`
- All existing functionality preserved

---

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
