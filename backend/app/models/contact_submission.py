from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from backend.app.database import Base

class ContactSubmission(Base):
    __tablename__ = "contact_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    subject = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(30), default="unread") # unread, read, archived
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
