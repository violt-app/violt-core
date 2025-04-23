"""
Violt Core Lite - WebSocket Module

This module handles WebSocket connections for real-time updates.
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from typing import Dict, List, Any, Optional
import json
import logging
import asyncio
from datetime import datetime

from ..core.auth import get_current_user
from ..database.models import User, Device, Event

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket connection manager."""

    def __init__(self):
        # Store active connections by user_id and connection type
        self.active_connections: Dict[str, Dict[str, List[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, connection_type: str):
        """Connect a new WebSocket client."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        if connection_type not in self.active_connections[user_id]:
            self.active_connections[user_id][connection_type] = []

        self.active_connections[user_id][connection_type].append(websocket)
        logger.info(
            f"New WebSocket connection: user_id={user_id}, type={connection_type}"
        )

    async def disconnect(
        self, websocket: WebSocket, user_id: str, connection_type: str
    ):
        """Disconnect a WebSocket client."""
        if (
            user_id in self.active_connections
            and connection_type in self.active_connections[user_id]
        ):

            self.active_connections[user_id][connection_type].remove(websocket)

            # Clean up empty lists
            if not self.active_connections[user_id][connection_type]:
                del self.active_connections[user_id][connection_type]

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

            logger.info(
                f"WebSocket disconnected: user_id={user_id}, type={connection_type}"
            )

    async def send_personal_message(
        self, message: Dict[str, Any], user_id: str, connection_type: str
    ):
        """Send a message to a specific user's connections of a specific type."""
        if (
            user_id in self.active_connections
            and connection_type in self.active_connections[user_id]
        ):

            # Add timestamp to message
            message["timestamp"] = datetime.utcnow().isoformat()

            # Convert message to JSON
            json_message = json.dumps(message)

            logger.debug(f"WS → sending to {user_id}/{connection_type}: {message}")

            # Send to all connections of this type for this user
            for connection in self.active_connections[user_id][connection_type]:
                try:
                    await connection.send_text(json_message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: Dict[str, Any], connection_type: str):
        """Broadcast a message to all connections of a specific type."""
        # Add timestamp to message
        message["timestamp"] = datetime.utcnow().isoformat()

        # Convert message to JSON
        json_message = json.dumps(message)

        # Send to all connections of this type
        for user_id in self.active_connections:
            if connection_type in self.active_connections[user_id]:
                for connection in self.active_connections[user_id][connection_type]:
                    try:
                        await connection.send_text(json_message)
                    except Exception as e:
                        logger.error(f"Error broadcasting message: {e}")


# Create global connection manager
manager = ConnectionManager()


async def get_token_from_query(websocket: WebSocket) -> Optional[str]:
    """Extract token from WebSocket query parameters."""
    token = websocket.query_params.get("token")
    return token


async def handle_device_updates(websocket: WebSocket, user: User):
    """Handle device update WebSocket connection."""
    user_id = user.id
    connection_type = "devices"

    try:
        await manager.connect(websocket, user_id, connection_type)

        # Send initial connection confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to device updates",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            # Process message (e.g., subscribe to specific devices)
            try:
                message = json.loads(data)
                logger.debug(f"Received WebSocket message: {message}")

                # Handle message types
                if message.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, connection_type)


async def handle_automation_updates(websocket: WebSocket, user: User):
    """Handle automation update WebSocket connection."""
    user_id = user.id
    connection_type = "automations"

    try:
        await manager.connect(websocket, user_id, connection_type)

        # Send initial connection confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to automation updates",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            # Process message
            try:
                message = json.loads(data)
                logger.debug(f"Received WebSocket message: {message}")

                # Handle message types
                if message.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, connection_type)


async def handle_event_updates(websocket: WebSocket, user: User):
    """Handle event update WebSocket connection."""
    user_id = user.id
    connection_type = "events"

    try:
        await manager.connect(websocket, user_id, connection_type)

        # Send initial connection confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to event updates",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            # Process message
            try:
                message = json.loads(data)
                logger.debug(f"Received WebSocket message: {message}")

                # Handle message types
                if message.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, connection_type)


async def get_total_connections() -> int:
    """Get the total number of active WebSocket connections."""
    try:
        return len(manager.active_connections)
    except Exception as e:
        logger.error(f"Error getting total connections: {e}")
        return 0


# Functions to send updates
async def send_device_update(device: Device):
    """Send device update to connected clients."""
    message = {
        "type": "device_update",
        "device_id": device.id,
        "name": device.name,
        "status": device.status,
        "state": device.state,
        "last_updated": device.last_updated.isoformat(),
    }

    await manager.send_personal_message(message, device.user_id, "devices")


async def send_automation_update(
    automation_id: str, user_id: str, data: Dict[str, Any]
):
    """Send automation update to connected clients."""
    message = {"type": "automation_update", "automation_id": automation_id, **data}

    await manager.send_personal_message(message, user_id, "automations")


async def send_event_notification(event: Event, user_id: str):
    """Send event notification to connected clients."""
    message = {
        "type": "event_notification",
        "event_id": event.id,
        "event_type": event.type,
        "source": event.source,
        "device_id": event.device_id,
        "data": event.data,
        "timestamp": event.timestamp.isoformat(),
    }

    await manager.send_personal_message(message, user_id, "events")
