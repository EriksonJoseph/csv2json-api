from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from app.database import get_collection
from app.utils.serializers import list_serial, individual_serial

class MatchingRepository:
    def __init__(self):
        self.csv_collection_name = "csv"
        self.search_history_collection_name = "search_history"

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

    async def save_search_history(self, search_data: Dict[str, Any]) -> str:
        """Save search history"""
        collection = await get_collection(self.search_history_collection_name)
        
        search_data["created_at"] = datetime.now()
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
        
        # Get paginated results (exclude matched_records for performance)
        projection = {"matched_records": 0}
        cursor = collection.find(query, projection).sort("created_at", -1).skip(skip).limit(limit)
        history = await cursor.to_list(length=limit)

        
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
            to_return = {
                "_id": result.get("_id", ""),
                "task_id": result.get("task_id", ''),
                "total_query_names": len(result.get("query_names", [])),
                "total_found": len([
                    name for name in result.get("query_names", [])
                    if any(matched.get("query_name") == name for matched in result.get("matched_records", []))
                ]),
                "execution_time_ms": result.get('execution_time_ms', 0),
                "threshold_used": result.get("threshold_used", 0),
                "search_type": result.get('search_type', ''),
                "columns_used": result.get('columns_used', []),
                "query_names": result.get("query_names", []),
                "total_rows": result.get('total_rows', 0),
                "matched_result": [
                    {
                        "query_name": name,
                        "matched_record_number": len([
                            item for item in result.get("matched_records", [])
                            if item.get("query_name") == name
                        ])
                    }
                    for name in result.get("query_names", [])
                ]
            }
            return individual_serial(to_return)
        return None