"""
Violt Core Lite - API Router for Authentication

This module handles authentication API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from ...core.schemas import UserCreate, UserResponse, Token, LoginRequest
from ...core.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user,
)
from ...database.session import get_db
from ...database.models import User

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to register new user with username: {user_data.username}")
    
    # Log the validation requirements
    logger.debug(f"Validating registration data - Name: {len(user_data.name)} chars, Username: {len(user_data.username)} chars")
    
    # Check if username already exists
    result = await db.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": user_data.username},
    )
    if result.scalar_one_or_none():
        logger.warning(f"Registration failed: Username '{user_data.username}' is already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    result = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": user_data.email},
    )
    if result.scalar_one_or_none():
        logger.warning(f"Registration failed: Email '{user_data.email}' is already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Log if terms are accepted
    if user_data.terms_accepted:
        logger.info(f"User '{user_data.username}' has accepted terms and conditions")
    else:
        logger.info(f"User '{user_data.username}' has not accepted terms and conditions")

    try:
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            name=user_data.name,
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            terms_accepted=user_data.terms_accepted,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"Successfully registered new user: {user_data.username}")
        return new_user
    except Exception as e:
        logger.error(f"Failed to create user '{user_data.username}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Login and get access token using OAuth2 form."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token)
async def login_json(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login and get access token using JSON request."""
    user = await authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.post("/terms", response_model=UserResponse)
async def accept_terms(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept terms and conditions."""
    current_user.terms_accepted = True
    await db.commit()
    await db.refresh(current_user)
    return current_user
