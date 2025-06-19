#!/usr/bin/env python3
"""
Debug script to check email tasks in database
"""
import asyncio
from app.database import get_collection
from app.utils.serializers import list_serial
from datetime import datetime

async def check_email_tasks():
    try:
        email_tasks_collection = await get_collection("email_tasks")
        
        # Get recent email tasks
        tasks = await email_tasks_collection.find({}).sort("created_at", -1).limit(10).to_list(length=10)
        
        print(f"Found {len(tasks)} recent email tasks:")
        print("-" * 50)
        
        for task in tasks:
            print(f"Task ID: {task['_id']}")
            print(f"To: {task.get('to_emails', [])}")
            print(f"Subject: {task.get('subject', '')}")
            print(f"Status: {task.get('status', 'unknown')}")
            print(f"Created: {task.get('created_at', 'unknown')}")
            print(f"Sent: {task.get('sent_at', 'not sent')}")
            print(f"Error: {task.get('error_message', 'none')}")
            print(f"Retry Count: {task.get('retry_count', 0)}")
            print("-" * 30)
        
    except Exception as e:
        print(f"Error checking email tasks: {e}")

if __name__ == "__main__":
    asyncio.run(check_email_tasks())