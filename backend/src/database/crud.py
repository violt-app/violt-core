"""
CRUD utilities for Violt Core Lite database operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from .models import Device
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def get_device_by_id(db: AsyncSession, device_id: str) -> Optional[Device]:
    result = await db.execute(select(Device).where(Device.id == device_id))
    return result.scalars().first()

async def get_device_by_ip(db: AsyncSession, ip_address: str) -> Optional[Device]:
    result = await db.execute(select(Device).where(Device.ip_address == ip_address))
    return result.scalars().first()

async def upsert_device_from_integration(db: AsyncSession, device_data: Dict[str, Any], user_id: str) -> Device:
    """
    Ensure a device exists in the DB matching the integration device. If not, create it.
    device_data should contain at least: id (optional), name, type, manufacturer, model, location, ip_address, status, integration_type, config
    """
    # Try to find by device_id or ip_address
    device = None
    if device_data.get("id"):
        device = await get_device_by_id(db, device_data["id"])
    if not device and device_data.get("ip_address"):
        device = await get_device_by_ip(db, device_data["ip_address"])
    
    if device:
        # Optionally update fields here
        logger.info(f"Device already exists in DB: {device.id} ({device.name})")
        return device
    
    # Create new device
    device = Device(
        id=device_data.get("id"),
        user_id=user_id,
        name=device_data.get("name", "Unnamed Device"),
        type=device_data.get("type", "unknown"),
        manufacturer=device_data.get("manufacturer", "Unknown"),
        model=device_data.get("model"),
        location=device_data.get("location"),
        ip_address=device_data.get("ip_address"),
        mac_address=device_data.get("mac_address"),
        status=device_data.get("status", "offline"),
        properties=device_data.get("properties"),
        state=device_data.get("state"),
        integration_type=device_data.get("integration_type", "xiaomi"),
        config=device_data.get("config"),
    )
    db.add(device)
    try:
        await db.commit()
        await db.refresh(device)
        logger.info(f"Device created in DB from integration: {device.id} ({device.name})")
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError creating device in DB: {e}")
        raise
    return device
