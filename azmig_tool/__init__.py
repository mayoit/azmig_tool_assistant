"""
Azure Bulk Migration Tool

A comprehensive CLI tool for bulk migrating servers to Azure using Azure Migrate.
"""

# Core modules
from .core import constants, models, run_migration_tool
from . import base
from . import clients
from . import config

# Base interfaces
from .base import BaseValidatorInterface, BaseLandingZoneInterface

# Validators - new wrapper architecture
from .validators.wrappers import ServersValidatorWrapper, LandingZoneValidatorWrapper

# Helper utilities - NEW MODULE STRUCTURE
from .config import (
    ConfigParser,
    LandingZoneConfigParser,
    ExcelParser,
    ValidationConfig,
    ValidationConfigLoader,
    get_validation_config
)

from .clients import (
    AzureRestApiClient,
    AzureMigrateApiClient,
    AzureMigrateIntegration
)

# Backward compatibility - keep old imports working
# Layer1ConfigParser is now an alias for LandingZoneConfigParser
Layer1ConfigParser = LandingZoneConfigParser

# Backward compatibility - module-level imports

__all__ = [
    # Core functionality
    "run_migration_tool",

    # Base interfaces
    "BaseValidatorInterface",
    "BaseLandingZoneInterface",

    # Validators - new wrapper architecture
    "ServersValidatorWrapper",
    "LandingZoneValidatorWrapper",

    # Config utilities
    "ConfigParser",
    "LandingZoneConfigParser",
    "Layer1ConfigParser",  # Backward compatibility alias
    "ExcelParser",
    "ValidationConfig",
    "ValidationConfigLoader",
    "get_validation_config",

    # Clients
    "AzureRestApiClient",
    "AzureMigrateApiClient",
    "AzureMigrateIntegration",
]

__version__ = "3.0.0"
