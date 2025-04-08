# backend/migrations/env.py
import os
import sys
import logging
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from pathlib import Path  # Use pathlib for better path handling

# --- Configure Logging Immediately ---
# Setup basic logging FIRST to capture any issues early, including path problems
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s"
)
log = logging.getLogger("alembic.env")
log.info("--- Running migrations/env.py ---")
log.info(f"Python executable: {sys.executable}")
log.info(f"Initial sys.path: {sys.path}")

# --- Path Setup ---
try:
    # Calculate paths relative to this script file
    CURRENT_SCRIPT_DIR = Path(__file__).resolve().parent  # .../backend/migrations
    log.info(f"CURRENT_SCRIPT_DIR: {CURRENT_SCRIPT_DIR}")
    # Assume alembic.ini is in the parent of migrations directory
    ALEMBIC_DIR = CURRENT_SCRIPT_DIR.parent  # .../backend/migrations
    BACKEND_DIR = ALEMBIC_DIR.parent  # .../backend/
    log.info(f"Calculated BACKEND_DIR: {BACKEND_DIR}")

    # Add the BACKEND directory to sys.path BEFORE attempting src imports
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
        log.info(f"INSERTED {BACKEND_DIR} into sys.path")
    else:
        log.info(f"{BACKEND_DIR} was already in sys.path")

    log.info(f"sys.path AFTER insert: {sys.path}")

    # Check if src directory exists where expected
    # SRC_DIR_CHECK = BACKEND_DIR / "src"
    # log.info(
    #     f"Checking for src directory at: {SRC_DIR_CHECK} - Exists: {SRC_DIR_CHECK.is_dir()}"
    # )
    # Add the src directory to sys.path
    SRC_DIR = BACKEND_DIR
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
        log.info(f"Added {SRC_DIR} to sys.path")
    else:
        log.info(f"{SRC_DIR} is already in sys.path")

except Exception as path_err:
    log.critical(f"Error during path setup: {path_err}", exc_info=True)
    sys.exit("Path setup failed in env.py")


# --- Import Models and Config ---
# Now attempt the imports
try:
    log.info("Attempting to import Base from src.database.models...")
    from src.database.models import Base  # Import your models' Base

    log.info(f"Successfully imported Base: {type(Base)}")

    log.info("Attempting to import get_database_url from src.database.session...")
    from src.database.session import get_database_url  # Import function to get DB URL

    log.info("Successfully imported get_database_url.")

    # Define target_metadata right after successful import
    target_metadata = Base.metadata
    log.info(
        f"Successfully accessed Base.metadata. Tables: {list(target_metadata.tables.keys())}"
    )

except ImportError as e:
    log.critical(
        f"Failed crucial import from src.*: {e}. Check BACKEND_DIR/sys.path.",
        exc_info=True,
    )
    sys.exit(f"ImportError in env.py: {e}")
except AttributeError as e:
    log.critical(
        f"Failed to access Base.metadata: {e}. Is Base defined correctly?",
        exc_info=True,
    )
    sys.exit(f"AttributeError getting metadata: {e}")
except Exception as import_err:
    log.critical(
        f"An unexpected error occurred during imports: {import_err}", exc_info=True
    )
    sys.exit(f"Unexpected import error in env.py: {import_err}")


# --- Alembic Config Object ---
config = context.config

# Interpret the config file for Python logging (AFTER basic logging is set up).
if config.config_file_name is not None:
    try:
        # Pass disable_existing_loggers=False if you want to keep the basicConfig logger active
        fileConfig(config.config_file_name, disable_existing_loggers=False)
        log.info(f"Logging re-configured from: {config.config_file_name}")
    except Exception as e:
        log.warning(f"Could not configure logging from ini file: {e}")


# --- Migration Functions ---
# (These functions remain the same as the previous version, ensuring target_metadata is passed)
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    log.info(f"Running migrations offline with URL: {url}")
    context.configure(
        url=url,
        target_metadata=target_metadata,  # Use the globally defined metadata
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
    log.info("Offline migrations complete.")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    alembic_config_section = config.get_section(config.config_ini_section)
    if not alembic_config_section:
        alembic_config_section = {}

    db_url = get_database_url()
    alembic_config_section["sqlalchemy.url"] = db_url
    log.info(f"Running migrations online with URL: {db_url}")

    connectable = engine_from_config(
        alembic_config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        log.info("Configuring Alembic context with connection and metadata...")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,  # Use the globally defined metadata
        )
        log.info("Beginning transaction and running migrations...")
        with context.begin_transaction():
            context.run_migrations()
        log.info("Online migrations run complete.")


# --- Execution ---
log.info(
    f"Alembic context mode: {'offline' if context.is_offline_mode() else 'online'}"
)
if context.is_offline_mode():
    run_migrations_offline()
else:
    try:
        run_migrations_online()
    except Exception as e:
        log.critical(f"Error during run_migrations_online: {e}", exc_info=True)
        raise  # Re-raise the exception so Alembic reports the failure

log.info("--- Finished migrations/env.py ---")
