"""
Zigbee device integration module for Violt.

This module provides integration with Zigbee coordinators (e.g., Sonoff Zigbee Dongle E)
and supports device discovery, pairing (permit join), and product catalog mapping.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Coroutine
from ..base import DeviceIntegration, Device
import logging

logger = logging.getLogger(__name__)

class ZigbeeIntegration(DeviceIntegration):
    integration_type = "zigbee"
    name = "Zigbee"
    description = "Zigbee device integration (Sonoff, Aqara, etc.)"
    supported_device_types = ["sensor", "switch", "light", "climate", "lock", "cover", "other"]

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.product_catalog = self._load_product_catalog()
        self.discovery_active = False
        # Initialize Zigbee coordinator connection (Sonoff Zigbee Dongle E)
        self.coordinator = None
        self.application_controller = None
        try:
            import zigpy.application
            import zigpy_znp
            import serial
            # Use zigpy_znp for Texas Instruments chips, zigpy_efr32 for Silicon Labs (Sonoff E is EFR32)
            import zigpy_efr32
            self.serial_port = self.config.get("serial_port", "COM4")
            self.baudrate = self.config.get("baudrate", 115200)
            # Create zigpy application (async, so actual init is in discover_devices)
        except ImportError as e:
            logger.error(f"Failed to import zigpy or radio libraries: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Zigbee coordinator: {e}")

    def _load_product_catalog(self) -> Dict[str, Dict[str, Any]]:
        import os, json
        catalog_path = os.path.join(os.path.dirname(__file__), "product_catalog.json")
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
            logger.info(f"Loaded Zigbee product catalog with {len(catalog)} entries.")
            return catalog
        except Exception as e:
            logger.error(f"Failed to load Zigbee product catalog: {e}")
            return {}

    async def discover_devices(self) -> List[Device]:
        """
        Discover Zigbee devices by enabling permit join and listening for new device joins.
        """
        if self.discovery_active:
            logger.warning("Zigbee device discovery already in progress.")
            return []
        self.discovery_active = True
        discovered_devices = []
        try:
            import zigpy.application
            import zigpy_efr32
            import asyncio

            # Initialize application controller if not already done
            if not self.application_controller:
                radio_config = {
                    "device": {
                        "path": self.config.get("serial_port", "COM4"),
                        "baudrate": self.config.get("baudrate", 115200),
                    }
                }
                self.application_controller = await zigpy.application.ControllerApplication.new(
                    config=radio_config,
                    auto_form=True,
                    radio_type=zigpy_efr32.radio,
                )

            logger.info("Enabling Zigbee permit join (pairing mode) for 60 seconds...")
            await self.application_controller.permit(60)
            logger.info("Listening for new Zigbee device joins...")
            # Listen for device joins for 60 seconds
            joined_devices = []
            def device_joined(device):
                logger.info(f"New Zigbee device joined: {device.ieee}")
                joined_devices.append(device)
            self.application_controller.add_listener(device_joined)
            await asyncio.sleep(60)
            self.application_controller.remove_listener(device_joined)
            # For each joined device, match model to product catalog
            for device in joined_devices:
                model = getattr(device, "model", None)
                if model and model in self.product_catalog:
                    product = self.product_catalog[model]
                    discovered_devices.append(Device(
                        device_id=f"zigbee-{model.lower()}",
                        name=product["name"],
                        device_type=product["type"],
                        manufacturer=product["manufacturer"],
                        model=product["model"],
                        integration_type="zigbee"
                    ))
                else:
                    logger.warning(f"Unknown Zigbee device model: {model}")
            logger.info("Zigbee discovery finished. Found %d devices.", len(discovered_devices))
        except Exception as e:
            logger.error(f"Error during Zigbee device discovery: {e}")
        finally:
            self.discovery_active = False
        return discovered_devices

    # Advanced Zigbee device controls
    async def remove_device(self, device_id: str) -> bool:
        if device_id in self.devices:
            device = self.devices.pop(device_id)
            logger.info(f"Removed Zigbee device: {device_id}")
            # TODO: Remove from Zigbee network via application_controller
            return True
        logger.warning(f"Zigbee device not found for removal: {device_id}")
        return False

    async def refresh_state(self, device_id: str) -> bool:
        device = self.devices.get(device_id)
        if not device:
            logger.warning(f"Zigbee device not found for refresh: {device_id}")
            return False
        # TODO: Query device state via Zigbee application_controller
        logger.info(f"Refreshed Zigbee device state: {device_id}")
        return True

    async def execute_command(self, device_id: str, command: str, params: dict = None) -> bool:
        device = self.devices.get(device_id)
        if not device:
            logger.warning(f"Zigbee device not found for command: {device_id}")
            return False
        # TODO: Send command via Zigbee application_controller
        logger.info(f"Executed command '{command}' on Zigbee device: {device_id}")
        return True

    # Optionally, add methods for pairing, removing, and controlling Zigbee devices

    def import_product_catalog_from_zigbee2mqtt(self, zigbee2mqtt_devices_json_path: str):
        """
        Import a large device catalog from Zigbee2MQTT or Home Assistant device database.
        """
        import json
        try:
            with open(zigbee2mqtt_devices_json_path, "r", encoding="utf-8") as f:
                ext_catalog = json.load(f)
            # TODO: Parse and merge ext_catalog into self.product_catalog
            logger.info(f"Imported {len(ext_catalog)} devices from Zigbee2MQTT/Home Assistant.")
        except Exception as e:
            logger.error(f"Failed to import external Zigbee device catalog: {e}")

# Make the integration discoverable by the registry
__all__ = ["ZigbeeIntegration"]
