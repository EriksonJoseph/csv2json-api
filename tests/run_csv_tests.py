import os
import sys
import pandas as pd
import tempfile
import unittest
from unittest.mock import patch, AsyncMock
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the functions to test
from app.dependencies.file import read_csv_file

# Sample CSV data for testing
SAMPLE_CSV_DATA = """Entity_logical_id,Subject_type,Naal_wholename,Naal_gender,Citi_country
13,P,John Smith,M,USA
20,P,Jane Doe,F,GBR
23,P,Ahmed Ali,M,EGY"""

SAMPLE_CSV_WITH_SEMICOLON = """Entity_logical_id;Subject_type;Naal_wholename;Naal_gender;Citi_country
13;P;John Smith;M;USA
20;P;Jane Doe;F;GBR
23;P;Ahmed Ali;M;EGY"""

class TestCSVFunctions(unittest.TestCase):
    def setUp(self):
        # Create temporary CSV files
        self.comma_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        with open(self.comma_file.name, 'w') as f:
            f.write(SAMPLE_CSV_DATA)
            
        self.semicolon_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        with open(self.semicolon_file.name, 'w') as f:
            f.write(SAMPLE_CSV_WITH_SEMICOLON)
    
    def tearDown(self):
        # Remove temporary files
        os.unlink(self.comma_file.name)
        os.unlink(self.semicolon_file.name)
    
    def test_read_csv_file_comma(self):
        """Test reading a CSV file with comma delimiter."""
        # Call the function
        df = read_csv_file(self.comma_file.name)
        
        # Verify the result
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertEqual(len(df.columns), 5)
        self.assertEqual(list(df.columns), ['Entity_logical_id', 'Subject_type', 'Naal_wholename', 'Naal_gender', 'Citi_country'])
        self.assertEqual(df['Naal_wholename'].tolist(), ['John Smith', 'Jane Doe', 'Ahmed Ali'])
        self.assertEqual(df['Citi_country'].tolist(), ['USA', 'GBR', 'EGY'])
    
    def test_read_csv_file_semicolon(self):
        """Test reading a CSV file with semicolon delimiter."""
        # Call the function
        df = read_csv_file(self.semicolon_file.name)
        
        # Verify the result - should detect semicolon delimiter
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertEqual(len(df.columns), 5)
        self.assertEqual(list(df.columns), ['Entity_logical_id', 'Subject_type', 'Naal_wholename', 'Naal_gender', 'Citi_country'])
        self.assertEqual(df['Naal_wholename'].tolist(), ['John Smith', 'Jane Doe', 'Ahmed Ali'])
        self.assertEqual(df['Citi_country'].tolist(), ['USA', 'GBR', 'EGY'])
    
    def test_read_csv_file_nonexistent(self):
        """Test reading a nonexistent CSV file."""
        with self.assertRaises(Exception):
            read_csv_file("nonexistent_file.csv")

if __name__ == '__main__':
    # Mock environment variables
    os.environ["MONGODB_URL"] = "mongomock://localhost"
    os.environ["MONGODB_DB"] = "test_db"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-1234567890"
    os.environ["JWT_REFRESH_SECRET_KEY"] = "test-refresh-secret-key-1234567890"
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    os.environ["JWT_REFRESH_TOKEN_EXPIRE_MINUTES"] = "1440"
    
    # Run the tests
    unittest.main()
