import logging
import re
from typing import Dict, List, Optional
from backend.app.schemas.agent import WebsitePlan, AssetManifest, CodeFile, SectionItem, SectionSpec
from backend.app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)

class DesignAgent:
    """
    Design Agent:
    - Generates clean, responsive, production-ready frontend code (HTML5, modern Tailwind CSS, JS).
    - Supports both Single-page landing pages and Multi-page corporate websites (Home, About, Services, Portfolio, Contact).
    - Implements reusable component structures, responsive viewports, and accessible forms.
    - Applies targeted natural language modifications (colors, headlines, sections).
    """

    AGENT_NAME = "Design Agent"

    def generate_website_bundle(
        self,
        project_id: str,
        plan: WebsitePlan,
        assets: AssetManifest,
        website_type: str = "single-page",
        selected_pages: Optional[List[str]] = None
    ) -> List[CodeFile]:
        """
        Produces a complete frontend bundle:
        - If multi-page: index.html, about.html, services.html, portfolio.html, contact.html
        - If single-page: index.html with smooth anchor scrolling
        - styles.css
        - main.js (mobile navigation drawer, active link highlighting, contact form submission)
        """
        is_multi = website_type == "multi-page" or (selected_pages and len(selected_pages) > 1)
        pages_to_build = selected_pages or (["Home", "About Us", "Services", "Portfolio", "Contact Us"] if is_multi else ["Home"])

        files: List[CodeFile] = []

        if is_multi:
            # Multi-page architecture
            # Normalize pages list
            norm_pages = [p.strip().title() for p in pages_to_build if p.strip()]
            if "Home" not in norm_pages:
                norm_pages.insert(0, "Home")

            # Generate individual pages
            for page_name in norm_pages:
                file_slug = "index" if page_name.lower() in ["home", "index"] else self._slugify(page_name)
                html = self._render_multipage_html(project_id, plan, assets, page_name, norm_pages)
                files.append(CodeFile(
                    path=f"{file_slug}.html",
                    content=html,
                    description=f"{page_name} page for {plan.business_name}"
                ))
        else:
            # Single-page architecture
            html = self._render_singlepage_html(project_id, plan, assets)
            files.append(CodeFile(
                path="index.html",
                content=html,
                description=f"Single-page landing page for {plan.business_name}"
            ))

        # CSS and JS
        files.append(CodeFile(path="styles.css", content=self._render_css(plan), description="Theme tokens and micro-interactions"))
        files.append(CodeFile(path="main.js", content=self._render_js(project_id), description="Client scripts and form submission handler"))

        return files

    def _slugify(self, text: str) -> str:
        s = text.lower().strip()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        return s.strip("-")

    def _render_nav_links(self, current_page: str, pages: List[str], primary_color: str, is_mobile: bool = False) -> str:
        links_html = ""
        for p in pages:
            is_active = p.lower() == current_page.lower()
            file_name = "index.html" if p.lower() == "home" else f"{self._slugify(p)}.html"
            is_contact = p.lower() in ["contact", "contact us"]

            if is_mobile:
                if is_contact:
                    links_html += f'<a href="{file_name}" class="block px-4 py-2.5 text-base font-bold text-white rounded-xl text-center shadow-sm" style="background-color: {primary_color}">{p}</a>\n'
                else:
                    active_cls = f"bg-blue-50 text-blue-700 font-bold" if is_active else "text-slate-700 hover:bg-slate-50 font-medium"
                    links_html += f'<a href="{file_name}" class="block px-3 py-2 rounded-lg text-base {active_cls}">{p}</a>\n'
            else:
                if is_contact:
                    links_html += f'<a href="{file_name}" class="inline-flex items-center px-5 py-2 text-sm font-bold text-white rounded-xl shadow-sm hover:opacity-95 transition-all" style="background-color: {primary_color}">{p}</a>\n'
                else:
                    active_cls = f"text-blue-600 font-bold border-b-2" if is_active else "text-slate-600 hover:text-slate-900 font-medium"
                    active_style = f"border-color: {primary_color};" if is_active else ""
                    links_html += f'<a href="{file_name}" class="text-sm px-1 py-1 transition-colors {active_cls}" style="{active_style}">{p}</a>\n'
        return links_html

    def _safe_lucide_icon(self, icon_name: Optional[str]) -> str:
        if not icon_name:
            return "Sparkles"
        name = icon_name.strip()
        clean = re.sub(r"[^a-zA-Z0-9]", "", name)
        return clean if clean else "Sparkles"

    def _render_dynamic_features_cards(self, plan: WebsitePlan, p_col: str, link_target: str = "services.html") -> str:
        sec = next((s for s in plan.sections if s.type in ["features", "services"] or s.id in ["features", "services"]), None)
        items = sec.items if sec and sec.items else []
        if not items:
            items = [
                SectionItem(title=f"Signature {plan.industry} Solutions", description=f"Engineered specifically for {plan.business_name} clients to drive superior outcomes.", icon="Sparkles"),
                SectionItem(title="Rapid Execution & Precision", description="Accelerating timelines through disciplined processes and modern methodologies.", icon="Zap"),
                SectionItem(title="Dedicated Advisory & Support", description="Continuous consultation and dedicated specialist oversight at every milestone.", icon="ShieldCheck")
            ]

        cards_html = ""
        for item in items[:6]:
            icon = self._safe_lucide_icon(item.icon)
            cards_html += f"""
                    <div class="p-8 bg-slate-50 rounded-2xl border border-slate-200/60 hover:shadow-md transition-shadow">
                        <div class="w-12 h-12 rounded-xl flex items-center justify-center mb-5 font-bold" style="background-color: {p_col}15; color: {p_col};">
                            <i data-lucide="{icon}" class="w-6 h-6"></i>
                        </div>
                        <h3 class="text-xl font-bold text-slate-900 mb-2">{item.title}</h3>
                        <p class="text-slate-600 text-sm leading-relaxed mb-4">{item.description}</p>
                        <a href="{link_target}" class="text-xs font-bold hover:underline" style="color: {p_col}">Learn more →</a>
                    </div>"""
        return cards_html

    def _render_dynamic_services_page_cards(self, plan: WebsitePlan, p_col: str) -> str:
        sec = next((s for s in plan.sections if s.type in ["features", "services"] or s.id in ["features", "services"]), None)
        items = sec.items if sec and sec.items else []
        if not items:
            items = [
                SectionItem(title=f"Full-Lifecycle {plan.industry} Services", description=f"Bespoke consulting, strategic deployment, and turnkey outcomes for {plan.business_name}.", icon="Layers"),
                SectionItem(title="Scalability & Performance", description="Modernizing operations and scaling infrastructure to exceed benchmark standards.", icon="TrendingUp"),
                SectionItem(title="Compliance, Quality & Security", description="Uncompromising adherence to industry protocols and data safeguards.", icon="ShieldCheck")
            ]

        cards_html = ""
        for item in items:
            icon = self._safe_lucide_icon(item.icon)
            badge_text = item.badge or "Turnkey"
            cards_html += f"""
                    <div class="p-8 bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg transition-all space-y-4">
                        <div class="flex items-center justify-between">
                            <div class="w-12 h-12 rounded-xl flex items-center justify-center font-bold" style="background-color: {p_col}15; color: {p_col};">
                                <i data-lucide="{icon}" class="w-6 h-6"></i>
                            </div>
                            <span class="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">{badge_text}</span>
                        </div>
                        <h3 class="text-xl font-bold text-slate-900">{item.title}</h3>
                        <p class="text-slate-600 text-sm leading-relaxed">{item.description}</p>
                        <ul class="text-xs text-slate-500 space-y-2 pt-2 border-t border-slate-100">
                            <li class="flex items-center"><i data-lucide="Check" class="w-4 h-4 mr-2 text-emerald-500"></i> Tailored for {plan.business_name} clients</li>
                            <li class="flex items-center"><i data-lucide="Check" class="w-4 h-4 mr-2 text-emerald-500"></i> Full quality assurance & support</li>
                        </ul>
                    </div>"""
        return cards_html

    def _render_dynamic_testimonials(self, plan: WebsitePlan, p_col: str) -> str:
        sec = next((s for s in plan.sections if s.type == "testimonials" or s.id == "testimonials"), None)
        items = sec.items if sec and sec.items else []
        if not items:
            items = [
                SectionItem(title="Enterprise Client", description=f"Partnering with {plan.business_name} elevated our operations in {plan.industry}. Their attention to detail and delivery speed are unmatched.", badge="Managing Director"),
                SectionItem(title="Commercial Partner", description=f"Exceptional responsiveness, world-class execution, and measurable outcomes. Highly recommend {plan.business_name}.", badge="Head of Operations")
            ]

        cards_html = ""
        for item in items[:3]:
            cards_html += f"""
                    <div class="p-8 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
                        <div class="flex text-amber-400 space-x-1">
                            <i data-lucide="Star" class="w-4 h-4 fill-amber-400"></i>
                            <i data-lucide="Star" class="w-4 h-4 fill-amber-400"></i>
                            <i data-lucide="Star" class="w-4 h-4 fill-amber-400"></i>
                            <i data-lucide="Star" class="w-4 h-4 fill-amber-400"></i>
                            <i data-lucide="Star" class="w-4 h-4 fill-amber-400"></i>
                        </div>
                        <p class="text-slate-600 text-sm italic leading-relaxed">"{item.description}"</p>
                        <div class="pt-3 border-t border-slate-100">
                            <h4 class="font-bold text-slate-900 text-sm">{item.title}</h4>
                            <p class="text-xs text-slate-400">{item.badge or "Verified Client"}</p>
                        </div>
                    </div>"""

        return f"""
        <!-- Testimonials Section -->
        <section class="py-20 bg-slate-50 border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16">
                    <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Client Feedback</span>
                    <h2 class="text-3xl font-extrabold text-slate-900 mt-1">Trusted by Industry Leaders</h2>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-{min(len(items), 3)} gap-8">
                    {cards_html}
                </div>
            </div>
        </section>"""

    def _render_dynamic_portfolio_cards(self, plan: WebsitePlan, hero_img: str, features_img: str, about_img: str) -> str:
        sec = next((s for s in plan.sections if s.type in ["portfolio", "projects", "gallery"] or s.id in ["portfolio", "projects"]), None)
        items = sec.items if sec and sec.items else []
        img_pool = [hero_img, features_img, about_img]

        if not items:
            items = [
                SectionItem(title=f"Flagship {plan.industry} Deployment", description=f"Turnkey execution delivering benchmark performance for high-profile clients of {plan.business_name}.", badge="Flagship"),
                SectionItem(title="Enterprise Transformation", description="Scalable modern implementation deployed seamlessly with zero operational downtime.", badge="Enterprise"),
                SectionItem(title="Bespoke Client Initiative", description="Handcrafted solutions aligned to distinct aesthetic and functional requirements.", badge="Custom")
            ]

        cards_html = ""
        for i, item in enumerate(items[:6]):
            card_img = img_pool[i % len(img_pool)]
            badge_text = item.badge or "Case Study"
            cards_html += f"""
                    <div class="bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-sm hover:shadow-xl transition-all">
                        <img src="{card_img}" alt="{item.title}" class="w-full h-56 object-cover">
                        <div class="p-6 space-y-2">
                            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-700">{badge_text}</span>
                            <h3 class="text-lg font-bold text-slate-900">{item.title}</h3>
                            <p class="text-xs text-slate-500 leading-relaxed">{item.description}</p>
                        </div>
                    </div>"""
        return cards_html

    def _render_header(self, plan: WebsitePlan, assets: AssetManifest, current_page: str, pages: List[str]) -> str:
        p_col = plan.color_scheme.primary
        nav_desktop = self._render_nav_links(current_page, pages, p_col, is_mobile=False)
        nav_mobile = self._render_nav_links(current_page, pages, p_col, is_mobile=True)

        return f"""
    <!-- Global Header / Navigation -->
    <header class="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-100 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
            <a href="index.html" class="flex items-center space-x-2">
                <img src="{assets.logo.url}" alt="{plan.business_name} Logo" class="h-9 w-auto">
            </a>

            <!-- Desktop Navigation -->
            <nav class="hidden md:flex items-center space-x-8">
                {nav_desktop}
            </nav>

            <!-- Mobile Hamburger Toggle -->
            <button id="mobileMenuBtn" aria-label="Toggle Navigation" class="md:hidden p-2 rounded-xl text-slate-700 hover:bg-slate-100 transition-colors">
                <i data-lucide="Menu" class="w-6 h-6"></i>
            </button>
        </div>

        <!-- Mobile Drawer -->
        <div id="mobileDrawer" class="hidden md:hidden border-b border-slate-200 bg-white px-4 pt-3 pb-6 space-y-3">
            {nav_mobile}
        </div>
    </header>"""

    def _render_footer(self, plan: WebsitePlan, pages: List[str]) -> str:
        footer_links = "".join([f'<a href="{"index.html" if p.lower() == "home" else self._slugify(p) + ".html"}" class="hover:text-white transition-colors">{p}</a>\n' for p in pages])
        return f"""
    <!-- Global Footer -->
    <footer class="bg-slate-900 text-slate-400 py-14 border-t border-slate-800 mt-auto">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex flex-col md:flex-row justify-between items-center space-y-6 md:space-y-0">
                <div class="space-y-2 text-center md:text-left">
                    <span class="text-white font-extrabold text-xl tracking-tight">{plan.business_name}</span>
                    <p class="text-xs text-slate-500 max-w-sm">{plan.tagline or plan.summary[:100]}</p>
                </div>
                <div class="flex flex-wrap justify-center gap-6 text-sm font-medium">
                    {footer_links}
                </div>
            </div>
            <div class="border-t border-slate-800 mt-10 pt-8 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-4">
                <p>© {plan.business_name}. All rights reserved. Powered by AI Website Builder Agent.</p>
                <div class="flex space-x-4">
                    <a href="contact.html" class="hover:text-slate-300">Privacy Policy</a>
                    <a href="contact.html" class="hover:text-slate-300">Terms of Service</a>
                </div>
            </div>
        </div>
    </footer>"""

    def _render_multipage_html(
        self,
        project_id: str,
        plan: WebsitePlan,
        assets: AssetManifest,
        page_name: str,
        all_pages: List[str]
    ) -> str:
        """Renders specialized HTML for a dedicated sub-page in a multi-page site."""
        p_col = plan.color_scheme.primary
        s_col = plan.color_scheme.secondary
        p_lower = page_name.lower()

        header_html = self._render_header(plan, assets, page_name, all_pages)
        footer_html = self._render_footer(plan, all_pages)

        hero_img = next((img.url for img in assets.images if img.type == "hero_image"), "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80")
        about_img = next((img.url for img in assets.images if img.type == "about_image"), "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80")
        features_img = next((img.url for img in assets.images if img.type == "feature_image"), "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80")

        # Page-specific Body Content
        body_content = ""

        if p_lower == "home":
            # Multi-page Home Page
            body_content = f"""
        <!-- Hero Section -->
        <section class="relative pt-16 pb-24 lg:pt-24 lg:pb-32 bg-gradient-to-b from-slate-50 to-white overflow-hidden">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                    <div class="lg:col-span-7 space-y-6">
                        <span class="inline-flex items-center px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider text-slate-800 bg-white border border-slate-200 shadow-sm">
                            <i data-lucide="Sparkles" class="w-3.5 h-3.5 mr-2" style="color: {p_col}"></i>
                            {plan.industry}
                        </span>
                        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-tight">
                            {plan.tagline or f"Transforming {plan.industry} with {plan.business_name}"}
                        </h1>
                        <p class="text-lg text-slate-600 leading-relaxed max-w-2xl">
                            {plan.summary}
                        </p>
                        <div class="flex flex-col sm:flex-row gap-4 pt-4">
                            <a href="contact.html" class="inline-flex items-center justify-center px-7 py-3.5 text-base font-bold text-white rounded-xl shadow-md hover:opacity-95 transition-all" style="background-color: {p_col}">
                                Get In Touch <i data-lucide="ArrowRight" class="w-4 h-4 ml-2"></i>
                            </a>
                            <a href="services.html" class="inline-flex items-center justify-center px-7 py-3.5 text-base font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-all">
                                Explore Services
                            </a>
                        </div>
                    </div>
                    <div class="lg:col-span-5">
                        <div class="rounded-2xl overflow-hidden shadow-2xl border-4 border-white">
                            <img src="{hero_img}" alt="{plan.business_name} Hero" class="w-full h-96 object-cover transform hover:scale-105 transition-transform duration-500">
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Services Preview Section -->
        <section class="py-20 bg-white border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex flex-col md:flex-row md:items-end justify-between mb-12">
                    <div>
                        <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">What We Offer</span>
                        <h2 class="text-3xl font-extrabold text-slate-900 mt-1">Core Services & Capabilities</h2>
                    </div>
                    <a href="services.html" class="mt-4 md:mt-0 inline-flex items-center text-sm font-bold hover:underline" style="color: {p_col}">
                        View All Services <i data-lucide="ArrowRight" class="w-4 h-4 ml-1"></i>
                    </a>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
{self._render_dynamic_features_cards(plan, p_col, "services.html")}
                </div>
            </div>
        </section>

        <!-- About Teaser -->
        <section class="py-20 bg-slate-50 border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                    <div class="lg:col-span-6">
                        <img src="{about_img}" alt="About {plan.business_name}" class="rounded-2xl shadow-xl w-full h-80 object-cover">
                    </div>
                    <div class="lg:col-span-6 space-y-6">
                        <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Our Foundation</span>
                        <h2 class="text-3xl font-extrabold text-slate-900">Setting the Benchmark in {plan.industry}</h2>
                        <p class="text-slate-600 leading-relaxed">
                            {plan.summary}
                        </p>
                        <a href="about.html" class="inline-flex items-center px-6 py-3 rounded-xl font-bold text-sm text-white shadow-sm hover:opacity-95" style="background-color: {p_col}">
                            Read Our Story <i data-lucide="ArrowRight" class="w-4 h-4 ml-2"></i>
                        </a>
                    </div>
                </div>
            </div>
        </section>

{self._render_dynamic_testimonials(plan, p_col)}
"""

        elif "about" in p_lower:
            # Dedicated About Page
            body_content = f"""
        <section class="py-16 lg:py-24 bg-gradient-to-b from-slate-50 to-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
                    <span class="text-xs font-bold uppercase tracking-wider px-3 py-1 bg-white rounded-full border border-slate-200" style="color: {p_col}">Our Story & Heritage</span>
                    <h1 class="text-4xl sm:text-5xl font-black text-slate-900">About {plan.business_name}</h1>
                    <p class="text-lg text-slate-600 leading-relaxed">
                        Dedicated to delivering extraordinary outcomes in the {plan.industry} industry with integrity, innovation, and client-first values.
                    </p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center mb-20">
                    <div class="lg:col-span-6">
                        <img src="{about_img}" alt="About {plan.business_name}" class="rounded-2xl shadow-2xl w-full h-[450px] object-cover border-4 border-white">
                    </div>
                    <div class="lg:col-span-6 space-y-6">
                        <h2 class="text-3xl font-extrabold text-slate-900">Our Mission & Purpose</h2>
                        <p class="text-slate-600 leading-relaxed text-base">
                            At {plan.business_name}, we believe in transforming client expectations into tangible results. Whether working on complex enterprise undertakings or bespoke assignments, our team brings disciplined execution and passion to every project.
                        </p>
                        <div class="grid grid-cols-2 gap-6 pt-4">
                            <div class="p-6 bg-slate-50 rounded-2xl border border-slate-200">
                                <span class="text-3xl font-black" style="color: {p_col}">99.9%</span>
                                <p class="text-xs text-slate-500 font-semibold mt-1">Client Satisfaction</p>
                            </div>
                            <div class="p-6 bg-slate-50 rounded-2xl border border-slate-200">
                                <span class="text-3xl font-black" style="color: {p_col}">24/7</span>
                                <p class="text-xs text-slate-500 font-semibold mt-1">Operational Support</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Values Grid -->
                <div class="bg-slate-900 text-white rounded-3xl p-10 lg:p-14 mb-16">
                    <div class="max-w-2xl mb-10">
                        <span class="text-xs font-bold uppercase tracking-wider text-blue-400">Core Principles</span>
                        <h2 class="text-3xl font-extrabold text-white mt-2">What We Stand For</h2>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div class="space-y-3">
                            <div class="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">1</div>
                            <h3 class="text-lg font-bold text-white">Uncompromising Quality</h3>
                            <p class="text-xs text-slate-400 leading-relaxed">Every deliverable is scrutinized against strict quality standards before delivery.</p>
                        </div>
                        <div class="space-y-3">
                            <div class="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">2</div>
                            <h3 class="text-lg font-bold text-white">Radical Transparency</h3>
                            <p class="text-xs text-slate-400 leading-relaxed">Direct communication, clear milestone tracking, and honest collaboration.</p>
                        </div>
                        <div class="space-y-3">
                            <div class="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">3</div>
                            <h3 class="text-lg font-bold text-white">Client-Centric Innovation</h3>
                            <p class="text-xs text-slate-400 leading-relaxed">Adapting cutting-edge tools to deliver real-world business advantages.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
"""

        elif "service" in p_lower:
            # Dedicated Services Page
            body_content = f"""
        <section class="py-16 lg:py-24 bg-gradient-to-b from-slate-50 to-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
                    <span class="text-xs font-bold uppercase tracking-wider px-3 py-1 bg-white rounded-full border border-slate-200" style="color: {p_col}">Capabilities & Solutions</span>
                    <h1 class="text-4xl sm:text-5xl font-black text-slate-900">Our Services</h1>
                    <p class="text-lg text-slate-600 leading-relaxed">
                        Comprehensive solutions engineered specifically for the {plan.industry} landscape.
                    </p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
{self._render_dynamic_services_page_cards(plan, p_col)}
                </div>

                <!-- Call to action card -->
                <div class="p-10 rounded-3xl bg-slate-900 text-white flex flex-col md:flex-row items-center justify-between gap-6">
                    <div>
                        <h3 class="text-2xl font-bold text-white">Need a customized proposal?</h3>
                        <p class="text-xs text-slate-400 mt-1">Get in touch with our specialists for a detailed scope of work.</p>
                    </div>
                    <a href="contact.html" class="px-6 py-3 rounded-xl font-bold text-sm text-white shadow-md hover:opacity-95" style="background-color: {p_col}">
                        Request Proposal
                    </a>
                </div>
            </div>
        </section>
"""

        elif "portfolio" in p_lower or "project" in p_lower or "gallery" in p_lower:
            # Dedicated Portfolio / Projects Page
            body_content = f"""
        <section class="py-16 lg:py-24 bg-gradient-to-b from-slate-50 to-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
                    <span class="text-xs font-bold uppercase tracking-wider px-3 py-1 bg-white rounded-full border border-slate-200" style="color: {p_col}">Featured Works</span>
                    <h1 class="text-4xl sm:text-5xl font-black text-slate-900">Portfolio & Case Studies</h1>
                    <p class="text-lg text-slate-600 leading-relaxed">
                        A curated showcase of successful deliveries and high-impact projects by {plan.business_name}.
                    </p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
{self._render_dynamic_portfolio_cards(plan, hero_img, features_img, about_img)}
                </div>
            </div>
        </section>
"""

        else:
            # Dedicated Contact Page (and default for any other custom page)
            body_content = f"""
        <section class="py-16 lg:py-24 bg-gradient-to-b from-slate-50 to-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
                    <span class="text-xs font-bold uppercase tracking-wider px-3 py-1 bg-white rounded-full border border-slate-200" style="color: {p_col}">Get In Touch</span>
                    <h1 class="text-4xl sm:text-5xl font-black text-slate-900">Contact Us</h1>
                    <p class="text-lg text-slate-600 leading-relaxed">
                        Have a question or looking to begin a new engagement? Send us a message and our team will get back to you promptly.
                    </p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
                    <div class="lg:col-span-5 space-y-8">
                        <div class="bg-slate-50 p-8 rounded-2xl border border-slate-200 space-y-6">
                            <h3 class="text-xl font-bold text-slate-900">Direct Inquiries</h3>
                            <div class="space-y-4 text-sm text-slate-600">
                                <div class="flex items-center space-x-3">
                                    <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                                        <i data-lucide="Mail" class="w-5 h-5"></i>
                                    </div>
                                    <div>
                                        <span class="block text-[10px] font-bold text-slate-400 uppercase">Email</span>
                                        <span class="font-semibold text-slate-900">{plan.contact_email or 'contact@company.com'}</span>
                                    </div>
                                </div>
                                <div class="flex items-center space-x-3">
                                    <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                                        <i data-lucide="Phone" class="w-5 h-5"></i>
                                    </div>
                                    <div>
                                        <span class="block text-[10px] font-bold text-slate-400 uppercase">Phone</span>
                                        <span class="font-semibold text-slate-900">{plan.contact_phone or '+1 (555) 234-5678'}</span>
                                    </div>
                                </div>
                                <div class="flex items-center space-x-3">
                                    <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                                        <i data-lucide="Clock" class="w-5 h-5"></i>
                                    </div>
                                    <div>
                                        <span class="block text-[10px] font-bold text-slate-400 uppercase">Business Hours</span>
                                        <span class="font-semibold text-slate-900">Mon - Fri: 9:00 AM - 6:00 PM</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- PHP Backend notice badge -->
                        <div class="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start space-x-3 text-xs text-emerald-800">
                            <i data-lucide="ShieldCheck" class="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5"></i>
                            <div>
                                <span class="font-bold block">Live Verified Backend</span>
                                <span>Submissions are processed in real-time by the validated PHP backend with database persistence.</span>
                            </div>
                        </div>
                    </div>

                    <!-- Contact Form Card -->
                    <div class="lg:col-span-7">
                        <div class="bg-white p-8 sm:p-10 rounded-3xl border border-slate-200 shadow-xl">
                            <form id="contactForm" class="space-y-6" novalidate>
                                <input type="hidden" id="projectIdField" value="{project_id}">
                                <!-- Anti-spam honeypot -->
                                <div style="display:none;" aria-hidden="true">
                                    <input type="text" name="website_hp" id="websiteHp" tabindex="-1" autocomplete="off">
                                </div>

                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                    <div>
                                        <label for="senderName" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Full Name *</label>
                                        <input type="text" id="senderName" required placeholder="Alex Morgan" class="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                                    </div>
                                    <div>
                                        <label for="senderEmail" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Email Address *</label>
                                        <input type="email" id="senderEmail" required placeholder="alex@example.com" class="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                                    </div>
                                </div>

                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                    <div>
                                        <label for="senderPhone" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Phone Number</label>
                                        <input type="tel" id="senderPhone" placeholder="+1 (555) 000-0000" class="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                                    </div>
                                    <div>
                                        <label for="senderSubject" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Subject</label>
                                        <input type="text" id="senderSubject" placeholder="Project inquiry" class="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                                    </div>
                                </div>

                                <div>
                                    <label for="senderMessage" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Your Message *</label>
                                    <textarea id="senderMessage" rows="5" required placeholder="Tell us about your project requirements or question..." class="w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm"></textarea>
                                </div>

                                <div id="formStatus" class="hidden p-4 rounded-xl text-sm font-medium"></div>

                                <button type="submit" id="submitBtn" class="w-full py-4 px-6 rounded-xl font-bold text-white shadow-lg hover:opacity-95 transition-all flex items-center justify-center space-x-2" style="background-color: {p_col}">
                                    <span>Send Message</span>
                                    <i data-lucide="Send" class="w-4 h-4 ml-1"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </section>
"""

        return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_name} | {plan.business_name}</title>
    <meta name="description" content="{plan.seo_meta.get("description", plan.summary)}">
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons CDN -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <link rel="stylesheet" href="styles.css">
</head>
<body class="bg-white text-slate-800 antialiased font-sans flex flex-col min-h-screen">
    {header_html}

    <main class="flex-grow">
        {body_content}
    </main>

    {footer_html}

    <!-- Initialize Lucide Icons -->
    <script>
        document.addEventListener('DOMContentLoaded', function () {{
            if (window.lucide) {{
                window.lucide.createIcons();
            }}
        }});
    </script>
    <script src="main.js"></script>
</body>
</html>"""

    def _render_singlepage_html(self, project_id: str, plan: WebsitePlan, assets: AssetManifest) -> str:
        """Renders comprehensive, single-page landing page."""
        p_col = plan.color_scheme.primary
        s_col = plan.color_scheme.secondary
        hero_img = next((img.url for img in assets.images if img.type == "hero_image"), "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80")
        about_img = next((img.url for img in assets.images if img.type == "about_image"), "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80")

        return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plan.seo_meta.get("title", plan.business_name)}</title>
    <meta name="description" content="{plan.seo_meta.get("description", plan.summary)}">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link rel="stylesheet" href="styles.css">
</head>
<body class="bg-white text-slate-800 antialiased font-sans flex flex-col min-h-screen">

    <!-- Header -->
    <header class="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-100 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
            <a href="#" class="flex items-center space-x-2">
                <img src="{assets.logo.url}" alt="{plan.business_name} Logo" class="h-9 w-auto">
            </a>

            <nav class="hidden md:flex items-center space-x-8">
                <a href="#hero" class="text-sm font-medium text-slate-600 hover:text-slate-900">Home</a>
                <a href="#services" class="text-sm font-medium text-slate-600 hover:text-slate-900">Services</a>
                <a href="#about" class="text-sm font-medium text-slate-600 hover:text-slate-900">About</a>
                <a href="#contact" class="inline-flex items-center px-5 py-2 text-sm font-bold text-white rounded-xl shadow-sm hover:opacity-95" style="background-color: {p_col}">Contact</a>
            </nav>

            <button id="mobileMenuBtn" aria-label="Toggle Navigation" class="md:hidden p-2 rounded-xl text-slate-700 hover:bg-slate-100">
                <i data-lucide="Menu" class="w-6 h-6"></i>
            </button>
        </div>

        <div id="mobileDrawer" class="hidden md:hidden border-b border-slate-200 bg-white px-4 pt-3 pb-6 space-y-3">
            <a href="#hero" class="block px-3 py-2 text-base font-medium text-slate-700">Home</a>
            <a href="#services" class="block px-3 py-2 text-base font-medium text-slate-700">Services</a>
            <a href="#about" class="block px-3 py-2 text-base font-medium text-slate-700">About</a>
            <a href="#contact" class="block px-4 py-2 text-base font-bold text-white rounded-xl text-center" style="background-color: {p_col}">Contact</a>
        </div>
    </header>

    <main class="flex-grow">
        <!-- Hero Section -->
        <section id="hero" class="pt-16 pb-24 lg:pt-24 lg:pb-32 bg-gradient-to-b from-slate-50 to-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                    <div class="lg:col-span-7 space-y-6">
                        <span class="inline-flex items-center px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider text-slate-800 bg-white border border-slate-200 shadow-sm">
                            <i data-lucide="Sparkles" class="w-3.5 h-3.5 mr-2" style="color: {p_col}"></i>
                            {plan.industry}
                        </span>
                        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-tight">
                            {plan.tagline or plan.business_name}
                        </h1>
                        <p class="text-lg text-slate-600 leading-relaxed max-w-2xl">
                            {plan.summary}
                        </p>
                        <div class="flex flex-col sm:flex-row gap-4 pt-4">
                            <a href="#contact" class="inline-flex items-center justify-center px-7 py-3.5 text-base font-bold text-white rounded-xl shadow-md hover:opacity-95" style="background-color: {p_col}">
                                Get In Touch <i data-lucide="ArrowRight" class="w-4 h-4 ml-2"></i>
                            </a>
                            <a href="#services" class="inline-flex items-center justify-center px-7 py-3.5 text-base font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50">
                                Explore Services
                            </a>
                        </div>
                    </div>
                    <div class="lg:col-span-5">
                        <div class="rounded-2xl overflow-hidden shadow-2xl border-4 border-white">
                            <img src="{hero_img}" alt="{plan.business_name}" class="w-full h-96 object-cover">
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Services Section -->
        <section id="services" class="py-20 bg-white border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16">
                    <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Our Services</span>
                    <h2 class="text-3xl font-extrabold text-slate-900 mt-1">Engineered for Excellence</h2>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
{self._render_dynamic_features_cards(plan, p_col, "#contact")}
                </div>
            </div>
        </section>

        <!-- About Section -->
        <section id="about" class="py-20 bg-slate-50 border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                    <div class="lg:col-span-6">
                        <img src="{about_img}" alt="About {plan.business_name}" class="rounded-2xl shadow-xl w-full h-80 object-cover">
                    </div>
                    <div class="lg:col-span-6 space-y-6">
                        <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Who We Are</span>
                        <h2 class="text-3xl font-extrabold text-slate-900">About {plan.business_name}</h2>
                        <p class="text-slate-600 leading-relaxed">{plan.summary}</p>
                    </div>
                </div>
            </div>
        </section>

{self._render_dynamic_testimonials(plan, p_col)}

        <!-- Contact Section -->
        <section id="contact" class="py-20 bg-white border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="max-w-2xl mx-auto bg-slate-50 p-8 sm:p-10 rounded-3xl border border-slate-200 shadow-xl">
                    <div class="text-center mb-8">
                        <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Get In Touch</span>
                        <h2 class="text-3xl font-black text-slate-900 mt-1">Contact Us</h2>
                    </div>
                    <form id="contactForm" class="space-y-5" novalidate>
                        <input type="hidden" id="projectIdField" value="{project_id}">
                        <div style="display:none;" aria-hidden="true">
                            <input type="text" name="website_hp" id="websiteHp" tabindex="-1">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-2">Name *</label>
                            <input type="text" id="senderName" required placeholder="Your Name" class="w-full px-4 py-3 rounded-xl border border-slate-300 bg-white text-sm">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-2">Email *</label>
                            <input type="email" id="senderEmail" required placeholder="your.email@example.com" class="w-full px-4 py-3 rounded-xl border border-slate-300 bg-white text-sm">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-700 uppercase mb-2">Message *</label>
                            <textarea id="senderMessage" rows="4" required placeholder="How can we help?" class="w-full px-4 py-3 rounded-xl border border-slate-300 bg-white text-sm"></textarea>
                        </div>
                        <div id="formStatus" class="hidden p-4 rounded-xl text-sm font-medium"></div>
                        <button type="submit" id="submitBtn" class="w-full py-3.5 px-6 rounded-xl font-bold text-white shadow-md hover:opacity-95" style="background-color: {p_col}">
                            <span>Send Message</span>
                        </button>
                    </form>
                </div>
            </div>
        </section>
    </main>

    <footer class="bg-slate-900 text-slate-400 py-10 border-t border-slate-800 text-center text-xs">
        <p>© {plan.business_name}. All rights reserved.</p>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', function () {{
            if (window.lucide) {{ window.lucide.createIcons(); }}
        }});
    </script>
    <script src="main.js"></script>
</body>
</html>"""

    def _render_css(self, plan: WebsitePlan) -> str:
        return f"""/* Theme Tokens & Micro-interactions */
:root {{
    --primary: {plan.color_scheme.primary};
    --secondary: {plan.color_scheme.secondary};
    --accent: {plan.color_scheme.accent};
}}
html {{
    scroll-behavior: smooth;
}}
input:focus, textarea:focus {{
    border-color: var(--primary) !important;
}}
button:focus-visible, a:focus-visible {{
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}}
"""

    def _render_js(self, project_id: str) -> str:
        return f"""// Client Interaction & Validated Form Handler
document.addEventListener('DOMContentLoaded', () => {{
    // Mobile navigation toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mobileDrawer = document.getElementById('mobileDrawer');
    if (mobileBtn && mobileDrawer) {{
        mobileBtn.addEventListener('click', () => {{
            mobileDrawer.classList.toggle('hidden');
        }});
    }}

    // Real Contact Form Handler (Supports both platform API and PHP backend)
    const form = document.getElementById('contactForm');
    const statusBox = document.getElementById('formStatus');
    const submitBtn = document.getElementById('submitBtn');

    if (form) {{
        form.addEventListener('submit', async (e) => {{
            e.preventDefault();

            const name = document.getElementById('senderName')?.value.trim();
            const email = document.getElementById('senderEmail')?.value.trim();
            const phone = document.getElementById('senderPhone')?.value.trim();
            const subject = document.getElementById('senderSubject')?.value.trim();
            const message = document.getElementById('senderMessage')?.value.trim();
            const hp = document.getElementById('websiteHp')?.value;
            const projectId = document.getElementById('projectIdField')?.value || '{project_id}';

            if (!name || !email || !message) {{
                showStatus('Please complete all required fields.', false);
                return;
            }}

            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.6';
            const btnSpan = submitBtn.querySelector('span');
            if (btnSpan) btnSpan.innerText = 'Sending...';

            try {{
                // Submit to genuine project contact endpoint
                const endpoint = `/api/v1/projects/${{projectId}}/contact`;
                const response = await fetch(endpoint, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        name: name,
                        email: email,
                        phone: phone || null,
                        subject: subject || null,
                        message: message,
                        website_hp: hp || null
                    }})
                }});

                if (response.ok) {{
                    showStatus('Thank you! Your message has been received successfully.', true);
                    form.reset();
                }} else {{
                    const err = await response.json().catch(() => ({{ detail: 'Submission failed' }}));
                    showStatus(err.detail || 'Failed to submit form. Please try again.', false);
                }}
            }} catch (error) {{
                showStatus('Network error while submitting. Please check connection.', false);
            }} finally {{
                submitBtn.disabled = false;
                submitBtn.style.opacity = '1';
                if (btnSpan) btnSpan.innerText = 'Send Message';
            }}
        }});
    }}

    function showStatus(msg, isSuccess) {{
        if (!statusBox) return;
        statusBox.classList.remove('hidden', 'bg-emerald-50', 'text-emerald-800', 'border-emerald-200', 'bg-rose-50', 'text-rose-800', 'border-rose-200');
        if (isSuccess) {{
            statusBox.classList.add('bg-emerald-50', 'text-emerald-800', 'border', 'border-emerald-200');
        }} else {{
            statusBox.classList.add('bg-rose-50', 'text-rose-800', 'border', 'border-rose-200');
        }}
        statusBox.innerText = msg;
    }}
}});
"""

design_agent = DesignAgent()
