from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId # type: ignore
from app.database import get_collection
from app.utils.serializers import list_serial, individual_serial
from app.routers.task.task_repository import TaskRepository

class SearchRepository:
    def __init__(self) -> None:
        self.csv_collection_name: str = "csv"
        self.search_history_collection_name: str = "search_history"
        self.task_repository = TaskRepository()

    async def get_csv_data_by_task_id(self, task_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get CSV data for a specific task"""
        collection = await get_collection(self.csv_collection_name)
        
        # Create query filter
        query = {"task_id": task_id}
        
        # Execute query
        if limit:
            cursor = collection.find(query).limit(limit)
        else:
            cursor = collection.find(query)
        
        records = await cursor.to_list(length=None)
        return list_serial(records)

    async def get_available_columns(self, task_id: str) -> Dict[str, Any]:
        """Get available columns for a task"""
        collection = await get_collection(self.csv_collection_name)
        
        # Get one document to extract column names
        sample_doc = await collection.find_one({"task_id": task_id})
        
        if not sample_doc:
            return {
                "available_columns": [],
                "recommended_columns": [],
                "total_records": 0
            }
        
        # Count total records
        total_records = await collection.count_documents({"task_id": task_id})
        
        # Extract column names (exclude MongoDB internal fields)
        available_columns = [key for key in sample_doc.keys() 
                           if not key.startswith('_') and key not in ['task_id', 'processed_at']]
        
        # Define recommended columns for name matching
        recommended_columns = []
        name_column_patterns = [
            'NameAlias_WholeName',
            'NameAlias_FirstName', 
            'NameAlias_LastName',
            'NameAlias_MiddleName'
        ]
        
        for pattern in name_column_patterns:
            if pattern in available_columns:
                recommended_columns.append(pattern)
        
        return {
            "available_columns": available_columns,
            "recommended_columns": recommended_columns,
            "total_records": total_records
        }

    async def search_in_columns(self, task_id: str, columns: List[str], 
                              limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search specific columns in CSV data"""
        collection = await get_collection(self.csv_collection_name)
        
        # Create projection to only get specified columns plus some metadata
        projection = {"task_id": 1, "_id": 1}
        for col in columns:
            projection[col] = 1
        
        # Add some additional useful fields
        additional_fields = [
            "Entity_LogicalId", 
            "Entity_EU_ReferenceNumber",
            "Entity_SubjectType"
        ]
        for field in additional_fields:
            if field not in projection:
                projection[field] = 1
        
        query = {"task_id": task_id}
        
        if limit:
            cursor = collection.find(query, projection).limit(limit)
        else:
            cursor = collection.find(query, projection)
        
        records = await cursor.to_list(length=None)
        return list_serial(records)

    async def save_search_history(self, search_data: Dict[str, Any], created_by: str) -> str:
        """Save search history"""
        collection = await get_collection(self.search_history_collection_name)
        
        # Get task information to save topic and original filename
        task_id = search_data.get("task_id")
        if task_id:
            try:
                # Get task details
                tasks_collection = await get_collection("tasks")
                task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
                
                if task:
                    search_data["task_topic"] = task.get("topic", "")
                    
                    # Get file details using file_id from task
                    file_id = task.get("file_id")
                    if file_id:
                        files_collection = await get_collection("files")
                        file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
                        if file_doc:
                            search_data["original_filename"] = file_doc.get("original_filename", "")
                        else:
                            search_data["original_filename"] = ""
                    else:
                        search_data["original_filename"] = ""
                else:
                    search_data["task_topic"] = ""
                    search_data["original_filename"] = ""
            except Exception as e:
                print(f"Warning: Could not fetch task/file details for search history: {e}")
                search_data["task_topic"] = ""
                search_data["original_filename"] = ""
        else:
            search_data["task_topic"] = ""
            search_data["original_filename"] = ""
        
        # Add audit fields
        now = datetime.now()
        search_data.update({
            "created_at": now,
            "created_by": created_by,
            "updated_at": now,
            "updated_by": created_by
        })
        
        result = await collection.insert_one(search_data)
        return str(result.inserted_id)

    async def get_search_history(self, user_id: str, page: int = 1, 
                               limit: int = 10) -> Dict[str, Any]:
        """Get search history for a user"""
        collection = await get_collection(self.search_history_collection_name)
        
        skip = (page - 1) * limit
        query = {"created_by": user_id}
        
        # Count total records
        total = await collection.count_documents(query)
        
        # Get paginated results (exclude heavy fields for performance)
        projection = {
            "matched_records": 0, 
            "results": 0,
            "column_options": 0,
            "query_list": 0,
            "query_names": 0
        }
        cursor = collection.find(query, projection).sort("created_at", -1).skip(skip).limit(limit)
        history = await cursor.to_list(length=limit)

        # Since we exclude query fields from projection, we need to get the count separately
        # Add query count information from total_queries field if available
        for item in history:
            # Use total_queries field if available, otherwise set to 0
            total_queries = item.get("total_queries", 0)
            item["query_name_length"] = total_queries
        
        return {
            "list": list_serial(history),
            "total": total,
            "page": page,
            "limit": limit
        }

    async def get_task_record_count(self, task_id: str) -> int:
        """Get total number of records for a task"""
        collection = await get_collection(self.csv_collection_name)
        return await collection.count_documents({"task_id": task_id})

    async def validate_task_exists(self, task_id: str) -> bool:
        """Check if task has any data in CSV collection"""
        collection = await get_collection(self.csv_collection_name)
        count = await collection.count_documents({"task_id": task_id})
        return count > 0

    async def get_search_result(self, search_id: str) -> Optional[Dict[str, Any]]:
        """Get search result by search_id"""
        collection = await get_collection(self.search_history_collection_name)
        
        result = await collection.find_one({"_id": ObjectId(search_id)})
        if result:
            # Get task details and append to result
            if result.get("task_id"):
                task_detail = await self.task_repository.get_task_by_id(result.get("task_id"))
                if task_detail:
                    result["task_detail"] = task_detail
            
            return individual_serial(result)
        return None

    async def update_search_status(self, search_id: str, status: str, updated_by: str, 
                                 additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update search status and additional data"""
        collection = await get_collection(self.search_history_collection_name)
        
        update_data = {
            "status": status,
            "updated_at": datetime.now(),
            "updated_by": updated_by
        }
        
        if additional_data:
            update_data.update(additional_data)
        
        result = await collection.update_one(
            {"_id": ObjectId(search_id)},
            {"$set": update_data}
        )
        
        return result.modified_count > 0

    async def get_pending_searches(self) -> List[Dict[str, Any]]:
        """Get all pending search tasks"""
        collection = await get_collection(self.search_history_collection_name)
        
        cursor = collection.find({"status": "pending"})
        searches = await cursor.to_list(length=None)
        
        return list_serial(searches)