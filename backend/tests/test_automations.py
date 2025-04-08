import pytest
from fastapi.testclient import TestClient
import uuid

@pytest.fixture
def test_automation(authorized_client, test_db, test_device):
    """Create a test automation for testing."""
    automation_data = {
        "name": "Test Automation",
        "description": "Test automation for unit tests",
        "enabled": True,
        "trigger": {
            "type": "time",
            "config": {
                "time": "08:00",
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            }
        },
        "conditions": [],
        "actions": [
            {
                "type": "device_command",
                "config": {
                    "device_id": test_device["id"],
                    "command": "turn_on",
                    "params": {}
                }
            }
        ],
        "condition_type": "and"
    }
    
    response = authorized_client.post("/api/automations", json=automation_data)
    assert response.status_code == 201
    return response.json()

def test_create_automation(authorized_client, test_db, test_device):
    """Test creating a new automation."""
    automation_data = {
        "name": "Morning Routine",
        "description": "Turn on lights in the morning",
        "enabled": True,
        "trigger": {
            "type": "time",
            "config": {
                "time": "07:00",
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            }
        },
        "conditions": [],
        "actions": [
            {
                "type": "device_command",
                "config": {
                    "device_id": test_device["id"],
                    "command": "turn_on",
                    "params": {}
                }
            }
        ],
        "condition_type": "and"
    }
    
    response = authorized_client.post("/api/automations", json=automation_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == automation_data["name"]
    assert data["description"] == automation_data["description"]
    assert data["enabled"] == automation_data["enabled"]
    assert data["trigger"]["type"] == automation_data["trigger"]["type"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_get_automations(authorized_client, test_automation):
    """Test getting all automations."""
    response = authorized_client.get("/api/automations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(automation["id"] == test_automation["id"] for automation in data)

def test_get_automation(authorized_client, test_automation):
    """Test getting a specific automation."""
    response = authorized_client.get(f"/api/automations/{test_automation['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_automation["id"]
    assert data["name"] == test_automation["name"]
    assert data["trigger"]["type"] == test_automation["trigger"]["type"]

def test_get_automation_not_found(authorized_client):
    """Test getting a non-existent automation."""
    non_existent_id = str(uuid.uuid4())
    response = authorized_client.get(f"/api/automations/{non_existent_id}")
    assert response.status_code == 404

def test_update_automation(authorized_client, test_automation):
    """Test updating an automation."""
    update_data = {
        "name": "Updated Automation Name",
        "description": test_automation["description"],
        "enabled": test_automation["enabled"],
        "trigger": test_automation["trigger"],
        "conditions": test_automation["conditions"],
        "actions": test_automation["actions"],
        "condition_type": test_automation["condition_type"]
    }
    
    response = authorized_client.put(f"/api/automations/{test_automation['id']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_automation["id"]
    assert data["name"] == update_data["name"]
    assert data["updated_at"] != test_automation["updated_at"]

def test_toggle_automation(authorized_client, test_automation):
    """Test toggling an automation's enabled state."""
    toggle_data = {
        "enabled": not test_automation["enabled"]
    }
    
    response = authorized_client.post(f"/api/automations/{test_automation['id']}/toggle", json=toggle_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_automation["id"]
    assert data["enabled"] == toggle_data["enabled"]

def test_delete_automation(authorized_client, test_automation):
    """Test deleting an automation."""
    response = authorized_client.delete(f"/api/automations/{test_automation['id']}")
    assert response.status_code == 204
    
    # Verify the automation is deleted
    response = authorized_client.get(f"/api/automations/{test_automation['id']}")
    assert response.status_code == 404

def test_duplicate_automation(authorized_client, test_automation):
    """Test duplicating an automation."""
    response = authorized_client.post(f"/api/automations/{test_automation['id']}/duplicate")
    assert response.status_code == 201
    data = response.json()
    assert data["name"].startswith("Copy of ")
    assert data["name"].endswith(test_automation["name"])
    assert data["id"] != test_automation["id"]
    assert data["trigger"]["type"] == test_automation["trigger"]["type"]
    assert data["actions"] == test_automation["actions"]

def test_unauthorized_access(client, test_automation):
    """Test accessing automations without authentication."""
    response = client.get("/api/automations")
    assert response.status_code == 401
    
    response = client.get(f"/api/automations/{test_automation['id']}")
    assert response.status_code == 401
    
    response = client.post("/api/automations", json={"name": "Unauthorized Automation"})
    assert response.status_code == 401
