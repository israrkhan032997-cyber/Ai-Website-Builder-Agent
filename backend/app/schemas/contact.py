from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

class ContactSubmissionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    subject: Optional[str] = Field(None, max_length=200)
    message: str = Field(..., min_length=5, max_length=5000)
    # Honeypot field for anti-bot validation; should be left empty by legitimate users
    website_hp: Optional[str] = Field(None, description="Anti-spam honeypot")

class ContactSubmissionResponse(BaseModel):
    id: int
    project_id: str
    name: str
    email: str
    phone: Optional[str]
    subject: Optional[str]
    message: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ContactSubmissionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(unread|read|archived)$")
