# backend/src/database/migration_runner.py
import asyncio
import os
import logging
from alembic.config import Config
from alembic import command, script
from alembic.runtime import migration
from sqlalchemy import create_engine, inspect  # Import inspect
from pathlib import Path

# Import necessary config/settings from your application
from ..core.config import settings  # If needed for paths, etc.

# Import get_database_url to check the connection string directly if needed
from .session import get_database_url

logger = logging.getLogger(__name__)


def run_migrations():
    """Applies Alembic migrations programmatically."""
    logger.info("Attempting to apply database migrations...")
    migration_applied = False
    try:
        # Get the path to alembic.ini relative to this file or project root
        # Assuming this file is at src/database/migration_runner.py
        # and alembic.ini is at the root of the 'backend' directory
        backend_root = Path(__file__).parent.parent.parent
        alembic_cfg_path = backend_root / "alembic.ini"
        migrations_path = backend_root / "migrations"

        if not alembic_cfg_path.is_file():
            logger.error(f"Alembic config file not found at: {alembic_cfg_path}")
            # Fallback: Maybe try creating tables directly if migrations aren't setup?
            from .init_db import init_db  # Careful with circular imports
        if not migrations_path.is_dir():
            logger.error(f"Migrations directory not found at: {migrations_path}")
            raise FileNotFoundError("Alembic migrations directory not found.")
        # else:
        #     asyncio.run(init_db())  # Running async from sync might be complex here
        #     raise FileNotFoundError("Alembic config not found.")

        logger.info(f"Using Alembic config: {alembic_cfg_path}")
        logger.info(f"Using migrations directory: {migrations_path}")

        # Explicitly set the DB URL for Alembic using the same function the app uses
        alembic_cfg = Config(str(alembic_cfg_path))  # Create Alembic Config instance
        db_url = get_database_url()
        logger.info(f"Configuring Alembic with DB URL: {db_url}")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        # Optional: Check current revision before upgrading
        try:
            # Need a sync engine for this Alembic API call
            sync_engine = create_engine(db_url)
            with sync_engine.connect() as connection:
                context = migration.MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                logger.info(f"Current database revision: {current_rev}")
            sync_engine.dispose()
        except Exception as check_err:
            logger.warning(
                f"Could not determine current DB revision (might be empty): {check_err}"
            )

        # Apply migrations
        logger.info("Running alembic upgrade head...")
        command.upgrade(alembic_cfg, "head")
        migration_applied = True  # Assume success if no exception
        logger.info("Database migrations applied successfully (or already up-to-date).")
        return True

    except FileNotFoundError:
        # Logged above
        return False
    except Exception as e:
        # Log the full traceback for debugging Alembic issues
        logger.critical(f"Failed to apply database migrations: {e}", exc_info=True)
        # If migrations fail, the table likely won't exist.
        return False
