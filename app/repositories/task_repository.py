from typing import Optional, List, Tuple
from datetime import datetime
from bson import ObjectId
from app.database import get_collection

class TaskRepository:
    async def create_task(self, task_data: dict) -> str:
        """Create a new task in the database"""
        tasks_collection = await get_collection("tasks")
        result = await tasks_collection.insert_one(task_data)
        return str(result.inserted_id)

    async def get_all_tasks(self, page: int = 1, limit: int = 10) -> Tuple[List[dict], int]:
        """Get all tasks with pagination"""
        tasks_collection = await get_collection("tasks")
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Count total tasks
        total = await tasks_collection.count_documents({})
        
        # Get tasks with pagination
        cursor = tasks_collection.find().sort("created_at", -1).skip(skip).limit(limit)
        tasks = await cursor.to_list(length=limit)
        
        # Convert ObjectId and datetime to string
        for task in tasks:
            task["_id"] = str(task["_id"])
            task["created_file_date"] = task["created_file_date"].strftime("%Y-%m-%d")
            task["updated_file_date"] = task["updated_file_date"].strftime("%Y-%m-%d")
            task["created_at"] = task["created_at"].isoformat()
            task["updated_at"] = task["updated_at"].isoformat()
        
        return tasks, total

    async def get_task_by_id(self, task_id: str) -> Optional[dict]:
        """Get task by ID"""
        tasks_collection = await get_collection("tasks")
        
        if not ObjectId.is_valid(task_id):
            return None
            
        task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
        if task:
            task["_id"] = str(task["_id"])
            task["created_file_date"] = task["created_file_date"].strftime("%Y-%m-%d")
            task["updated_file_date"] = task["updated_file_date"].strftime("%Y-%m-%d")
            task["created_at"] = task["created_at"].isoformat()
            task["updated_at"] = task["updated_at"].isoformat()
        
        return task

    async def update_task(self, task_id: str, task_update: dict) -> dict:
        """Update task"""
        tasks_collection = await get_collection("tasks")
        
        if not ObjectId.is_valid(task_id):
            raise ValueError("Invalid task_id format")
            
        # Update task
        update_data = {"$set": task_update}
        result = await tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            update_data
        )
        
        if result.modified_count == 0:
            raise ValueError("Task not found")
            
        # Get updated task
        updated_task = await self.get_task_by_id(task_id)
        return updated_task

    async def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        tasks_collection = await get_collection("tasks")
        
        if not ObjectId.is_valid(task_id):
            return False
            
        result = await tasks_collection.delete_one({"_id": ObjectId(task_id)})
        return result.deleted_count > 0
