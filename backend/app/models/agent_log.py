from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Integer
from backend.app.database import Base

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False, index=True) # Orchestrator, Asset Agent, Design Agent, Backend Agent, Execution Agent
    step_name = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False) # started, in_progress, success, failed, awaiting_approval
    message = Column(Text, nullable=False)
    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    error_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
