# backend/src/automation/engine.py

"""
Violt Core Lite - Automation Engine

This module implements the core automation engine for evaluating rules and executing actions.
"""
from typing import Dict, List, Any, Optional, Set, Callable, Coroutine
import logging
import asyncio
import uuid
from datetime import datetime, timedelta
import time
import json
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import AutomationRule, Trigger, Condition, Action, AutomationError
from .triggers import create_trigger
from .conditions import create_condition
from .actions import create_action
from ..devices.registry import registry as device_registry
from ..database.models import (
    Automation,
    Event,
    User,
)  # Import User if needed for context
from ..database.session import (
    AsyncSessionLocal,
)  # Use the session factory directly for background tasks
from ..core.config import settings
from ..core.websocket import manager as websocket_manager  # Import websocket manager

# Use standard logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """Provide an async database session for background tasks."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class AutomationEngine:
    """Main automation engine for evaluating rules and executing actions."""

    def __init__(self):
        self.rules: Dict[str, AutomationRule] = {}  # Store rules keyed by ID (string)
        self.running = False
        self.check_interval = (
            settings.AUTOMATION_CHECK_INTERVAL
        )  # Use interval from settings
        self.worker_task: Optional[asyncio.Task] = None
        self.event_processor_task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()  # Protect access to self.rules
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.event_handlers: List[Callable[[Dict[str, Any]], Coroutine]] = (
            []
        )  # Handlers are now async

    async def start(self):
        """Start the automation engine."""
        if self.running:
            logger.warning("Automation engine is already running")
            return

        logger.info("Starting automation engine...")
        self.running = True

        # Load rules from database
        await self.load_rules_from_db()

        # Start worker task for periodic checks (time, interval triggers)
        self.worker_task = asyncio.create_task(
            self._worker_loop(), name="AutomationWorkerLoop"
        )

        # Start event processor task for event-based triggers
        self.event_processor_task = asyncio.create_task(
            self._event_processor(), name="AutomationEventProcessor"
        )

        logger.info(
            f"Automation engine started with {len(self.rules)} rules. Check interval: {self.check_interval}s"
        )

    async def stop(self):
        """Stop the automation engine."""
        if not self.running:
            logger.warning("Automation engine is not running")
            return

        logger.info("Stopping automation engine...")
        self.running = False

        # Signal event queue to stop
        await self.event_queue.put(None)  # Sentinel value to stop processor

        # Cancel worker task
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                logger.info("Automation worker loop cancelled.")
            except Exception as e:
                logger.error(
                    f"Error during worker task cancellation: {e}", exc_info=True
                )
            self.worker_task = None

        # Cancel event processor task
        if self.event_processor_task and not self.event_processor_task.done():
            self.event_processor_task.cancel()
            try:
                await self.event_processor_task
            except asyncio.CancelledError:
                logger.info("Automation event processor cancelled.")
            except Exception as e:
                logger.error(
                    f"Error during event processor cancellation: {e}", exc_info=True
                )
            self.event_processor_task = None

        # Clear rules (optional, depends if state needs to be preserved)
        async with self.lock:
            self.rules.clear()

        logger.info("Automation engine stopped.")

    async def load_rules_from_db(self):
        """Load automation rules from the database."""
        logger.info("Loading automation rules from database...")
        loaded_count = 0
        failed_count = 0
        rules_to_add = {}
        try:
            async with get_db_session() as db:  # Use async session context manager
                # Query all automations (consider filtering by enabled if desired)
                result = await db.execute(
                    select(Automation)
                )  # Load all, handle enabled status in engine
                automations = result.scalars().all()

                # Create rules from automations
                for automation in automations:
                    try:
                        rule = await self._create_rule_from_automation(automation)
                        if rule:
                            rules_to_add[rule.id] = rule
                            loaded_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(
                            f"Error creating rule from automation {automation.id}: {e}",
                            exc_info=True,
                        )
                        failed_count += 1

            # Update the engine's rules atomically
            async with self.lock:
                self.rules = rules_to_add

            logger.info(
                f"Loaded {loaded_count} rules from database. Failed to load: {failed_count}"
            )

        except Exception as e:
            logger.error(f"Error loading rules from database: {e}", exc_info=True)

    async def _create_rule_from_automation(
        self, automation: Automation
    ) -> Optional[AutomationRule]:
        """Create an AutomationRule object from the database model."""
        try:
            # Ensure config fields are dictionaries
            trigger_config = automation.trigger_config or {}
            conditions = automation.conditions or []
            actions = automation.actions or []

            # Create trigger
            trigger = create_trigger(automation.trigger_type, trigger_config)
            if not trigger:
                logger.error(
                    f"Failed to create trigger type '{automation.trigger_type}' for automation {automation.id}"
                )
                return None

            # Create conditions
            condition_objects = []
            for condition_config in conditions:
                cond_type = condition_config.get("type")
                cond_conf = condition_config.get("config", {})
                if cond_type:
                    condition = create_condition(cond_type, cond_conf)
                    if condition:
                        condition_objects.append(condition)
                    else:
                        logger.warning(
                            f"Failed to create condition type '{cond_type}' for automation {automation.id}"
                        )
                else:
                    logger.warning(
                        f"Condition missing 'type' in automation {automation.id}: {condition_config}"
                    )

            # Create actions
            action_objects = []
            for action_config in actions:
                act_type = action_config.get("type")
                act_conf = action_config.get("config", {})
                if act_type:
                    action = create_action(act_type, act_conf)
                    if action:
                        action_objects.append(action)
                    else:
                        logger.warning(
                            f"Failed to create action type '{act_type}' for automation {automation.id}"
                        )
                else:
                    logger.warning(
                        f"Action missing 'type' in automation {automation.id}: {action_config}"
                    )

            if not action_objects:
                logger.error(
                    f"No valid actions found for automation {automation.id}. Skipping rule creation."
                )
                return None

            # Create rule instance
            rule = AutomationRule(
                automation_id=str(automation.id),
                name=automation.name,
                trigger=trigger,
                actions=action_objects,
                conditions=condition_objects,
                condition_type=automation.condition_type or "and",  # Default to 'and'
                enabled=automation.enabled,
            )
            # Restore stateful info if needed (e.g., last triggered times from DB)
            rule.last_triggered = automation.last_triggered
            rule.execution_count = automation.execution_count

            return rule

        except Exception as e:
            logger.error(
                f"Error creating rule instance for automation {automation.id}: {e}",
                exc_info=True,
            )
            return None

    async def add_rule(self, rule: AutomationRule) -> bool:
        """Add a rule to the engine (thread-safe)."""
        if not rule or not isinstance(rule, AutomationRule):
            logger.error("Attempted to add invalid rule object.")
            return False

        async with self.lock:
            if rule.id in self.rules:
                logger.warning(
                    f"Rule {rule.id} already exists. Use update_rule instead."
                )
                # Optionally update if preferred behavior
                # self.rules[rule.id] = rule
                return False
            self.rules[rule.id] = rule
            logger.info(f"Added rule to engine: {rule.name} ({rule.id})")

        return True

    async def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the engine (thread-safe)."""
        async with self.lock:
            if rule_id in self.rules:
                removed_rule = self.rules.pop(rule_id)
                logger.info(
                    f"Removed rule from engine: {removed_rule.name} ({rule_id})"
                )
                return True
            else:
                logger.warning(f"Rule {rule_id} not found in engine for removal.")
                return False

    async def update_rule(self, rule: AutomationRule) -> bool:
        """Update an existing rule in the engine (thread-safe)."""
        if not rule or not isinstance(rule, AutomationRule):
            logger.error("Attempted to update with invalid rule object.")
            return False

        async with self.lock:
            if rule.id in self.rules:
                self.rules[rule.id] = rule
                logger.info(f"Updated rule in engine: {rule.name} ({rule.id})")
                return True
            else:
                # Optionally add if not found, or return False
                logger.warning(f"Rule {rule.id} not found for update. Adding instead.")
                self.rules[rule.id] = rule
                return True  # Or return False depending on desired behavior

    async def get_rule(self, rule_id: str) -> Optional[AutomationRule]:
        """Get a rule by ID (thread-safe)."""
        async with self.lock:
            return self.rules.get(rule_id)

    async def get_rules(self) -> List[AutomationRule]:
        """Get all active rules (thread-safe)."""
        async with self.lock:
            return list(self.rules.values())

    async def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule in the engine (thread-safe)."""
        async with self.lock:
            rule = self.rules.get(rule_id)
            if rule:
                if not rule.enabled:
                    rule.enabled = True
                    logger.info(f"Enabled rule in engine: {rule.name} ({rule_id})")
                return True
            else:
                logger.warning(f"Rule {rule_id} not found in engine for enabling.")
                return False

    async def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule in the engine (thread-safe)."""
        async with self.lock:
            rule = self.rules.get(rule_id)
            if rule:
                if rule.enabled:
                    rule.enabled = False
                    logger.info(f"Disabled rule in engine: {rule.name} ({rule_id})")
                return True
            else:
                logger.warning(f"Rule {rule_id} not found in engine for disabling.")
                return False

    async def process_event(self, event_data: Dict[str, Any]):
        """Add an event to the processing queue."""
        if not self.running:
            logger.warning("Automation engine not running, cannot process event.")
            return
        if not event_data or not isinstance(event_data, dict):
            logger.error(f"Invalid event data received: {event_data}")
            return

        await self.event_queue.put(event_data)
        logger.debug(f"Event added to queue: {event_data.get('type')}")

    async def _execute_rule(self, rule: AutomationRule, context: Dict[str, Any]):
        """Helper method to execute a single rule's actions if conditions met."""
        try:
            conditions_met = await rule.evaluate_conditions(context)
            if conditions_met:
                logger.info(
                    f"Conditions met for automation '{rule.name}'. Executing actions..."
                )
                action_success = await rule.execute_actions(context)

                # Log trigger event to DB after successful execution
                try:
                    async with get_db_session() as db:
                        # Find the user_id associated with this rule
                        automation_db = await db.get(Automation, uuid.UUID(rule.id))
                        user_id = automation_db.user_id if automation_db else None

                        if user_id:
                            event = Event(
                                type="automation_triggered",
                                source="engine",
                                data={
                                    "automation_id": rule.id,
                                    "automation_name": rule.name,
                                    "success": action_success,
                                    "context": context.get("event", {}),
                                },
                                # Maybe associate event with user? Needs schema change.
                            )
                            db.add(event)
                            # Update execution count and last triggered time in DB
                            if automation_db:
                                automation_db.last_triggered = rule.last_triggered
                                automation_db.execution_count = rule.execution_count
                                # Commit happens within get_db_session context

                            # Send WebSocket notification
                            await websocket_manager.send_personal_message(
                                {
                                    "type": "automation_triggered",
                                    "automation_id": rule.id,
                                    "success": action_success,
                                },
                                user_id,
                                "automations",
                            )

                        else:
                            logger.warning(
                                f"Could not find user_id for automation {rule.id} to log trigger event."
                            )

                except Exception as db_err:
                    logger.error(
                        f"Error logging automation trigger event or updating stats for {rule.name}: {db_err}",
                        exc_info=True,
                    )

            else:
                logger.debug(f"Conditions not met for automation '{rule.name}'.")
        except Exception as e:
            logger.error(
                f"Error during action execution for rule '{rule.name}': {e}",
                exc_info=True,
            )

    async def _event_processor(self):
        """Process events from the queue (for event-based triggers)."""
        logger.info("Automation event processor started.")
        while self.running:
            try:
                event_data = await self.event_queue.get()
                if event_data is None:  # Sentinel value check
                    logger.info("Event processor received stop signal.")
                    break

                logger.debug(f"Processing event: {event_data.get('type')}")
                context = {"event": event_data, "timestamp": datetime.now(datetime.timezone.utc)}

                # Get relevant rules (event triggers, enabled)
                rules_to_check = []
                async with self.lock:
                    for rule in self.rules.values():
                        # Check if rule is enabled and uses an event trigger
                        if rule.enabled and rule.trigger.trigger_type == "event":
                            # Perform a preliminary check if the trigger *might* match the event type
                            # This avoids evaluating every single event trigger for every event
                            if (
                                hasattr(rule.trigger, "event_type")
                                and rule.trigger.event_type
                                and rule.trigger.event_type == event_data.get("type")
                            ):
                                rules_to_check.append(rule)
                            elif (
                                not hasattr(rule.trigger, "event_type")
                                or not rule.trigger.event_type
                            ):
                                # If trigger doesn't specify an event type, check it always
                                rules_to_check.append(rule)

                # Check triggers and execute if matched
                if rules_to_check:
                    logger.debug(
                        f"Checking {len(rules_to_check)} event triggers for event type '{event_data.get('type')}'"
                    )
                for rule in rules_to_check:
                    try:
                        if await rule.check_trigger(context):
                            logger.info(
                                f"Event trigger matched for automation '{rule.name}'. Evaluating conditions..."
                            )
                            await self._execute_rule(
                                rule, context
                            )  # Evaluate conditions & execute actions
                    except Exception as e:
                        logger.error(
                            f"Error processing event trigger for rule {rule.name}: {e}",
                            exc_info=True,
                        )

                # Notify external event handlers (if any)
                if self.event_handlers:
                    # Use asyncio.gather for concurrent handler execution
                    await asyncio.gather(
                        *(handler(event_data) for handler in self.event_handlers),
                        return_exceptions=True,  # Log errors from handlers but don't stop processor
                    )

                self.event_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Event processor task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in event processor loop: {e}", exc_info=True)
                # Avoid busy-looping on persistent errors
                await asyncio.sleep(1)
        logger.info("Automation event processor stopped.")

    async def _worker_loop(self):
        """Main worker loop for checking time-based and interval-based triggers."""
        logger.info("Automation worker loop started.")
        while self.running:
            start_time = time.monotonic()
            try:
                current_dt = (
                    datetime.now()
                )  # Use datetime.now() for local time checks in triggers
                context = {
                    "timestamp": datetime.now(datetime.timezone.utc),
                    "current_time_local": current_dt,
                }  # Provide both UTC and local time context

                # Get relevant rules (non-event triggers, enabled)
                rules_to_check: List[AutomationRule] = []
                async with self.lock:
                    # Use list comprehension for slightly better performance
                    rules_to_check = [
                        rule
                        for rule in self.rules.values()
                        if rule.enabled and rule.trigger.trigger_type != "event"
                    ]

                if rules_to_check:
                    logger.debug(
                        f"Checking {len(rules_to_check)} time/interval triggers..."
                    )

                # Check triggers and execute if matched
                # Use asyncio.gather to check triggers somewhat concurrently
                trigger_checks = [
                    rule.check_trigger(context) for rule in rules_to_check
                ]
                results = await asyncio.gather(*trigger_checks, return_exceptions=True)

                for i, result in enumerate(results):
                    rule = rules_to_check[i]
                    if isinstance(result, Exception):
                        logger.error(
                            f"Error checking trigger for rule {rule.name}: {result}",
                            exc_info=result,
                        )
                    elif result:  # Trigger condition met
                        logger.info(
                            f"{rule.trigger.trigger_type.capitalize()} trigger matched for automation '{rule.name}'. Evaluating conditions..."
                        )
                        # Execute the rule (conditions + actions) in a separate task
                        # This prevents one long-running rule execution from blocking others
                        asyncio.create_task(self._execute_rule(rule, context))

            except asyncio.CancelledError:
                logger.info("Worker loop task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in automation worker loop: {e}", exc_info=True)

            # Calculate sleep time ensuring checks happen close to the interval
            elapsed_time = time.monotonic() - start_time
            sleep_duration = max(
                0.1, self.check_interval - elapsed_time
            )  # Sleep at least 0.1s
            await asyncio.sleep(sleep_duration)
        logger.info("Automation worker loop stopped.")

    async def register_event_handler(
        self, handler: Callable[[Dict[str, Any]], Coroutine]
    ):
        """Register an async handler for processed events."""
        if not asyncio.iscoroutinefunction(handler):
            logger.error("Event handler must be an async function.")
            return
        if handler not in self.event_handlers:
            self.event_handlers.append(handler)
            logger.info(f"Registered event handler: {handler.__name__}")

    async def unregister_event_handler(
        self, handler: Callable[[Dict[str, Any]], Coroutine]
    ):
        """Unregister an event handler."""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
            logger.info(f"Unregistered event handler: {handler.__name__}")

    async def trigger_automation_manually(
        self, rule_id: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Manually trigger an automation, bypassing its trigger check but evaluating conditions."""
        rule = await self.get_rule(rule_id)
        if not rule:
            logger.error(f"Cannot manually trigger rule {rule_id}: Not found.")
            return False
        if not rule.enabled:
            logger.warning(f"Cannot manually trigger rule {rule_id}: Disabled.")
            # Optionally allow triggering disabled rules?
            # return False

        execution_context = context or {}
        execution_context.setdefault("timestamp", datetime.now(datetime.timezone.utc))
        execution_context.setdefault("trigger_type", "manual")

        logger.info(
            f"Manually triggering automation '{rule.name}' ({rule_id}). Evaluating conditions..."
        )
        await self._execute_rule(
            rule, execution_context
        )  # Evaluate conditions & execute actions
        return True  # Indicate the trigger attempt was made


# --- Global Engine Instance ---
# It's generally better practice to create the engine instance within the application's
# startup/lifespan context manager rather than as a global variable at module level.
# However, for simplicity in this structure, we keep it here.
# Ensure it's started appropriately in your main application startup (`startup.py`).
engine = AutomationEngine()


# --- Helper functions (moved from router, potentially belong elsewhere like a crud module) ---

# Functions like `create_rule_from_config` and `save_rule_to_db` might be better
# placed in a dedicated module for managing automation configurations or within
# the API router itself if they are only used there.
# Keeping them here for now as they relate closely to the engine's rule structure.


async def create_rule_from_config(config: Dict[str, Any]) -> Optional[AutomationRule]:
    """Create an AutomationRule object from a configuration dictionary."""
    try:
        # Validate required fields
        rule_id = config.get("id", str(uuid.uuid4()))
        name = config.get("name")
        if not name:
            raise ValueError("Rule name is required.")

        # Create trigger
        trigger_config = config.get("trigger", {})
        trigger_type = trigger_config.get("type")
        if not trigger_type:
            raise ValueError("Trigger type is required.")
        trigger = create_trigger(trigger_type, trigger_config.get("config", {}))
        if not trigger:
            raise ValueError(f"Failed to create trigger type '{trigger_type}'.")

        # Create conditions
        conditions = []
        for condition_config in config.get("conditions", []):
            cond_type = condition_config.get("type")
            if not cond_type:
                raise ValueError("Condition type is required.")
            condition = create_condition(cond_type, condition_config.get("config", {}))
            if not condition:
                raise ValueError(f"Failed to create condition type '{cond_type}'.")
            conditions.append(condition)

        # Create actions
        actions = []
        action_configs = config.get("actions", [])
        if not action_configs:
            raise ValueError("At least one action is required.")
        for action_config in action_configs:
            act_type = action_config.get("type")
            if not act_type:
                raise ValueError("Action type is required.")
            action = create_action(act_type, action_config.get("config", {}))
            if not action:
                raise ValueError(f"Failed to create action type '{act_type}'.")
            actions.append(action)

        # Create rule instance
        rule = AutomationRule(
            automation_id=str(rule_id),  # Ensure ID is string
            name=name,
            trigger=trigger,
            actions=actions,
            conditions=conditions,
            condition_type=config.get("condition_type", "and"),
            enabled=config.get("enabled", True),
        )
        return rule

    except Exception as e:
        logger.error(f"Error creating rule from config: {e}", exc_info=True)
        return None


async def save_rule_to_db(rule: AutomationRule, user_id: str) -> bool:
    """Save an automation rule to the database (Create or Update)."""
    if not rule or not user_id:
        return False
    try:
        async with get_db_session() as db:
            automation_uuid = uuid.UUID(rule.id)
            existing = await db.get(
                Automation, str(automation_uuid)
            )  # Fetch existing by primary key

            # Prepare config data (Ensure it's JSON serializable)
            trigger_conf = (
                rule.trigger.config if hasattr(rule.trigger, "config") else {}
            )
            cond_conf = (
                [
                    {"type": c.condition_type, "config": c.config}
                    for c in rule.conditions
                ]
                if rule.conditions
                else []
            )
            act_conf = [
                {"type": a.action_type, "config": a.config} for a in rule.actions
            ]

            if existing:
                # Update existing automation
                if existing.user_id != user_id:
                    logger.error(
                        f"User {user_id} attempting to save automation {rule.id} owned by {existing.user_id}"
                    )
                    return False  # Or raise Forbidden

                existing.name = rule.name
                existing.description = getattr(
                    rule, "description", None
                )  # Add description if available
                existing.enabled = rule.enabled
                existing.trigger_type = rule.trigger.trigger_type
                existing.trigger_config = trigger_conf
                existing.condition_type = rule.condition_type
                existing.conditions = cond_conf
                existing.action_type = (
                    rule.actions[0].action_type if rule.actions else "unknown"
                )  # Or derive differently
                existing.actions = act_conf
                existing.last_modified = datetime.now(tz=datetime.timezone.utc)
                # Don't overwrite execution count/last triggered unless explicitly intended
            else:
                # Create new automation
                automation_db = Automation(
                    id=str(automation_uuid),
                    user_id=user_id,
                    name=rule.name,
                    description=getattr(rule, "description", None),
                    enabled=rule.enabled,
                    trigger_type=rule.trigger.trigger_type,
                    trigger_config=trigger_conf,
                    condition_type=rule.condition_type,
                    conditions=cond_conf,
                    action_type=(
                        rule.actions[0].action_type if rule.actions else "unknown"
                    ),
                    actions=act_conf,
                    execution_count=0,
                    last_modified=datetime.now(tz=datetime.timezone.utc),
                    created_at=datetime.now(tz=datetime.timezone.utc),
                )
                db.add(automation_db)
            # Commit happens automatically via asynccontextmanager

        return True
    except Exception as e:
        logger.error(f"Error saving rule {rule.id} to database: {e}", exc_info=True)
        return False
