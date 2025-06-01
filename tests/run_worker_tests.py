import os
import sys
import unittest
import tempfile
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import worker functions to test
from app.workers.background_worker import (
    process_csv_task, 
    add_task_to_queue,
    start_worker,
    worker_loop,
    get_current_processing_task
)

class TestBackgroundWorker(unittest.TestCase):
    def setUp(self):
        # Set up environment variables for testing
        os.environ["MONGODB_URL"] = "mongomock://localhost"
        os.environ["MONGODB_DB"] = "test_db"
        # Create temp folder for files
        os.makedirs("temp", exist_ok=True)
        # Create temp folder for logs
        os.makedirs("logs", exist_ok=True)
        
        # Set up sample CSV content
        self.csv_content = """Entity_logical_id,Subject_type,Naal_wholename,Naal_gender,Citi_country
13,P,John Smith,M,USA
20,P,Jane Doe,F,GBR
23,P,Ahmed Ali,M,EGY"""
        
        # Create a temp file with the CSV content
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        with open(self.temp_file.name, 'w') as f:
            f.write(self.csv_content)
        
        # Store original event loop policy
        self.original_policy = asyncio.get_event_loop_policy()
    
    def tearDown(self):
        # Remove temp file
        if hasattr(self, 'temp_file'):
            os.unlink(self.temp_file.name)
        
        # Reset event loop policy
        asyncio.set_event_loop_policy(self.original_policy)
    
    def test_get_current_processing_task(self):
        """Test getting current processing task."""
        # Run the test with a custom event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the test
            result = loop.run_until_complete(get_current_processing_task())
            
            # Verify the result
            self.assertIsNone(result)  # Should be None when no task is processing
        finally:
            loop.close()
    
    def test_add_task_to_queue(self):
        """Test adding a task to the queue."""
        # Run the test with a custom event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the test
            loop.run_until_complete(add_task_to_queue("test_task_id", "test_file_id"))
            
            # Success if no exception was raised
            self.assertTrue(True)
        finally:
            loop.close()
    
    @patch('app.workers.background_worker.TaskRepository')
    @patch('app.workers.background_worker.FileRepository')
    @patch('app.workers.background_worker.get_collection')
    @patch('app.workers.background_worker.read_csv_file')
    def test_process_csv_task(self, mock_read_csv, mock_get_collection, mock_file_repo, mock_task_repo):
        """Test processing a CSV task."""
        # Run the test with a custom event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Configure mocks
            # Mock FileRepository
            file_repo_instance = mock_file_repo.return_value
            file_repo_instance.get_file_by_id = AsyncMock(return_value={
                "file_path": self.temp_file.name
            })
            
            # Mock TaskRepository
            task_repo_instance = mock_task_repo.return_value
            task_repo_instance.update_task_status = AsyncMock()
            
            # Mock read_csv_file
            import pandas as pd
            mock_df = pd.DataFrame({
                'Entity_logical_id': [13, 20, 23],
                'Subject_type': ['P', 'P', 'P'],
                'Naal_wholename': ['John Smith', 'Jane Doe', 'Ahmed Ali'],
                'Naal_gender': ['M', 'F', 'M'],
                'Citi_country': ['USA', 'GBR', 'EGY']
            })
            mock_read_csv.return_value = mock_df
            
            # Mock MongoDB collection
            mock_collection = AsyncMock()
            mock_collection.insert_many = AsyncMock()
            mock_get_collection.return_value = mock_collection
            
            # Run the test
            loop.run_until_complete(process_csv_task("test_task_id", "test_file_id"))
            
            # Verify that the required methods were called
            file_repo_instance.get_file_by_id.assert_called_once_with("test_file_id")
            mock_read_csv.assert_called_once_with(self.temp_file.name)
            mock_get_collection.assert_called_once_with("csv")
            mock_collection.insert_many.assert_called_once()
            task_repo_instance.update_task_status.assert_called_once()
            
            # Check that the data format is correct
            insert_call_args = mock_collection.insert_many.call_args[0][0]
            self.assertEqual(len(insert_call_args), 3)
            self.assertTrue('task_id' in insert_call_args[0])
            self.assertTrue('processed_at' in insert_call_args[0])
            self.assertTrue('Entity_logical_id' in insert_call_args[0])
            self.assertTrue('Naal_wholename' in insert_call_args[0])
            
        finally:
            loop.close()
    
    @patch('app.workers.background_worker.TaskRepository')
    @patch('app.workers.background_worker.FileRepository')
    def test_process_csv_task_file_not_found(self, mock_file_repo, mock_task_repo):
        """Test processing a CSV task with file not found."""
        # Run the test with a custom event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Configure mocks
            # Mock FileRepository
            file_repo_instance = mock_file_repo.return_value
            file_repo_instance.get_file_by_id = AsyncMock(return_value=None)
            
            # Mock TaskRepository
            task_repo_instance = mock_task_repo.return_value
            task_repo_instance.update_task_status = AsyncMock()
            
            # Run the test
            loop.run_until_complete(process_csv_task("test_task_id", "nonexistent_file_id"))
            
            # Verify that error handling worked
            task_repo_instance.update_task_status.assert_called_once()
            
            # Check error message contains "not found"
            update_call_kwargs = task_repo_instance.update_task_status.call_args[1]
            self.assertTrue('error_message' in update_call_kwargs)
            self.assertIsNotNone(update_call_kwargs['error_message'])
            self.assertTrue('not found' in update_call_kwargs['error_message'].lower())
            
        finally:
            loop.close()
    
    @patch('asyncio.create_task')
    def test_start_worker(self, mock_create_task):
        """Test starting the worker."""
        # Run the test with a custom event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the test
            loop.run_until_complete(start_worker())
            
            # Verify that worker loop was started
            mock_create_task.assert_called_once()
            # The first argument to create_task should be the return value of worker_loop()
            self.assertEqual(mock_create_task.call_args[0][0].cr_awaitable.__name__, worker_loop.__name__)
            
        finally:
            loop.close()


if __name__ == '__main__':
    unittest.main()
