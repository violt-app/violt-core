# backend/src/devices/alexa/integration.py

"""
Violt Core Lite - Amazon Alexa Integration

This module implements the integration with Amazon Alexa Smart Home Skill API.
Requires OAuth2 setup and token management.
"""

from typing import Dict, List, Any, Optional, Coroutine, Callable
import logging
import asyncio
from datetime import datetime, timedelta
import uuid
import json
import aiohttp  # Import aiohttp

from ..base import Device, DeviceIntegration, DeviceIntegrationError, DeviceState
from ..capabilities import (
    OnOffCapability,
    BrightnessCapability,
    ColorCapability,
    ThermostatCapability,
    # Add other relevant Alexa capabilities: ColorTemperature, TemperatureSensor, etc.
)

# from ...core.websocket import manager as websocket_manager # If needed

logger = logging.getLogger(__name__)

# --- Constants ---
# Replace with actual Alexa API endpoints
ALEXA_API_BASE_URL = "https://api.amazonalexa.com"  # Example, check documentation
ALEXA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"  # Example
ALEXA_EVENT_GATEWAY_URL = f"{ALEXA_API_BASE_URL}/v3/events"  # Example

# --- Capability Implementations ---
# These need to map Violt commands to Alexa directives


class AlexaOnOffCapability(OnOffCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        alexa_device: AlexaDevice = self.device
        alexa_command = None
        if command == "turn_on":
            alexa_command = "TurnOn"
        elif command == "turn_off":
            alexa_command = "TurnOff"
        # Toggle needs current state, which might require a state report first if not cached
        # Or, send TurnOn/TurnOff based on cached state (less reliable)
        elif command == "toggle":
            current_power = alexa_device.state.get("power")
            if current_power == "ON":
                alexa_command = "TurnOff"
            else:
                alexa_command = "TurnOn"

        if alexa_command:
            return await alexa_device.send_alexa_directive(
                "Alexa.PowerController", alexa_command, {}
            )
        else:
            logger.warning(f"Unsupported OnOff command: {command}")
            return False


class AlexaBrightnessCapability(BrightnessCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        alexa_device: AlexaDevice = self.device
        params = params or {}
        try:
            if command == "set_brightness":
                brightness = int(params.get("brightness", 50))
                payload = {
                    "brightness": max(0, min(100, brightness))
                }  # Alexa uses 0-100
                return await alexa_device.send_alexa_directive(
                    "Alexa.BrightnessController", "SetBrightness", payload
                )
            elif command == "increase_brightness":
                delta = int(params.get("step", 10))
                payload = {"brightnessDelta": min(100, max(-100, delta))}
                return await alexa_device.send_alexa_directive(
                    "Alexa.BrightnessController", "AdjustBrightness", payload
                )
            elif command == "decrease_brightness":
                delta = int(params.get("step", 10))
                payload = {
                    "brightnessDelta": -min(100, max(-100, delta))
                }  # Negative delta
                return await alexa_device.send_alexa_directive(
                    "Alexa.BrightnessController", "AdjustBrightness", payload
                )
            else:
                logger.warning(f"Unsupported Brightness command: {command}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter for brightness command {command}: {e}")
            return False


class AlexaColorCapability(ColorCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        alexa_device: AlexaDevice = self.device
        params = params or {}
        try:
            if command == "set_color":
                color_data = params.get("color", {})
                # Alexa uses HSB, need conversion from RGB
                # Placeholder: Assume RGB params are provided, convert here (or require HSB)
                hsb_color = self._rgb_to_hsb(
                    color_data.get("r", 255),
                    color_data.get("g", 255),
                    color_data.get("b", 255),
                )
                if hsb_color:
                    payload = {
                        "color": {
                            "hue": hsb_color[0],
                            "saturation": hsb_color[1],
                            "brightness": hsb_color[2],
                        }
                    }
                    return await alexa_device.send_alexa_directive(
                        "Alexa.ColorController", "SetColor", payload
                    )
                else:
                    return False  # Conversion failed
            # Alexa uses ColorTemperatureController for temp
            elif command == "set_color_temp":
                if not alexa_device.has_capability(
                    "Alexa.ColorTemperatureController"
                ):  # Check if device supports this
                    logger.warning(
                        f"Device {alexa_device.name} does not support ColorTemperatureController"
                    )
                    return False
                temp = int(params.get("color_temp", 4000))
                payload = {"colorTemperatureInKelvin": temp}
                return await alexa_device.send_alexa_directive(
                    "Alexa.ColorTemperatureController", "SetColorTemperature", payload
                )
            else:
                logger.warning(f"Unsupported Color command: {command}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter for color command {command}: {e}")
            return False

    def _rgb_to_hsb(self, r, g, b):
        # Basic RGB to HSB conversion (simplified, use a library for accuracy)
        try:
            r, g, b = r / 255.0, g / 255.0, b / 255.0
            mx = max(r, g, b)
            mn = min(r, g, b)
            df = mx - mn
            h = 0.0
            if mx == mn:
                h = 0.0
            elif mx == r:
                h = (60 * ((g - b) / df) + 360) % 360
            elif mx == g:
                h = (60 * ((b - r) / df) + 120) % 360
            elif mx == b:
                h = (60 * ((r - g) / df) + 240) % 360
            s = 0.0 if mx == 0 else (df / mx)
            v = mx  # Brightness (0-1, Alexa uses 0-100?) - Alexa brightness is separate controller usually
            # Alexa uses H(0-360), S(0-1), B(0-1) for ColorController
            # But BrightnessController uses 0-100. Be careful how these interact.
            # Here we return H, S, V(as B) for the SetColor payload
            return h, s, v  # Check Alexa docs for exact scale (0-1 or 0-100 for S/B)
        except Exception as e:
            logger.error(f"RGB to HSB conversion failed: {e}")
            return None


class AlexaThermostatCapability(ThermostatCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        alexa_device: AlexaDevice = self.device
        params = params or {}
        try:
            if command == "set_temperature":
                temp = float(params.get("temperature", 22.0))
                # Alexa might require scale (CELSIUS/FAHRENHEIT)
                payload = {
                    "targetSetpoint": {"value": temp, "scale": "CELSIUS"}
                }  # Assume Celsius
                return await alexa_device.send_alexa_directive(
                    "Alexa.ThermostatController", "SetTargetTemperature", payload
                )
            elif command == "set_mode":
                mode = params.get("mode", "AUTO")  # Alexa modes are uppercase
                payload = {"thermostatMode": {"value": mode.upper()}}
                return await alexa_device.send_alexa_directive(
                    "Alexa.ThermostatController", "SetThermostatMode", payload
                )
            # Alexa doesn't have a standard Fan Mode controller, often custom or part of ThermostatMode/RangeController
            # elif command == "set_fan_mode": ...
            else:
                logger.warning(f"Unsupported Thermostat command: {command}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter for thermostat command {command}: {e}")
            return False


# --- Alexa Device Class ---


class AlexaDevice(Device):
    """Implementation of Device for Alexa devices."""

    def __init__(
        self,
        device_id: str,
        name: str,
        device_type: str,  # Violt's type (light, switch, etc.)
        manufacturer: str,
        model: Optional[str] = None,
        location: Optional[str] = None,
        endpoint_id: Optional[str] = None,  # Alexa's unique ID for the device
        capabilities_supported: List[
            str
        ] = None,  # List of Alexa capability interfaces (e.g., "Alexa.PowerController")
        integration: Optional["AlexaIntegration"] = None,
    ):
        super().__init__(
            device_id=device_id,
            name=name,
            device_type=device_type,
            manufacturer=manufacturer,
            model=model,
            location=location,
            integration_type="alexa",
        )
        self.endpoint_id = endpoint_id
        self.integration = integration
        self.alexa_capabilities = (
            capabilities_supported or []
        )  # Store supported Alexa interfaces
        self._add_violt_capabilities()  # Map Alexa caps to Violt caps

    def _add_violt_capabilities(self):
        """Add Violt capabilities based on supported Alexa interfaces."""
        self.capabilities.clear()
        if "Alexa.PowerController" in self.alexa_capabilities:
            self.add_capability(AlexaOnOffCapability(self))
        if "Alexa.BrightnessController" in self.alexa_capabilities:
            self.add_capability(AlexaBrightnessCapability(self))
        if "Alexa.ColorController" in self.alexa_capabilities:
            # Only add if ColorController is present
            self.add_capability(AlexaColorCapability(self))
        # Note: Alexa ColorTemperature is a separate capability
        # if "Alexa.ColorTemperatureController" in self.alexa_capabilities:
        # Add specific temp control or integrate into ColorCapability?
        # pass
        if "Alexa.ThermostatController" in self.alexa_capabilities:
            self.add_capability(AlexaThermostatCapability(self))
        # Map other Alexa capabilities (RangeController, TemperatureSensor etc.) to Violt capabilities

    def has_capability(self, capability_interface: str) -> bool:
        """Check if the device supports a specific Alexa capability interface."""
        return capability_interface in self.alexa_capabilities

    async def connect(self) -> bool:
        """Connect (verify API access and perform initial state report)."""
        if (
            not self.endpoint_id
            or not self.integration
            or not self.integration.access_token
        ):
            logger.error(
                f"Cannot connect Alexa device {self.name}: Missing endpoint ID, integration, or access token."
            )
            self.set_status("offline_config")
            return False

        logger.debug(
            f"Connecting/Verifying Alexa device: {self.name} ({self.endpoint_id})"
        )
        # Perform an initial state report or query to confirm connectivity
        refreshed = await self.refresh_state()
        if refreshed:
            self.set_status("online")
            logger.info(f"Alexa device verified: {self.name}")
        else:
            # Refresh failed, might be token issue or device offline from Alexa's perspective
            self.set_status("offline")  # Or maybe "error" / "offline_unreachable"
            logger.warning(
                f"Failed initial state refresh for Alexa device: {self.name}"
            )
            # Consider attempting token refresh here if refresh failed
            # if await self.integration.refresh_access_token():
            #    refreshed = await self.refresh_state() # Retry refresh
            #    if refreshed: self.set_status("online")

        return self.status == "online"

    async def disconnect(self) -> bool:
        """Disconnect (no persistent connection, just update status)."""
        self.set_status("offline")
        return True

    async def refresh_state(self) -> bool:
        """Refresh device state by requesting a state report from Alexa."""
        if not self.integration or not self.endpoint_id:
            return False

        logger.debug(f"Requesting state report for Alexa device: {self.name}")
        directive_namespace = "Alexa"
        directive_name = "ReportState"
        payload = {}  # ReportState doesn't need payload in request

        # Send the directive - uses the event gateway but is a request/response
        response_data = await self.integration._send_alexa_request(
            endpoint_id=self.endpoint_id,
            namespace=directive_namespace,
            name=directive_name,
            payload=payload,
        )

        if not response_data:
            self.set_status("offline")  # Assume offline if request failed
            return False

        # Parse the state report response
        # Structure: response_data['context']['properties'] is a list of properties
        new_state = {}
        reported_properties = response_data.get("context", {}).get("properties", [])
        for prop in reported_properties:
            namespace = prop.get("namespace")
            name = prop.get("name")
            value = prop.get("value")
            time_of_sample = prop.get("timeOfSample")  # TODO: Use this timestamp?
            # Map Alexa properties to Violt state keys
            if namespace == "Alexa.PowerController" and name == "powerState":
                new_state["power"] = value  # 'ON' or 'OFF'
            elif namespace == "Alexa.BrightnessController" and name == "brightness":
                new_state["brightness"] = value  # 0-100
            elif namespace == "Alexa.ColorController" and name == "color":
                # Value is { "hue": 0.0-360.0, "saturation": 0.0-1.0, "brightness": 0.0-1.0 }
                # Convert HSB back to RGB for Violt state? Or store HSB? Store both?
                # Storing Violt standard RGB for consistency
                h, s, v = (
                    value.get("hue"),
                    value.get("saturation"),
                    value.get("brightness"),
                )
                # rgb_tuple = self._hsb_to_rgb(h, s, v) # Requires helper
                # if rgb_tuple: new_state['color'] = {'r': rgb_tuple[0], 'g': rgb_tuple[1], 'b': rgb_tuple[2]}
                new_state["color_hsb"] = value  # Store raw HSB as well?
            elif (
                namespace == "Alexa.ColorTemperatureController"
                and name == "colorTemperatureInKelvin"
            ):
                new_state["color_temp"] = value  # Kelvin
            elif namespace == "Alexa.ThermostatController":
                if name == "targetSetpoint":
                    new_state["target_temperature"] = value.get(
                        "value"
                    )  # Assuming Celsius
                elif name == "thermostatMode":
                    new_state["mode"] = value.get(
                        "value", ""
                    ).lower()  # e.g., "HEAT" -> "heat"
            elif namespace == "Alexa.TemperatureSensor" and name == "temperature":
                new_state["current_temperature"] = value.get(
                    "value"
                )  # Assuming Celsius
            # Add mappings for other properties (EndpointHealth etc.)

        if new_state:
            self.update_state(new_state)
            if self.status != "online":
                self.set_status("online")
            logger.debug(f"State refreshed for Alexa device {self.name}: {new_state}")
            return True
        else:
            logger.warning(
                f"No state properties parsed from Alexa response for {self.name}. Response: {response_data}"
            )
            # Consider device offline if state report is empty/invalid?
            # self.set_status("offline_error")
            return False

    async def execute_command(
        self, command: str, params: Dict[str, Any] = None
    ) -> bool:
        """Execute a command using capabilities."""
        if self.status == "offline_config":
            logger.error(
                f"Cannot execute command '{command}' on {self.name}: Requires configuration/auth."
            )
            return False

        # Find capability and execute
        for capability in self.capabilities.values():
            if command in capability.get_commands():
                logger.debug(
                    f"Executing command '{command}' via Violt capability '{type(capability).__name__}' on {self.name}"
                )
                return await capability.execute(command, params)

        logger.warning(
            f"Unsupported Violt command '{command}' for Alexa device {self.name}"
        )
        return False

    async def send_alexa_directive(
        self, namespace: str, name: str, payload: Dict[str, Any]
    ) -> bool:
        """Helper to send a directive to this specific device."""
        if not self.integration or not self.endpoint_id:
            return False
        response_data = await self.integration._send_alexa_request(
            endpoint_id=self.endpoint_id,
            namespace=namespace,
            name=name,
            payload=payload,
        )
        # Basic check: Alexa usually returns an event object on success, check for its presence
        # More robust checking would parse the response payload if needed
        return response_data is not None and "event" in response_data


# --- Alexa Integration Class ---


class AlexaIntegration(DeviceIntegration):
    """Implementation of DeviceIntegration for Amazon Alexa."""

    integration_type = "alexa"
    name = "Amazon Alexa"
    description = "Integration with Amazon Alexa Smart Home Skill API"
    # Define types Violt can represent, mapped from Alexa categories
    supported_device_types = [
        "light",
        "switch",
        "plug",
        "thermostat",
        "sensor",
        "other",
    ]

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None  # Store securely!
        self.redirect_uri: Optional[str] = None
        self.access_token: Optional[str] = None  # Store securely!
        self.refresh_token: Optional[str] = None  # Store securely!
        self.token_expiry: Optional[datetime] = None
        self.discovery_active = False
        self.http_session: Optional[aiohttp.ClientSession] = None

    async def setup(self, config: Dict[str, Any]) -> bool:
        """Set up the integration, load config, and initialize session."""
        self.config = config or {}
        self.client_id = self.config.get("client_id")
        self.client_secret = self.config.get(
            "client_secret", "YOUR_ALEXA_CLIENT_SECRET"
        )  # Placeholder
        # Load tokens from config (should be stored securely, e.g., encrypted or separate vault)
        self.access_token = self.config.get("access_token")
        self.refresh_token = self.config.get("refresh_token")
        token_expiry_ts = self.config.get("token_expiry_timestamp")
        if token_expiry_ts:
            self.token_expiry = datetime.utcfromtimestamp(token_expiry_ts)

        if not self.client_id or self.client_secret == "YOUR_ALEXA_CLIENT_SECRET":
            logger.error("Alexa client_id and client_secret must be configured.")
            return False

        # Create a persistent HTTP session
        self.http_session = aiohttp.ClientSession()
        logger.info("Alexa integration setup initialized.")

        # Check if token needs refreshing
        if (
            self.access_token
            and self.token_expiry
            and datetime.utcnow() >= self.token_expiry
        ):
            logger.info("Alexa access token expired, attempting refresh...")
            if not await self.refresh_access_token():
                logger.warning(
                    "Failed to refresh Alexa access token. Authentication may fail."
                )
                self.access_token = None  # Clear expired token
        elif not self.access_token and self.refresh_token:
            logger.info("No Alexa access token, attempting refresh...")
            if not await self.refresh_access_token():
                logger.warning(
                    "Failed to get initial Alexa access token using refresh token."
                )

        if not self.access_token:
            logger.warning(
                "Alexa integration setup complete, but requires authentication (no valid access token)."
            )
            # Need an auth flow initiated elsewhere (e.g., via API endpoint)

        return True

    async def close_session(self):
        """Close the HTTP session."""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
            logger.info("Closed Alexa HTTP session.")

    # --- Authentication ---
    # Need methods for the OAuth2 flow (get auth URL, handle callback, exchange code for token)
    # These would likely be called by API endpoints, not directly by the engine.

    def get_authorization_url(self, state: str) -> Optional[str]:
        """Generate the Alexa authorization URL for the user."""
        if not self.client_id or not self.redirect_uri:
            logger.error("Cannot generate auth URL: Missing client_id or redirect_uri.")
            return None
        # Construct the OAuth2 URL (refer to Alexa LWA docs)
        # Example:
        # params = {
        #     'client_id': self.client_id,
        #     'response_type': 'code',
        #     'redirect_uri': self.redirect_uri,
        #     'scope': 'alexa::smarthome', # Adjust scope as needed
        #     'state': state
        # }
        # auth_url = f"https://www.amazon.com/ap/oa?{aiohttp.helpers.BasicAuth(...)}"
        # return auth_url
        logger.warning("get_authorization_url is a placeholder.")
        return f"https://placeholder.amazon.com/auth?client_id={self.client_id}&state={state}&redirect_uri={self.redirect_uri}&scope=alexa::smarthome&response_type=code"

    async def exchange_code_for_token(self, code: str) -> bool:
        """Exchange the authorization code for access and refresh tokens."""
        if (
            not self.http_session
            or not self.client_id
            or not self.client_secret
            or not self.redirect_uri
        ):
            logger.error("Cannot exchange code: Integration or config not ready.")
            return False

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        logger.info("Exchanging Alexa authorization code for token...")
        try:
            async with self.http_session.post(
                ALEXA_TOKEN_URL, data=payload, headers=headers
            ) as response:
                response_data = await response.json()
                if response.status == 200:
                    self.access_token = response_data.get("access_token")
                    self.refresh_token = response_data.get("refresh_token")
                    expires_in = response_data.get("expires_in")  # Seconds
                    if expires_in:
                        self.token_expiry = datetime.utcnow() + timedelta(
                            seconds=int(expires_in) - 60
                        )  # Add buffer
                    # Persist tokens securely (e.g., update config file/database)
                    self._update_stored_tokens()  # Placeholder for saving tokens
                    logger.info("Successfully obtained Alexa tokens.")
                    return True
                else:
                    logger.error(
                        f"Failed to exchange code: {response.status} - {response_data}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error exchanging Alexa code: {e}", exc_info=True)
            return False

    async def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if (
            not self.http_session
            or not self.refresh_token
            or not self.client_id
            or not self.client_secret
        ):
            logger.error(
                "Cannot refresh token: Missing refresh token or client credentials."
            )
            return False

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        logger.info("Refreshing Alexa access token...")
        try:
            async with self.http_session.post(
                ALEXA_TOKEN_URL, data=payload, headers=headers
            ) as response:
                response_data = await response.json()
                if response.status == 200:
                    self.access_token = response_data.get("access_token")
                    # Note: Refresh token might also be updated in the response
                    new_refresh = response_data.get("refresh_token")
                    if new_refresh:
                        self.refresh_token = new_refresh
                    expires_in = response_data.get("expires_in")
                    if expires_in:
                        self.token_expiry = datetime.utcnow() + timedelta(
                            seconds=int(expires_in) - 60
                        )  # Buffer
                    self._update_stored_tokens()  # Placeholder for saving tokens
                    logger.info("Successfully refreshed Alexa access token.")
                    return True
                else:
                    logger.error(
                        f"Failed to refresh Alexa token: {response.status} - {response_data}"
                    )
                    # If refresh fails (e.g., invalid refresh token), clear tokens?
                    self.access_token = None
                    self.refresh_token = None  # Potentially clear refresh token too
                    self.token_expiry = None
                    self._update_stored_tokens()
                    return False
        except Exception as e:
            logger.error(f"Error refreshing Alexa token: {e}", exc_info=True)
            return False

    def _update_stored_tokens(self):
        """Placeholder: Save the current tokens (access, refresh, expiry) securely."""
        logger.info("Persisting Alexa tokens (placeholder)...")
        # In a real app, update self.config and save it to a file or database securely.
        self.config["access_token"] = self.access_token
        self.config["refresh_token"] = self.refresh_token
        self.config["token_expiry_timestamp"] = (
            self.token_expiry.timestamp() if self.token_expiry else None
        )
        # Example: save_config(self.config, "config/integrations/alexa.yaml")

    # --- Device Discovery & Management ---

    async def discover_devices(
        self, callback: Optional[Callable[[Dict[str, Any]], Coroutine]] = None
    ) -> List[Dict[str, Any]]:
        """Discover devices via the Alexa Smart Home Skill API."""
        if self.discovery_active:
            logger.warning("Alexa device discovery already in progress.")
            return []
        if not self.access_token or not self.http_session:
            logger.error(
                "Cannot discover Alexa devices: Not authenticated or session not ready."
            )
            return []

        logger.info("Starting Alexa device discovery...")
        self.discovery_active = True
        discovered_devices_info: List[Dict[str, Any]] = []

        # Send Discovery directive
        directive_namespace = "Alexa.Discovery"
        directive_name = "Discover"
        payload = {
            "scope": {"type": "BearerToken", "token": self.access_token}
        }  # Use access token

        response_data = await self._send_alexa_request(
            # Discovery doesn't target a specific endpoint
            endpoint_id=None,  # Or use a generic ID if required by _send_alexa_request structure
            namespace=directive_namespace,
            name=directive_name,
            payload=payload,
        )

        if (
            response_data
            and "event" in response_data
            and response_data["event"]["header"]["name"] == "Discover.Response"
        ):
            endpoints = response_data["event"]["payload"].get("endpoints", [])
            logger.info(
                f"Alexa discovery response received, processing {len(endpoints)} endpoints."
            )
            for endpoint in endpoints:
                try:
                    ep_id = endpoint.get("endpointId")
                    manufacturer = endpoint.get("manufacturerName", "Unknown")
                    model = endpoint.get(
                        "description", "Alexa Device"
                    )  # Often description has model info
                    name = endpoint.get("friendlyName", f"Alexa {ep_id}")
                    display_cats = endpoint.get("displayCategories", [])
                    alexa_caps_list = [
                        cap.get("interface")
                        for cap in endpoint.get("capabilities", [])
                        if cap.get("interface")
                    ]

                    # Map Alexa display category to Violt type
                    violt_type = "other"
                    if "LIGHT" in display_cats:
                        violt_type = "light"
                    elif "SWITCH" in display_cats:
                        violt_type = "switch"
                    elif "SMARTPLUG" in display_cats:
                        violt_type = "plug"
                    elif "THERMOSTAT" in display_cats:
                        violt_type = "thermostat"
                    elif "TEMPERATURE_SENSOR" in display_cats:
                        violt_type = "sensor"
                    # Add more mappings

                    device_data = {
                        "integration_type": self.integration_type,
                        "endpoint_id": ep_id,  # Key identifier for Alexa
                        "name": name,
                        "type": violt_type,
                        "manufacturer": manufacturer,
                        "model": model,
                        "alexa_capabilities": alexa_caps_list,  # Store supported Alexa interfaces
                        "config_suggestion": {  # Info needed to add the device
                            "endpoint_id": ep_id,
                            "alexa_capabilities": alexa_caps_list,
                        },
                    }
                    discovered_devices_info.append(device_data)
                    if callback:
                        await callback(device_data)  # Notify callback

                except Exception as e:
                    logger.error(
                        f"Error processing discovered Alexa endpoint: {endpoint.get('endpointId')} - {e}",
                        exc_info=True,
                    )

        else:
            logger.error(
                f"Alexa discovery failed or received invalid response: {response_data}"
            )

        self.discovery_active = False
        logger.info(
            f"Alexa discovery finished. Found {len(discovered_devices_info)} usable devices."
        )
        return discovered_devices_info

    async def add_device(self, device_config: Dict[str, Any]) -> Optional[Device]:
        """Add an Alexa device instance based on discovered info."""
        device_id = device_config.get("id", str(uuid.uuid4()))  # Violt's internal ID
        endpoint_id = device_config.get("endpoint_id")  # Alexa's ID

        if not endpoint_id:
            raise DeviceIntegrationError("Missing 'endpoint_id' for Alexa device.")

        # Prevent duplicates based on endpoint_id
        async with self.lock:
            existing = next(
                (
                    d
                    for d in self.devices.values()
                    if getattr(d, "endpoint_id", None) == endpoint_id
                ),
                None,
            )
            if existing:
                logger.warning(
                    f"Alexa device with endpoint ID {endpoint_id} already exists ({existing.id}). Skipping add."
                )
                return existing  # Return existing instance

            # Create device instance
            device = AlexaDevice(
                device_id=str(device_id),
                name=device_config.get("name", f"Alexa Device {endpoint_id[:6]}"),
                device_type=device_config.get("type", "other"),
                manufacturer=device_config.get("manufacturer", "Unknown"),
                model=device_config.get("model"),
                location=device_config.get("location"),
                endpoint_id=endpoint_id,
                capabilities_supported=device_config.get("alexa_capabilities", []),
                integration=self,
            )

            # Attempt to connect (verify state report)
            if await device.connect():
                self.devices[device.id] = device
                logger.info(
                    f"Successfully added and verified Alexa device: {device.name} ({device.id})"
                )
                return device
            else:
                # Connection/verification failed
                # Add anyway but offline? Or reject? Rejecting for now.
                raise DeviceIntegrationError(
                    f"Failed to verify/connect to Alexa device {device.name} ({endpoint_id}). Check logs and Alexa app."
                )

    async def remove_device(self, device_id: str) -> bool:
        """Remove an Alexa device instance."""
        async with self.lock:
            if device_id in self.devices:
                device = self.devices.pop(device_id)
                await device.disconnect()  # Update status
                logger.info(f"Removed Alexa device: {device.name} ({device_id})")
                return True
            else:
                logger.warning(f"Alexa device not found for removal: {device_id}")
                return False

    # --- State Reporting and Directives ---

    async def get_device_state(self, endpoint_id: str) -> Dict[str, Any]:
        """Request and return the state for a specific endpoint ID."""
        # Find the Violt device ID associated with the endpoint ID
        violt_device = next(
            (d for d in self.devices.values() if d.endpoint_id == endpoint_id), None
        )
        if violt_device:
            # Use the device's refresh_state method
            if await violt_device.refresh_state():
                return violt_device.state.to_dict()
            else:
                logger.warning(
                    f"Failed to refresh state for endpoint {endpoint_id} via get_device_state"
                )
                return {}  # Return empty or raise error?
        else:
            logger.warning(
                f"Device with endpoint ID {endpoint_id} not found in integration."
            )
            # Potentially try a direct ReportState anyway? Risky without device context.
            return {}

    async def _send_alexa_request(
        self,
        endpoint_id: Optional[str],
        namespace: str,
        name: str,
        payload: Dict[str, Any],
        correlation_token: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a directive or discovery request to the Alexa Event Gateway."""
        if not self.http_session or not self.access_token:
            logger.error(
                "Cannot send Alexa request: Not authenticated or session not ready."
            )
            return None

        # Construct the Alexa event payload (Directive or Discover)
        request_id = str(uuid.uuid4())  # Unique message ID
        correlation_token = correlation_token or str(
            uuid.uuid4()
        )  # For tracking responses

        event = {
            (
                "directive" if namespace != "Alexa.Discovery" else "event"
            ): {  # Structure differs slightly
                "header": {
                    "namespace": namespace,
                    "name": name,
                    "messageId": request_id,
                    "payloadVersion": "3",
                    # Add correlationToken for directives expecting a response
                    **(
                        {"correlationToken": correlation_token}
                        if namespace != "Alexa.Discovery"
                        else {}
                    ),
                },
                "payload": payload,
            }
        }
        # Add endpoint structure for directives targeting a specific device
        if endpoint_id and namespace != "Alexa.Discovery":
            event["directive"]["endpoint"] = {
                "scope": {"type": "BearerToken", "token": self.access_token},
                "endpointId": endpoint_id,
            }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        logger.debug(f"Sending Alexa Request: {json.dumps(event)}")

        try:
            async with self.http_session.post(
                ALEXA_EVENT_GATEWAY_URL, json=event, headers=headers
            ) as response:
                response_text = (
                    await response.text()
                )  # Read text first for better error logging
                logger.debug(
                    f"Alexa Response Status: {response.status}, Body: {response_text}"
                )
                if (
                    response.status == 200 or response.status == 202
                ):  # Alexa can return 202 Accepted
                    try:
                        response_data = json.loads(response_text)
                        # Check for specific error responses from Alexa
                        if (
                            "event" in response_data
                            and "payload" in response_data["event"]
                        ):
                            payload = response_data["event"]["payload"]
                            if (
                                payload.get("type")
                                == "INVALID_AUTHORIZATION_CREDENTIAL"
                            ):
                                logger.error(
                                    "Alexa returned INVALID_AUTHORIZATION_CREDENTIAL. Token likely invalid."
                                )
                                # Trigger token refresh? Mark as unauthenticated?
                                self.access_token = None  # Clear potentially bad token
                                asyncio.create_task(self.refresh_access_token())
                                return None
                            elif payload.get("type") == "INTERNAL_SERVICE_EXCEPTION":
                                logger.error(
                                    f"Alexa internal error: {payload.get('message')}"
                                )
                                return None  # Treat as failure
                        return (
                            response_data  # Return full response for parsing by caller
                        )
                    except json.JSONDecodeError:
                        logger.error(
                            f"Failed to decode Alexa JSON response: {response_text}"
                        )
                        return None  # Treat as failure
                elif response.status == 401 or response.status == 403:
                    logger.error(
                        "Alexa authentication failed (401/403). Token may be invalid or expired."
                    )
                    self.access_token = None  # Clear potentially bad token
                    asyncio.create_task(self.refresh_access_token())  # Attempt refresh
                    return None
                else:
                    logger.error(
                        f"Alexa request failed: {response.status} - {response_text}"
                    )
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error sending Alexa request: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending Alexa request: {e}", exc_info=True)
            return None


# --- Register with Registry ---
from ..registry import registry

registry.register_integration_class(AlexaIntegration)
