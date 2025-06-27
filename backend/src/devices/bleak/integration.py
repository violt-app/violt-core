"""
Generic BLE integration base class for Violt using bleak.
"""
import logging
from bleak import BleakScanner, BleakClient
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class BleakIntegration:
    integration_type = "bleak"
    name = "Generic BLE"
    description = "Generic Bluetooth Low Energy integration via bleak."
    supported_device_types = ["sensor", "switch", "light", "other"]
    known_manufacturers = ["Generic", "Xiaomi", "Other BLE"]
    def __init__(self):
        self.devices = {}

    async def discover_devices(self) -> List[Dict[str, Any]]:
        """Scan for BLE devices. Returns a list of dicts with address, name, rssi, etc."""
        logger.info("Scanning for BLE devices...")
        devices = await BleakScanner.discover()
        return [
            {
                "address": d.address,
                "name": d.name,
                "rssi": d.rssi,
                "details": d.details,
            }
            for d in devices
        ]

    async def add_device(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Add a BLE device by address. Override in subclass for device-specific logic."""
        address = device_info.get("address")
        if not address:
            raise ValueError("Device address required")
        logger.info(f"Adding BLE device: {address}")
        self.devices[address] = device_info
        return device_info

    async def remove_device(self, address: str) -> bool:
        if address in self.devices:
            logger.info(f"Removing BLE device: {address}")
            self.devices.pop(address)
            return True
        logger.warning(f"BLE device not found for removal: {address}")
        return False

__all__ = ["BleakIntegration"]
