from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from backend.app.database import Base

class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_hash = Column(String(64), nullable=False, index=True)
    branch = Column(String(50), default="main")
    message = Column(Text, nullable=False)
    author = Column(String(100), default="AI Website Builder Agent")
    changed_files = Column(JSON, nullable=True) # list of file paths modified/created
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
