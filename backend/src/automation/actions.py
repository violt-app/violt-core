"""
Violt Core Lite - Automation Engine Actions

This module implements various action types for the automation engine.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, time
import asyncio
import json
import requests

from .base import Action, AutomationError
from ..devices.registry import registry as device_registry

logger = logging.getLogger(__name__)

class DeviceCommandAction(Action):
    """Action that executes a command on a device."""

    action_type = "device_command"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.device_id = config.get("device_id")
        self.command = config.get("command")
        self.params = config.get("params", {})

    async def execute(self, context: Dict[str, Any]) -> bool:
        """Execute a command on a device."""
        if not self.device_id or not self.command:
            logger.error("Missing device_id or command in DeviceCommandAction")
            return False

        # Get device from registry
        device = device_registry.get_device(self.device_id)
        if not device:
            logger.warning(f"Device not found: {self.device_id}")
            return False

        try:
            # Execute command
            params = self._resolve_params(self.params, context)
            success = await device.execute_command(self.command, params)

            if success:
                logger.info(
                    f"Successfully executed command {self.command} on device {device.name}"
                )
            else:
                logger.warning(
                    f"Failed to execute command {self.command} on device {device.name}"
                )

            return success

        except Exception as e:
            logger.error(
                f"Error executing command {self.command} on device {device.name}: {e}"
            )
            return False

    def _resolve_params(
        self, params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve parameter values from context if needed."""
        resolved_params = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # Variable reference
                var_name = value[1:]
                resolved_params[key] = context.get(var_name, value)
            else:
                resolved_params[key] = value

        return resolved_params


class DelayAction(Action):
    """Action that introduces a delay."""

    action_type = "delay"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.seconds = config.get("seconds", 0)
        self.minutes = config.get("minutes", 0)
        self.hours = config.get("hours", 0)

    async def execute(self, context: Dict[str, Any]) -> bool:
        """Introduce a delay."""
        total_seconds = self.seconds + (self.minutes * 60) + (self.hours * 3600)

        if total_seconds <= 0:
            return True

        try:
            logger.info(f"Delaying for {total_seconds} seconds")
            await asyncio.sleep(total_seconds)
            return True

        except Exception as e:
            logger.error(f"Error during delay: {e}")
            return False


class NotificationAction(Action):
    """Action that sends a notification."""

    action_type = "notification"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.title = config.get("title", "Violt Notification")
        self.message = config.get("message", "")
        self.level = config.get("level", "info")  # info, warning, error
        self.targets = config.get("targets", ["system"])  # system, email, push, etc.

    async def execute(self, context: Dict[str, Any]) -> bool:
        """Send a notification."""
        if not self.message:
            logger.warning("Missing message in NotificationAction")
            return False

        try:
            # Resolve message template
            message = self._resolve_template(self.message, context)
            title = self._resolve_template(self.title, context)

            # Log notification
            log_method = getattr(logger, self.level, logger.info)
            log_method(f"Notification: {title} - {message}")

            # Create notification event
            from ..database.models import Event
            from ..database.session import get_db

            db = next(get_db())
            event = Event(
                type="notification",
                source="automation",
                level=self.level,
                title=title,
                message=message,
                data={"targets": self.targets},
            )
            db.add(event)
            db.commit()

            # TODO: Implement actual notification delivery based on targets
            # For MVP, we just log the notification

            return True

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    def _resolve_template(self, template: str, context: Dict[str, Any]) -> str:
        """Resolve template string with variables from context."""
        if not template:
            return ""

        result = template

        # Replace variables in format ${variable_name}
        import re

        for match in re.finditer(r"\${([^}]+)}", template):
            var_name = match.group(1)
            var_value = self._get_nested_value(context, var_name)
            if var_value is not None:
                result = result.replace(match.group(0), str(var_value))

        return result

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        parts = path.split(".")
        value = data

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return value


class SceneAction(Action):
    """Action that activates a scene (multiple device commands)."""

    action_type = "scene"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.scene_id = config.get("scene_id")
        self.commands = config.get("commands", [])

    async def execute(self, context: Dict[str, Any]) -> bool:
        """Activate a scene."""
        if not self.commands and not self.scene_id:
            logger.error("Missing scene_id or commands in SceneAction")
            return False

        try:
            # If scene_id is provided, load commands from database
            if self.scene_id:
                # TODO: Implement scene loading from database
                # For MVP, we use the commands provided directly
                pass

            # Execute all commands
            success = True
            for cmd in self.commands:
                device_id = cmd.get("device_id")
                command = cmd.get("command")
                params = cmd.get("params", {})

                if not device_id or not command:
                    logger.warning(f"Invalid command in scene: {cmd}")
                    success = False
                    continue

                # Get device from registry
                device = device_registry.get_device(device_id)
                if not device:
                    logger.warning(f"Device not found: {device_id}")
                    success = False
                    continue

                # Execute command
                cmd_success = await device.execute_command(command, params)
                if not cmd_success:
                    logger.warning(
                        f"Failed to execute command {command} on device {device.name}"
                    )
                    success = False

            return success

        except Exception as e:
            logger.error(f"Error activating scene: {e}")
            return False


class WebhookAction(Action):
    """Action that sends a webhook request."""

    action_type = "webhook"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url")
        self.method = config.get("method", "POST")
        self.headers = config.get("headers", {})
        self.body = config.get("body", {})
        self.timeout = config.get("timeout", 10)

    async def execute(self, context: Dict[str, Any]) -> bool:
        """Send a webhook request."""
        if not self.url:
            logger.error("Missing URL in WebhookAction")
            return False

        try:
            # Resolve body template
            body = self._resolve_template(self.body, context)

            # Send request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.request(
                    method=self.method,
                    url=self.url,
                    headers=self.headers,
                    json=body,
                    timeout=self.timeout,
                ),
            )

            # Check response
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Webhook request successful: {response.status_code}")
                return True
            else:
                logger.warning(
                    f"Webhook request failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error sending webhook request: {e}")
            return False

    def _resolve_template(
        self, template: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve template with variables from context."""
        if not template:
            return {}

        # Convert to JSON and back to handle nested structures
        template_str = json.dumps(template)

        # Replace variables in format ${variable_name}
        import re

        for match in re.finditer(r"\${([^}]+)}", template_str):
            var_name = match.group(1)
            var_value = self._get_nested_value(context, var_name)
            if var_value is not None:
                # Convert value to JSON string
                value_str = json.dumps(var_value)
                # Remove quotes for numeric and boolean values
                if value_str.startswith('"') and value_str.endswith('"'):
                    pass  # Keep quotes for strings
                template_str = template_str.replace(match.group(0), value_str)

        # Convert back to dictionary
        try:
            return json.loads(template_str)
        except json.JSONDecodeError:
            logger.error(f"Error parsing template: {template_str}")
            return {}

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        parts = path.split(".")
        value = data

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return value


class ConditionAction(Action):
    """Action that executes different actions based on a condition."""

    action_type = "condition"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Create condition
        from .conditions import create_condition

        condition_config = config.get("condition", {})
        condition_type = condition_config.get("type")
        self.condition = create_condition(
            condition_type, condition_config.get("config", {})
        )

        # Create then actions
        self.then_actions = []
        for action_config in config.get("then_actions", []):
            action_type = action_config.get("type")
            action = create_action(action_type, action_config.get("config", {}))
            if action:
                self.then_actions.append(action)

        # Create else actions
        self.else_actions = []
        for action_config in config.get("else_actions", []):
            action_type = action_config.get("type")
            action = create_action(action_type, action_config.get("config", {}))
            if action:
                self.else_actions.append(action)

    async def execute(self, context: Dict[str, Any]) -> bool:
        """Execute actions based on condition."""
        if not self.condition:
            logger.error("Missing condition in ConditionAction")
            return False

        try:
            # Evaluate condition
            result = await self.condition.evaluate(context)

            # Execute actions based on condition result
            if result:
                # Execute then actions
                success = True
                for action in self.then_actions:
                    action_success = await action.execute(context)
                    if not action_success:
                        success = False
                return success
            else:
                # Execute else actions
                success = True
                for action in self.else_actions:
                    action_success = await action.execute(context)
                    if not action_success:
                        success = False
                return success

        except Exception as e:
            logger.error(f"Error executing conditional action: {e}")
            return False


# Factory function to create actions
def create_action(action_type: str, config: Dict[str, Any]) -> Optional[Action]:
    """Create an action instance based on type and configuration."""
    action_classes = {
        "device_command": DeviceCommandAction,
        "delay": DelayAction,
        "notification": NotificationAction,
        "scene": SceneAction,
        "webhook": WebhookAction,
        "condition": ConditionAction,
    }

    if action_type not in action_classes:
        logger.error(f"Unknown action type: {action_type}")
        return None

    try:
        return action_classes[action_type](config)
    except Exception as e:
        logger.error(f"Error creating action of type {action_type}: {e}")
        return None
