"""
Violt Core Lite - Database Initialization

This module handles database initialization and migrations using Alembic.
"""

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import text
import asyncio
import logging
import os
from pathlib import Path

from .session import engine, Base
from ..core.config import settings, DEFAULT_DATA_DIR

logger = logging.getLogger(__name__)


async def init_db():
    """Initialize the database by creating all tables."""
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Log database location for debugging
        db_url = str(engine.url)
        if db_url.startswith("sqlite+aiosqlite:///"):
            db_path = db_url[19:]  # Remove 'sqlite+aiosqlite:///'
            logger.info(f"Database initialized at: {db_path}")

            # Ensure database directory has proper permissions
            try:
                db_file = Path(db_path)
                if db_file.exists():
                    # Make sure the file is readable and writable
                    os.chmod(db_file, 0o644)
                    logger.debug(f"Set permissions on database file: {db_file}")
            except Exception as perm_error:
                logger.warning(
                    f"Could not set permissions on database file: {perm_error}"
                )

        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


async def check_db_connection():
    """Check if database connection is working."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

        # Provide more helpful error messages for common issues
        error_str = str(e).lower()
        if "permission denied" in error_str:
            if settings.IS_WINDOWS:
                logger.error(
                    "Windows permission error: Make sure you have write access to the database directory"
                )
            else:
                logger.error(
                    "Linux permission error: Check file permissions and ownership"
                )
        elif "no such file or directory" in error_str:
            logger.error(
                f"Database directory does not exist. Creating directory structure..."
            )
            try:
                # Try to create the directory structure
                db_url = str(engine.url)
                if db_url.startswith("sqlite+aiosqlite:///"):
                    db_path = Path(db_url[19:])  # Remove 'sqlite+aiosqlite:///'
                    os.makedirs(db_path.parent, exist_ok=True)
                    logger.info(f"Created database directory: {db_path.parent}")
            except Exception as dir_error:
                logger.error(f"Failed to create database directory: {dir_error}")

        return False
