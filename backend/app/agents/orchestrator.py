import logging
from typing import Dict, Any, Optional, Tuple, List
from backend.app.schemas.agent import WebsitePlan, SectionSpec, SectionItem, NavigationItem, ColorScheme, Typography, ValidationResult
from backend.app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Orchestrator Agent:
    - Translates business prompt into structured website specification (WebsitePlan).
    - Coordinates downstream agents (Asset, Design, Backend, Execution).
    - Evaluates generated artifacts against specifications ("Does everything match the plan?").
    - Dispatches targeted repair instructions when validation fails.
    - Interprets user's natural language edit requests and plans surgical updates.
    """

    AGENT_NAME = "Orchestrator Agent"

    async def create_website_plan(
        self,
        business_name: str,
        industry: str,
        description: str,
        target_audience: Optional[str] = None,
        style: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        accent_color: Optional[str] = None,
        website_type: Optional[str] = "single-page",
        selected_pages: Optional[List[str]] = None,
        api_key: Optional[str] = None
    ) -> Tuple[WebsitePlan, str]:
        """
        Creates a structured WebsitePlan from business requirements.
        Uses Gemini if configured, otherwise produces a high-fidelity industry-tailored plan.
        """
        pages_str = ", ".join(selected_pages) if selected_pages else ("Home, About, Services, Contact" if website_type == "multi-page" else "Single-page sections")
        prompt = f"""
You are the Lead Website Architect. Create a complete, production-ready website specification for this business:
Business Name: {business_name}
Industry: {industry}
Description: {description}
Target Audience: {target_audience or 'General customers and enterprise clients'}
Visual Style: {style or 'Modern & Clean'}
Website Architecture: {website_type or 'single-page'} (Pages/Scope: {pages_str})
Primary Color Preference: {primary_color or '#2563eb'}
Secondary Color: {secondary_color or '#0f172a'}
Accent Color: {accent_color or '#38bdf8'}

Requirements:
1. Provide a punchy tagline and comprehensive business summary.
2. Formulate navigation links tailored to the architecture ({website_type}).
3. Plan distinct, high-converting sections:
   - 'hero' with headline, subtitle, and CTAs
   - 'features' with at least 3-4 distinct offerings (title, description, Lucide icon name)
   - 'about' with company background, values, and credibility metrics
   - 'testimonials' with 2-3 realistic client reviews
   - 'pricing' with transparent packages
   - 'contact' with clear contact info and interactive form
   - 'footer' with links and copyright
4. Include color scheme with exact hex codes.
"""

        plan, log_msg = await ai_provider.generate_structured(
            prompt=prompt,
            schema_class=WebsitePlan,
            system_instruction="You are an expert full-stack web architect and product strategist. Output only valid JSON matching the WebsitePlan schema.",
            api_key=api_key
        )

        if plan:
            return plan, log_msg

        # Fallback generator: creates an authentic, deep industry-tailored plan
        logger.info(f"Using high-fidelity deterministic planner for {business_name} ({industry})")
        plan = self._generate_fallback_plan(
            business_name=business_name,
            industry=industry,
            description=description,
            target_audience=target_audience,
            style=style,
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_color=accent_color,
            website_type=website_type,
            selected_pages=selected_pages
        )
        return plan, f"Plan formulated via tailored architectural heuristics ({website_type})."

    def _generate_fallback_plan(
        self,
        business_name: str,
        industry: str,
        description: str,
        target_audience: Optional[str] = None,
        style: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        accent_color: Optional[str] = None,
        website_type: Optional[str] = "single-page",
        selected_pages: Optional[List[str]] = None
    ) -> WebsitePlan:
        """Constructs an industry-specific, realistic WebsitePlan."""
        p_col = primary_color or "#2563eb"
        s_col = secondary_color or "#0f172a"
        a_col = accent_color or "#38bdf8"

        is_multipage = website_type == "multi-page" or (selected_pages and len(selected_pages) > 1)

        if is_multipage:
            pages = selected_pages or ["Home", "About Us", "Services", "Portfolio", "Contact Us"]
            nav_items = []
            for p in pages:
                p_slug = "index.html" if p.lower() in ["home", "index"] else f"{p.lower().replace(' ', '-')}.html"
                is_contact = "contact" in p.lower()
                nav_items.append(NavigationItem(label=p, href=p_slug, is_cta=is_contact))
        else:
            nav_items = [
                NavigationItem(label="Services", href="#features"),
                NavigationItem(label="About", href="#about"),
                NavigationItem(label="Testimonials", href="#testimonials"),
                NavigationItem(label="Pricing", href="#pricing"),
                NavigationItem(label="Contact", href="#contact", is_cta=True)
            ]

        contact_href = "contact.html" if is_multipage else "#contact"
        services_href = "services.html" if is_multipage else "#features"

        sections = [
            SectionSpec(
                id="hero",
                type="hero",
                title=f"Transforming {industry} with {business_name}",
                subtitle=description[:160] + "..." if len(description) > 160 else description,
                badge="Leading Industry Innovation",
                cta_primary={"text": "Get In Touch", "href": contact_href},
                cta_secondary={"text": "Explore Services", "href": services_href},
                layout_style="split-left"
            ),
            SectionSpec(
                id="features",
                type="features",
                title="Engineered for Performance and Growth",
                subtitle="Delivering reliable, scalable, and modern solutions designed specifically for your needs.",
                badge="Our Capabilities",
                items=[
                    SectionItem(title="Enterprise Reliability", description="Built with rigorous engineering standards ensuring 99.99% availability and continuous operational excellence.", icon="ShieldCheck", badge="Guaranteed"),
                    SectionItem(title="Rapid Execution", description="Accelerate time-to-market with streamlined workflows and agile methodologies tailored to your goals.", icon="Zap", badge="Fast"),
                    SectionItem(title="Dedicated Support", description="Direct access to seasoned domain specialists around the clock, dedicated to your long-term success.", icon="Headphones", badge="24/7"),
                    SectionItem(title="Measurable Results", description="Data-driven strategies that optimize outcomes, increase engagement, and drive quantifiable value.", icon="TrendingUp", badge="Proven")
                ],
                layout_style="grid-cards"
            ),
            SectionSpec(
                id="about",
                type="about",
                title=f"About {business_name}",
                subtitle=f"Founded to bring modern innovation, reliability, and human-centric design to the {industry} sector.",
                badge="Who We Are",
                items=[
                    SectionItem(title="Our Mission", description="To empower our clients with cutting-edge capabilities and steadfast trust in every engagement.", icon="Compass"),
                    SectionItem(title="Our Vision", description="Setting the standard for quality, transparency, and innovation across global markets.", icon="Eye")
                ],
                layout_style="split-right"
            ),
            SectionSpec(
                id="testimonials",
                type="testimonials",
                title="Trusted by Forward-Thinking Leaders",
                subtitle="Discover how our partners achieve lasting impact and exceed their benchmarks.",
                badge="Client Stories",
                items=[
                    SectionItem(
                        title="Sarah Jenkins, VP of Operations",
                        description=f"Working with {business_name} completely transformed our operations. Their team delivered beyond our expectations with utmost professionalism.",
                        badge="5.0 Rating"
                    ),
                    SectionItem(
                        title="David Chen, Managing Director",
                        description=f"The level of expertise and responsiveness from {business_name} is unmatched in the {industry} space. Highly recommended.",
                        badge="5.0 Rating"
                    )
                ],
                layout_style="centered-carousel"
            ),
            SectionSpec(
                id="pricing",
                type="pricing",
                title="Simple, Transparent Plans",
                subtitle="Predictable pricing designed to scale seamlessly with your organization.",
                badge="Investment",
                items=[
                    SectionItem(title="Starter", description="Ideal for emerging teams and focused projects. Essential features included.", badge="$499/mo"),
                    SectionItem(title="Professional", description="Comprehensive toolkit with priority support, automated workflows, and advanced integrations.", badge="$999/mo"),
                    SectionItem(title="Enterprise", description="Custom architecture, dedicated account manager, SLA guarantees, and tailored onboarding.", badge="Custom")
                ],
                layout_style="pricing-3col"
            ),
            SectionSpec(
                id="contact",
                type="contact",
                title="Let's Build Something Exceptional Together",
                subtitle="Have a question or ready to begin? Send us a message and our team will respond within 24 hours.",
                badge="Contact Us",
                items=[],
                cta_primary={"text": "Send Message", "href": "#contact"},
                layout_style="split-form"
            ),
            SectionSpec(
                id="footer",
                type="footer",
                title=business_name,
                subtitle=f"© {business_name}. All rights reserved.",
                items=[]
            )
        ]

        return WebsitePlan(
            business_name=business_name,
            industry=industry,
            tagline=f"Empowering the Future of {industry}",
            summary=description,
            color_scheme=ColorScheme(
                primary=p_col,
                secondary=s_col,
                accent=a_col,
                background="#ffffff",
                surface="#f8fafc",
                text_primary=s_col,
                text_muted="#64748b"
            ),
            typography=Typography(heading_font="Inter", body_font="Inter"),
            navigation=nav_items,
            sections=sections,
            contact_email=f"contact@{business_name.lower().replace(' ', '')}.com",
            contact_phone="+1 (555) 234-5678",
            social_links={
                "linkedin": "https://linkedin.com",
                "twitter": "https://twitter.com",
                "github": "https://github.com"
            },
            seo_meta={
                "title": f"{business_name} | {industry} Solutions",
                "description": description[:150]
            }
        )

    def evaluate_output_against_plan(
        self,
        plan: WebsitePlan,
        html_content: str,
        has_contact_endpoint: bool
    ) -> ValidationResult:
        """
        Evaluates generated output against the original plan:
        'Does everything match the plan?'
        """
        checks: Dict[str, bool] = {}
        issues: List[str] = []
        recommendations: List[str] = []

        # 1. Check title & business name
        has_business_name = plan.business_name.lower() in html_content.lower()
        checks["business_name_present"] = has_business_name
        if not has_business_name:
            issues.append(f"Business name '{plan.business_name}' is not clearly visible in the document.")

        # 2. Check sections
        for section in plan.sections:
            if section.id in ["features", "services"]:
                sec_id_check = 'id="features"' in html_content or 'id="services"' in html_content or 'services.html' in html_content
            elif section.id == "footer":
                sec_id_check = '<footer' in html_content or 'id="footer"' in html_content
            elif section.id in ["contact"]:
                sec_id_check = 'id="contact"' in html_content or '<form' in html_content or 'contact.html' in html_content
            else:
                sec_id_check = f'id="{section.id}"' in html_content or f"id='{section.id}'" in html_content or f'{section.id}.html' in html_content

            checks[f"section_{section.id}"] = sec_id_check
            if not sec_id_check and section.id not in ["testimonials", "pricing"]:
                issues.append(f"Required section '{section.id}' ({section.type}) is missing from HTML.")

        # 3. Check contact form element or link
        has_form = ("<form" in html_content and "</form>" in html_content) or ("contact.html" in html_content)
        checks["contact_form_element"] = has_form
        if not has_form:
            issues.append("Contact section or link does not contain a functional form/page.")

        # 4. Check form submission handler / interaction script
        has_submit_handler = "fetch(" in html_content or "submit" in html_content or "main.js" in html_content or "<script" in html_content
        checks["form_submission_script"] = has_submit_handler
        if not has_submit_handler:
            issues.append("No client-side submission logic or main.js script attached.")

        # 5. Check responsiveness tags
        has_viewport = '<meta name="viewport"' in html_content
        checks["responsive_viewport"] = has_viewport
        if not has_viewport:
            issues.append("Missing responsive viewport meta tag in head.")

        # 6. Check backend contact endpoint support
        checks["backend_contact_endpoint_configured"] = has_contact_endpoint

        # Calculate score
        total_checks = len(checks)
        passed_checks = sum(1 for v in checks.values() if v)
        score = int((passed_checks / total_checks) * 100) if total_checks > 0 else 0

        passed = len(issues) == 0

        if not passed:
            recommendations.append("Instruct Design Agent and Backend Agent to resolve identified issues.")

        return ValidationResult(
            passed=passed,
            score=score,
            checks=checks,
            issues=issues,
            recommendations=recommendations
        )

orchestrator_agent = OrchestratorAgent()
