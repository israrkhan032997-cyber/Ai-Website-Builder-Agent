from typing import Optional, List
from pydantic import BaseModel, Field

class SubdomainCheckRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=63)
    project_id: Optional[str] = None

class SubdomainCheckResponse(BaseModel):
    available: bool
    slug: str
    message: str
    suggested_alternatives: List[str] = Field(default_factory=list)
    preview_url: Optional[str] = None

class SubdomainReserveRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=63)

class SubdomainAssignRequest(BaseModel):
    project_id: str
    subdomain: str

class SubdomainAssignResponse(BaseModel):
    project_id: str
    subdomain: str
    full_url: str
    message: str
