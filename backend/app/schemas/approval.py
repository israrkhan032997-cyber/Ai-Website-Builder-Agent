from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.app.schemas.project import normalize_and_validate_custom_domain

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
    custom_domain: Optional[str] = Field(None, description="Optional verified custom domain e.g. 'pepsi.com'")
    confirm: bool = True

    @field_validator("provider", mode="before")
    @classmethod
    def validate_provider(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("provider must be a string.")
        p = v.strip().lower()
        if p not in ("local", "netlify", "vercel"):
            raise ValueError(f"Unsupported deployment provider '{v}'. Must be 'local', 'netlify', or 'vercel'.")
        return p

    @field_validator("custom_domain", mode="before")
    @classmethod
    def validate_custom_domain(cls, v: Any) -> Optional[str]:
        return normalize_and_validate_custom_domain(v)

class DeploymentResponse(BaseModel):
    project_id: str
    provider: str
    status: str # preparing, deploying, deployed, failed
    deployment_url: Optional[str]
    live_preview_url: Optional[str]
    message: str
    deployed_at: Optional[datetime] = None
