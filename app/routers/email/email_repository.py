from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.database import get_collection
from app.routers.email.email_model import EmailTask, EmailTaskCreate, EmailStatus, EmailPriority, EmailStats
import logging

logger = logging.getLogger(__name__)

class EmailRepository:
    
    async def create_email_task(self, email_data: EmailTaskCreate) -> str:
        """Create a new email task"""
        try:
            collection = await get_collection("email_tasks")
            
            now = datetime.now()
            task_data = {
                "to_emails": email_data.to_emails,
                "subject": email_data.subject,
                "body": email_data.body,
                "html_body": email_data.html_body,
                "priority": email_data.priority.value,
                "status": EmailStatus.PENDING.value,
                "reply_to": email_data.reply_to,
                "cc_emails": email_data.cc_emails or [],
                "bcc_emails": email_data.bcc_emails or [],
                "attachments": email_data.attachments or [],
                "template_data": email_data.template_data or {},
                "created_by": email_data.created_by,
                "created_at": now,
                "updated_at": now,
                "scheduled_at": email_data.scheduled_at,
                "sent_at": None,
                "error_message": None,
                "retry_count": 0,
                "max_retries": 3
            }
            
            result = await collection.insert_one(task_data)
            logger.info(f"Created email task with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error creating email task: {str(e)}")
            raise

    async def get_email_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get email task by ID"""
        try:
            collection = await get_collection("email_tasks")
            
            task = await collection.find_one({"_id": ObjectId(task_id)})
            if task:
                task["_id"] = str(task["_id"])
            
            return task
            
        except Exception as e:
            logger.error(f"Error getting email task {task_id}: {str(e)}")
            raise

    async def update_email_task_status(
        self, 
        task_id: str, 
        status: EmailStatus, 
        error_message: Optional[str] = None,
        sent_at: Optional[datetime] = None
    ) -> bool:
        """Update email task status"""
        try:
            collection = await get_collection("email_tasks")
            
            update_data = {
                "status": status.value,
                "updated_at": datetime.now()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            if sent_at:
                update_data["sent_at"] = sent_at
            
            result = await collection.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating email task status {task_id}: {str(e)}")
            raise

    async def increment_retry_count(self, task_id: str) -> bool:
        """Increment retry count for email task"""
        try:
            collection = await get_collection("email_tasks")
            
            result = await collection.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$inc": {"retry_count": 1},
                    "$set": {"updated_at": datetime.now()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error incrementing retry count for task {task_id}: {str(e)}")
            raise

    async def get_pending_email_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pending email tasks"""
        try:
            collection = await get_collection("email_tasks")
            
            # Get tasks that are pending or retry AND (scheduled for now/past OR not scheduled) AND not already sent
            now = datetime.now()
            query = {
                "$and": [
                    {
                        "$or": [
                            {"status": EmailStatus.PENDING.value},
                            {"status": EmailStatus.RETRY.value}
                        ]
                    },
                    {
                        "$or": [
                            {"scheduled_at": {"$lte": now}},
                            {"scheduled_at": None}
                        ]
                    },
                    {
                        "sent_at": None  # Only get emails that haven't been sent yet
                    }
                ]
            }
            
            cursor = collection.find(query).sort([
                ("priority", -1),  # High priority first
                ("created_at", 1)  # Older tasks first
            ]).limit(limit)
            
            tasks = []
            async for task in cursor:
                task["_id"] = str(task["_id"])
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting pending email tasks: {str(e)}")
            raise

    async def get_email_tasks_by_user(
        self, 
        user_id: str, 
        status: Optional[EmailStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get email tasks by user"""
        try:
            collection = await get_collection("email_tasks")
            
            query = {"created_by": user_id}
            if status:
                query["status"] = status.value
            
            cursor = collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
            
            tasks = []
            async for task in cursor:
                task["_id"] = str(task["_id"])
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting email tasks for user {user_id}: {str(e)}")
            raise

    async def get_email_stats(self, user_id: Optional[str] = None) -> EmailStats:
        """Get email statistics"""
        try:
            collection = await get_collection("email_tasks")
            
            base_query = {}
            if user_id:
                base_query["created_by"] = user_id
            
            # Get counts for each status
            pipeline = [
                {"$match": base_query},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            status_counts = {}
            
            async for result in cursor:
                status_counts[result["_id"]] = result["count"]
            
            return EmailStats(
                total_emails=sum(status_counts.values()),
                pending_emails=status_counts.get(EmailStatus.PENDING.value, 0),
                sent_emails=status_counts.get(EmailStatus.SENT.value, 0),
                failed_emails=status_counts.get(EmailStatus.FAILED.value, 0),
                retry_emails=status_counts.get(EmailStatus.RETRY.value, 0)
            )
            
        except Exception as e:
            logger.error(f"Error getting email stats: {str(e)}")
            raise

    async def delete_email_task(self, task_id: str) -> bool:
        """Delete email task"""
        try:
            collection = await get_collection("email_tasks")
            
            result = await collection.delete_one({"_id": ObjectId(task_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting email task {task_id}: {str(e)}")
            raise

    async def get_failed_email_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get failed email tasks that can be retried"""
        try:
            collection = await get_collection("email_tasks")
            
            query = {
                "status": EmailStatus.FAILED.value,
                "$expr": {"$lt": ["$retry_count", "$max_retries"]}
            }
            
            cursor = collection.find(query).sort("updated_at", 1).limit(limit)
            
            tasks = []
            async for task in cursor:
                task["_id"] = str(task["_id"])
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting failed email tasks: {str(e)}")
            raise