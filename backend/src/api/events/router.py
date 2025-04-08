"""
Violt Core Lite - API Router for Events

This module handles event API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from ...core.schemas import EventResponse
from ...core.auth import get_current_active_user
from ...database.session import get_db
from ...database.models import User, Device, Event

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[EventResponse])
async def get_events(
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent events with optional filtering."""
    query = select(Event).order_by(Event.timestamp.desc()).limit(limit)
    
    # Apply filters if provided
    if event_type:
        query = query.where(Event.type == event_type)
    if source:
        query = query.where(Event.source == source)
    if start_time:
        query = query.where(Event.timestamp >= start_time)
    if end_time:
        query = query.where(Event.timestamp <= end_time)
    
    # For device-specific events, filter by user's devices
    device_subquery = select(Device.id).where(Device.user_id == current_user.id)
    query = query.where(
        (Event.device_id.is_(None)) | (Event.device_id.in_(device_subquery))
    )
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get event details by ID."""
    event = await get_event_by_id(db, event_id, current_user.id)
    return event


@router.get("/device/{device_id}", response_model=List[EventResponse])
async def get_device_events(
    device_id: str,
    event_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get events for specific device."""
    # Verify device exists and belongs to user
    device = await get_device_by_id(db, device_id, current_user.id)
    
    # Query events for this device
    query = select(Event).where(Event.device_id == device_id).order_by(Event.timestamp.desc()).limit(limit)
    
    # Apply type filter if provided
    if event_type:
        query = query.where(Event.type == event_type)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return events


# Helper functions
async def get_event_by_id(db: AsyncSession, event_id: str, user_id: str) -> Event:
    """Get an event by ID and verify access."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # If event is associated with a device, verify ownership
    if event.device_id:
        device_result = await db.execute(
            select(Device).where(Device.id == event.device_id, Device.user_id == user_id)
        )
        device = device_result.scalars().first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this event"
            )
    
    return event


async def get_device_by_id(db: AsyncSession, device_id: str, user_id: str) -> Device:
    """Get a device by ID and verify ownership."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.user_id == user_id)
    )
    device = result.scalars().first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return device
