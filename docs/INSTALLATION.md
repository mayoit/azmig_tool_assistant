# Azure Bulk Migration Tool - Installation Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Virtual Environment Setup](#virtual-environment-setup)
4. [Dependency Installation](#dependency-installation)
5. [Azure CLI Configuration](#azure-cli-configuration)
6. [Verification](#verification)
7. [Upgrading](#upgrading)
8. [Troubleshooting](#troubleshooting)
9. [Development Setup](#development-setup)

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| **Python** | 3.8+ | 3.12+ |
| **OS** | Windows 10, Ubuntu 20.04, macOS 11+ | Windows 11, Ubuntu 22.04, macOS 13+ |
| **RAM** | 4 GB | 8 GB+ |
| **Disk Space** | 500 MB | 1 GB |
| **Network** | Internet access for Azure API | Stable connection |

### Software Dependencies

**Required:**
- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning repository)

**Optional but Recommended:**
- Azure CLI (`az`) for authentication
- Visual Studio Code with Python extension
- PowerShell 7+ (Windows) or Bash (Linux/Mac)

### Azure Requirements

**For Live Mode:**
- Active Azure subscription
- Azure Migrate project (for migration validation)
- Recovery Services Vault (for replication)
- Appropriate RBAC permissions (see [Permissions](#azure-permissions))

**For Mock Mode:**
- No Azure resources required
- Can run completely offline

---

## Installation Methods

### Method 1: Clone from GitHub (Recommended)

```bash
# Clone the repository
git clone https://github.com/atef-aziz/azmig_tool.git
cd azmig_tool_package

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Windows Command Prompt:
.venv\Scripts\activate.bat

# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the tool in editable mode
pip install -e .
```

### Method 2: Install from PyPI (Future)

```bash
# Once published to PyPI
pip install azmig-tool

# Upgrade to latest version
pip install --upgrade azmig-tool
```

### Method 3: Install from Local Archive

```bash
# If you have a wheel or tar.gz file
pip install azmig_tool-1.0.0-py3-none-any.whl

# Or
pip install azmig_tool-1.0.0.tar.gz
```

---

## Virtual Environment Setup

### Why Use Virtual Environments?

Virtual environments isolate project dependencies, preventing conflicts with system-wide packages.

### Creating Virtual Environment

**Windows (PowerShell):**
```powershell
# Navigate to project directory
cd C:\Projects\azmig_tool_package

# Create virtual environment
python -m venv .venv

# Activate
.\.venv\Scripts\Activate.ps1

# If execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows (Command Prompt):**
```cmd
cd C:\Projects\azmig_tool_package
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
cd ~/projects/azmig_tool_package
python3 -m venv .venv
source .venv/bin/activate
```

### Deactivating Virtual Environment

```bash
deactivate
```

---

## Dependency Installation

### Core Dependencies

The tool requires these Python packages:

| Package | Version | Purpose |
|---------|---------|---------|
| `azure-identity` | >=1.12.0 | Azure authentication |
| `azure-mgmt-compute` | >=30.0.0 | Compute API client |
| `azure-mgmt-network` | >=23.0.0 | Network API client |
| `azure-mgmt-resource` | >=22.0.0 | Resource management |
| `azure-mgmt-subscription` | >=3.1.0 | Subscription management |
| `azure-mgmt-authorization` | >=3.0.0 | RBAC management |
| `rich` | >=13.0.0 | Terminal UI |
| `pandas` | >=2.0.0 | Data processing |
| `openpyxl` | >=3.1.0 | Excel parsing |
| `pyyaml` | >=6.0.0 | YAML configuration |
| `requests` | >=2.31.0 | HTTP requests |

### Installing Dependencies

**Automatic (Recommended):**
```bash
pip install -r requirements.txt
```

**Manual:**
```bash
pip install azure-identity azure-mgmt-compute azure-mgmt-network \
    azure-mgmt-resource azure-mgmt-subscription azure-mgmt-authorization \
    rich pandas openpyxl pyyaml requests
```

### Verifying Installation

```bash
# Check installed packages
pip list | grep azure

# Verify azmig_tool installation
pip show azmig-tool

# Test CLI
azmig --help
```

---

## Azure CLI Configuration

### Installing Azure CLI

**Windows (PowerShell):**
```powershell
# Using winget
winget install Microsoft.AzureCLI

# Or using MSI installer
# Download from: https://aka.ms/installazurecliwindows
```

**Linux:**
```bash
# Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# RHEL/CentOS
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
sudo dnf install azure-cli
```

**macOS:**
```bash
brew update && brew install azure-cli
```

### Azure Login

**Interactive Login:**
```bash
az login
```

**Service Principal Login:**
```bash
az login --service-principal \
    --username <app-id> \
    --password <password-or-cert> \
    --tenant <tenant-id>
```

**Managed Identity Login:**
```bash
az login --identity
```

### Setting Default Subscription

```bash
# List subscriptions
az account list --output table

# Set default subscription
az account set --subscription "Subscription Name or ID"

# Verify
az account show
```

---

## Verification

### Step 1: Verify Python Installation

```bash
python --version
# Expected: Python 3.8 or higher
```

### Step 2: Verify Package Installation

```bash
pip show azmig-tool
# Should show version 1.0.0-dev
```

### Step 3: Verify CLI Access

```bash
azmig --help
```

Expected output:
```
usage: azmig [OPTIONS]

Azure Bulk Migration Tool - Validate and migrate servers to Azure

options:
  --live                    Run in live Azure mode
  --mock                    Run in mock/simulation mode (default)
  --excel PATH              Path to Excel mapping file
  --validation-config PATH  Path to validation configuration YAML
  --validation-profile NAME Validation profile (quick, full, rbac_only, resource_only)
  --create-default-config   Create default validation_config.yaml
  --export-json PATH        Export results to JSON
  -h, --help                Show this help message
```

### Step 4: Test Mock Mode

```bash
# Create sample validation config
azmig --create-default-config

# Run in mock mode (no Azure connection needed)
azmig --mock --excel tests/data/sample_migration.xlsx
```

### Step 5: Test Live Mode (Optional)

**Authentication Options:**

The tool supports multiple authentication methods similar to Azure CLI:

1. **Azure CLI (Recommended for Development)**
   ```bash
   # Login first
   az login
   
   # Run with Azure CLI authentication
   azmig --live --auth-method azure_cli --excel tests/data/sample_migration.xlsx
   ```

2. **Managed Identity (For Azure VMs/Services)**
   ```bash
   # System-assigned identity
   azmig --live --auth-method managed_identity --excel tests/data/sample_migration.xlsx
   
   # User-assigned identity
   export AZURE_CLIENT_ID="your-identity-client-id"
   azmig --live --auth-method managed_identity --excel tests/data/sample_migration.xlsx
   ```

3. **Service Principal (For Automation)**
   ```bash
   # Using environment variables
   export AZURE_TENANT_ID="your-tenant-id"
   export AZURE_CLIENT_ID="your-client-id"
   export AZURE_CLIENT_SECRET="your-client-secret"
   azmig --live --auth-method service_principal --excel tests/data/sample_migration.xlsx
   
   # Using command-line arguments
   azmig --live --auth-method service_principal \
       --tenant-id "your-tenant-id" \
       --client-id "your-client-id" \
       --client-secret "your-client-secret" \
       --excel tests/data/sample_migration.xlsx
   ```

4. **Interactive Browser Login**
   ```bash
   # Opens browser for sign-in
   azmig --live --auth-method interactive --excel tests/data/sample_migration.xlsx
   ```

5. **Device Code Flow (For SSH/Remote Sessions)**
   ```bash
   # Provides a code to enter at microsoft.com/devicelogin
   azmig --live --auth-method device_code --excel tests/data/sample_migration.xlsx
   ```

6. **Default Credential Chain (Auto-detect)**
   ```bash
   # Tries: Environment → Managed Identity → Azure CLI → Interactive
   azmig --live --auth-method default --excel tests/data/sample_migration.xlsx
   
   # Or simply (will prompt for auth method if not specified)
   azmig --live --excel tests/data/sample_migration.xlsx
   ```

**Quick Start:**
```bash
# Ensure Azure login
az login

# Run live validation (will prompt for authentication method)
azmig --live
# Run live mode
azmig --live --excel tests/data/sample_migration.xlsx
```

---

## Upgrading

### Upgrading from Git

```bash
# Navigate to project directory
cd azmig_tool_package

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

# Pull latest changes
git pull origin main

# Upgrade dependencies
pip install --upgrade -r requirements.txt

# Reinstall package
pip install -e .
```

### Upgrading from PyPI (Future)

```bash
pip install --upgrade azmig-tool
```

### Checking Version

```bash
# Via CLI
azmig --version

# Via Python
python -c "import azmig_tool; print(azmig_tool.__version__)"
```

---

## Troubleshooting

### Installation Issues

#### Issue: "Python not found"
**Solution:**
```bash
# Windows: Add Python to PATH
# Download Python from python.org and check "Add to PATH" during installation

# Linux: Install Python
sudo apt install python3 python3-pip  # Ubuntu/Debian
sudo dnf install python3 python3-pip  # RHEL/CentOS

# macOS: Install Python
brew install python
```

#### Issue: "pip not found"
**Solution:**
```bash
# Windows
python -m ensurepip --upgrade

# Linux/macOS
python3 -m ensurepip --upgrade
```

#### Issue: "Permission denied" during installation
**Solution:**
```bash
# Don't use sudo with virtual environments
# Instead, use --user flag (not recommended with venv)
pip install --user -r requirements.txt

# Or fix virtual environment ownership
sudo chown -R $USER:$USER .venv
```

#### Issue: Virtual environment activation fails on Windows
**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate again
.\.venv\Scripts\Activate.ps1
```

### Dependency Issues

#### Issue: "Package version conflict"
**Solution:**
```bash
# Create fresh virtual environment
deactivate
rm -rf .venv  # Linux/Mac
Remove-Item -Recurse -Force .venv  # Windows PowerShell

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
```

#### Issue: "SSL certificate verification failed"
**Solution:**
```bash
# Temporary workaround (not recommended for production)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Better solution: Update certificates
pip install --upgrade certifi
```

### Azure CLI Issues

#### Issue: "az: command not found"
**Solution:**
```bash
# Verify Azure CLI installation
which az  # Linux/Mac
where az  # Windows

# Reinstall if necessary (see Azure CLI Configuration section)
```

#### Issue: "Azure login fails"
**Solution:**
```bash
# Clear cached credentials
az account clear

# Login again
az login

# If behind proxy:
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
az login
```

### Runtime Issues

#### Issue: "Module not found: azmig_tool"
**Solution:**
```bash
# Ensure virtual environment is activated
# Reinstall in editable mode
pip install -e .

# Verify installation
pip show azmig-tool
```

#### Issue: "Import error: azure.identity"
**Solution:**
```bash
# Reinstall Azure packages
pip install --force-reinstall azure-identity azure-mgmt-compute azure-mgmt-network
```

---

## Development Setup

### For Contributors

**1. Clone and Setup:**
```bash
git clone https://github.com/atef-aziz/azmig_tool.git
cd azmig_tool_package

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

**2. Install Pre-commit Hooks:**
```bash
pip install pre-commit
pre-commit install
```

**3. Run Tests:**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validation_config.py

# Run with coverage
pytest --cov=azmig_tool --cov-report=html
```

**4. Code Formatting:**
```bash
# Format code with black
black azmig_tool/

# Sort imports
isort azmig_tool/

# Lint with flake8
flake8 azmig_tool/

# Type checking with mypy
mypy azmig_tool/
```

### Development Dependencies

Create `requirements-dev.txt`:
```
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.7.0
flake8>=6.1.0
mypy>=1.5.0
isort>=5.12.0
pre-commit>=3.3.0
```

---

## Azure Permissions

### Required RBAC Roles

| Scope | Role | Purpose |
|-------|------|---------|
| **Subscription** | Reader | List resources, check quotas |
| **Azure Migrate Project** | Contributor | Manage migration project |
| **Recovery Services Vault** | Contributor | Configure replication |
| **Target Resource Groups** | Contributor | Deploy VMs |
| **Target VNets** | Reader | Validate network configuration |

### Checking Permissions

```bash
# Check subscription access
az role assignment list --assignee <your-email> --subscription <subscription-id>

# Check resource group access
az role assignment list --assignee <your-email> --resource-group <rg-name>
```

### Requesting Access

If you lack permissions, request from your Azure administrator:

```
Subject: Access Request - Azure Migration Tool

I need the following permissions to run the Azure Migration Tool:

- Reader on subscription: <subscription-name>
- Contributor on resource group: <target-rg-name>
- Contributor on Recovery Services Vault: <vault-name>
- Contributor on Azure Migrate project: <project-name>

Purpose: Server migration from on-premises to Azure
Tool: azmig_tool v1.0.0
```

---

## Azure Authentication

### Authentication Methods

The tool supports **6 authentication methods** similar to Azure CLI, providing flexibility for different environments:

| Method | Use Case | Required |
|--------|----------|----------|
| **Azure CLI** | Development, local testing | `az login` |
| **Managed Identity** | Azure VM, App Service, Container Instances | System/User-assigned identity |
| **Service Principal** | CI/CD pipelines, automation | Tenant ID, Client ID, Secret |
| **Interactive Browser** | Interactive sessions with browser | Browser access |
| **Device Code** | SSH sessions, remote terminals | Device with browser (any device) |
| **Default Chain** | Auto-detection | Any of the above |

---

### 1. Azure CLI Authentication (Recommended)

**Best for:** Development and testing

**Prerequisites:**
- Azure CLI installed
- Logged in via `az login`

**Usage:**
```bash
# Step 1: Login
az login

# Step 2: Run tool
azmig --live --auth-method azure_cli --excel servers.xlsx

# Or let it auto-detect
azmig --live --excel servers.xlsx  # Will prompt to choose
```

**Advantages:**
- ✅ Simple and fast
- ✅ No credentials to manage
- ✅ Same as `az cli` experience

**Troubleshooting:**
```bash
# If auth fails, clear cache and re-login
az account clear
az login
```

---

### 2. Managed Identity Authentication

**Best for:** Production workloads on Azure resources

**Prerequisites:**
- Running on Azure VM, App Service, Container Instance, or AKS
- System-assigned or user-assigned identity configured
- Identity has required RBAC permissions

**System-Assigned Identity:**
```bash
# No additional configuration needed
azmig --live --auth-method managed_identity --excel servers.xlsx
```

**User-Assigned Identity:**
```bash
# Set client ID
export AZURE_CLIENT_ID="your-user-assigned-identity-client-id"
azmig --live --auth-method managed_identity --excel servers.xlsx

# Or via command-line
azmig --live --auth-method managed_identity \
    --client-id "your-identity-client-id" \
    --excel servers.xlsx
```

**Advantages:**
- ✅ No credentials to store
- ✅ Automatic credential rotation
- ✅ Most secure for Azure workloads

**How to Configure:**
```bash
# Enable system-assigned identity on VM
az vm identity assign --name myVM --resource-group myRG

# Assign RBAC permissions
az role assignment create \
    --assignee $(az vm show --name myVM --resource-group myRG --query identity.principalId -o tsv) \
    --role Contributor \
    --scope /subscriptions/{subscription-id}/resourceGroups/{target-rg}
```

---

### 3. Service Principal Authentication

**Best for:** CI/CD pipelines, automation, scripts

**Prerequisites:**
- App registration (service principal) created
- Client secret generated
- RBAC permissions assigned

**Environment Variables (Recommended):**
```bash
# Set environment variables
export AZURE_TENANT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export AZURE_CLIENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export AZURE_CLIENT_SECRET="your-client-secret"

# Run tool
azmig --live --auth-method service_principal --excel servers.xlsx
```

**Command-Line Arguments:**
```bash
azmig --live --auth-method service_principal \
    --tenant-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
    --client-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
    --client-secret "your-client-secret" \
    --excel servers.xlsx
```

**Interactive Prompts:**
```bash
# Tool will prompt for missing values
azmig --live --auth-method service_principal --excel servers.xlsx
# Prompts: Tenant ID? Client ID? Client Secret?
```

**How to Create Service Principal:**
```bash
# Create app registration
az ad sp create-for-rbac --name "azmig-automation" \
    --role Contributor \
    --scopes /subscriptions/{subscription-id}

# Output will include:
# {
#   "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",      # AZURE_CLIENT_ID
#   "password": "your-client-secret",                      # AZURE_CLIENT_SECRET
#   "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"      # AZURE_TENANT_ID
# }
```

**Advantages:**
- ✅ Perfect for automation
- ✅ Can be used in CI/CD
- ✅ Explicit permissions

**Security Best Practices:**
```bash
# Use Azure Key Vault for secrets
# Store in environment variables, not in code
# Rotate secrets regularly
# Use least-privilege RBAC
```

---

### 4. Interactive Browser Authentication

**Best for:** First-time setup, interactive sessions

**Prerequisites:**
- Web browser available
- Internet connectivity

**Usage:**
```bash
# Opens browser for login
azmig --live --auth-method interactive --excel servers.xlsx

# With specific tenant
azmig --live --auth-method interactive \
    --tenant-id "your-tenant-id" \
    --excel servers.xlsx
```

**What Happens:**
1. Browser opens automatically
2. Sign in with your Azure account
3. Grant consent
4. Return to terminal

**Advantages:**
- ✅ User-friendly
- ✅ Supports MFA
- ✅ No pre-configuration needed

---

### 5. Device Code Authentication

**Best for:** SSH sessions, remote servers, headless environments

**Prerequisites:**
- Internet connectivity
- Access to any browser (can be on different device)

**Usage:**
```bash
# Start device code flow
azmig --live --auth-method device_code --excel servers.xlsx

# You'll see:
# ╔══════════════════════════════════════════════════════╗
# ║   Device Code Authentication                         ║
# ║   1. Go to: https://microsoft.com/devicelogin       ║
# ║   2. Enter code: ABCD-1234                          ║
# ║   3. Code expires in 900 seconds                    ║
# ╚══════════════════════════════════════════════════════╝
```

**Steps:**
1. Run command in SSH session
2. Note the code displayed
3. On ANY device with browser, go to https://microsoft.com/devicelogin
4. Enter the code
5. Sign in
6. Return to SSH session (authenticated)

**Advantages:**
- ✅ Works in SSH/headless environments
- ✅ Can use browser on different device
- ✅ Secure

---

### 6. Default Credential Chain

**Best for:** Flexible environments, auto-detection

**Tries in Order:**
1. Environment variables (Service Principal)
2. Managed Identity
3. Azure CLI
4. Azure PowerShell (Windows only)
5. Interactive Browser

**Usage:**
```bash
# Auto-detect best method
azmig --live --auth-method default --excel servers.xlsx
```

**Advantages:**
- ✅ Works in multiple environments
- ✅ No configuration needed
- ✅ Falls back gracefully

---

### Authentication Comparison

| Feature | Azure CLI | Managed Identity | Service Principal | Interactive | Device Code |
|---------|-----------|------------------|-------------------|-------------|-------------|
| **Setup Effort** | Low | Medium | Medium | Low | Low |
| **Best For** | Dev | Production | Automation | First-time | SSH/Remote |
| **Browser Required** | No | No | No | Yes | Yes (any device) |
| **Supports MFA** | Yes | N/A | No | Yes | Yes |
| **CI/CD Friendly** | No | Yes | Yes | No | No |
| **Credential Storage** | Azure CLI | Azure | Env vars/Vault | Browser | Browser |

---

### Environment Variables Reference

```bash
# Service Principal
export AZURE_TENANT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export AZURE_CLIENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export AZURE_CLIENT_SECRET="your-client-secret"

# User-Assigned Managed Identity
export AZURE_CLIENT_ID="identity-client-id"

# Proxy (if needed)
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
export NO_PROXY="localhost,127.0.0.1"
```

---

### Authentication Troubleshooting

#### "Authentication failed: No credentials found"
```bash
# Solution 1: Use Azure CLI
az login
azmig --live --auth-method azure_cli

# Solution 2: Set service principal env vars
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."
azmig --live --auth-method service_principal

# Solution 3: Use interactive login
azmig --live --auth-method interactive
```

#### "Managed Identity not found"
```bash
# Ensure running on Azure resource with identity enabled
az vm identity assign --name myVM --resource-group myRG

# Check identity status
az vm show --name myVM --resource-group myRG --query identity
```

#### "Invalid client secret"
```bash
# Regenerate secret
az ad sp credential reset --id $AZURE_CLIENT_ID

# Update environment variable
export AZURE_CLIENT_SECRET="new-secret"
```

#### "Browser not opening for interactive auth"
```bash
# Use device code flow instead
azmig --live --auth-method device_code
```

---

## Network Configuration

### Proxy Settings

**Windows PowerShell:**
```powershell
$env:HTTP_PROXY = "http://proxy.example.com:8080"
$env:HTTPS_PROXY = "http://proxy.example.com:8080"
$env:NO_PROXY = "localhost,127.0.0.1"
```

**Linux/macOS:**
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
export NO_PROXY=localhost,127.0.0.1
```

**Make Permanent (Linux/macOS):**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export HTTP_PROXY=http://proxy.example.com:8080' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://proxy.example.com:8080' >> ~/.bashrc
```

### Firewall Configuration

Allow outbound HTTPS (443) to:
- `management.azure.com` (Azure Resource Manager)
- `login.microsoftonline.com` (Azure AD)
- `pypi.org` (Python packages)
- `github.com` (Source code)

---

## Quick Reference

### Installation Commands

```bash
# Quick install (development mode)
git clone https://github.com/atef-aziz/azmig_tool.git
cd azmig_tool_package
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Verify
azmig --help
```

### First Run

```bash
# 1. Login to Azure (for Azure CLI auth)
az login

# 2. Create default validation config
azmig --create-default-config

# 3. Test in mock mode (no Azure connection)
azmig --mock --excel tests/data/sample_migration.xlsx

# 4. Run live validation with Azure CLI auth
azmig --live --auth-method azure_cli --excel tests/data/sample_migration.xlsx

# 5. Or let tool prompt for auth method
azmig --live --excel tests/data/sample_migration.xlsx
```

### Common Commands

```bash
# Azure CLI Authentication
azmig --live --auth-method azure_cli --excel servers.xlsx

# Managed Identity
azmig --live --auth-method managed_identity --excel servers.xlsx

# Service Principal (from environment)
export AZURE_TENANT_ID="xxx"
export AZURE_CLIENT_ID="yyy"
export AZURE_CLIENT_SECRET="zzz"
azmig --live --auth-method service_principal --excel servers.xlsx

# Service Principal (command-line)
azmig --live --auth-method service_principal \
    --tenant-id "xxx" --client-id "yyy" --client-secret "zzz" \
    --excel servers.xlsx

# Interactive Browser
azmig --live --auth-method interactive --excel servers.xlsx

# Device Code (for SSH)
azmig --live --auth-method device_code --excel servers.xlsx

# With validation profile
azmig --live --auth-method azure_cli \
    --validation-profile quick \
    --excel servers.xlsx

# Export results to JSON
azmig --live --auth-method azure_cli \
    --excel servers.xlsx \
    --export-json results.json
```

---

## Next Steps

After successful installation:

1. **Read Documentation:**
   - [FEATURES.md](FEATURES.md) - Learn about all features
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system design
   - [VALIDATION_CONFIG_GUIDE.md](../VALIDATION_CONFIG_GUIDE.md) - Configure validations

2. **Prepare Excel File:**
   - Use `examples/template_migrate_projects.csv` as template for landing zone config
   - Use `tests/data/sample_migration.xlsx` as sample servers data
   - Fill in your migration details

3. **Run First Migration:**
   ```bash
   # Test with mock mode
   azmig --mock --excel your_migration.xlsx
   
   # Run live validation
   azmig --live --excel your_migration.xlsx
   ```

4. **Join Community:**
   - Report issues: [GitHub Issues](https://github.com/atef-aziz/azmig_tool/issues)
   - Contribute: See [Development Setup](#development-setup)

---

**Document Version**: 1.0  
**Last Updated**: October 6, 2025  
**Tool Version**: 1.0.0-dev
