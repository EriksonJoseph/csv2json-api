from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.repositories.task_repository import TaskRepository
from app.repositories.file_repository import FileRepository
from app.models.task import TaskCreate, TaskUpdate
from app.exceptions import TaskException
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import asyncio
import pandas as pd
import numpy as np

# Thread pool for CPU-bound tasks
thread_pool = ThreadPoolExecutor(max_workers=4)

# Cache for frequently accessed files
cached_files: Dict[str, Any] = {}

class TaskService:
    def __init__(self, task_repository: TaskRepository, file_repository: FileRepository):
        self.task_repository = task_repository
        self.file_repository = file_repository

    @lru_cache(maxsize=128)
    async def get_cached_file(self, file_id: str):
        """Get file with caching"""
        if file_id in cached_files:
            return cached_files[file_id]
        file = await self.file_repository.get_file_by_id(file_id)
        if file:
            cached_files[file_id] = file
        return file

    async def create_task(self, task: TaskCreate) -> dict:
        """Create a new task with optimized performance"""
        # Validate file_id
        if not ObjectId.is_valid(task.file_id):
            raise TaskException("Invalid file_id format")
        
        # Get file with caching
        file = await self.get_cached_file(task.file_id)
        if not file:
            raise TaskException("File not found")

        # Optimize date parsing using ThreadPoolExecutor
        async def parse_dates():
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                lambda: (
                    datetime.strptime(task.created_file_date, "%Y-%m-%d"),
                    datetime.strptime(task.updated_file_date, "%Y-%m-%d")
                )
            )
        
        created_file_date, updated_file_date = await parse_dates()

        # Prepare task data
        task_data = {
            "topic": task.topic,
            "created_file_date": created_file_date,
            "updated_file_date": updated_file_date,
            "references": task.references,
            "file_id": task.file_id,
            "is_done_created_doc": False,
            "column_names": [],
            "error_message": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        # Create task
        task_id = await self.task_repository.create_task(task_data)
        created_task = await self.task_repository.get_task_by_id(task_id)

        return created_task

    async def process_large_csv(self, file_path: str, chunk_size: int = 10000):
        """Process large CSV files in chunks"""
        chunks = []
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # Clean and process data in chunks
            chunk = chunk.replace({np.nan: None})
            chunks.append(chunk)
        
        # Combine chunks
        return pd.concat(chunks, ignore_index=True)

    async def get_all_tasks(self, page: int = 1, limit: int = 10) -> dict:
        """Get all tasks with pagination and caching"""
        # Use cached result if available
        cache_key = f"tasks_page_{page}_limit_{limit}"
        if cache_key in cached_files:
            return cached_files[cache_key]

        tasks = await self.task_repository.get_all_tasks(page, limit)
        cached_files[cache_key] = tasks
        return tasks
        """Get all tasks with pagination"""
        tasks, total = await self.task_repository.get_all_tasks(page, limit)
        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "limit": limit
        }

    async def get_task_by_id(self, task_id: str) -> Optional[dict]:
        """Get task by ID"""
        return await self.task_repository.get_task_by_id(task_id)

    async def update_task(self, task_id: str, task_update: TaskUpdate) -> dict:
        """Update task"""
        if task_update.updated_file_date:
            try:
                datetime.strptime(task_update.updated_file_date, "%Y-%m-%d")
            except ValueError:
                raise TaskException("Invalid date format (must be YYYY-MM-DD)")
        if task_update.created_file_date:
            try:
                datetime.strptime(task_update.created_file_date, "%Y-%m-%d")
            except ValueError:
                raise TaskException("Invalid date format (must be YYYY-MM-DD)")

        updated_task = await self.task_repository.update_task(task_id, task_update)
        return updated_task

    async def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        return await self.task_repository.delete_task(task_id)

    async def create_task(self, task: TaskCreate) -> dict:
        # Optimize date parsing using ThreadPoolExecutor
        async def parse_dates():
            return await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                lambda: (
                    datetime.strptime(task.created_file_date, "%Y-%m-%d"),
                    datetime.strptime(task.updated_file_date, "%Y-%m-%d")
                )
            )

        # Parse dates
        created_file_date, updated_file_date = await parse_dates()

        # Prepare task data
        task_data = {
            "topic": task.topic,
            "created_file_date": created_file_date,
            "updated_file_date": updated_file_date,
            "references": task.references,
            "file_id": task.file_id,
            "is_done_created_doc": False,
            "column_names": [],
            "error_message": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        # Create task
        task_id = await self.task_repository.create_task(task_data)
        created_task = await self.task_repository.get_task_by_id(task_id)
        
        # Add task to processing queue
        from app.workers.background_worker import add_task_to_queue
        await add_task_to_queue(str(task_id), task.file_id)
        
        return created_task
