import os
import pytest
import asyncio
import tempfile
import shutil
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime, timedelta

from app.main import app
from app.config import get_settings

# Constants
TEST_FILE_PATH = os.path.join(os.path.dirname(__file__), '../../data/sample_from_gg_sheet_snippet - Sheet1.csv')
TEMP_DIR = tempfile.gettempdir()

@pytest.fixture
def test_client(monkeypatch):
    """Create a test client with temp dirs for uploads."""
    # Create temp dirs for testing
    temp_upload_dir = os.path.join(TEMP_DIR, 'e2e_uploads')
    temp_processed_dir = os.path.join(TEMP_DIR, 'e2e_processed')
    
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

@pytest.mark.asyncio
async def test_complete_workflow(test_client, mock_db):
    """Test the complete user workflow from login to file processing and matching."""
    # Step 1: Register a user
    user_data = {
        "username": "e2euser",
        "password": "testpassword",
        "email": "e2e@example.com",
        "full_name": "End to End Test User"
    }
    
    # Mock user registration
    with patch('app.services.auth_service.AuthService.register', 
              new_callable=AsyncMock) as mock_register:
        # Set up mock return value
        mock_register.return_value = {
            "_id": "e2e_user_id",
            "username": user_data["username"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "roles": ["user"],
            "created_at": datetime.now().isoformat()
        }
        
        # Make the request
        response = test_client.post("/api/auth/register", json=user_data)
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    
    # Step 2: Login
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    
    # Mock authentication
    with patch('app.services.auth_service.AuthService.authenticate', 
              new_callable=AsyncMock) as mock_auth:
        # Set up mock return value
        mock_auth.return_value = {
            "access_token": "e2e_test_access_token",
            "refresh_token": "e2e_test_refresh_token",
            "token_type": "bearer"
        }
        
        # Make the request
        response = test_client.post("/api/auth/login", json=login_data)
    
    # Check response
    assert response.status_code == 200
    auth_data = response.json()
    assert "access_token" in auth_data
    assert "refresh_token" in auth_data
    
    # Create auth headers for subsequent requests
    auth_headers = {"Authorization": f"Bearer {auth_data['access_token']}"}
    
    # Step 3: Create a watchlist
    watchlist_data = {
        "name": "E2E Test Watchlist",
        "description": "Watchlist for end-to-end testing",
        "criteria": {
            "country": "IRQ",
            "gender": "M"
        }
    }
    
    # Mock the watchlist creation
    with patch('app.services.watchlist_service.WatchlistService.create_watchlist', 
              new_callable=AsyncMock) as mock_create_watchlist:
        # Set up mock return value
        mock_create_watchlist.return_value = {
            "_id": "e2e_watchlist_id",
            "name": watchlist_data["name"],
            "description": watchlist_data["description"],
            "criteria": watchlist_data["criteria"],
            "user_id": "e2e_user_id",
            "created_at": datetime.now().isoformat()
        }
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": "e2e_user_id",
                "username": user_data["username"],
                "email": user_data["email"],
                "roles": ["user"]
            }
            
            # Make the request
            response = test_client.post(
                "/api/watchlists",
                json=watchlist_data,
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 201
    watchlist = response.json()
    assert watchlist["name"] == watchlist_data["name"]
    assert watchlist["criteria"]["country"] == "IRQ"
    
    # Step 4: Upload a file
    # Prepare test file
    file_content = open(TEST_FILE_PATH, 'rb').read()
    
    # Mock the file upload
    with patch('app.routers.file.file_router.save_upload_file', 
              new_callable=AsyncMock) as mock_save:
        # Set up the mock to return a file path
        test_filename = "e2e_test_upload.csv"
        mock_save.return_value = os.path.join(get_settings().UPLOAD_DIR, test_filename)
        
        # Mock FileService.register_file
        with patch('app.services.file_service.FileService.register_file', 
                  new_callable=AsyncMock) as mock_register_file:
            # Set up the mock to return a file record
            file_record = {
                "_id": "e2e_file_id",
                "filename": test_filename,
                "original_filename": "sample_from_gg_sheet_snippet - Sheet1.csv",
                "file_path": os.path.join(get_settings().UPLOAD_DIR, test_filename),
                "file_type": "csv",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "user_id": "e2e_user_id"
            }
            mock_register_file.return_value = file_record
            
            # Mock background task
            with patch('app.routers.file.file_router.process_file_task', 
                      new_callable=AsyncMock) as mock_process_task:
                
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
    file_data = response.json()
    assert file_data["filename"] == test_filename
    assert file_data["status"] == "pending"
    
    # Step 5: Process file (simulate background task completion)
    with patch('app.services.file_service.FileService.get_file_by_id', 
              new_callable=AsyncMock) as mock_get_file:
        # Update file status to completed
        processed_file = file_record.copy()
        processed_file["status"] = "completed"
        processed_file["processed_path"] = os.path.join(get_settings().PROCESSED_DIR, "e2e_test_output.json")
        mock_get_file.return_value = processed_file
        
        # Mock file update
        with patch('app.services.file_service.FileService.update_file_status', 
                  new_callable=AsyncMock) as mock_update_file:
            mock_update_file.return_value = processed_file
            
            # Create task record
            task_record = {
                "_id": "e2e_task_id",
                "task_type": "csv_conversion",
                "status": "completed",
                "file_id": "e2e_file_id",
                "user_id": "e2e_user_id",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "result": {"processed_file": processed_file["processed_path"]}
            }
            
            # Mock task service
            with patch('app.services.task_service.TaskService.get_task_by_id', 
                      new_callable=AsyncMock) as mock_get_task:
                mock_get_task.return_value = task_record
                
                # Make the request to get task status
                response = test_client.get(
                    f"/api/tasks/e2e_task_id",
                    headers=auth_headers
                )
    
    # Check response
    assert response.status_code == 200
    task_data = response.json()
    assert task_data["status"] == "completed"
    
    # Step 6: Run watchlist against the file
    with patch('app.services.watchlist_service.WatchlistService.run_watchlist', 
              new_callable=AsyncMock) as mock_run_watchlist:
        # Set up mock return value
        mock_run_watchlist.return_value = {
            "_id": "e2e_match_id",
            "watchlist_id": "e2e_watchlist_id",
            "file_id": "e2e_file_id",
            "matches": [
                {
                    "row_index": 0,
                    "data": {
                        "Entity_logical_id": "13",
                        "Subject_type": "P",
                        "Naal_wholename": "Saddam Hussein Al-Tikriti",
                        "Naal_gender": "M",
                        "Citi_country": "IRQ"
                    },
                    "match_reason": "Country and gender match"
                },
                {
                    "row_index": 5,
                    "data": {
                        "Entity_logical_id": "20",
                        "Subject_type": "P",
                        "Naal_wholename": "Qusay Saddam Hussein Al-Tikriti",
                        "Naal_gender": "M",
                        "Citi_country": "IRQ"
                    },
                    "match_reason": "Country and gender match"
                }
            ],
            "total_matches": 2,
            "match_criteria": {"country": "IRQ", "gender": "M"},
            "created_at": datetime.now().isoformat(),
            "user_id": "e2e_user_id"
        }
        
        # Make the request
        run_data = {
            "file_id": "e2e_file_id"
        }
        response = test_client.post(
            f"/api/watchlists/e2e_watchlist_id/run",
            json=run_data,
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    match_data = response.json()
    assert match_data["watchlist_id"] == "e2e_watchlist_id"
    assert match_data["file_id"] == "e2e_file_id"
    assert match_data["total_matches"] == 2
    
    # Step 7: Get match details
    with patch('app.services.matching_service.MatchingService.get_match_by_id', 
              new_callable=AsyncMock) as mock_get_match:
        # Set up mock return value - same as above
        mock_get_match.return_value = match_data
        
        # Make the request
        response = test_client.get(
            f"/api/matches/e2e_match_id",
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    match_details = response.json()
    assert match_details["_id"] == "e2e_match_id"
    assert len(match_details["matches"]) == 2
    assert "Saddam Hussein Al-Tikriti" in match_details["matches"][0]["data"]["Naal_wholename"]
    
    # Step 8: Use refresh token to get a new access token
    refresh_data = {
        "refresh_token": auth_data["refresh_token"]
    }
    
    # Mock the refresh token verification
    with patch('app.services.auth_service.AuthService.refresh_token', 
              new_callable=AsyncMock) as mock_refresh:
        # Set up mock return value
        mock_refresh.return_value = {
            "access_token": "e2e_new_access_token",
            "token_type": "bearer"
        }
        
        # Make the request
        response = test_client.post(
            "/api/auth/refresh",
            json=refresh_data
        )
    
    # Check response
    assert response.status_code == 200
    refresh_result = response.json()
    assert "access_token" in refresh_result
    assert refresh_result["access_token"] == "e2e_new_access_token"
    
    # Step 9: Logout
    with patch('app.services.auth_service.AuthService.logout', 
              new_callable=AsyncMock) as mock_logout:
        # Set up mock return value
        mock_logout.return_value = True
        
        # Make the request
        response = test_client.post(
            "/api/auth/logout",
            json={"refresh_token": auth_data["refresh_token"]},
            headers=auth_headers
        )
    
    # Check response
    assert response.status_code == 200
    logout_result = response.json()
    assert logout_result["success"] is True

@pytest.mark.asyncio
async def test_refresh_token_flow(test_client, mock_db):
    """Test the refresh token flow."""
    # Step 1: Login
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    
    # Mock authentication
    with patch('app.services.auth_service.AuthService.authenticate', 
              new_callable=AsyncMock) as mock_auth:
        # Set up mock return value
        mock_auth.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer"
        }
        
        # Make the request
        response = test_client.post("/api/auth/login", json=login_data)
    
    # Check response
    assert response.status_code == 200
    auth_data = response.json()
    assert "access_token" in auth_data
    assert "refresh_token" in auth_data
    
    # Step 2: Use refresh token to get a new access token
    refresh_data = {
        "refresh_token": auth_data["refresh_token"]
    }
    
    # Mock the refresh token verification
    with patch('app.services.auth_service.AuthService.refresh_token', 
              new_callable=AsyncMock) as mock_refresh:
        # Set up mock return value
        mock_refresh.return_value = {
            "access_token": "new_access_token",
            "token_type": "bearer"
        }
        
        # Make the request
        response = test_client.post(
            "/api/auth/refresh",
            json=refresh_data
        )
    
    # Check response
    assert response.status_code == 200
    refresh_result = response.json()
    assert "access_token" in refresh_result
    assert refresh_result["access_token"] == "new_access_token"
    
    # Step 3: Try to use an expired or invalid refresh token
    invalid_refresh_data = {
        "refresh_token": "invalid_refresh_token"
    }
    
    # Mock the refresh token verification to raise an exception
    with patch('app.services.auth_service.AuthService.refresh_token', 
              new_callable=AsyncMock) as mock_refresh:
        # Set up mock to raise an exception
        mock_refresh.side_effect = Exception("Invalid refresh token")
        
        # Make the request
        response = test_client.post(
            "/api/auth/refresh",
            json=invalid_refresh_data
        )
    
    # Check response - should be unauthorized
    assert response.status_code == 401
    
    # Step 4: Logout with valid refresh token
    with patch('app.services.auth_service.AuthService.logout', 
              new_callable=AsyncMock) as mock_logout:
        # Set up mock return value
        mock_logout.return_value = True
        
        # Make the request
        response = test_client.post(
            "/api/auth/logout",
            json={"refresh_token": auth_data["refresh_token"]},
            headers={"Authorization": f"Bearer {auth_data['access_token']}"}
        )
    
    # Check response
    assert response.status_code == 200
    logout_result = response.json()
    assert logout_result["success"] is True
    
    # Step 5: Try to use the refresh token after logout
    with patch('app.services.auth_service.AuthService.refresh_token', 
              new_callable=AsyncMock) as mock_refresh:
        # Set up mock to raise an exception
        mock_refresh.side_effect = Exception("Refresh token has been revoked")
        
        # Make the request
        response = test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": auth_data["refresh_token"]}
        )
    
    # Check response - should be unauthorized
    assert response.status_code == 401
