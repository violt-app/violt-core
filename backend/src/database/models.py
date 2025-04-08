"""
Violt Core Lite - Database Models

This module defines the SQLAlchemy ORM models for the application.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from .session import Base

Base = declarative_base()

def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication and preferences."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    settings = Column(JSON, nullable=True)
    terms_accepted = Column(Boolean, default=False, nullable=False)

    # Relationships
    devices = relationship(
        "Device", back_populates="user", cascade="all, delete-orphan"
    )
    automations = relationship(
        "Automation", back_populates="user", cascade="all, delete-orphan"
    )


class Device(Base):
    """Device model for smart home devices."""

    __tablename__ = "devices"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=True)
    location = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    status = Column(String, default="offline", nullable=False)
    properties = Column(JSON, nullable=True)
    state = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    integration_type = Column(String, nullable=False)
    config = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="devices")
    events = relationship(
        "Event", back_populates="device", cascade="all, delete-orphan"
    )


class Automation(Base):
    """Automation model for IF/THEN rules."""

    __tablename__ = "automations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    trigger_type = Column(String, nullable=False)
    trigger_config = Column(JSON, nullable=False)
    condition_type = Column(String, default="none", nullable=False)
    conditions = Column(JSON, nullable=True)
    action_type = Column(String, nullable=False)
    actions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_triggered = Column(DateTime, nullable=True)
    execution_count = Column(Integer, default=0, nullable=False)
    last_modified = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="automations")


class Event(Base):
    """Event model for system events."""

    __tablename__ = "events"

    id = Column(String, primary_key=True, default=generate_uuid)
    device_id = Column(String, ForeignKey("devices.id"), nullable=True)
    type = Column(String, nullable=False)
    source = Column(String, nullable=False)
    data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)

    # Relationships
    device = relationship("Device", back_populates="events")


class Log(Base):
    """Log model for system logs."""

    __tablename__ = "logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    level = Column(String, nullable=False)
    source = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
