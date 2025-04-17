"""
Violt Core Lite - Pydantic Schemas

This module defines Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
import re
import uuid


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={"example": {}}
    )


# User schemas
class UserBase(BaseSchema):
    """Base schema for user data."""
    name: str = Field(..., min_length=3, max_length=50)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8)
    terms_accepted: bool = Field(default=False)
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "password": "SecurePass123",
                "terms_accepted": True
            }
        }
    )


class UserUpdate(BaseSchema):
    """Schema for user update."""
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    settings: Optional[Dict[str, Any]] = None

    
class UserInDB(UserBase):
    """Schema for user in database."""
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None
    terms_accepted: bool


class UserResponse(UserBase):
    """Schema for user response."""
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None
    terms_accepted: bool


# Authentication schemas
class Token(BaseSchema):
    """Schema for authentication token."""
    access_token: str
    token_type: str = "bearer"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )


class TokenData(BaseSchema):
    """Schema for token data."""
    username: Optional[str] = None
    user_id: Optional[str] = None


class LoginRequest(BaseSchema):
    """Schema for login request."""
    username: str
    password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "SecurePass123"
            }
        }
    )


from enum import Enum

class DeviceStatus(str, Enum):
    """Enumeration of possible device statuses."""
    CONNECTED = "connected"
    OFFLINE = "offline"
    ERROR = "error"
    CONNECTING = "connecting"

class DeviceStateField(str, Enum):
    """Enumeration of possible device state fields."""
    POWER = "power"
    BRIGHTNESS = "brightness"
    COLOR_TEMP = "color_temp"
    COLOR = "color"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    MOTION = "motion"
    BATTERY = "battery"

class DeviceCapability(str, Enum):
    """Enumeration of possible device capabilities."""
    POWER = "power"
    BRIGHTNESS = "brightness"
    COLOR = "color"
    COLOR_TEMP = "color_temp"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    MOTION = "motion"
    BATTERY = "battery"

# Device schemas
class DeviceBase(BaseSchema):
    """Base schema for device data."""
    name: str = Field(..., min_length=1, max_length=100)
    type: str
    manufacturer: str
    model: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    integration_type: str


class DeviceCreate(DeviceBase):
    """Schema for device creation."""
    config: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Living Room Light",
                "type": "light",
                "manufacturer": "Xiaomi",
                "model": "MJDP09YL",
                "location": "Living Room",
                "ip_address": "192.168.1.100",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "integration_type": "xiaomi",
                "config": {
                    "token": "abcdef1234567890"
                }
            }
        }
    )


class DeviceUpdate(BaseSchema):
    """Schema for device update."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class DeviceState(BaseSchema):
    """Schema for device state."""
    power: Optional[str] = Field(None, description="Power state: 'on', 'off', or None")
    brightness: Optional[int] = Field(None, ge=0, le=100, description="Brightness percentage")
    color_temp: Optional[int] = Field(None, description="Color temperature in Kelvin")
    color: Optional[str] = Field(None, description="Color in hex format")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity percentage")
    motion: Optional[bool] = Field(None, description="Motion detection state")
    battery: Optional[int] = Field(None, ge=0, le=100, description="Battery percentage")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "power": "on",
                "brightness": 80,
                "color_temp": 4000
            }
        }
    )


class DeviceProperties(BaseSchema):
    """Schema for device capabilities and properties."""
    capabilities: List[DeviceCapability] = Field(default_factory=list)
    supported_features: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "capabilities": ["power", "brightness", "color_temp"],
                "supported_features": {
                    "brightness_range": [0, 100],
                    "color_temp_range": [2700, 6500]
                }
            }
        }
    )

class DeviceInDB(DeviceBase):
    """Schema for device in database."""
    id: str
    user_id: str
    status: DeviceStatus = Field(default=DeviceStatus.OFFLINE)
    properties: DeviceProperties = Field(default_factory=DeviceProperties)
    state: DeviceState = Field(default_factory=DeviceState)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    config: Optional[Dict[str, Any]] = None


class DeviceResponse(DeviceBase):
    """Schema for device response."""
    id: str
    status: DeviceStatus
    properties: DeviceProperties
    state: DeviceState
    created_at: datetime
    last_updated: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "abc123",
                "name": "Living Room Light",
                "type": "light",
                "manufacturer": "Xiaomi",
                "model": "MJDP09YL",
                "location": "Living Room",
                "ip_address": "192.168.1.100",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "integration_type": "xiaomi",
                "status": "connected",
                "properties": {
                    "capabilities": ["power", "brightness", "color_temp"],
                    "supported_features": {
                        "brightness_range": [0, 100],
                        "color_temp_range": [2700, 6500]
                    }
                },
                "state": {
                    "power": "on",
                    "brightness": 80,
                    "color_temp": 4000
                },
                "created_at": "2025-04-17T11:33:03Z",
                "last_updated": "2025-04-17T11:33:03Z"
            }
        }
    )


# Automation schemas
class AutomationBase(BaseSchema):
    """Base schema for automation data."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: bool = True
    trigger_type: str
    trigger_config: Dict[str, Any]
    condition_type: str = "none"
    conditions: Optional[List[Dict[str, Any]]] = None
    action_type: str
    actions: List[Dict[str, Any]]


class AutomationCreate(AutomationBase):
    """Schema for automation creation."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Turn on lights at sunset",
                "description": "Automatically turn on living room lights at sunset",
                "enabled": True,
                "trigger_type": "time",
                "trigger_config": {
                    "type": "sunset",
                    "offset_minutes": -15
                },
                "condition_type": "none",
                "conditions": None,
                "action_type": "device",
                "actions": [
                    {
                        "device_id": "abc123",
                        "action": "set_state",
                        "parameters": {
                            "power": "on",
                            "brightness": 80
                        }
                    }
                ]
            }
        }
    )


class AutomationUpdate(BaseSchema):
    """Schema for automation update."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: Optional[bool] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    condition_type: Optional[str] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    action_type: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None


class AutomationInDB(AutomationBase):
    """Schema for automation in database."""
    id: str
    user_id: str
    created_at: datetime
    last_triggered: Optional[datetime] = None
    execution_count: int
    last_modified: datetime


class AutomationResponse(AutomationBase):
    """Schema for automation response."""
    id: str
    created_at: datetime
    last_triggered: Optional[datetime] = None
    execution_count: int
    last_modified: datetime


# Event schemas
class EventBase(BaseSchema):
    """Base schema for event data."""
    type: str
    source: str
    data: Optional[Dict[str, Any]] = None


class EventCreate(EventBase):
    """Schema for event creation."""
    device_id: Optional[str] = None


class EventInDB(EventBase):
    """Schema for event in database."""
    id: str
    device_id: Optional[str] = None
    timestamp: datetime
    processed: bool


class EventResponse(EventBase):
    """Schema for event response."""
    id: str
    device_id: Optional[str] = None
    timestamp: datetime
    processed: bool


# System schemas
class SystemStatus(BaseSchema):
    """Schema for system status."""
    status: str
    version: str
    uptime: str
    device_count: int
    automation_count: int
    last_event: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "running",
                "version": "0.1.0",
                "uptime": "1d 2h 34m",
                "device_count": 5,
                "automation_count": 3,
                "last_event": "2025-04-05T20:15:30Z"
            }
        }
    )


class SystemStats(BaseSchema):
    """Schema for system statistics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    device_stats: Dict[str, Any]
    automation_stats: Dict[str, Any]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpu_usage": 12.5,
                "memory_usage": 34.2,
                "disk_usage": 45.7,
                "device_stats": {
                    "total": 5,
                    "online": 4,
                    "offline": 1,
                    "by_type": {
                        "light": 2,
                        "switch": 1,
                        "sensor": 2
                    }
                },
                "automation_stats": {
                    "total": 3,
                    "enabled": 2,
                    "disabled": 1,
                    "executions_today": 15
                }
            }
        }
    )


# Integration schemas
class IntegrationInfo(BaseSchema):
    """Schema for integration information."""
    type: str
    name: str
    description: str
    enabled: bool
    device_types: List[str]
    config_schema: Dict[str, Any]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "xiaomi",
                "name": "Xiaomi Mi Home",
                "description": "Integration with Xiaomi Mi Home devices",
                "enabled": True,
                "device_types": ["light", "switch", "sensor", "vacuum"],
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "ip_address": {"type": "string"},
                        "token": {"type": "string"}
                    },
                    "required": ["ip_address", "token"]
                }
            }
        }
    )


class IntegrationSetup(BaseSchema):
    """Schema for integration setup."""
    config: Dict[str, Any]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "config": {
                    "client_id": "abc123",
                    "client_secret": "xyz789",
                    "redirect_uri": "http://localhost:8000/api/integrations/alexa/callback"
                }
            }
        }
    )
