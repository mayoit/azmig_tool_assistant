#!/usr/bin/env python
"""
Test script to verify all imports work after reorganization
"""

from azmig_tool import (
    ConfigParser,
    EnhancedTableFormatter,
    ValidationConfig,
    AzureRestApiClient,
    AzureMigrateApiClient
)
from azmig_tool import Layer1ConfigParser
from azmig_tool.clients import AzureRestApiClient, AzureMigrateApiClient, AzureValidator, AzureMigrateIntegration
from azmig_tool.formatters import EnhancedTableFormatter
from azmig_tool.config import ConfigParser, LandingZoneConfigParser, ExcelParser, ValidationConfig
print("Testing imports from reorganized structure...")

# Test config module
print("✓ Config imports working")

# Test formatters module
print("✓ Formatters imports working")

# Test clients module
print("✓ Clients imports working")

# Test backward compatibility
assert Layer1ConfigParser == LandingZoneConfigParser, "Layer1ConfigParser alias not working"
print("✓ Layer1ConfigParser backward compatibility alias working")

# Test main package exports
print("✓ Main package exports working")

print("\n✅ All imports successful! Reorganization is working correctly.")
print(f"\n📦 Package Structure:")
print(f"  - azmig_tool.config.*    : Configuration parsing and validation")
print(f"  - azmig_tool.clients.*   : Azure API clients")
print(f"  - azmig_tool.formatters.* : Output formatting")
print(f"\n🔄 Backward Compatibility:")
print(f"  - Layer1ConfigParser → LandingZoneConfigParser (alias)")
print(f"  - All original imports still work from main package")
