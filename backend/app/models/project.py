from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from backend.app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    target_audience = Column(String(255), nullable=True)
    style = Column(String(100), nullable=True, default="Modern & Clean")
    primary_color = Column(String(50), nullable=True, default="#2563eb")
    secondary_color = Column(String(50), nullable=True, default="#0f172a")
    accent_color = Column(String(50), nullable=True, default="#38bdf8")
    logo_url = Column(String(500), nullable=True)

    # Website Architecture: single-page or multi-page
    website_type = Column(String(30), nullable=False, default="single-page") # "single-page" | "multi-page"
    selected_pages = Column(JSON, nullable=True) # list of page slugs e.g. ["home", "about", "services", "contact"]
    tech_stack = Column(String(50), nullable=False, default="react") # Pure React SPA

    # Multi-tenant Subdomain Routing
    subdomain = Column(String(100), unique=True, index=True, nullable=True) # e.g. "pepsi", "arcline"
    custom_domain = Column(String(255), nullable=True)

    # Workflow & lifecycle status: draft, planning, generating_assets, generating_design, generating_backend, validating, awaiting_approval, ready, failed
    status = Column(String(50), nullable=False, default="draft")
    current_agent = Column(String(50), nullable=True)
    current_step = Column(String(100), nullable=True)
    progress_percentage = Column(String(10), nullable=False, default="0%")

    # Specs and generated output
    website_plan = Column(JSON, nullable=True)
    asset_manifest = Column(JSON, nullable=True)
    requirements_spec = Column(JSON, nullable=True) # Full smart requirement analysis specification
    active_checkpoint_hash = Column(String(64), nullable=True)

    # Deployment
    deployment_status = Column(String(50), nullable=False, default="unassigned") # unassigned, preparing, deployed, failed
    deployment_provider = Column(String(50), nullable=True)
    deployment_url = Column(String(500), nullable=True)
    live_preview_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
