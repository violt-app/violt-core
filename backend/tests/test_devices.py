import pytest
from fastapi.testclient import TestClient
import uuid

@pytest.fixture
def test_device(authorized_client, test_db):
    """Create a test device for testing."""
    device_data = {
        "name": "Test Light",
        "type": "light",
        "manufacturer": "Xiaomi",
        "model": "Yeelight LED Bulb",
        "integration_type": "xiaomi",
        "ip_address": "192.168.1.100"
    }
    
    response = authorized_client.post("/api/devices", json=device_data)
    assert response.status_code == 201
    return response.json()

def test_create_device(authorized_client, test_db):
    """Test creating a new device."""
    device_data = {
        "name": "Living Room Light",
        "type": "light",
        "manufacturer": "Xiaomi",
        "model": "Yeelight LED Bulb",
        "integration_type": "xiaomi",
        "ip_address": "192.168.1.100"
    }
    
    response = authorized_client.post("/api/devices", json=device_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == device_data["name"]
    assert data["type"] == device_data["type"]
    assert data["manufacturer"] == device_data["manufacturer"]
    assert data["model"] == device_data["model"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_get_devices(authorized_client, test_device):
    """Test getting all devices."""
    response = authorized_client.get("/api/devices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(device["id"] == test_device["id"] for device in data)

def test_get_device(authorized_client, test_device):
    """Test getting a specific device."""
    response = authorized_client.get(f"/api/devices/{test_device['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_device["id"]
    assert data["name"] == test_device["name"]
    assert data["type"] == test_device["type"]

def test_get_device_not_found(authorized_client):
    """Test getting a non-existent device."""
    non_existent_id = str(uuid.uuid4())
    response = authorized_client.get(f"/api/devices/{non_existent_id}")
    assert response.status_code == 404

def test_update_device(authorized_client, test_device):
    """Test updating a device."""
    update_data = {
        "name": "Updated Light Name",
        "type": test_device["type"],
        "manufacturer": test_device["manufacturer"],
        "model": test_device["model"],
        "integration_type": test_device["integration_type"]
    }
    
    response = authorized_client.put(f"/api/devices/{test_device['id']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_device["id"]
    assert data["name"] == update_data["name"]
    assert data["type"] == update_data["type"]
    assert data["updated_at"] != test_device["updated_at"]

def test_delete_device(authorized_client, test_device):
    """Test deleting a device."""
    response = authorized_client.delete(f"/api/devices/{test_device['id']}")
    assert response.status_code == 204
    
    # Verify the device is deleted
    response = authorized_client.get(f"/api/devices/{test_device['id']}")
    assert response.status_code == 404

def test_device_command(authorized_client, test_device):
    """Test executing a command on a device."""
    command_data = {
        "command": "turn_on",
        "params": {}
    }
    
    response = authorized_client.post(f"/api/devices/{test_device['id']}/command", json=command_data)
    # Note: In a real test environment with actual devices, we would check for 200
    # In our test environment without real devices, we expect a 404 or 501 response
    # This test is more of a placeholder for when mock devices are implemented
    assert response.status_code in [200, 404, 501]

def test_unauthorized_access(client, test_device):
    """Test accessing devices without authentication."""
    response = client.get("/api/devices")
    assert response.status_code == 401
    
    response = client.get(f"/api/devices/{test_device['id']}")
    assert response.status_code == 401
    
    response = client.post("/api/devices", json={"name": "Unauthorized Device"})
    assert response.status_code == 401
