import pytest
from fastapi.testclient import TestClient

def test_auth_register(client: TestClient, test_db):
    """Test user registration endpoint."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "New User"
    assert "id" in data["user"]

def test_auth_register_duplicate_email(client: TestClient, test_user, test_db):
    """Test registration with duplicate email."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Another User",
            "email": test_user["email"],  # Use existing email
            "password": "password123"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already registered" in data["detail"].lower()

def test_auth_login_success(client: TestClient, test_user, test_db):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == test_user["email"]
    assert data["user"]["name"] == test_user["name"]
    assert data["user"]["id"] == test_user["id"]

def test_auth_login_invalid_credentials(client: TestClient, test_user, test_db):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "incorrect" in data["detail"].lower()

def test_auth_me(authorized_client: TestClient, test_user):
    """Test getting current user information."""
    response = authorized_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["name"] == test_user["name"]
    assert data["id"] == test_user["id"]

def test_auth_me_unauthorized(client: TestClient):
    """Test getting user info without authentication."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
