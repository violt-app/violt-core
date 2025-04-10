# backend/src/api/system/router.py

"""
Violt Core Lite - API Router for System

This module handles system API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func as sql_func  # Import func for count
from typing import List, Optional, Dict, Any
import logging
import platform
import psutil
from datetime import datetime, timedelta
import os
import asyncio
from pathlib import Path
import uuid

# Assuming schemas are correctly defined
from ...core.schemas import (
    SystemStatus,
    SystemStats,
    EventResponse,
    BaseSchema,
)  # Added BaseSchema
from ...core.auth import get_current_active_user
from ...database.session import get_db
from ...database.models import User, Device, Automation, Event, Log
from ...core.config import settings, DEFAULT_DATA_DIR, SYSTEM_DRIVE

# Import utility functions if they exist
from ...core import system_utils

logger = logging.getLogger(__name__)
router = APIRouter()

# Store startup time (consider moving this to a central app state if needed)
try:
    # Attempt to read from a file if persistence across restarts is desired
    with open(DEFAULT_DATA_DIR / ".startup_time", "r") as f:
        STARTUP_TIME = datetime.fromisoformat(f.read().strip())
    logger.info(f"Read previous startup time: {STARTUP_TIME}")
except Exception:
    STARTUP_TIME = datetime.utcnow()
    try:
        # Save current startup time
        os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
        with open(DEFAULT_DATA_DIR / ".startup_time", "w") as f:
            f.write(STARTUP_TIME.isoformat())
    except Exception as e:
        logger.warning(f"Could not save startup time: {e}")

# --- Helper Functions ---


def format_uptime(delta: timedelta) -> str:
    """Format timedelta as human-readable uptime string."""
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    # Always show seconds if uptime is less than a minute, or if days/hours/mins are zero
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts) if parts else "0s"


async def get_db_counts(db: AsyncSession, user_id: str) -> tuple[int, int]:
    """Get counts of devices and automations asynchronously."""
    try:
        device_count_result = await db.execute(
            select(sql_func.count(Device.id)).where(Device.user_id == user_id)
        )
        device_count = device_count_result.scalar_one_or_none() or 0

        automation_count_result = await db.execute(
            select(sql_func.count(Automation.id)).where(Automation.user_id == user_id)
        )
        automation_count = automation_count_result.scalar_one_or_none() or 0
        return device_count, automation_count
    except Exception as e:
        logger.error(f"Error getting DB counts for user {user_id}: {e}", exc_info=True)
        return 0, 0  # Return 0 on error


async def get_last_event_time(db: AsyncSession) -> Optional[datetime]:
    """Get the timestamp of the most recent event."""
    try:
        event_result = await db.execute(
            select(Event.timestamp).order_by(Event.timestamp.desc()).limit(1)
        )
        last_event_time = event_result.scalar_one_or_none()
        return last_event_time
    except Exception as e:
        logger.error(f"Error getting last event time: {e}", exc_info=True)
        return None


# --- API Endpoints ---


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    db: AsyncSession = Depends(get_db),
):
    """Get overall system status, version, uptime, and entity counts."""
    uptime_delta = datetime.utcnow() - STARTUP_TIME
    uptime_str = format_uptime(uptime_delta)

    device_count = 0 # Placeholder
    automation_count = 0 # Placeholder
    last_event_time = await get_last_event_time(db)

    # Get connected WebSocket clients (example, needs actual implementation in websocket manager)
    connected_clients = 0  # Placeholder
    # if hasattr(websocket_manager, 'get_total_connections'):
    #    connected_clients = websocket_manager.get_total_connections()

    return SystemStatus(
        status="running",  # Could be 'degraded' if some checks fail
        version=settings.APP_VERSION,
        uptime=uptime_str,
        device_count=device_count,
        automation_count=automation_count,
        last_event=last_event_time,
        # Add more status indicators if needed
        # platform=settings.PLATFORM, # Removed as per schema, add if needed
        # connected_clients=connected_clients,
    )


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed system statistics (CPU, memory, disk, entity stats)."""
    try:
        cpu_usage = psutil.cpu_percent(interval=None)  # Non-blocking call
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
    except Exception as e:
        logger.warning(f"Failed to get CPU/Memory usage: {e}")
        cpu_usage = 0.0
        memory_usage = 0.0

    # Get disk usage
    disk_usage_info = system_utils.get_disk_usage(SYSTEM_DRIVE)  # Use utility

    # Get device statistics ( reusing get_device_stats logic, but could be optimized )
    try:
        device_result = await db.execute(
            select(Device).where(Device.user_id == current_user.id)
        )
        devices = device_result.scalars().all()
        total_devices = len(devices)
        online_devices = sum(1 for d in devices if d.status == "online")
        offline_devices = total_devices - online_devices
        devices_by_type = {}
        for d in devices:
            devices_by_type[d.type] = devices_by_type.get(d.type, 0) + 1
        device_stats_dict = {
            "total": total_devices,
            "online": online_devices,
            "offline": offline_devices,
            "by_type": devices_by_type,
        }
    except Exception as e:
        logger.error(
            f"Failed to get device stats for user {current_user.id}: {e}", exc_info=True
        )
        device_stats_dict = {"total": 0, "online": 0, "offline": 0, "by_type": {}}

    # Get automation statistics ( reusing get_automation_stats logic, optimized query )
    try:
        # Optimized query for counts
        enabled_count_res = await db.execute(
            select(sql_func.count(Automation.id)).where(
                Automation.user_id == current_user.id, Automation.enabled == True
            )
        )
        enabled_automations = enabled_count_res.scalar_one()
        total_count_res = await db.execute(
            select(sql_func.count(Automation.id)).where(
                Automation.user_id == current_user.id
            )
        )
        total_automations = total_count_res.scalar_one()
        disabled_automations = total_automations - enabled_automations

        # Count executions today
        today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        executions_today_res = await db.execute(
            select(sql_func.count(Event.id)).where(
                Event.type == "automation_triggered",  # Assuming this type is logged
                Event.timestamp >= today_start,
                # Need to ensure event is linked to this user's automations if events aren't user-specific
                # This might require joining Event -> Automation -> User or storing user_id on Event
            )
        )
        executions_today = executions_today_res.scalar_one()

        automation_stats_dict = {
            "total": total_automations,
            "enabled": enabled_automations,
            "disabled": disabled_automations,
            "executions_today": executions_today,
        }
    except Exception as e:
        logger.error(
            f"Failed to get automation stats for user {current_user.id}: {e}",
            exc_info=True,
        )
        automation_stats_dict = {
            "total": 0,
            "enabled": 0,
            "disabled": 0,
            "executions_today": 0,
        }

    return SystemStats(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage_info["percent"],
        device_stats=device_stats_dict,
        automation_stats=automation_stats_dict,
    )


# Placeholder response model for async tasks
class TaskResponse(BaseSchema):
    message: str
    status: str = "pending"
    task_id: Optional[str] = None


async def _run_system_restart():
    """Background task for restarting the system."""
    await asyncio.sleep(2)  # Short delay before attempting restart
    logger.info("Executing system restart...")
    success = system_utils.restart_system()  # Call the utility function
    if not success:
        logger.error("System restart command failed.")
    # Note: If successful, the process will likely terminate here.


@router.post(
    "/restart", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED
)
async def restart_system_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(
        get_current_active_user
    ),  # Ensure only authenticated users can restart
):
    """Initiate a system restart (runs in background)."""
    logger.warning(f"System restart initiated by user: {current_user.username}")
    # Add the restart function as a background task
    background_tasks.add_task(_run_system_restart)
    return TaskResponse(message="System restart initiated.")


@router.get(
    "/logs", response_model=List[EventResponse]
)  # Reuse EventResponse if suitable, or create LogResponse
async def get_system_logs(
    level: Optional[str] = Query(
        None, description="Filter logs by level (e.g., INFO, WARNING, ERROR)"
    ),
    source: Optional[str] = Query(None, description="Filter logs by source module"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of log entries to return"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # Require auth to view logs
):
    """Get system log entries with optional filtering."""
    try:
        query = select(Log).order_by(Log.timestamp.desc()).limit(limit)

        if level:
            query = query.where(
                Log.level == level.upper()
            )  # Assume level is stored uppercase
        if source:
            query = query.where(Log.source == source)

        result = await db.execute(query)
        logs = result.scalars().all()

        # Convert Log models to EventResponse or a dedicated LogResponse model
        # Using EventResponse might require mapping fields if they don't match perfectly
        # Example using dict conversion if LogResponse schema doesn't exist:
        # return [
        #     {
        #         "id": log.id,
        #         "timestamp": log.timestamp,
        #         "type": "log_entry", # Use a specific type for logs?
        #         "source": log.source,
        #         "data": {"level": log.level, "message": log.message, **(log.data or {})},
        #         "processed": True # Logs are generally considered 'processed'
        #     } for log in logs
        # ]
        # If EventResponse fits:
        return [EventResponse.model_validate(log) for log in logs]

    except Exception as e:
        logger.error(f"Error retrieving system logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve system logs.")


# --- Backup/Restore/Update Placeholders ---
# These require significant implementation effort and are kept as placeholders


async def _run_backup_task(task_id: str, backup_path: Path):
    logger.info(f"Starting backup task {task_id} to {backup_path}...")
    await asyncio.sleep(5)  # Simulate backup time
    # Actual backup logic: copy DB file, config files, etc. to a timestamped archive
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = backup_path / f"violt_backup_{timestamp}.zip"  # Example
    logger.info(f"Backup task {task_id} finished (simulation). Archive: {archive_name}")
    # Update task status in DB or via WebSocket?


@router.post(
    "/backup", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED
)
async def create_backup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """Create a system backup (database and configuration)."""
    task_id = f"backup_{uuid.uuid4()}"
    # Determine platform-specific default backup path
    if settings.IS_WINDOWS:
        backup_dir = (
            Path(os.environ.get("USERPROFILE", DEFAULT_DATA_DIR)) / "VioltBackups"
        )
    else:
        backup_dir = Path(
            "/var/backups/violt-core-lite"
        )  # Needs appropriate permissions

    try:
        os.makedirs(backup_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create backup directory {backup_dir}: {e}")
        raise HTTPException(status_code=500, detail="Cannot create backup directory.")

    logger.info(f"Backup requested by {current_user.username}. Task ID: {task_id}")
    background_tasks.add_task(_run_backup_task, task_id, backup_dir)
    return TaskResponse(message="Backup creation scheduled.", task_id=task_id)


async def _run_restore_task(task_id: str, backup_file_path: Path):
    logger.warning(f"Starting RESTORE task {task_id} from {backup_file_path}...")
    # !!! DANGEROUS OPERATION !!!
    # Needs careful implementation:
    # 1. Stop services/engine
    # 2. Validate backup file
    # 3. Extract files to temporary location
    # 4. Replace current DB/config files (handle permissions)
    # 5. Restart services/engine
    await asyncio.sleep(10)  # Simulate restore time
    logger.warning(
        f"RESTORE task {task_id} finished (simulation). System should be restarted."
    )


@router.post(
    "/restore", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED
)
async def restore_backup(
    background_tasks: BackgroundTasks,
    backup_filename: str = Body(
        ...,
        description="Filename of the backup archive (must exist in backup directory)",
    ),
    current_user: User = Depends(get_current_active_user),  # Ensure admin/auth
):
    """Restore system state from a backup file."""
    task_id = f"restore_{uuid.uuid4()}"
    # Determine platform-specific default backup path
    if settings.IS_WINDOWS:
        backup_dir = (
            Path(os.environ.get("USERPROFILE", DEFAULT_DATA_DIR)) / "VioltBackups"
        )
    else:
        backup_dir = Path("/var/backups/violt-core-lite")

    backup_file = backup_dir / backup_filename
    if not backup_file.is_file():
        logger.error(f"Backup file not found: {backup_file}")
        raise HTTPException(status_code=404, detail="Backup file not found.")

    logger.warning(
        f"Restore from {backup_filename} requested by {current_user.username}. Task ID: {task_id}"
    )
    # Add restore task to background
    background_tasks.add_task(_run_restore_task, task_id, backup_file)
    return TaskResponse(
        message="System restore scheduled. The application will restart if successful.",
        task_id=task_id,
    )


@router.get("/updates", response_model=Dict[str, Any])
async def check_updates(current_user: User = Depends(get_current_active_user)):
    """Check for available application updates (placeholder)."""
    # In a real implementation, this would check against a release server/GitHub releases
    logger.info("Update check requested.")
    # Simulate check
    latest_version = settings.APP_VERSION  # Assume up-to-date for now
    update_available = False  # Compare current with latest fetched version
    release_notes_url = "https://github.com/violt-app/violt-core/releases"  # Example

    return {
        "current_version": settings.APP_VERSION,
        "latest_version": latest_version,
        "update_available": update_available,
        "release_notes_url": release_notes_url if update_available else None,
    }
