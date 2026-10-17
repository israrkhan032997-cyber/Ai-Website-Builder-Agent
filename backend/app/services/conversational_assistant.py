import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from backend.app.schemas.chat import ConversationalStepResponse, RequirementsReview
from backend.app.services.ai_provider import ai_provider
from backend.app.schemas.project import decompose_page_entry, PAGE_SLUG_ALIASES

logger = logging.getLogger(__name__)

SLUG_TO_TITLE: Dict[str, str] = {
    "home": "Home",
    "about": "About Us",
    "about-us": "About Us",
    "services": "Services",
    "portfolio": "Portfolio",
    "case-study": "Case Study",
    "case-studies": "Case Studies",
    "contact": "Contact Us",
    "contact-us": "Contact Us",
    "faq": "FAQ",
    "faqs": "FAQ",
    "blog": "Blog",
    "pricing": "Pricing",
    "testimonials": "Testimonials",
    "team": "Team",
    "our-team": "Our Team",
    "products": "Products",
    "gallery": "Gallery",
    "careers": "Careers",
}


def sanitize_page_list(pages: List[str]) -> List[str]:
    """
    Normalizes any list of page names, actions, or compound strings into unique canonical slugs.
    e.g. ['Home', 'Add Portfolio About', 'Case Study'] -> ['home', 'portfolio', 'about', 'case-study']
    """
    if not pages:
        return ["home"]
    slugs = []
    seen = set()
    for p in pages:
        for s in decompose_page_entry(str(p)):
            s = PAGE_SLUG_ALIASES.get(s, s)
            if s not in seen:
                seen.add(s)
                slugs.append(s)
    if not slugs:
        return ["home"]
    if "home" not in slugs:
        slugs.insert(0, "home")
    return slugs


def sanitize_page_titles(pages: List[str]) -> List[str]:
    """
    Normalizes any list of pages into human-readable Title strings for display.
    """
    slugs = sanitize_page_list(pages)
    return [SLUG_TO_TITLE.get(s, s.replace("-", " ").title()) for s in slugs]


class TurnGuidance(BaseModel):
    inferred_business_name: Optional[str] = None
    inferred_industry: Optional[str] = None
    inferred_description: Optional[str] = None
    inferred_target_audience: Optional[str] = None
    inferred_website_type: Optional[str] = None
    inferred_pages: Optional[List[str]] = None
    inferred_style: Optional[str] = None
    inferred_primary_color: Optional[str] = None
    assistant_message: str
    next_step: Optional[str] = None
    suggested_options: List[str] = Field(default_factory=list)
    is_complete: bool = False


class ConversationalAssistant:
    """
    Intelligent Conversational AI Website Builder:
    Guides users through a stateful, requirement-aware dialogue.
    Extracts explicit facts, prevents hallucinated business attributes,
    and accurately manages single-page vs multi-page React architectures.
    """

    INDUSTRY_OPTIONS = [
        "Technology & SaaS",
        "Architecture & Construction",
        "Healthcare & Medical",
        "E-commerce & Retail",
        "Food & Hospitality",
        "Real Estate & Property",
        "Finance & Consulting",
        "Education & Training",
        "Art & Creative Studio",
        "Legal & Professional Services"
    ]

    PAGE_RECOMMENDATIONS = {
        "architecture": ["Home", "About Us", "Services", "Portfolio", "Contact Us"],
        "construction": ["Home", "About Us", "Services", "Projects", "Contact Us"],
        "healthcare": ["Home", "About Us", "Services", "Testimonials", "Contact Us"],
        "medical": ["Home", "About Us", "Services", "Testimonials", "Contact Us"],
        "technology": ["Home", "Features", "About Us", "Pricing", "Contact Us"],
        "saas": ["Home", "Features", "About Us", "Pricing", "Contact Us"],
        "e-commerce": ["Home", "Products", "About Us", "FAQ", "Contact Us"],
        "retail": ["Home", "Products", "About Us", "Gallery", "Contact Us"],
        "food": ["Home", "Menu", "About Us", "Gallery", "Contact Us"],
        "restaurant": ["Home", "Menu", "About Us", "Reservations", "Contact Us"],
        "hospitality": ["Home", "Rooms & Suites", "Amenities", "Dining", "Contact Us"],
        "real estate": ["Home", "Listings", "About Us", "Services", "Contact Us"],
        "finance": ["Home", "Services", "About Us", "Case Studies", "Contact Us"],
        "creative": ["Home", "Portfolio", "Services", "About Us", "Contact Us"],
        "default": ["Home", "About Us", "Services", "Portfolio", "Contact Us"]
    }

    STYLE_OPTIONS = [
        "Modern & Clean",
        "Minimalist & Bold",
        "Luxury & Premium",
        "Technical & Sleek",
        "Warm & Approachable"
    ]

    def _infer_industry(self, text: str) -> Optional[str]:
        t = text.lower()
        if any(w in t for w in ["architect", "interior", "decor", "building", "construct"]):
            return "Architecture & Construction"
        if any(w in t for w in ["health", "clinic", "doctor", "medical", "patient", "dental", "pharma"]):
            return "Healthcare & Medical"
        if any(w in t for w in ["software", "saas", "tech", "ai", "platform", "app", "cloud", "code", "dev"]):
            return "Technology & SaaS"
        if any(w in t for w in ["shop", "store", "cloth", "fashion", "ecommerce", "retail", "boutique"]):
            return "E-commerce & Retail"
        if any(w in t for w in ["restaurant", "cafe", "food", "dining", "bar", "beverage", "soda", "drink", "bistro"]):
            return "Food & Hospitality"
        if any(w in t for w in ["realtor", "real estate", "property", "apartment", "villa", "house"]):
            return "Real Estate & Property"
        if any(w in t for w in ["consult", "finance", "bank", "invest", "accounting", "advisory"]):
            return "Finance & Consulting"
        if any(w in t for w in ["school", "learn", "academy", "course", "education", "tutor"]):
            return "Education & Training"
        if any(w in t for w in ["art", "design", "photo", "studio", "creative", "agency"]):
            return "Art & Creative Studio"
        return None

    def _infer_pages_for_industry(self, industry: str) -> List[str]:
        ind_lower = industry.lower()
        for key, pages in self.PAGE_RECOMMENDATIONS.items():
            if key in ind_lower:
                return pages
        return self.PAGE_RECOMMENDATIONS["default"]

    def _get_recommended_pages_for_count(self, industry: str, count: int) -> List[str]:
        ind_pages = self._infer_pages_for_industry(industry)
        pool = ["Home", "About Us", "Services", "Portfolio", "Case Study", "Testimonials", "Pricing", "FAQ", "Blog", "Contact Us"]
        chosen = []
        for p in ind_pages:
            if p not in chosen:
                chosen.append(p)
            if len(chosen) >= count:
                break
        if len(chosen) < count:
            for p in pool:
                if p not in chosen:
                    chosen.append(p)
                if len(chosen) >= count:
                    break
        return chosen[:count]

    def _is_name_only_input(self, text: str) -> bool:
        """Determines if input is just a business name rather than a detailed brief."""
        words = text.strip().split()
        if len(words) <= 3:
            indicators = ["we", "is", "a", "an", "for", "our", "providing", "sell", "help", "platform", "store", "build", "want", "pages", "page"]
            if not any(w.lower() in indicators for w in words):
                return True
        return False

    def _extract_clean_industry_and_description(self, msg: str) -> Tuple[str, str, Optional[int]]:
        """
        Extracts a clean, normalized industry title, a well-formed description, and any requested page count.
        Prevents raw user prompts from polluting the industry field.
        """
        m_lower = msg.lower()

        # 1. Detect page count requests (e.g. "give me a five pages website", "5 pages")
        page_count = None
        num_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8}
        count_match = re.search(r'(\d+|one|two|three|four|five|six|seven|eight)\s*(?:page|pages)', m_lower)
        if count_match:
            val = count_match.group(1)
            page_count = int(val) if val.isdigit() else num_map.get(val, 5)

        # 2. Match known industry concepts
        if any(k in m_lower for k in ['webdeveloper', 'web developer', 'full stack', 'fullstack', 'frontend', 'backend dev']):
            industry = "Web Development & Technology"
            description = "Full stack web development services, custom applications, and modern digital engineering."
        elif any(k in m_lower for k in ['ai and software', 'artificial intelligence', 'machine learning', 'software company', 'software development']):
            industry = "AI & Software Development"
            description = "AI and software development company providing innovative technology solutions and scalable systems."
        elif any(k in m_lower for k in ['web development', 'it services', 'information tech']):
            industry = "Web Development & IT Services"
            description = "Professional web development and IT infrastructure services."
        elif any(k in m_lower for k in ['digital agency', 'marketing agency', 'consulting', 'advisory']):
            industry = "Digital Agency & Consulting"
            description = "Digital agency and strategic consulting services delivering high-impact growth."
        elif any(k in m_lower for k in ['portfolio', 'freelance', 'personal portfolio']):
            industry = "Personal Portfolio & Services"
            description = "Showcase of professional projects, technical skills, and client work."
        elif any(k in m_lower for k in ['architect', 'interior', 'construction', 'decor', 'building']):
            industry = "Architecture & Construction"
            description = "Innovative architecture and construction services designing sustainable spaces."
        elif any(k in m_lower for k in ['health', 'clinic', 'medical', 'dental', 'doctor']):
            industry = "Healthcare & Medical"
            description = "Compassionate and professional healthcare and medical services."
        elif any(k in m_lower for k in ['restaurant', 'cafe', 'food', 'hospitality', 'bistro']):
            industry = "Food & Hospitality"
            description = "Exquisite dining experiences and culinary hospitality services."
        elif any(k in m_lower for k in ['shop', 'store', 'ecommerce', 'retail', 'clothing', 'fashion']):
            industry = "E-commerce & Retail"
            description = "Curated retail shopping and premier e-commerce products."
        else:
            cleaned = re.sub(r'^(give me|i want|create|build|make|we are|we do)\s+(a\s+)?', '', msg, flags=re.I).strip()
            # Remove any trailing "website" or "for full stack..."
            cleaned = re.sub(r'\s+website.*$', '', cleaned, flags=re.I).strip()
            industry = cleaned.title() if len(cleaned) < 50 and cleaned else "Technology & Services"
            description = f"{industry} providing specialized client solutions."

        return industry, description, page_count

    def _resolve_pages_from_message(self, msg: str, current_pages: List[str]) -> List[str]:
        """
        Interprets natural language page customization inputs, decomposes compound labels,
        and accurately mutates the list of pages.
        """
        m_lower = msg.lower().strip()
        if "keep" in m_lower or not m_lower:
            return sanitize_page_titles(current_pages)

        # Check for numeric requests e.g. "so give me another two pages" or "add 2 pages"
        count_match = re.search(r'(?:another|more|add)\s*(\d+|one|two|three|four)\s*(?:page|pages)?', m_lower)
        if count_match:
            num_words = {"one": 1, "two": 2, "three": 3, "four": 4}
            val = count_match.group(1)
            add_count = int(val) if val.isdigit() else num_words.get(val, 2)
            pool = ["Portfolio", "Case Study", "Testimonials", "Pricing", "FAQ", "Blog", "Our Team", "Careers"]
            existing = set(sanitize_page_list(current_pages))
            to_add = []
            for candidate in pool:
                cand_slug = decompose_page_entry(candidate)[0]
                if cand_slug not in existing:
                    to_add.append(candidate)
                    existing.add(cand_slug)
                    if len(to_add) >= add_count:
                        break
            return sanitize_page_titles(current_pages + to_add)

        # Decompose input string into valid slugs
        slugs = decompose_page_entry(msg)
        if not slugs:
            return sanitize_page_titles(current_pages)

        # If user explicitly said "add ..." or "also ...", append to existing
        if re.search(r'^(add|also|include|plus)\b', m_lower):
            combined = list(current_pages)
            for s in slugs:
                title = SLUG_TO_TITLE.get(s, s.replace("-", " ").title())
                if title not in combined:
                    combined.append(title)
            return sanitize_page_titles(combined)

        # Otherwise treat as a new explicit list of pages
        titles = [SLUG_TO_TITLE.get(s, s.replace("-", " ").title()) for s in slugs]
        if "Home" not in titles:
            titles.insert(0, "Home")
        return titles

    async def _ask_ai_turn_guidance(
        self,
        current_step: str,
        user_message: str,
        collected_data: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> Tuple[Optional[TurnGuidance], str]:
        if not ai_provider.is_configured(api_key):
            return None, "Gemini API key is not configured. Please configure GEMINI_API_KEY in your local .env file."
        try:
            prompt = f"""
You are an expert AI Website Builder Consultant guiding a client through creating a professional business website.
The user's website architecture MUST use pure React SPA on the frontend (Vite + Tailwind CSS).

Current Onboarding Step: {current_step}
User's latest message: "{user_message}"
Collected data so far: {json.dumps(collected_data)}

YOUR GOALS:
1. Provide a warm, conversational, professional response in `assistant_message`.
   - Directly acknowledge the user's specific input with tailored enthusiasm.
   - If the user asks a question, gives feedback, or inquires about options (e.g. "What's the difference between single and multi page?" or "What pages do you recommend?"), answer their question thoroughly, then guide them to the next required question.
   - If the user only gave a person or business name (e.g. 'Israr'), warmly welcome them, ask what type of business or website they want to create under this name, and DO NOT guess or hallucinate what the business is.
   - Never use generic or repetitive canned templates. Speak authentically and contextually.
2. Determine `next_step` logically:
   - 'business_name' (if name is missing)
   - 'industry' (if industry/sector is missing)
   - 'description' (if services/description is missing)
   - 'target_audience' (if target demographic is missing. If the user already provided the audience/demographic in their brief, do NOT ask for it again; advance to 'website_type')
   - 'website_type' (if user hasn't decided between 'single-page' and 'multi-page'. If user provided a comprehensive brief upfront, advance directly to 'website_type')
   - 'page_selection' (if multi-page was chosen and pages need confirmation/customization)
   - 'design_preferences' (if visual style, colors, mood are needed)
   - 'review' (when all core requirements are gathered, present a clear, comprehensive review)
   - 'ready_to_generate' (when review is confirmed)
3. Generate 3-4 dynamic, highly relevant `suggested_options` tailored specifically to this business and current step.
   - Tailor options strictly to the business context (e.g. if bakery: suggest bakery products/audiences/pages; if tech agency: suggest SaaS/cloud/enterprise options).
4. Extract clean fields without hallucinating details the user has not mentioned:
   - `inferred_business_name`: extract if newly mentioned or changed. If `collected_data` already has a valid business_name (e.g. 'Israr'), DO NOT overwrite it unless the user explicitly requested to rename.
   - `inferred_industry`: concise industry sector (e.g. "AI & Software Development", "Artisan Bakery", "Dental Clinic").
   - `inferred_description`: clear summary of business offerings and value proposition.
   - `inferred_target_audience`: concise description of ideal customer base.
   - `inferred_website_type`: 'single-page' or 'multi-page' if specified or implied.
   - `inferred_pages`: list of clean page names (e.g. ["Home", "About Us", "Services", "Contact Us"]) if mentioned.
   - `inferred_style`: visual design mood (e.g. "Modern & Clean", "Dark & High-Tech", "Warm & Elegant").
   - `inferred_primary_color`: brand hex color if specified.
5. If at the 'review' step or all requirements are present, set `is_complete` to true, and in `assistant_message` format a clean, comprehensive Markdown requirements review, then invite them to click 'Generate Website'.
"""
            guidance, log_msg = await ai_provider.generate_structured(
                prompt=prompt,
                schema_class=TurnGuidance,
                system_instruction="You are an expert full-stack web consultant and AI architect. Output only valid JSON matching TurnGuidance.",
                api_key=api_key
            )
            return guidance, log_msg
        except Exception as e:
            logger.warning(f"AI conversational guidance error: {e}")
            return None, str(e)

    async def process_chat_turn(
        self,
        user_message: str,
        current_step: str,
        collected_data: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> ConversationalStepResponse:
        """
        Processes a single conversational turn using Google Gemini API,
        updates accumulated state, and returns real AI-generated text and suggestions.
        """
        data = dict(collected_data)
        data["tech_stack"] = "react"
        msg = user_message.strip()
        if not msg:
            raise ValueError("User message cannot be empty.")

        # Real Gemini integration check
        if not ai_provider.is_configured(api_key):
            raise RuntimeError(
                "Gemini API key is not configured. Please configure GEMINI_API_KEY in your local .env file."
            )

        # Call Google Gemini API with the exact user message and state
        ai_res, log_err = await self._ask_ai_turn_guidance(current_step, msg, data, api_key=api_key)
        if not ai_res:
            raise RuntimeError(f"Gemini API request failed: {log_err}")

        # Update collected data using genuine Gemini extraction & strict anti-hallucination rules
        is_name_only = self._is_name_only_input(msg)
        if not data.get("business_name"):
            if ai_res.inferred_business_name:
                data["business_name"] = ai_res.inferred_business_name.strip()
            elif is_name_only:
                data["business_name"] = msg
            elif "," in msg or " - " in msg or " for " in msg:
                parts = re.split(r"[,–—\-]| for ", msg, maxsplit=1)
                data["business_name"] = parts[0].strip()
            else:
                data["business_name"] = msg
        elif "rename" in msg.lower() or "change name" in msg.lower():
            if ai_res.inferred_business_name:
                data["business_name"] = ai_res.inferred_business_name.strip()

        # Industry & Description
        ind, desc, page_count = self._extract_clean_industry_and_description(msg)
        if ind:
            data["industry"] = ind
        elif ai_res.inferred_industry:
            data["industry"] = ai_res.inferred_industry.strip()

        if desc and not data.get("description"):
            data["description"] = desc
        elif ai_res.inferred_description and not data.get("description"):
            data["description"] = ai_res.inferred_description.strip()

        # Anti-hallucination check: if user only typed a name on business_name step
        if is_name_only and current_step == "business_name":
            data.pop("industry", None)
            data.pop("description", None)
            data.pop("target_audience", None)

        if ai_res.inferred_target_audience and not data.get("target_audience"):
            data["target_audience"] = ai_res.inferred_target_audience.strip()

        # Website architecture & pages
        if page_count and page_count > 1:
            data["website_type"] = "multi-page"
            recommended = self._get_recommended_pages_for_count(data.get("industry", "general"), page_count)
            data["selected_pages"] = recommended
        elif ai_res.inferred_website_type in ["single-page", "multi-page"]:
            data["website_type"] = ai_res.inferred_website_type
            if data["website_type"] == "single-page":
                data["selected_pages"] = ["Home"]
            elif not data.get("selected_pages"):
                data["selected_pages"] = self._infer_pages_for_industry(data.get("industry", "general"))
        elif "multi" in msg.lower():
            data["website_type"] = "multi-page"
            if not data.get("selected_pages"):
                data["selected_pages"] = self._infer_pages_for_industry(data.get("industry", "general"))
        elif "single" in msg.lower():
            data["website_type"] = "single-page"
            data["selected_pages"] = ["Home"]

        if current_step == "page_selection" or ai_res.inferred_pages:
            if ai_res.inferred_pages:
                data["selected_pages"] = sanitize_page_titles(ai_res.inferred_pages)
            elif current_step == "page_selection":
                current_pages = data.get("selected_pages", ["Home", "About Us", "Services", "Portfolio", "Contact Us"])
                data["selected_pages"] = self._resolve_pages_from_message(msg, current_pages)

        # Style & Colors
        if ai_res.inferred_style:
            data["style"] = ai_res.inferred_style.strip()
        elif current_step == "design_preferences":
            data["style"] = msg

        if ai_res.inferred_primary_color:
            data["primary_color"] = ai_res.inferred_primary_color.strip()
        elif "primary_color" not in data:
            data["primary_color"] = "#2563eb"
            data["secondary_color"] = "#0f172a"
            data["accent_color"] = "#38bdf8"

        # Determine next step
        if current_step == "website_type":
            if data.get("website_type") == "multi-page":
                next_s = "page_selection"
                if not data.get("selected_pages"):
                    data["selected_pages"] = self._infer_pages_for_industry(data.get("industry", "general"))
            else:
                next_s = "design_preferences"
                data["selected_pages"] = ["Home"]
        else:
            next_s = ai_res.next_step

        # If next_s is asking for an attribute that is already collected, advance forward
        # to avoid asking redundant questions
        if next_s == "business_name" and data.get("business_name"):
            next_s = "industry"
        if next_s == "industry" and data.get("industry"):
            next_s = "description"
        if next_s == "description" and data.get("description"):
            next_s = "target_audience"
        if next_s == "target_audience" and data.get("target_audience"):
            next_s = "website_type"
        if next_s == "website_type" and data.get("website_type"):
            next_s = "page_selection" if data.get("website_type") == "multi-page" and not data.get("selected_pages") else "design_preferences"

        if not next_s or next_s not in [
            "business_name", "industry", "description", "target_audience",
            "website_type", "page_selection", "design_preferences", "review", "ready_to_generate"
        ]:
            if not data.get("business_name"):
                next_s = "business_name"
            elif not data.get("industry"):
                next_s = "industry"
            elif not data.get("description"):
                next_s = "description"
            elif not data.get("target_audience"):
                next_s = "target_audience"
            elif not data.get("website_type"):
                next_s = "website_type"
            elif data.get("website_type") == "multi-page" and not data.get("selected_pages"):
                next_s = "page_selection"
            elif not data.get("style"):
                next_s = "design_preferences"
            else:
                next_s = "review"

        # Align suggested options if step advanced to website_type
        suggested_options = list(ai_res.suggested_options or [])
        if next_s == "website_type" and not any("page" in opt.lower() for opt in suggested_options):
            suggested_options = ["Multi-Page Website (Recommended)", "Single-Page Website (Landing Page)"]

        # Construct review summary if at review stage
        is_complete = ai_res.is_complete or (next_s in ["review", "ready_to_generate"])
        if is_complete or next_s in ["review", "ready_to_generate"]:
            pages_list = sanitize_page_titles(data.get("selected_pages", ["Home"]))
            data["selected_pages"] = pages_list
            summary = {
                "business_name": data.get("business_name", "My Business"),
                "industry": data.get("industry", "Technology & Services"),
                "description": data.get("description", "Quality professional solutions."),
                "target_audience": data.get("target_audience", "General public and businesses"),
                "website_type": data.get("website_type", "single-page"),
                "selected_pages": pages_list,
                "design_style": data.get("style", "Modern & Clean"),
                "tech_stack": "react",
                "brand_colors": {
                    "primary": data.get("primary_color", "#2563eb"),
                    "secondary": data.get("secondary_color", "#0f172a"),
                    "accent": data.get("accent_color", "#38bdf8")
                }
            }
            data["review_summary"] = summary
            next_s = "review"
            is_complete = True

        return ConversationalStepResponse(
            assistant_message=ai_res.assistant_message,
            next_step=next_s,
            suggested_options=suggested_options,
            updated_data=data,
            is_complete=is_complete,
            review_summary=data.get("review_summary")
        )

conversational_assistant = ConversationalAssistant()
