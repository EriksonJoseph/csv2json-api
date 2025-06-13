from typing import List, Dict, Any, Tuple, Optional
import re
from rapidfuzz import fuzz
from bson import ObjectId
from app.routers.matching.matching_repository import MatchingRepository
from app.routers.watchlist.watchlist_repository import WatchlistRepository
from app.routers.matching.matching_model import (
    SingleSearchRequest, BulkSearchRequest, SingleSearchResponse, 
    BulkSearchResponse, BulkSearchItem, MatchedRecord, AvailableColumnsResponse
)
from app.exceptions import TaskException
import asyncio
from concurrent.futures import ThreadPoolExecutor

import math

class MatchingService:
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
        self.repository: MatchingRepository = MatchingRepository()
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

    def _fuzzy_match(self, query: str, target: str, method: str = "ratio") -> float:
        """Perform fuzzy matching between two strings"""
        if not query or not target:
            return 0.0
        
        query_clean = self._clean_text(query)
        target_clean = self._clean_text(target)
        
        if not query_clean or not target_clean:
            return 0.0
        
        # Use different matching methods
        if method == "ratio":
            return fuzz.ratio(query_clean, target_clean)
        elif method == "partial_ratio":
            return fuzz.partial_ratio(query_clean, target_clean)
        elif method == "token_sort_ratio":
            return fuzz.token_sort_ratio(query_clean, target_clean)
        elif method == "token_set_ratio":
            return fuzz.token_set_ratio(query_clean, target_clean)
        else:
            return fuzz.ratio(query_clean, target_clean)

    def _get_best_match_score(self, query: str, target: str) -> float:
        """Get the best match score using multiple fuzzy matching methods"""
        if not query or not target:
            return 0.0
        
        scores = [
            self._fuzzy_match(query, target, "ratio"),
            self._fuzzy_match(query, target, "partial_ratio"),
            self._fuzzy_match(query, target, "token_sort_ratio"),
            self._fuzzy_match(query, target, "token_set_ratio")
        ]
        
        # Return the highest score
        return max(scores)

    async def _search_single_name_in_data(self, query_name: str, columns: List[str], 
                                        data: List[Dict[str, Any]], 
                                        threshold: int) -> Tuple[str, List[MatchedRecord]]:
        """Search for a single name in the dataset"""
        
        def search_in_thread():
            matches = []
            
            for record in data:
                for column in columns:
                    if column in record and record[column]:
                        target_value = str(record[column])
                        confidence = self._get_best_match_score(query_name, target_value)
                        
                        if confidence >= threshold:
                            matched_record = MatchedRecord(
                                query_name=query_name,
                                confidence=confidence,
                                matched_column=column,
                                matched_value=target_value,
                                entity_id=record.get("Entity_LogicalId"),
                                full_record=record
                            )
                            matches.append(matched_record)
            
            # Sort by confidence score (highest first)
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches
        
        # Run the search in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        matches = await loop.run_in_executor(self.thread_pool, search_in_thread)
        
        return query_name, matches

    async def single_search(self, request: SingleSearchRequest, user_id: str) -> SingleSearchResponse:
        """Create single name search task"""
        
        # Validate task exists
        if not await self.repository.validate_task_exists(request.task_id):
            raise TaskException(f"Task {request.task_id} not found or has no data")
        
        # Get total rows count
        total_rows = await self.repository.get_task_record_count(request.task_id)
        
        # Create pending search entry
        search_data = self.clean_json({
            "task_id": request.task_id,
            "search_type": "single",
            "query_names": [request.name],
            "columns_used": request.columns,
            "threshold_used": request.threshold,
            "total_rows": total_rows,
            "status": "pending",
            "created_by": user_id
        })
        
        # Save search history with pending status
        search_id = await self.repository.save_search_history(search_data, user_id)
        
        # Add to search queue
        from app.workers.background_worker import add_search_to_queue
        await add_search_to_queue(search_id, "single", {
            "task_id": request.task_id,
            "name": request.name,
            "columns": request.columns,
            "threshold": request.threshold,
            "user_id": user_id
        })
        
        # Return immediate response with pending status
        response_data = {
            "name": request.name,
            "matched": 0.0,
            "found": False,
            "total_rows": total_rows,
            "execution_time_ms": 0,
            "matched_records": [],
            "search_id": search_id,
            "status": "pending"
        }
        response = SingleSearchResponse(**response_data)
        return response

    async def bulk_search(self, request: BulkSearchRequest, user_id: str) -> BulkSearchResponse:
        """Create bulk name search task"""
        
        # Validate task exists
        if not await self.repository.validate_task_exists(request.task_id):
            raise TaskException(f"Task {request.task_id} not found or has no data")
        
        # Validate watchlist_id if provided
        if request.watchlist_id:
            if not ObjectId.is_valid(request.watchlist_id):
                raise TaskException(f"Invalid watchlist_id format: {request.watchlist_id}")
            
            watchlist = await WatchlistRepository.get_watchlist_by_id(ObjectId(request.watchlist_id))
            if not watchlist:
                raise TaskException(f"Watchlist {request.watchlist_id} not found")
        
        # Get total rows count
        total_rows = await self.repository.get_task_record_count(request.task_id)
        
        # Create pending search entry
        search_data = self.clean_json({
            "task_id": request.task_id,
            "search_type": "bulk",
            "query_names": request.list,
            "columns_used": request.columns,
            "threshold_used": request.threshold,
            "total_rows": total_rows,
            "watchlist_id": request.watchlist_id,
            "status": "pending",
            "created_by": user_id
        })
        
        # Save search history with pending status
        search_id = await self.repository.save_search_history(search_data, user_id)
        
        # Add to search queue
        from app.workers.background_worker import add_search_to_queue
        await add_search_to_queue(search_id, "bulk", {
            "task_id": request.task_id,
            "list": request.list,
            "columns": request.columns,
            "threshold": request.threshold,
            "watchlist_id": request.watchlist_id,
            "user_id": user_id
        })
        
        # Return immediate response with pending status
        empty_results = [BulkSearchItem(
            name=name,
            matched=0.0,
            found=False,
            best_match=None
        ) for name in request.list]
        
        summary = {
            "total_searched": len(request.list),
            "total_found": 0,
            "total_above_threshold": 0,
            "average_confidence": 0.0,
            "threshold_used": request.threshold,
            "total_rows": total_rows,
            "execution_time_ms": 0,
            "status": "pending"
        }
        
        response_data = {
            "results": empty_results,
            "summary": summary,
            "search_id": search_id
        }
        response = BulkSearchResponse(**response_data)
        return response

    async def get_available_columns(self, task_id: str, user_id: Optional[str] = None) -> AvailableColumnsResponse:
        """Get available columns for a task"""
        
        # Validate task exists
        if not await self.repository.validate_task_exists(task_id):
            raise TaskException(f"Task {task_id} not found or has no data")
        
        column_data = await self.repository.get_available_columns(task_id)
        
        return AvailableColumnsResponse(
            task_id=task_id,
            columns=column_data["available_columns"],
            recommended_columns=column_data["recommended_columns"],
            total_records=column_data["total_records"]
        )

    async def get_search_history(self, user_id: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get search history for a user"""
        history_data = await self.repository.get_search_history(user_id, page, limit)
        # Clean the data to prevent JSON serialization errors
        return self.clean_json(history_data)

    async def get_search_result(self, search_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get search result by search_id"""
        result = await self.repository.get_search_result(search_id)
        if not result:
            raise TaskException(f"Search result with ID {search_id} not found")
        # Clean the data to prevent JSON serialization errors
        return self.clean_json(result)