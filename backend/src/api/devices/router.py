# backend/src/api/devices/router.py

"""
Violt Core - API Router for Devices

This module handles device API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete as sql_delete
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime, timezone
import asyncio
import re

from ...core.schemas import (
    DeviceCommand,
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceState,
    DeviceStatus,
    DeviceProperties,
    DeviceCapability,
)
from ...core.auth import get_current_active_user
from ...database.session import get_db
from ...database.models import Device, User, Event

# Placeholder for device integration registry and control functions
# These would be properly imported from device/integration modules in a full implementation
from ...devices.registry import registry as device_registry
from ...devices.base import Device as IntegrationDevice, DeviceIntegrationError
from ...core.websocket import manager as websocket_manager

TOKEN_REGEX = re.compile(r"^[0-9A-Fa-f]+$")

logger = logging.getLogger(__name__)
router = APIRouter()


# Helper function (TODO: consider moving to a crud utility module)
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
    status: Optional[DeviceStatus] = None,
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
        query = query.where(Device.status == status.value)

    result = await db.execute(query.order_by(Device.name))  # Order by name
    devices = result.scalars().all()

    return devices


@router.post(
    "/create", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED
)
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
            "integrations"
        )  # Assuming config path
        integration = device_registry.get_integration(device_data.integration_type)
        if not integration:
            logger.error(
                f"Device creation failed: Unsupported integration type '{device_data.integration_type}'. Request data: {device_data.model_dump()}"
            )
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
        logger.error(
            f"Device creation failed: Missing ip_address or token for Xiaomi. Request data: {device_data.model_dump()}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Xiaomi devices require ip_address and token in config.",
        )
    if device_data.integration_type == "xiaomi":
        token = device_data.config.get("token", "")
        if not TOKEN_REGEX.fullmatch(token):
            logger.error(
                f"Device creation failed: Invalid Xiaomi token format: {token}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Xiaomi token must be a hexadecimal string.",
            )
    # Add similar checks for other integrations as needed

    # Create new device model instance with proper schema initialization
    new_device_db = Device(
        id=str(uuid.uuid4()),
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
        properties=DeviceProperties().model_dump(),
        state=DeviceState().model_dump(),
        status=DeviceStatus.OFFLINE,
    )

    db.add(new_device_db)

    # Save device to DB without attempting connection
    try:
        await db.commit()
        await db.refresh(new_device_db)
        logger.info(
            f"Device {new_device_db.name} created successfully with ID: {new_device_db.id}"
        )

        # Try to connect in background without affecting device creation
        try:
            integration_device: Optional[IntegrationDevice] = (
                await integration.add_device(
                    {
                        **device_data.model_dump(),
                        "id": new_device_db.id,
                    }
                )
            )
            if integration_device:
                # Update device status
                new_device_db.status = DeviceStatus.CONNECTED

                # Update device state with actual values
                new_device_db.state = DeviceState(
                    power=integration_device.state.get("power"),
                    brightness=integration_device.state.get("brightness"),
                    color_temp=integration_device.state.get("color_temp"),
                    color=integration_device.state.get("color"),
                    temperature=integration_device.state.get("temperature"),
                    humidity=integration_device.state.get("humidity"),
                    motion=integration_device.state.get("motion"),
                    battery=integration_device.state.get("battery"),
                ).model_dump()

                # Update device properties with capabilities
                new_device_db.properties = DeviceProperties(
                    capabilities=[
                        DeviceCapability(cap)
                        for cap in integration_device.properties.get("capabilities", [])
                    ],
                    supported_features=integration_device.properties.get(
                        "supported_features", {}
                    ),
                ).model_dump()

                await db.commit()
                logger.info(f"Device {new_device_db.name} connected successfully")
        except Exception as e:
            logger.warning(
                f"Initial connection attempt failed for device {new_device_db.name}: {str(e)}"
            )
            # Don't raise exception - device is created but offline

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create device in database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device",
        )
    except Exception as e:
        await db.rollback()  # Rollback if commit fails
        logger.error(
            f"Database error creating device: {e}. Device data: {device_data.model_dump()}",
            exc_info=True,
        )
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


@router.post("/{device_id}/connect", response_model=DeviceResponse)
async def connect_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Attempt to connect to a device."""
    # Get the device
    device = await get_device_by_id(db, device_id, current_user.id)

    # Helper to notify connection failure after delay
    def _schedule_failure(dev):
        async def _notify():
            await asyncio.sleep(5)
            await websocket_manager.send_personal_message(
                {
                    "type": "device_updated",
                    "device": DeviceResponse.model_validate(dev).model_dump(),
                },
                current_user.id,
                "devices",
            )

        asyncio.create_task(_notify())

    # Validate Xiaomi token format before connecting
    if device.integration_type == "xiaomi":
        token = device.config.get("token", "")
        if not TOKEN_REGEX.fullmatch(token):
            logger.error(
                f"Connection failed: Invalid Xiaomi token format: {token} for device {device.name}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Xiaomi token format.",
            )

    # Get the integration
    integration = device_registry.get_integration(device.integration_type)
    if not integration:
        logger.error(
            f"Connection failed: Integration {device.integration_type} not found for device {device.name}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integration {device.integration_type} not found",
        )

    try:
        # Update status to connecting
        device.status = DeviceStatus.CONNECTING
        await db.commit()

        # Try to connect to the device
        integration_device: Optional[IntegrationDevice] = await integration.add_device(
            {
                "id": device.id,
                "name": device.name,
                "type": device.type,
                "model": device.model,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "config": device.config,
            }
        )

        if integration_device:
            # Update device status
            device.status = DeviceStatus.CONNECTED

            # Update device state with actual values
            device.state = DeviceState(
                power=integration_device.state.get("power"),
                brightness=integration_device.state.get("brightness"),
                color_temp=integration_device.state.get("color_temp"),
                color=integration_device.state.get("color"),
                temperature=integration_device.state.get("temperature"),
                humidity=integration_device.state.get("humidity"),
                motion=integration_device.state.get("motion"),
                battery=integration_device.state.get("battery"),
            ).model_dump()

            # Update device properties with capabilities
            device.properties = DeviceProperties(
                capabilities=[
                    DeviceCapability(cap)
                    for cap in integration_device.properties.get("capabilities", [])
                ],
                supported_features=integration_device.properties.get(
                    "supported_features", {}
                ),
            ).model_dump()

            await db.commit()
            logger.info(f"Device {device.name} connected successfully")

            # Send WebSocket update
            await websocket_manager.send_personal_message(
                {
                    "type": "device_updated",
                    "device": DeviceResponse.model_validate(device).model_dump(),
                },
                current_user.id,
                "devices",
            )

            return device
        else:
            device.status = DeviceStatus.OFFLINE
            await db.commit()
            logger.error(
                f"Connection failed: Integration returned None for device {device.name}"
            )
            _schedule_failure(device)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Device is offline or unreachable.",
            )

    except DeviceIntegrationError as e:
        device.status = DeviceStatus.ERROR
        await db.commit()
        logger.error(
            f"Connection failed: Integration error for device {device.name}: {str(e)}"
        )
        _schedule_failure(device)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect: {str(e)}",
        )
    except Exception as e:
        device.status = DeviceStatus.ERROR
        await db.commit()
        logger.error(f"Unexpected error connecting to device {device.name}: {str(e)}")
        _schedule_failure(device)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while connecting to the device",
        )


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

        device_db.last_updated = datetime.now(
            timezone.utc
        )  # Update timestamp explicitly
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


@router.get("/{device_id}/state", response_model=DeviceState)
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

    return device.state


@router.put("/{device_id}/state", response_model=DeviceState)
async def update_device_state(
    device_id: str,
    state_data: DeviceState,
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
    device_db.state = state_data.model_dump()
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
            "state": state_data.model_dump(),
        },
        device_id=device_db.id,
    )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {
            "type": "device_state_changed",
            "device_id": device_id,
            "device": DeviceResponse.model_validate(device_db).model_dump(),
        },
        current_user.id,
        "devices",
    )

    logger.info(f"Device state manually updated: {device_db.id} - {device_db.name}")
    return device_db.state


@router.post("/{device_id}/command", response_model=Dict[str, Any])
async def execute_device_command(
    device_id: str,
    command_data: DeviceCommand,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Execute a command on a device via its integration."""
    device_db = await get_device_by_id(db, device_id, current_user.id)
    command = command_data.get("command")
    payload = command_data.get("payload", {})

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
        # Update status to show we're executing a command
        device_db.status = DeviceStatus.CONNECTING
        await db.commit()

        success = await integration_device.execute_command(command, payload)
        if success:
            # Get updated state from device
            new_state = await integration_device.get_state()

            # Update device with new state and status
            device_db.status = DeviceStatus.CONNECTED
            device_db.state = DeviceState(
                power=new_state.get("power"),
                brightness=new_state.get("brightness"),
                color_temp=new_state.get("color_temp"),
                color=new_state.get("color"),
                temperature=new_state.get("temperature"),
                humidity=new_state.get("humidity"),
                motion=new_state.get("motion"),
                battery=new_state.get("battery"),
            ).model_dump()
            device_db.last_updated = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                f"Command '{command}' executed successfully on device {device_id}"
            )

            # Log event
            await log_event(
                db,
                event_type="device_command_sent",
                source="api",
                data={
                    "device_id": device_id,
                    "command": command,
                    "payload": payload,
                    "success": True,
                    "new_state": device_db.state,
                },
                device_id=device_id,
            )

            # Optionally record telemetry data if needed
            telemetry_service = request.app.state.telemetry_service
            if telemetry_service:
                await telemetry_service.record_event(
                    event_type="device_command",
                    params={
                        "device_id": device_id,
                        "integration": device_db.integration_type,
                        "command": command,
                        "payload": payload,
                    },
                    user_id=current_user.id,
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

            return {
                "status": "success",
                "message": f"Command '{command}' executed successfully.",
                "device": DeviceResponse.model_validate(device_db).model_dump(),
            }
        else:
            # Update status to error
            device_db.status = DeviceStatus.ERROR
            await db.commit()

            logger.warning(f"Command '{command}' failed for device {device_id}")
            await log_event(
                db,
                event_type="device_command_failed",
                source="integration",
                data={"device_id": device_id, "command": command, "params": params},
                device_id=device_id,
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

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute command '{command}'.",
            )
    except DeviceIntegrationError as e:
        # Update status to error
        device_db.status = DeviceStatus.ERROR
        await db.commit()

        logger.error(
            f"Integration error executing command '{command}' on device {device_id}: {str(e)}"
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

        # Send WebSocket update
        await websocket_manager.send_personal_message(
            {
                "type": "device_updated",
                "device": DeviceResponse.model_validate(device_db).model_dump(),
            },
            current_user.id,
            "devices",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integration error: {e}",
        )
    except Exception as e:
        # Update status to error
        device_db.status = DeviceStatus.ERROR
        await db.commit()

        logger.error(
            f"Unexpected error executing command '{command}' on device {device_id}: {str(e)}"
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

        # Send WebSocket update
        await websocket_manager.send_personal_message(
            {
                "type": "device_updated",
                "device": DeviceResponse.model_validate(device_db).model_dump(),
            },
            current_user.id,
            "devices",
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
