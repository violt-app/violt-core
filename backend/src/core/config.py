"""
Violt Core Lite - Configuration Module

This module handles loading and validating application configuration from environment variables.
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
import os
import platform
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    APP_NAME: str = "Violt Core"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "debug"

    # Platform settings
    PLATFORM: str = platform.system()  # 'Windows', 'Linux', etc.
    IS_WINDOWS: bool = platform.system() == "Windows"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = True

    # Database settings
    DATABASE_URL: str = "sqlite:///./violt.db"
    DATABASE_CONNECT_ARGS: Dict[str, Any] = {"check_same_thread": False}

    # Security settings
    SECRET_KEY: str
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
    AUTOMATION_CHECK_INTERVAL: int = 5  # seconds

    # Device discovery settings
    DEVICE_DISCOVERY_ENABLED: bool = True
    DEVICE_DISCOVERY_INTERVAL: int = 300  # seconds

    # Integration settings
    XIAOMI_INTEGRATION_ENABLED: bool = True
    ALEXA_INTEGRATION_ENABLED: bool = False
    GOOGLE_HOME_INTEGRATION_ENABLED: bool = False

    # Logging settings
    LOG_FILE: str = "logs/violt.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"

    # Windows service settings (only used on Windows)
    WINDOWS_SERVICE_NAME: str = "VioltCoreLite"
    WINDOWS_SERVICE_DISPLAY_NAME: str = "Violt Core Lite Service"
    WINDOWS_SERVICE_DESCRIPTION: str = "Local smart home automation platform"
    WINDOWS_SERVICE_AUTO_START: bool = True

    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        """Validate that SECRET_KEY is set and not the default value in production."""
        if (
            v == "changeme_in_production_this_is_not_secure"
            and not os.getenv("DEBUG", "false").lower() == "true"
        ):
            raise ValueError("SECRET_KEY must be changed in production")
        return v

    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        """Ensure database URL is compatible with the current platform."""
        # For SQLite URLs, ensure path separators are correct
        if v.startswith("sqlite:///"):
            # Extract the path part
            path_part = v[10:]
            # Convert to Path object and back to string to normalize separators
            normalized_path = str(Path(path_part))
            # Reconstruct the URL
            return f"sqlite:///{normalized_path}"
        return v

    @validator("LOG_FILE", pre=True)
    def validate_log_file(cls, v):
        """Ensure log file path is compatible with the current platform."""
        # Convert to Path object and back to string to normalize separators
        return str(Path(v))

    class Config:
        env_file = Path(__file__).parent.parent.parent / "config" / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Define platform-specific constants
if settings.IS_WINDOWS:
    # Windows-specific paths and settings
    DEFAULT_DATA_DIR = Path(os.environ.get("APPDATA", "")) / "VioltCoreLite"
    DEFAULT_CONFIG_DIR = DEFAULT_DATA_DIR / "config"
    DEFAULT_LOGS_DIR = DEFAULT_DATA_DIR / "logs"
    SYSTEM_DRIVE = os.environ.get("SystemDrive", "C:")
else:
    # Linux/Raspberry Pi paths and settings
    DEFAULT_DATA_DIR = Path("/var/lib/violt-core-lite")
    DEFAULT_CONFIG_DIR = Path("/etc/violt-core-lite")
    DEFAULT_LOGS_DIR = Path("/var/log/violt-core-lite")
    SYSTEM_DRIVE = "/"

# Ensure data directories exist
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
os.makedirs(DEFAULT_LOGS_DIR, exist_ok=True)
