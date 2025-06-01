import asyncio
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from app.routers.task.task_repository import TaskRepository
from app.routers.file.file_repository import FileRepository
from app.database import get_collection
from app.dependencies.file import read_csv_file
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("background_worker")

# Global task queue
task_queue = asyncio.Queue()
is_worker_running = False

# Global variable to track current task
_current_task = None

async def get_current_processing_task() -> Optional[dict]:
    """
    Get current processing task information
    
    Returns:
        dict: Current task information if processing, None otherwise
    """
    if _current_task is None:
        return None
    
    # Return just the task ID since we don't need the full task details
    return {
        "task_id": _current_task,
        "status": "processing"
    }

async def process_csv_task(task_id: str, file_id: str):
    """
    Process a CSV file and insert data into MongoDB
    
    Args:
        task_id: ID of the task
        file_id: ID of the file to process
    """
    global _current_task
    _current_task = task_id
    start_time = datetime.now()
    logger.info(f"Processing task {task_id} with file {file_id}")
    
    task_repo = TaskRepository()
    file_repo = FileRepository()
    
    try:
        # Get file data
        file_data = await file_repo.get_file_by_id(file_id)
        if not file_data:
            raise Exception(f"File not found: {file_id}")
        
        file_path = file_data["file_path"]
        if not os.path.exists(file_path):
            raise Exception(f"File not found on disk: {file_path}")
        
        # Read CSV file
        df = read_csv_file(file_path)
        
        # Get collection
        csv_collection = await get_collection("csv")

        # Extract column names
        column_names = df.columns.tolist()

        # Convert DataFrame to list of dictionaries for MongoDB insertion
        records = df.to_dict("records")
        
        # Add metadata to each record
        for record in records:
            record["task_id"] = task_id
            record["processed_at"] = datetime.now()
        
        # Insert records in batches to avoid overwhelming MongoDB
        if records:
            BATCH_SIZE = 1000  # ปรับขนาด batch ตามที่ต้องการ
            total_records = len(records)
            for i in range(0, total_records, BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                await csv_collection.insert_many(batch)
                logger.info(f"Inserted batch {i//BATCH_SIZE + 1}/{(total_records + BATCH_SIZE - 1)//BATCH_SIZE}")
                # อาจเพิ่ม delay ระหว่าง batches ถ้าต้องการให้ช้าลง
                # await asyncio.sleep(0.1)
        
        # Calculate processing time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Update task with column names, processing time, and mark as completed
        await task_repo.update_task_status(
            task_id=task_id,
            is_done_created_doc=True,
            column_names=column_names,
            error_message=None,
            processing_time=execution_time
        )
        
        # Delete file from disk
        os.remove(file_path)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"Successfully processed task {task_id} with {len(records)} records in {execution_time:.2f} seconds")
        
    except Exception as e:
        error_message = str(e)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.error(f"Error processing task {task_id} in {execution_time:.2f} seconds: {error_message}")
        
        # Calculate processing time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Update task with error and processing time
        await task_repo.update_task_status(
            task_id=task_id,
            is_done_created_doc=True,
            column_names=[],
            error_message=error_message,
            processing_time=execution_time
        )
        
        # Attempt to clean up file (best effort)
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as clean_error:
            logger.error(f"Error cleaning up file: {clean_error}")

async def worker_loop():
    """
    Main worker loop that processes tasks from the queue
    """
    global is_worker_running
    is_worker_running = True
    
    logger.info("Starting background worker loop")
    
    try:
        while True:
            # Get task from queue
            task_data = await task_queue.get()
            task_id = task_data["task_id"]
            file_id = task_data["file_id"]
            
            try:
                await process_csv_task(task_id, file_id)
            except Exception as e:
                logger.error(f"Uncaught error in worker: {str(e)}")
            finally:
                # Clear current task
                _current_task = None
                # Mark task as done in the queue
                task_queue.task_done()
    except asyncio.CancelledError:
        logger.info("Worker loop cancelled")
    except Exception as e:
        logger.error(f"Worker loop error: {str(e)}")
    finally:
        is_worker_running = False

async def add_task_to_queue(task_id: str, file_id: str):
    """
    Add a task to the processing queue
    
    Args:
        task_id: ID of the task
        file_id: ID of the file to process
    """
    await task_queue.put({"task_id": task_id, "file_id": file_id})
    logger.info(f"Added task {task_id} to the queue")

async def start_worker():
    """
    Start the background worker if it's not already running
    """
    global is_worker_running
    
    if not is_worker_running:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Start worker as a background task
        asyncio.create_task(worker_loop())
        logger.info("Background worker started")

async def load_pending_tasks():
    """
    Load pending tasks from the database and add them to the queue
    """
    logger.info("Loading pending tasks")
    
    task_repo = TaskRepository()
    
    try:
        # Get tasks that aren't completed
        pending_tasks = await task_repo.get_pending_tasks()
        
        if pending_tasks:
            logger.info(f"Found {len(pending_tasks)} pending tasks")
            
            # Add tasks to queue
            for task in pending_tasks:
                await add_task_to_queue(task["_id"], task["file_id"])
        else:
            logger.info("No pending tasks found")
            
    except Exception as e:
        logger.error(f"Error loading pending tasks: {str(e)}")
