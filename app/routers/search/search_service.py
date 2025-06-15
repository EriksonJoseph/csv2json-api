from typing import Dict, Any
import re
from app.routers.search.search_repository import SearchRepository
from app.routers.search.search_model import (AdvancedSearchRequest,ColumnOptions)
from app.exceptions import TaskException
from concurrent.futures import ThreadPoolExecutor

import math

class SearchService:
    def clean_json(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: self.clean_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_json(i) for i in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        else:
            return obj

    def __init__(self) -> None:
        self.repository: SearchRepository = SearchRepository()
        # Thread pool for CPU-bound fuzzy matching operations
        self.thread_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=4)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better matching"""
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep letters, numbers, and spaces
        text = re.sub(r'[^\w\s]', '', text)
        
        return text

    def _matches_criteria(self, cell_value: str, search_term: str, options: ColumnOptions) -> bool:
        """Check if cell_value matches search_term based on given options"""
        if not cell_value or not search_term:
            return False
        
        cell_str = str(cell_value)
        search_str = str(search_term)
        
        # Apply case sensitivity option
        if not options.match_case:
            cell_str = cell_str.lower()
            search_str = search_str.lower()
        
        # Apply whole word matching
        if options.whole_word:
            # Use word boundary regex for whole word matching
            import re
            pattern = r'\b' + re.escape(search_str) + r'\b'
            flags = 0 if options.match_case else re.IGNORECASE
            match = re.search(pattern, cell_str, flags)
            if not match:
                return False
            
            # If match_length is True, check that the matched text has exact length
            if options.match_length:
                matched_text = match.group()
                return len(matched_text) == len(search_term)
            return True
        else:
            # Simple substring matching
            if search_str not in cell_str:
                return False
            
            # If match_length is True, check that cell_value has exact length as search_term
            if options.match_length:
                return len(cell_str) == len(search_term)
            return True

    async def create_search(self, request: AdvancedSearchRequest, user_id: str) -> str:
        """Create advanced search task for background processing"""
        
        # Validate task exists
        if not await self.repository.validate_task_exists(request.task_id):
            raise TaskException(f"Task {request.task_id} not found or has no data")
        
        # Get total rows count
        total_rows = await self.repository.get_task_record_count(request.task_id)
        
        # Create pending search entry
        search_data = self.clean_json({
            "task_id": request.task_id,
            "column_names": request.column_names,
            "column_options": {k: v.dict() for k, v in request.column_options.items()},
            "query_list": request.list,
            "total_queries": len(request.list),
            "total_rows": total_rows,
            "status": "pending",
            "created_by": user_id
        })
        
        # Save search history with pending status
        search_id = await self.repository.save_search_history(search_data, user_id)
        
        # Add to search queue
        from app.workers.background_worker import add_search_to_queue
        await add_search_to_queue(search_id,{
            "task_id": request.task_id,
            "column_names": request.column_names,
            "column_options": request.column_options,
            "query_list": request.list,
            "user_id": user_id
        })
        
        # Return response with pending status
        return "Create search background process successfully!"
    
    async def get_search_history(self, user_id: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get search history for a user"""
        history_data = await self.repository.get_search_history(user_id, page, limit)
        # Clean the data to prevent JSON serialization errors
        return self.clean_json(history_data)

    async def get_search_result(self, search_id: str) -> Dict[str, Any]:
        """Get search result by search_id"""
        result = await self.repository.get_search_result(search_id)
        if not result:
            raise TaskException(f"Search result with ID {search_id} not found")
        # Clean the data to prevent JSON serialization errors
        return self.clean_json(result)
