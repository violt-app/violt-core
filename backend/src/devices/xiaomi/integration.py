# backend/src/devices/xiaomi/integration.py

"""
Violt Core Lite - Xiaomi Device Integration

This module implements the integration with Xiaomi devices using the miio library.
"""

from typing import Dict, List, Any, Optional, Type, Coroutine, Callable
import logging
import asyncio
from datetime import datetime
import uuid
import miio
from miio import (
    Device as MiioDeviceInstance,
)  # Alias to avoid confusion with our Device class
from miio.exceptions import DeviceException
from miio.integrations.vacuum.roborock import (
    vacuum,
)  # Import specific vacuum models if needed
from bleak import BleakClient
import struct
from ..bleak.integration import BleakIntegration
from ..base import Device, DeviceIntegration, DeviceIntegrationError, DeviceState
from ..capabilities import (
    OnOffCapability,
    BrightnessCapability,
    ColorCapability,
    TemperatureSensorCapability,  # Add if needed for sensors
    HumiditySensorCapability,  # Add if needed for sensors
    # MotionSensorCapability, # Add if needed for sensors
    VacuumCapability,
)

# Import websocket manager if needed for real-time updates *from* the integration
# from ...core.websocket import manager as websocket_manager

logger = logging.getLogger(__name__)

# --- Capability Implementations ---
# These remain largely the same, but now interact with a real miio_device instance


class XiaomiOnOffCapability(OnOffCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        xiaomi_device: XiaomiDevice = self.device  # Type hint for clarity
        if not xiaomi_device.miio_device:
            logger.warning(
                f"Command '{command}' failed: Device {xiaomi_device.name} not connected."
            )
            return False
        loop = asyncio.get_event_loop()
        try:
            if command == "turn_on":
                await loop.run_in_executor(None, xiaomi_device.miio_device.on)
                xiaomi_device.update_state({"power": "on"})
            elif command == "turn_off":
                await loop.run_in_executor(None, xiaomi_device.miio_device.off)
                xiaomi_device.update_state({"power": "off"})
            elif command == "toggle":
                # Fetch current state before toggling if not cached reliably
                # await xiaomi_device.refresh_state() # Be cautious about frequent refreshes
                current_power = xiaomi_device.state.get("power")
                if current_power == "on":
                    await loop.run_in_executor(None, xiaomi_device.miio_device.off)
                    xiaomi_device.update_state({"power": "off"})
                else:
                    await loop.run_in_executor(None, xiaomi_device.miio_device.on)
                    xiaomi_device.update_state({"power": "on"})
            else:
                logger.warning(f"Unsupported OnOff command: {command}")
                return False
            logger.debug(f"Executed '{command}' on {xiaomi_device.name}")
            return True
        except DeviceException as e:
            logger.error(f"Error executing {command} on {xiaomi_device.name}: {e}")
            xiaomi_device.set_status("offline")  # Mark as offline on error
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error executing {command} on {xiaomi_device.name}: {e}",
                exc_info=True,
            )
            return False


class XiaomiBrightnessCapability(BrightnessCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        xiaomi_device: XiaomiDevice = self.device
        if not xiaomi_device.miio_device or not hasattr(
            xiaomi_device.miio_device, "set_brightness"
        ):
            logger.warning(
                f"Command '{command}' failed: Device {xiaomi_device.name} not connected or doesn't support brightness."
            )
            return False
        loop = asyncio.get_event_loop()
        params = params or {}
        try:
            current_brightness = xiaomi_device.state.get(
                "brightness", 50
            )  # Default to 50 if unknown
            if command == "set_brightness":
                brightness = int(params.get("brightness", 50))
                brightness = max(1, min(100, brightness))  # Clamp value
                await loop.run_in_executor(
                    None, lambda: xiaomi_device.miio_device.set_brightness(brightness)
                )
                xiaomi_device.update_state({"brightness": brightness})
            elif command == "increase_brightness":
                step = int(params.get("step", 10))
                new_brightness = min(100, current_brightness + step)
                await loop.run_in_executor(
                    None,
                    lambda: xiaomi_device.miio_device.set_brightness(new_brightness),
                )
                xiaomi_device.update_state({"brightness": new_brightness})
            elif command == "decrease_brightness":
                step = int(params.get("step", 10))
                new_brightness = max(1, current_brightness - step)
                await loop.run_in_executor(
                    None,
                    lambda: xiaomi_device.miio_device.set_brightness(new_brightness),
                )
                xiaomi_device.update_state({"brightness": new_brightness})
            else:
                logger.warning(f"Unsupported Brightness command: {command}")
                return False
            logger.debug(f"Executed '{command}' on {xiaomi_device.name}")
            return True
        except (DeviceException, ValueError, TypeError) as e:
            logger.error(f"Error executing {command} on {xiaomi_device.name}: {e}")
            if isinstance(e, DeviceException):
                xiaomi_device.set_status("offline")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error executing {command} on {xiaomi_device.name}: {e}",
                exc_info=True,
            )
            return False


class XiaomiColorCapability(ColorCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        xiaomi_device: XiaomiDevice = self.device
        if not xiaomi_device.miio_device:
            logger.warning(
                f"Command '{command}' failed: Device {xiaomi_device.name} not connected."
            )
            return False
        loop = asyncio.get_event_loop()
        params = params or {}
        try:
            if command == "set_color":
                if not hasattr(xiaomi_device.miio_device, "set_rgb"):
                    logger.warning(
                        f"Device {xiaomi_device.name} does not support set_rgb"
                    )
                    return False
                color = params.get("color", {"r": 255, "g": 255, "b": 255})
                r, g, b = color.get("r", 255), color.get("g", 255), color.get("b", 255)
                rgb_int = (r << 16) + (g << 8) + b  # Some miio devices expect integer
                await loop.run_in_executor(
                    None, lambda: xiaomi_device.miio_device.set_rgb(rgb_int)
                )
                xiaomi_device.update_state(
                    {"color": {"r": r, "g": g, "b": b}}
                )  # Update with dict
            elif command == "set_color_temp":
                if not hasattr(xiaomi_device.miio_device, "set_color_temp"):
                    logger.warning(
                        f"Device {xiaomi_device.name} does not support set_color_temp"
                    )
                    return False
                color_temp = int(params.get("color_temp", 4000))
                # Add validation for device's supported color temp range if available
                await loop.run_in_executor(
                    None, lambda: xiaomi_device.miio_device.set_color_temp(color_temp)
                )
                xiaomi_device.update_state({"color_temp": color_temp})
            else:
                logger.warning(f"Unsupported Color command: {command}")
                return False
            logger.debug(f"Executed '{command}' on {xiaomi_device.name}")
            return True
        except (DeviceException, ValueError, TypeError) as e:
            logger.error(f"Error executing {command} on {xiaomi_device.name}: {e}")
            if isinstance(e, DeviceException):
                xiaomi_device.set_status("offline")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error executing {command} on {xiaomi_device.name}: {e}",
                exc_info=True,
            )
            return False


class XiaomiVacuumCapability(VacuumCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        xiaomi_device: XiaomiDevice = self.device
        if not xiaomi_device.miio_device or not isinstance(
            xiaomi_device.miio_device, miio.Vacuum
        ):  # Check type
            logger.warning(
                f"Command '{command}' failed: Device {xiaomi_device.name} not connected or not a vacuum."
            )
            return False
        loop = asyncio.get_event_loop()
        params = params or {}
        vacuum_instance: miio.Vacuum = xiaomi_device.miio_device  # Type hint
        try:
            if command == "start":
                await loop.run_in_executor(None, vacuum_instance.start)
            elif command == "stop":
                await loop.run_in_executor(None, vacuum_instance.stop)
            elif command == "pause":
                await loop.run_in_executor(None, vacuum_instance.pause)
            elif command == "return_to_base":
                await loop.run_in_executor(None, vacuum_instance.home)
            elif command == "set_fan_speed":
                # Fan speed might be int or preset string depending on model
                fan_speed_input = params.get("fan_speed", "standard")  # or an int
                # Map preset name to speed value if needed (e.g., using vacuum_instance.fan_speed_presets())
                presets = await loop.run_in_executor(
                    None, vacuum_instance.fan_speed_presets
                )
                if (
                    isinstance(fan_speed_input, str)
                    and fan_speed_input.lower() in presets
                ):
                    speed_value = presets[fan_speed_input.lower()]
                    await loop.run_in_executor(
                        None, lambda: vacuum_instance.set_fan_speed(speed_value)
                    )
                    xiaomi_device.update_state({"fan_speed": fan_speed_input.lower()})
                elif isinstance(fan_speed_input, int):
                    # Directly set int if model supports it, validate range first
                    await loop.run_in_executor(
                        None, lambda: vacuum_instance.set_fan_speed(fan_speed_input)
                    )
                    # Try to find matching preset name for state update
                    preset_name = next(
                        (k for k, v in presets.items() if v == fan_speed_input),
                        str(fan_speed_input),
                    )
                    xiaomi_device.update_state({"fan_speed": preset_name})
                else:
                    logger.warning(
                        f"Invalid fan speed '{fan_speed_input}'. Supported: {list(presets.keys())}"
                    )
                    return False
            # Add other vacuum commands: locate, clean_spot, clean_segment, etc.
            # elif command == "locate": await loop.run_in_executor(None, vacuum_instance.find)
            else:
                logger.warning(f"Unsupported Vacuum command: {command}")
                return False

            # Optimistically update state for some commands, or trigger refresh
            if command in ["start", "stop", "pause", "return_to_base"]:
                # State might change, trigger refresh after a short delay?
                asyncio.create_task(
                    asyncio.sleep(2).then(xiaomi_device.refresh_state())
                )
                pass

            logger.debug(f"Executed '{command}' on {xiaomi_device.name}")
            return True
        except DeviceException as e:
            logger.error(f"Error executing {command} on {xiaomi_device.name}: {e}")
            xiaomi_device.set_status("offline")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error executing {command} on {xiaomi_device.name}: {e}",
                exc_info=True,
            )
            return False


# --- Xiaomi BLE Device Class ---
# Xiaomi BLE Service UUIDs
XIAOMI_SERVICE_UUID = "fe95"
XIAOMI_CHARACTERISTIC_UUID = "00001a00-0000-1000-8000-00805f9b34fb"


class XiaomiBLEIntegration(BleakIntegration):
    def __init__(self):
        super().__init__()
        self._supported_devices = {
            "LYWSD03MMC": {"name": "Xiaomi Temperature/Humidity Sensor"},
            "MHO-C401": {"name": "Xiaomi Hygrometer"},
            "MHO-C303": {"name": "Xiaomi Smart Clock"},
        }

    async def read_sensor_data(self, device_address: str) -> Dict[str, Any]:
        """Read data from Xiaomi BLE sensor"""
        if device_address not in self._connected_devices:
            await self.connect_to_device(device_address)

        client = self._connected_devices[device_address]
        try:
            # Read characteristic data
            raw_data = await client.read_gatt_char(XIAOMI_CHARACTERISTIC_UUID)

            # Parse Xiaomi-specific data format
            return self._parse_xiaomi_data(raw_data)
        except Exception as e:
            raise Exception(f"Failed to read Xiaomi sensor data: {str(e)}")

    def _parse_xiaomi_data(self, raw_data: bytes) -> Dict[str, Any]:
        """Parse Xiaomi's proprietary BLE data format"""
        # Example parsing for temperature/humidity sensors
        if len(raw_data) >= 6:
            temp = struct.unpack("<h", raw_data[0:2])[0] / 10.0
            humidity = struct.unpack("<H", raw_data[2:4])[0] / 10.0
            battery = raw_data[4] & 0x7F
            return {"temperature": temp, "humidity": humidity, "battery": battery}
        return {}


# --- Xiaomi Device Class ---
class XiaomiDevice(Device):
    """Implementation of Device for Xiaomi devices using python-miio."""

    def __init__(
        self,
        device_id: str,
        name: str,
        device_type: str,
        manufacturer: str = "Xiaomi",
        model: Optional[str] = None,  # Model identifier from discovery if available
        location: Optional[str] = None,
        ip_address: Optional[str] = None,
        token: Optional[str] = None,  # This should be the actual token
        # Add user_id if needed by callbacks
        # user_id: Optional[str] = None,
    ):
        super().__init__(
            device_id=device_id,
            name=name,
            device_type=device_type.lower(),  # Normalize type
            manufacturer=manufacturer,
            model=model or "Unknown Xiaomi",  # Use model if provided
            location=location,
            integration_type="xiaomi",
        )
        self.ip_address = ip_address
        # Store token securely if possible, avoid logging it directly
        self._token = (
            token  # Use placeholder like YOUR_XIAOMI_TOKEN_HERE if not provided
        )
        self.miio_device: Optional[MiioDeviceInstance] = None
        self.model_info: Optional[Dict[str, Any]] = None  # Store discovered model info

        # Add capabilities based on likely device type (can be refined after connection)
        self._add_capabilities_by_type(self.type)

    def _add_capabilities_by_type(self, device_type: str):
        """Add capabilities based on device type string."""
        self.capabilities.clear()  # Clear existing before adding
        if device_type in [
            "light",
            "bulb",
            "ceiling_light",
            "gateway",
        ]:  # Gateway might have light
            self.add_capability(XiaomiOnOffCapability(self))
            self.add_capability(XiaomiBrightnessCapability(self))
            self.add_capability(XiaomiColorCapability(self))
        elif device_type in ["switch", "plug", "outlet"]:
            self.add_capability(XiaomiOnOffCapability(self))
        elif device_type == "vacuum":
            self.add_capability(XiaomiVacuumCapability(self))
        elif device_type == "sensor_ht":  # Example humidity/temp sensor
            self.add_capability(TemperatureSensorCapability(self))
            self.add_capability(HumiditySensorCapability(self))
        # Add more types: airpurifier, fan, humidifier, motion_sensor etc.
        # else: logger.warning(f"Capabilities not defined for Xiaomi device type: {device_type}")

    async def connect(self) -> bool:
        """Connect to the device using miio."""
        if not self.ip_address:
            logger.error(f"Missing IP address for device {self.id} ({self.name})")
            return False
        if not self._token or self._token == "YOUR_XIAOMI_TOKEN_HERE":
            logger.error(
                f"Missing or placeholder token for device {self.id} ({self.name}) at {self.ip_address}. Please provide the actual token."
            )
            # Don't attempt connection without a real token
            self.set_status("offline_config")  # Custom status indicating config issue
            return False

        logger.debug(
            f"Attempting to connect to Xiaomi device: {self.name} ({self.ip_address})"
        )
        loop = asyncio.get_event_loop()
        try:
            # Use miio's device factory for better model detection if possible
            # This requires knowing the model string beforehand, which discovery might provide
            # if self.model:
            #     self.miio_device = await loop.run_in_executor(None, lambda: miio.device_factory(self.ip_address, self._token, model=self.model))
            # else: # Fallback to generic Device
            self.miio_device = await loop.run_in_executor(
                None, lambda: MiioDeviceInstance(self.ip_address, self._token)
            )

            # Get device info (includes model)
            self.model_info = await loop.run_in_executor(None, self.miio_device.info)
            if self.model_info and self.model_info.model:
                self.model = self.model_info.model
                logger.info(
                    f"Connected to {self.name} ({self.ip_address}), Model: {self.model}"
                )
                # Potentially re-evaluate capabilities based on detected model
                # self._add_capabilities_by_model(self.model)
            else:
                logger.warning(
                    f"Connected to {self.name} ({self.ip_address}), but failed to get detailed model info."
                )

            self.set_status("online")
            # Perform initial state refresh after successful connection
            await self.refresh_state()
            return True

        except DeviceException as e:
            logger.error(
                f"Failed to connect to Xiaomi device {self.name} ({self.ip_address}): {e}"
            )
            self.set_status("offline")
            self.miio_device = None
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error connecting to {self.name}: {e}", exc_info=True
            )
            self.set_status("offline")
            self.miio_device = None
            return False

    async def disconnect(self) -> bool:
        """Disconnect (miio doesn't maintain persistent connection, so just cleanup)."""
        logger.debug(f"Disconnecting Xiaomi device: {self.name}")
        self.miio_device = None
        self.set_status("offline")
        return True

    async def refresh_state(self) -> bool:
        """Refresh device state using miio."""
        if self.status == "offline_config":
            logger.debug(
                f"Skipping state refresh for {self.name}: Requires configuration (token)."
            )
            return False
        if not self.miio_device:
            logger.warning(
                f"Cannot refresh state for {self.name}: Device not connected. Attempting reconnect..."
            )
            # Try to reconnect before failing
            if not await self.connect():
                return False
            # If connect succeeded, miio_device is now set

        logger.debug(f"Refreshing state for {self.name} ({self.model})")
        loop = asyncio.get_event_loop()
        try:
            # Get device status - miio status() is synchronous
            status = await loop.run_in_executor(None, self.miio_device.status)
            logger.debug(f"Raw status for {self.name}: {status}")

            # --- Parse status based on known device types/models ---
            # This needs to be expanded based on the specific device models supported
            new_state = {}
            if isinstance(
                status, miio.integrations.light.yeelight.common.YeelightStatus
            ):  # Example for Yeelight
                new_state["power"] = status.power
                new_state["brightness"] = status.brightness
                new_state["color_temp"] = status.color_temp
                new_state["rgb"] = status.rgb  # Store raw RGB tuple
                new_state["color"] = {
                    "r": status.rgb[0],
                    "g": status.rgb[1],
                    "b": status.rgb[2],
                }  # User-friendly color
            elif isinstance(
                status, miio.integrations.plug.plug_common.PlugStatus
            ):  # Example for Plugs
                new_state["power"] = "on" if status.is_on else "off"
                if hasattr(status, "temperature"):
                    new_state["temperature"] = status.temperature
                # Add power load, etc. if available (status.load_power)
            elif isinstance(status, miio.VacuumStatus):  # Example for Vacuums
                new_state["status"] = str(
                    status.state
                )  # Convert state enum/code to string
                new_state["battery_level"] = status.battery
                new_state["fan_speed_preset"] = str(
                    status.fanspeed
                )  # Use preset name if available
                presets = await loop.run_in_executor(
                    None, self.miio_device.fan_speed_presets
                )
                new_state["fan_speed"] = next(
                    (k for k, v in presets.items() if v == status.fanspeed),
                    str(status.fanspeed),
                )
                new_state["is_charging"] = status.is_charging
                # Add more vacuum states: error, cleaning time, area, etc.
            elif isinstance(
                status, miio.gateway.gateway.GatewayStatus
            ):  # Example for Gateway
                # Gateways often have sub-devices, state might be complex
                new_state["illumination"] = status.illumination
                # Might need to query sub-devices separately
            # Add more elif blocks for AirPurifierStatus, SensorHTStatus, etc.
            else:
                # Fallback for unknown devices: try common attributes
                if hasattr(status, "is_on"):
                    new_state["power"] = "on" if status.is_on else "off"
                if hasattr(status, "brightness"):
                    new_state["brightness"] = status.brightness
                if hasattr(status, "temperature"):
                    new_state["temperature"] = status.temperature
                if hasattr(status, "humidity"):
                    new_state["humidity"] = status.humidity
                logger.warning(
                    f"Parsing state for unknown miio status type: {type(status)} for {self.name}. State: {new_state}"
                )
                if not new_state:  # If we couldn't parse anything useful
                    logger.error(
                        f"Unable to parse status for {self.name}. Raw status: {status}"
                    )
                    # Keep previous state? Or mark as error?
                    # self.set_status("error_state")
                    return False

            # Update internal state and timestamp
            self.update_state(new_state)  # This also updates last_updated
            if self.status != "online":
                self.set_status("online")  # Mark as online if refresh succeeds
            logger.debug(f"State refreshed for {self.name}: {self.state.to_dict()}")
            return True

        except DeviceException as e:
            logger.error(f"Error refreshing state for {self.name}: {e}")
            self.set_status("offline")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error refreshing state for {self.name}: {e}", exc_info=True
            )
            self.set_status("offline")  # Assume offline on unexpected error
            return False

    async def execute_command(
        self, command: str, params: Dict[str, Any] = None
    ) -> bool:
        """Execute a command using capabilities."""
        if self.status == "offline_config":
            logger.error(
                f"Cannot execute command '{command}' on {self.name}: Requires configuration."
            )
            return False
        if not self.miio_device and self.status != "offline":
            logger.warning(
                f"Device {self.name} not connected, attempting reconnect before command '{command}'..."
            )
            if not await self.connect():
                logger.error(
                    f"Reconnect failed. Cannot execute command '{command}' on {self.name}."
                )
                return False

        # Find capability that supports this command
        for capability in self.capabilities.values():
            if command in capability.get_commands():
                logger.debug(
                    f"Executing command '{command}' via capability '{capability.capability_type}' on {self.name}"
                )
                return await capability.execute(command, params)

        # If no capability found, maybe it's a raw miio command? (Use with caution)
        # if hasattr(self.miio_device, command):
        #     try:
        #         logger.debug(f"Executing raw miio command '{command}' on {self.name}")
        #         loop = asyncio.get_event_loop()
        #         method_to_call = getattr(self.miio_device, command)
        #         await loop.run_in_executor(None, lambda: method_to_call(**(params or {})))
        #         # Trigger state refresh after raw command?
        #         asyncio.create_task(asyncio.sleep(1).then(self.refresh_state()))
        #         return True
        #     except Exception as e:
        #          logger.error(f"Error executing raw miio command '{command}' on {self.name}: {e}")
        #          return False

        logger.warning(
            f"Unsupported command '{command}' for device {self.name} (Type: {self.type}, Model: {self.model})"
        )
        return False


# --- Xiaomi Integration Class ---
class XiaomiIntegration(DeviceIntegration):
    """Implementation of DeviceIntegration for Xiaomi devices."""

    integration_type = "xiaomi"
    name = "Xiaomi Mi Home"
    description = "Integration with Xiaomi Mi Home devices via local network"
    # Expand supported types as specific device classes are implemented
    supported_device_types = [
        "light",
        "bulb",
        "plug",
        "switch",
        "vacuum",
        "gateway",
        "sensor_ht",
    ]

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.lock = asyncio.Lock()
        logger.info(f"XiaomiIntegration __init__ called with config: {config}")
        self.discovery_task: Optional[asyncio.Task] = None
        self._discover_callback: Optional[Callable[[Dict[str, Any]], Coroutine]] = None

    async def setup(self, config: Dict[str, Any]) -> bool:
        """Set up the integration (currently no specific setup needed)."""
        self.config = config or {}
        logger.info(f"XiaomiIntegration.setup called. Config: {config}, Self: {self}")
        logger.info(f"Integration class dict after setup: {self.__dict__}")
        # Load devices specified in config?
        # await self.load_devices_from_config(self.config.get("devices", []))
        logger.info("Xiaomi integration setup complete.")
        return True

    async def discover_devices(
        self, callback: Optional[Callable[[Dict[str, Any]], Coroutine]] = None
    ) -> List[Dict[str, Any]]:
        """Discover Xiaomi devices on the local network using miio."""
        if self.discovery_task and not self.discovery_task.done():
            logger.warning("Xiaomi device discovery already in progress.")
            return []  # Return empty list or raise exception?

        logger.info("Starting Xiaomi device discovery...")
        self._discover_callback = callback  # Store callback for discovered devices
        discovered_devices_info: List[Dict[str, Any]] = []

        # Run discovery in a separate task to avoid blocking
        self.discovery_task = asyncio.create_task(
            self._run_discovery(discovered_devices_info)
        )

        # Wait for discovery task to complete (or implement a timeout)
        try:
            await self.discovery_task
            logger.info(
                f"Xiaomi discovery finished. Found {len(discovered_devices_info)} potential devices."
            )
        except Exception as e:
            logger.error(f"Xiaomi discovery task failed: {e}", exc_info=True)
        finally:
            self.discovery_task = None
            self._discover_callback = None

        return discovered_devices_info

    async def _run_discovery(self, discovered_info_list: List[Dict[str, Any]]):
        """Internal method to run miio discovery."""
        loop = asyncio.get_event_loop()
        try:
            # miio.discover is synchronous, run in executor
            # Consider adding a timeout to the discovery process
            discovered_miio_devices = await loop.run_in_executor(None, miio.discover)

            for ip, info in discovered_miio_devices.items():
                logger.debug(f"Discovered potential Xiaomi device at {ip}: {info}")
                device_data = {
                    "integration_type": self.integration_type,
                    "ip_address": ip,
                    "token": "YOUR_XIAOMI_TOKEN_HERE",  # Requires manual input
                    "model": info.model if hasattr(info, "model") else "Unknown",
                    "name": f"Xiaomi {info.model or 'Device'} ({ip})",  # Suggest name
                    # Determine potential type based on model string (needs mapping)
                    "type": (
                        self._guess_type_from_model(info.model)
                        if hasattr(info, "model")
                        else "unknown"
                    ),
                    "mac_address": info.mac if hasattr(info, "mac") else None,
                }
                discovered_info_list.append(device_data)
                # If a callback is provided, call it for each discovered device
                if self._discover_callback:
                    try:
                        await self._discover_callback(device_data)
                    except Exception as cb_err:
                        logger.error(f"Error in discovery callback for {ip}: {cb_err}")

        except Exception as e:
            logger.error(f"Error during miio discovery execution: {e}", exc_info=True)
            # Re-raise or handle as needed

    def _guess_type_from_model(self, model_str: Optional[str]) -> str:
        """Attempt to guess device type from model string."""
        if not model_str:
            return "unknown"
        model = model_str.lower()
        # This requires maintaining a list of known model prefixes/names
        if (
            "light" in model
            or "bulb" in model
            or "yeelight" in model
            or "lamp" in model
            or "ceiling" in model
        ):
            return "light"
        if (
            "plug" in model
            or "switch" in model
            or "outlet" in model
            or "ctrl_neutral" in model
        ):
            return "switch"
        if "vacuum" in model or "robot" in model or "roborock" in model:
            return "vacuum"
        if "gateway" in model or "lumi" in model:
            return "gateway"
        if "sensor_ht" in model:
            return "sensor_ht"  # Humidity/Temp
        if "airpurifier" in model or "air_purifier" in model:
            return "airpurifier"
        if "fan" in model:
            return "fan"
        # Add more mappings based on common Xiaomi models
        return "unknown"

    async def add_device(self, device_config: Dict[str, Any]) -> Optional[Device]:
        """Add a device instance and connect to it."""
        config = device_config.get("config", {})
        token = config.get("token") or device_config.get("token")
        if not token or token == "placeholder":
            raise DeviceIntegrationError(
                f"Missing or placeholder token for device {device_config.get('id')} ({device_config.get('name')}) at {device_config.get('ip_address')}. Please provide the actual token."
            )
        device_id = device_config.get(
            "id", str(uuid.uuid4())
        )  # Use provided ID or generate
        ip_address = device_config.get("ip_address")
        # token = device_config.get("token")

        if not ip_address:
            raise DeviceIntegrationError(
                "Missing 'ip_address' in device configuration."
            )
        if not token:
            # Allow adding without token for later configuration? Or require it now?
            # For now, require it, but use placeholder if needed during discovery phase.
            logger.warning(
                f"Missing 'token' for device at {ip_address}. Using placeholder."
            )
            token = "YOUR_XIAOMI_TOKEN_HERE"  # Or raise DeviceIntegrationError("Missing 'token'")

        # Prevent adding duplicates based on IP? Or allow multiple logical devices for one IP?
        # Assuming unique IP for now.
        async with self.lock:  # Protect self.devices access if needed (though add is likely called sequentially)
            existing = next(
                (
                    d
                    for d in self.devices.values()
                    if getattr(d, "ip_address", None) == ip_address
                ),
                None,
            )
            if existing:
                logger.warning(
                    f"Device with IP {ip_address} already exists ({existing.id}). Updating."
                )
                # Optionally update existing device config instead of adding new
                existing._token = token  # Update token
                # Update other config fields?
                if await existing.connect():  # Try reconnecting with new token
                    return existing
                else:
                    raise DeviceIntegrationError(
                        f"Failed to connect/update existing device at {ip_address}"
                    )

            # Create device instance
            device = XiaomiDevice(
                device_id=str(device_id),
                name=device_config.get("name", f"Xiaomi Device {ip_address}"),
                device_type=device_config.get(
                    "type", "unknown"
                ),  # Type might be refined on connect
                model=device_config.get("model"),
                location=device_config.get("location"),
                ip_address=ip_address,
                token=token,
            )

            # Attempt to connect
            if await device.connect():
                # Refine type based on connection info if needed
                if device.model and device.type == "unknown":
                    guessed_type = self._guess_type_from_model(device.model)
                    if guessed_type != "unknown":
                        logger.info(
                            f"Refined device type for {device.name} to '{guessed_type}' based on model {device.model}"
                        )
                        device.type = guessed_type
                        # Re-add capabilities based on refined type
                        device._add_capabilities_by_type(guessed_type)

                self.devices[device.id] = device
                logger.info(
                    f"Successfully added and connected to Xiaomi device: {device.name} ({device.id})"
                )
                return device
            else:
                # Connection failed, don't add to active devices unless specifically desired
                # Even if connection fails now, user might fix token later. Store it anyway?
                # For now, let's only add if connection is successful initially.
                # If adding without token, add it with offline_config status.
                if token == "YOUR_XIAOMI_TOKEN_HERE":
                    device.set_status("offline_config")
                    self.devices[device.id] = device  # Add but mark as needing config
                    logger.warning(
                        f"Added Xiaomi device {device.name} ({device.id}) but requires token configuration."
                    )
                    return device
                else:
                    # Connection failed with a provided token
                    raise DeviceIntegrationError(
                        f"Failed to connect to device {ip_address} with the provided token."
                    )

    async def remove_device(self, device_id: str) -> bool:
        """Remove a device instance."""
        async with self.lock:  # Protect self.devices access if needed
            if device_id in self.devices:
                device = self.devices.pop(device_id)
                await device.disconnect()  # Cleanup state
                logger.info(f"Removed Xiaomi device: {device.name} ({device_id})")
                return True
            else:
                logger.warning(f"Xiaomi device not found for removal: {device_id}")
                return False


# --- Register with Registry ---
from ..registry import registry

registry.register_integration_class(XiaomiIntegration)
registry.register_integration_class(XiaomiBLEIntegration)
# or by having the registry scan a specific directory.

# Example registration (if registry is imported here):
# from ..registry import registry

# registry.register_integration_class(XiaomiIntegration)
# registry.register_integration_class(XiaomiBLEIntegration)
