"""
Azure Bulk Migration Tool

A comprehensive CLI tool for bulk migrating servers to Azure using Azure Migrate.
"""

# Core modules
from . import constants
from . import models
from . import base
from . import clients
from . import config
from . import formatters

# Core functionality
from .core import run_migration_tool

# Base interfaces
from .base import BaseValidatorInterface, BaseLandingZoneInterface

# Validators
from .validators import ServersValidator, LandingZoneValidator

# Helper utilities - NEW MODULE STRUCTURE
from .config import (
    ConfigParser,
    LandingZoneConfigParser,
    ExcelParser,
    ValidationConfig,
    ValidationConfigLoader,
    get_validation_config
)

from .formatters import EnhancedTableFormatter

from .clients import (
    AzureRestApiClient,
    AzureMigrateApiClient,
    AzureValidator,
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

    # Validators
    "ServersValidator",
    "LandingZoneValidator",

    # Config utilities
    "ConfigParser",
    "LandingZoneConfigParser",
    "Layer1ConfigParser",  # Backward compatibility alias
    "ExcelParser",
    "ValidationConfig",
    "ValidationConfigLoader",
    "get_validation_config",

    # Formatters
    "EnhancedTableFormatter",

    # Clients
    "AzureRestApiClient",
    "AzureMigrateApiClient",
    "AzureValidator",
    "AzureMigrateIntegration",
]

__version__ = "3.0.0"
