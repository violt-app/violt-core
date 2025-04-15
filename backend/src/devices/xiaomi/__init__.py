"""
Xiaomi device integration module.

This module provides integration with Xiaomi smart home devices.
"""

# Import the integration class so it can be registered
from .integration import XiaomiIntegration

# This will make the module discoverable by the registry
__all__ = ['XiaomiIntegration']
