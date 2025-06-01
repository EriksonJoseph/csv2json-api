import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

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

@pytest.mark.asyncio
async def test_create_watchlist(test_client, auth_headers, mock_db):
    """Test creating a new watchlist."""
    # Mock user data
    user_id = "test_user_id"
    
    # Mock the WatchlistService.create_watchlist method
    with patch('app.services.watchlist_service.WatchlistService.create_watchlist', 
              new_callable=AsyncMock) as mock_create_watchlist:
        # Set up mock return value
        mock_create_watchlist.return_value = {
            "_id": "watchlist_id_1",
            "name": "Test Watchlist",
            "description": "A test watchlist",
            "criteria": {
                "country": "IRQ",
                "gender": "M"
            },
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": user_id,
                "username": "testuser",
                "email": "test@example.com"
            }
            
            # Make the request
            watchlist_data = {
                "name": "Test Watchlist",
                "description": "A test watchlist",
                "criteria": {
                    "country": "IRQ",
                    "gender": "M"
                }
            }
            response = test_client.post(
                "/api/watchlists",
                json=watchlist_data,
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Watchlist"
    assert data["criteria"]["country"] == "IRQ"
    assert data["user_id"] == user_id

@pytest.mark.asyncio
async def test_get_watchlists(test_client, auth_headers, mock_db):
    """Test getting all watchlists for a user."""
    # Mock user data
    user_id = "test_user_id"
    
    # Mock the WatchlistService.get_watchlists method
    with patch('app.services.watchlist_service.WatchlistService.get_watchlists', 
              new_callable=AsyncMock) as mock_get_watchlists:
        # Set up mock return value
        mock_get_watchlists.return_value = [
            {
                "_id": "watchlist_id_1",
                "name": "Watchlist 1",
                "description": "First test watchlist",
                "criteria": {"country": "IRQ"},
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            },
            {
                "_id": "watchlist_id_2",
                "name": "Watchlist 2",
                "description": "Second test watchlist",
                "criteria": {"gender": "M"},
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": user_id,
                "username": "testuser",
                "email": "test@example.com"
            }
            
            # Make the request
            response = test_client.get(
                "/api/watchlists",
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Watchlist 1"
    assert data[1]["name"] == "Watchlist 2"

@pytest.mark.asyncio
async def test_get_watchlist_by_id(test_client, auth_headers, mock_db):
    """Test getting a specific watchlist by ID."""
    # Mock user data
    user_id = "test_user_id"
    watchlist_id = "watchlist_id_1"
    
    # Mock the WatchlistService.get_watchlist_by_id method
    with patch('app.services.watchlist_service.WatchlistService.get_watchlist_by_id', 
              new_callable=AsyncMock) as mock_get_watchlist:
        # Set up mock return value
        mock_get_watchlist.return_value = {
            "_id": watchlist_id,
            "name": "Test Watchlist",
            "description": "A test watchlist",
            "criteria": {"country": "IRQ", "gender": "M"},
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": user_id,
                "username": "testuser",
                "email": "test@example.com"
            }
            
            # Make the request
            response = test_client.get(
                f"/api/watchlists/{watchlist_id}",
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == watchlist_id
    assert data["name"] == "Test Watchlist"
    assert data["criteria"]["country"] == "IRQ"

@pytest.mark.asyncio
async def test_update_watchlist(test_client, auth_headers, mock_db):
    """Test updating a watchlist."""
    # Mock user data
    user_id = "test_user_id"
    watchlist_id = "watchlist_id_1"
    
    # Mock the WatchlistService.update_watchlist method
    with patch('app.services.watchlist_service.WatchlistService.update_watchlist', 
              new_callable=AsyncMock) as mock_update_watchlist:
        # Set up mock return value
        mock_update_watchlist.return_value = {
            "_id": watchlist_id,
            "name": "Updated Watchlist",
            "description": "Updated description",
            "criteria": {"country": "IRQ", "gender": "F"},
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": user_id,
                "username": "testuser",
                "email": "test@example.com"
            }
            
            # Make the request
            update_data = {
                "name": "Updated Watchlist",
                "description": "Updated description",
                "criteria": {"country": "IRQ", "gender": "F"}
            }
            response = test_client.put(
                f"/api/watchlists/{watchlist_id}",
                json=update_data,
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Watchlist"
    assert data["description"] == "Updated description"
    assert data["criteria"]["gender"] == "F"

@pytest.mark.asyncio
async def test_delete_watchlist(test_client, auth_headers, mock_db):
    """Test deleting a watchlist."""
    # Mock user data
    user_id = "test_user_id"
    watchlist_id = "watchlist_id_1"
    
    # Mock the WatchlistService.delete_watchlist method
    with patch('app.services.watchlist_service.WatchlistService.delete_watchlist', 
              new_callable=AsyncMock) as mock_delete_watchlist:
        # Set up mock return value
        mock_delete_watchlist.return_value = True
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": user_id,
                "username": "testuser",
                "email": "test@example.com"
            }
            
            # Make the request
            response = test_client.delete(
                f"/api/watchlists/{watchlist_id}",
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "deleted successfully" in data["message"].lower()

@pytest.mark.asyncio
async def test_run_watchlist(test_client, auth_headers, mock_db):
    """Test running a watchlist against a file."""
    # Mock user data
    user_id = "test_user_id"
    watchlist_id = "watchlist_id_1"
    file_id = "file_id_1"
    
    # Mock the WatchlistService.run_watchlist method
    with patch('app.services.watchlist_service.WatchlistService.run_watchlist', 
              new_callable=AsyncMock) as mock_run_watchlist:
        # Set up mock return value
        mock_run_watchlist.return_value = {
            "_id": "match_id_1",
            "watchlist_id": watchlist_id,
            "file_id": file_id,
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
            "user_id": user_id
        }
        
        # Mock the get_current_user dependency
        with patch('app.dependencies.auth.get_current_user', 
                  new_callable=AsyncMock) as mock_user:
            mock_user.return_value = {
                "_id": user_id,
                "username": "testuser",
                "email": "test@example.com"
            }
            
            # Make the request
            run_data = {
                "file_id": file_id
            }
            response = test_client.post(
                f"/api/watchlists/{watchlist_id}/run",
                json=run_data,
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["watchlist_id"] == watchlist_id
    assert data["file_id"] == file_id
    assert data["total_matches"] == 2
    assert len(data["matches"]) == 2
    assert data["matches"][0]["data"]["Naal_wholename"] == "Saddam Hussein Al-Tikriti"
