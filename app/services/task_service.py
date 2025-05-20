from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.repositories.task_repository import TaskRepository
from app.repositories.file_repository import FileRepository
from app.models.task import TaskCreate, TaskUpdate
from app.exceptions import TaskException

class TaskService:
    def __init__(self, task_repository: TaskRepository, file_repository: FileRepository):
        self.task_repository = task_repository
        self.file_repository = file_repository

    async def create_task(self, task: TaskCreate) -> dict:
        """Create a new task"""
        # Validate file_id
        if not ObjectId.is_valid(task.file_id):
            raise TaskException("Invalid file_id format")
        
        file = await self.file_repository.get_file_by_id(task.file_id)
        if not file:
            raise TaskException("File not found")

        # Parse dates
        try:
            created_file_date = datetime.strptime(task.created_file_date, "%Y-%m-%d")
            updated_file_date = datetime.strptime(task.updated_file_date, "%Y-%m-%d")
        except ValueError:
            raise TaskException("Invalid date format (must be YYYY-MM-DD)")

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

    async def get_all_tasks(self, page: int = 1, limit: int = 10) -> dict:
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
        updated_task = await self.task_repository.update_task(task_id, task_update)
        return updated_task

    async def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        return await self.task_repository.delete_task(task_id)
