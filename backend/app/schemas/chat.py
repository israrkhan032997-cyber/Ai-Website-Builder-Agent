from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from backend.app.schemas.project import (
    TechStackType,
    WebsiteType,
    SUPPORTED_TECH_STACKS,
    SUPPORTED_WEBSITE_TYPES,
    normalize_and_validate_page_slugs,
)

class ChatMessageCreate(BaseModel):
    sender: str = Field(..., pattern="^(user|assistant|system)$")
    step: Optional[str] = None
    content: str = Field(..., min_length=1)
    message_metadata: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    id: int
    project_id: str
    sender: str
    step: Optional[str] = None
    content: str
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationalStepRequest(BaseModel):
    project_id: Optional[str] = None
    user_message: str
    current_step: Optional[str] = "business_name"
    collected_data: Dict[str, Any] = Field(default_factory=dict)

class ConversationalStepResponse(BaseModel):
    assistant_message: str
    next_step: str # "business_name", "industry", "description", "target_audience", "website_type", "page_selection", "design_preferences", "technology", "review", "ready_to_generate"
    suggested_options: List[str] = Field(default_factory=list)
    updated_data: Dict[str, Any] = Field(default_factory=dict)
    is_complete: bool = False
    review_summary: Optional[Dict[str, Any]] = None
    structured_specification: Optional[Dict[str, Any]] = None

class RequirementsReview(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=150)
    industry: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10)
    target_audience: str
    website_type: WebsiteType = Field("single-page", description="'single-page' or 'multi-page'")
    selected_pages: List[str] = Field(default_factory=list)
    design_style: str = "Modern & Clean"
    brand_colors: Dict[str, str] = Field(default_factory=dict)
    tech_stack: TechStackType = Field("react", description="Supported architecture: 'react'")
    additional_notes: Optional[str] = None

    @field_validator("tech_stack", mode="before")
    @classmethod
    def validate_tech_stack(cls, v: Any) -> str:
        if v is None:
            return "react"
        if not isinstance(v, str):
            raise ValueError("tech_stack must be a string.")
        v_clean = v.strip().lower()
        if v_clean not in SUPPORTED_TECH_STACKS:
            raise ValueError(
                f"Unsupported tech_stack '{v}'. The required architecture is 'react' (Pure React SPA)."
            )
        return v_clean

    @field_validator("website_type", mode="before")
    @classmethod
    def validate_website_type(cls, v: Any) -> str:
        if v is None:
            return "single-page"
        if not isinstance(v, str):
            raise ValueError("website_type must be a string.")
        v_clean = v.strip().lower()
        if v_clean not in SUPPORTED_WEBSITE_TYPES:
            raise ValueError(
                f"Invalid website_type '{v}'. Must be either 'single-page' or 'multi-page'."
            )
        return v_clean

    @field_validator("selected_pages", mode="before")
    @classmethod
    def validate_selected_pages(cls, v: Any) -> List[str]:
        pages = normalize_and_validate_page_slugs(v)
        return pages or []

    @model_validator(mode="after")
    def validate_consistency(self) -> "RequirementsReview":
        if self.website_type == "single-page":
            if not self.selected_pages:
                self.selected_pages = ["home"]
            elif self.selected_pages != ["home"]:
                raise ValueError(
                    "For a 'single-page' website, selected_pages must only contain ['home']."
                )
        elif self.website_type == "multi-page":
            if len(self.selected_pages) < 2:
                raise ValueError(
                    "For a 'multi-page' website, selected_pages must contain at least 2 distinct pages."
                )
            if "home" not in self.selected_pages:
                raise ValueError(
                    "For a 'multi-page' website, selected_pages must include 'home'."
                )
        return self

class CreateProjectFromChatRequest(BaseModel):
    collected_data: Dict[str, Any] = Field(default_factory=dict)

# Convenient aliases
ChatTurnRequest = ConversationalStepRequest
ChatTurnResponse = ConversationalStepResponse
