"""
Violt Core Lite - Common Device Capabilities

This module defines common device capabilities that can be used across different integrations.
"""

from typing import Dict, List, Any, Optional
import logging
from abc import abstractmethod

from .base import DeviceCapability, Device

logger = logging.getLogger(__name__)


class OnOffCapability(DeviceCapability):
    """Capability for devices that can be turned on and off."""

    @property
    def capability_type(self) -> str:
        return "on_off"

    def get_commands(self) -> List[str]:
        return ["turn_on", "turn_off", "toggle"]

    def get_state(self) -> Dict[str, Any]:
        return {"power": self.device.state.get("power", "off")}

    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        pass


class BrightnessCapability(DeviceCapability):
    """Capability for devices with adjustable brightness."""

    @property
    def capability_type(self) -> str:
        return "brightness"

    def get_commands(self) -> List[str]:
        return ["set_brightness", "increase_brightness", "decrease_brightness"]

    def get_state(self) -> Dict[str, Any]:
        return {"brightness": self.device.state.get("brightness", 0)}

    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        pass


class ColorCapability(DeviceCapability):
    """Capability for devices with adjustable color."""

    @property
    def capability_type(self) -> str:
        return "color"

    def get_commands(self) -> List[str]:
        return ["set_color", "set_color_temp"]

    def get_state(self) -> Dict[str, Any]:
        return {
            "color": self.device.state.get("color", {"r": 255, "g": 255, "b": 255}),
            "color_temp": self.device.state.get("color_temp", 4000),
        }

    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        pass


class TemperatureSensorCapability(DeviceCapability):
    """Capability for temperature sensors."""

    @property
    def capability_type(self) -> str:
        return "temperature_sensor"

    def get_commands(self) -> List[str]:
        return ["get_temperature"]

    def get_state(self) -> Dict[str, Any]:
        return {"temperature": self.device.state.get("temperature", 0)}

    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        if command == "get_temperature":
            # This is a read-only capability, so just return the current state
            return True
        return False


class HumiditySensorCapability(DeviceCapability):
    """Capability for humidity sensors."""

    @property
    def capability_type(self) -> str:
        return "humidity_sensor"

    def get_commands(self) -> List[str]:
        return ["get_humidity"]

    def get_state(self) -> Dict[str, Any]:
        return {"humidity": self.device.state.get("humidity", 0)}

    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        if command == "get_humidity":
            # This is a read-only capability, so just return the current state
            return True
        return False


class MotionSensorCapability(DeviceCapability):
    """Capability for motion sensors."""

    @property
    def capability_type(self) -> str:
        return "motion_sensor"

    def get_commands(self) -> List[str]:
        return ["get_motion"]

    def get_state(self) -> Dict[str, Any]:
        return {"motion": self.device.state.get("motion", False)}

    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        if command == "get_motion":
            # This is a read-only capability, so just return the current state
            return True
        return False


class ThermostatCapability(DeviceCapability):
    """Capability for thermostats."""

    @property
    def capability_type(self) -> str:
        return "thermostat"

    def get_commands(self) -> List[str]:
        return ["set_temperature", "set_mode", "set_fan_mode"]

    def get_state(self) -> Dict[str, Any]:
        return {
            "target_temperature": self.device.state.get("target_temperature", 22),
            "current_temperature": self.device.state.get("current_temperature", 22),
            "mode": self.device.state.get("mode", "off"),
            "fan_mode": self.device.state.get("fan_mode", "auto"),
        }

    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        pass


class CoverCapability(DeviceCapability):
    """Capability for covers (blinds, curtains, etc.)."""

    @property
    def capability_type(self) -> str:
        return "cover"

    def get_commands(self) -> List[str]:
        return ["open", "close", "stop", "set_position"]

    def get_state(self) -> Dict[str, Any]:
        return {
            "position": self.device.state.get("position", 0),
            "state": self.device.state.get("state", "closed"),
        }

    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        pass


class LockCapability(DeviceCapability):
    """Capability for locks."""

    @property
    def capability_type(self) -> str:
        return "lock"

    def get_commands(self) -> List[str]:
        return ["lock", "unlock"]

    def get_state(self) -> Dict[str, Any]:
        return {"locked": self.device.state.get("locked", True)}

    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        pass


class VacuumCapability(DeviceCapability):
    """Capability for vacuum cleaners."""

    @property
    def capability_type(self) -> str:
        return "vacuum"

    def get_commands(self) -> List[str]:
        return ["start", "stop", "pause", "return_to_base", "set_fan_speed"]

    def get_state(self) -> Dict[str, Any]:
        return {
            "status": self.device.state.get("status", "idle"),
            "battery_level": self.device.state.get("battery_level", 0),
            "fan_speed": self.device.state.get("fan_speed", "normal"),
        }

    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Execute a command with parameters."""
        pass
