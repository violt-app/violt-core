"""
Violt Core Lite - API Router for Integrations

This module handles integration API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
import logging

from ...core.schemas import IntegrationInfo, IntegrationSetup
from ...core.auth import get_current_active_user
from ...database.session import get_db
from ...database.models import User, Device, Event
from ...core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[IntegrationInfo])
async def list_integrations(
    current_user: User = Depends(get_current_active_user)
):
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
                    "token": {"type": "string"}
                },
                "required": ["ip_address", "token"]
            }
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
                    "redirect_uri": {"type": "string"}
                },
                "required": ["client_id", "client_secret", "redirect_uri"]
            }
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
                    "client_secret": {"type": "string"}
                },
                "required": ["project_id", "client_id", "client_secret"]
            }
        }
    ]
    
    return integrations


@router.get("/{integration_type}", response_model=IntegrationInfo)
async def get_integration(
    integration_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get integration details."""
    integration = await get_integration_by_type(integration_type)
    return integration


@router.post("/{integration_type}/setup", status_code=status.HTTP_202_ACCEPTED)
async def setup_integration(
    integration_type: str,
    setup_data: IntegrationSetup,
    current_user: User = Depends(get_current_active_user)
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
        "task_id": f"setup_task_{integration_type}"
    }


@router.delete("/{integration_type}", status_code=status.HTTP_202_ACCEPTED)
async def remove_integration(
    integration_type: str,
    current_user: User = Depends(get_current_active_user)
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
        "task_id": f"remove_task_{integration_type}"
    }


@router.get("/{integration_type}/devices", response_model=List[Dict[str, Any]])
async def list_integration_devices(
    integration_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List devices for integration."""
    # Verify integration exists
    integration = await get_integration_by_type(integration_type)
    
    # Get devices for this integration
    result = await db.execute(
        select(Device).where(
            Device.user_id == current_user.id,
            Device.integration_type == integration_type
        )
    )
    devices = result.scalars().all()
    
    # Format devices for response
    device_list = []
    for device in devices:
        device_list.append({
            "id": device.id,
            "name": device.name,
            "type": device.type,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "status": device.status
        })
    
    return device_list


@router.post("/{integration_type}/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_integration_devices(
    integration_type: str,
    current_user: User = Depends(get_current_active_user)
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
        "task_id": f"sync_task_{integration_type}"
    }


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
                    "token": {"type": "string"}
                },
                "required": ["ip_address", "token"]
            }
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
                    "redirect_uri": {"type": "string"}
                },
                "required": ["client_id", "client_secret", "redirect_uri"]
            }
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
                    "client_secret": {"type": "string"}
                },
                "required": ["project_id", "client_id", "client_secret"]
            }
        }
    }
    
    if integration_type not in integrations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    return integrations[integration_type]
