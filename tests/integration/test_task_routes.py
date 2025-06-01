import os
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime, timedelta

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
async def test_get_tasks(test_client, auth_headers, mock_db):
    """Test getting all tasks."""
    # Mock the TaskService.get_tasks method
    with patch('app.services.task_service.TaskService.get_tasks', 
              new_callable=AsyncMock) as mock_get_tasks:
        # Set up mock return value
        mock_get_tasks.return_value = [
            {
                "_id": "task_id_1",
                "task_type": "csv_conversion",
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "file_id": "file_id_1",
                "user_id": "test_user_id",
                "result": {"processed_file": "/path/to/processed1.json"}
            },
            {
                "_id": "task_id_2",
                "task_type": "csv_conversion",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "file_id": "file_id_2",
                "user_id": "test_user_id",
                "result": None
            }
        ]
        
        # Make the request
        response = test_client.get(
            "/api/tasks",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["_id"] == "task_id_1"
    assert data[0]["status"] == "completed"
    assert data[1]["_id"] == "task_id_2"
    assert data[1]["status"] == "pending"

@pytest.mark.asyncio
async def test_get_task_by_id(test_client, auth_headers, mock_db):
    """Test getting a task by ID."""
    task_id = "test_task_id"
    
    # Mock the TaskService.get_task_by_id method
    with patch('app.services.task_service.TaskService.get_task_by_id', 
              new_callable=AsyncMock) as mock_get_task:
        # Set up mock return value
        mock_get_task.return_value = {
            "_id": task_id,
            "task_type": "csv_conversion",
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "file_id": "file_id_1",
            "user_id": "test_user_id",
            "result": {"processed_file": "/path/to/processed.json"}
        }
        
        # Make the request
        response = test_client.get(
            f"/api/tasks/{task_id}",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == task_id
    assert data["status"] == "completed"
    assert data["task_type"] == "csv_conversion"

@pytest.mark.asyncio
async def test_cancel_task(test_client, auth_headers, mock_db):
    """Test cancelling a task."""
    task_id = "test_task_id"
    
    # Mock the TaskService.update_task_status method
    with patch('app.services.task_service.TaskService.update_task_status', 
              new_callable=AsyncMock) as mock_update_status:
        # Set up mock return value
        mock_update_status.return_value = {
            "_id": task_id,
            "task_type": "csv_conversion",
            "status": "cancelled",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "file_id": "file_id_1",
            "user_id": "test_user_id",
            "result": None
        }
        
        # Make the request
        response = test_client.put(
            f"/api/tasks/{task_id}/cancel",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == task_id
    assert data["status"] == "cancelled"
    
@pytest.mark.asyncio
async def test_retry_task(test_client, auth_headers, mock_db):
    """Test retrying a failed task."""
    task_id = "test_task_id"
    
    # Mock the TaskService.retry_task method
    with patch('app.services.task_service.TaskService.retry_task', 
              new_callable=AsyncMock) as mock_retry_task:
        # Set up mock return value
        mock_retry_task.return_value = {
            "_id": task_id,
            "task_type": "csv_conversion",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "file_id": "file_id_1",
            "user_id": "test_user_id",
            "result": None,
            "retry_count": 1
        }
        
        # Make the request
        response = test_client.put(
            f"/api/tasks/{task_id}/retry",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == task_id
    assert data["status"] == "pending"
    assert data["retry_count"] == 1

@pytest.mark.asyncio
async def test_admin_get_all_tasks(test_client, admin_headers, mock_db):
    """Test admin getting all tasks in the system."""
    # Mock the TaskService.get_all_tasks method
    with patch('app.services.task_service.TaskService.get_all_tasks', 
              new_callable=AsyncMock) as mock_get_all_tasks:
        # Set up mock return value - admin should see all tasks
        mock_get_all_tasks.return_value = [
            {
                "_id": "task_id_1",
                "task_type": "csv_conversion",
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "file_id": "file_id_1",
                "user_id": "user_id_1",
                "result": {"processed_file": "/path/to/processed1.json"}
            },
            {
                "_id": "task_id_2",
                "task_type": "csv_conversion",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "file_id": "file_id_2",
                "user_id": "user_id_2",
                "result": None
            },
            {
                "_id": "task_id_3",
                "task_type": "csv_conversion",
                "status": "failed",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "file_id": "file_id_3",
                "user_id": "user_id_3",
                "result": {"error": "File format error"}
            }
        ]
        
        # Make the request with admin headers
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": "admin_id",
                "username": "admin",
                "email": "admin@example.com",
                "roles": ["admin"]
            }
            
            response = test_client.get(
                "/api/tasks/all",
                headers=admin_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["user_id"] == "user_id_1"
    assert data[1]["user_id"] == "user_id_2"
    assert data[2]["user_id"] == "user_id_3"
