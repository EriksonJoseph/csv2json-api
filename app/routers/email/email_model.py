from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"

class EmailRequest(BaseModel):
    to_emails: List[EmailStr]
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    html_body: Optional[str] = None
    priority: EmailPriority = EmailPriority.NORMAL
    send_immediately: bool = False
    scheduled_at: Optional[datetime] = None
    reply_to: Optional[EmailStr] = None
    cc_emails: Optional[List[EmailStr]] = []
    bcc_emails: Optional[List[EmailStr]] = []
    attachments: Optional[List[str]] = []
    template_data: Optional[Dict[str, Any]] = {}

class EmailResponse(BaseModel):
    id: str
    status: EmailStatus
    message: str
    created_at: datetime
    scheduled_at: Optional[datetime] = None

class EmailTemplate(BaseModel):
    name: str
    subject_template: str
    body_template: str
    html_template: Optional[str] = None
    variables: List[str] = []

class EmailTaskCreate(BaseModel):
    to_emails: List[str]
    subject: str
    body: str
    html_body: Optional[str] = None
    priority: EmailPriority = EmailPriority.NORMAL
    reply_to: Optional[str] = None
    cc_emails: Optional[List[str]] = []
    bcc_emails: Optional[List[str]] = []
    attachments: Optional[List[str]] = []
    template_data: Optional[Dict[str, Any]] = {}
    created_by: str
    scheduled_at: Optional[datetime] = None

class EmailTask(BaseModel):
    id: Optional[str] = Field(alias="_id")
    to_emails: List[str]
    subject: str
    body: str
    html_body: Optional[str] = None
    priority: EmailPriority
    status: EmailStatus
    reply_to: Optional[str] = None
    cc_emails: List[str] = []
    bcc_emails: List[str] = []
    attachments: List[str] = []
    template_data: Dict[str, Any] = {}
    created_by: str
    created_at: datetime
    updated_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EmailStats(BaseModel):
    total_emails: int
    pending_emails: int
    sent_emails: int
    failed_emails: int
    retry_emails: int