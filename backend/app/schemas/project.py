from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.agent import WebsitePlan, AssetManifest

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Business name")
    industry: str = Field(..., min_length=2, max_length=100, description="Industry or business sector")
    description: str = Field(..., min_length=10, description="Description of the business, services, and value proposition")
    target_audience: Optional[str] = Field(None, max_length=255, description="Target demographic or customer persona")
    style: Optional[str] = Field("Modern & Clean", max_length=100, description="Desired visual design style")
    primary_color: Optional[str] = Field("#2563eb", pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    secondary_color: Optional[str] = Field("#0f172a", pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    accent_color: Optional[str] = Field("#38bdf8", pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    logo_url: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    target_audience: Optional[str] = None
    style: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    logo_url: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    industry: str
    description: str
    target_audience: Optional[str]
    style: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    accent_color: Optional[str]
    logo_url: Optional[str]
    status: str
    current_agent: Optional[str]
    current_step: Optional[str]
    progress_percentage: str
    active_checkpoint_hash: Optional[str]
    deployment_status: str
    deployment_provider: Optional[str]
    deployment_url: Optional[str]
    live_preview_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectDetailResponse(ProjectResponse):
    website_plan: Optional[Dict[str, Any]] = None
    asset_manifest: Optional[Dict[str, Any]] = None
    submissions_count: int = 0
    checkpoints_count: int = 0
    pending_approvals_count: int = 0

class NaturalLanguageEditRequest(BaseModel):
    instruction: str = Field(..., min_length=3, description="Natural language instructions describing requested changes")
    section_id: Optional[str] = Field(None, description="Optional target section ID (e.g., hero, features, contact)")
