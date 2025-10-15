"""
Validators Package

Azure migration validation architecture with specialized core validators
and orchestrating wrapper validators.

Core Validators (validators.core):
- Individual validation concerns (region, SKU, storage, etc.)
- Single responsibility, composable, testable
- Credential-based authentication

Wrapper Validators (validators.wrappers):
- High-level orchestration of core validators
- Configuration-driven validation execution  
- Result aggregation and reporting

Usage:
    # Wrapper validator usage (recommended)
    from azmig_tool.validators.wrappers import ServersValidatorWrapper
    from azmig_tool.config.validation_config import get_validation_config
    
    wrapper = ServersValidatorWrapper(credential, get_validation_config())
    report = wrapper.validate_all(configs)
    
    # Direct core validator usage
    from azmig_tool.validators.core import RegionValidator
    validator = RegionValidator(credential)
    result = validator.validate(config)
"""

# Core validators - individual validation concerns
from .core import (
    AccessValidator,
    ApplianceValidator, 
    StorageValidator,
    QuotaValidator,
    RegionValidator,
    ResourceGroupValidator,
    VNetValidator,
    VMSkuValidator,
    DiskValidator,
    DiscoveryValidator,
    RbacValidator
)

# Wrapper validators - orchestrated validation workflows
from .wrappers import (
    LandingZoneValidatorWrapper,
    ServersValidatorWrapper
)

__all__ = [
    # Core validators
    "AccessValidator",
    "ApplianceValidator", 
    "StorageValidator",
    "QuotaValidator", 
    "RegionValidator",
    "ResourceGroupValidator",
    "VNetValidator",
    "VMSkuValidator",
    "DiskValidator",
    "DiscoveryValidator", 
    "RbacValidator",
    
    # Wrapper validators
    "LandingZoneValidatorWrapper",
    "ServersValidatorWrapper"
]
