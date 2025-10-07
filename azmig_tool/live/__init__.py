"""
Live Validators - Real Azure API integration

This package contains live implementations that interact with Azure services.
"""

from .servers_validator import LiveServersValidator
from .landing_zone_validator import LiveLandingZoneValidator

__all__ = [
    'LiveServersValidator',
    'LiveLandingZoneValidator',
]
