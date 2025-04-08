# backend/src/core/startup.py

"""
Violt Core Lite - Application Startup

This module handles application startup and initialization.
"""
import asyncio
import logging
from fastapi import FastAPI, HTTPException  # Import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from .config import settings, DEFAULT_LOGS_DIR, DEFAULT_DATA_DIR, DEFAULT_CONFIG_DIR
from ..database.migration_runner import run_migrations
from ..database.session import (
    check_db_connection,
    engine as async_engine,
)  # Import engine
from .logger import setup_logging
from ..devices.registry import load_integration_modules
from ..automation.engine import engine as automation_engine

logger = logging.getLogger(__name__)


# Custom Exception for startup errors
class StartupError(Exception):
    pass


async def run_migrations_startup():
    """Check DB connection and run Alembic migrations."""
    logger.info("Checking database connection...")
    # Use the async connection check
    db_connected = await check_db_connection()
    if not db_connected:
        logger.critical("Database connection failed. Halting startup.")
        raise StartupError("Database connection failed during startup.")

    logger.info("Running database migrations...")
    # Run migrations synchronously in a thread pool executor
    loop = asyncio.get_event_loop()
    try:
        migrations_ok = await loop.run_in_executor(
            None, run_migrations
        )  # run_migrations is sync
    except Exception as e:
        logger.critical(f"Exception during migration execution: {e}", exc_info=True)
        migrations_ok = False

    if not migrations_ok:
        logger.critical("Database migrations failed. Halting startup.")
        raise StartupError("Database migrations failed during startup.")


async def startup_event_handler(app: FastAPI):
    """Handle application startup events."""
    try:
        # Setup logging first
        setup_logging()
        logger.info(
            f"Starting {settings.APP_NAME} v{settings.APP_VERSION} on {settings.PLATFORM}"
        )

        # Create required directories
        log_file_path = Path(settings.LOG_FILE)
        if not log_file_path.is_absolute():
            log_file_path = DEFAULT_LOGS_DIR / log_file_path
        try:
            os.makedirs(log_file_path.parent, exist_ok=True)
            os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
            os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
            os.makedirs(DEFAULT_CONFIG_DIR / "integrations", exist_ok=True)
            logger.info(f"Log directory: {log_file_path.parent}")
            logger.info(f"Data directory: {DEFAULT_DATA_DIR}")
            logger.info(f"Config directory: {DEFAULT_CONFIG_DIR}")
        except OSError as e:
            logger.error(f"Error creating directories: {e}", exc_info=True)
            raise StartupError(f"Failed to create essential directories: {e}")

        # Check connection and run migrations - critical step
        await run_migrations_startup()  # This will raise StartupError if it fails

        # Load device integration modules
        logger.info("Loading device integration modules...")
        load_integration_modules()

        # Start the automation engine
        logger.info("Starting automation engine...")
        # Ensure engine start doesn't raise unhandled exceptions during startup
        try:
            await automation_engine.start()
        except Exception as e:
            logger.error(f"Failed to start automation engine: {e}", exc_info=True)
            # Decide if this is critical enough to stop startup
            # raise StartupError(f"Automation engine failed to start: {e}")

        logger.info(f"{settings.APP_NAME} startup complete, application ready.")

    except StartupError as e:
        logger.critical(f"Application startup failed: {e}")
        # Gracefully shutdown? Or let the process exit?
        # For docker, letting it exit might be better for restart policies.
        # Attempt cleanup if necessary
        await shutdown_event_handler(app)  # Call shutdown handler on startup failure
        # Re-raise or exit to signal failure
        raise e  # Re-raise to stop FastAPI/Uvicorn startup
    except Exception as e:
        logger.critical(
            f"Unexpected error during application startup: {e}", exc_info=True
        )
        # Attempt cleanup
        await shutdown_event_handler(app)
        raise e


async def shutdown_event_handler(app: FastAPI):
    """Handle application shutdown events."""
    logger.info(f"Shutting down {settings.APP_NAME}...")
    # Stop the automation engine
    if automation_engine.running:
        logger.info("Stopping automation engine...")
        await automation_engine.stop()

    # Close integration sessions (e.g., aiohttp)
    # from ..devices.registry import registry as device_registry
    # for integration in device_registry.get_integrations():
    #     if hasattr(integration, 'close_session') and asyncio.iscoroutinefunction(integration.close_session):
    #         await integration.close_session()

    # Dispose of the main database engine pool (optional for aiosqlite)
    if async_engine:
        await async_engine.dispose()
        logger.info("Database engine disposed.")

    logger.info(f"{settings.APP_NAME} shutdown complete.")


def init_app():
    """Initialize and configure the FastAPI application."""
    from ..main import app

    # Use lifespan context manager for cleaner startup/shutdown handling
    # This replaces add_event_handler
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Runs on startup
        await startup_event_handler(app)
        yield  # Application runs here
        # Runs on shutdown
        await shutdown_event_handler(app)

    app.router.lifespan_context = lifespan
    return app


# NOTE: Ensure your main entry point (e.g., if you have a run.py or similar)
# calls init_app() to attach the lifespan manager correctly before uvicorn.run()
# If you run directly via uvicorn src.main:app, FastAPI should handle lifespan.
