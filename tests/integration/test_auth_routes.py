import pytest
from fastapi.testclient import TestClient
import json
from datetime import datetime

pytestmark = pytest.mark.integration

def test_login_route(test_client, test_user):
    """Test the login endpoint."""
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    
    response = test_client.post("/api/auth/login", json=login_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0

def test_login_route_invalid_credentials(test_client, test_user):
    """Test login with invalid credentials."""
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    
    response = test_client.post("/api/auth/login", json=login_data)
    
    # Check response
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "Invalid username or password" in data["detail"]

def test_register_route(test_client):
    """Test the register endpoint."""
    user_data = {
        "username": "newreguser",
        "password": "password123",
        "email": "newreg@example.com",
        "full_name": "New Register User"
    }
    
    response = test_client.post("/api/auth/register", json=user_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["username"] == "newreguser"
    assert data["email"] == "newreg@example.com"
    assert "password" not in data  # Password should not be returned

def test_me_route_authenticated(test_client, token_headers):
    """Test the me endpoint with valid authentication."""
    response = test_client.get("/api/auth/me", headers=token_headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "username" in data
    assert data["username"] == "testuser"
    assert "roles" in data

def test_me_route_unauthenticated(test_client):
    """Test the me endpoint without authentication."""
    response = test_client.get("/api/auth/me")
    
    # Check response
    assert response.status_code in [401, 403]  # Depends on your auth implementation
    data = response.json()
    assert "detail" in data  # Should contain an error message

def test_unlock_user_route(test_client, test_user, admin_token_headers):
    """Test the unlock user endpoint."""
    user_id = test_user.get("user_id")
    
    # Admin should be able to unlock a user
    response = test_client.post(f"/api/auth/unlock/{user_id}", headers=admin_token_headers)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "User unlocked successfully" in data["message"]

def test_unlock_user_unauthorized(test_client, test_user, token_headers):
    """Test the unlock user endpoint without admin privileges."""
    user_id = test_user.get("user_id")
    
    # Regular user should not be able to unlock another user
    response = test_client.post(f"/api/auth/unlock/{user_id}", headers=token_headers)
    
    # Check response - should be unauthorized
    assert response.status_code in [401, 403]
    data = response.json()
    assert "detail" in data  # Should contain an error message

def test_login_history_route(test_client, test_user, admin_token_headers):
    """Test the login history endpoint."""
    user_id = test_user.get("user_id")
    
    # Admin should be able to view login history
    response = test_client.get(f"/api/auth/login_history/{user_id}", headers=admin_token_headers)
    
    # Check response
    assert response.status_code == 200
