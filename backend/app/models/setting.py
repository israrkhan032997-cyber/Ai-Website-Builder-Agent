from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean
from backend.app.database import Base

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True, index=True)
    value = Column(Text, nullable=True)
    is_secret = Column(Boolean, default=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
