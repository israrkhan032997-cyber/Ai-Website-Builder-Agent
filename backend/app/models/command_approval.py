from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from backend.app.database import Base

class CommandApproval(Base):
    __tablename__ = "command_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    command = Column(Text, nullable=False)
    working_directory = Column(String(255), nullable=False)
    purpose = Column(String(255), nullable=False)
    risk_level = Column(String(20), default="low") # low, medium, high
    status = Column(String(30), default="pending") # pending, approved, rejected, executed, failed
    execution_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    decided_at = Column(DateTime, nullable=True)
