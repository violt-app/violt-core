# backend/src/api/automations/router.py

"""
Violt Core Lite - API Router for Automations

This module handles automation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete as sql_delete
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid
import json  # Needed for potential JSON operations on config

from ...core.schemas import (
    AutomationCreate,
    AutomationUpdate,
    AutomationResponse,
    EventResponse,  # Assuming EventResponse is defined in schemas
)
from ...core.auth import get_current_active_user
from ...database.session import get_db
from ...database.models import Automation, User, Event

# Placeholder for the automation engine and WebSocket manager
# These would be properly imported in a full implementation
from ...automation.engine import (
    engine as automation_engine,
    create_rule_from_config,
    save_rule_to_db,
)
from ...core.websocket import manager as websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# Helper function (consider moving to a crud utility module)
async def get_automation_by_id(
    db: AsyncSession, automation_id: str, user_id: str
) -> Automation:
    """Get an automation by ID and verify ownership."""
    # Convert string ID to UUID if your model uses UUID type
    try:
        automation_uuid = uuid.UUID(automation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid automation ID format.",
        )

    result = await db.execute(
        select(Automation).where(
            Automation.id
            == str(
                automation_uuid
            ),  # Compare with string representation if ID is String in model
            Automation.user_id == user_id,
        )
    )
    automation = result.scalars().first()

    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Automation not found"
        )

    return automation


async def log_event(
    db: AsyncSession,
    event_type: str,
    source: str,
    data: Dict[str, Any],
    automation_id: Optional[str] = None,  # Add automation_id if relevant
    device_id: Optional[str] = None,
):
    """Helper to create and log an event."""
    event = Event(
        type=event_type,
        source=source,
        data=data,
        device_id=device_id,
        # Consider adding automation_id to the Event model if needed often
    )
    db.add(event)
    try:
        await db.commit()
        # Optionally notify via websockets here if needed for events
        # Find user_id associated with the automation/device to send targeted ws message
        # await websocket_manager.send_personal_message(...)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to log event {event_type}: {e}")


@router.get("/", response_model=List[AutomationResponse])
async def list_automations(
    enabled: Optional[bool] = None,
    trigger_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all automations for the current user with optional filtering."""
    query = select(Automation).where(Automation.user_id == current_user.id)

    # Apply filters if provided
    if enabled is not None:
        query = query.where(Automation.enabled == enabled)
    if trigger_type:
        # Ensure case-insensitive comparison if needed, or adjust based on stored values
        query = query.where(Automation.trigger_type == trigger_type)

    result = await db.execute(query.order_by(Automation.name))  # Order by name
    automations = result.scalars().all()

    return automations


@router.post(
    "/", response_model=AutomationResponse, status_code=status.HTTP_201_CREATED
)
async def create_automation(
    automation_data: AutomationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new automation."""
    automation_id = str(uuid.uuid4())

    # Basic validation (more complex validation might happen in automation_engine)
    if not automation_data.actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automation must have at least one action.",
        )

    # Create new automation model instance
    new_automation_db = Automation(
        id=automation_id,
        user_id=current_user.id,
        name=automation_data.name,
        description=automation_data.description,
        enabled=automation_data.enabled,
        trigger_type=automation_data.trigger_type,
        trigger_config=automation_data.trigger_config,
        condition_type=automation_data.condition_type,
        conditions=automation_data.conditions,
        action_type=automation_data.action_type,  # Note: action_type might be redundant if actions list exists
        actions=automation_data.actions,
        execution_count=0,
        last_modified=datetime.now(datetime.timezone.utc),  # Set initial last_modified
        created_at=datetime.now(datetime.timezone.utc),  # Explicitly set created_at
    )

    db.add(new_automation_db)

    # Attempt to create the rule in the engine
    rule_config = {
        "id": automation_id,
        "name": automation_data.name,
        "trigger": {
            "type": automation_data.trigger_type,
            "config": automation_data.trigger_config,
        },
        "condition_type": automation_data.condition_type,
        "conditions": automation_data.conditions,
        "actions": automation_data.actions,
        "enabled": automation_data.enabled,
    }
    rule = await create_rule_from_config(rule_config)
    if not rule:
        await db.rollback()  # Rollback DB change if engine rule creation fails
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid automation configuration for the engine.",
        )

    # Add rule to the engine's active rules
    engine_add_success = await automation_engine.add_rule(rule)
    if not engine_add_success:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add rule to automation engine.",
        )

    # Commit to DB
    try:
        await db.commit()
        await db.refresh(new_automation_db)
    except Exception as e:
        await db.rollback()
        # Also remove from engine if DB commit fails
        await automation_engine.remove_rule(automation_id)
        logger.error(f"Database error creating automation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save automation to database.",
        )

    # Log event
    await log_event(
        db,
        event_type="automation_added",
        source="api",
        data={
            "automation_id": new_automation_db.id,
            "automation_name": new_automation_db.name,
        },
        # automation_id=new_automation_db.id # Add if field exists in Event model
    )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {
            "type": "automation_added",
            "automation": AutomationResponse.model_validate(
                new_automation_db
            ).model_dump(),
        },
        current_user.id,
        "automations",
    )

    logger.info(
        f"Automation created: {new_automation_db.id} - {new_automation_db.name}"
    )
    return new_automation_db


@router.get("/{automation_id}", response_model=AutomationResponse)
async def get_automation(
    automation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get automation details by ID."""
    automation = await get_automation_by_id(db, automation_id, current_user.id)
    return automation


@router.put("/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: str,
    automation_data: AutomationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing automation."""
    automation_db = await get_automation_by_id(db, automation_id, current_user.id)
    update_occurred = False
    engine_update_needed = False

    # Prepare update data, excluding fields not set in the request
    update_dict = automation_data.model_dump(exclude_unset=True)

    # Update automation fields in the DB model
    for key, value in update_dict.items():
        if hasattr(automation_db, key) and getattr(automation_db, key) != value:
            setattr(automation_db, key, value)
            update_occurred = True
            # Mark if engine needs update (e.g., trigger, conditions, actions changed)
            if key in [
                "trigger_type",
                "trigger_config",
                "condition_type",
                "conditions",
                "action_type",
                "actions",
                "enabled",
            ]:
                engine_update_needed = True

    if not update_occurred:
        logger.info(f"No changes detected for automation update: {automation_id}")
        return automation_db  # Return existing data if no changes

    automation_db.last_modified = datetime.now(datetime.timezone.utc)

    # If engine needs update, create the new rule configuration
    if engine_update_needed:
        rule_config = {
            "id": automation_db.id,
            "name": automation_db.name,
            "trigger": {
                "type": automation_db.trigger_type,
                "config": automation_db.trigger_config,
            },
            "condition_type": automation_db.condition_type,
            "conditions": automation_db.conditions,
            "actions": automation_db.actions,
            "enabled": automation_db.enabled,
        }
        new_rule = await create_rule_from_config(rule_config)
        if not new_rule:
            # Don't rollback DB change yet, maybe just log a warning or prevent specific engine-related updates
            logger.error(
                f"Failed to create updated rule config for engine: {automation_id}"
            )
            # Optionally raise HTTPException if engine update is critical
            # raise HTTPException(status_code=400, detail="Invalid configuration for automation engine update.")
            engine_update_needed = False  # Skip engine update if config is invalid
        else:
            # Attempt to update the rule in the engine *before* committing DB changes
            engine_update_success = await automation_engine.update_rule(new_rule)
            if not engine_update_success:
                # This case is tricky - rule might not exist in engine if it was disabled/failed previously
                # Maybe try adding it instead? Or log a warning.
                logger.warning(
                    f"Failed to update rule {automation_id} in engine (might not exist or error occurred)."
                )
                # Decide if this should prevent the DB update

    # Commit DB changes
    try:
        await db.commit()
        await db.refresh(automation_db)
    except Exception as e:
        await db.rollback()
        # If DB commit fails after a successful engine update, we have inconsistency.
        # Attempt to revert the engine change if possible, or log severe warning.
        # Reverting might be complex if the old rule state isn't stored.
        logger.error(
            f"Database error updating automation {automation_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update automation in database.",
        )

    # Log event
    await log_event(
        db,
        event_type="automation_updated",
        source="api",
        data={
            "automation_id": automation_db.id,
            "automation_name": automation_db.name,
            "updated_fields": list(update_dict.keys()),
        },
        # automation_id=automation_db.id
    )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {
            "type": "automation_updated",
            "automation": AutomationResponse.model_validate(automation_db).model_dump(),
        },
        current_user.id,
        "automations",
    )

    logger.info(f"Automation updated: {automation_db.id} - {automation_db.name}")
    return automation_db


@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an automation."""
    automation = await get_automation_by_id(db, automation_id, current_user.id)
    automation_name = automation.name  # Store before deletion

    # Remove from engine first
    engine_remove_success = await automation_engine.remove_rule(automation_id)
    if not engine_remove_success:
        # Log warning if it wasn't found in the engine (might have been disabled/failed)
        logger.warning(f"Rule {automation_id} not found in engine during deletion.")

    # Log deletion event
    await log_event(
        db,
        event_type="automation_deleted",
        source="api",
        data={"automation_id": automation_id, "automation_name": automation_name},
        # automation_id=automation_id
    )

    # Delete from DB
    try:
        # Delete related history events if desired (or handle via cascade)
        # await db.execute(sql_delete(Event).where(Event.data["automation_id"].astext == automation_id)) # Example if storing ID in data
        await db.delete(automation)
        await db.commit()
    except Exception as e:
        await db.rollback()
        # If DB delete fails after engine remove, we have inconsistency. Log severe warning.
        # Maybe try to re-add to engine? Complex.
        logger.error(
            f"Database error deleting automation {automation_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete automation from database.",
        )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {"type": "automation_removed", "automation_id": automation_id},
        current_user.id,
        "automations",
    )

    logger.info(f"Automation deleted: {automation_id}")
    # No return for 204


@router.put("/{automation_id}/enable", response_model=AutomationResponse)
async def enable_automation(
    automation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Enable an automation."""
    automation_db = await get_automation_by_id(db, automation_id, current_user.id)

    if automation_db.enabled:
        return automation_db  # Already enabled

    automation_db.enabled = True
    automation_db.last_modified = datetime.utcnow()

    # Enable in engine
    engine_enable_success = await automation_engine.enable_rule(automation_id)
    if not engine_enable_success:
        # Rule might not be loaded in engine if it wasn't before, try adding it
        logger.warning(
            f"Rule {automation_id} not found in engine to enable, attempting to add."
        )
        rule_config = {  # Recreate config from DB model
            "id": automation_db.id,
            "name": automation_db.name,
            "trigger": {
                "type": automation_db.trigger_type,
                "config": automation_db.trigger_config,
            },
            "condition_type": automation_db.condition_type,
            "conditions": automation_db.conditions,
            "actions": automation_db.actions,
            "enabled": True,
        }
        rule = await create_rule_from_config(rule_config)
        if rule:
            await automation_engine.add_rule(rule)
        else:
            # If rule creation fails, we can't enable it in the engine. Rollback DB?
            automation_db.enabled = False  # Revert DB state change
            logger.error(
                f"Failed to create rule config for enabling automation {automation_id}"
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to enable rule in engine due to config error.",
            )

    # Commit DB change
    try:
        await db.commit()
        await db.refresh(automation_db)
    except Exception as e:
        await db.rollback()
        # Attempt to disable in engine again if DB commit failed
        await automation_engine.disable_rule(automation_id)
        logger.error(
            f"Database error enabling automation {automation_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to save enabled state.")

    # Log event
    await log_event(
        db,
        event_type="automation_enabled",
        source="api",
        data={"automation_id": automation_db.id, "automation_name": automation_db.name},
        # automation_id=automation_db.id
    )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {
            "type": "automation_updated",
            "automation": AutomationResponse.model_validate(automation_db).model_dump(),
        },
        current_user.id,
        "automations",
    )

    logger.info(f"Automation enabled: {automation_db.id} - {automation_db.name}")
    return automation_db


@router.put("/{automation_id}/disable", response_model=AutomationResponse)
async def disable_automation(
    automation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Disable an automation."""
    automation_db = await get_automation_by_id(db, automation_id, current_user.id)

    if not automation_db.enabled:
        return automation_db  # Already disabled

    automation_db.enabled = False
    automation_db.last_modified = datetime.utcnow()

    # Disable in engine
    engine_disable_success = await automation_engine.disable_rule(automation_id)
    if not engine_disable_success:
        # Log warning, but proceed with DB update as the rule might already be gone from engine
        logger.warning(f"Rule {automation_id} not found in engine to disable.")

    # Commit DB change
    try:
        await db.commit()
        await db.refresh(automation_db)
    except Exception as e:
        await db.rollback()
        # Attempt to re-enable in engine if DB commit fails? Complex.
        logger.error(
            f"Database error disabling automation {automation_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to save disabled state.")

    # Log event
    await log_event(
        db,
        event_type="automation_disabled",
        source="api",
        data={"automation_id": automation_db.id, "automation_name": automation_db.name},
        # automation_id=automation_db.id
    )

    # Send WebSocket update
    await websocket_manager.send_personal_message(
        {
            "type": "automation_updated",
            "automation": AutomationResponse.model_validate(automation_db).model_dump(),
        },
        current_user.id,
        "automations",
    )

    logger.info(f"Automation disabled: {automation_db.id} - {automation_db.name}")
    return automation_db


@router.get(
    "/{automation_id}/history", response_model=List[EventResponse]
)  # Reuse EventResponse
async def get_automation_history(
    automation_id: str,
    limit: int = Query(20, ge=1, le=200),  # Increased default/max limit
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get automation execution history (logged as events)."""
    # Verify automation exists and belongs to user
    await get_automation_by_id(
        db, automation_id, current_user.id
    )  # Ensure automation exists

    # Query events related to this automation's triggering
    # This relies on consistent logging within the automation engine's execute_actions
    query = (
        select(Event)
        .where(
            Event.type == "automation_triggered"
        )  # Assuming this event type is logged by engine
        # Need a reliable way to link event to automation, e.g., storing ID in data field
        .where(
            Event.data["automation_id"].astext == automation_id
        )  # Adjust based on how ID is stored in data
        .order_by(Event.timestamp.desc())
        .limit(limit)
    )

    try:
        result = await db.execute(query)
        events = result.scalars().all()
    except Exception as e:
        logger.error(
            f"Error querying automation history for {automation_id}: {e}", exc_info=True
        )
        # Handle potential JSON query errors if data structure isn't guaranteed
        raise HTTPException(
            status_code=500, detail="Failed to retrieve automation history."
        )

    return events


@router.post("/{automation_id}/test", response_model=Dict[str, Any])
async def test_automation(
    automation_id: str,
    context: Optional[Dict[str, Any]] = Body(
        None, description="Optional context data for testing trigger/conditions"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Test automation logic (trigger, conditions) without executing actions.
    Requires the automation engine to support a 'test' or 'dry-run' mode.
    """
    # Verify automation exists and belongs to user
    automation_db = await get_automation_by_id(db, automation_id, current_user.id)

    # Get the rule from the engine
    rule = await automation_engine.get_rule(automation_id)
    if not rule:
        # Try loading it if not currently in engine (e.g., if disabled)
        rule_config = {
            "id": automation_db.id,
            "name": automation_db.name,  # ... (rest of config) ...
            "trigger": {
                "type": automation_db.trigger_type,
                "config": automation_db.trigger_config,
            },
            "condition_type": automation_db.condition_type,
            "conditions": automation_db.conditions,
            "actions": automation_db.actions,
            "enabled": automation_db.enabled,
        }
        rule = await create_rule_from_config(rule_config)
        if not rule:
            raise HTTPException(
                status_code=404, detail="Automation rule not found or invalid."
            )

    # Prepare context for testing
    test_context = context or {}
    test_context.setdefault("timestamp", datetime.now(datetime.timezone.utc))
    # Add other relevant default context if needed

    logger.info(f"Testing automation {automation_id} with context: {test_context}")

    try:
        # Evaluate trigger (if applicable/testable without real events)
        # Trigger check might depend on real-time data not present in context
        trigger_result = await rule.trigger.check(test_context)

        # Evaluate conditions
        conditions_result = await rule.evaluate_conditions(test_context)

        # Determine overall test result
        would_run = trigger_result and conditions_result

        logger.info(
            f"Automation test result for {automation_id}: Trigger={trigger_result}, Conditions={conditions_result}, WouldRun={would_run}"
        )

        return {
            "message": "Automation test completed.",
            "automation_id": automation_id,
            "automation_name": rule.name,
            "test_context": test_context,
            "trigger_evaluation": trigger_result,
            "conditions_evaluation": conditions_result,
            "would_execute": would_run,
            "actions_to_execute": (
                [
                    {"type": action.action_type, "config": action.config}
                    for action in rule.actions
                ]
                if would_run
                else []
            ),
        }

    except Exception as e:
        logger.error(
            f"Error during automation test for {automation_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Error during test: {e}")
