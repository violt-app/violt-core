"""
Violt Core Lite - Automation Engine Triggers

This module implements various trigger types for the automation engine.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, time, timedelta
import asyncio
import re
import pytz
import astral
from astral.sun import sun

from .base import Trigger, AutomationError
from ..devices.registry import registry as device_registry

logger = logging.getLogger(__name__)


class TimeTrigger(Trigger):
    """Trigger that activates at a specific time."""
    
    trigger_type = "time"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.time = self._parse_time(config.get("time", "00:00"))
        self.days = config.get("days", ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
        self.last_triggered_day = None
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string into time object."""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour=hour, minute=minute)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid time format: {time_str}")
            return time(0, 0)  # Default to midnight
    
    async def check(self, context: Dict[str, Any]) -> bool:
        """Check if current time matches the trigger time."""
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime("%A").lower()
        
        # Check if day is included
        if current_day not in self.days:
            return False
        
        # Check if already triggered today
        if self.last_triggered_day == now.date():
            return False
        
        # Check if current time matches trigger time
        # Allow a 1-minute window to avoid missing the exact second
        trigger_datetime = datetime.combine(now.date(), self.time)
        time_diff = abs((now - trigger_datetime).total_seconds())
        
        if time_diff <= 60:  # Within 1 minute
            self.last_triggered_day = now.date()
            self.update_last_triggered()
            return True
        
        return False


class SunTrigger(Trigger):
    """Trigger that activates at sunrise or sunset."""
    
    trigger_type = "sun"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.event = config.get("event", "sunset")  # sunrise or sunset
        self.offset_minutes = config.get("offset_minutes", 0)
        self.latitude = config.get("latitude", 0)
        self.longitude = config.get("longitude", 0)
        self.last_triggered_day = None
    
    async def check(self, context: Dict[str, Any]) -> bool:
        """Check if current time matches the sun event time."""
        now = datetime.now()
        
        # Check if already triggered today
        if self.last_triggered_day == now.date():
            return False
        
        try:
            # Calculate sun times
            location = astral.LocationInfo(
                name="Home",
                region="",
                timezone="UTC",
                latitude=self.latitude,
                longitude=self.longitude
            )
            
            s = sun(location.observer, date=now.date())
            
            if self.event == "sunrise":
                event_time = s["sunrise"]
            elif self.event == "sunset":
                event_time = s["sunset"]
            else:
                logger.error(f"Invalid sun event: {self.event}")
                return False
            
            # Apply offset
            event_time = event_time + timedelta(minutes=self.offset_minutes)
            
            # Convert to local time
            event_time = event_time.replace(tzinfo=None)
            
            # Check if current time matches event time
            # Allow a 1-minute window to avoid missing the exact second
            time_diff = abs((now - event_time).total_seconds())
            
            if time_diff <= 60:  # Within 1 minute
                self.last_triggered_day = now.date()
                self.update_last_triggered()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error calculating sun times: {e}")
            return False


class IntervalTrigger(Trigger):
    """Trigger that activates at regular intervals."""
    
    trigger_type = "interval"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.interval_minutes = config.get("interval_minutes", 60)
        self.start_time = config.get("start_time")
        self.end_time = config.get("end_time")
        
        if self.start_time:
            self.start_time = self._parse_time(self.start_time)
        if self.end_time:
            self.end_time = self._parse_time(self.end_time)
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string into time object."""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour=hour, minute=minute)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid time format: {time_str}")
            return None
    
    async def check(self, context: Dict[str, Any]) -> bool:
        """Check if interval has elapsed since last trigger."""
        now = datetime.now()
        current_time = now.time()
        
        # Check if within allowed time range
        if self.start_time and current_time < self.start_time:
            return False
        if self.end_time and current_time > self.end_time:
            return False
        
        # Check if interval has elapsed
        if self.last_triggered:
            elapsed_minutes = (now - self.last_triggered).total_seconds() / 60
            if elapsed_minutes < self.interval_minutes:
                return False
        
        self.update_last_triggered()
        return True


class DeviceStateTrigger(Trigger):
    """Trigger that activates when a device state changes."""
    
    trigger_type = "device_state"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.device_id = config.get("device_id")
        self.property = config.get("property")
        self.operator = config.get("operator", "==")
        self.value = config.get("value")
        self.previous_state = None
    
    async def check(self, context: Dict[str, Any]) -> bool:
        """Check if device state matches the trigger condition."""
        if not self.device_id or not self.property:
            return False
        
        # Get device from registry
        device = device_registry.get_device(self.device_id)
        if not device:
            logger.warning(f"Device not found: {self.device_id}")
            return False
        
        # Get current state
        current_state = device.state.to_dict()
        property_value = self._get_nested_property(current_state, self.property)
        
        if property_value is None:
            return False
        
        # Check if state has changed since last check
        if self.previous_state is not None:
            previous_value = self._get_nested_property(self.previous_state, self.property)
            if property_value == previous_value:
                # State hasn't changed
                self.previous_state = current_state
                return False
        
        # Update previous state
        self.previous_state = current_state
        
        # Check if state matches condition
        result = self._compare_values(property_value, self.operator, self.value)
        
        if result:
            self.update_last_triggered()
        
        return result
    
    def _get_nested_property(self, state: Dict[str, Any], property_path: str) -> Any:
        """Get a nested property from a state dictionary."""
        if not property_path:
            return None
        
        parts = property_path.split(".")
        value = state
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
    
    def _compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare values using the specified operator."""
        try:
            if operator == "==":
                return actual == expected
            elif operator == "!=":
                return actual != expected
            elif operator == ">":
                return float(actual) > float(expected)
            elif operator == ">=":
                return float(actual) >= float(expected)
            elif operator == "<":
                return float(actual) < float(expected)
            elif operator == "<=":
                return float(actual) <= float(expected)
            elif operator == "contains":
                return expected in actual
            elif operator == "starts_with":
                return str(actual).startswith(str(expected))
            elif operator == "ends_with":
                return str(actual).endswith(str(expected))
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Error comparing values: {e}")
            return False


class EventTrigger(Trigger):
    """Trigger that activates when a specific event occurs."""
    
    trigger_type = "event"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.event_type = config.get("event_type")
        self.source = config.get("source")
        self.device_id = config.get("device_id")
        self.data_conditions = config.get("data_conditions", {})
    
    async def check(self, context: Dict[str, Any]) -> bool:
        """Check if event matches the trigger condition."""
        # Get event from context
        event = context.get("event")
        if not event:
            return False
        
        # Check event type
        if self.event_type and event.type != self.event_type:
            return False
        
        # Check source
        if self.source and event.source != self.source:
            return False
        
        # Check device ID
        if self.device_id and event.device_id != self.device_id:
            return False
        
        # Check data conditions
        if self.data_conditions and event.data:
            for key, value in self.data_conditions.items():
                if key not in event.data or event.data[key] != value:
                    return False
        
        self.update_last_triggered()
        return True


# Factory function to create triggers
def create_trigger(trigger_type: str, config: Dict[str, Any]) -> Optional[Trigger]:
    """Create a trigger instance based on type and configuration."""
    trigger_classes = {
        "time": TimeTrigger,
        "sun": SunTrigger,
        "interval": IntervalTrigger,
        "device_state": DeviceStateTrigger,
        "event": EventTrigger
    }
    
    if trigger_type not in trigger_classes:
        logger.error(f"Unknown trigger type: {trigger_type}")
        return None
    
    try:
        return trigger_classes[trigger_type](config)
    except Exception as e:
        logger.error(f"Error creating trigger of type {trigger_type}: {e}")
        return None
