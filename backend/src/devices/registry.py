"""
Violt Core Lite - Device Integration Registry

This module manages device integration plugins and provides a registry for them.
"""

from typing import Dict, List, Any, Optional, Type
import logging
import importlib
import os
import yaml
import json
from pathlib import Path

from .base import DeviceIntegration, Device, DeviceIntegrationError
from ..core.config import settings, DEFAULT_CONFIG_DIR

logger = logging.getLogger(__name__)

logger.info("Registry module imported and top-level code executed.")


class IntegrationRegistry:
    """Registry for device integrations."""

    def __init__(self):
        self.integrations: Dict[str, DeviceIntegration] = {}
        self.integration_classes: Dict[str, Type[DeviceIntegration]] = {}

    def register_integration_class(
        self, integration_class: Type[DeviceIntegration]
    ) -> None:
        """Register an integration class."""
        integration_type = getattr(integration_class, "integration_type", None)
        logger.info(
            f"Attempting to register integration class: {integration_class} (type={integration_type})"
        )
        if not integration_type:
            logger.error(
                f"Integration class {integration_class} missing 'integration_type' attribute!"
            )
            return
        self.integration_classes[integration_type] = integration_class
        logger.info(
            f"Registered integration class: {integration_type}. Current keys: {list(self.integration_classes.keys())}"
        )

    async def setup_integration(
        self, integration_type: str, config: Dict[str, Any]
    ) -> Optional[DeviceIntegration]:
        """Set up an integration with configuration."""
        if integration_type not in self.integration_classes:
            logger.error(f"Integration type not found: {integration_type}")
            return None

        # Create integration instance
        integration_class = self.integration_classes[integration_type]
        integration = integration_class(config)

        # Set up integration
        try:
            success = await integration.setup(config)
            if not success:
                logger.error(f"Failed to set up integration: {integration_type}")
                return None

            # Store integration
            self.integrations[integration_type] = integration
            logger.info(f"Integration set up successfully: {integration_type}")
            return integration

        except Exception as e:
            logger.error(f"Error setting up integration {integration_type}: {e}")
            return None

    def get_integration(self, integration_type: str) -> Optional[DeviceIntegration]:
        """Get an integration by type."""
        return self.integrations.get(integration_type)

    def get_integrations(self) -> List[DeviceIntegration]:
        """Get all integrations."""
        return list(self.integrations.values())

    def get_integration_types(self) -> List[str]:
        """Get all registered integration types."""
        return list(self.integration_classes.keys())

    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID from any integration."""
        for integration in self.integrations.values():
            device = integration.get_device(device_id)
            if device:
                return device
        return None

    def get_devices(self) -> List[Device]:
        """Get all devices from all integrations."""
        devices = []
        for integration in self.integrations.values():
            devices.extend(integration.get_devices())
        return devices

    async def discover_devices(
        self, integration_type: Optional[str] = None
    ) -> Dict[str, List[Device]]:
        """Discover devices for specified integration or all integrations."""
        discovered_devices = {}

        if integration_type:
            # Discover for specific integration
            integration = self.get_integration(integration_type)
            if integration:
                try:
                    devices = await integration.discover_devices()
                    discovered_devices[integration_type] = devices
                except Exception as e:
                    logger.error(
                        f"Error discovering devices for {integration_type}: {e}"
                    )
        else:
            # Discover for all integrations
            for integration_type, integration in self.integrations.items():
                try:
                    devices = await integration.discover_devices()
                    discovered_devices[integration_type] = devices
                except Exception as e:
                    logger.error(
                        f"Error discovering devices for {integration_type}: {e}"
                    )

        return discovered_devices

    async def load_integrations_from_config(self, config_dir: str) -> None:
        """Load integrations from configuration directory."""
        # Convert to Path object for cross-platform compatibility
        config_path = Path(config_dir)

        # If path is relative, use the default config directory
        if not config_path.is_absolute():
            config_path = DEFAULT_CONFIG_DIR / config_path

        if not config_path.exists():
            logger.warning(f"Integration config directory not found: {config_path}")
            # Try to create the directory
            try:
                os.makedirs(config_path, exist_ok=True)
                logger.info(f"Created integration config directory: {config_path}")
            except Exception as e:
                logger.error(f"Failed to create integration config directory: {e}")
            return

        # Load all YAML and JSON files in the directory
        yaml_files = list(config_path.glob("*.yaml")) + list(config_path.glob("*.yml"))
        for file_path in yaml_files:
            await self._load_integration_from_file(file_path)

        json_files = list(config_path.glob("*.json"))
        for file_path in json_files:
            await self._load_integration_from_file(file_path)

        logger.info(
            f"Loaded {len(yaml_files) + len(json_files)} integration configuration files from {config_path}"
        )

    async def _load_integration_from_file(self, file_path: Path) -> None:
        """Load an integration from a configuration file."""
        try:
            # Load configuration from file
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() in [".yaml", ".yml"]:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)

            if not config:
                logger.warning(f"Empty configuration file: {file_path}")
                return

            # Get integration type
            integration_type = config.get("type")
            if not integration_type:
                logger.warning(f"Integration type not specified in {file_path}")
                return

            # Set up integration
            await self.setup_integration(integration_type, config)

        except Exception as e:
            logger.error(f"Error loading integration from {file_path}: {e}")


def load_integration_modules():
    # logger.info("Calling load_integration_modules() 3")
    """Load all integration modules."""
    # Get the directory of this file using pathlib for cross-platform compatibility
    current_dir = Path(__file__).parent.absolute()

    # Log the directory we're searching for modules
    logger.info(f"Subdirectories found: {os.listdir(current_dir)}")

    # Get all subdirectories (potential integration modules)
    for item in os.listdir(current_dir):
        item_path = current_dir / item
        logger.info(f"Inspecting item: {item} (is_dir={item_path.is_dir()})")
        if item_path.is_dir() and not item.startswith("__"):
            try:
                # Try to import the module
                module_name = f".{item}"
                logger.info(f"Attempting to import integration module: {module_name}")
                importlib.import_module(module_name, package="src.devices")
                logger.info(f"Loaded integration module: {item}")
            except ImportError as e:
                logger.error(f"Failed to import integration module '{item}': {e}")
                logger.error(f"Error importing integration module {item}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading module {item}: {e}")


# Create global registry instance
registry = IntegrationRegistry()
integration_registry = registry

logger.info("Calling load_integration_modules() 2")

load_integration_modules()
