# backend/src/api/devices/router.py

"""
Violt Core Lite - API Router for Devices

This module handles device API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete as sql_delete
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime
import asyncio

from ...core.schemas import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceState as DeviceStateSchema,
)
from ...core.auth import get_current_active_user
from ...database.session import get_db
from ...database.models import Device, User, Event

# Placeholder for device integration registry and control functions
# These would be properly imported from device/integration modules in a full implementation
from ...devices.registry import registry as device_registry
from ...devices.base import Device as IntegrationDevice, DeviceIntegrationError
from ...core.websocket import manager as websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# Helper function (consider moving to a crud utility module)
async def get_device_by_id(db: AsyncSession, device_id: str, user_id: str) -> Device:
    """Get a device by ID and verify ownership."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.user_id == user_id)
    )
    device = result.scalars().first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    return device


async def log_event(
    db: AsyncSession,
    event_type: str,
    source: str,
    data: Dict[str, Any],
    device_id: Optional[str] = None,
):
    """Helper to create and log an event."""
    event = Event(type=event_type, source=source, data=data, device_id=device_id)
    db.add(event)
    try:
        await db.commit()
        # Optionally notify via websockets here if needed for events
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to log event {event_type}: {e}")


@router.get("/all", response_model=List[DeviceResponse])
async def list_devices(
    location: Optional[str] = None,
    type: Optional[str] = None,
    manufacturer: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all devices for the current user with optional filtering."""
    query = select(Device).where(Device.user_id == current_user.id)

    # Apply filters if provided
    if location:
        query = query.where(
            Device.location.ilike(f"%{location}%")
        )  # Use ilike for case-insensitive matching
    if type:
        query = query.where(Device.type == type)
    if manufacturer:
        query = query.where(Device.manufacturer == manufacturer)
    if status:
        query = query.where(Device.status == status)

    result = await db.execute(query.order_by(Device.name))  # Order by name
    devices = result.scalars().all()

    return devices


@router.post("/create", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new device manually.
    Requires device details including integration type and necessary config.
    """
    # Check if integration type exists (basic check)
    integration = device_registry.get_integration(device_data.integration_type)
    if not integration:
        # Attempt to load the integration if not already loaded - needed if config is dynamic
        await device_registry.load_integrations_from_config(
            "config/integrations"
        )  # Assuming config path
        integration = device_registry.get_integration(device_data.integration_type)
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integration type '{device_data.integration_type}' not supported or configured.",
            )

    # Basic validation based on integration type (example)
    if device_data.integration_type == "xiaomi" and not (
        device_data.ip_address
        and device_data.config
        and device_data.config.get("token")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Xiaomi devices require ip_address and token in config.",
        )
    # Add similar checks for other integrations as needed

    # Create new device model instance
    new_device_db = Device(
        id=str(uuid.uuid4()),  # Ensure ID is generated
        user_id=current_user.id,
        name=device_data.name,
        type=device_data.type,
        manufacturer=device_data.manufacturer,
        model=device_data.model,
        location=device_data.location,
        ip_address=device_data.ip_address,
        mac_address=device_data.mac_address,
        integration_type=device_data.integration_type,
        config=device_data.config,
        properties={},  # Initialize properties
        state={},  # Initialize state
        status="offline",  # Initial status
    )

    db.add(new_device_db)

    # Attempt to add/connect via the integration module
    try:
        # The integration's add_device should handle connection and initial state
        integration_device: Optional[IntegrationDevice] = await integration.add_device(
            {
                **device_data.model_dump(),
                "id": new_device_db.id,  # Pass the generated ID
            }
        )
        if not integration_device:
            # Rollback database change if integration add fails
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add device to integration.",
            )
        # Update DB record with initial state/status from integration
        new_device_db.status = integration_device.status
        new_device_db.state = integration_device.state.to_dict()
        new_device_db.properties = integration_device.properties

    except DeviceIntegrationError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Integration error: {e}"
        )
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Unexpected error adding device to integration: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while adding the device.",
        )

    # Commit device to DB
    try:
        await db.commit()
        await db.refresh(new_device_db)
    except Exception as e:
        await db.rollback()  # Rollback if commit fails
        logger.error(f"Database error creating device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save device to database.",
        )

    # Log event
    await log_event(
        db,
        event_type="device_added",
        source="api",
        data={"device_id": new_device_db.id, "device_name": new_device_db.name},
        device_id=new_device_db.id,
    )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {
            "type": "device_added",
            "device": DeviceResponse.model_validate(new_device_db).model_dump(),
        },
        current_user.id,
        "devices",
    )

    logger.info(f"Device created: {new_device_db.id} - {new_device_db.name}")
    return new_device_db


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get device details by ID."""
    device = await get_device_by_id(db, device_id, current_user.id)
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update device information (name, location, config)."""
    device_db = await get_device_by_id(db, device_id, current_user.id)
    update_occurred = False

    # Update specific fields if provided in the request
    update_data = device_data.model_dump(exclude_unset=True)  # Get only provided fields

    if "name" in update_data and device_db.name != update_data["name"]:
        device_db.name = update_data["name"]
        update_occurred = True
    if "location" in update_data and device_db.location != update_data["location"]:
        device_db.location = update_data["location"]
        update_occurred = True
    if "config" in update_data and device_db.config != update_data["config"]:
        device_db.config = update_data["config"]
        # Potentially need to re-initialize/update the device in the integration
        integration = device_registry.get_integration(device_db.integration_type)
        if integration:
            try:
                # Assuming integration has an update_device_config method or similar
                # This part is highly dependent on the integration's design
                logger.info(
                    f"Updating config for device {device_id} in integration {device_db.integration_type}"
                )
                # await integration.update_device_config(device_id, update_data["config"])
            except Exception as e:
                logger.error(f"Failed to update device config in integration: {e}")
                # Decide if this should be a fatal error or just a warning
        update_occurred = True

    if update_occurred:
        from datetime import timezone
        device_db.last_updated = datetime.now(timezone.utc)  # Update timestamp explicitly
        try:
            await db.commit()
            await db.refresh(device_db)
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Database error updating device {device_id}: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update device in database.",
            )

        # Log event
        await log_event(
            db,
            event_type="device_updated",
            source="api",
            data={
                "device_id": device_db.id,
                "device_name": device_db.name,
                "updated_fields": list(update_data.keys()),
            },
            device_id=device_db.id,
        )

        # Send WebSocket update
        await websocket_manager.send_personal_message(
            {
                "type": "device_updated",
                "device": DeviceResponse.model_validate(device_db).model_dump(),
            },
            current_user.id,
            "devices",
        )
        logger.info(f"Device updated: {device_db.id} - {device_db.name}")
    else:
        logger.info(f"No changes detected for device update: {device_id}")

    return device_db


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a device."""
    device = await get_device_by_id(db, device_id, current_user.id)
    device_name = device.name  # Store name before potential deletion issues
    integration_type = device.integration_type

    # Remove from integration first
    integration = device_registry.get_integration(integration_type)
    if integration:
        try:
            removed_from_integration = await integration.remove_device(device_id)
            if not removed_from_integration:
                logger.warning(
                    f"Could not remove device {device_id} from integration {integration_type}, proceeding with DB deletion."
                )
        except Exception as e:
            logger.error(
                f"Error removing device {device_id} from integration {integration_type}: {e}",
                exc_info=True,
            )
            # Decide if this should prevent DB deletion

    # Log event before deleting from DB
    await log_event(
        db,
        event_type="device_deleted",
        source="api",
        data={"device_id": device_id, "device_name": device_name},
        device_id=device_id,
    )

    # Delete the device from DB
    try:
        # Manually delete related events if cascade isn't working as expected or not set
        await db.execute(sql_delete(Event).where(Event.device_id == device_id))
        await db.delete(device)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error deleting device {device_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device from database.",
        )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {"type": "device_removed", "device_id": device_id}, current_user.id, "devices"
    )

    logger.info(f"Device deleted: {device_id}")
    # No return needed for 204


@router.get("/{device_id}/state", response_model=DeviceStateSchema)
async def get_device_state(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get the current cached state of a device."""
    device = await get_device_by_id(db, device_id, current_user.id)

    # Optionally, trigger a state refresh from the integration if state is old
    # Needs careful consideration regarding timing and API rate limits
    # Example:
    # if datetime.utcnow() - device.last_updated > timedelta(minutes=5):
    #    integration = device_registry.get_integration(device.integration_type)
    #    if integration:
    #        integration_device = integration.get_device(device_id)
    #        if integration_device:
    #            await integration_device.refresh_state()
    #            # Re-fetch from DB to get updated state (or update device object directly)
    #            device = await get_device_by_id(db, device_id, current_user.id)

    return DeviceStateSchema(state=device.state or {})


@router.put("/{device_id}/state", response_model=DeviceStateSchema)
async def update_device_state(
    device_id: str,
    state_data: DeviceStateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update device state (control device).
    This endpoint should ideally send commands via the integration,
    and the state update should come via a refresh or event from the device/integration.
    Directly setting state here might lead to inconsistencies if the command fails.
    A better approach might be a /command endpoint. Let's implement that instead.
    This endpoint is kept for potential manual overrides or simple state setting.
    """
    device_db = await get_device_by_id(db, device_id, current_user.id)

    # Directly update state in DB - USE WITH CAUTION
    new_state = state_data.state
    device_db.state = new_state
    from datetime import timezone
    device_db.last_updated = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(device_db)
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Database error updating device state {device_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device state in database.",
        )

    # Log event
    await log_event(
        db,
        event_type="device_state_changed",
        source="api_manual",  # Indicate manual override
        data={
            "device_id": device_db.id,
            "device_name": device_db.name,
            "state": new_state,
        },
        device_id=device_db.id,
    )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {"type": "device_state_changed", "device_id": device_id, "state": new_state},
        current_user.id,
        "devices",
    )

    logger.info(f"Device state manually updated: {device_db.id} - {device_db.name}")
    return DeviceStateSchema(state=device_db.state)


@router.post("/{device_id}/command", response_model=Dict[str, Any])
async def execute_device_command(
    device_id: str,
    command_data: Dict[str, Any] = Body(
        ...,
        example={"command": "turn_on", "params": {"brightness": 80}},
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Execute a command on a device via its integration."""
    device_db = await get_device_by_id(db, device_id, current_user.id)
    command = command_data.get("command")
    params = command_data.get("params", {})

    if not command:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Command name is required."
        )

    integration = device_registry.get_integration(device_db.integration_type)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Integration '{device_db.integration_type}' not loaded or supported.",
        )

    integration_device = integration.get_device(device_id)
    if not integration_device:
        # This case might happen if the integration lost connection or wasn't fully initialized
        logger.error(
            f"Device {device_id} found in DB but not in integration {integration.integration_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Device not available in the integration.",
        )

    try:
        success = await integration_device.execute_command(command, params)
        if success:
            logger.info(
                f"Command '{command}' executed successfully on device {device_id}"
            )

            # Log event (optional, command execution itself might trigger state change event)
            await log_event(
                db,
                event_type="device_command_sent",
                source="api",
                data={
                    "device_id": device_id,
                    "command": command,
                    "params": params,
                    "success": True,
                },
                device_id=device_id,
            )

            # Optionally trigger a state refresh after a short delay
            asyncio.create_task(asyncio.sleep(2), integration_device.refresh_state())

            return {"status": "success", "message": f"Command '{command}' sent."}
        else:
            logger.warning(f"Command '{command}' failed for device {device_id}")
            await log_event(
                db,
                event_type="device_command_failed",
                source="integration",
                data={"device_id": device_id, "command": command, "params": params},
                device_id=device_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute command '{command}'.",
            )
    except DeviceIntegrationError as e:
        logger.error(
            f"Integration error executing command '{command}' on device {device_id}: {e}",
            exc_info=True,
        )
        await log_event(
            db,
            event_type="device_command_failed",
            source="integration",
            data={
                "device_id": device_id,
                "command": command,
                "params": params,
                "error": str(e),
            },
            device_id=device_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integration error: {e}",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error executing command '{command}' on device {device_id}: {e}",
            exc_info=True,
        )
        await log_event(
            db,
            event_type="device_command_failed",
            source="system",
            data={
                "device_id": device_id,
                "command": command,
                "params": params,
                "error": "Unexpected error",
            },
            device_id=device_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post("/discover", status_code=status.HTTP_202_ACCEPTED)
async def discover_devices(
    integration_type: Optional[str] = Query(
        None, description="Limit discovery to a specific integration type"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger device discovery across specified or all integrations.
    Returns discovered devices that are *not* already added.
    """
    logger.info(
        f"Device discovery requested by user {current_user.id}, integration: {integration_type or 'all'}"
    )

    # This should ideally run as a background task
    # For simplicity here, we run it directly but this might block
    try:
        discovered_integration_devices = await device_registry.discover_devices(
            integration_type
        )

        # Filter out devices already added by the user
        result = await db.execute(
            select(Device.config, Device.integration_type).where(
                Device.user_id == current_user.id
            )
        )
        existing_devices_identifiers = set()
        for config, int_type in result.fetchall():
            # Create a unique identifier based on config (e.g., ip+token for xiaomi, endpoint_id for alexa/google)
            if int_type == "xiaomi" and config and config.get("ip_address"):
                existing_devices_identifiers.add(f"xiaomi_{config.get('ip_address')}")
            elif (
                int_type in ["alexa", "google_home"]
                and config
                and config.get("endpoint_id")
            ):  # Assuming endpoint_id is stored in config
                existing_devices_identifiers.add(
                    f"{int_type}_{config.get('endpoint_id')}"
                )
            # Add other identifiers as needed

        newly_discovered = []
        for int_type, devices in discovered_integration_devices.items():
            for device in devices:
                identifier = None
                if int_type == "xiaomi" and device.ip_address:
                    identifier = f"xiaomi_{device.ip_address}"
                elif (
                    int_type == "alexa"
                    and hasattr(device, "endpoint_id")
                    and device.endpoint_id
                ):
                    identifier = f"alexa_{device.endpoint_id}"
                elif (
                    int_type == "google_home"
                    and hasattr(device, "device_identifier")
                    and device.device_identifier
                ):
                    identifier = f"google_home_{device.device_identifier}"

                if identifier and identifier not in existing_devices_identifiers:
                    # Convert integration device object to a serializable format
                    # Exclude sensitive info like tokens unless explicitly needed for adding
                    newly_discovered.append(
                        {
                            "name": device.name,
                            "type": device.type,
                            "manufacturer": device.manufacturer,
                            "model": device.model,
                            "integration_type": device.integration_type,
                            "ip_address": getattr(device, "ip_address", None),
                            "mac_address": getattr(device, "mac_address", None),
                            # Include minimal config needed to add the device, *excluding tokens*
                            "config_suggestion": {
                                "ip_address": getattr(device, "ip_address", None)
                                # Add other relevant non-sensitive config suggestions
                            },
                        }
                    )

        # In a real background task, the result would be stored or sent via WebSocket
        # Here, we return it directly, which isn't ideal for long discovery processes
        return {
            "message": "Device discovery finished.",
            "discovered_devices": newly_discovered,
        }

    except Exception as e:
        logger.error(f"Device discovery failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Device discovery failed.",
        )


# Endpoint to get supported types and manufacturers - useful for frontend filters
# These might be better served by the integration registry directly
@router.get("/types", response_model=List[str])
async def get_device_types():
    """Get list of all unique device types across registered integrations."""
    all_types = set()
    for integration in device_registry.get_integrations():
        all_types.update(integration.supported_device_types)
    return sorted(list(all_types))


@router.get("/manufacturers", response_model=List[str])
async def get_manufacturers():
    """Get list of potential device manufacturers (could be hardcoded or from integrations)."""
    # This could be dynamic based on discovered devices or a predefined list
    manufacturers = set()
    # Example: Add from existing devices in DB
    db = next(get_db())  # Sync access - not ideal
    result = await db.execute(select(Device.manufacturer).distinct())
    manufacturers.update(r[0] for r in result.fetchall() if r[0])

    # Add known manufacturers from integrations
    # for integration in device_registry.get_integrations():
    #    # Assuming integrations might have a known_manufacturers property
    #    manufacturers.update(getattr(integration, 'known_manufacturers', []))

    # Add a common set
    manufacturers.update(
        [
            "Xiaomi",
            "Generic",
            "Philips Hue",
            "IKEA",
            "TP-Link",
            "Tuya",
            "Nest",
            "Ecobee",
        ]
    )

    return sorted(list(manufacturers))
