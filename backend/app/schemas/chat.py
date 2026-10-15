from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

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
    business_name: str
    industry: str
    description: str
    target_audience: str
    website_type: str # "single-page" | "multi-page"
    selected_pages: List[str] = Field(default_factory=list)
    design_style: str
    brand_colors: Dict[str, str] = Field(default_factory=dict)
    tech_stack: str # "react-php"
    additional_notes: Optional[str] = None

class CreateProjectFromChatRequest(BaseModel):
    collected_data: Dict[str, Any] = Field(default_factory=dict)

# Convenient aliases
ChatTurnRequest = ConversationalStepRequest
ChatTurnResponse = ConversationalStepResponse
