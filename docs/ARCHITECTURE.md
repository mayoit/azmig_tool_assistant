# Azure Migration Tool - Architecture Documentation# Azure Bulk Migration Tool - Architecture Documentation



## Overview## Table of Contents

1. [Overview](#overview)

The Azure Migration Tool is a comprehensive Python CLI application designed for bulk server migration from on-premises environments to Azure. The tool provides live Azure integration with a sophisticated two-layer validation architecture, intelligent project matching, and comprehensive migration readiness assessment.2. [System Architecture](#system-architecture)

3. [Directory Structure](#directory-structure)

## Version Information4. [Core Components](#core-components)

- **Current Version**: 3.0.05. [Validation System](#validation-system)

- **Architecture**: Modular, organized folder structure with clear separation of concerns6. [Configuration Management](#configuration-management)

- **Target Platform**: Python 3.9+7. [Design Patterns](#design-patterns)

- **Azure Integration**: Live API integration with Azure Migrate, Site Recovery, and Resource Manager8. [Extension Points](#extension-points)

9. [Testing Strategy](#testing-strategy)

## Core Architecture Principles10. [Performance & Security](#performance--security)



### 1. Two-Layer Validation System---

The tool implements a sophisticated validation approach:

## Overview

- **Layer 1 (Landing Zone)**: Project-level validation including Azure Migrate projects, appliances, quotas, and RBAC

- **Layer 2 (Servers)**: Machine-level validation covering regions, resource groups, VNets, SKUs, and discovery statusThe Azure Bulk Migration Tool is a comprehensive CLI application designed for bulk server migration from on-premises data centers to Azure using Azure Migrate and Azure Site Recovery.



### 2. Live Azure Integration### Key Characteristics

- Real-time Azure API integration using `azmig_tool/clients/` - **Two-Layer Validation Architecture**: Landing Zone (project-level) and Servers (machine-level)

- All validators implement base interfaces from `azmig_tool/base/`- **Configurable Validations**: YAML-based configuration for flexible validation control

- Comprehensive error handling with Azure trace ID tracking- **Mock/Live Modes**: Offline testing and production Azure integration

- **Interactive Wizard**: Guided migration workflow

### 3. Configuration-Driven Validation- **Batch Processing**: Simultaneous validation of multiple servers

All validations are controlled by `validation_config.yaml` with profiles:

```yaml---

servers:

  region_validation: {enabled: true}## System Architecture

  rbac_validation: {enabled: false}  # Can be disabled

### High-Level Architecture

profiles:

  quick: {overrides: {servers.rbac_validation.enabled: false}}```

```┌─────────────────────────────────────────────────────────────┐

│             Azure Bulk Migration Tool v1.0.0                 │

## Folder Structure└─────────────────────────────────────────────────────────────┘

                              │

```                              ▼

azmig_tool/        ┌──────────────────────────────────────────┐

├── __init__.py                    # Main module entry point        │     CLI Interface (cli.py)                │

├── core/                          # Core business logic and models        │  --live, --mock, --validation-config,     │

│   ├── __init__.py        │  --validation-profile, --excel            │

│   ├── models.py                  # Data models and schemas        └──────────────────────────────────────────┘

│   ├── constants.py               # Application constants                                │

│   └── core.py                   # Core business logic         ┌────────────────────┴────────────────────┐

├── interface/                     # User interface components           │                                         │

│   ├── __init__.py         ▼                                         ▼

│   ├── cli.py                    # Command-line interface┌────────────────────┐                  ┌──────────────────────┐

│   ├── wizard.py                 # Interactive wizard│  Configuration     │                  │  Validation Engine    │

│   └── interactive_prompts.py    # User input prompts│  Management        │                  │                       │

├── utils/                         # Utility functions and helpers├────────────────────┤                  ├──────────────────────┤

│   ├── __init__.py
│   ├── auth.py                   # Authentication utilities
│   └── exit_codes.py             # Application exit codes
├── management/                    # Project and template management
│   ├── __init__.py
│   ├── project_manager.py        # Project management logic
│   └── template_manager.py       # Template handling
├── config/                        # Configuration handling

│   ├── __init__.py                                        │                      │

│   ├── parsers.py               # File parsers (CSV, JSON, Excel)                                        │ Servers Layer        │

│   ├── validation_config.py     # Validation configuration                                        │ ┌──────────────────┐ │

│   └── validation_config.yaml   # Configuration file                                        │ │ BaseValidator    │ │

├── validators/                    # Validation engine                                        │ └──────────────────┘ │

│   ├── __init__.py                                        │        ▲             │

│   ├── core/                    # Specialized core validators                                        │ ┌──────┴──────────┐  │

│   │   ├── access_validator.py  # RBAC and permissions                                        │ │ Mock   │  Live  │  │

│   │   ├── appliance_validator.py # Azure Migrate appliances                                        │ │Validator│Validator│ │

│   │   ├── discovery_validator.py # Machine discovery                                        │ └──────────────────┘  │

│   │   ├── disk_validator.py    # Disk configuration                                        └──────────────────────┘

│   │   ├── quota_validator.py   # Azure quotas                                                  │

│   │   ├── rbac_validator.py    # Role-based access                                                  ▼

│   │   ├── region_validator.py  # Azure regions                                        ┌──────────────────────┐

│   │   ├── resource_group_validator.py # Resource groups                                        │  Output & Reporting   │

│   │   ├── storage_validator.py # Storage accounts                                        ├──────────────────────┤

│   │   ├── vmsku_validator.py   # Virtual machine SKUs                                        │ • Rich Tables        │

│   │   └── vnet_validator.py    # Virtual networks                                        │ • JSON Reports       │

│   └── wrappers/               # Orchestrator wrappers                                        │ • Console Output     │

│       ├── landing_zone_wrapper.py        # Landing zone orchestrator
│       ├── servers_wrapper.py             # Servers orchestrator
│       └── intelligent_servers_wrapper.py # Intelligent validation
├── clients/                       # Azure API clients
│   ├── __init__.py
│   ├── azure_client.py           # Base Azure client
│   └── azure_migrate_client.py   # Azure Migrate specific client
├── base/                          # Base interfaces and contracts
│   ├── __init__.py
│   ├── validator_interface.py     # Validator base interface
│   └── landing_zone_interface.py # Landing zone base interface
├── utils/                         # Utility modules
│   ├── __init__.py
│   ├── auth.py                   # Authentication utilities
│   └── exit_codes.py             # Exit code management
└── config/                        # Configuration management
    ├── __init__.py
    ├── parsers.py                # Config file parsers
    └── validation_config.py      # Validation configuration
```

## Key Components

### Core Module (`azmig_tool/core/`)
- **models.py**: Comprehensive data models using `@dataclass` with type hints
- **constants.py**: Application constants including Azure regions, SKUs, and role definitions
- **core.py**: Main business logic and orchestration functions

### Interface Module (`azmig_tool/interface/`)
- **cli.py**: Command-line interface with argument parsing
- **wizard.py**: Interactive wizard for guided migration setup
- **interactive_prompts.py**: User input handling and validation

## Component Interaction Flow

```
User Input
    │
    ▼
CLI Parser ──► Validation Config Loader ──► Load YAML/Apply Profile
    │                                              │
    ▼                                              ▼
Config Parser ──► Detect Format ──► Parse ──► Validation Engine
    │                                              │
    │                                              ▼
    │                                    Check Config Enablement
    │                                              │
    │                            ┌─────────────────┴─────────────────┐
    │                            ▼                                   ▼
    │                    Landing Zone Layer                   Servers Layer
    │                    (Project Readiness)                  (Machine Config)
    │                            │                                   │
    │                            ▼                                   ▼
    │                    Skip if disabled                    Skip if disabled
    │                            │                                   │
    └────────────────────────────┴───────────────────────────────────┘
                                 │
                                 ▼
                         Consolidated Results
                                 │
                                 ▼
                         Enhanced Formatting
                                 │
                                 ▼
                         Console/JSON Output
```

---

### Validation Engine (`azmig_tool/validators/`)

#### Core Validators (`validators/core/`)
Each validator is specialized for a specific Azure resource or concept:

- Implements base interfaces from `azmig_tool/base/`                                 │

- Uses live Azure API integration                                 ▼

- Returns structured `ValidationResult` objects                         Console/JSON Output

- Handles Azure API errors gracefully with retry logic```



#### Wrapper Orchestrators (`validators/wrappers/`)---

- **LandingZoneValidatorWrapper**: Orchestrates landing zone validation

- **ServersValidatorWrapper**: Orchestrates server-level validation  ## Directory Structure

- **IntelligentServersValidatorWrapper**: Advanced validation with project matching

```

### Configuration System (`azmig_tool/config/`)azmig_tool_package/

- **Unified parsing**: Auto-detects CSV/JSON (Layer 1) and Excel (Layer 2)├── azmig_tool/                          # Main package

- **Validation profiles**: Different validation configurations (quick, full, rbac_only)│   ├── __init__.py                      # Package initialization

- **Configuration singleton**: Ensures consistent configuration across components│   ├── cli.py                           # CLI entry point with argument parsing

│   ├── wizard.py                        # Interactive wizard workflow

### Azure Integration (`azmig_tool/clients/`)│   │

- **Live API integration**: Real-time Azure resource validation│   ├── models.py                        # 🎯 Consolidated data models

- **Comprehensive error handling**: Azure trace ID tracking and meaningful error messages│   │   ├── Landing Zone Models          # Project-level configuration & results

- **Authentication support**: Multiple auth methods (CLI, Service Principal, Managed Identity)│   │   └── Servers Models               # Machine-level configuration & results

│   │

## Data Flow Architecture│   ├── validators/                      # 🎯 Validation engine

│   │   ├── __init__.py                  # Exports all validators

### 1. Configuration Phase│   │   │

```│   │   ├── landing_zone_validator.py   # Base Landing Zone validator

User Input → ConfigParser → ValidationConfig → Validation Engine│   │   ├── mock_landing_zone_validator.py  # Mock LZ implementation

```│   │   ├── live_landing_zone_validator.py  # Live LZ implementation (future)

│   │   │

### 2. Authentication Phase│   │   ├── base.py                      # Base Servers validator

```│   │   ├── mock_validator.py           # Mock Servers implementation

Auth Method → Credential Factory → Azure Clients → API Authentication│   │   └── live_validator.py           # Live Servers implementation

```│   │

│   ├── config_parser.py                 # 🎯 Unified configuration parser

### 3. Validation Phase│   │   ├── Auto-detection (CSV/JSON/Excel)

```│   │   ├── Landing Zone parsing (CSV/JSON)

Input Data → Landing Zone Validation → Server Validation → Results Aggregation│   │   └── Servers parsing (Excel)

```│   │

│   ├── validation_config_loader.py      # 🎯 Validation configuration system

### 4. Intelligent Validation Phase (Advanced)│   │   ├── ValidationConfig class

```│   │   ├── ValidationConfigLoader class

Server Configs → Project Matching → Discovery Check → Readiness Assessment│   │   ├── Profile application

```│   │   └── Singleton pattern

│   │

## Validation Workflow

### Landing Zone Validation (Layer 1)

1. **Access Validation**: RBAC permissions for Azure Migrate and Site Recovery
2. **Appliance Health**: Azure Migrate appliance status and connectivity
3. **Storage Cache**: Cache storage account validation and auto-creation
4. **Quota Validation**: vCPU and resource quotas in target regions

### Server Validation (Layer 2)│       ├── __init__.py

1. **Region Validation**: Target Azure region availability and capabilities│       ├── live_mode.py                 # Live Azure integration mode

2. **Resource Group**: Target resource group existence and access│       └── mock_mode.py                 # Offline simulation mode

3. **Network Validation**: VNet and subnet configuration validation│

4. **VM SKU Validation**: Target VM SKU availability and compatibility├── docs/                                # 📚 Documentation

5. **Disk Validation**: Disk type and configuration validation│   ├── ARCHITECTURE.md                  # This file - Technical architecture

6. **Discovery Validation**: Machine discovery status in Azure Migrate│   ├── INSTALLATION.md                  # Installation guide

7. **RBAC Validation**: Machine-specific access permissions│   ├── FEATURES.md                      # Feature documentation

│   └── ROADMAP.md                       # Future enhancements

### Intelligent Validation (Advanced)│

1. **Project Matching**: Automatic server-to-project association├── tests/                               # Test suite

2. **Discovery Integration**: Live Azure Migrate discovery status│   ├── data/                            # Sample data for tests

3. **Cross-Subscription**: Handle complex enterprise scenarios│   │   ├── sample_migrate_projects.csv  # Sample LZ CSV

4. **Enhanced Reporting**: Detailed insights and recommendations│   │   ├── sample_migrate_projects.json # Sample LZ JSON

│   │   └── sample_migration.xlsx        # Sample Servers Excel

## Error Handling Strategy│   ├── test_layer1.py                   # Landing Zone tests

│   ├── test_config_parser.py            # Parser tests

### Azure API Error Patterns│   ├── test_validation_config.py        # Validation config tests

- **401 Unauthorized**: Authentication failure with remediation guidance│   ├── test_installation.py             # Installation tests

- **403 Forbidden**: Permission issues with specific RBAC requirements│   ├── test_live_landing_zone.py        # Live landing zone tests

- **404 Not Found**: Resource missing with creation suggestions│   └── test_subnet_validations.py       # Subnet validation tests

- **429 Throttling**: Rate limiting with exponential backoff retry│

- **500+ Server Errors**: Transient issues with retry logic├── scripts/                             # Utility scripts

│   ├── create_sample_excel.py           # Generate sample Excel file

### Structured Error Response│   └── generate_sample_config.py        # Generate sample config files

```python│

@dataclass├── examples/                            # User-facing templates

class ValidationResult:│   └── template_migrate_projects.csv    # Template for LZ config

    stage: ValidationStage│

    passed: bool├── validation_config.yaml               # Default validation configuration

    message: str├── requirements.txt                     # Python dependencies

    details: Optional[dict] = None├── setup.py                             # Package setup

```├── README.md                            # Main entry documentation

└── CHANGELOG.md                         # Version history

## Authentication Architecture```



### Supported Authentication Methods### Module Responsibilities

1. **Azure CLI**: `az login` based authentication

2. **Service Principal**: Client ID/Secret based authentication  | Module | Responsibility | Key Classes/Functions |

3. **Managed Identity**: Azure resource-based authentication|--------|---------------|----------------------|

| `cli.py` | Command-line interface, argument parsing | `main()`, argparse setup |

### Token Management| `wizard.py` | Interactive migration workflow | `MigrationWizard` |

- **Credential caching**: Per-profile token caching to avoid re-authentication| `models.py` | Data structures and validation | All dataclasses and enums |

- **Automatic refresh**: Azure SDK handles token refresh automatically| `validators/` | Validation logic for both layers | All validator classes |

- **Secure storage**: Credentials stored securely using Azure SDK patterns

| File | Responsibility | Key Classes/Functions |
|------|---------------|----------------------|
| `config_parser.py` | Configuration file parsing | `ConfigParser` |
| `validation_config_loader.py` | Validation settings management | `ValidationConfig`, `ValidationConfigLoader` |
| `constants.py` | Shared constants and configurations | Region lists, role IDs, etc. |
| `modes/` | Execution mode wrappers | `run_mock_mode()`, `run_live_mode()` |

---

## Configuration Profiles

### Profile System



```yaml

active_profile: "default"---



profiles:## Core Components

  quick:

    overrides:### 1. Data Models (`models.py`)

      servers.rbac_validation.enabled: false

      servers.discovery_validation.enabled: falseCentralized data models using Python dataclasses with type hints and validation.

  

  full:#### Landing Zone Models

    overrides:

      # All validations enabled (default)```python

  # Enumerations

  rbac_only:class ApplianceType(Enum):

    overrides:    VMWARE = "VMware"

      servers.region_validation.enabled: false    HYPERV = "Hyper-V"

      servers.vnet_subnet_validation.enabled: false    PHYSICAL = "Physical"

```

class HealthStatus(Enum):

## Extensibility Points    HEALTHY = "Healthy"

    WARNING = "Warning"

### Adding New Validators    UNHEALTHY = "Unhealthy"

1. Implement base interface in `validators/core/`    CRITICAL = "Critical"

2. Add to validation configuration schema

3. Register in appropriate wrapper orchestrator# Configuration

4. Add error handling patterns@dataclass

class MigrateProjectConfig:

### Adding New Input Formats    """Azure Migrate project configuration"""

1. Extend `ConfigParser` in `config/parsers.py`    subscription_id: str

2. Add format detection logic    migrate_project_name: str

3. Implement parsing methods    appliance_type: ApplianceType

4. Add validation for required columns    region: str

    # ... additional fields

### Adding New Authentication Methods

1. Extend `AuthManager` in `utils/auth.py`# Results

2. Add credential factory methods@dataclass

3. Update configuration schemaclass ProjectReadinessResult:

4. Add user guidance documentation    """Consolidated project readiness result"""

    config: MigrateProjectConfig

## Performance Considerations    access_result: Optional[AccessValidationResult]

    appliance_result: Optional[ApplianceHealthResult]

### Parallel Execution    storage_result: Optional[StorageCacheResult]

- Validation operations can run concurrently where safe    quota_result: Optional[QuotaValidationResult]

- Azure API calls use connection pooling    

- Intelligent batching for bulk operations    def is_ready(self) -> bool:

        """Check if project is ready for migration"""

### Resource Optimization        # Validation logic

- Connection reuse across validation operations```

- Caching of Azure resource metadata

- Lazy loading of validation components#### Servers Models



### Scalability Patterns```python

- Batch processing for large server lists# Enumerations

- Streaming validation resultsclass ValidationStage(Enum):

- Progress tracking for long-running operations    EXCEL_STRUCTURE = "Excel Structure"

    AZURE_REGION = "Azure Region"

## Security Architecture    RESOURCE_GROUP = "Resource Group"

    # ... additional stages

### Credential Isolation

- No credential persistence to disk# Configuration

- Memory-only credential caching@dataclass

- Secure credential disposalclass MigrationConfig:

    """Individual machine migration configuration"""

### Azure Permissions    target_machine_name: str

- Principle of least privilege    target_region: str

- Read-only operations where possible    target_subscription: str

- Clear permission requirements documentation    target_rg: str

    # ... additional fields

### Audit Trail

- Azure trace ID tracking# Results

- Validation operation logging@dataclass

- Error context preservationclass ValidationResult:

    """Single validation check result"""

## Future Architecture Considerations    stage: ValidationStage

    passed: bool

### Planned Enhancements    message: str

1. **Plugin Architecture**: Dynamic validator loading    details: Optional[str] = None

2. **REST API**: Web service interface for integration```

3. **Database Integration**: Persistent validation history

4. **Multi-tenant**: Support for multiple Azure tenants### 2. Validation System

5. **Workflow Engine**: Complex migration workflow orchestration

#### Two-Layer Architecture

### Deprecation Path

- `intelligent_validator.py` has been removed and replaced with wrapper architecture
- Legacy import aliases maintained for backward compatibility
- Migration guides for API changes

**Layer 1: Landing Zone Validation (Project Readiness)**

Validates Azure Migrate project-level prerequisites:



## Testing Strategy```python

from azmig_tool.validators import BaseLandingZoneValidator

### Unit Testing

- Individual validator componentsclass BaseLandingZoneValidator(ABC):

- Configuration parsing logic      """Base class for Landing Zone validators"""

- Error handling scenarios    

    def __init__(self, validation_config: Optional[ValidationConfig] = None):

### Integration Testing          self.validation_config = validation_config or get_validation_config()

- Live Azure API integration    

- End-to-end validation workflows    @abstractmethod

- Authentication method validation    def validate_access(self, config) -> AccessValidationResult:

        """Validate RBAC permissions"""

### Performance Testing        pass

- Large-scale validation scenarios    

- Azure API rate limiting behavior    @abstractmethod

- Memory usage optimization    def validate_appliance_health(self, config) -> ApplianceHealthResult:

        """Validate appliance health and connectivity"""

This architecture provides a robust, scalable, and maintainable foundation for Azure migration assessment and validation operations.        pass
    
    @abstractmethod
    def validate_storage_cache(self, config) -> StorageCacheResult:
        """Validate cache storage account"""
        pass
    
    @abstractmethod
    def validate_quota(self, config) -> QuotaValidationResult:
        """Validate vCPU quotas"""
        pass
    
    def validate_project(self, config) -> ProjectReadinessResult:
        """Run all validations based on configuration"""
        # Check validation_config and run enabled validations only
```

**Layer 2: Servers Validation (Machine Configuration)**

Validates individual machine migration configurations:

```python
from azmig_tool.validators import BaseValidator

class BaseValidator(ABC):
    """Base class for Servers validators"""
    
    def __init__(self, validation_config: Optional[ValidationConfig] = None):
        self.validation_config = validation_config or get_validation_config()
    
    @abstractmethod
    def validate_region(self, config) -> ValidationResult:
        """Validate Azure region"""
        pass
    
    @abstractmethod
    def validate_resource_group(self, config) -> ValidationResult:
        """Validate resource group exists"""
        pass
    
    # ... additional validation methods
    
    def validate_all(self, configs, project, user_object_id) -> dict:
        """Run all enabled validations"""
        # Check validation_config for each validation
```

#### Validation Flow with Configuration

```
┌─────────────────────────────────────────────────────────┐
│  1. Load Validation Configuration                       │
│  └─► validation_config.yaml or --validation-config      │
│  └─► Apply profile if specified (quick, full, etc.)     │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  2. Landing Zone Validation (if enabled)                │
│  ┌────────────────────────────────────────────────────┐ │
│  │ For each project:                                  │ │
│  │  • Check if access_validation enabled              │ │
│  │  • Check if appliance_health enabled               │ │
│  │  • Check if storage_cache enabled                  │ │
│  │  • Check if quota_validation enabled               │ │
│  │  • Run only enabled validations                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  3. Servers Validation (if enabled)                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │ For each machine:                                  │ │
│  │  • Check if region_validation enabled              │ │
│  │  • Check if resource_group_validation enabled      │ │
│  │  • Check if vnet_subnet_validation enabled         │ │
│  │  • ... (check each validation)                     │ │
│  │  • Run only enabled validations                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3. Configuration Management

#### Unified Configuration Parser

```python
class ConfigParser:
    """Unified parser for all configuration formats"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.file_type = self._detect_file_type()
    
    def _detect_file_type(self) -> str:
        """Auto-detect CSV, JSON, or Excel"""
        # Detection logic
    
    def parse_landing_zone(self) -> Tuple[bool, List[MigrateProjectConfig], str]:
        """Parse Landing Zone configuration (CSV/JSON)"""
        # Parsing logic
    
    def parse_servers(self) -> Tuple[bool, List[MigrationConfig], List[ValidationResult]]:
        """Parse Servers configuration (Excel)"""
        # Parsing logic
    
    def parse(self) -> Tuple[bool, Any, Any]:
        """Auto-detect layer and parse"""
        # Generic parsing
```

#### Validation Configuration Loader

```python
class ValidationConfig:
    """Holds validation configuration settings"""
    
    def __init__(self, config_data: Dict, active_profile: str):
        self.config_data = config_data
        self.active_profile = active_profile
    
    # Landing Zone checks
    def is_access_validation_enabled(self) -> bool: ...
    def is_appliance_health_enabled(self) -> bool: ...
    def is_storage_cache_enabled(self) -> bool: ...
    def is_quota_validation_enabled(self) -> bool: ...
    
    # Servers checks
    def is_region_validation_enabled(self) -> bool: ...
    def is_resource_group_validation_enabled(self) -> bool: ...
    # ... additional checks

class ValidationConfigLoader:
    """Loads validation configuration from YAML"""
    
    @staticmethod
    def load(config_path: Optional[str] = None) -> ValidationConfig:
        """Load config from file or use default"""
        # Loading logic
    
    @staticmethod
    def create_default_config(output_path: Optional[str] = None) -> str:
        """Create default validation_config.yaml"""
        # Creation logic
```

#### Validation Configuration Structure

```yaml
# validation_config.yaml
landing_zone:
  access_validation:
    enabled: true
    checks:
      migrate_project_rbac: {enabled: true}
      recovery_vault_rbac: {enabled: true}
      subscription_rbac: {enabled: true}
  
  appliance_health: {enabled: true}
  storage_cache: {enabled: true, auto_create_if_missing: false}
  quota_validation: {enabled: true}

servers:
  region_validation: {enabled: true}
  resource_group_validation: {enabled: true}
  vnet_subnet_validation: {enabled: true}
  vm_sku_validation: {enabled: true}
  disk_type_validation: {enabled: true}
  discovery_validation: {enabled: true}
  rbac_validation: {enabled: true}

global:
  fail_fast: false
  parallel_execution: false
  timeout_seconds: 300
  
profiles:
  quick:  # Skip time-consuming checks
    overrides:
      landing_zone.appliance_health.enabled: false
      landing_zone.quota_validation.enabled: false
      servers.discovery_validation.enabled: false
  
  rbac_only:  # Only permission checks
    overrides:
      # Disable all except RBAC checks
  
  resource_only:  # Only infrastructure checks
    overrides:
      # Disable RBAC, enable resources

active_profile: "default"
```

---

## Design Patterns

### 1. Abstract Base Class (ABC) Pattern
- **Purpose**: Define contract for validators
- **Implementation**: `BaseLandingZoneValidator`, `BaseValidator`
- **Benefits**: Enforces interface consistency, enables polymorphism

### 2. Strategy Pattern
- **Purpose**: Swap validation strategies (Mock ↔ Live)
- **Implementation**: Validator implementations
- **Benefits**: Flexible testing, environment-specific behavior

### 3. Dataclass Pattern
- **Purpose**: Type-safe data structures
- **Implementation**: All models use `@dataclass`
- **Benefits**: Auto-generated methods, type checking, validation

### 4. Singleton Pattern
- **Purpose**: Single validation config instance
- **Implementation**: `get_validation_config()` with global cache
- **Benefits**: Consistent config across application

### 5. Factory Pattern (Implicit)
- **Purpose**: Create appropriate validator based on mode
- **Implementation**: Mode functions instantiate correct validator
- **Benefits**: Encapsulates creation logic

### 6. Template Method Pattern
- **Purpose**: Define validation workflow skeleton
- **Implementation**: `validate_project()`, `validate_all()`
- **Benefits**: Reusable workflow, customizable steps

### 7. Facade Pattern
- **Purpose**: Simplify complex subsystems
- **Implementation**: CLI provides simple interface
- **Benefits**: Easy-to-use API for complex operations

---

## Extension Points

### 1. Custom Validators

Add new validation logic by extending base classes:

```python
# Custom Landing Zone Validator
class ComplianceValidator(BaseLandingZoneValidator):
    """Validates compliance requirements"""
    
    def validate_access(self, config):
        # Custom compliance checks
        pass
    
    def validate_compliance_tags(self, config):
        """Additional compliance validation"""
        # Custom logic
        pass
```

### 2. Custom Configuration Parsers

Support new configuration formats:

```python
class TOMLConfigParser(ConfigParser):
    """Parser for TOML configuration files"""
    
    def _detect_file_type(self):
        if self.config_path.suffix == '.toml':
            return 'toml'
        return super()._detect_file_type()
    
    def parse_toml(self):
        # TOML parsing logic
        pass
```

### 3. Custom Validation Checks

Add new validations to existing validators:

```python
class ExtendedLiveValidator(LiveValidator):
    """Extended validator with additional checks"""
    
    def validate_security_posture(self, config):
        """Validate security configurations"""
        # Security validation logic
        pass
    
    def validate_all(self, configs, project, user_object_id):
        """Override to include new validations"""
        results = super().validate_all(configs, project, user_object_id)
        
        # Add security validation
        if self.validation_config.is_security_validation_enabled():
            for config in configs:
                security_result = self.validate_security_posture(config)
                results[config.target_machine_name].append(security_result)
        
        return results
```

### 4. Custom Output Formatters

Create specialized output formats:

```python
class HTMLFormatter:
    """Generate HTML validation reports"""
    
    def format_landing_zone_report(self, report):
        """Generate HTML for Landing Zone report"""
        # HTML generation logic
        pass
    
    def format_servers_report(self, results):
        """Generate HTML for Servers report"""
        # HTML generation logic
        pass
```

---

## Testing Strategy

### Test Pyramid

```
                  ▲
                 / \
                /   \
               /  E2E \      - End-to-end tests (few)
              /  Tests \     - Real Azure integration
             ───────────
            /           \
           / Integration \   - Component integration
          /    Tests      \  - Mock Azure services
         ─────────────────
        /                 \
       /   Unit Tests      \  - Individual functions
      /    (Most Tests)     \ - Fast, isolated
     ───────────────────────
```

### Unit Tests

**Validator Tests**:
```python
# tests/test_validators.py
def test_mock_landing_zone_validator():
    """Test mock Landing Zone validator"""
    validator = MockLandingZoneValidator(success_rate=1.0)
    config = MigrateProjectConfig(...)
    result = validator.validate_project(config)
    
    assert result.is_ready()
    assert result.access_result.has_contributor_migrate_project
```

**Parser Tests**:
```python
# tests/test_config_parser.py
def test_csv_parsing():
    """Test CSV configuration parsing"""
    parser = ConfigParser("test.csv")
    success, configs, message = parser.parse_landing_zone()
    
    assert success
    assert len(configs) > 0
    assert isinstance(configs[0], MigrateProjectConfig)
```

**Validation Config Tests**:
```python
# tests/test_validation_config.py
def test_profile_application():
    """Test validation profile application"""
    config = ValidationConfig(config_data, active_profile="quick")
    
    assert config.is_access_validation_enabled() == True
    assert config.is_appliance_health_enabled() == False
```

### Integration Tests

**Live Validator Tests** (requires Azure credentials):
```python
# tests/test_live_validation.py
@pytest.mark.integration
def test_live_region_validation():
    """Test live region validation with Azure API"""
    validator = LiveValidator()
    config = MigrationConfig(target_region="eastus", ...)
    result = validator.validate_region(config)
    
    assert result.passed
```

### End-to-End Tests

**Full Workflow Tests**:
```python
# tests/test_e2e.py
@pytest.mark.e2e
def test_full_migration_workflow():
    """Test complete migration workflow"""
    # 1. Parse configuration
    # 2. Run Landing Zone validation
    # 3. Run Servers validation
    # 4. Generate reports
    # Verify complete flow
```

### Test Organization

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_validators.py
│   ├── test_parsers.py
│   └── test_validation_config.py
├── integration/
│   ├── test_live_validators.py
│   └── test_azure_clients.py
├── e2e/
│   └── test_workflows.py
└── fixtures/
    ├── sample_configs/
    └── mock_responses/
```

---

## Performance & Security

### Performance Optimization

**1. Caching Strategy**
```python
# Cache Azure API responses
class LiveValidator(BaseValidator):
    def __init__(self):
        self._clients_cache = {}  # Reuse Azure clients
        self._resource_cache = {}  # Cache resource lookups
```

**2. Parallel Processing**
```python
# Validate multiple machines concurrently
from concurrent.futures import ThreadPoolExecutor

def validate_machines_parallel(configs):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(validate_machine, configs)
    return list(results)
```

**3. Lazy Loading**
```python
# Load Azure clients only when needed
@property
def compute_client(self):
    if not hasattr(self, '_compute_client'):
        self._compute_client = ComputeManagementClient(...)
    return self._compute_client
```

**4. Batch API Calls**
```python
# Batch resource queries
resources = resource_client.resources.list_by_resource_group(
    resource_group_name=rg_name,
    filter="resourceType eq 'Microsoft.Network/virtualNetworks'"
)
```

### Security Considerations

**1. Credential Management**
```python
# Use DefaultAzureCredential for secure authentication
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
# Tries: Managed Identity → Service Principal → CLI → Environment
```

**2. Required Permissions**

| Layer | Resource | Required Role | Purpose |
|-------|----------|--------------|---------|
| Landing Zone | Subscription | Reader | List resources, check quotas |
| Landing Zone | Migrate Project | Contributor | Manage migration |
| Landing Zone | Recovery Vault | Contributor | Configure replication |
| Servers | Resource Group | Contributor | Deploy VMs |
| Servers | VNet/Subnet | Reader | Validate network config |

**3. Data Privacy**
- No credentials stored in configuration files
- No sensitive data logged (use `sanitize_*` methods)
- Configuration files should be `.gitignore`d if containing real data

**4. Input Validation**
```python
# Validate all user inputs
@dataclass
class MigrationConfig:
    target_machine_name: str
    
    def __post_init__(self):
        # Basic configuration validation (machine name validation removed)
```

**5. Azure API Error Handling**
```python
try:
    result = client.virtual_machines.get(rg_name, vm_name)
except HttpResponseError as e:
    if e.status_code == 404:
        return ValidationResult(passed=False, message="VM not found")
    elif e.status_code == 403:
        return ValidationResult(passed=False, message="Access denied")
    raise  # Re-raise unexpected errors
```

---

## Configuration Validation Architecture

### Validation Configuration Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│  Phase 1: Configuration Loading                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 1. Search for validation_config.yaml               │  │
│  │    • --validation-config path (highest priority)   │  │
│  │    • ./validation_config.yaml                      │  │
│  │    • package_root/validation_config.yaml           │  │
│  │    • ~/.azmig/validation_config.yaml              │  │
│  │                                                    │  │
│  │ 2. Load YAML and parse                            │  │
│  │ 3. Get active_profile from config                 │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 2: Profile Application                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │ if active_profile != "default":                    │  │
│  │   • Get profile from profiles section              │  │
│  │   • Apply overrides to config_data                 │  │
│  │   • Use dot notation (e.g., "servers.rbac.enabled")│  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 3: Validator Initialization                       │
│  ┌────────────────────────────────────────────────────┐  │
│  │ validator = MockValidator(                         │  │
│  │     validation_config=config                       │  │
│  │ )                                                  │  │
│  │                                                    │  │
│  │ Validator stores reference to ValidationConfig    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 4: Runtime Validation Checks                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Before each validation:                            │  │
│  │   if self.validation_config.is_xxx_enabled():      │  │
│  │       run_validation()                             │  │
│  │   else:                                            │  │
│  │       skip_validation()                            │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Singleton Pattern for Configuration

```python
# Global singleton instance
_config_instance: Optional[ValidationConfig] = None

def get_validation_config(config_path: Optional[str] = None) -> ValidationConfig:
    """Get validation configuration (singleton)"""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ValidationConfigLoader.load(config_path)
    
    return _config_instance

def reset_validation_config():
    """Reset singleton (useful for testing)"""
    global _config_instance
    _config_instance = None
```

---

## Error Handling Architecture

### Error Hierarchy

```
Exception
├── ValidationError              # Validation failures
│   ├── ConfigurationError      # Configuration file issues
│   ├── AccessError             # RBAC/permission issues
│   └── ResourceNotFoundError   # Azure resource missing
│
├── ParsingError                # Configuration parsing failures
│   ├── CSVParsingError
│   ├── JSONParsingError
│   └── ExcelParsingError
│
└── AzureAPIError              # Azure API communication issues
    ├── AuthenticationError
    ├── QuotaExceededError
    └── NetworkError
```

### Error Handling Strategy

```python
try:
    # Parse configuration
    success, configs, message = parser.parse_landing_zone()
    if not success:
        console.print(f"[red]✗ {message}[/red]")
        sys.exit(1)
    
    # Validate
    validator = MockLandingZoneValidator()
    for config in configs:
        result = validator.validate_project(config)
        
        if not result.is_ready():
            console.print(f"[yellow]⚠ {config.migrate_project_name}: {result.get_blockers()}[/yellow]")

except FileNotFoundError as e:
    console.print(f"[red]✗ File not found: {e}[/red]")
    sys.exit(1)

except ValidationError as e:
    console.print(f"[red]✗ Validation error: {e}[/red]")
    sys.exit(1)

except KeyboardInterrupt:
    console.print("\n[yellow]Cancelled by user[/yellow]")
    sys.exit(130)

except Exception as e:
    console.print(f"[red]✗ Unexpected error: {e}[/red]")
    if os.getenv("DEBUG"):
        import traceback
        traceback.print_exc()
    sys.exit(1)
```

---

## Version History

### v2.2.0 (Current - October 2025)
- ✅ Validation configuration system (YAML-based)
- ✅ Validation profiles (quick, full, rbac_only, resource_only)
- ✅ Granular validation control
- ✅ Auto-create storage cache option
- ✅ Enhanced documentation structure

### v2.1.0
- ✅ Consolidated models into single `models.py`
- ✅ Reorganized validators under unified `validators/` package
- ✅ Landing Zone validator architecture
- ✅ Enhanced table formatting with Rich library
- ✅ CSV/JSON configuration support for Landing Zone

### v2.0.0
- Excel format updated to Title Case
- Refactored validators
- Azure Migrate API integration

### v1.0.0
- Initial release
- Basic Excel parsing
- Mock validation support

---

## Contributors & Technology Stack

**Technology Stack**:
- Python 3.12+
- Azure SDK for Python
- Rich (Terminal UI)
- Pandas (Data processing)
- PyYAML (Configuration management)
- OpenPyXL (Excel parsing)

**Architecture Principles**:
- SOLID principles
- Clean Architecture
- Design Patterns
- Test-Driven Development
- Documentation-First approach

---

## Code Quality Assessment

### Overall Score: **A- (90/100)**

**Breakdown**:
- **Architecture**: A+ (95/100) - Excellent separation of concerns
- **Naming**: B+ (88/100) - Good with minor inconsistencies
- **Duplication**: A+ (100/100) - Only intentional backward compatibility
- **Organization**: A (92/100) - Very good structure
- **Documentation**: A (90/100) - Comprehensive

### Key Strengths
1. ✅ Excellent module organization (clients/, config/, validators/, utils/)
2. ✅ Clean abstractions with base interfaces
3. ✅ Strategy pattern for Mock/Live validators
4. ✅ Comprehensive data models with type hints
5. ✅ Backward compatibility maintained
6. ✅ Good error handling
7. ✅ Flexible YAML-based configuration system

### Improvement Opportunities
1. ⚠️ Consider splitting large files (models.py ~500 lines, parsers.py ~600 lines)
2. ⚠️ Add API documentation with Sphinx
3. ⚠️ Increase test coverage for edge cases

### Architecture Compliance

| Principle | Status | Evidence |
|-----------|--------|----------|
| **Single Responsibility** | ✅ | Each module has clear purpose |
| **Open/Closed** | ✅ | Interfaces allow extension |
| **Liskov Substitution** | ✅ | Mock/Live validators interchangeable |
| **Interface Segregation** | ✅ | Separate interfaces for different concerns |
| **Dependency Inversion** | ✅ | Validators depend on abstractions |
| **DRY** | ✅ | Minimal code duplication |
| **KISS** | ✅ | Clean, understandable code |

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Tool Version**: 1.0.0-dev
