from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CommandApprovalResponse(BaseModel):
    id: int
    project_id: str
    command: str
    working_directory: str
    purpose: str
    risk_level: str
    status: str
    execution_output: Optional[str]
    created_at: datetime
    decided_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class CommandApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = None

class DeploymentApprovalRequest(BaseModel):
    provider: str = Field("local", description="Deployment provider: 'local', 'netlify', or 'vercel'")
    custom_domain: Optional[str] = None
    confirm: bool = True

class DeploymentResponse(BaseModel):
    project_id: str
    provider: str
    status: str # preparing, deploying, deployed, failed
    deployment_url: Optional[str]
    live_preview_url: Optional[str]
    message: str
    deployed_at: Optional[datetime] = None
