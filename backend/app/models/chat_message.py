from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from backend.app.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False) # "user", "assistant", "system"
    step = Column(String(50), nullable=True) # "business_name", "industry", "description", "target_audience", "website_type", "page_selection", "design_preferences", "technology", "review", "modification"
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True) # options, chips, inferred_data, edit_action
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
