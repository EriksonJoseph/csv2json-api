import os
import pytest
import asyncio
from fastapi import UploadFile
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open, MagicMock, AsyncMock
import json
import tempfile
import shutil
from pathlib import Path

from app.main import app
from app.config import get_settings

# Constants
TEST_FILE_PATH = os.path.join(os.path.dirname(__file__), '../../data/sample_from_gg_sheet_snippet - Sheet1.csv')
TEMP_DIR = tempfile.gettempdir()

@pytest.fixture
def test_client(monkeypatch):
    """Create a test client with temp dirs for uploads."""
    # Create temp dirs for testing
    temp_upload_dir = os.path.join(TEMP_DIR, 'uploads')
    temp_processed_dir = os.path.join(TEMP_DIR, 'processed')
    
    os.makedirs(temp_upload_dir, exist_ok=True)
    os.makedirs(temp_processed_dir, exist_ok=True)
    
    # Patch settings to use temp dirs
    settings = get_settings()
    original_upload_dir = settings.UPLOAD_DIR
    original_processed_dir = settings.PROCESSED_DIR
    
    monkeypatch.setattr(settings, 'UPLOAD_DIR', temp_upload_dir)
    monkeypatch.setattr(settings, 'PROCESSED_DIR', temp_processed_dir)
    
    # Return test client
    with TestClient(app) as client:
        yield client
    
    # Cleanup
    try:
        shutil.rmtree(temp_upload_dir)
        shutil.rmtree(temp_processed_dir)
    except:
        pass


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


@pytest.mark.asyncio
async def test_upload_file(test_client, auth_headers, monkeypatch, mock_db):
    """Test uploading a file."""
    # Mock the background task processing
    mock_process_task = AsyncMock()
    monkeypatch.setattr("app.routers.file.file_router.process_file_task", mock_process_task)
    
    # Prepare test file
    file_content = open(TEST_FILE_PATH, 'rb').read()
    
    # Mock the UploadFile
    with patch('app.routers.file.file_router.save_upload_file', 
               new_callable=AsyncMock) as mock_save:
        # Set up the mock to return a file path
        test_filename = "test_upload.csv"
        mock_save.return_value = os.path.join(get_settings().UPLOAD_DIR, test_filename)
        
        # Mock FileService.register_file
        with patch('app.services.file_service.FileService.register_file', 
                  new_callable=AsyncMock) as mock_register:
            # Set up the mock to return a file record
            mock_register.return_value = {
                "_id": "test_file_id",
                "filename": test_filename,
                "original_filename": "sample_from_gg_sheet_snippet - Sheet1.csv",
                "file_path": os.path.join(get_settings().UPLOAD_DIR, test_filename),
                "file_type": "csv",
                "status": "pending",
                "created_at": "2025-06-01T10:00:00Z",
                "user_id": "test_user_id"
            }
            
            # Create the test file
            files = {
                "file": ("sample_from_gg_sheet_snippet - Sheet1.csv", file_content, "text/csv")
            }
            
            # Make the request
            response = test_client.post(
                "/api/files/upload",
                files=files,
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == test_filename
    assert data["status"] == "pending"
    assert mock_process_task.called


@pytest.mark.asyncio
async def test_get_file_list(test_client, auth_headers, mock_db):
    """Test getting file list."""
    # Mock the FileService.get_files method
    with patch('app.services.file_service.FileService.get_files', 
              new_callable=AsyncMock) as mock_get_files:
        # Set up mock return value
        mock_get_files.return_value = [
            {
                "_id": "file_id_1",
                "filename": "file1.csv",
                "original_filename": "original_file1.csv",
                "file_type": "csv",
                "status": "completed",
                "created_at": "2025-06-01T10:00:00Z",
                "user_id": "test_user_id"
            },
            {
                "_id": "file_id_2",
                "filename": "file2.csv",
                "original_filename": "original_file2.csv",
                "file_type": "csv",
                "status": "pending",
                "created_at": "2025-06-01T11:00:00Z",
                "user_id": "test_user_id"
            }
        ]
        
        # Make the request
        response = test_client.get(
            "/api/files",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["filename"] == "file1.csv"
    assert data[1]["filename"] == "file2.csv"


@pytest.mark.asyncio
async def test_get_file_by_id(test_client, auth_headers, mock_db):
    """Test getting a file by ID."""
    file_id = "test_file_id"
    
    # Mock the FileService.get_file_by_id method
    with patch('app.services.file_service.FileService.get_file_by_id', 
              new_callable=AsyncMock) as mock_get_file:
        # Set up mock return value
        mock_get_file.return_value = {
            "_id": file_id,
            "filename": "test_file.csv",
            "original_filename": "original_test_file.csv",
            "file_type": "csv",
            "status": "completed",
            "created_at": "2025-06-01T10:00:00Z",
            "user_id": "test_user_id",
            "processed_path": "/path/to/processed/file.json"
        }
        
        # Make the request
        response = test_client.get(
            f"/api/files/{file_id}",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == file_id
    assert data["filename"] == "test_file.csv"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_download_processed_file(test_client, auth_headers, mock_db):
    """Test downloading a processed file."""
    file_id = "test_file_id"
    
    # Create a test JSON file
    test_json = {"data": [{"column1": "value1", "column2": "value2"}]}
    test_json_path = os.path.join(TEMP_DIR, "test_processed.json")
    with open(test_json_path, "w") as f:
        json.dump(test_json, f)
    
    # Mock the FileService.get_file_by_id method
    with patch('app.services.file_service.FileService.get_file_by_id', 
              new_callable=AsyncMock) as mock_get_file:
        # Set up mock return value
        mock_get_file.return_value = {
            "_id": file_id,
            "filename": "test_file.csv",
            "original_filename": "original_test_file.csv",
            "file_type": "csv",
            "status": "completed",
            "created_at": "2025-06-01T10:00:00Z",
            "user_id": "test_user_id",
            "processed_path": test_json_path
        }
        
        # Make the request
        response = test_client.get(
            f"/api/files/{file_id}/download",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
    
    # Clean up
    os.remove(test_json_path)


@pytest.mark.asyncio
async def test_delete_file(test_client, auth_headers, mock_db):
    """Test deleting a file."""
    file_id = "test_file_id"
    
    # Mock the FileService.delete_file method
    with patch('app.services.file_service.FileService.delete_file', 
              new_callable=AsyncMock) as mock_delete_file:
        # Set up mock return value
        mock_delete_file.return_value = True
        
        # Make the request
        response = test_client.delete(
            f"/api/files/{file_id}",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "file deleted successfully" in data["message"].lower()
