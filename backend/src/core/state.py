"""
Violt Core - State Management System

This module implements the state management system for tracking entity states and state changes.
"""

from typing import Dict, Any, Optional, List, Callable, Coroutine
import logging
import asyncio
from datetime import datetime
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class State:
    """Represents the state of an entity."""

    entity_id: str
    state: str
    attributes: Dict[str, Any]
    last_changed: datetime
    last_updated: datetime
    context: Dict[str, Any]


class StateManager:
    """Manages entity states and state changes."""

    def __init__(self):
        self._states: Dict[str, State] = {}
        self._listeners: List[Callable[[str, State, State], Coroutine]] = []
        self._lock = asyncio.Lock()

    async def set_state(
        self,
        entity_id: str,
        state: str,
        attributes: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> State:
        """Set the state of an entity."""
        async with self._lock:
            now = datetime.now(datetime.timezone.utc)
            old_state = self._states.get(entity_id)

            # Create new state
            new_state = State(
                entity_id=entity_id,
                state=state,
                attributes=attributes or {},
                last_changed=(
                    now
                    if not old_state or old_state.state != state
                    else old_state.last_changed
                ),
                last_updated=now,
                context=context or {},
            )

            # Update state
            self._states[entity_id] = new_state

            # Notify listeners
            if old_state != new_state:
                await self._notify_state_changed(entity_id, old_state, new_state)

            return new_state

    async def get_state(self, entity_id: str) -> Optional[State]:
        """Get the current state of an entity."""
        return self._states.get(entity_id)

    async def get_states(self) -> Dict[str, State]:
        """Get all current states."""
        return self._states.copy()

    async def add_listener(self, listener: Callable[[str, State, State], Coroutine]):
        """Add a state change listener."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    async def remove_listener(self, listener: Callable[[str, State, State], Coroutine]):
        """Remove a state change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    async def _notify_state_changed(
        self, entity_id: str, old_state: Optional[State], new_state: State
    ):
        """Notify all listeners of a state change."""
        for listener in self._listeners:
            try:
                await listener(entity_id, old_state, new_state)
            except Exception as e:
                logger.error(f"Error in state change listener: {e}", exc_info=True)


# Global state manager instance
state_manager = StateManager()
