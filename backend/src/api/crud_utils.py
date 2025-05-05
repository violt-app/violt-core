"""
Utility functions for CRUD operations and event logging.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database.models import Device, Event

logger = logging.getLogger(__name__)


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
