"""
Violt Core Lite - Main Application

This module initializes the FastAPI application and includes all routers.
"""

from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles
from .database.session import initialize_database, get_db
from .core.config import settings
from .core.websocket import (
    get_token_from_query,
    get_current_user,
    handle_device_updates,
    handle_automation_updates,
    handle_event_updates,
    send_device_update,
    send_automation_update,
    send_event_notification,
)
from sqlalchemy.ext.asyncio import AsyncSession

import os
import logging
import importlib
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local-only, open-source smart home automation platform",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger = logging.getLogger(__name__)

    # First, ensure models are imported
    try:
        logger.info("Importing models...")
        # Import all models to register them with SQLAlchemy metadata
        from .database.models import Base

        # Import user model explicitly to ensure it's registered
        from .database.models import User

        logger.info(
            f"Models imported successfully. Tables defined: {Base.metadata.tables.keys()}"
        )
    except ImportError as e:
        logger.error(f"Failed to import models: {e}")
        # Continue running as tables may still be created

    try:
        logger.info("Initializing database tables...")
        # Initialize the database
        await initialize_database()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # Don't exit - let the application keep running
        # The error will be logged, but API endpoints might fail


# Include routers - moved here to prevent circular imports
from .api.auth import router as auth_router
from .api.devices import router as devices_router
from .api.automations import router as automations_router
from .api.system import router as system_router
from .api.integrations import router as integrations_router
from .api.events import router as events_router


# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2025-04-05T20:24:00Z",
    }


# API endpoints
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices_router.router, prefix="/api/devices", tags=["Devices"])
app.include_router(
    automations_router.router, prefix="/api/automations", tags=["Automations"]
)
app.include_router(system_router.router, prefix="/api/system", tags=["System"])
app.include_router(
    integrations_router.router, prefix="/api/integrations", tags=["Integrations"]
)
app.include_router(events_router.router, prefix="/api/events", tags=["Events"])


# Websocket endpoints
@app.websocket("/ws/devices")
async def ws_devices(
    websocket: WebSocket,
    token: str = Depends(get_token_from_query),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token, db)
    logger.info(f"WebSocket /ws/devices handshake for user {user.id}")
    await handle_device_updates(websocket, user)


@app.websocket("/ws/automations")
async def ws_automations(
    websocket: WebSocket,
    token: str = Depends(get_token_from_query),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token, db)
    logger.info(f"WebSocket /ws/automations handshake for user {user.id}")
    await handle_automation_updates(websocket, user)


@app.websocket("/ws/events")
async def ws_events(
    websocket: WebSocket,
    token: str = Depends(get_token_from_query),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token, db)
    logger.info(f"WebSocket /ws/events handshake for user {user.id}")
    await handle_event_updates(websocket, user)


@app.websocket("/ws/send/devices")
async def ws_send_devices(
    websocket: WebSocket,
    token: str = Depends(get_token_from_query),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token, db)
    logger.info(f"WebSocket /ws/send/devices handshake for user {user.id}")
    await send_device_update(websocket, user)


@app.websocket("/ws/send/automations")
async def ws_send_automations(
    websocket: WebSocket,
    token: str = Depends(get_token_from_query),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token, db)
    logger.info(f"WebSocket /ws/send/automations handshake for user {user.id}")
    await send_automation_update(websocket, user)


@app.websocket("/ws/send/events")
async def ws_send_events(
    websocket: WebSocket,
    token: str = Depends(get_token_from_query),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token, db)
    logger.info(f"WebSocket /ws/send/events handshake for user {user.id}")
    await send_event_notification(websocket, user)


# Mount static files
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(
        f"Static directory '{static_dir}' not found. Static files will not be served."
    )
