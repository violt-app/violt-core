import pytest
from fastapi.testclient import TestClient

def test_system_status(authorized_client):
    """Test getting system status."""
    response = authorized_client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "uptime" in data
    assert "device_count" in data
    assert "automation_count" in data
    assert "cpu_usage" in data
    assert "memory_usage" in data
    assert "disk_usage" in data
    assert "connected_clients" in data

def test_system_logs(authorized_client):
    """Test getting system logs."""
    response = authorized_client.get("/api/system/logs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # If logs exist, check their structure
    if data:
        log = data[0]
        assert "id" in log
        assert "timestamp" in log
        assert "level" in log
        assert "source" in log
        assert "message" in log

def test_system_logs_with_limit(authorized_client):
    """Test getting system logs with a limit."""
    limit = 5
    response = authorized_client.get(f"/api/system/logs?limit={limit}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= limit

def test_system_logs_with_level_filter(authorized_client):
    """Test getting system logs filtered by level."""
    response = authorized_client.get("/api/system/logs?level=error")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # If logs exist, check they all have the correct level
    for log in data:
        assert log["level"] == "error"

def test_system_restart(authorized_client):
    """Test system restart endpoint."""
    # Note: In a real test environment, we would mock the restart function
    # Here we just check that the endpoint exists and returns the expected response
    response = authorized_client.post("/api/system/restart")
    assert response.status_code in [200, 202]
    
    if response.status_code == 200:
        data = response.json()
        assert "message" in data
        assert "restart" in data["message"].lower()

def test_unauthorized_access(client):
    """Test accessing system endpoints without authentication."""
    response = client.get("/api/system/status")
    assert response.status_code == 401
    
    response = client.get("/api/system/logs")
    assert response.status_code == 401
    
    response = client.post("/api/system/restart")
    assert response.status_code == 401
