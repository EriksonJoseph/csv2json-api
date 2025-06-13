#!/usr/bin/env python3
"""
Simple test script to verify the background search functionality works correctly.
"""

import asyncio
import time
from app.routers.matching.matching_service import MatchingService
from app.routers.matching.matching_model import SingleSearchRequest, BulkSearchRequest
from app.routers.matching.matching_repository import MatchingRepository
from app.workers.background_worker import start_worker, load_pending_searches

async def test_search_background():
    """Test that search operations are properly queued and processed."""
    
    print("🔧 Testing background search functionality...")
    
    # Start the workers
    await start_worker()
    await load_pending_searches()
    
    matching_service = MatchingService()
    matching_repo = MatchingRepository()
    
    # Test single search (with fake data for demo)
    try:
        single_request = SingleSearchRequest(
            task_id="test_task_id",
            name="test_name",
            threshold=70,
            columns=["test_column"]
        )
        
        # This should create a pending search entry and queue it
        response = await matching_service.single_search(single_request, "test_user")
        
        print(f"✅ Single search queued successfully:")
        print(f"   - Search ID: {response.search_id}")
        print(f"   - Status: {response.status}")
        print(f"   - Name: {response.name}")
        
        # Check if search was saved with pending status
        search_result = await matching_repo.get_search_result(response.search_id)
        if search_result and search_result.get("status") == "pending":
            print("✅ Search properly saved with pending status")
        else:
            print("❌ Search not saved or status incorrect")
            
    except Exception as e:
        print(f"❌ Single search test failed: {e}")
    
    # Test bulk search
    try:
        bulk_request = BulkSearchRequest(
            task_id="test_task_id",
            threshold=70,
            columns=["test_column"],
            list=["name1", "name2", "name3"]
        )
        
        response = await matching_service.bulk_search(bulk_request, "test_user")
        
        print(f"✅ Bulk search queued successfully:")
        print(f"   - Search ID: {response.search_id}")
        print(f"   - Results count: {len(response.results)}")
        print(f"   - Summary: {response.summary}")
        
    except Exception as e:
        print(f"❌ Bulk search test failed: {e}")
    
    print("🎉 Background search functionality test completed!")

if __name__ == "__main__":
    asyncio.run(test_search_background())