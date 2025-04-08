"""
Violt Core Lite - Device Integration Base Module

This module defines the base classes and interfaces for device integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
import logging
import asyncio
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class DeviceIntegrationError(Exception):
    """Exception raised for errors in device integrations."""

    pass


class DeviceState:
    """Class representing device state."""

    def __init__(self, state_data: Dict[str, Any]):
        self._state = state_data

    def get(self, key: str, default: Any = None) -> Any:
        """Get state value by key."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set state value by key."""
        self._state[key] = value

    def update(self, state_data: Dict[str, Any]) -> None:
        """Update state with new data."""
        self._state.update(state_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return self._state.copy()

    def __getitem__(self, key: str) -> Any:
        """Get state value by key using dictionary syntax."""
        return self._state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set state value by key using dictionary syntax."""
        self._state[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if key exists in state."""
        return key in self._state

    def __str__(self) -> str:
        """String representation of state."""
        return str(self._state)


class DeviceCapability(ABC):
    """Base class for device capabilities."""

    def __init__(self, device: "Device"):
        self.device = device

    @property
    @abstractmethod
    def capability_type(self) -> str:
        """Get capability type."""
        pass

    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        pass

    @abstractmethod
    def get_commands(self) -> List[str]:
        """Get list of supported commands."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current state for this capability."""
        pass


class Device(ABC):
    """Base class for all devices."""

    def __init__(
        self,
        device_id: str,
        name: str,
        device_type: str,
        manufacturer: str,
        model: Optional[str] = None,
        location: Optional[str] = None,
        integration_type: str = "generic",
    ):
        self.id = device_id or str(uuid.uuid4())
        self.name = name
        self.type = device_type
        self.manufacturer = manufacturer
        self.model = model
        self.location = location
        self.integration_type = integration_type
        self.state = DeviceState({})
        self.properties = {}
        self.capabilities: Dict[str, DeviceCapability] = {}
        self.status = "offline"
        self.last_updated = datetime.utcnow()
        self._state_callbacks: List[Callable[[DeviceState], None]] = []

    def add_capability(self, capability: DeviceCapability) -> None:
        """Add a capability to the device."""
        self.capabilities[capability.capability_type] = capability

    def has_capability(self, capability_type: str) -> bool:
        """Check if device has a specific capability."""
        return capability_type in self.capabilities

    def get_capability(self, capability_type: str) -> Optional[DeviceCapability]:
        """Get a specific capability."""
        return self.capabilities.get(capability_type)

    def register_state_callback(self, callback: Callable[[DeviceState], None]) -> None:
        """Register a callback for state changes."""
        self._state_callbacks.append(callback)

    def update_state(self, state_data: Dict[str, Any]) -> None:
        """Update device state and notify callbacks."""
        self.state.update(state_data)
        self.last_updated = datetime.utcnow()

        # Notify callbacks
        for callback in self._state_callbacks:
            try:
                callback(self.state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")

    def set_status(self, status: str) -> None:
        """Set device status (online/offline)."""
        self.status = status
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "location": self.location,
            "integration_type": self.integration_type,
            "status": self.status,
            "state": self.state.to_dict(),
            "properties": self.properties,
            "capabilities": list(self.capabilities.keys()),
            "last_updated": self.last_updated.isoformat(),
        }

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the device."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the device."""
        pass

    @abstractmethod
    async def refresh_state(self) -> bool:
        """Refresh device state."""
        pass

    @abstractmethod
    async def execute_command(
        self, command: str, params: Dict[str, Any] = None
    ) -> bool:
        """Execute a command with parameters."""
        pass


class DeviceIntegration(ABC):
    """Base class for device integrations."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.devices: Dict[str, Device] = {}
        self.discovery_active = False

    @property
    @abstractmethod
    def integration_type(self) -> str:
        """Get integration type."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get integration name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get integration description."""
        pass

    @property
    @abstractmethod
    def supported_device_types(self) -> List[str]:
        """Get list of supported device types."""
        pass

    @abstractmethod
    async def setup(self, config: Dict[str, Any]) -> bool:
        """Set up the integration with configuration."""
        pass

    @abstractmethod
    async def discover_devices(self) -> List[Device]:
        """Discover devices for this integration."""
        pass

    @abstractmethod
    async def add_device(self, device_config: Dict[str, Any]) -> Optional[Device]:
        """Add a device with configuration."""
        pass

    @abstractmethod
    async def remove_device(self, device_id: str) -> bool:
        """Remove a device."""
        pass

    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        return self.devices.get(device_id)

    def get_devices(self) -> List[Device]:
        """Get all devices for this integration."""
        return list(self.devices.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert integration to dictionary."""
        return {
            "type": self.integration_type,
            "name": self.name,
            "description": self.description,
            "device_types": self.supported_device_types,
            "device_count": len(self.devices),
            "config": {
                k: v for k, v in self.config.items() if k != "token" and k != "password"
            },
        }
