"""
Violt Core Lite - API Router for Integrations

This module handles integration API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
import logging

from ...core.schemas import IntegrationInfo, IntegrationSetup, DiscoveredBleDevice, BLEService, BLECharacteristic
from ...core.auth import get_current_active_user
from ...database.session import get_db
from ...database.models import User, Device, Event
from ...core.config import settings
from ...devices.registry import registry as integration_registry

# from devices.bleak.integration import BleakIntegration  # Commented out: bleak integration module not found

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[IntegrationInfo])
async def list_integrations(current_user: User = Depends(get_current_active_user)):
    """List all available integrations."""
    # TODO: In step 004, this will be replaced with dynamic integration discovery
    # For now, we'll return a static list of supported integrations

    integrations = [
        {
            "type": "xiaomi",
            "name": "Xiaomi Mi Home",
            "description": "Integration with Xiaomi Mi Home devices",
            "enabled": settings.XIAOMI_INTEGRATION_ENABLED,
            "device_types": ["light", "switch", "sensor", "vacuum"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "ip_address": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["ip_address", "token"],
            },
        },
        {
            "type": "alexa",
            "name": "Amazon Alexa",
            "description": "Integration with Amazon Alexa voice assistant",
            "enabled": settings.ALEXA_INTEGRATION_ENABLED,
            "device_types": ["all"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string"},
                    "client_secret": {"type": "string"},
                    "redirect_uri": {"type": "string"},
                },
                "required": ["client_id", "client_secret", "redirect_uri"],
            },
        },
        {
            "type": "google_home",
            "name": "Google Home",
            "description": "Integration with Google Home voice assistant",
            "enabled": settings.GOOGLE_HOME_INTEGRATION_ENABLED,
            "device_types": ["all"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "client_id": {"type": "string"},
                    "client_secret": {"type": "string"},
                },
                "required": ["project_id", "client_id", "client_secret"],
            },
        },
    ]

    return integrations


@router.get("/{integration_type}", response_model=IntegrationInfo)
async def get_integration(
    integration_type: str, current_user: User = Depends(get_current_active_user)
):
    """Get integration details."""
    integration = await get_integration_by_type(integration_type)
    return integration


@router.post("/{integration_type}/setup", status_code=status.HTTP_202_ACCEPTED)
async def setup_integration(
    integration_type: str,
    setup_data: IntegrationSetup,
    current_user: User = Depends(get_current_active_user),
):
    """Setup integration."""
    # Verify integration exists
    integration = await get_integration_by_type(integration_type)

    # TODO: In step 004, this will be replaced with actual integration setup logic
    # For now, we'll just return a placeholder response

    logger.info(f"Integration setup requested: {integration_type}")

    return {
        "message": f"{integration['name']} setup initiated",
        "status": "pending",
        "task_id": f"setup_task_{integration_type}",
    }


@router.delete("/{integration_type}", status_code=status.HTTP_202_ACCEPTED)
async def remove_integration(
    integration_type: str, current_user: User = Depends(get_current_active_user)
):
    """Remove integration."""
    # Verify integration exists
    integration = await get_integration_by_type(integration_type)

    # TODO: In step 004, this will be replaced with actual integration removal logic
    # For now, we'll just return a placeholder response

    logger.info(f"Integration removal requested: {integration_type}")

    return {
        "message": f"{integration['name']} removal initiated",
        "status": "pending",
        "task_id": f"remove_task_{integration_type}",
    }


@router.get("/{integration_type}/devices", response_model=List[Dict[str, Any]])
async def list_integration_devices(
    integration_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List devices for integration."""
    # Verify integration exists
    integration = await get_integration_by_type(integration_type)

    # Get devices for this integration
    result = await db.execute(
        select(Device).where(
            Device.user_id == current_user.id,
            Device.integration_type == integration_type,
        )
    )
    devices = result.scalars().all()

    # Format devices for response
    device_list = []
    for device in devices:
        device_list.append(
            {
                "id": device.id,
                "name": device.name,
                "type": device.type,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "status": device.status,
            }
        )

    return device_list


@router.post("/{integration_type}/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_integration_devices(
    integration_type: str, current_user: User = Depends(get_current_active_user)
):
    """Sync devices with integration."""
    # Verify integration exists
    integration = await get_integration_by_type(integration_type)

    # TODO: In step 004, this will be replaced with actual device sync logic
    # For now, we'll just return a placeholder response

    logger.info(f"Integration device sync requested: {integration_type}")

    return {
        "message": f"{integration['name']} device sync initiated",
        "status": "pending",
        "task_id": f"sync_task_{integration_type}",
    }


@router.get("/ble/discover", response_model=List[DiscoveredBleDevice])
async def discover_ble_devices(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    timeout: int = 10,  # Default scan timeout
):
    """Scan for nearby BLE devices."""
    integration = integration_registry.get_integration("bleak")
    if not integration or not isinstance(integration, BleakIntegration):
        logger.error("BLE (Bleak) integration not found or not running.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BLE integration is not available.",
        )

    try:
        logger.info(f"Starting BLE discovery for {timeout} seconds...")
        discovered_devices = await integration.discover_devices(scan_duration=timeout)
        logger.info(f"BLE discovery finished. Found {len(discovered_devices)} devices.")

        # Optionally record telemetry
        telemetry_service = request.app.state.telemetry_service
        if telemetry_service:
            await telemetry_service.record_event(
                event_type="ble_discovery",
                payload={"duration": timeout, "devices_found": len(discovered_devices)},
                user_id=current_user.id,
            )

        # Convert Bleak device objects to Pydantic models for response
        response_devices = [
            DiscoveredBleDevice(
                name=dev.name,
                address=dev.address,
                rssi=dev.rssi,
                metadata=dev.metadata,
            )
            for dev in discovered_devices
        ]
        return response_devices

    except Exception as e:
        logger.error(f"Error during BLE discovery: {e}", exc_info=True)
        # Optionally record telemetry for failure
        telemetry_service = request.app.state.telemetry_service
        if telemetry_service:
            await telemetry_service.record_event(
                event_type="ble_discovery",
                payload={"duration": timeout, "success": False, "error": str(e)},
                user_id=current_user.id,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform BLE discovery: {e}",
        )


@router.post("/ble/{device_address}/connect", status_code=status.HTTP_202_ACCEPTED)
async def connect_ble_device(
    device_address: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """Connect to a BLE device."""
    integration = integration_registry.get_integration("bleak")
    if not integration or not isinstance(integration, BleakIntegration):
        logger.error("BLE (Bleak) integration not found or not running.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BLE integration is not available.",
        )

    try:
        logger.info(f"Attempting to connect to BLE device {device_address}")
        connection = await integration.connect_to_device(device_address)

        return {
            "message": f"Connected to BLE device {device_address}",
            "status": "connected",
            "device_address": device_address,
        }

    except Exception as e:
        logger.error(f"Error connecting to BLE device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to BLE device: {e}",
        )


@router.post("/ble/{device_address}/disconnect", status_code=status.HTTP_202_ACCEPTED)
async def disconnect_ble_device(
    device_address: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """Disconnect from a BLE device."""
    integration = integration_registry.get_integration("bleak")
    if not integration or not isinstance(integration, BleakIntegration):
        logger.error("BLE (Bleak) integration not found or not running.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BLE integration is not available.",
        )

    try:
        logger.info(f"Attempting to disconnect from BLE device {device_address}")
        success = await integration.disconnect_device(device_address)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_address} not found or already disconnected",
            )

        return {
            "message": f"Disconnected from BLE device {device_address}",
            "status": "disconnected",
            "device_address": device_address,
        }

    except Exception as e:
        logger.error(f"Error disconnecting from BLE device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect from BLE device: {e}",
        )


@router.get("/ble/{device_address}/services", response_model=List[BLEService])
async def get_ble_services(
    device_address: str, current_user: User = Depends(get_current_active_user)
):
    """List all services for a BLE device"""
    integration = integration_registry.get_integration("bleak")
    if not integration:
        raise HTTPException(status_code=404, detail="BLE integration not available")

    try:
        services = await integration.get_services(device_address)
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ble/{device_address}/characteristics", response_model=List[BLECharacteristic]
)
async def get_ble_characteristics(
    device_address: str,
    service_uuid: str,
    current_user: User = Depends(get_current_active_user),
):
    """List characteristics for a BLE service"""
    integration = integration_registry.get_integration("bleak")
    if not integration:
        raise HTTPException(status_code=404, detail="BLE integration not available")

    try:
        characteristics = await integration.get_characteristics(
            device_address, service_uuid
        )
        return characteristics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ble/{device_address}/read")
async def read_ble_characteristic(
    device_address: str,
    characteristic_uuid: str,
    current_user: User = Depends(get_current_active_user),
):
    """Read a BLE characteristic"""
    integration = integration_registry.get_integration("bleak")
    if not integration:
        raise HTTPException(status_code=404, detail="BLE integration not available")

    try:
        value = await integration.read_characteristic(
            device_address, characteristic_uuid
        )
        return {"value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ble/{device_address}/subscribe")
async def subscribe_to_characteristic(
    device_address: str,
    characteristic_uuid: str,
    current_user: User = Depends(get_current_active_user),
):
    """Subscribe to BLE characteristic notifications"""
    integration = integration_registry.get_integration("bleak")
    if not integration:
        raise HTTPException(status_code=404, detail="BLE integration not available")

    try:
        await integration.subscribe_to_characteristic(
            device_address, characteristic_uuid
        )
        return {"status": "subscribed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def get_integration_by_type(integration_type: str) -> dict:
    """Get integration by type."""
    # TODO: In step 004, this will be replaced with dynamic integration lookup
    # For now, we'll use a static mapping

    integrations = {
        "xiaomi": {
            "type": "xiaomi",
            "name": "Xiaomi Mi Home",
            "description": "Integration with Xiaomi Mi Home devices",
            "enabled": settings.XIAOMI_INTEGRATION_ENABLED,
            "device_types": ["light", "switch", "sensor", "vacuum"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "ip_address": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["ip_address", "token"],
            },
        },
        "alexa": {
            "type": "alexa",
            "name": "Amazon Alexa",
            "description": "Integration with Amazon Alexa voice assistant",
            "enabled": settings.ALEXA_INTEGRATION_ENABLED,
            "device_types": ["all"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string"},
                    "client_secret": {"type": "string"},
                    "redirect_uri": {"type": "string"},
                },
                "required": ["client_id", "client_secret", "redirect_uri"],
            },
        },
        "google_home": {
            "type": "google_home",
            "name": "Google Home",
            "description": "Integration with Google Home voice assistant",
            "enabled": settings.GOOGLE_HOME_INTEGRATION_ENABLED,
            "device_types": ["all"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "client_id": {"type": "string"},
                    "client_secret": {"type": "string"},
                },
                "required": ["project_id", "client_id", "client_secret"],
            },
        },
    }

    if integration_type not in integrations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found"
        )

    return integrations[integration_type]
