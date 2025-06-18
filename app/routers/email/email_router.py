from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.dependencies.auth import get_current_user, require_roles
from app.routers.email.email_model import (
    EmailRequest, EmailResponse, EmailStatus, EmailStats, EmailTaskCreate
)
from app.routers.email.email_service import EmailService
from app.routers.user.user_model import User
from app.routers.auth.auth_model import UserRole

router = APIRouter(prefix="/email", tags=["email"])

@router.post("/send", response_model=EmailResponse)
async def send_email(
    email_request: EmailRequest,
    current_user: User = Depends(get_current_user)
):
    """Send email (queued for background processing)"""
    try:
        email_service = EmailService()
        
        # Create email task
        task_data = EmailTaskCreate(
            to_emails=[str(email) for email in email_request.to_emails],
            subject=email_request.subject,
            body=email_request.body,
            html_body=email_request.html_body,
            priority=email_request.priority,
            reply_to=str(email_request.reply_to) if email_request.reply_to else None,
            cc_emails=[str(email) for email in email_request.cc_emails] if email_request.cc_emails else [],
            bcc_emails=[str(email) for email in email_request.bcc_emails] if email_request.bcc_emails else [],
            attachments=email_request.attachments or [],
            template_data=email_request.template_data or {},
            created_by=current_user.username,
            scheduled_at=email_request.scheduled_at
        )
        
        task_id = await email_service.create_email_task(task_data)
        
        # If send_immediately is True, process immediately
        if email_request.send_immediately:
            from app.workers.background_worker import add_email_to_queue
            await add_email_to_queue(task_id)
        
        return EmailResponse(
            id=task_id,
            status=EmailStatus.PENDING,
            message="Email queued for sending",
            created_at=datetime.now(),
            scheduled_at=email_request.scheduled_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue email: {str(e)}"
        )

@router.post("/send-now", response_model=EmailResponse)
async def send_email_immediately(
    email_request: EmailRequest,
    current_user: User = Depends(get_current_user)
):
    """Send email immediately (bypass queue)"""
    try:
        email_service = EmailService()
        
        success = await email_service.send_immediate_email(
            to_emails=[str(email) for email in email_request.to_emails],
            subject=email_request.subject,
            body=email_request.body,
            html_body=email_request.html_body,
            created_by=current_user.username
        )
        
        if success:
            return EmailResponse(
                id="immediate",
                status=EmailStatus.SENT,
                message="Email sent successfully",
                created_at=datetime.now()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email immediately"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email immediately: {str(e)}"
        )

@router.get("/tasks", response_model=List[dict])
async def get_user_email_tasks(
    status_filter: Optional[EmailStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get email tasks for current user"""
    try:
        email_service = EmailService()
        
        tasks = await email_service.get_user_email_tasks(
            user_id=current_user.username,
            status=status_filter,
            limit=limit,
            offset=offset
        )
        
        return tasks
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email tasks: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=dict)
async def get_email_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific email task"""
    try:
        email_service = EmailService()
        
        task = await email_service.get_email_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email task not found"
            )
        
        # Check if user owns this task or is admin
        if task["created_by"] != current_user.username and UserRole.ADMIN not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email task: {str(e)}"
        )

@router.delete("/tasks/{task_id}")
async def delete_email_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete email task"""
    try:
        email_service = EmailService()
        
        # Get task to check ownership
        task = await email_service.get_email_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email task not found"
            )
        
        # Check if user owns this task or is admin
        if task["created_by"] != current_user.username and UserRole.ADMIN not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = await email_service.delete_email_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete email task"
            )
        
        return {"message": "Email task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete email task: {str(e)}"
        )

@router.get("/stats", response_model=EmailStats)
async def get_email_stats(
    current_user: User = Depends(get_current_user)
):
    """Get email statistics for current user"""
    try:
        email_service = EmailService()
        
        stats = await email_service.get_email_stats(current_user.username)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email stats: {str(e)}"
        )

@router.get("/stats/admin", response_model=EmailStats)
async def get_admin_email_stats(
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Get email statistics for all users (admin only)"""
    try:
        email_service = EmailService()
        
        stats = await email_service.get_email_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email stats: {str(e)}"
        )

@router.post("/retry/{task_id}")
async def retry_email_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Retry failed email task"""
    try:
        email_service = EmailService()
        
        # Get task to check ownership and status
        task = await email_service.get_email_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email task not found"
            )
        
        # Check if user owns this task or is admin
        if task["created_by"] != current_user.username and UserRole.ADMIN not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if task can be retried
        if task["status"] not in ["failed", "retry"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task cannot be retried"
            )
        
        # Add to email queue for retry
        from app.workers.background_worker import add_email_to_queue
        await add_email_to_queue(task_id)
        
        return {"message": "Email task queued for retry"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry email task: {str(e)}"
        )