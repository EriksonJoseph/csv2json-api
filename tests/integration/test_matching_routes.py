import os
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from app.main import app

# Create a simple class to represent match results for testing
class MatchResult:
    """Simple representation of match results for testing purposes"""
    pass

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
async def test_get_matches(test_client, auth_headers, mock_db):
    """Test getting all matches for a user."""
    # Mock user data
    user_id = "test_user_id"
    
    # Mock the MatchingService.get_matches method
    with patch('app.services.matching_service.MatchingService.get_matches', 
              new_callable=AsyncMock) as mock_get_matches:
        # Set up mock return value
        mock_get_matches.return_value = [
            {
                "_id": "match_id_1",
                "watchlist_id": "watchlist_id_1",
                "watchlist_name": "Watchlist 1",
                "file_id": "file_id_1",
                "file_name": "test_file.csv",
                "total_matches": 3,
                "match_criteria": {"country": "IRQ", "gender": "M"},
                "created_at": datetime.now().isoformat(),
                "user_id": user_id
            },
            {
                "_id": "match_id_2",
                "watchlist_id": "watchlist_id_2",
                "watchlist_name": "Watchlist 2",
                "file_id": "file_id_2",
                "file_name": "test_file2.csv",
                "total_matches": 1,
                "match_criteria": {"country": "FRA"},
                "created_at": datetime.now().isoformat(),
                "user_id": user_id
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
                "/api/matches",
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["watchlist_id"] == "watchlist_id_1"
    assert data[0]["total_matches"] == 3
    assert data[1]["watchlist_id"] == "watchlist_id_2"
    assert data[1]["total_matches"] == 1

@pytest.mark.asyncio
async def test_get_match_by_id(test_client, auth_headers, mock_db):
    """Test getting a specific match by ID."""
    # Mock user data
    user_id = "test_user_id"
    match_id = "match_id_1"
    
    # Mock the MatchingService.get_match_by_id method
    with patch('app.services.matching_service.MatchingService.get_match_by_id', 
              new_callable=AsyncMock) as mock_get_match:
        # Set up mock return value
        mock_get_match.return_value = {
            "_id": match_id,
            "watchlist_id": "watchlist_id_1",
            "watchlist_name": "Test Watchlist",
            "file_id": "file_id_1",
            "file_name": "test_file.csv",
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
                },
                {
                    "row_index": 10,
                    "data": {
                        "Entity_logical_id": "23",
                        "Subject_type": "P",
                        "Naal_wholename": "Uday Saddam Hussein Al-Tikriti",
                        "Naal_gender": "M",
                        "Citi_country": "IRQ"
                    },
                    "match_reason": "Country and gender match"
                }
            ],
            "total_matches": 3,
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
            response = test_client.get(
                f"/api/matches/{match_id}",
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == match_id
    assert data["watchlist_id"] == "watchlist_id_1"
    assert data["total_matches"] == 3
    assert len(data["matches"]) == 3
    assert "Saddam Hussein Al-Tikriti" in data["matches"][0]["data"]["Naal_wholename"]
    assert "Qusay Saddam Hussein Al-Tikriti" in data["matches"][1]["data"]["Naal_wholename"]
    assert "Uday Saddam Hussein Al-Tikriti" in data["matches"][2]["data"]["Naal_wholename"]

@pytest.mark.asyncio
async def test_delete_match(test_client, auth_headers, mock_db):
    """Test deleting a match."""
    # Mock user data
    user_id = "test_user_id"
    match_id = "match_id_1"
    
    # Mock the MatchingService.delete_match method
    with patch('app.services.matching_service.MatchingService.delete_match', 
              new_callable=AsyncMock) as mock_delete_match:
        # Set up mock return value
        mock_delete_match.return_value = True
        
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
                f"/api/matches/{match_id}",
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "deleted successfully" in data["message"].lower()

@pytest.mark.asyncio
async def test_export_match_to_csv(test_client, auth_headers, mock_db):
    """Test exporting match results to CSV."""
    # Mock user data
    user_id = "test_user_id"
    match_id = "match_id_1"
    
    # Create mock match data
    match_data = {
        "_id": match_id,
        "watchlist_id": "watchlist_id_1",
        "watchlist_name": "Test Watchlist",
        "file_id": "file_id_1",
        "file_name": "test_file.csv",
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
    
    # Mock CSV export
    csv_content = "Entity_logical_id,Subject_type,Naal_wholename,Naal_gender,Citi_country,match_reason\n" + \
                 "13,P,Saddam Hussein Al-Tikriti,M,IRQ,Country and gender match\n" + \
                 "20,P,Qusay Saddam Hussein Al-Tikriti,M,IRQ,Country and gender match\n"
    
    # Mock the MatchingService.get_match_by_id method
    with patch('app.services.matching_service.MatchingService.get_match_by_id', 
              new_callable=AsyncMock) as mock_get_match:
        mock_get_match.return_value = match_data
        
        # Mock the export_matches_to_csv method
        with patch('app.services.matching_service.MatchingService.export_matches_to_csv', 
                  new_callable=AsyncMock) as mock_export:
            mock_export.return_value = csv_content
            
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
                    f"/api/matches/{match_id}/export",
                    headers=auth_headers
                )
        
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert "attachment" in response.headers["content-disposition"]
    assert "Saddam Hussein Al-Tikriti" in response.content.decode()
    assert "Qusay Saddam Hussein Al-Tikriti" in response.content.decode()

@pytest.mark.asyncio
async def test_bulk_match(test_client, auth_headers, mock_db):
    """Test bulk matching of a file against all watchlists."""
    # Mock user data
    user_id = "test_user_id"
    file_id = "file_id_1"
    
    # Mock the MatchingService.bulk_match method
    with patch('app.services.matching_service.MatchingService.bulk_match', 
              new_callable=AsyncMock) as mock_bulk_match:
        # Set up mock return value
        mock_bulk_match.return_value = {
            "total_matches": 2,
            "matches": [
                {
                    "watchlist_id": "watchlist_id_1",
                    "watchlist_name": "Watchlist 1",
                    "match_id": "match_id_1",
                    "match_count": 3,
                    "criteria": {"country": "IRQ", "gender": "M"}
                },
                {
                    "watchlist_id": "watchlist_id_2",
                    "watchlist_name": "Watchlist 2",
                    "match_id": "match_id_2",
                    "match_count": 1,
                    "criteria": {"country": "FRA"}
                }
            ],
            "file_id": file_id,
            "file_name": "test_file.csv"
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
            request_data = {
                "file_id": file_id
            }
            response = test_client.post(
                "/api/matches/bulk",
                json=request_data,
                headers=auth_headers
            )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == file_id
    assert data["total_matches"] == 2
    assert len(data["matches"]) == 2
    assert data["matches"][0]["watchlist_id"] == "watchlist_id_1"
    assert data["matches"][0]["match_count"] == 3
    assert data["matches"][1]["watchlist_id"] == "watchlist_id_2"
    assert data["matches"][1]["match_count"] == 1
