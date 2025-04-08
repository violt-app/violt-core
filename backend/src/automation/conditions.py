"""
Violt Core Lite - Automation Engine Conditions

This module implements various condition types for the automation engine.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, time
import asyncio
import re
import pytz
import astral
from astral.sun import sun

from .base import Condition, AutomationError
from ..devices.registry import registry as device_registry

logger = logging.getLogger(__name__)


class TimeCondition(Condition):
    """Condition that checks if current time is within a specified range."""
    
    condition_type = "time"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.start_time = self._parse_time(config.get("start_time", "00:00"))
        self.end_time = self._parse_time(config.get("end_time", "23:59"))
        self.days = config.get("days", ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string into time object."""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour=hour, minute=minute)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid time format: {time_str}")
            return time(0, 0)  # Default to midnight
    
    async def evaluate(self, context: Dict[str, Any]) -> bool:
        """Check if current time is within the specified range."""
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime("%A").lower()
        
        # Check if day is included
        if current_day not in self.days:
            return False
        
        # Check if current time is within range
        if self.start_time <= self.end_time:
            # Normal time range (e.g., 8:00 to 17:00)
            return self.start_time <= current_time <= self.end_time
        else:
            # Overnight time range (e.g., 22:00 to 6:00)
            return current_time >= self.start_time or current_time <= self.end_time


class SunCondition(Condition):
    """Condition that checks if current time is before or after sunrise/sunset."""
    
    condition_type = "sun"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.event = config.get("event", "sunset")  # sunrise or sunset
        self.offset_minutes = config.get("offset_minutes", 0)
        self.relation = config.get("relation", "after")  # before or after
        self.latitude = config.get("latitude", 0)
        self.longitude = config.get("longitude", 0)
    
    async def evaluate(self, context: Dict[str, Any]) -> bool:
        """Check if current time is before or after the sun event."""
        now = datetime.now()
        
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
            
            # Check relation
            if self.relation == "before":
                return now < event_time
            elif self.relation == "after":
                return now > event_time
            else:
                logger.error(f"Invalid relation: {self.relation}")
                return False
            
        except Exception as e:
            logger.error(f"Error calculating sun times: {e}")
            return False


class DeviceStateCondition(Condition):
    """Condition that checks if a device state matches a specified value."""
    
    condition_type = "device_state"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.device_id = config.get("device_id")
        self.property = config.get("property")
        self.operator = config.get("operator", "==")
        self.value = config.get("value")
    
    async def evaluate(self, context: Dict[str, Any]) -> bool:
        """Check if device state matches the condition."""
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
        
        # Check if state matches condition
        return self._compare_values(property_value, self.operator, self.value)
    
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


class NumericCondition(Condition):
    """Condition that compares numeric values."""
    
    condition_type = "numeric"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.value1 = config.get("value1")
        self.value2 = config.get("value2")
        self.operator = config.get("operator", "==")
    
    async def evaluate(self, context: Dict[str, Any]) -> bool:
        """Compare numeric values."""
        try:
            # Resolve values from context if needed
            value1 = self._resolve_value(self.value1, context)
            value2 = self._resolve_value(self.value2, context)
            
            # Convert to float for comparison
            value1 = float(value1)
            value2 = float(value2)
            
            # Compare values
            if self.operator == "==":
                return value1 == value2
            elif self.operator == "!=":
                return value1 != value2
            elif self.operator == ">":
                return value1 > value2
            elif self.operator == ">=":
                return value1 >= value2
            elif self.operator == "<":
                return value1 < value2
            elif self.operator == "<=":
                return value1 <= value2
            else:
                logger.warning(f"Unknown operator: {self.operator}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.error(f"Error comparing numeric values: {e}")
            return False
    
    def _resolve_value(self, value: Any, context: Dict[str, Any]) -> Any:
        """Resolve value from context if it's a variable reference."""
        if isinstance(value, str) and value.startswith("$"):
            # Variable reference
            var_name = value[1:]
            return context.get(var_name, 0)
        return value


class BooleanCondition(Condition):
    """Condition that performs boolean operations."""
    
    condition_type = "boolean"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.operation = config.get("operation", "and")
        self.conditions = []
        
        # Create sub-conditions
        for condition_config in config.get("conditions", []):
            condition_type = condition_config.get("type")
            condition = create_condition(condition_type, condition_config.get("config", {}))
            if condition:
                self.conditions.append(condition)
    
    async def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate boolean operation on sub-conditions."""
        if not self.conditions:
            return True
        
        results = []
        for condition in self.conditions:
            result = await condition.evaluate(context)
            results.append(result)
        
        if self.operation == "and":
            return all(results)
        elif self.operation == "or":
            return any(results)
        elif self.operation == "not":
            return not results[0] if results else True
        else:
            logger.warning(f"Unknown boolean operation: {self.operation}")
            return False


# Factory function to create conditions
def create_condition(condition_type: str, config: Dict[str, Any]) -> Optional[Condition]:
    """Create a condition instance based on type and configuration."""
    condition_classes = {
        "time": TimeCondition,
        "sun": SunCondition,
        "device_state": DeviceStateCondition,
        "numeric": NumericCondition,
        "boolean": BooleanCondition
    }
    
    if condition_type not in condition_classes:
        logger.error(f"Unknown condition type: {condition_type}")
        return None
    
    try:
        return condition_classes[condition_type](config)
    except Exception as e:
        logger.error(f"Error creating condition of type {condition_type}: {e}")
        return None
