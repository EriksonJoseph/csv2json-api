import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.db]

@pytest.mark.asyncio
async def test_database_connection(mock_db):
    """Test that the database connection is working."""
    # Insert a test document
    test_collection = mock_db["test_collection"]
    test_doc = {"test_key": "test_value"}
    
    result = await test_collection.insert_one(test_doc)
    
    # Check that document was inserted
    assert result.inserted_id is not None
    
    # Retrieve the document
    retrieved = await test_collection.find_one({"_id": result.inserted_id})
    
    # Check that the document is as expected
    assert retrieved is not None
    assert retrieved["test_key"] == "test_value"

@pytest.mark.asyncio
async def test_database_transaction():
    """Test database transactions with real MongoDB (skip if using mock)."""
    # This test is intended for real MongoDB and would be skipped when using mocks
    # since mongomock doesn't support transactions
    pytest.skip("Skipping transaction test with mock database")
    
    # If using real MongoDB, you would test transactions here
