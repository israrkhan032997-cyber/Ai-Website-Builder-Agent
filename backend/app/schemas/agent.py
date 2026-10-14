from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NavigationItem(BaseModel):
    label: str
    href: str
    is_cta: bool = False

class SectionItem(BaseModel):
    title: str
    description: str
    icon: Optional[str] = "Sparkles"
    badge: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class SectionSpec(BaseModel):
    id: str
    type: str # hero, features, about, testimonials, pricing, cta, contact, footer
    title: str
    subtitle: Optional[str] = None
    badge: Optional[str] = None
    items: List[SectionItem] = []
    cta_primary: Optional[Dict[str, str]] = None # {"text": "Get Started", "href": "#contact"}
    cta_secondary: Optional[Dict[str, str]] = None
    layout_style: str = "default" # grid-3, cards, split-left, split-right, centered

class ColorScheme(BaseModel):
    primary: str = "#2563eb"
    secondary: str = "#0f172a"
    accent: str = "#38bdf8"
    background: str = "#ffffff"
    surface: str = "#f8fafc"
    text_primary: str = "#0f172a"
    text_muted: str = "#64748b"

class Typography(BaseModel):
    heading_font: str = "Inter"
    body_font: str = "Inter"

class WebsitePlan(BaseModel):
    business_name: str
    industry: str
    tagline: str
    summary: str
    color_scheme: ColorScheme = Field(default_factory=ColorScheme)
    typography: Typography = Field(default_factory=Typography)
    navigation: List[NavigationItem] = []
    sections: List[SectionSpec] = []
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    social_links: Dict[str, str] = {}
    seo_meta: Dict[str, str] = {}

class AssetItem(BaseModel):
    id: str
    type: str # hero_image, feature_image, about_image, icon, logo
    name: str
    description: str
    url: str
    fallback_svg: Optional[str] = None
    alt: str
    source: str = "Unsplash"

class AssetManifest(BaseModel):
    logo: AssetItem
    images: List[AssetItem] = []
    icons: List[str] = []

class CodeFile(BaseModel):
    path: str
    content: str
    description: Optional[str] = None

class ValidationResult(BaseModel):
    passed: bool
    score: int = 100 # 0-100
    checks: Dict[str, bool] = {} # e.g. {"has_index_html": True, "has_contact_form": True}
    issues: List[str] = []
    recommendations: List[str] = []

class AgentWorkflowStatus(BaseModel):
    project_id: str
    overall_status: str # draft, planning, generating_assets, generating_design, generating_backend, validating, ready, failed
    current_agent: Optional[str] = None
    current_step: Optional[str] = None
    progress: str = "0%"
    last_log_message: Optional[str] = None
