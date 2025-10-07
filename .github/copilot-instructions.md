# Azure Migration Tool - AI Coding Assistant Instructions

## Project Overview
This is a Python CLI tool for bulk server migration from on-premises to Azure using Azure Migrate and Site Recovery. The tool provides **live Azure integration** with a **two-layer validation architecture**.

## Core Architecture Patterns

### Two-Layer Validation System
- **Layer 1 (Landing Zone)**: Project-level validation (Azure Migrate projects, appliances, quotas, RBAC)
- **Layer 2 (Servers)**: Machine-level validation (regions, resource groups, VNets, SKUs, discovery)

Each layer has separate validators inheriting from base interfaces in `azmig_tool/base/`:
```python
# Always use validation config to check if validations are enabled
if self.validation_config.is_region_validation_enabled():
    machine_results.append(self.validate_region(config))
```

### Live Azure Integration
- **Live Mode**: Real Azure API integration using `azmig_tool/live/` validators
- All validators implement base interfaces from `azmig_tool/base/`

### Validation Configuration System
All validations are controlled by `validation_config.yaml` with profiles:
```yaml
servers:
  region_validation: {enabled: true}
  rbac_validation: {enabled: false}  # Can be disabled

profiles:
  quick: {overrides: {servers.rbac_validation.enabled: false}}
```

## Key Development Patterns

### Data Models (`azmig_tool/models.py`)
- All models use `@dataclass` with type hints
- Enums for constants (DiskType, ValidationStage, ApplianceType)
- Separate models for config vs results: `MigrateProjectConfig` → `ProjectReadinessResult`

### Configuration Parsing (`azmig_tool/config/parsers.py`)
- Auto-detects file types: CSV/JSON (Layer 1), Excel (Layer 2)
- Use `ConfigParser("file.xlsx").parse()` for unified parsing
- Always validate Excel structure before Azure validation

### CLI Structure (`azmig_tool/cli.py`)
- Interactive wizard by default - prompts for missing parameters
- Use `--non-interactive` flag to require all CLI parameters
- Always runs in live Azure mode with proper authentication

## Interactive Wizard and Configuration Formats

### YAML/JSON Schema for Validation Config
```yaml
# validation_config.yaml - Complete schema
active_profile: "default" | "quick" | "full" | "rbac_only" | "resource_only"

global:
  fail_fast: boolean           # Stop on first validation failure
  parallel_execution: boolean  # Run validations concurrently
  timeout_seconds: integer     # API call timeout

landing_zone:
  access_validation:
    enabled: boolean
    checks:
      migrate_project_rbac: {enabled: boolean}
      recovery_vault_rbac: {enabled: boolean} 
      subscription_rbac: {enabled: boolean}
  appliance_health: {enabled: boolean}
  storage_cache: {enabled: boolean, auto_create_if_missing: boolean}
  quota_validation: {enabled: boolean}

servers:
  region_validation: {enabled: boolean}
  resource_group_validation: {enabled: boolean}
  vnet_subnet_validation: {enabled: boolean}
  vm_sku_validation: {enabled: boolean}
  disk_type_validation: {enabled: boolean}
  discovery_validation: {enabled: boolean}
  rbac_validation: {enabled: boolean}

profiles:
  profile_name:
    overrides:
      "config.path.key": value  # Dot notation for nested overrides
```

### Wizard Decision Flow
```
CLI Launch
    │
    ▼
Authentication configured? ──No──► Prompt for auth method
    │Yes
    ▼
All required params? ──No──► Interactive prompts
    │Yes                        │
    ▼                          ▼
Non-interactive mode ────► Validate params ────► Execute
                              │
                              ▼
                         Missing/Invalid? ──Yes──► Error & Exit
                              │No
                              ▼
                           Execute
```

### CLI Option Precedence (Highest to Lowest)
1. **CLI Flags**: `--auth-method azure_cli`
2. **Environment Variables**: `AZURE_AUTH_METHOD=azure_cli`  
3. **Config File**: `validation_config.yaml` settings
4. **Interactive Prompts**: User input during wizard
5. **Built-in Defaults**: Hardcoded fallbacks

### Wizard Prompt Triggers
```python
# Prompts triggered when:
def should_prompt_for_auth(args):
    return (
        not args.non_interactive and     # Interactive mode enabled
        not args.auth_method and         # No CLI auth method
        not os.getenv('AZURE_AUTH_METHOD')  # No env var
    )
```

## Development Workflows

### Adding New Validations
1. Add to `ValidationStage` enum in `models.py`
2. Add config option to `validation_config.yaml`
3. Add `is_xxx_validation_enabled()` method to `ValidationConfig`
4. Implement in base interface and live validators
5. Update `validate_all()` method to check config before running
6. Add appropriate Azure API error handling with retry logic

### Azure Setup Requirements
- **Authentication**: Must have valid Azure credentials (CLI, Service Principal, or Managed Identity)
- **Permissions**: Minimum Reader on subscription, Contributor on target resources
- **Network**: Outbound HTTPS access to Azure APIs
- **Quotas**: Sufficient vCPU quotas in target regions

### Testing Strategy
```bash
# Run unit tests (isolated components)
python -m pytest tests/test_*.py -k "unit"

# Run integration tests (requires Azure auth)
python -m pytest tests/test_live_*.py -m integration

# Test configuration parsing
python -m pytest tests/test_config_parser.py
```

### Excel Template Structure
Required columns (Title Case naming):
```
Target Machine Name | Target Region | Target Subscription | Target RG | 
Target Vnet | Target Subnet | Target Machine Sku | Target Disk Type
```

## Critical Implementation Details

### Validation Config Singleton
```python
from azmig_tool.config.validation_config import get_validation_config
config = get_validation_config()  # Always use this singleton
```

### Error Handling Patterns
- Use `ValidationResult` dataclass for individual checks
- Return structured results, don't raise exceptions in validators
- CLI handles exceptions and formats user-friendly messages
- Always include Azure trace IDs for API errors

### Azure Client Management
- Use `DefaultAzureCredential` for authentication
- Cache clients in validators to avoid recreating connections
- Handle Azure API errors gracefully with informative messages

### Azure Authentication Patterns
**Profile-Based Credential Isolation**:
```python
# Each auth method has isolated credential chain
auth_methods = {
    'azure_cli': AzureCliCredential(),
    'managed_identity': ManagedIdentityCredential(client_id=client_id),
    'service_principal': ClientSecretCredential(tenant_id, client_id, secret)
}
```

**Token Cache Management**:
```python
# Per-profile token caching to avoid re-authentication
class AuthManager:
    def __init__(self):
        self._credential_cache = {}  # Cache per auth method
        
    def get_credential(self, auth_method: str, **kwargs):
        cache_key = f"{auth_method}_{hash(str(kwargs))}"
        if cache_key not in self._credential_cache:
            self._credential_cache[cache_key] = self._create_credential(auth_method, **kwargs)
        return self._credential_cache[cache_key]
```

**Automatic Token Refresh**:
- Azure SDK handles token refresh automatically
- Use `credential.get_token()` with appropriate scopes
- Handle `ClientAuthenticationError` for expired/invalid tokens

### Rich Console Output
- Use `rich.console.Console` for all CLI output
- Color coding: `[green]✓[/green]` success, `[red]✗[/red]` error, `[yellow]⚠[/yellow]` warning
- Tables for validation results, panels for sections

## Error Handling and Debugging

### Rich Error Model
```python
# Distinguish error types for better handling
class AzureMigrationError(Exception):
    """Base exception for all tool errors"""
    pass

class AzureAPIError(AzureMigrationError):
    """Azure API communication failures"""
    def __init__(self, status_code: int, message: str, trace_id: str = None):
        self.status_code = status_code
        self.trace_id = trace_id
        super().__init__(message)

class ValidationLogicError(AzureMigrationError):
    """Business logic validation failures"""
    pass

class CLIMisuseError(AzureMigrationError):
    """User input or CLI usage errors"""
    pass
```

### Debug Mode and Tracing
```python
# Enable with --debug flag or DEBUG=1 env var
def make_azure_request(client, operation, **kwargs):
    if os.getenv('DEBUG'):
        console.print(f"[dim]API Call: {operation}[/dim]")
        console.print(f"[dim]Payload: {kwargs}[/dim]")
    
    try:
        response = getattr(client, operation)(**kwargs)
        if os.getenv('DEBUG'):
            console.print(f"[dim]Trace ID: {response.headers.get('x-ms-request-id')}[/dim]")
        return response
    except Exception as e:
        if hasattr(e, 'response'):
            trace_id = e.response.headers.get('x-ms-request-id')
            console.print(f"[red]Error Trace ID: {trace_id}[/red]")
        raise
```

### Common Azure API Failure Patterns
```python
def handle_azure_api_error(e: HttpResponseError) -> ValidationResult:
    """Standardized Azure API error handling"""
    status_code = e.status_code
    trace_id = e.response.headers.get('x-ms-request-id', 'N/A')
    
    error_patterns = {
        401: ("Authentication failed", "Run 'az login' or check service principal credentials"),
        403: ("Permission denied", "Ensure user has required RBAC roles on target resources"),
        404: ("Resource not found", "Verify resource names and subscription access"),
        429: ("Request throttled", "Azure API rate limit exceeded, will retry with backoff"),
        500: ("Azure service error", "Temporary Azure service issue, will retry"),
    }
    
    if status_code in error_patterns:
        message, suggestion = error_patterns[status_code]
        return ValidationResult(
            stage=ValidationStage.AZURE_API,
            passed=False,
            message=f"{message} (HTTP {status_code})",
            details=f"{suggestion}\nTrace ID: {trace_id}"
        )
    
    # Unknown error
    return ValidationResult(
        stage=ValidationStage.AZURE_API,
        passed=False,
        message=f"Unexpected Azure API error (HTTP {status_code})",
        details=f"Trace ID: {trace_id}\nResponse: {e.message}"
    )
```

### Safe Retry Logic
```python
import time
from functools import wraps

def azure_retry(max_attempts=3, backoff_factor=2):
    """Decorator for Azure API calls with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except HttpResponseError as e:
                    last_exception = e
                    
                    # Only retry on transient errors
                    if e.status_code in [429, 500, 502, 503, 504]:
                        if attempt < max_attempts - 1:
                            wait_time = backoff_factor ** attempt
                            console.print(f"[yellow]Retrying in {wait_time}s (attempt {attempt + 1}/{max_attempts})[/yellow]")
                            time.sleep(wait_time)
                            continue
                    
                    # Don't retry on auth/permission errors
                    raise
            
            raise last_exception
        return wrapper
    return decorator

# Usage
@azure_retry(max_attempts=3)
def validate_resource_group(self, rg_name: str):
    return self.resource_client.resource_groups.get(rg_name)
```

## Testing & Development

### Sample Data Location
- Excel samples: `tests/data/sample_migration.xlsx`
- CSV samples: `tests/data/sample_migrate_projects.csv`
- JSON samples: `tests/data/sample_migrate_projects.json`

### Live Testing Requirements
```python
# Live validators require Azure authentication
from azure.identity import DefaultAzureCredential
validator = LiveServersValidator(credential=DefaultAzureCredential())
results = validator.validate_all(configs)
```

### Backward Compatibility
Maintain aliases for layer naming changes:
```python
# Old names still work
from azmig_tool.config import Layer1ConfigParser  # → LandingZoneConfigParser
```

## Common Gotchas

1. **Always check validation config** before running validations - not all are enabled by default
2. **Excel column names are Title Case** - "Target Machine Name" not "target_machine_name"  
3. **Live validators require Azure credentials** - ensure proper authentication before initialization
4. **Validation profiles override base config** - check active profile when debugging
5. **Use singleton pattern** for validation config - don't instantiate directly
6. **Rich console formatting** is required - plain print() statements won't match UI style
7. **Always handle Azure API throttling** - implement retry logic for production use

## CI/CD and Deployment Patterns

### Versioning Strategy (setup.py)
```python
# Semantic versioning: MAJOR.MINOR.PATCH
# Major: Breaking API changes
# Minor: New features, backward compatible
# Patch: Bug fixes
version="3.0.0"
```

### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  release:
    types: [published]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8
    
    - name: Lint with flake8
      run: flake8 azmig_tool/ --max-line-length=100
    
    - name: Test with pytest
      run: pytest tests/ --cov=azmig_tool --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build-package:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    
    steps:
    - uses: actions/checkout@v4
    - name: Build package
      run: |
        python setup.py sdist bdist_wheel
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
```

### Secure Secret Management
```bash
# Environment variables for different deployment contexts

# Development (local .env file)
AZURE_CLIENT_ID=dev-sp-client-id
AZURE_CLIENT_SECRET=dev-sp-secret
AZURE_TENANT_ID=dev-tenant-id

# Production (GitHub Secrets, Azure KeyVault, etc.)
# Never commit these to code!
echo $AZURE_CLIENT_SECRET | base64  # For Kubernetes secrets
```

### Release Tagging Strategy
```bash
# Branch strategy
main        # Stable releases (v3.0.0, v3.1.0)
develop     # Next release candidate (v3.1.0-rc1)
feature/*   # Feature development
hotfix/*    # Critical fixes

# Tagging convention
git tag -a v3.0.0 -m "Release 3.0.0: Two-layer validation system"
git tag -a v3.1.0-beta1 -m "Beta: Enhanced error handling"
```

### Package Distribution
```python
# setup.py configuration for different distribution channels
setup(
    name="azmig_tool",
    # ... other config
    
    # PyPI public distribution
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
    ],
    
    # Azure Artifacts private feed (for enterprise)
    # Configure in pip.conf or requirements.txt:
    # --index-url https://pkgs.dev.azure.com/org/_packaging/feed/pypi/simple/
)
```