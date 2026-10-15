import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
from backend.app.schemas.chat import ConversationalStepResponse, RequirementsReview
from backend.app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)

class TurnGuidance(BaseModel):
    inferred_business_name: Optional[str] = None
    inferred_industry: Optional[str] = None
    inferred_description: Optional[str] = None
    inferred_target_audience: Optional[str] = None
    assistant_message: str
    suggested_options: List[str]

class ConversationalAssistant:
    """
    Intelligent Conversational AI Builder:
    Guides users sequentially through Step 1 to Step 9, recognizes pre-supplied context,
    infers sensible defaults, and compiles structured website specifications.
    """

    INDUSTRY_OPTIONS = [
        "Architecture & Construction",
        "Healthcare & Medical",
        "Technology & SaaS",
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
        "hospitality": ["Home", "Rooms & Suites", "Amenities", "Dining", "Contact Us"],
        "real estate": ["Home", "Listings", "About Us", "Services", "Contact Us"],
        "finance": ["Home", "Services", "About Us", "Case Studies", "Contact Us"],
        "creative": ["Home", "Portfolio", "Services", "About Us", "Contact Us"],
        "default": ["Home", "About Us", "Services", "Pricing", "Contact Us"]
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
        if any(w in t for w in ["software", "saas", "tech", "ai", "platform", "app", "cloud"]):
            return "Technology & SaaS"
        if any(w in t for w in ["shop", "store", "cloth", "fashion", "ecommerce", "retail"]):
            return "E-commerce & Retail"
        if any(w in t for w in ["restaurant", "cafe", "food", "dining", "bar", "beverage", "soda", "drink"]):
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

    async def _ask_ai_turn_guidance(
        self,
        current_step: str,
        user_message: str,
        collected_data: Dict[str, Any]
    ) -> Optional[TurnGuidance]:
        if not ai_provider.is_configured():
            return None
        try:
            prompt = f"""
You are an intelligent, friendly AI Website Builder Consultant guiding a client through creating a professional business website.
Current Step: {current_step}
User's latest message: "{user_message}"
Collected data so far: {json.dumps(collected_data)}

Instructions:
1. Extract any newly stated business attributes (business name, industry, services/description, target audience).
2. Formulate a warm, personalized conversational assistant message that addresses the user's business directly and prompts for the next missing piece of information.
3. Provide 3-4 realistic, highly relevant clickable suggestion chips specifically tailored to THIS business (e.g. for a soda company, options about flavors and retail; for a law firm, options about corporate litigation and personal injury).
"""
            guidance, _ = await ai_provider.generate_structured(
                prompt=prompt,
                schema_class=TurnGuidance,
                system_instruction="You are an expert full-stack web consultant. Return valid JSON matching TurnGuidance. Never give generic boilerplate options."
            )
            return guidance
        except Exception as e:
            logger.warning(f"AI conversational guidance error: {e}")
            return None

    async def process_chat_turn(
        self,
        user_message: str,
        current_step: str,
        collected_data: Dict[str, Any]
    ) -> ConversationalStepResponse:
        """
        Processes a single conversational turn, updates accumulated state,
        and transitions intelligently to the next step.
        """
        data = dict(collected_data)
        msg = user_message.strip()

        # Step 1: Business Name or Initial Idea
        if current_step == "business_name":
            data["raw_idea"] = msg
            if "," in msg or " - " in msg or " for " in msg or len(msg.split()) > 4:
                parts = re.split(r"[,–—\-]| for ", msg, maxsplit=1)
                data["business_name"] = parts[0].strip()
                data["description"] = parts[1].strip() if len(parts) > 1 else msg
            else:
                data["business_name"] = msg

            ai_res = await self._ask_ai_turn_guidance(current_step, msg, data)
            if ai_res:
                if ai_res.inferred_business_name and not data.get("business_name"):
                    data["business_name"] = ai_res.inferred_business_name
                if ai_res.inferred_industry:
                    data["industry"] = ai_res.inferred_industry
                if ai_res.inferred_description and not data.get("description"):
                    data["description"] = ai_res.inferred_description

                if not data.get("industry"):
                    next_s = "industry"
                elif not data.get("description"):
                    next_s = "description"
                else:
                    next_s = "target_audience"

                return ConversationalStepResponse(
                    assistant_message=ai_res.assistant_message,
                    next_step=next_s,
                    suggested_options=ai_res.suggested_options or self.INDUSTRY_OPTIONS,
                    updated_data=data
                )

            # Fallback deterministic
            inferred_ind = self._infer_industry(msg)
            if inferred_ind:
                data["industry"] = inferred_ind

            if not data.get("industry"):
                return ConversationalStepResponse(
                    assistant_message=f"Excellent! '{data['business_name']}' is a great name. What industry does your business belong to?",
                    next_step="industry",
                    suggested_options=self.INDUSTRY_OPTIONS,
                    updated_data=data
                )
            elif not data.get("description"):
                return ConversationalStepResponse(
                    assistant_message=f"Great! I see you are in {data['industry']}. Tell me about what '{data['business_name']}' offers, your primary services, and what makes you unique.",
                    next_step="description",
                    suggested_options=["We provide premium custom solutions", "Fast, reliable services with 24/7 support", "Innovative modern products designed for scale"],
                    updated_data=data
                )
            else:
                return ConversationalStepResponse(
                    assistant_message=f"Got it! Now, who are your ideal target customers?",
                    next_step="target_audience",
                    suggested_options=["Homeowners and property developers", "Enterprise businesses and CTOs", "Individuals and families", "Small and medium businesses"],
                    updated_data=data
                )

        # Step 2: Industry Sector
        elif current_step == "industry":
            data["industry"] = msg
            ai_res = await self._ask_ai_turn_guidance(current_step, msg, data)
            if ai_res:
                if ai_res.inferred_description and not data.get("description"):
                    data["description"] = ai_res.inferred_description
                next_s = "description" if not data.get("description") else "target_audience"
                return ConversationalStepResponse(
                    assistant_message=ai_res.assistant_message,
                    next_step=next_s,
                    suggested_options=ai_res.suggested_options,
                    updated_data=data
                )

            if not data.get("description"):
                return ConversationalStepResponse(
                    assistant_message=f"Perfect. Tell me about '{data.get('business_name', 'your business')}', what services or products you provide, and your key strengths.",
                    next_step="description",
                    suggested_options=["Turnkey professional services", "High-performance modern solutions", "Custom bespoke craftsmanship"],
                    updated_data=data
                )
            else:
                return ConversationalStepResponse(
                    assistant_message=f"Understood. Who is your primary target audience or ideal customer?",
                    next_step="target_audience",
                    suggested_options=["Homeowners & property owners", "Enterprise and corporate clients", "Everyday consumers & shoppers", "Commercial partners"],
                    updated_data=data
                )

        # Step 3: Business Description
        elif current_step == "description":
            data["description"] = msg
            ai_res = await self._ask_ai_turn_guidance(current_step, msg, data)
            if ai_res:
                if ai_res.inferred_target_audience and not data.get("target_audience"):
                    data["target_audience"] = ai_res.inferred_target_audience
                next_s = "target_audience" if not data.get("target_audience") else "website_type"
                return ConversationalStepResponse(
                    assistant_message=ai_res.assistant_message,
                    next_step=next_s,
                    suggested_options=ai_res.suggested_options,
                    updated_data=data
                )

            if not data.get("target_audience"):
                return ConversationalStepResponse(
                    assistant_message="Wonderful description! Who are your ideal customers or target audience?",
                    next_step="target_audience",
                    suggested_options=["Local homeowners and private clients", "Enterprise and commercial clients", "B2B organizations", "Direct consumers worldwide"],
                    updated_data=data
                )
            else:
                return ConversationalStepResponse(
                    assistant_message="Would you like a single-page website or a multi-page website?",
                    next_step="website_type",
                    suggested_options=["Single-page website (Smooth scrolling landing page)", "Multi-page website (Dedicated pages & navigation)"],
                    updated_data=data
                )

        # Step 4: Target Audience
        elif current_step == "target_audience":
            data["target_audience"] = msg
            ai_res = await self._ask_ai_turn_guidance(current_step, msg, data)
            if ai_res and ai_res.assistant_message:
                return ConversationalStepResponse(
                    assistant_message=ai_res.assistant_message,
                    next_step="website_type",
                    suggested_options=ai_res.suggested_options if len(ai_res.suggested_options) >= 2 else ["Single-page website (Smooth scrolling landing page)", "Multi-page website (Dedicated pages & navigation)"],
                    updated_data=data
                )
            return ConversationalStepResponse(
                assistant_message="Would you prefer a single-page website or a multi-page website for your business?",
                next_step="website_type",
                suggested_options=["Single-page website (Smooth scrolling landing page)", "Multi-page website (Dedicated pages & navigation)"],
                updated_data=data
            )

        # Step 5: Website Type (Single-page vs Multi-page)
        elif current_step == "website_type":
            if "multi" in msg.lower():
                data["website_type"] = "multi-page"
                recommended_pages = self._infer_pages_for_industry(data.get("industry", "default"))
                data["selected_pages"] = recommended_pages
                pages_str = ", ".join(recommended_pages)
                return ConversationalStepResponse(
                    assistant_message=f"Multi-page website selected! Based on your {data.get('industry', 'business')}, I recommend these dedicated pages: {pages_str}. Would you like to use these pages, or add/remove any?",
                    next_step="page_selection",
                    suggested_options=[f"Keep recommended ({pages_str})", "Add Portfolio & Case Studies", "Add FAQ page", "Add Blog page"],
                    updated_data=data
                )
            else:
                data["website_type"] = "single-page"
                data["selected_pages"] = ["home"]
                return ConversationalStepResponse(
                    assistant_message="Single-page website selected! What visual design style and brand color palette would you like?",
                    next_step="design_preferences",
                    suggested_options=self.STYLE_OPTIONS,
                    updated_data=data
                )

        # Step 6: Page Selection
        elif current_step == "page_selection":
            if "keep" in msg.lower() or not msg:
                # Keep recommended
                pass
            else:
                # Parse customized pages
                custom_pages = [p.strip().title() for p in re.split(r"[,;&]|\band\b", msg) if p.strip()]
                if custom_pages:
                    if "Home" not in custom_pages:
                        custom_pages.insert(0, "Home")
                    data["selected_pages"] = custom_pages

            return ConversationalStepResponse(
                assistant_message="Pages saved! What visual design style best fits your brand?",
                next_step="design_preferences",
                suggested_options=self.STYLE_OPTIONS,
                updated_data=data
            )

        # Step 7: Design Preferences
        elif current_step == "design_preferences":
            data["style"] = msg
            # Set default colors if not already specified
            if "primary_color" not in data:
                data["primary_color"] = "#2563eb"
                data["secondary_color"] = "#0f172a"
                data["accent_color"] = "#38bdf8"

            return ConversationalStepResponse(
                assistant_message="Which technology stack would you prefer for your website? We recommend a modern React frontend with a secure PHP backend.",
                next_step="technology",
                suggested_options=["React frontend with PHP backend (Recommended)", "Modern HTML5/Tailwind + PHP backend"],
                updated_data=data
            )

        # Step 8: Technology Preference
        elif current_step == "technology":
            data["tech_stack"] = "react-php" if "react" in msg.lower() or "php" in msg.lower() else "html-tailwind-php"

            # Step 9: Review Requirements Summary
            pages_list = data.get("selected_pages", ["Home", "About Us", "Services", "Contact Us"])
            summary = {
                "business_name": data.get("business_name", "My Business"),
                "industry": data.get("industry", "Professional Services"),
                "description": data.get("description", "Quality professional solutions."),
                "target_audience": data.get("target_audience", "General public and businesses"),
                "website_type": data.get("website_type", "multi-page"),
                "selected_pages": pages_list,
                "design_style": data.get("style", "Modern & Clean"),
                "tech_stack": data.get("tech_stack", "react-php"),
                "brand_colors": {
                    "primary": data.get("primary_color", "#2563eb"),
                    "secondary": data.get("secondary_color", "#0f172a"),
                    "accent": data.get("accent_color", "#38bdf8")
                }
            }
            data["review_summary"] = summary

            review_text = (
                f"### Requirements Review for {summary['business_name']}\n\n"
                f"- **Industry:** {summary['industry']}\n"
                f"- **Website Architecture:** {summary['website_type'].capitalize()} ({len(pages_list)} pages)\n"
                f"- **Pages / Sections:** {', '.join(pages_list)}\n"
                f"- **Visual Style:** {summary['design_style']}\n"
                f"- **Technology Stack:** {summary['tech_stack'].upper()} (Interactive Frontend + Validated PHP API)\n"
                f"- **Target Audience:** {summary['target_audience']}\n\n"
                f"Everything is ready! Click **Generate Website** below to launch the 5 specialized AI agents."
            )

            return ConversationalStepResponse(
                assistant_message=review_text,
                next_step="review",
                suggested_options=["🚀 Generate Website Now", "✏️ Edit Requirements", "⬅️ Back to Design"],
                updated_data=data,
                is_complete=True,
                review_summary=summary
            )

        # Default fallback
        return ConversationalStepResponse(
            assistant_message="Tell me your business name or describe what website you want to build:",
            next_step="business_name",
            suggested_options=["Architecture & Design Studio", "Healthcare & Dental Clinic", "E-commerce Clothing Store", "SaaS Tech Platform"],
            updated_data=data
        )

conversational_assistant = ConversationalAssistant()
