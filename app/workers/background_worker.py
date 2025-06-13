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
logger: logging.Logger = logging.getLogger("background_worker")

# Global task queue
task_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
search_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
is_worker_running: bool = False
is_search_worker_running: bool = False

# Global variable to track current task
_current_task: Optional[str] = None
_current_search: Optional[str] = None

async def get_current_processing_task() -> Optional[Dict[str, Any]]:
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

async def get_current_processing_search() -> Optional[Dict[str, Any]]:
    """
    Get current processing search information
    
    Returns:
        dict: Current search information if processing, None otherwise
    """
    if _current_search is None:
        return None
    
    return {
        "search_id": _current_search,
        "status": "processing"
    }

async def process_csv_task(task_id: str, file_id: str) -> None:
    """
    Process a CSV file and insert data into MongoDB
    
    Args:
        task_id: ID of the task to process
        file_id: ID of the file to process
    """
    global _current_task
    _current_task = task_id
    start_time: datetime = datetime.now()
    logger.info(f"Processing task {task_id} with file {file_id}")
    
    task_repo: TaskRepository = TaskRepository()
    file_repo: FileRepository = FileRepository()
    file_path: Optional[str] = None  # Initialize file_path to avoid unbound variable
    
    try:
        # Get file data
        file_data = await file_repo.get_file_by_id(file_id)
        if not file_data:
            raise Exception(f"File not found: {file_id}")
        
        file_path = file_data["file_path"]
        if not file_path:
            raise Exception("No file path")
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
        now = datetime.now()
        for record in records:
            record["task_id"] = task_id
            record["processed_at"] = now
            record["created_by"] = "worker"
            record["created_at"] = now
            record["updated_by"] = "worker"
            record["updated_at"] = now
        
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
        
        # Update task with column names, processing time, total rows, and mark as completed
        await task_repo.update_task_status(
            task_id=task_id,
            is_done_created_doc=True,
            column_names=column_names,
            error_message=None,
            processing_time=execution_time,
            total_rows=len(records)
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
            processing_time=execution_time,
            total_rows=0
        )
        
        # Attempt to clean up file (best effort)
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as clean_error:
            logger.error(f"Error cleaning up file: {clean_error}")

async def process_search_task(search_id: str, search_type: str, search_params: Dict[str, Any]) -> None:
    """
    Process a search task and update results
    
    Args:
        search_id: ID of the search task
        search_type: Type of search (single or bulk)
        search_params: Search parameters
    """
    global _current_search
    _current_search = search_id
    start_time = datetime.now()
    logger.info(f"Processing search {search_id} of type {search_type}")
    
    from app.routers.matching.matching_repository import MatchingRepository
    from app.routers.matching.matching_service import MatchingService
    
    matching_repo = MatchingRepository()
    matching_service = MatchingService()
    
    try:
        # Update status to processing
        await matching_repo.update_search_status(search_id, "processing", "worker")
        
        # Get CSV data for the specified columns
        data = await matching_repo.search_in_columns(
            task_id=search_params["task_id"],
            columns=search_params["columns"]
        )
        
        if not data:
            raise Exception("No data found for the specified task")
        
        if search_type == "single":
            # Process single search
            _, matched_records = await matching_service._search_single_name_in_data(
                query_name=search_params["name"],
                columns=search_params["columns"],
                data=data,
                threshold=search_params["threshold"]
            )
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Prepare results
            results_found = len(matched_records)
            best_match_score = matched_records[0].confidence if matched_records else 0.0
            
            # Update search with results
            additional_data = {
                "results_found": results_found,
                "total_searched": 1,
                "execution_time_ms": execution_time_ms,
                "best_match_score": best_match_score,
                "matched_records": [matching_service.clean_json(record.dict()) for record in matched_records]
            }
            
        else:  # bulk search
            # Process bulk search
            results = []
            total_found = 0
            total_above_threshold = 0
            best_overall_match_score = 0.0
            all_matched_records = []
            
            # Process each name in the list
            for name in search_params["list"]:
                _, matched_records = await matching_service._search_single_name_in_data(
                    query_name=name,
                    columns=search_params["columns"],
                    data=data,
                    threshold=search_params["threshold"]
                )
                
                # Collect all matched records
                all_matched_records.extend(matched_records)
                
                best_match_score = matched_records[0].confidence if matched_records else 0.0
                found = len(matched_records) > 0
                
                # Track the highest score across all searches
                if best_match_score > best_overall_match_score:
                    best_overall_match_score = best_match_score
                
                if found:
                    total_found += 1
                if best_match_score >= search_params["threshold"]:
                    total_above_threshold += 1
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update search with results
            additional_data = {
                "results_found": total_found,
                "total_searched": len(search_params["list"]),
                "execution_time_ms": execution_time_ms,
                "best_match_score": best_overall_match_score,
                "total_above_threshold": total_above_threshold,
                "matched_records": [matching_service.clean_json(record.dict()) for record in all_matched_records]
            }
        
        # Update search status to completed
        await matching_repo.update_search_status(search_id, "completed", "worker", additional_data)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"Successfully processed search {search_id} in {execution_time:.2f} seconds")
        
    except Exception as e:
        error_message = str(e)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.error(f"Error processing search {search_id} in {execution_time:.2f} seconds: {error_message}")
        
        # Update search status to failed
        await matching_repo.update_search_status(
            search_id, 
            "failed", 
            "worker", 
            {"error_message": error_message, "execution_time_ms": execution_time * 1000}
        )
    finally:
        # Clear current search
        _current_search = None

async def worker_loop() -> None:
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

async def search_worker_loop() -> None:
    """
    Main search worker loop that processes search tasks from the queue
    """
    global is_search_worker_running
    is_search_worker_running = True
    
    logger.info("Starting search worker loop")
    
    try:
        while True:
            # Get search task from queue
            search_data = await search_queue.get()
            search_id = search_data["search_id"]
            search_type = search_data["search_type"]
            search_params = search_data["search_params"]
            
            try:
                await process_search_task(search_id, search_type, search_params)
            except Exception as e:
                logger.error(f"Uncaught error in search worker: {str(e)}")
            finally:
                # Clear current search
                _current_search = None
                # Mark search task as done in the queue
                search_queue.task_done()
    except asyncio.CancelledError:
        logger.info("Search worker loop cancelled")
    except Exception as e:
        logger.error(f"Search worker loop error: {str(e)}")
    finally:
        is_search_worker_running = False

async def add_task_to_queue(task_id: str, file_id: str) -> None:
    """
    Add a task to the processing queue
    
    Args:
        task_id: ID of the task
        file_id: ID of the file to process
    """
    await task_queue.put({"task_id": task_id, "file_id": file_id})
    logger.info(f"Added task {task_id} to the queue")

async def add_search_to_queue(search_id: str, search_type: str, search_params: Dict[str, Any]) -> None:
    """
    Add a search task to the processing queue
    
    Args:
        search_id: ID of the search
        search_type: Type of search (single or bulk)
        search_params: Search parameters
    """
    await search_queue.put({
        "search_id": search_id, 
        "search_type": search_type, 
        "search_params": search_params
    })
    logger.info(f"Added search {search_id} to the queue")

async def start_worker() -> None:
    """
    Start the background worker if it's not already running
    """
    global is_worker_running, is_search_worker_running
    
    if not is_worker_running:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Start worker as a background task
        asyncio.create_task(worker_loop())
        logger.info("Background worker started")
    
    if not is_search_worker_running:
        # Start search worker as a background task
        asyncio.create_task(search_worker_loop())
        logger.info("Search worker started")

async def load_pending_tasks() -> None:
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

async def load_pending_searches() -> None:
    """
    Load pending searches from the database and add them to the queue
    """
    logger.info("Loading pending searches")
    
    from app.routers.matching.matching_repository import MatchingRepository
    
    matching_repo = MatchingRepository()
    
    try:
        # Get searches that aren't completed
        pending_searches = await matching_repo.get_pending_searches()
        
        if pending_searches:
            logger.info(f"Found {len(pending_searches)} pending searches")
            
            # Add searches to queue
            for search in pending_searches:
                search_params = {
                    "task_id": search["task_id"],
                    "columns": search["columns_used"],
                    "threshold": search["threshold_used"],
                    "user_id": search["created_by"]
                }
                
                if search["search_type"] == "single":
                    search_params["name"] = search["query_names"][0]
                else:  # bulk
                    search_params["list"] = search["query_names"]
                    search_params["watchlist_id"] = search.get("watchlist_id")
                
                await add_search_to_queue(search["_id"], search["search_type"], search_params)
        else:
            logger.info("No pending searches found")
            
    except Exception as e:
        logger.error(f"Error loading pending searches: {str(e)}")
