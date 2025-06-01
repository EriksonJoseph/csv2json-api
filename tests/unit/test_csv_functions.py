import os
import pandas as pd
import pytest
import tempfile
import csv
from unittest.mock import patch, AsyncMock

from app.dependencies.file import read_csv_file, read_and_save_csv_to_mongodb

# Sample CSV data for testing
SAMPLE_CSV_DATA = """Entity_logical_id,Subject_type,Naal_wholename,Naal_gender,Citi_country
13,P,John Smith,M,USA
20,P,Jane Doe,F,GBR
23,P,Ahmed Ali,M,EGY"""

SAMPLE_CSV_WITH_SEMICOLON = """Entity_logical_id;Subject_type;Naal_wholename;Naal_gender;Citi_country
13;P;John Smith;M;USA
20;P;Jane Doe;F;GBR
23;P;Ahmed Ali;M;EGY"""

@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd, 'w') as f:
        f.write(SAMPLE_CSV_DATA)
    yield path
    os.unlink(path)

@pytest.fixture
def temp_csv_file_semicolon():
    """Create a temporary CSV file with semicolon delimiter for testing."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd, 'w') as f:
        f.write(SAMPLE_CSV_WITH_SEMICOLON)
    yield path
    os.unlink(path)

def test_read_csv_file_comma(temp_csv_file):
    """Test reading a CSV file with comma delimiter."""
    # Call the function
    df = read_csv_file(temp_csv_file)
    
    # Verify the result
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert len(df.columns) == 5
    assert list(df.columns) == ['Entity_logical_id', 'Subject_type', 'Naal_wholename', 'Naal_gender', 'Citi_country']
    assert df['Naal_wholename'].tolist() == ['John Smith', 'Jane Doe', 'Ahmed Ali']
    assert df['Citi_country'].tolist() == ['USA', 'GBR', 'EGY']

def test_read_csv_file_semicolon(temp_csv_file_semicolon):
    """Test reading a CSV file with semicolon delimiter."""
    # Call the function
    df = read_csv_file(temp_csv_file_semicolon)
    
    # Verify the result - should detect semicolon delimiter
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert len(df.columns) == 5
    assert list(df.columns) == ['Entity_logical_id', 'Subject_type', 'Naal_wholename', 'Naal_gender', 'Citi_country']
    assert df['Naal_wholename'].tolist() == ['John Smith', 'Jane Doe', 'Ahmed Ali']
    assert df['Citi_country'].tolist() == ['USA', 'GBR', 'EGY']

def test_read_csv_file_nonexistent():
    """Test reading a nonexistent CSV file."""
    with pytest.raises(Exception):
        read_csv_file("nonexistent_file.csv")

@pytest.mark.asyncio
async def test_read_and_save_csv_to_mongodb(temp_csv_file):
    """Test reading a CSV file and saving to MongoDB."""
    # Mock MongoDB collection
    with patch('app.dependencies.file.get_collection', new_callable=AsyncMock) as mock_get_collection:
        # Mock collection operations
        mock_collection = AsyncMock()
        mock_collection.delete_many = AsyncMock(return_value=None)
        # Create a mock response with inserted_ids attribute
        mock_insert_result = AsyncMock()
        mock_insert_result.inserted_ids = [f"id_{i}" for i in range(3)]
        mock_collection.insert_many = AsyncMock(return_value=mock_insert_result)
        mock_get_collection.return_value = mock_collection
        
        # Call the function
        result = await read_and_save_csv_to_mongodb(file_path=temp_csv_file, batch_size=10)
        
        # Verify the result
        assert result['success'] is True
        assert 'total_rows' in result
        assert result['total_rows'] == 3
        
        # Verify that MongoDB operations were called
        mock_get_collection.assert_called_once()
        mock_collection.delete_many.assert_called_once()
        mock_collection.insert_many.assert_called_once()
        
        # Check the inserted data format
        insert_call_args = mock_collection.insert_many.call_args[0][0]
        assert len(insert_call_args) == 3
        assert all('Entity_logical_id' in record for record in insert_call_args)
        assert all('Naal_wholename' in record for record in insert_call_args)

@pytest.mark.asyncio
async def test_read_and_save_csv_to_mongodb_nonexistent_file():
    """Test reading a nonexistent CSV file for MongoDB."""
    # Call the function with nonexistent file
    result = await read_and_save_csv_to_mongodb(file_path="nonexistent_file.csv")
    
    # Verify the result
    assert result['success'] is False
    assert '❌' in result['message']
