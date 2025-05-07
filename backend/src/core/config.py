# backend/src/core/config.py

"""
Violt Core - Configuration Module

This module handles loading and validating application configuration from environment variables.
"""
import json
from pydantic import Field, field_validator, EmailStr, ConfigDict, validator
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional, ClassVar, Union  # Import ClassVar
import os
import platform
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# --- Calculate .env file path BEFORE the class definition ---
ENV_FILE_PATH: Optional[Path] = None
try:
    # Path to the 'backend' directory relative to this config.py file
    # config.py is in backend/src/core/config.py
    # Need to go up 3 levels to reach 'backend'
    backend_dir_path = Path(__file__).resolve().parent.parent.parent
    potential_env_path = backend_dir_path / ".env"
    if potential_env_path.is_file():
        ENV_FILE_PATH = potential_env_path
        logger.info(f"Found .env file at: {ENV_FILE_PATH}")
    else:
        logger.info(
            f".env file not found at {potential_env_path}, relying on environment variables."
        )
except Exception as e:
    logger.error(f"Error calculating .env file path: {e}", exc_info=True)
# --- End path calculation ---


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    APP_NAME: str = "Violt-Core"
    APP_VERSION: str = "1.0.1"
    DEBUG: bool = False
    LOG_LEVEL: str = "info"
    ENVIRONMENT: str = "production"  # Default to production

    # Platform settings
    PLATFORM: str = platform.system()
    IS_WINDOWS: bool = platform.system() == "Windows"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = False

    # Database settings
    DATABASE_URL: str = "sqlite:///./violt.db"
    DATABASE_CONNECT_ARGS: Dict[str, Any] = {"check_same_thread": False}

    # Security settings
    SECRET_KEY: str = "changeme_in_production_this_is_not_secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # MongoDB settings
    MONGODB_ENABLED: bool = False
    MONGODB_URI: Optional[str] = None
    MONGODB_DATABASE: Optional[str] = None

    # Background worker settings
    AUTOMATION_CHECK_INTERVAL: int = 5

    # Device discovery settings
    DEVICE_DISCOVERY_ENABLED: bool = True
    DEVICE_DISCOVERY_INTERVAL: int = 300

    # Integration settings
    XIAOMI_INTEGRATION_ENABLED: bool = True
    ALEXA_INTEGRATION_ENABLED: bool = False
    GOOGLE_HOME_INTEGRATION_ENABLED: bool = False

    # Logging settings
    LOG_FILE: str = "logs/violt.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"

    # Windows service settings
    WINDOWS_SERVICE_NAME: str = "VioltCore"
    WINDOWS_SERVICE_DISPLAY_NAME: str = "Violt Core Service"
    WINDOWS_SERVICE_DESCRIPTION: str = "Local smart home automation platform"
    WINDOWS_SERVICE_STARTUP: str = "auto"  # Kept as string

    WINDOWS_SERVICE_STARTUP: str = "auto"  # Kept as string

    # BLE Integration
    BLE_SCAN_INTERVAL: int = 60
    BLE_SCAN_TIMEOUT: int = 10
    BLE_MAX_CONNECTION_ATTEMPTS: int = 5
    BLE_CONNECTION_RETRY_BASE_WAIT: int = 5
    BLE_CONNECTION_RETRY_MAX_WAIT: int = 120
    BLE_MONITOR_INTERVAL: int = 30
    BLE_DEVICE_FILTERS: dict = Field(default={})

    @field_validator("BLE_DEVICE_FILTERS", mode="before")
    def assemble_ble_filters(cls, v: Union[str, dict]) -> dict:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse BLE_DEVICE_FILTERS JSON string: {v}")
                return {}
        elif isinstance(v, dict):
            return v
        return {}

    # --- Validator for SECRET_KEY ---
    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v):
        is_debug = os.getenv("DEBUG", "false").lower() == "true"
        logger.debug(
            f"Validating SECRET_KEY. DEBUG={is_debug}, Input Value Provided Type='{type(v)}'"
        )
        default_secret = "changeme_in_production_this_is_not_secure"
        # Handle case where v might be None if not set anywhere
        actual_value = v if v is not None else default_secret
        if actual_value == default_secret and not is_debug:
            logger.error(
                "SECRET_KEY validation failed: Default key used in non-DEBUG mode."
            )
            raise ValueError(
                "SECRET_KEY must be changed in production when DEBUG is not true"
            )
        logger.debug("SECRET_KEY validation passed.")
        # Return the original value 'v' if it existed, otherwise Pydantic uses the default
        return v if v is not None else default_secret

    # --- Pydantic V2 model configuration ---
    model_config = ConfigDict(
        # Use the pre-calculated ENV_FILE_PATH variable
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields
    )


# Create a single instance of the settings
settings = Settings()

# --- Define DEFAULT_DATA_DIR etc. AFTER Settings class ---
# (Path logic remains the same, needs APP_ROOT_DIR calculation)
if getattr(sys, "frozen", False):
    APP_ROOT_DIR = Path(sys.executable).parent
else:
    # Assuming config.py is in backend/src/core/config.py
    APP_ROOT_DIR = Path(__file__).resolve().parent.parent.parent

if platform.system() == "Windows":
    DEFAULT_DATA_DIR = (
        Path(os.environ.get("PROGRAMDATA", APP_ROOT_DIR / "data")) / "VioltCore"
    )
    DEFAULT_CONFIG_DIR = DEFAULT_DATA_DIR / "config"
    DEFAULT_LOGS_DIR = DEFAULT_DATA_DIR / "logs"
    SYSTEM_DRIVE = os.environ.get("SystemDrive", "C:")
else:
    DEFAULT_DATA_DIR = APP_ROOT_DIR / "data"
    DEFAULT_CONFIG_DIR = APP_ROOT_DIR / "config"
    DEFAULT_LOGS_DIR = APP_ROOT_DIR / "logs"
    SYSTEM_DRIVE = "/"

# --- Directory Creation & Settings Instantiation ---
# Moved directory creation here to ensure paths exist before Settings uses them potentially
# (e.g., if DATABASE_URL default used DEFAULT_DATA_DIR)
try:
    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
    os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
    os.makedirs(DEFAULT_LOGS_DIR, exist_ok=True)
except Exception as e:
    logger.warning(
        f"Could not create default directories during config import: {e}", exc_info=True
    )

# --- Create global settings instance ---
try:
    logger.info("Initializing Settings object...")
    settings = Settings()  # Now reads ENV_FILE_PATH set above
    logger.info("Settings object initialized successfully.")
    # Add more detailed logging if DEBUG is true
    if settings and settings.DEBUG:
        # Safely dump model excluding sensitive keys
        sensitive_keys = {
            "SECRET_KEY",
            "MONGODB_URI",
            "client_secret",
            "access_token",
            "refresh_token",
        }
        dump_safe = settings.model_dump(exclude=sensitive_keys)
        logger.debug(f"Debug mode active. Loaded Settings (safe dump): {dump_safe}")

except Exception as e:
    logger.critical(f"CRITICAL: Failed to initialize settings: {e}", exc_info=True)
    settings = None

# Ensure the directory for the SQLite database exists
if settings.DATABASE_URL.startswith("sqlite"):
    db_path_str = settings.DATABASE_URL.split("///")[-1]
    # Handle potential relative paths correctly
    if not os.path.isabs(db_path_str):
        # Assume relative to project root (one level above backend)
        db_path = APP_ROOT_DIR / db_path_str
    else:
        db_path = Path(db_path_str)

    db_dir = db_path.parent
    try:
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory ensured: {db_dir}")
    except Exception as e:
        logger.error(f"Error creating database directory {db_dir}: {e}")

    logger.info(f"Loaded settings. Database URL: {settings.DATABASE_URL}")
    logger.debug(f"Database path resolved: {db_path}")
