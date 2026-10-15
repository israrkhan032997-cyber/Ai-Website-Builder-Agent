from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
from backend.app.schemas.project import normalize_and_validate_subdomain

class SubdomainCheckRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=63, description="Desired customer subdomain slug")
    project_id: Optional[str] = None

    @field_validator("slug", mode="before")
    @classmethod
    def clean_slug(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("slug must be a string.")
        return v.strip().lower()

class SubdomainCheckResponse(BaseModel):
    available: bool
    slug: str
    message: str
    suggested_alternatives: List[str] = Field(default_factory=list)
    preview_url: Optional[str] = None

class SubdomainReserveRequest(BaseModel):
    slug: str = Field(..., min_length=3, max_length=63, description="RFC-1035 compliant subdomain slug")

    @field_validator("slug", mode="before")
    @classmethod
    def validate_slug(cls, v: Any) -> str:
        res = normalize_and_validate_subdomain(v)
        if not res:
            raise ValueError("Subdomain slug cannot be empty.")
        return res

class SubdomainAssignRequest(BaseModel):
    project_id: str
    subdomain: str

    @field_validator("subdomain", mode="before")
    @classmethod
    def validate_subdomain(cls, v: Any) -> str:
        res = normalize_and_validate_subdomain(v)
        if not res:
            raise ValueError("Subdomain cannot be empty.")
        return res

class SubdomainAssignResponse(BaseModel):
    project_id: str
    subdomain: str
    full_url: str
    message: str
