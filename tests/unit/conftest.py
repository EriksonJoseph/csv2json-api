import os
import asyncio
import sys
from typing import AsyncGenerator, Generator, Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config import get_settings

# Initialize settings
settings = get_settings()

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    # Set default test values
    test_config = {
        "MONGODB_URL": "mongomock://localhost",
        "MONGODB_DB": "test_db",
        "JWT_SECRET_KEY": "test-secret-key-1234567890",
        "JWT_REFRESH_SECRET_KEY": "test-refresh-secret-key-1234567890",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "JWT_REFRESH_TOKEN_EXPIRE_MINUTES": "1440",
        "SECURITY_PASSWORD_SALT_ROUNDS": "10"
    }
    
    with patch.dict(os.environ, test_config):
        yield

@pytest_asyncio.fixture
async def mock_mongodb_client() -> AsyncGenerator[AsyncMongoMockClient, None]:
    """Create a mock MongoDB client using mongomock_motor."""
    # Create a mongomock_motor client
    mock_client = AsyncMongoMockClient()
    
    # Patch the database functions
    with patch('app.database.get_client', return_value=mock_client), \
         patch('app.database.get_database') as mock_get_db, \
         patch('app.database.get_collection') as mock_get_collection:
        
        # Configure mocks
        mock_db = mock_client[settings.MONGODB_DB]
        mock_get_db.return_value = mock_db
        
        # Mock get_collection
        async def mock_get_coll(collection_name: str):
            return mock_db[collection_name]
        
        mock_get_collection.side_effect = mock_get_coll
        
        yield mock_client

@pytest_asyncio.fixture
async def mock_db(mock_mongodb_client: AsyncMongoMockClient) -> AsyncMongoMockClient:
    """Get the mock database instance."""
    return mock_mongodb_client[settings.MONGODB_DB]

# Define event loop for pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
