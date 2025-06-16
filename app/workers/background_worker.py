import asyncio
import os
import re
from datetime import datetime
from typing import Dict, Optional, Any
from app.routers.task.task_repository import TaskRepository
from app.routers.file.file_repository import FileRepository
from app.database import get_collection
from app.dependencies.file import read_csv_file
import logging

# Configure logging with explicit handler setup
import sys

# Create handlers
file_handler = logging.FileHandler("logs/worker.log")
console_handler = logging.StreamHandler(sys.stdout)

# Set levels for handlers
file_handler.setLevel(logging.DEBUG)
console_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Configure logger
logger: logging.Logger = logging.getLogger("background_worker")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Prevent duplicate logs from root logger
logger.propagate = False

# Test debug logging on startup
logger.debug("🔧 DEBUG logging is enabled for background worker")
logger.info("📋 Background worker module loaded")

# Global task queue
task_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
search_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
email_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
is_worker_running: bool = False
is_search_worker_running: bool = False
is_email_worker_running: bool = False

# Global variable to track current task
_current_task: Optional[str] = None
_current_search: Optional[str] = None
_current_email: Optional[str] = None

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

async def get_current_processing_email() -> Optional[Dict[str, Any]]:
    """
    Get current processing email information
    
    Returns:
        dict: Current email information if processing, None otherwise
    """
    if _current_email is None:
        return None
    
    return {
        "email_id": _current_email,
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

async def process_search_task(search_id: str, search_params: Dict[str, Any]) -> None:
    """
    Process a search task and update results
    
    Args:
        search_id: ID of the search task
        search_params: Search parameters
    """
    global _current_search
    _current_search = search_id
    start_time = datetime.now()
    logger.info(f"🔍 [SEARCH-{search_id}] Starting search processing")
    logger.debug(f"🔍 [SEARCH-{search_id}] Search params: {search_params}")
    
    from app.routers.search.search_repository import SearchRepository
    from app.routers.search.search_service import SearchService
    
    search_repo = None
    search_service = None
    
    try:
        logger.debug(f"🔍 [SEARCH-{search_id}] Step 1: Initializing repositories")
        search_repo = SearchRepository()
        search_service = SearchService()
        logger.debug(f"🔍 [SEARCH-{search_id}] ✅ Repositories initialized successfully")
        
        logger.debug(f"🔍 [SEARCH-{search_id}] Step 2: Updating status to processing")
        await search_repo.update_search_status(search_id, "processing", "worker")
        logger.debug(f"🔍 [SEARCH-{search_id}] ✅ Status updated to processing")
        
        logger.debug(f"🔍 [SEARCH-{search_id}] Step 3: Importing ColumnOptions")
        from app.routers.search.search_model import ColumnOptions
        logger.debug(f"🔍 [SEARCH-{search_id}] ✅ ColumnOptions imported")
        
        logger.debug(f"🔍 [SEARCH-{search_id}] Step 4: Getting CSV collection for aggregation")
        logger.debug(f"🔍 [SEARCH-{search_id}] Task ID: {search_params.get('task_id')}")
        logger.debug(f"🔍 [SEARCH-{search_id}] Column names: {search_params.get('column_names')}")
        
        # Get CSV collection for aggregation queries
        csv_collection = await get_collection("csv")
        
        # Verify that data exists for this task
        total_count = await csv_collection.count_documents({"task_id": search_params["task_id"]})
        logger.debug(f"🔍 [SEARCH-{search_id}] ✅ Total documents for task: {total_count}")
        
        if total_count == 0:
            raise Exception("No CSV data found for the specified task")
        
        results = []
        logger.debug(f"🔍 [SEARCH-{search_id}] Step 5: Processing query list")
        logger.debug(f"🔍 [SEARCH-{search_id}] Query list length: {len(search_params.get('query_list', []))}")
        
        # Process each search query
        for query_idx, query_row in enumerate(search_params["query_list"]):
            logger.debug(f"🔍 [SEARCH-{search_id}] Processing query {query_idx + 1}/{len(search_params['query_list'])}")
            logger.debug(f"🔍 [SEARCH-{search_id}] Query row: {query_row}")
            
            try:
                query_no = int(query_row.get("no", 0))
                logger.debug(f"🔍 [SEARCH-{search_id}] Query no: {query_no}")
                
                # Build query name from all non-empty column values
                query_name_parts = []
                logger.debug(f"🔍 [SEARCH-{search_id}] Column names: {search_params.get('column_names', [])}")
                
                for col in search_params["column_names"]:
                    if col in query_row and query_row[col]:
                        query_name_parts.append(query_row[col])
                query_name = " ".join(query_name_parts)
                logger.debug(f"🔍 [SEARCH-{search_id}] Query name: '{query_name}'")
                
                column_results = {}
                
                # Process each column
                for col_idx, column in enumerate(search_params["column_names"]):
                    logger.debug(f"🔍 [SEARCH-{search_id}] Processing column {col_idx + 1}/{len(search_params['column_names'])}: '{column}'")
                    
                    search_term = query_row.get(column, "")
                    logger.debug(f"🔍 [SEARCH-{search_id}] Search term for '{column}': '{search_term}'")
                    
                    if not search_term:
                        column_results[column] = {
                            "found": False,
                            "count": 0,
                            "search_term": ""
                        }
                        logger.debug(f"🔍 [SEARCH-{search_id}] Empty search term for column '{column}', skipping")
                        continue
                    
                    try:
                        # Get options for this column and convert to ColumnOptions object
                        logger.debug(f"🔍 [SEARCH-{search_id}] Getting options for column '{column}'")
                        column_option_dict = search_params["column_options"].get(column, {})
                        logger.debug(f"🔍 [SEARCH-{search_id}] Column options dict: {column_option_dict}")
                        
                        if hasattr(column_option_dict, 'dict'):
                            # It's already a ColumnOptions object
                            options = column_option_dict
                            logger.debug(f"🔍 [SEARCH-{search_id}] Using existing ColumnOptions object")
                        else:
                            # It's a dictionary, convert to ColumnOptions
                            options = ColumnOptions(**column_option_dict)
                            logger.debug(f"🔍 [SEARCH-{search_id}] Created ColumnOptions from dict: {options}")
                        
                        # Build aggregation pipeline for counting matches
                        logger.debug(f"🔍 [SEARCH-{search_id}] Building aggregation pipeline for column '{column}'")
                        
                        # Create MongoDB match conditions based on ColumnOptions
                        match_conditions = {"task_id": search_params["task_id"]}
                        
                        # Build regex pattern based on options
                        if options.whole_word and options.match_case:
                            # Exact whole word match with case sensitivity
                            pattern = f"^{re.escape(search_term)}$"
                            match_conditions[column] = {"$regex": pattern}
                        elif options.whole_word and not options.match_case:
                            # Exact whole word match without case sensitivity
                            pattern = f"^{re.escape(search_term)}$"
                            match_conditions[column] = {"$regex": pattern, "$options": "i"}
                        elif not options.whole_word and options.match_case:
                            # Partial match with case sensitivity
                            pattern = re.escape(search_term)
                            match_conditions[column] = {"$regex": pattern}
                        else:
                            # Partial match without case sensitivity
                            pattern = re.escape(search_term)
                            match_conditions[column] = {"$regex": pattern, "$options": "i"}
                        
                        logger.debug(f"🔍 [SEARCH-{search_id}] Match conditions: {match_conditions}")
                        
                        # Use aggregation to count matches
                        pipeline = [
                            {"$match": match_conditions},
                            {"$count": "total"}
                        ]
                        
                        logger.debug(f"🔍 [SEARCH-{search_id}] Executing aggregation pipeline for column '{column}'")
                        
                        try:
                            result = await csv_collection.aggregate(pipeline).to_list(length=1)
                            matching_count = result[0]["total"] if result else 0
                            logger.debug(f"🔍 [SEARCH-{search_id}] Found {matching_count} matches for column '{column}' using aggregation")
                        except Exception as agg_error:
                            logger.error(f"🔍 [SEARCH-{search_id}] Aggregation error for column '{column}': {agg_error}")
                            raise Exception(f"Aggregation failed for column '{column}': {str(agg_error)}")
                        
                        column_results[column] = {
                            "found": matching_count > 0,
                            "count": matching_count,
                            "search_term": search_term
                        }
                        
                    except Exception as col_error:
                        logger.error(f"🔍 [SEARCH-{search_id}] Error processing column '{column}': {col_error}")
                        raise Exception(f"Error processing column '{column}': {str(col_error)}")
                
                # Add query result
                query_result = {
                    "query_no": query_no,
                    "query_name": query_name,
                    "column_results": column_results
                }
                results.append(query_result)
                logger.debug(f"🔍 [SEARCH-{search_id}] ✅ Query {query_idx + 1} processed successfully")
                
            except Exception as query_error:
                logger.error(f"🔍 [SEARCH-{search_id}] Error processing query {query_idx + 1}: {query_error}")
                raise Exception(f"Error processing query {query_idx + 1}: {str(query_error)}")
        
        logger.debug(f"🔍 [SEARCH-{search_id}] Step 6: Calculating execution time and results")
        # Calculate execution time
        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Count total queries processed and found
        total_queries = len(results)
        total_found = sum(1 for result in results 
                        if any(col_result["found"] for col_result in result["column_results"].values()))
        
        logger.debug(f"🔍 [SEARCH-{search_id}] Total queries: {total_queries}, Found: {total_found}")
        
        # Update search with results
        additional_data = {
            "results": results,
            "total_queries": total_queries,
            "results_found": total_found,
            "total_searched": total_queries,
            "execution_time_ms": execution_time_ms,
            "processing_time": execution_time_ms / 1000.0,
            "completed_at": end_time.isoformat()
        }
        
        logger.debug(f"🔍 [SEARCH-{search_id}] Step 7: Updating search status to completed")
        # Update search status to completed
        await search_repo.update_search_status(search_id, "completed", "worker", additional_data)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"🔍 [SEARCH-{search_id}] ✅ Successfully processed search in {execution_time:.2f} seconds")
        
    except Exception as e:
        error_message = str(e)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Get the line number where the error occurred
        import traceback
        tb = traceback.format_exc()
        logger.error(f"🔍 [SEARCH-{search_id}] ❌ FULL ERROR TRACEBACK:")
        logger.error(f"🔍 [SEARCH-{search_id}] {tb}")
        logger.error(f"🔍 [SEARCH-{search_id}] Error processing search in {execution_time:.2f} seconds: {error_message}")
        
        # Update search status to failed
        try:
            if search_repo:
                await search_repo.update_search_status(
                    search_id, 
                    "failed", 
                    "worker", 
                    {"error_message": error_message, "execution_time_ms": execution_time * 1000, "traceback": tb}
                )
                logger.debug(f"🔍 [SEARCH-{search_id}] ✅ Updated status to failed")
            else:
                logger.error(f"🔍 [SEARCH-{search_id}] ❌ Could not update status - search_repo is None")
        except Exception as status_error:
            logger.error(f"🔍 [SEARCH-{search_id}] ❌ Error updating search status to failed: {status_error}")
    finally:
        # Clear current search
        _current_search = None
        logger.debug(f"🔍 [SEARCH-{search_id}] Cleared current search")

async def process_email_task(email_id: str) -> None:
    """
    Process an email task
    
    Args:
        email_id: ID of the email task to process
    """
    global _current_email
    _current_email = email_id
    start_time = datetime.now()
    logger.info(f"📧 [EMAIL-{email_id}] Starting email processing")
    
    try:
        # Import email service
        from app.routers.email.email_service import EmailService
        
        email_service = EmailService()
        
        # Get email task
        logger.debug(f"📧 [EMAIL-{email_id}] Fetching email task from database")
        email_task = await email_service.get_email_task(email_id)
        if not email_task:
            raise Exception(f"Email task not found: {email_id}")
        
        # Check if email was already sent (double check)
        if email_task.get("sent_at") is not None:
            logger.warning(f"📧 [EMAIL-{email_id}] ⚠️ Email already sent at {email_task['sent_at']}, skipping")
            return
        
        if email_task.get("status") == "sent":
            logger.warning(f"📧 [EMAIL-{email_id}] ⚠️ Email status is already 'sent', skipping")
            return
        
        logger.info(f"📧 [EMAIL-{email_id}] Email task ready for sending: to={email_task.get('to_emails')}, subject='{email_task.get('subject')}'")
        
        # Send email
        success = await email_service.send_email_task(email_task)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if success:
            logger.info(f"📧 [EMAIL-{email_id}] ✅ Successfully processed email in {execution_time:.2f} seconds")
        else:
            logger.error(f"📧 [EMAIL-{email_id}] ❌ Failed to process email in {execution_time:.2f} seconds")
        
    except Exception as e:
        error_message = str(e)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.error(f"📧 [EMAIL-{email_id}] ❌ Error processing email in {execution_time:.2f} seconds: {error_message}")
        
        # Handle error in email service
        try:
            from app.routers.email.email_service import EmailService
            email_service = EmailService()
            await email_service._handle_email_failure(email_id, error_message)
        except Exception as handle_error:
            logger.error(f"📧 [EMAIL-{email_id}] Error handling email failure: {handle_error}")
            
    finally:
        # Clear current email
        _current_email = None
        logger.debug(f"📧 [EMAIL-{email_id}] Cleared current email")

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
            search_params = search_data["search_params"]
            
            try:
                await process_search_task(search_id, search_params)
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

async def email_worker_loop() -> None:
    """
    Main email worker loop that processes email tasks from the queue
    """
    global is_email_worker_running
    is_email_worker_running = True
    
    logger.info("Starting email worker loop")
    
    try:
        while True:
            # Get email task from queue
            logger.debug("📧 Email worker waiting for tasks...")
            email_data = await email_queue.get()
            email_id = email_data["email_id"]
            
            logger.info(f"📧 Email worker picked up task: {email_id}")
            
            try:
                await process_email_task(email_id)
            except Exception as e:
                logger.error(f"📧 ❌ Uncaught error in email worker: {str(e)}")
            finally:
                # Clear current email
                _current_email = None
                # Mark email task as done in the queue
                email_queue.task_done()
                logger.debug(f"📧 Email worker finished processing {email_id}")
    except asyncio.CancelledError:
        logger.info("Email worker loop cancelled")
    except Exception as e:
        logger.error(f"Email worker loop error: {str(e)}")
    finally:
        is_email_worker_running = False

async def add_task_to_queue(task_id: str, file_id: str) -> None:
    """
    Add a task to the processing queue
    
    Args:
        task_id: ID of the task
        file_id: ID of the file to process
    """
    await task_queue.put({"task_id": task_id, "file_id": file_id})
    logger.info(f"Added task {task_id} to the queue")

async def add_search_to_queue(search_id: str, search_params: Dict[str, Any]) -> None:
    """
    Add a search task to the processing queue
    
    Args:
        search_id: ID of the search
        search_params: Search parameters
    """
    await search_queue.put({
        "search_id": search_id, 
        "search_params": search_params
    })
    logger.info(f"Added search {search_id} to the queue")

async def add_email_to_queue(email_id: str) -> None:
    """
    Add an email task to the processing queue
    
    Args:
        email_id: ID of the email task
    """
    await email_queue.put({"email_id": email_id})
    logger.info(f"📧 ➕ Added email {email_id} to processing queue (queue size: ~{email_queue.qsize()})")

async def start_worker() -> None:
    """
    Start the background worker if it's not already running
    """
    global is_worker_running, is_search_worker_running, is_email_worker_running
    
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
    
    if not is_email_worker_running:
        # Start email worker as a background task
        asyncio.create_task(email_worker_loop())
        logger.info("Email worker started")

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
    
    from app.routers.search.search_repository import SearchRepository
    
    search_repo = SearchRepository()
    
    try:
        # Get searches that aren't completed
        pending_searches = await search_repo.get_pending_searches()
        
        if pending_searches:
            logger.info(f"Found {len(pending_searches)} pending searches")
            
            # Add searches to queue
            for search in pending_searches:
                search_params = {
                    "task_id": search["task_id"],
                    "user_id": search["created_by"],
                    "column_names": search.get("column_names", []),
                    "column_options": search.get("column_options", {}),
                    "query_list": search.get("query_list", [])
                }
                
                
                await add_search_to_queue(search["_id"], search_params)
        else:
            logger.info("No pending searches found")
            
    except Exception as e:
        logger.error(f"Error loading pending searches: {str(e)}")

async def load_pending_emails() -> None:
    """
    Load pending email tasks from the database and add them to the queue
    """
    logger.info("📧 Loading pending emails from database")
    
    try:
        from app.routers.email.email_service import EmailService
        
        email_service = EmailService()
        
        # Get pending email tasks
        pending_emails = await email_service.get_pending_tasks()
        
        if pending_emails:
            logger.info(f"📧 Found {len(pending_emails)} pending emails to process")
            
            # Add emails to queue with detailed logging
            for email in pending_emails:
                email_id = email["_id"]
                status = email.get("status", "unknown")
                sent_at = email.get("sent_at")
                created_at = email.get("created_at")
                
                logger.info(f"📧 Loading email {email_id}: status={status}, sent_at={sent_at}, created_at={created_at}")
                
                # Double check: only queue if not already sent
                if sent_at is None and status in ["pending", "retry"]:
                    await add_email_to_queue(email_id)
                    logger.info(f"📧 ✅ Added email {email_id} to queue")
                else:
                    logger.warning(f"📧 ⚠️ Skipping email {email_id} - already sent or wrong status")
        else:
            logger.info("📧 No pending emails found in database")
            
    except Exception as e:
        logger.error(f"📧 ❌ Error loading pending emails: {str(e)}")
