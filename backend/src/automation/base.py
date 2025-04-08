"""
Violt Core Lite - Automation Engine Base Module

This module defines the base classes and interfaces for the automation engine.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
import logging
from datetime import datetime, time
import asyncio
import uuid
import re

from ..devices.registry import registry as device_registry
from ..database.models import Automation, Event

logger = logging.getLogger(__name__)


class AutomationError(Exception):
    """Exception raised for errors in automation engine."""
    pass


class Trigger(ABC):
    """Base class for automation triggers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.last_triggered = None
    
    @property
    @abstractmethod
    def trigger_type(self) -> str:
        """Get trigger type."""
        pass
    
    @abstractmethod
    async def check(self, context: Dict[str, Any]) -> bool:
        """Check if trigger condition is met."""
        pass
    
    def update_last_triggered(self):
        """Update last triggered timestamp."""
        self.last_triggered = datetime.utcnow()


class Condition(ABC):
    """Base class for automation conditions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @property
    @abstractmethod
    def condition_type(self) -> str:
        """Get condition type."""
        pass
    
    @abstractmethod
    async def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate if condition is met."""
        pass


class Action(ABC):
    """Base class for automation actions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @property
    @abstractmethod
    def action_type(self) -> str:
        """Get action type."""
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> bool:
        """Execute the action."""
        pass


class AutomationRule:
    """Class representing an automation rule with trigger, conditions, and actions."""
    
    def __init__(
        self,
        automation_id: str,
        name: str,
        trigger: Trigger,
        actions: List[Action],
        conditions: Optional[List[Condition]] = None,
        condition_type: str = "and",
        enabled: bool = True
    ):
        self.id = automation_id
        self.name = name
        self.trigger = trigger
        self.actions = actions
        self.conditions = conditions or []
        self.condition_type = condition_type.lower()  # "and" or "or"
        self.enabled = enabled
        self.last_triggered = None
        self.execution_count = 0
    
    async def check_trigger(self, context: Dict[str, Any]) -> bool:
        """Check if trigger condition is met."""
        if not self.enabled:
            return False
        
        try:
            return await self.trigger.check(context)
        except Exception as e:
            logger.error(f"Error checking trigger for automation {self.name}: {e}")
            return False
    
    async def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate if all conditions are met."""
        if not self.conditions:
            return True
        
        try:
            results = []
            for condition in self.conditions:
                result = await condition.evaluate(context)
                results.append(result)
            
            if self.condition_type == "and":
                return all(results)
            elif self.condition_type == "or":
                return any(results)
            else:
                logger.warning(f"Unknown condition type: {self.condition_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating conditions for automation {self.name}: {e}")
            return False
    
    async def execute_actions(self, context: Dict[str, Any]) -> bool:
        """Execute all actions."""
        if not self.enabled:
            return False
        
        success = True
        results = {}
        
        try:
            for i, action in enumerate(self.actions):
                try:
                    action_success = await action.execute(context)
                    results[f"action_{i}"] = {
                        "type": action.action_type,
                        "success": action_success
                    }
                    
                    if not action_success:
                        success = False
                        
                except Exception as e:
                    logger.error(f"Error executing action {i} for automation {self.name}: {e}")
                    results[f"action_{i}"] = {
                        "type": action.action_type,
                        "success": False,
                        "error": str(e)
                    }
                    success = False
            
            # Update execution stats
            self.last_triggered = datetime.utcnow()
            self.execution_count += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing actions for automation {self.name}: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert automation rule to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "trigger_type": self.trigger.trigger_type,
            "trigger_config": self.trigger.config,
            "condition_type": self.condition_type,
            "conditions": [
                {"type": condition.condition_type, "config": condition.config}
                for condition in self.conditions
            ] if self.conditions else [],
            "actions": [
                {"type": action.action_type, "config": action.config}
                for action in self.actions
            ],
            "enabled": self.enabled,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "execution_count": self.execution_count
        }
