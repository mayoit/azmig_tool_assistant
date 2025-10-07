"""
Base interfaces for validators - Defines contracts for mock and live implementations
"""

from .validator_interface import BaseValidatorInterface
from .landing_zone_interface import BaseLandingZoneInterface

__all__ = [
    'BaseValidatorInterface',
    'BaseLandingZoneInterface',
]
