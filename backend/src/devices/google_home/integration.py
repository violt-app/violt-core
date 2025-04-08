# backend/src/devices/google_home/integration.py

"""
Violt Core Lite - Google Home Integration

This module implements the integration with Google Smart Home Actions API.
Requires OAuth2 setup and token management. Uses the HomeGraph API.
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
    # Add other relevant Google capabilities: FanSpeed, TemperatureSetting, etc.
)

# from ...core.websocket import manager as websocket_manager # If needed

logger = logging.getLogger(__name__)

# --- Constants ---
# Replace with actual Google API endpoints
GOOGLE_API_BASE_URL = "https://homegraph.googleapis.com/v1"  # HomeGraph API
GOOGLE_TOKEN_URL = (
    "https://oauth2.googleapis.com/token"  # Standard Google OAuth2 token endpoint
)
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"  # Standard Google OAuth2 auth endpoint
REPORT_STATE_URL = f"{GOOGLE_API_BASE_URL}/devices:reportStateAndNotification"
REQUEST_SYNC_URL = f"{GOOGLE_API_BASE_URL}/devices:requestSync"
QUERY_URL = f"{GOOGLE_API_BASE_URL}/devices:query"
EXECUTE_URL = f"{GOOGLE_API_BASE_URL}/devices:execute"


# --- Capability Implementations ---
# Map Violt commands to Google device traits and commands


class GoogleHomeOnOffCapability(OnOffCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        google_device: GoogleHomeDevice = self.device
        on_state = None
        if command == "turn_on":
            on_state = True
        elif command == "turn_off":
            on_state = False
        elif command == "toggle":
            current_power = google_device.state.get(
                "power"
            )  # Assumes state has 'on' boolean
            on_state = (
                not current_power if isinstance(current_power, bool) else True
            )  # Default to turning on if state unknown

        if on_state is not None:
            return await google_device.send_google_command(
                "action.devices.commands.OnOff", {"on": on_state}
            )
        else:
            logger.warning(f"Unsupported OnOff command: {command}")
            return False


class GoogleHomeBrightnessCapability(BrightnessCapability):
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        google_device: GoogleHomeDevice = self.device
        params = params or {}
        google_command = None
        command_params = {}
        try:
            if command == "set_brightness":
                brightness = int(params.get("brightness", 50))
                google_command = "action.devices.commands.BrightnessAbsolute"
                command_params = {
                    "brightness": max(0, min(100, brightness))
                }  # Google uses 0-100
            # Google doesn't have a direct relative brightness command, need to calculate
            elif command in ["increase_brightness", "decrease_brightness"]:
                logger.warning(
                    f"Relative brightness '{command}' not directly supported by Google Home trait, using absolute."
                )
                # Get current brightness (might need refresh?)
                current_brightness = google_device.state.get("brightness", 50)
                step = int(params.get("step", 10))
                delta = step if command == "increase_brightness" else -step
                new_brightness = max(0, min(100, current_brightness + delta))
                google_command = "action.devices.commands.BrightnessAbsolute"
                command_params = {"brightness": new_brightness}
            else:
                logger.warning(f"Unsupported Brightness command: {command}")
                return False

            return await google_device.send_google_command(
                google_command, command_params
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter for brightness command {command}: {e}")
            return False


class GoogleHomeColorCapability(ColorCapability):
    # Google uses ColorSetting trait with different command options
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        google_device: GoogleHomeDevice = self.device
        params = params or {}
        google_command = "action.devices.commands.ColorAbsolute"  # Common command
        command_params = {}
        try:
            if command == "set_color":
                color_data = params.get("color", {})
                r, g, b = (
                    color_data.get("r", 255),
                    color_data.get("g", 255),
                    color_data.get("b", 255),
                )
                # Google uses integer representation for RGB
                rgb_int = (r << 16) + (g << 8) + b
                command_params = {"color": {"spectrumRgb": rgb_int}}
            elif command == "set_color_temp":
                temp = int(params.get("color_temp", 4000))
                command_params = {"color": {"temperature": temp}}  # Google uses Kelvin
            else:
                logger.warning(f"Unsupported Color command: {command}")
                return False

            return await google_device.send_google_command(
                google_command, command_params
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter for color command {command}: {e}")
            return False


class GoogleHomeThermostatCapability(ThermostatCapability):
    # Uses TemperatureSetting trait
    async def execute(self, command: str, params: Dict[str, Any] = None) -> bool:
        google_device: GoogleHomeDevice = self.device
        params = params or {}
        google_command = None
        command_params = {}
        try:
            if command == "set_temperature":
                temp = float(params.get("temperature", 22.0))
                # Google uses thermostatTemperatureSetpoint
                google_command = "action.devices.commands.ThermostatTemperatureSetpoint"
                # Assume Celsius, Google might infer or require unit based on device setup
                command_params = {"thermostatTemperatureSetpoint": temp}
            elif command == "set_mode":
                mode = params.get("mode", "auto")  # Google modes are lowercase strings
                google_command = "action.devices.commands.ThermostatSetMode"
                command_params = {"thermostatMode": mode.lower()}
            # Fan mode might be separate FanSpeed trait
            # elif command == "set_fan_mode": ...
            else:
                logger.warning(f"Unsupported Thermostat command: {command}")
                return False

            return await google_device.send_google_command(
                google_command, command_params
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter for thermostat command {command}: {e}")
            return False


# --- Google Home Device Class ---


class GoogleHomeDevice(Device):
    """Implementation of Device for Google Home devices."""

    def __init__(
        self,
        device_id: str,  # Violt's internal ID
        name: str,
        device_type: str,  # Violt's type
        manufacturer: str,
        model: Optional[str] = None,
        location: Optional[str] = None,
        google_device_id: Optional[str] = None,  # Google's unique ID for the device
        traits_supported: List[
            str
        ] = None,  # List of Google traits (e.g., "action.devices.traits.OnOff")
        integration: Optional["GoogleHomeIntegration"] = None,
    ):
        super().__init__(
            device_id=device_id,
            name=name,
            device_type=device_type,
            manufacturer=manufacturer,
            model=model,
            location=location,
            integration_type="google_home",
        )
        self.google_device_id = google_device_id  # Use google_device_id for API calls
        self.integration = integration
        self.google_traits = traits_supported or []
        self._add_violt_capabilities()

    def _add_violt_capabilities(self):
        """Add Violt capabilities based on supported Google traits."""
        self.capabilities.clear()
        if "action.devices.traits.OnOff" in self.google_traits:
            self.add_capability(GoogleHomeOnOffCapability(self))
        if "action.devices.traits.Brightness" in self.google_traits:
            self.add_capability(GoogleHomeBrightnessCapability(self))
        if "action.devices.traits.ColorSetting" in self.google_traits:
            self.add_capability(GoogleHomeColorCapability(self))
        if "action.devices.traits.TemperatureSetting" in self.google_traits:
            # This trait covers Thermostat and TemperatureSensor aspects
            self.add_capability(GoogleHomeThermostatCapability(self))
            # Could potentially add separate TempSensor capability too if needed
        # Map other Google traits (FanSpeed, Scene, Toggles, Modes etc.) to Violt capabilities

    def has_trait(self, trait: str) -> bool:
        """Check if the device supports a specific Google trait."""
        return trait in self.google_traits

    async def connect(self) -> bool:
        """Connect (verify API access and perform initial query)."""
        if (
            not self.google_device_id
            or not self.integration
            or not self.integration.access_token
        ):
            logger.error(
                f"Cannot connect Google Home device {self.name}: Missing Google device ID, integration, or access token."
            )
            self.set_status("offline_config")
            return False

        logger.debug(
            f"Connecting/Verifying Google Home device: {self.name} ({self.google_device_id})"
        )
        # Perform an initial state query to confirm connectivity
        refreshed = await self.refresh_state()
        if refreshed:
            self.set_status("online")
            logger.info(f"Google Home device verified: {self.name}")
        else:
            self.set_status("offline")  # Or specific error status
            logger.warning(
                f"Failed initial state query for Google Home device: {self.name}"
            )
            # Consider token refresh attempt

        return self.status == "online"

    async def disconnect(self) -> bool:
        """Disconnect (no persistent connection, just update status)."""
        self.set_status("offline")
        return True

    async def refresh_state(self) -> bool:
        """Refresh device state using the HomeGraph QUERY endpoint."""
        if not self.integration or not self.google_device_id:
            return False

        logger.debug(f"Querying state for Google Home device: {self.name}")
        query_payload = {
            "agentUserId": self.integration.agent_user_id,  # Agent user ID needed
            "payload": {"devices": [{"id": self.google_device_id}]},
        }
        response_data = await self.integration._send_google_api_request(
            QUERY_URL, query_payload
        )

        if (
            not response_data
            or "payload" not in response_data
            or "devices" not in response_data["payload"]
        ):
            logger.warning(
                f"Failed to query state or received invalid response for {self.name}. Response: {response_data}"
            )
            self.set_status("offline")  # Assume offline on query failure
            return False

        device_states = response_data["payload"]["devices"]
        if self.google_device_id not in device_states:
            logger.warning(
                f"Queried state for {self.name} ({self.google_device_id}) not found in response."
            )
            # Device might have been removed from Google Home?
            self.set_status("offline")  # Or "removed"?
            return False

        google_state = device_states[self.google_device_id]
        new_state = {}
        # Parse Google state based on traits
        if google_state.get("online"):
            self.set_status("online")
            if "on" in google_state:
                new_state["power"] = google_state["on"]  # Boolean state
            if "brightness" in google_state:
                new_state["brightness"] = google_state["brightness"]  # 0-100
            if "color" in google_state:
                if "spectrumRgb" in google_state["color"]:
                    rgb_int = google_state["color"]["spectrumRgb"]
                    r = (rgb_int >> 16) & 255
                    g = (rgb_int >> 8) & 255
                    b = rgb_int & 255
                    new_state["color"] = {"r": r, "g": g, "b": b}
                if "temperatureK" in google_state["color"]:
                    new_state["color_temp"] = google_state["color"]["temperatureK"]
            if "thermostatTemperatureSetpoint" in google_state:
                new_state["target_temperature"] = google_state[
                    "thermostatTemperatureSetpoint"
                ]
            if "thermostatTemperatureAmbient" in google_state:
                new_state["current_temperature"] = google_state[
                    "thermostatTemperatureAmbient"
                ]
            if "thermostatMode" in google_state:
                new_state["mode"] = google_state[
                    "thermostatMode"
                ]  # e.g., "heat", "cool"
            # Add other state mappings (fan speed, etc.)
        else:
            self.set_status("offline")  # Device is offline according to Google
            # Keep last known state or clear it? Clearing might be safer.
            # new_state = {} # Clear state if offline

        self.update_state(new_state)
        logger.debug(f"State refreshed for Google device {self.name}: {new_state}")
        return True

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
            f"Unsupported Violt command '{command}' for Google Home device {self.name}"
        )
        return False

    async def send_google_command(
        self, google_command: str, params: Dict[str, Any]
    ) -> bool:
        """Helper to send an EXECUTE command for this device."""
        if not self.integration or not self.google_device_id:
            return False

        execute_payload = {
            "agentUserId": self.integration.agent_user_id,
            "payload": {
                "commands": [
                    {
                        "devices": [{"id": self.google_device_id}],
                        "execution": [
                            {
                                "command": google_command,
                                "params": params,
                            }
                        ],
                    }
                ]
            },
        }
        response_data = await self.integration._send_google_api_request(
            EXECUTE_URL, execute_payload
        )

        # Check response status
        if (
            response_data
            and "payload" in response_data
            and "commands" in response_data["payload"]
        ):
            command_response = response_data["payload"]["commands"][
                0
            ]  # Assuming one command
            status = command_response.get("status")
            if status == "SUCCESS":
                logger.debug(
                    f"Google command {google_command} successful for {self.name}"
                )
                # Optionally update state optimistically based on command, or trigger refresh
                # Example optimistic update:
                if google_command == "action.devices.commands.OnOff":
                    self.update_state({"power": params.get("on", False)})
                elif google_command == "action.devices.commands.BrightnessAbsolute":
                    self.update_state({"brightness": params.get("brightness")})
                # etc.
                return True
            elif status == "PENDING":
                logger.info(
                    f"Google command {google_command} is PENDING for {self.name}"
                )
                # Need to handle async results later if required
                return True  # Treat as success for now
            elif status == "OFFLINE":
                logger.warning(
                    f"Google command {google_command} failed for {self.name}: Device OFFLINE"
                )
                self.set_status("offline")
                return False
            elif status == "ERROR":
                error_code = command_response.get("errorCode", "unknownError")
                logger.error(
                    f"Google command {google_command} failed for {self.name}: ERROR - {error_code}"
                )
                return False
            else:
                logger.error(
                    f"Google command {google_command} for {self.name} had unexpected status: {status}"
                )
                return False
        else:
            logger.error(
                f"Invalid or missing EXECUTE response for {self.name}. Response: {response_data}"
            )
            return False


# --- Google Home Integration Class ---


class GoogleHomeIntegration(DeviceIntegration):
    """Implementation of DeviceIntegration for Google Home."""

    integration_type = "google_home"
    name = "Google Home"
    description = "Integration with Google Smart Home Actions API"
    supported_device_types = [
        "light",
        "switch",
        "plug",
        "thermostat",
        "scene",
        "other",
    ]  # Scene is a device type in Google

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # OAuth Credentials (store securely!)
        self.project_id: Optional[str] = (
            None  # Google Cloud Project ID for Device Access / HomeGraph
        )
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.redirect_uri: Optional[str] = None  # Needed for OAuth flow
        # Tokens (store securely!)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        # Agent User ID (Stable ID representing the Violt user in HomeGraph)
        self.agent_user_id: Optional[str] = (
            None  # Typically corresponds to Violt user ID
        )
        # HTTP Session
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.discovery_active = False

    async def setup(self, config: Dict[str, Any]) -> bool:
        """Set up the integration, load config, initialize session."""
        self.config = config or {}
        self.project_id = self.config.get("project_id")
        self.client_id = self.config.get("client_id")
        self.client_secret = self.config.get(
            "client_secret", "YOUR_GOOGLE_CLIENT_SECRET"
        )  # Placeholder
        self.redirect_uri = self.config.get(
            "redirect_uri"
        )  # Usually Violt's callback URL
        self.agent_user_id = self.config.get(
            "agent_user_id", "default_violt_user"
        )  # MUST BE STABLE PER USER

        # Load tokens
        self.access_token = self.config.get("access_token")
        self.refresh_token = self.config.get("refresh_token")
        token_expiry_ts = self.config.get("token_expiry_timestamp")
        if token_expiry_ts:
            self.token_expiry = datetime.utcfromtimestamp(token_expiry_ts)

        if (
            not self.project_id
            or not self.client_id
            or self.client_secret == "YOUR_GOOGLE_CLIENT_SECRET"
        ):
            logger.error(
                "Google Home project_id, client_id, and client_secret must be configured."
            )
            return False

        self.http_session = aiohttp.ClientSession()
        logger.info("Google Home integration setup initialized.")

        # Token refresh logic (similar to Alexa)
        if (
            self.access_token
            and self.token_expiry
            and datetime.utcnow() >= self.token_expiry
        ):
            logger.info("Google access token expired, attempting refresh...")
            if not await self.refresh_access_token():
                logger.warning("Failed to refresh Google access token.")
                self.access_token = None
        elif not self.access_token and self.refresh_token:
            logger.info("No Google access token, attempting refresh...")
            if not await self.refresh_access_token():
                logger.warning("Failed to get initial Google access token.")

        if not self.access_token:
            logger.warning(
                "Google Home integration setup complete, but requires authentication."
            )

        return True

    async def close_session(self):
        """Close the HTTP session."""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
            logger.info("Closed Google Home HTTP session.")

    # --- Authentication (OAuth2 Flow) ---
    # Similar methods needed as Alexa: get_authorization_url, exchange_code_for_token

    def get_authorization_url(self, state: str) -> Optional[str]:
        """Generate the Google authorization URL."""
        if not self.client_id or not self.redirect_uri:
            return None
        # Refer to Google Identity OAuth 2.0 docs for web server apps
        # scope typically includes 'https://www.googleapis.com/auth/homegraph'
        # and potentially others like SDM API if used directly.
        # params = {
        #      'client_id': self.client_id,
        #      'redirect_uri': self.redirect_uri,
        #      'response_type': 'code',
        #      'scope': 'https://www.googleapis.com/auth/homegraph', # Adjust scope
        #      'access_type': 'offline', # To get refresh token
        #      'prompt': 'consent', # Force consent screen for refresh token
        #      'state': state
        # }
        # auth_url = f"{GOOGLE_AUTH_URL}?{aiohttp.helpers.BasicAuth(...)}"
        # return auth_url
        logger.warning("get_authorization_url is a placeholder.")
        return f"{GOOGLE_AUTH_URL}?client_id={self.client_id}&state={state}&redirect_uri={self.redirect_uri}&scope=https://www.googleapis.com/auth/homegraph&response_type=code&access_type=offline&prompt=consent"

    async def exchange_code_for_token(self, code: str) -> bool:
        """Exchange the authorization code for tokens."""
        if (
            not self.http_session
            or not self.client_id
            or not self.client_secret
            or not self.redirect_uri
        ):
            return False
        payload = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        logger.info("Exchanging Google authorization code for token...")
        try:
            async with self.http_session.post(
                GOOGLE_TOKEN_URL, data=payload, headers=headers
            ) as response:
                response_data = await response.json()
                if response.status == 200:
                    self.access_token = response_data.get("access_token")
                    self.refresh_token = response_data.get(
                        "refresh_token"
                    )  # Only sent first time usually
                    expires_in = response_data.get("expires_in")
                    if expires_in:
                        self.token_expiry = datetime.utcnow() + timedelta(
                            seconds=int(expires_in) - 60
                        )
                    self._update_stored_tokens()
                    logger.info("Successfully obtained Google tokens.")
                    # After getting tokens, trigger a sync request
                    await self.request_sync()
                    return True
                else:
                    logger.error(
                        f"Failed to exchange Google code: {response.status} - {response_data}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error exchanging Google code: {e}", exc_info=True)
            return False

    async def refresh_access_token(self) -> bool:
        """Refresh the Google access token."""
        if (
            not self.http_session
            or not self.refresh_token
            or not self.client_id
            or not self.client_secret
        ):
            logger.error(
                "Cannot refresh Google token: Missing refresh token or client credentials."
            )
            return False
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        logger.info("Refreshing Google access token...")
        try:
            async with self.http_session.post(
                GOOGLE_TOKEN_URL, data=payload, headers=headers
            ) as response:
                response_data = await response.json()
                if response.status == 200:
                    self.access_token = response_data.get("access_token")
                    expires_in = response_data.get("expires_in")
                    if expires_in:
                        self.token_expiry = datetime.utcnow() + timedelta(
                            seconds=int(expires_in) - 60
                        )
                    # Refresh token usually remains the same unless revoked
                    self._update_stored_tokens()
                    logger.info("Successfully refreshed Google access token.")
                    return True
                else:
                    logger.error(
                        f"Failed to refresh Google token: {response.status} - {response_data}"
                    )
                    self.access_token = None
                    # Don't necessarily clear refresh token unless error indicates it's invalid
                    self.token_expiry = None
                    self._update_stored_tokens()
                    return False
        except Exception as e:
            logger.error(f"Error refreshing Google token: {e}", exc_info=True)
            return False

    def _update_stored_tokens(self):
        """Placeholder: Save the current tokens securely."""
        logger.info("Persisting Google tokens (placeholder)...")
        self.config["access_token"] = self.access_token
        self.config["refresh_token"] = self.refresh_token
        self.config["token_expiry_timestamp"] = (
            self.token_expiry.timestamp() if self.token_expiry else None
        )
        # Save self.config

    # --- Device Discovery & Management ---

    async def request_sync(self) -> bool:
        """Request Google Assistant to sync devices for this agent user ID."""
        if not self.access_token or not self.agent_user_id:
            logger.error("Cannot request sync: Missing access token or agent user ID.")
            return False
        logger.info(
            f"Requesting Google Home device sync for agentUserId: {self.agent_user_id}"
        )
        payload = {"agentUserId": self.agent_user_id}
        response_data = await self._send_google_api_request(REQUEST_SYNC_URL, payload)
        if response_data is not None:  # Success is typically 200 OK with empty body
            logger.info("Google Home device sync request sent successfully.")
            # Actual discovery happens via SYNC intent fulfillment by Violt's smart home backend
            return True
        else:
            logger.error("Failed to send Google Home device sync request.")
            return False

    async def discover_devices(
        self, callback: Optional[Callable[[Dict[str, Any]], Coroutine]] = None
    ) -> List[Dict[str, Any]]:
        """
        Discovery for Google Home is typically passive. Violt acts as the fulfillment
        endpoint for Google's SYNC intent. This method could trigger a RequestSync
        and maybe query recently synced devices, but doesn't actively scan network.
        """
        if self.discovery_active:
            return []
        logger.info(
            "Google Home 'discovery' triggered (RequestSync). Actual devices provided via SYNC intent."
        )
        self.discovery_active = True
        await self.request_sync()
        # Optionally, could query devices after a delay, but SYNC fulfillment is the primary source
        # discovered = await self.query_all_devices() # Implement query_all_devices if needed
        self.discovery_active = False
        return []  # Return empty as discovery is passive

    async def add_device(self, device_config: Dict[str, Any]) -> Optional[Device]:
        """
        Adds a device managed by Google Home. Assumes device info came from SYNC intent fulfillment.
        This method primarily registers the device within Violt.
        """
        device_id = device_config.get("id", str(uuid.uuid4()))  # Violt ID
        google_device_id = device_config.get("google_device_id")  # Google's ID

        if not google_device_id:
            raise DeviceIntegrationError(
                "Missing 'google_device_id' for Google Home device."
            )

        async with self.lock:
            existing = next(
                (
                    d
                    for d in self.devices.values()
                    if getattr(d, "google_device_id", None) == google_device_id
                ),
                None,
            )
            if existing:
                logger.warning(
                    f"Google device with ID {google_device_id} already exists ({existing.id}). Updating info."
                )
                # Update existing device info if needed
                existing.name = device_config.get("name", existing.name)
                existing.google_traits = device_config.get(
                    "traits_supported", existing.google_traits
                )
                existing._add_violt_capabilities()  # Re-map capabilities
                await existing.connect()  # Re-verify
                return existing

            # Create device instance
            device = GoogleHomeDevice(
                device_id=str(device_id),
                name=device_config.get("name", f"Google Device {google_device_id[:6]}"),
                device_type=device_config.get("type", "other"),
                manufacturer=device_config.get("manufacturer", "Unknown"),
                model=device_config.get("model"),
                location=device_config.get("location"),
                google_device_id=google_device_id,
                traits_supported=device_config.get("traits_supported", []),
                integration=self,
            )

            # Attempt to connect (verify state query)
            if await device.connect():
                self.devices[device.id] = device
                logger.info(
                    f"Successfully added and verified Google Home device: {device.name} ({device.id})"
                )
                return device
            else:
                raise DeviceIntegrationError(
                    f"Failed to verify/connect to Google device {device.name} ({google_device_id})."
                )

    async def remove_device(self, device_id: str) -> bool:
        """Remove a Google Home device instance."""
        # Removing usually involves telling Google via ReportStateAndNotification (device offline/removed)
        # And potentially triggering RequestSync
        async with self.lock:
            if device_id in self.devices:
                device = self.devices.pop(device_id)
                # Notify Google that the device is gone (optional, depends on fulfillment logic)
                # await self.report_state(...) with offline status?
                await device.disconnect()
                logger.info(f"Removed Google Home device: {device.name} ({device_id})")
                # Maybe trigger RequestSync after removal?
                # asyncio.create_task(self.request_sync())
                return True
            else:
                logger.warning(f"Google Home device not found for removal: {device_id}")
                return False

    # --- HomeGraph API Interaction ---

    async def report_state(self, device_states: List[Dict[str, Any]]):
        """Report device states to Google HomeGraph."""
        if not self.access_token or not self.agent_user_id:
            return False
        logger.debug(
            f"Reporting state for {len(device_states)} devices to Google HomeGraph."
        )
        payload = {
            "agentUserId": self.agent_user_id,
            "requestId": str(uuid.uuid4()),
            "payload": {
                "devices": {
                    "states": {  # Map Violt state to Google state format
                        device["google_device_id"]: device["google_state"]
                        for device in device_states
                        if "google_device_id" in device and "google_state" in device
                    }
                }
            },
        }
        # Add async support if needed (payload.async=True)
        response_data = await self._send_google_api_request(REPORT_STATE_URL, payload)
        # Check response (200 OK with empty body is success)
        return (
            response_data is not None and response_data == {}
        )  # Check for empty dict on success

    async def _send_google_api_request(
        self, url: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send request to Google HomeGraph API."""
        if not self.http_session or not self.access_token:
            logger.error(
                "Cannot send Google API request: Not authenticated or session not ready."
            )
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-GFE-SSL": "yes",  # Often required by HomeGraph
        }
        request_id = payload.get("requestId", str(uuid.uuid4()))  # Ensure request ID
        payload["requestId"] = request_id

        logger.debug(f"Sending Google API Request to {url}: {json.dumps(payload)}")
        try:
            async with self.http_session.post(
                url, json=payload, headers=headers
            ) as response:
                response_text = await response.text()
                logger.debug(
                    f"Google API Response Status: {response.status}, Body: {response_text}"
                )
                if response.status == 200:
                    try:
                        # Handle empty success body for ReportState/RequestSync
                        if not response_text:
                            return {}
                        response_data = json.loads(response_text)
                        # Check for specific error payloads if documented
                        return response_data
                    except json.JSONDecodeError:
                        logger.error(
                            f"Failed to decode Google JSON response: {response_text}"
                        )
                        return None
                elif response.status == 401 or response.status == 403:
                    logger.error(
                        "Google API authentication failed (401/403). Token may be invalid or expired."
                    )
                    self.access_token = None
                    asyncio.create_task(self.refresh_access_token())
                    return None
                else:
                    logger.error(
                        f"Google API request failed: {response.status} - {response_text}"
                    )
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error sending Google API request: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error sending Google API request: {e}", exc_info=True
            )
            return None


# --- Register with Registry ---
from ..registry import registry

registry.register_integration_class(GoogleHomeIntegration)
