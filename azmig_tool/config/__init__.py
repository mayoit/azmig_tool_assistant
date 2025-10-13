"""
Configuration parsing and validation configuration

This module provides:
- ConfigParser: Primary parser for CSV/JSON (landing zone) and Excel (servers) files
- ValidationConfig: Backward compatibility for legacy validation configs 
- ValidationSettings: Modern project-persistent validation configuration (see models.py)

DEPRECATED: Layer1ConfigParser, ExcelParser - use ConfigParser instead
"""
from .parsers import ConfigParser, ExcelParser, Layer1ConfigParser
from .validation_config import ValidationConfig, ValidationConfigLoader, get_validation_config, reset_validation_config

# Backward compatibility aliases - use ConfigParser directly instead
from .parsers import ConfigParser as LandingZoneConfigParser
from .parsers import ConfigParser as ServerConfigParser

__all__ = [
    'ConfigParser',  # Primary parser - use this for new code
    'LandingZoneConfigParser',  # Alias for backward compatibility
    'ServerConfigParser',  # Alias for backward compatibility
    'Layer1ConfigParser',  # DEPRECATED - use ConfigParser
    'ExcelParser',  # DEPRECATED - use ConfigParser
    'ValidationConfig',  # Backward compatibility - use ValidationSettings model
    'ValidationConfigLoader',  # For loading legacy validation configs
    'get_validation_config',  # Singleton access to legacy config
    'reset_validation_config',  # Reset singleton for testing
]
