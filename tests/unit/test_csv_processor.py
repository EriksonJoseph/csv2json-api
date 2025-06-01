import os
import json
import pytest
from pathlib import Path

from app.utils.csv_processor import process_csv_to_json, validate_csv_headers

# Path to test file
TEST_FILE_PATH = os.path.join(os.path.dirname(__file__), '../../data/sample_from_gg_sheet_snippet - Sheet1.csv')

@pytest.mark.asyncio
async def test_csv_validation():
    """Test CSV header validation."""
    # Read the test file
    with open(TEST_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test valid headers validation
    valid_headers = ['Date_file', 'Entity_logical_id', 'Subject_type', 'Leba_numtitle']
    is_valid = validate_csv_headers(content, valid_headers)
    assert is_valid is True
    
    # Test invalid headers validation
    invalid_headers = ['Invalid_header', 'Another_invalid']
    is_valid = validate_csv_headers(content, invalid_headers)
    assert is_valid is False

@pytest.mark.asyncio
async def test_csv_to_json_conversion():
    """Test converting CSV to JSON."""
    # Define test input and output paths
    input_path = TEST_FILE_PATH
    output_path = os.path.join(os.path.dirname(__file__), '../../../temp/test_output.json')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Process the CSV file
    result = await process_csv_to_json(input_path, output_path)
    
    # Check that processing was successful
    assert result is True
    assert os.path.exists(output_path)
    
    # Verify JSON content
    with open(output_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Check that data was properly converted
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    
    # Check fields from first row
    first_row = json_data[0]
    assert 'Date_file' in first_row
    assert 'Entity_logical_id' in first_row
    assert 'Subject_type' in first_row
    assert 'Leba_numtitle' in first_row
    
    # Clean up test file
    if os.path.exists(output_path):
        os.remove(output_path)

@pytest.mark.asyncio
async def test_csv_to_json_error_handling():
    """Test error handling during CSV processing."""
    # Define test input and output paths
    input_path = "non_existent_file.csv"
    output_path = os.path.join(os.path.dirname(__file__), '../../../temp/test_output.json')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Process non-existent CSV file
    with pytest.raises(FileNotFoundError):
        result = await process_csv_to_json(input_path, output_path)
    
    # Test with corrupted CSV
    corrupted_csv_path = os.path.join(os.path.dirname(__file__), '../../../temp/corrupted.csv')
    with open(corrupted_csv_path, 'w') as f:
        f.write('Invalid,CSV\nFormat,"Missing quotes\nNewline in field')
    
    # Test processing corrupted file
    with pytest.raises(Exception):
        result = await process_csv_to_json(corrupted_csv_path, output_path)
    
    # Clean up test files
    if os.path.exists(corrupted_csv_path):
        os.remove(corrupted_csv_path)
    if os.path.exists(output_path):
        os.remove(output_path)

@pytest.mark.asyncio
async def test_csv_to_json_large_file_handling():
    """Test handling of large CSV files."""
    # Define test input and output paths
    input_path = TEST_FILE_PATH
    output_path = os.path.join(os.path.dirname(__file__), '../../../temp/test_large_output.json')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create a mock for the CSV file handling
    large_csv_path = os.path.join(os.path.dirname(__file__), '../../../temp/large.csv')
    
    # Generate a larger CSV file based on the test data
    with open(TEST_FILE_PATH, 'r', encoding='utf-8') as src:
        headers = src.readline().strip()
        sample_data = src.readline().strip()
    
    # Create a larger file by duplicating rows
    with open(large_csv_path, 'w', encoding='utf-8') as dest:
        dest.write(headers + '\n')
        for i in range(1000):  # Create 1000 rows
            dest.write(sample_data + '\n')
    
    # Process the large CSV file
    result = await process_csv_to_json(large_csv_path, output_path)
    
    # Check that processing was successful
    assert result is True
    assert os.path.exists(output_path)
    
    # Verify JSON content
    with open(output_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Check that all rows were processed
    assert isinstance(json_data, list)
    assert len(json_data) == 1000
    
    # Clean up test files
    if os.path.exists(large_csv_path):
        os.remove(large_csv_path)
    if os.path.exists(output_path):
        os.remove(output_path)
