import os
import pytest
from unittest.mock import patch, AsyncMock

from app.workers.background_worker import process_csv_task as process_file_task, start_worker, load_pending_tasks

@pytest.mark.asyncio
async def test_process_file_task(mock_db):
    """Test the background task for processing a file."""
    # Mock data
    file_id = "test_file_id"
    user_id = "test_user_id"
    
    # Create test file paths
    test_file_path = os.path.join(os.path.dirname(__file__), '../../data/sample_from_gg_sheet_snippet - Sheet1.csv')
    test_output_dir = os.path.join(os.path.dirname(__file__), '../../../temp')
    os.makedirs(test_output_dir, exist_ok=True)
    test_output_path = os.path.join(test_output_dir, 'test_output.json')
    
    # Mock file and task services
    with patch('app.routers.file.file_service.FileService.get_file_by_id', 
              new_callable=AsyncMock) as mock_get_file:
        # Set up mock file
        mock_get_file.return_value = {
            "_id": file_id,
            "filename": "test_file.csv",
            "original_filename": "sample_from_gg_sheet_snippet - Sheet1.csv",
            "file_path": test_file_path,
            "file_type": "csv",
            "status": "pending",
            "created_at": "2025-06-01T10:00:00Z",
            "user_id": user_id
        }
        
        # Mock file update
        with patch('app.routers.file.file_service.FileService.update_file_status', 
                  new_callable=AsyncMock) as mock_update_file:
            mock_update_file.return_value = {
                "_id": file_id,
                "status": "completed",
                "processed_path": test_output_path
            }
            
            # Mock task update
            with patch('app.routers.task.task_service.TaskService.update_task_status', 
                      new_callable=AsyncMock) as mock_update_task:
                mock_update_task.return_value = {
                    "_id": "test_task_id",
                    "status": "completed",
                    "result": {"processed_file": test_output_path}
                }
                
                # Mock CSV processing
                with patch('app.utils.csv_processor.process_csv_to_json', 
                          new_callable=AsyncMock) as mock_process_csv:
                    mock_process_csv.return_value = True
                    
                    # Run the task
                    result = await process_file_task(file_id, "test_task_id")
                    
                    # Check that the task was completed successfully
                    assert result is True
                    assert mock_get_file.called
                    assert mock_update_file.called
                    assert mock_update_task.called
                    assert mock_process_csv.called

@pytest.mark.asyncio
async def test_process_file_task_error_handling(mock_db):
    """Test error handling in the file processing task."""
    # Mock data
    file_id = "test_file_id"
    
    # Mock file service to raise an exception
    with patch('app.routers.file.file_service.FileService.get_file_by_id', 
              new_callable=AsyncMock) as mock_get_file:
        mock_get_file.side_effect = Exception("Test error")
        
        # Mock task update
        with patch('app.routers.task.task_service.TaskService.update_task_status', 
                  new_callable=AsyncMock) as mock_update_task:
            mock_update_task.return_value = {
                "_id": "test_task_id",
                "status": "failed",
                "result": {"error": "Test error"}
            }
            
            # Run the task - it should handle the exception
            result = await process_file_task(file_id, "test_task_id")
            
            # Check that the task was marked as failed
            assert result is False
            assert mock_get_file.called
            assert mock_update_task.called
            assert mock_update_task.call_args[0][1] == "failed"

@pytest.mark.asyncio
async def test_start_worker(mock_db):
    """Test starting the background worker."""
    # Mock the asyncio.create_task
    with patch('asyncio.create_task') as mock_create_task:
        # Run the function
        await start_worker()
        
        # Check that the worker was started
        assert mock_create_task.called

@pytest.mark.asyncio
async def test_load_pending_tasks(mock_db):
    """Test loading pending tasks on startup."""
    # Mock the task service
    with patch('app.routers.task.task_service.TaskService.get_pending_tasks', 
              new_callable=AsyncMock) as mock_get_tasks:
        # Set up mock tasks
        mock_get_tasks.return_value = [
            {
                "_id": "task_id_1",
                "task_type": "csv_conversion",
                "status": "pending",
                "file_id": "file_id_1"
            },
            {
                "_id": "task_id_2",
                "task_type": "csv_conversion",
                "status": "pending",
                "file_id": "file_id_2"
            }
        ]
        
        # Mock process_file_task
        with patch('app.workers.background_worker.process_file_task', 
                  new_callable=AsyncMock) as mock_process:
            mock_process.return_value = True
            
            # Run the function
            await load_pending_tasks()
            
            # Check that pending tasks were loaded and processed
            assert mock_get_tasks.called
            assert mock_process.call_count == 2
