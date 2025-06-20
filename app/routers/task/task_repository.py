from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from bson import ObjectId # type: ignore
from app.database import get_collection
from app.utils.serializers import list_serial

class TaskRepository:
    async def create_task(self, task_data: Dict[str, Any], user_id: str) -> str:
        """Create a new task in the database"""
        tasks_collection = await get_collection("tasks")
        
        # Add audit fields
        task_data.update({
            "created_by": user_id,
            "created_at": datetime.now(),
            "updated_by": user_id,
            "updated_at": datetime.now()
        })
        
        result = await tasks_collection.insert_one(task_data)
        return str(result.inserted_id)

    async def get_all_tasks(self, page: int = 1, limit: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """Get all tasks with pagination"""
        tasks_collection = await get_collection("tasks")
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Count total tasks
        total = await tasks_collection.count_documents({})
        
        # Use aggregation to join with files collection
        pipeline = [
            {
                "$addFields": {
                    "file_id_obj": {"$toObjectId": "$file_id"}
                }
            },
            {
                "$lookup": {
                    "from": "files",
                    "localField": "file_id_obj",
                    "foreignField": "_id",
                    "as": "file_info"
                }
            },
            {
                "$unwind": {
                    "path": "$file_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$skip": skip
            },
            {
                "$limit": limit
            }
        ]
        
        cursor = tasks_collection.aggregate(pipeline)
        tasks = await cursor.to_list(length=limit)
        
        # Convert ObjectId and datetime to string
        for task in tasks:
            task["_id"] = str(task["_id"])
            task["created_file_date"] = task["created_file_date"].strftime("%Y-%m-%d")
            task["updated_file_date"] = task["updated_file_date"].strftime("%Y-%m-%d")
            task["created_at"] = task["created_at"].isoformat()
            task["updated_at"] = task["updated_at"].isoformat()
            task["total_columns"] = len(task["column_names"])
            # Add original_filename from joined file_info
            if "file_info" in task and task["file_info"]:
                task["original_filename"] = task["file_info"].get("original_filename", "")
            else:
                task["original_filename"] = ""
            # Remove column_names, file_info, and temporary field from response
            task.pop("column_names", None)
            task.pop("file_info", None)
            task.pop("file_id_obj", None)
        
        return tasks, total

    async def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        tasks_collection = await get_collection("tasks")
        
        if not ObjectId.is_valid(task_id):
            return None
        
        # Use aggregation to join with files collection
        pipeline = [
            {
                "$match": {"_id": ObjectId(task_id)}
            },
            {
                "$addFields": {
                    "file_id_obj": {"$toObjectId": "$file_id"}
                }
            },
            {
                "$lookup": {
                    "from": "files",
                    "localField": "file_id_obj",
                    "foreignField": "_id",
                    "as": "file_info"
                }
            },
            {
                "$unwind": {
                    "path": "$file_info",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]
        
        cursor = tasks_collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if not result:
            return None
            
        task = result[0]
        task["_id"] = str(task["_id"])
        # Handle both string and datetime dates
        if isinstance(task["created_file_date"], datetime):
            task["created_file_date"] = task["created_file_date"].strftime("%Y-%m-%d")
        if isinstance(task["updated_file_date"], datetime):
            task["updated_file_date"] = task["updated_file_date"].strftime("%Y-%m-%d")
        task["created_at"] = task["created_at"].isoformat()
        task["updated_at"] = task["updated_at"].isoformat()
        
        # Add original_filename from joined file_info
        if "file_info" in task and task["file_info"]:
            task["original_filename"] = task["file_info"].get("original_filename", "")
        else:
            task["original_filename"] = ""
        
        # Remove file_info and temporary field from response
        task.pop("file_info", None)
        task.pop("file_id_obj", None)
        
        return task

    async def update_task(self, task_id: str, task_update: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update task"""
        tasks_collection = await get_collection("tasks")
        
        if not ObjectId.is_valid(task_id):
            raise ValueError("Invalid task_id format")
            
        # Convert Pydantic model to dictionary and filter out None values
        update_fields = {k: v for k, v in task_update.items() if v is not None}
        
        # Add audit fields
        update_fields.update({
            "updated_by": user_id,
            "updated_at": datetime.now()
        })
        
        update_data = {"$set": update_fields}
        result = await tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            update_data
        )
        
        if result.modified_count == 0:
            raise ValueError("Task not found")
            
        # Get updated task
        updated_task = await self.get_task_by_id(task_id)
        if updated_task is None:
            raise ValueError("Task not found after update")
        return updated_task

    async def delete_task(self, task_id: str) -> bool:
        """Delete task and all related documents from all collections"""
        if not ObjectId.is_valid(task_id):
            return False
        
        try:
            # Delete from all collections that contain task_id
            collections_to_clean = [
                "tasks",           # Main task collection
                "csv",             # CSV data
                "search_history",  # Search history
                # Add other collections as needed
            ]
            
            total_deleted = 0
            
            for collection_name in collections_to_clean:
                collection = await get_collection(collection_name)
                
                if collection_name == "tasks":
                    # Delete by _id for tasks collection
                    result = await collection.delete_many({"_id": ObjectId(task_id)})
                else:
                    # Delete by task_id for other collections
                    result = await collection.delete_many({"task_id": task_id})
                
                total_deleted += result.deleted_count
                print(f"Deleted {result.deleted_count} documents from {collection_name}")
            
            print(f"Total deleted: {total_deleted} documents related to task_id: {task_id}")
            return total_deleted > 0
            
        except Exception as e:
            print(f"Error deleting task {task_id}: {str(e)}")
            return False

    async def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending tasks (is_done_created_doc=False)"""
        tasks_collection = await get_collection("tasks")
        cursor = tasks_collection.find({"is_done_created_doc": False})
        tasks = await cursor.to_list(length=100)  # Limit to 100 pending tasks
        return list_serial(tasks)
    
    async def update_task_status(self, task_id: str, is_done_created_doc: bool, 
                             column_names: List[str], error_message: Optional[str],
                             processing_time: Optional[float] = None, total_rows: Optional[int] = None, user_id: str = "worker") -> None:
        """Update task status after processing"""
        if not ObjectId.is_valid(task_id):
            raise ValueError("Invalid task_id format")
            
        tasks_collection = await get_collection("tasks")
        
        update_data = {
            "is_done_created_doc": is_done_created_doc,
            "column_names": column_names,
            "updated_by": user_id,
            "updated_at": datetime.now()
        }
        
        if error_message is not None:
            update_data["error_message"] = error_message
        if processing_time is not None:
            update_data["processing_time"] = processing_time
        if total_rows is not None:
            update_data["total_rows"] = total_rows
        
        await tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data}
        )
