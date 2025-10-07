"""
Mock Validators - Simulates validation without Azure API calls

This package contains mock implementations for offline testing and development.
"""

from .servers_validator import MockServersValidator
from .landing_zone_validator import MockLandingZoneValidator

__all__ = [
    'MockServersValidator',
    'MockLandingZoneValidator',
]
