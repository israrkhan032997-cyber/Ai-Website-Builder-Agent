import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal, Set
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from backend.app.schemas.agent import WebsitePlan, AssetManifest

# ---------------------------------------------------------------------------
# Supported Architectural Constants and Types
# ---------------------------------------------------------------------------

SUPPORTED_TECH_STACKS: tuple[str, ...] = ("react-php", "html-tailwind-php")
TechStackType = Literal["react-php", "html-tailwind-php"]

SUPPORTED_WEBSITE_TYPES: tuple[str, ...] = ("single-page", "multi-page")
WebsiteType = Literal["single-page", "multi-page"]

SUPPORTED_PAGE_SLUGS: Set[str] = {
    "home",
    "about",
    "about-us",
    "services",
    "products",
    "portfolio",
    "projects",
    "gallery",
    "pricing",
    "testimonials",
    "blog",
    "faq",
    "contact",
    "contact-us",
    "careers",
    "team",
}

PAGE_SLUG_ALIASES: Dict[str, str] = {
    "about-us": "about",
    "contact-us": "contact",
    "projects": "portfolio",
}

RESERVED_SUBDOMAINS: Set[str] = {
    "admin", "api", "app", "dashboard", "dev", "staging", "mail", "ftp",
    "smtp", "pop", "status", "test", "demo", "help", "support", "billing",
    "root", "localhost", "preview", "assets", "static", "login", "register",
    "www", "public", "internal", "gateway", "backend", "frontend", "prod",
    "production", "site", "sites", "auth", "account", "settings", "docs"
}

# RFC-1035 compliant hostname slug regex (3-63 characters, lowercase letters, digits, hyphens)
SUBDOMAIN_REGEX = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")

# FQDN custom domain regex (e.g. example.com, shop.example.co.uk)
CUSTOM_DOMAIN_REGEX = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)

# Section ID regex (alphanumeric, hyphens, underscores, 2-50 characters)
SECTION_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{2,50}$")

# Page slug regex
PAGE_SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Helper Normalizers & Validators
# ---------------------------------------------------------------------------

def normalize_and_validate_subdomain(v: Any) -> Optional[str]:
    """Validates and normalizes RFC-1035 subdomain slugs."""
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError("subdomain must be a string.")
    sub = v.strip().lower()
    if not sub:
        return None
    if len(sub) < 3 or len(sub) > 63:
        raise ValueError(
            f"Subdomain '{sub}' must be between 3 and 63 characters long (RFC-1035 standard)."
        )
    if "--" in sub:
        raise ValueError(
            f"Subdomain '{sub}' cannot contain consecutive hyphens."
        )
    if not SUBDOMAIN_REGEX.match(sub):
        raise ValueError(
            f"Invalid subdomain hostname '{sub}'. Subdomains may only contain lowercase letters, "
            f"numbers, and hyphens, and cannot start or end with a hyphen."
        )
    if sub in RESERVED_SUBDOMAINS:
        raise ValueError(
            f"Subdomain '{sub}' is a reserved platform hostname and cannot be claimed."
        )
    return sub


def normalize_and_validate_custom_domain(v: Any) -> Optional[str]:
    """Validates and normalizes Fully Qualified Domain Names (FQDN)."""
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError("custom_domain must be a string.")
    domain = v.strip().lower()
    if not domain:
        return None
    # Strip protocol if accidentally entered
    domain = re.sub(r"^https?://", "", domain)
    # Strip paths, queries, hashes
    domain = domain.split("/")[0].split("?")[0].split("#")[0]
    if ":" in domain:
        raise ValueError(
            f"Invalid custom_domain '{v}'. Custom domains must not include a port number."
        )
    if len(domain) > 253:
        raise ValueError("custom_domain cannot exceed 253 characters.")
    if not CUSTOM_DOMAIN_REGEX.match(domain):
        raise ValueError(
            f"Invalid custom_domain '{domain}'. Must be a valid Fully Qualified Domain Name (e.g. 'example.com' or 'shop.example.co.uk')."
        )
    return domain


def normalize_and_validate_page_slugs(v: Any) -> Optional[List[str]]:
    """Validates and normalizes a list of page slugs against supported slugs."""
    if v is None:
        return None
    if not isinstance(v, list):
        raise ValueError("selected_pages must be a list of page slug strings.")

    normalized_pages: List[str] = []
    seen: Set[str] = set()
    for idx, page in enumerate(v):
        if not isinstance(page, str):
            raise ValueError(f"Page slug at index {idx} must be a string.")
        slug = page.strip().lower().replace(" ", "-")
        if not slug:
            raise ValueError(f"Page slug at index {idx} cannot be empty.")
        if slug in PAGE_SLUG_ALIASES:
            slug = PAGE_SLUG_ALIASES[slug]
        if not PAGE_SLUG_REGEX.match(slug):
            raise ValueError(
                f"Invalid page slug format '{page}'. Page slugs must only contain lowercase alphanumeric characters and hyphens."
            )
        if slug not in SUPPORTED_PAGE_SLUGS and slug not in PAGE_SLUG_ALIASES.values():
            raise ValueError(
                f"Unsupported page slug '{slug}'. Supported page slugs are: {', '.join(sorted(SUPPORTED_PAGE_SLUGS))}."
            )
        if slug not in seen:
            seen.add(slug)
            normalized_pages.append(slug)
    return normalized_pages


# ---------------------------------------------------------------------------
# Project Schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Business name")
    industry: str = Field(..., min_length=2, max_length=100, description="Industry or business sector")
    description: str = Field(..., min_length=10, description="Description of the business, services, and value proposition")
    target_audience: Optional[str] = Field(None, max_length=255, description="Target demographic or customer persona")
    style: Optional[str] = Field("Modern & Clean", max_length=100, description="Desired visual design style")
    primary_color: Optional[str] = Field("#2563eb", description="Primary brand hex color")
    secondary_color: Optional[str] = Field("#0f172a", description="Secondary brand hex color")
    accent_color: Optional[str] = Field("#38bdf8", description="Accent brand hex color")
    logo_url: Optional[str] = None
    website_type: WebsiteType = Field("single-page", description="Website architecture: 'single-page' or 'multi-page'")
    selected_pages: Optional[List[str]] = Field(None, description="List of page slugs e.g. ['home', 'about', 'services', 'contact']")
    tech_stack: TechStackType = Field("react-php", description="Supported technology stack: 'react-php' (React frontend + PHP backend) or 'html-tailwind-php'")
    subdomain: Optional[str] = Field(None, description="Desired customer subdomain slug e.g. 'pepsi'")
    custom_domain: Optional[str] = Field(None, description="Custom domain e.g. 'pepsi.com'")

    @field_validator("tech_stack", mode="before")
    @classmethod
    def validate_tech_stack(cls, v: Any) -> str:
        if v is None:
            return "react-php"
        if not isinstance(v, str):
            raise ValueError("tech_stack must be a string.")
        v_clean = v.strip().lower()
        if v_clean not in SUPPORTED_TECH_STACKS:
            raise ValueError(
                f"Unsupported tech_stack '{v}'. Supported stacks are: {', '.join(SUPPORTED_TECH_STACKS)}. "
                f"The required architecture is 'react-php' (React frontend + PHP backend)."
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
                f"Invalid website_type '{v}'. website_type must be either 'single-page' or 'multi-page'."
            )
        return v_clean

    @field_validator("selected_pages", mode="before")
    @classmethod
    def validate_selected_pages(cls, v: Any) -> Optional[List[str]]:
        return normalize_and_validate_page_slugs(v)

    @field_validator("subdomain", mode="before")
    @classmethod
    def validate_subdomain(cls, v: Any) -> Optional[str]:
        return normalize_and_validate_subdomain(v)

    @field_validator("custom_domain", mode="before")
    @classmethod
    def validate_custom_domain(cls, v: Any) -> Optional[str]:
        return normalize_and_validate_custom_domain(v)

    @model_validator(mode="after")
    def validate_pages_consistent_with_website_type(self) -> "ProjectCreate":
        w_type = self.website_type
        pages = self.selected_pages

        if w_type == "single-page":
            if pages is None:
                self.selected_pages = ["home"]
            elif pages != ["home"]:
                raise ValueError(
                    f"For a 'single-page' website, selected_pages must only contain ['home']. "
                    f"Got {pages}. To generate multiple dedicated pages, select website_type='multi-page'."
                )
        elif w_type == "multi-page":
            if pages is None or len(pages) < 2:
                raise ValueError(
                    "For a 'multi-page' website, selected_pages must contain at least 2 distinct pages "
                    "(e.g., 'home' and at least one secondary page such as 'about', 'services', or 'contact')."
                )
            if "home" not in pages:
                raise ValueError(
                    "For a 'multi-page' website, selected_pages must include 'home' as the primary landing page."
                )
        return self


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
    website_type: Optional[WebsiteType] = None
    selected_pages: Optional[List[str]] = None
    tech_stack: Optional[TechStackType] = None
    subdomain: Optional[str] = None
    custom_domain: Optional[str] = None

    @field_validator("tech_stack", mode="before")
    @classmethod
    def validate_tech_stack(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("tech_stack must be a string.")
        v_clean = v.strip().lower()
        if v_clean not in SUPPORTED_TECH_STACKS:
            raise ValueError(
                f"Unsupported tech_stack '{v}'. Supported stacks are: {', '.join(SUPPORTED_TECH_STACKS)}. "
                f"The required architecture is 'react-php' (React frontend + PHP backend)."
            )
        return v_clean

    @field_validator("website_type", mode="before")
    @classmethod
    def validate_website_type(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("website_type must be a string.")
        v_clean = v.strip().lower()
        if v_clean not in SUPPORTED_WEBSITE_TYPES:
            raise ValueError(
                f"Invalid website_type '{v}'. website_type must be either 'single-page' or 'multi-page'."
            )
        return v_clean

    @field_validator("selected_pages", mode="before")
    @classmethod
    def validate_selected_pages(cls, v: Any) -> Optional[List[str]]:
        return normalize_and_validate_page_slugs(v)

    @field_validator("subdomain", mode="before")
    @classmethod
    def validate_subdomain(cls, v: Any) -> Optional[str]:
        return normalize_and_validate_subdomain(v)

    @field_validator("custom_domain", mode="before")
    @classmethod
    def validate_custom_domain(cls, v: Any) -> Optional[str]:
        return normalize_and_validate_custom_domain(v)

    @model_validator(mode="after")
    def validate_pages_consistent_with_website_type(self) -> "ProjectUpdate":
        w_type = self.website_type
        pages = self.selected_pages

        if w_type and pages is not None:
            if w_type == "single-page" and pages != ["home"]:
                raise ValueError(
                    f"For a 'single-page' website, selected_pages must only contain ['home']. "
                    f"Got {pages}. To generate multiple dedicated pages, select website_type='multi-page'."
                )
            if w_type == "multi-page":
                if len(pages) < 2:
                    raise ValueError(
                        "For a 'multi-page' website, selected_pages must contain at least 2 distinct pages."
                    )
                if "home" not in pages:
                    raise ValueError(
                        "For a 'multi-page' website, selected_pages must include 'home'."
                    )
        return self


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
    website_type: str
    selected_pages: Optional[List[str]] = None
    tech_stack: str
    subdomain: Optional[str] = None
    custom_domain: Optional[str] = None
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
    requirements_spec: Optional[Dict[str, Any]] = None
    submissions_count: int = 0
    checkpoints_count: int = 0
    pending_approvals_count: int = 0
    pages_count: int = 0


class NaturalLanguageEditRequest(BaseModel):
    instruction: str = Field(..., min_length=3, description="Natural language instructions describing requested changes")
    section_id: Optional[str] = Field(None, description="Optional target section ID (e.g., 'hero', 'features', 'contact')")
    page_slug: Optional[str] = Field(None, description="Optional target page slug (e.g., 'home', 'about', 'services')")

    @field_validator("section_id", mode="before")
    @classmethod
    def validate_section_id(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("section_id must be a string.")
        s = v.strip().lower()
        if not s:
            return None
        if not SECTION_ID_REGEX.match(s):
            raise ValueError(
                f"Invalid section_id '{v}'. section_id must contain only alphanumeric characters, "
                f"hyphens, and underscores (2-50 characters)."
            )
        return s

    @field_validator("page_slug", mode="before")
    @classmethod
    def validate_page_slug(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("page_slug must be a string.")
        slug = v.strip().lower().replace(" ", "-")
        if not slug:
            return None
        if slug in PAGE_SLUG_ALIASES:
            slug = PAGE_SLUG_ALIASES[slug]
        if not PAGE_SLUG_REGEX.match(slug):
            raise ValueError(
                f"Invalid page_slug '{v}'. page_slug must contain only lowercase alphanumeric characters and hyphens."
            )
        if slug not in SUPPORTED_PAGE_SLUGS and slug not in PAGE_SLUG_ALIASES.values():
            raise ValueError(
                f"Unsupported page_slug '{slug}'. Supported page slugs are: {', '.join(sorted(SUPPORTED_PAGE_SLUGS))}."
            )
        return slug
