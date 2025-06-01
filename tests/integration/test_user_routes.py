import os
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.main import app

@pytest.fixture
def test_client():
    """Create a test client."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def auth_headers(test_client):
    """Get auth headers for protected endpoints."""
    # Login to get token
    login_data = {"username": "testuser", "password": "password123"}
    with patch('app.routers.auth.auth_router.AuthService.authenticate', 
               new_callable=AsyncMock) as mock_auth:
        # Mock successful authentication
        mock_auth.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer"
        }
        response = test_client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}

@pytest.fixture
def admin_headers(test_client):
    """Get admin auth headers for protected endpoints."""
    # Login to get token
    login_data = {"username": "admin", "password": "admin123"}
    with patch('app.routers.auth.auth_router.AuthService.authenticate', 
               new_callable=AsyncMock) as mock_auth:
        # Mock successful authentication with admin role
        mock_auth.return_value = {
            "access_token": "admin_access_token",
            "refresh_token": "admin_refresh_token",
            "token_type": "bearer"
        }
        
        # Mock the get_current_user to return admin
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": "admin_id",
                "username": "admin",
                "email": "admin@example.com",
                "roles": ["admin"]
            }
            response = test_client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}

@pytest.mark.asyncio
async def test_get_current_user(test_client, auth_headers, mock_db):
    """Test getting current user profile."""
    # Mock the get_current_user dependency
    with patch('app.dependencies.auth.get_current_user', 
              new_callable=AsyncMock) as mock_user:
        # Set up mock return value
        mock_user.return_value = {
            "_id": "test_user_id",
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "roles": ["user"],
            "created_at": "2025-06-01T10:00:00Z"
        }
        
        # Make the request
        response = test_client.get(
            "/api/users/me",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "user" in data["roles"]

@pytest.mark.asyncio
async def test_update_user_profile(test_client, auth_headers, mock_db):
    """Test updating user profile."""
    # Mock user data
    user_id = "test_user_id"
    
    # Mock the UserService.update_user method
    with patch('app.services.user_service.UserService.update_user', 
              new_callable=AsyncMock) as mock_update_user:
        # Set up mock return value
        mock_update_user.return_value = {
            "_id": user_id,
            "username": "testuser",
            "email": "updated@example.com",
            "full_name": "Updated Name",
            "roles": ["user"],
            "created_at": "2025-06-01T10:00:00Z",
            "updated_at": "2025-06-01T11:00:00Z"
        }
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": user_id,
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "roles": ["user"],
                "created_at": "2025-06-01T10:00:00Z"
            }
            
            # Make the request
            update_data = {
                "email": "updated@example.com",
                "full_name": "Updated Name"
            }
            response = test_client.put(
                "/api/users/me",
                json=update_data,
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
    assert data["full_name"] == "Updated Name"

@pytest.mark.asyncio
async def test_change_password(test_client, auth_headers, mock_db):
    """Test changing user password."""
    # Mock user data
    user_id = "test_user_id"
    
    # Mock the UserService.change_password method
    with patch('app.services.user_service.UserService.change_password', 
              new_callable=AsyncMock) as mock_change_password:
        # Set up mock return value
        mock_change_password.return_value = True
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": user_id,
                "username": "testuser",
                "email": "test@example.com",
                "roles": ["user"]
            }
            
            # Make the request
            password_data = {
                "current_password": "password123",
                "new_password": "new_password123"
            }
            response = test_client.put(
                "/api/users/me/password",
                json=password_data,
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

@pytest.mark.asyncio
async def test_admin_get_all_users(test_client, admin_headers, mock_db):
    """Test admin getting all users."""
    # Mock the UserService.get_all_users method
    with patch('app.services.user_service.UserService.get_all_users', 
              new_callable=AsyncMock) as mock_get_all_users:
        # Set up mock return value
        mock_get_all_users.return_value = [
            {
                "_id": "user_id_1",
                "username": "user1",
                "email": "user1@example.com",
                "full_name": "User One",
                "roles": ["user"],
                "created_at": "2025-06-01T10:00:00Z"
            },
            {
                "_id": "user_id_2",
                "username": "user2",
                "email": "user2@example.com",
                "full_name": "User Two",
                "roles": ["user"],
                "created_at": "2025-06-01T11:00:00Z"
            },
            {
                "_id": "admin_id",
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "Admin User",
                "roles": ["admin", "user"],
                "created_at": "2025-06-01T09:00:00Z"
            }
        ]
        
        # Mock the get_current_user to return admin
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": "admin_id",
                "username": "admin",
                "email": "admin@example.com",
                "roles": ["admin"]
            }
            
            # Make the request
            response = test_client.get(
                "/api/users",
                headers=admin_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["username"] == "user1"
    assert data[1]["username"] == "user2"
    assert data[2]["username"] == "admin"

@pytest.mark.asyncio
async def test_admin_create_user(test_client, admin_headers, mock_db):
    """Test admin creating a new user."""
    # Mock the UserService.create_user method
    with patch('app.services.user_service.UserService.create_user', 
              new_callable=AsyncMock) as mock_create_user:
        # Set up mock return value
        mock_create_user.return_value = {
            "_id": "new_user_id",
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "roles": ["user"],
            "created_at": "2025-06-01T12:00:00Z"
        }
        
        # Mock the get_current_user to return admin
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": "admin_id",
                "username": "admin",
                "email": "admin@example.com",
                "roles": ["admin"]
            }
            
            # Make the request
            user_data = {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
            response = test_client.post(
                "/api/users",
                json=user_data,
                headers=admin_headers
            )
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "user" in data["roles"]

@pytest.mark.asyncio
async def test_admin_update_user(test_client, admin_headers, mock_db):
    """Test admin updating a user."""
    # Mock user data
    user_id = "user_id_to_update"
    
    # Mock the UserService.update_user method
    with patch('app.services.user_service.UserService.update_user', 
              new_callable=AsyncMock) as mock_update_user:
        # Set up mock return value
        mock_update_user.return_value = {
            "_id": user_id,
            "username": "updateduser",
            "email": "updated@example.com",
            "full_name": "Updated User",
            "roles": ["user", "moderator"],
            "created_at": "2025-06-01T10:00:00Z",
            "updated_at": "2025-06-01T13:00:00Z"
        }
        
        # Mock the get_current_user to return admin
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": "admin_id",
                "username": "admin",
                "email": "admin@example.com",
                "roles": ["admin"]
            }
            
            # Make the request
            update_data = {
                "email": "updated@example.com",
                "full_name": "Updated User",
                "roles": ["user", "moderator"]
            }
            response = test_client.put(
                f"/api/users/{user_id}",
                json=update_data,
                headers=admin_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
    assert data["full_name"] == "Updated User"
    assert "moderator" in data["roles"]

@pytest.mark.asyncio
async def test_admin_delete_user(test_client, admin_headers, mock_db):
    """Test admin deleting a user."""
    # Mock user data
    user_id = "user_id_to_delete"
    
    # Mock the UserService.delete_user method
    with patch('app.services.user_service.UserService.delete_user', 
              new_callable=AsyncMock) as mock_delete_user:
        # Set up mock return value
        mock_delete_user.return_value = True
        
        # Mock the get_current_user to return admin
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": "admin_id",
                "username": "admin",
                "email": "admin@example.com",
                "roles": ["admin"]
            }
            
            # Make the request
            response = test_client.delete(
                f"/api/users/{user_id}",
                headers=admin_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
