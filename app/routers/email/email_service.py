import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import logging
from jinja2 import Template

from app.config import get_settings
from app.routers.email.email_model import (
    EmailTaskCreate, EmailStatus, EmailPriority, EmailStats, EmailTask
)
from app.routers.email.email_repository import EmailRepository

logger = logging.getLogger('email_service')

class EmailService:
    def __init__(self):
        self.settings = get_settings()
        self.repository = EmailRepository()

    async def send_email_task(self, task_data: Dict[str, Any]) -> bool:
        """Send email from task data"""
        try:
            task_id = task_data["_id"]
            logger.info(f"📧 [EMAIL-{task_id}] Starting email send process")
            
            # Update status to processing
            await self.repository.update_email_task_status(
                task_id, EmailStatus.PROCESSING
            )
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.settings.SMTP_FROM_NAME} <{self.settings.SMTP_FROM_EMAIL}>"
            msg['To'] = ", ".join(task_data["to_emails"])
            msg['Subject'] = task_data["subject"]
            
            if task_data.get("reply_to"):
                msg['Reply-To'] = task_data["reply_to"]
            
            if task_data.get("cc_emails"):
                msg['Cc'] = ", ".join(task_data["cc_emails"])
            
            # Add text part
            text_part = MIMEText(task_data["body"], 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if task_data.get("html_body"):
                html_part = MIMEText(task_data["html_body"], 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments if any
            if task_data.get("attachments"):
                for file_path in task_data["attachments"]:
                    if os.path.exists(file_path):
                        await self._add_attachment(msg, file_path)
            
            # Send email
            success = await self._send_smtp_email(msg, task_data)
            
            if success:
                # Update status to sent
                await self.repository.update_email_task_status(
                    task_id, EmailStatus.SENT, sent_at=datetime.now()
                )
                logger.info(f"📧 [EMAIL-{task_id}] ✅ Email sent successfully")
                return True
            else:
                # Handle failure
                await self._handle_email_failure(task_id, "SMTP send failed")
                return False
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"📧 [EMAIL-{task_data['_id']}] ❌ Error sending email: {error_message}")
            await self._handle_email_failure(task_data["_id"], error_message)
            return False

    async def _send_smtp_email(self, msg: MIMEMultipart, task_data: Dict[str, Any]) -> bool:
        """Send email via SMTP"""
        try:
            # Validate SMTP configuration
            if not all([
                self.settings.SMTP_HOST,
                self.settings.SMTP_USERNAME,
                self.settings.SMTP_PASSWORD,
                self.settings.SMTP_FROM_EMAIL
            ]):
                raise Exception("SMTP configuration is incomplete")
            
            # Create SMTP connection
            server = smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT)
            
            if self.settings.SMTP_USE_TLS:
                server.starttls()
            
            server.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
            
            # Prepare recipient list
            recipients = task_data["to_emails"][:]
            if task_data.get("cc_emails"):
                recipients.extend(task_data["cc_emails"])
            if task_data.get("bcc_emails"):
                recipients.extend(task_data["bcc_emails"])
            
            # Send email
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False

    async def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add attachment to email"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {str(e)}")

    async def _handle_email_failure(self, task_id: str, error_message: str):
        """Handle email sending failure"""
        try:
            task = await self.repository.get_email_task_by_id(task_id)
            if not task:
                return
            
            retry_count = task.get("retry_count", 0)
            max_retries = task.get("max_retries", 3)
            
            if retry_count < max_retries:
                # Increment retry count and set status to retry
                await self.repository.increment_retry_count(task_id)
                await self.repository.update_email_task_status(
                    task_id, EmailStatus.RETRY, error_message
                )
                logger.info(f"📧 [EMAIL-{task_id}] 🔄 Marked for retry ({retry_count + 1}/{max_retries})")
            else:
                # Max retries reached, mark as failed
                await self.repository.update_email_task_status(
                    task_id, EmailStatus.FAILED, error_message
                )
                logger.error(f"📧 [EMAIL-{task_id}] ❌ Max retries reached, marked as failed")
                
        except Exception as e:
            logger.error(f"Error handling email failure for {task_id}: {str(e)}")

    async def create_email_task(self, email_data: EmailTaskCreate) -> str:
        """Create a new email task"""
        try:
            task_id = await self.repository.create_email_task(email_data)
            logger.info(f"📧 Created email task {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error creating email task: {str(e)}")
            raise

    async def get_email_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get email task by ID"""
        return await self.repository.get_email_task_by_id(task_id)

    async def get_user_email_tasks(
        self, 
        user_id: str, 
        status: Optional[EmailStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get email tasks for a user"""
        return await self.repository.get_email_tasks_by_user(
            user_id, status, limit, offset
        )

    async def get_email_stats(self, user_id: Optional[str] = None) -> EmailStats:
        """Get email statistics"""
        return await self.repository.get_email_stats(user_id)

    async def delete_email_task(self, task_id: str) -> bool:
        """Delete email task"""
        return await self.repository.delete_email_task(task_id)

    def render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render email template with data"""
        try:
            jinja_template = Template(template)
            return jinja_template.render(**data)
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return template

    async def send_immediate_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        created_by: str = "system"
    ) -> bool:
        """Send email immediately without queuing"""
        try:
            logger.info(f"Creating email task for immediate sending to: {to_emails}")
            
            task_data = EmailTaskCreate(
                to_emails=to_emails,
                subject=subject,
                body=body,
                html_body=html_body,
                priority=EmailPriority.HIGH,
                created_by=created_by
            )
            
            logger.info(f"Email task data created with subject: {subject}")
            
            task_id = await self.create_email_task(task_data)
            logger.info(f"Email task created with ID: {task_id}")
            
            task = await self.get_email_task(task_id)
            logger.info(f"Retrieved email task: {task is not None}")
            
            if task:
                logger.info(f"Sending email task: {task_id}")
                result = await self.send_email_task(task)
                logger.info(f"Email send result for task {task_id}: {result}")
                return result
            
            logger.error(f"Failed to retrieve email task with ID: {task_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending immediate email: {str(e)}")
            return False

    async def get_pending_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pending email tasks for background processing"""
        return await self.repository.get_pending_email_tasks(limit)

    async def get_failed_tasks_for_retry(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get failed tasks that can be retried"""
        return await self.repository.get_failed_email_tasks(limit)