# migrations/env.py (Slight Refinement)

import os
import sys
from logging.config import fileConfig

# Make sure you are using engine_from_config from sqlalchemy, not async engine here
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# --- Add project root to path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, PROJECT_ROOT)
# --- End Path Addition ---

# Import your Base and settings
from src.database.models import Base  # Import your models' Base
from src.database.session import get_database_url  # Import function to get DB URL

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata  # Use your imported Base


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,  # Pass metadata here
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Get the Alembic config section
    alembic_config_section = config.get_section(config.config_ini_section)
    if not alembic_config_section:
        # Handle case where section might be missing, though unlikely
        alembic_config_section = {}

    # Set the database URL dynamically
    alembic_config_section["sqlalchemy.url"] = get_database_url()

    # Create engine using the dynamically set URL
    connectable = engine_from_config(
        alembic_config_section,  # Use the section dictionary
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,  # Pass metadata here too for consistency
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
