import os
import sys
import unittest
import tempfile
import pandas as pd
import json
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the file.py module directly to avoid circular imports
from app.dependencies.file import read_csv_file

class TestCSVToJSON(unittest.TestCase):
    def setUp(self):
        # Set up environment variables for testing
        os.environ["MONGODB_URL"] = "mongomock://localhost"
        os.environ["MONGODB_DB"] = "test_db"
        
        # Set up sample CSV content
        self.csv_content = """Entity_logical_id,Subject_type,Naal_wholename,Naal_gender,Citi_country
13,P,John Smith,M,USA
20,P,Jane Doe,F,GBR
23,P,Ahmed Ali,M,EGY"""
        
        # Create a temp file with the CSV content
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        with open(self.temp_file.name, 'w') as f:
            f.write(self.csv_content)
    
    def tearDown(self):
        # Remove temp file
        if hasattr(self, 'temp_file'):
            os.unlink(self.temp_file.name)
    
    def test_csv_to_dataframe(self):
        """Test converting CSV to pandas DataFrame."""
        # Read the CSV file
        df = read_csv_file(self.temp_file.name)
        
        # Verify the DataFrame structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertEqual(len(df.columns), 5)
        self.assertEqual(list(df.columns), ['Entity_logical_id', 'Subject_type', 'Naal_wholename', 'Naal_gender', 'Citi_country'])
        
        # Verify the data content
        self.assertEqual(df['Naal_wholename'].tolist(), ['John Smith', 'Jane Doe', 'Ahmed Ali'])
        self.assertEqual(df['Citi_country'].tolist(), ['USA', 'GBR', 'EGY'])
    
    def test_dataframe_to_json(self):
        """Test converting DataFrame to JSON."""
        # Read the CSV file
        df = read_csv_file(self.temp_file.name)
        
        # Convert DataFrame to list of dictionaries (JSON)
        json_records = df.to_dict("records")
        
        # Verify the JSON structure
        self.assertIsInstance(json_records, list)
        self.assertEqual(len(json_records), 3)
        
        # Verify each record has the correct keys and values
        self.assertEqual(json_records[0]['Naal_wholename'], 'John Smith')
        self.assertEqual(json_records[0]['Citi_country'], 'USA')
        self.assertEqual(json_records[1]['Naal_wholename'], 'Jane Doe')
        self.assertEqual(json_records[1]['Citi_country'], 'GBR')
        self.assertEqual(json_records[2]['Naal_wholename'], 'Ahmed Ali')
        self.assertEqual(json_records[2]['Citi_country'], 'EGY')
    
    def test_json_serialization(self):
        """Test that the JSON can be properly serialized."""
        # Read the CSV file
        df = read_csv_file(self.temp_file.name)
        
        # Convert DataFrame to list of dictionaries (JSON)
        json_records = df.to_dict("records")
        
        # Attempt to serialize to JSON string
        try:
            json_string = json.dumps(json_records)
            # If we get here, the serialization was successful
            self.assertTrue(True)
            
            # Additional verification of JSON structure
            self.assertIsInstance(json_string, str)
            self.assertIn('John Smith', json_string)
            self.assertIn('Jane Doe', json_string)
            self.assertIn('Ahmed Ali', json_string)
            self.assertIn('USA', json_string)
            self.assertIn('GBR', json_string)
            self.assertIn('EGY', json_string)
        except Exception as e:
            self.fail(f"JSON serialization failed: {str(e)}")
    
    def test_csv_with_different_delimiters(self):
        """Test CSV conversion with different delimiters."""
        # Create a temp file with semicolon delimiter
        semicolon_content = self.csv_content.replace(',', ';')
        semicolon_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        with open(semicolon_file.name, 'w') as f:
            f.write(semicolon_content)
        
        try:
            # Read the CSV file with semicolon delimiter
            df = read_csv_file(semicolon_file.name)
            
            # Verify the DataFrame structure
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 3)
            self.assertEqual(len(df.columns), 5)
            self.assertEqual(list(df.columns), ['Entity_logical_id', 'Subject_type', 'Naal_wholename', 'Naal_gender', 'Citi_country'])
            
            # Verify the data content
            self.assertEqual(df['Naal_wholename'].tolist(), ['John Smith', 'Jane Doe', 'Ahmed Ali'])
            self.assertEqual(df['Citi_country'].tolist(), ['USA', 'GBR', 'EGY'])
        finally:
            # Remove the temporary file
            os.unlink(semicolon_file.name)
    
    def test_csv_with_special_characters(self):
        """Test CSV conversion with special characters."""
        # Create a temp file with special characters
        special_content = """Entity_logical_id,Subject_type,Naal_wholename,Naal_gender,Citi_country
13,P,"Smith, John",M,USA
20,P,"Doe, Jane",F,GBR
23,P,"Ali, Ahmed",M,EGY"""
        special_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        with open(special_file.name, 'w') as f:
            f.write(special_content)
        
        try:
            # Read the CSV file with special characters
            df = read_csv_file(special_file.name)
            
            # Verify the DataFrame structure
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 3)
            self.assertEqual(len(df.columns), 5)
            
            # Verify the data content with quoted commas
            self.assertEqual(df['Naal_wholename'].tolist(), ['Smith, John', 'Doe, Jane', 'Ali, Ahmed'])
        finally:
            # Remove the temporary file
            os.unlink(special_file.name)


if __name__ == '__main__':
    unittest.main()
