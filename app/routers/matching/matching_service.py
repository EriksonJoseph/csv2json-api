from typing import List, Dict, Any, Optional, Tuple
import re
from rapidfuzz import fuzz, process
from app.routers.matching.matching_repository import MatchingRepository
from app.routers.matching.matching_model import (
    SingleSearchRequest, BulkSearchRequest, SingleSearchResponse, 
    BulkSearchResponse, BulkSearchItem, MatchedRecord, AvailableColumnsResponse
)
from app.exceptions import TaskException
import asyncio
from concurrent.futures import ThreadPoolExecutor

import math

class MatchingService:
    def clean_json(self, obj):
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

    def __init__(self):
        self.repository = MatchingRepository()
        # Thread pool for CPU-bound fuzzy matching operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

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
                                        threshold: int) -> List[MatchedRecord]:
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
        
        return matches

    async def single_search(self, request: SingleSearchRequest, user_id: str) -> SingleSearchResponse:
        """Perform single name search"""
        
        # Validate task exists
        if not await self.repository.validate_task_exists(request.task_id):
            raise TaskException(f"Task {request.task_id} not found or has no data")
        
        # Get CSV data for the specified columns
        data = await self.repository.search_in_columns(
            task_id=request.task_id,
            columns=request.columns
        )
        
        if not data:
            raise TaskException("No data found for the specified task")
        
        # Perform search
        matched_records = await self._search_single_name_in_data(
            query_name=request.name,
            columns=request.columns,
            data=data,
            threshold=request.threshold
        )
        
        # Prepare response
        best_match_score = matched_records[0].confidence if matched_records else 0.0
        found = len(matched_records) > 0
        
        # Save search history
        await self.repository.save_search_history({
            "search_id": f"single_{request.task_id}_{hash(request.name)}",
            "task_id": request.task_id,
            "search_type": "single",
            "query_names": [request.name],
            "columns_used": request.columns,
            "threshold_used": request.threshold,
            "results_found": len(matched_records),
            "total_searched": 1,
            "created_by": user_id
        })
        
        response = SingleSearchResponse(
            name=request.name,
            matched=best_match_score,
            found=found,
            matched_records=matched_records
        )
        return self.clean_json(response.dict())

    async def bulk_search(self, request: BulkSearchRequest, user_id: str) -> BulkSearchResponse:
        """Perform bulk name search"""
        
        # Validate task exists
        if not await self.repository.validate_task_exists(request.task_id):
            raise TaskException(f"Task {request.task_id} not found or has no data")
        
        # Get CSV data for the specified columns
        data = await self.repository.search_in_columns(
            task_id=request.task_id,
            columns=request.columns
        )
        
        if not data:
            raise TaskException("No data found for the specified task")
        
        results = []
        total_found = 0
        total_above_threshold = 0
        
        # Process each name in the list
        for name in request.list:
            matched_records = await self._search_single_name_in_data(
                query_name=name,
                columns=request.columns,
                data=data,
                threshold=request.threshold
            )
            
            best_match_score = matched_records[0].confidence if matched_records else 0.0
            found = len(matched_records) > 0
            best_match = matched_records[0] if matched_records else None
            
            if found:
                total_found += 1
            if best_match_score >= request.threshold:
                total_above_threshold += 1
            
            results.append(BulkSearchItem(
                name=name,
                matched=best_match_score,
                found=found,
                best_match=best_match
            ))
        
        # Prepare summary
        summary = {
            "total_searched": len(request.list),
            "total_found": total_found,
            "total_above_threshold": total_above_threshold,
            "average_confidence": sum(r.matched for r in results) / len(results) if results else 0,
            "threshold_used": request.threshold
        }
        
        # Save search history
        await self.repository.save_search_history({
            "search_id": f"bulk_{request.task_id}_{hash(str(request.list))}",
            "task_id": request.task_id,
            "search_type": "bulk",
            "query_names": request.list,
            "columns_used": request.columns,
            "threshold_used": request.threshold,
            "results_found": total_found,
            "total_searched": len(request.list),
            "created_by": user_id
        })
        
        response = BulkSearchResponse(
            results=results,
            summary=summary
        )
        return self.clean_json(response.dict())

    async def get_available_columns(self, task_id: str) -> AvailableColumnsResponse:
        """Get available columns for a task"""
        
        # Validate task exists
        if not await self.repository.validate_task_exists(task_id):
            raise TaskException(f"Task {task_id} not found or has no data")
        
        column_data = await self.repository.get_available_columns(task_id)
        
        return AvailableColumnsResponse(
            task_id=task_id,
            available_columns=column_data["available_columns"],
            recommended_columns=column_data["recommended_columns"],
            total_records=column_data["total_records"]
        )

    async def get_search_history(self, user_id: str, page: int = 1, limit: int = 10):
        """Get search history for a user"""
        return await self.repository.get_search_history(user_id, page, limit)