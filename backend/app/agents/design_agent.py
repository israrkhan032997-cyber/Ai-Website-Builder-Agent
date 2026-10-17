import json
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

        # Pure React source files (package.json, vite.config.js, src/App.jsx, src/components/*)
        react_files = self._generate_react_source_files(project_id, plan, website_type, pages_to_build)
        files.extend(react_files)

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

    def _generate_react_source_files(
        self,
        project_id: str,
        plan: WebsitePlan,
        website_type: str,
        pages: List[str]
    ) -> List[CodeFile]:
        is_multi = website_type == "multi-page" or len(pages) > 1
        p_col = plan.color_scheme.primary or "#2563eb"
        s_col = plan.color_scheme.secondary or "#0f172a"
        acc_col = plan.color_scheme.accent or "#38bdf8"
        b_name = plan.business_name
        b_slug = self._slugify(b_name)
        ind = plan.industry or "Professional Services"
        tagline = plan.tagline or f"Premium {ind} Solutions"
        summary = plan.summary or f"Empowering clients with superior {ind} services."
        email = plan.contact_email or f"info@{b_slug}.com"
        phone = plan.contact_phone or "+1 (555) 019-2834"

        files: List[CodeFile] = []

        # 1. package.json
        pkg_json = """{
  "name": "__SLUG__-react-site",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.344.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "vite": "^5.3.1"
  }
}""".replace("__SLUG__", b_slug)
        files.append(CodeFile(path="package.json", content=pkg_json, description="React project dependencies and scripts"))

        # 2. vite.config.js
        vite_config = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
});
"""
        files.append(CodeFile(path="vite.config.js", content=vite_config, description="Vite build configuration"))

        # 3. tailwind.config.js
        tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '__PRIMARY__',
        secondary: '__SECONDARY__',
        accent: '__ACCENT__',
      }
    },
  },
  plugins: [],
}""".replace("__PRIMARY__", p_col).replace("__SECONDARY__", s_col).replace("__ACCENT__", acc_col)
        files.append(CodeFile(path="tailwind.config.js", content=tailwind_config, description="Tailwind CSS theme configuration"))

        # 4. src/index.css
        index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --primary-color: __PRIMARY__;
  --secondary-color: __SECONDARY__;
}

html {
  scroll-behavior: smooth;
  font-family: '__FONT__', system-ui, -apple-system, sans-serif;
}
""".replace("__PRIMARY__", p_col).replace("__SECONDARY__", s_col).replace("__FONT__", plan.typography.body_font or "Inter")
        files.append(CodeFile(path="src/index.css", content=index_css, description="Global Tailwind and typography styles"))

        # 5. src/main.jsx
        main_jsx = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
        files.append(CodeFile(path="src/main.jsx", content=main_jsx, description="React root application entry point"))

        # 6. src/components/Navbar.jsx
        title_map = {
            "home": "Home",
            "about": "About",
            "about-us": "About",
            "services": "Services",
            "portfolio": "Portfolio",
            "projects": "Portfolio",
            "case-study": "Case Studies",
            "case-studies": "Case Studies",
            "contact": "Contact",
            "contact-us": "Contact",
            "pricing": "Pricing",
            "testimonials": "Testimonials",
            "team": "Team",
            "our-team": "Our Team",
            "blog": "Blog",
            "faq": "FAQ",
            "gallery": "Gallery",
            "products": "Products",
            "careers": "Careers",
        }
        multi_nav = []
        single_nav = []
        for p in (pages if pages else ["home"]):
            name = title_map.get(p.lower(), p.replace("-", " ").title())
            multi_nav.append({"name": name, "id": p.lower()})
            single_nav.append({"name": name, "href": f"#{p.lower()}"})

        multi_nav_json = json.dumps(multi_nav)
        single_nav_json = json.dumps(single_nav)

        navbar_jsx = """import React, { useState } from 'react';
import { Menu, X, Sparkles } from 'lucide-react';

export default function Navbar({ activePage, setActivePage, isMultiPage = false }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = isMultiPage ? __MULTI_NAV__ : __SINGLE_NAV__;

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20 items-center">
          <div 
            className="flex items-center gap-3 cursor-pointer" 
            onClick={() => isMultiPage && setActivePage && setActivePage('home')}
          >
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md">
              <Sparkles className="w-5 h-5" />
            </div>
            <span className="font-extrabold text-xl tracking-tight text-slate-900">
              __NAME__
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((item) => (
              isMultiPage ? (
                <button
                  key={item.id}
                  onClick={() => setActivePage(item.id)}
                  className={`text-sm font-semibold transition-colors pb-1 ${
                    activePage === item.id ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {item.name}
                </button>
              ) : (
                <a
                  key={item.name}
                  href={item.href}
                  className="text-sm font-semibold text-slate-600 hover:text-blue-600 transition-colors"
                >
                  {item.name}
                </a>
              )
            ))}

            <button
              onClick={() => isMultiPage ? (setActivePage && setActivePage('contact')) : document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })}
              className="px-5 py-2.5 rounded-xl font-bold text-sm text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-all"
            >
              Get in Touch
            </button>
          </nav>

          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-600 hover:text-slate-900 focus:outline-none"
              aria-label="Toggle Navigation"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden px-4 pt-2 pb-6 border-t border-slate-100 bg-white space-y-2">
          {navLinks.map((item) => (
            isMultiPage ? (
              <button
                key={item.id}
                onClick={() => { setActivePage(item.id); setMobileMenuOpen(false); }}
                className={`block w-full text-left px-3 py-2 rounded-lg text-base font-medium ${
                  activePage === item.id ? 'bg-blue-50 text-blue-700 font-bold' : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                {item.name}
              </button>
            ) : (
              <a
                key={item.name}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-base font-medium text-slate-700 hover:bg-slate-50"
              >
                {item.name}
              </a>
            )
          ))}
        </div>
      )}
    </header>
  );
}
""".replace("__NAME__", b_name).replace("__MULTI_NAV__", multi_nav_json).replace("__SINGLE_NAV__", single_nav_json)
        files.append(CodeFile(path="src/components/Navbar.jsx", content=navbar_jsx, description="React Navbar component"))

        # 7. src/components/Hero.jsx
        hero_jsx = """import React from 'react';
import { ArrowRight, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react';

export default function Hero({ onCtaClick }) {
  return (
    <section id="home" className="relative py-20 lg:py-32 overflow-hidden bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 border border-blue-200/60 text-blue-700 font-semibold text-xs tracking-wide uppercase mb-8 shadow-sm">
          <Sparkles className="w-4 h-4 text-blue-600" />
          <span>__INDUSTRY__ Excellence</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
          __NAME__
        </h1>

        <p className="mt-6 text-xl sm:text-2xl text-slate-600 max-w-3xl mx-auto font-normal leading-relaxed">
          __TAGLINE__
        </p>

        <p className="mt-4 text-base sm:text-lg text-slate-500 max-w-2xl mx-auto">
          __SUMMARY__
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            onClick={onCtaClick}
            className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/25 transition-all inline-flex items-center justify-center gap-2"
          >
            <span>Get Started</span>
            <ArrowRight className="w-5 h-5" />
          </button>
          <a
            href="#about"
            className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-all text-center"
          >
            Learn More
          </a>
        </div>

        <div className="mt-16 grid grid-cols-2 md:grid-cols-3 gap-6 max-w-3xl mx-auto pt-8 border-t border-slate-200/60 text-left">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
            <span className="text-sm font-semibold text-slate-700">Verified Quality</span>
          </div>
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-blue-500 shrink-0" />
            <span className="text-sm font-semibold text-slate-700">Enterprise Standards</span>
          </div>
          <div className="flex items-center gap-3 col-span-2 md:col-span-1">
            <Sparkles className="w-5 h-5 text-amber-500 shrink-0" />
            <span className="text-sm font-semibold text-slate-700">100% Client Focus</span>
          </div>
        </div>
      </div>
    </section>
  );
}
""".replace("__NAME__", b_name).replace("__INDUSTRY__", ind).replace("__TAGLINE__", tagline).replace("__SUMMARY__", summary)
        files.append(CodeFile(path="src/components/Hero.jsx", content=hero_jsx, description="React Hero component"))

        # 8. src/components/Features.jsx
        features_jsx = """import React from 'react';
import { Sparkles, Zap, ShieldCheck, Star, Award, Layers } from 'lucide-react';

export default function Features() {
  const features = [
    {
      title: "Signature __INDUSTRY__ Solutions",
      description: "Engineered specifically for __NAME__ clients to drive superior outcomes with modern standards.",
      icon: Sparkles
    },
    {
      title: "Rapid Execution & Precision",
      description: "Accelerating timelines through disciplined workflows and proven methodologies.",
      icon: Zap
    },
    {
      title: "Dedicated Specialist Advisory",
      description: "Continuous consultation and dedicated specialist oversight at every milestone.",
      icon: ShieldCheck
    },
    {
      title: "Quality Benchmarks",
      description: "Uncompromising focus on high performance, accessibility, and modern responsive design.",
      icon: Award
    },
    {
      title: "Customized Architecture",
      description: "Tailored to your specific organizational workflows and strategic priorities.",
      icon: Layers
    },
    {
      title: "Client-Centric Philosophy",
      description: "Focused transparent communication and verified results at every project phase.",
      icon: Star
    }
  ];

  return (
    <section id="services" className="py-24 bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-blue-600 font-bold text-xs uppercase tracking-widest bg-blue-50 px-3.5 py-1.5 rounded-full border border-blue-200/60">
            What We Deliver
          </span>
          <h2 className="mt-4 text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Comprehensive Capabilities for Every Milestone
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Explore our curated suite of professional capabilities designed to elevate your standard of service.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="p-8 bg-white rounded-2xl border border-slate-200/70 shadow-sm hover:shadow-md transition-all">
                <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-5">
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">{item.title}</h3>
                <p className="text-slate-600 leading-relaxed text-sm">{item.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
""".replace("__NAME__", b_name).replace("__INDUSTRY__", ind)
        files.append(CodeFile(path="src/components/Features.jsx", content=features_jsx, description="React Features and Capabilities component"))

        # 9. src/components/Contact.jsx
        contact_jsx = """import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Contact({ projectId = '__PROJECT_ID__' }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: '',
    website_hp: ''
  });
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.message) {
      setStatus({ type: 'error', message: 'Please complete all required fields.' });
      return;
    }}

    setLoading(true);
    setStatus(null);

    try {
      const res = await fetch(`/api/v1/projects/${projectId}/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (res.ok) {
        setStatus({ type: 'success', message: 'Thank you! Your message has been received successfully.' });
        setFormData({ name: '', email: '', phone: '', subject: '', message: '', website_hp: '' });
      } else {
        const err = await res.json().catch(() => ({ detail: 'Submission failed' }));
        setStatus({ type: 'error', message: err.detail || 'Failed to submit form. Please try again.' });
      }
    } catch (error) {
      setStatus({ type: 'error', message: 'Network error while submitting. Please check connection.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="contact" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <div className="lg:col-span-5 space-y-8">
            <div>
              <span className="text-blue-600 font-bold text-xs uppercase tracking-widest bg-blue-50 px-3.5 py-1.5 rounded-full border border-blue-200/60">
                Contact Us
              </span>
              <h2 className="mt-4 text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
                Let's Start a Conversation
              </h2>
              <p className="mt-4 text-slate-600 leading-relaxed">
                Reach out to our team today to discuss your vision, request a customized proposal, or schedule a consultation.
              </p>
            </div>

            <div className="space-y-6 pt-4">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Email Inquiries</h4>
                  <p className="text-slate-600 text-sm mt-1">__EMAIL__</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <Phone className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Phone Support</h4>
                  <p className="text-slate-600 text-sm mt-1">__PHONE__</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <MapPin className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">Headquarters</h4>
                  <p className="text-slate-600 text-sm mt-1">Global Services Network</p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-7 bg-slate-50 p-8 sm:p-10 rounded-3xl border border-slate-200/70">
            <h3 className="text-2xl font-bold text-slate-900 mb-6">Send an Inquiry</h3>

            {status && (
              <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 border text-sm font-medium ${
                status.type === 'success' 
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200' 
                  : 'bg-rose-50 text-rose-800 border-rose-200'
              }`}>
                {status.type === 'success' ? <CheckCircle2 className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
                <span>{status.message}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <input type="text" name="website_hp" value={formData.website_hp} onChange={handleChange} className="hidden" tabIndex={-1} autoComplete="off" />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Full Name *</label>
                  <input
                    type="text"
                    name="name"
                    required
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Jane Doe"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Email Address *</label>
                  <input
                    type="email"
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="jane@example.com"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Phone Number</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+1 (555) 000-0000"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Subject</label>
                  <input
                    type="text"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    placeholder="Project Inquiry"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Message *</label>
                <textarea
                  name="message"
                  required
                  rows={4}
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Tell us about your requirements..."
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 text-sm resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-60"
              >
                <Send className="w-4 h-4" />
                <span>{loading ? 'Sending Message...' : 'Submit Inquiry'}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}
""".replace("__PROJECT_ID__", project_id).replace("__EMAIL__", email).replace("__PHONE__", phone)
        files.append(CodeFile(path="src/components/Contact.jsx", content=contact_jsx, description="React Contact form component"))

        # 10. src/components/Footer.jsx
        footer_jsx = """import React from 'react';
import { Sparkles, Mail, Phone } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-950 text-slate-400 py-16 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white">
                <Sparkles className="w-5 h-5" />
              </div>
              <span className="font-extrabold text-xl text-white tracking-tight">__NAME__</span>
            </div>
            <p className="text-slate-400 max-w-sm text-sm leading-relaxed">
              __TAGLINE__. Dedicated to delivering excellence, precision, and reliable service.
            </p>
          </div>

          <div>
            <h4 className="text-white font-bold text-sm tracking-wider uppercase mb-4">Direct Contact</h4>
            <ul className="space-y-2.5 text-sm">
              <li className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-blue-400" />
                <span>__EMAIL__</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-blue-400" />
                <span>__PHONE__</span>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-bold text-sm tracking-wider uppercase mb-4">Platform</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Powered by AI Website Builder Agent. Built with modern React and Tailwind CSS.
            </p>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-slate-800/80 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-4">
          <p>© {new Date().getFullYear()} __NAME__. All rights reserved.</p>
          <div className="flex gap-6">
            <span>Privacy Policy</span>
            <span>Terms of Service</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
""".replace("__NAME__", b_name).replace("__TAGLINE__", tagline).replace("__EMAIL__", email).replace("__PHONE__", phone)
        files.append(CodeFile(path="src/components/Footer.jsx", content=footer_jsx, description="React Footer component"))

        # 11. Multi-page components or Single-page App.jsx
        if is_multi:
            # Multi-page pages
            home_page_jsx = """import React from 'react';
import Hero from '../components/Hero';
import Features from '../components/Features';
import Contact from '../components/Contact';

export default function HomePage({ setActivePage }) {
  return (
    <main>
      <Hero onCtaClick={() => setActivePage('services')} />
      <Features />
      <div className="py-16 bg-blue-600 text-white text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-3xl font-extrabold mb-4">Ready to Transform Your __INDUSTRY__ Experience?</h2>
          <p className="text-blue-100 mb-8 max-w-2xl mx-auto">Discover how __NAME__ partners with you to achieve measurable success.</p>
          <button onClick={() => setActivePage('contact')} className="px-8 py-3.5 bg-white text-blue-600 rounded-xl font-bold hover:bg-blue-50 transition-all shadow-md">
            Connect With Us Today
          </button>
        </div>
      </div>
      <Contact />
    </main>
  );
}
""".replace("__NAME__", b_name).replace("__INDUSTRY__", ind)
            files.append(CodeFile(path="src/pages/Home.jsx", content=home_page_jsx, description="React Home page"))

            about_page_jsx = """import React from 'react';
import { CheckCircle2, Target, Users } from 'lucide-react';

export default function AboutPage() {
  return (
    <main className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <span className="text-blue-600 font-bold text-xs uppercase tracking-widest bg-blue-50 px-3.5 py-1.5 rounded-full border border-blue-200/60">
            About Our Company
          </span>
          <h1 className="mt-4 text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            The Story Behind __NAME__
          </h1>
          <p className="mt-4 text-xl text-slate-600 leading-relaxed">
            __SUMMARY__
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center my-16">
          <div className="space-y-6">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              Committed to Distinction in __INDUSTRY__
            </h2>
            <p className="text-slate-600 leading-relaxed">
              Founded on the pillars of integrity, technological excellence, and client empowerment, __NAME__ has consistently redefined performance benchmarks across the sector.
            </p>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="font-semibold text-slate-700">Client-First Methodology</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="font-semibold text-slate-700">Dedicated Subject Specialists</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="font-semibold text-slate-700">Transparent Accountability</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-100 p-8 rounded-3xl border border-slate-200">
            <div className="grid grid-cols-2 gap-6 text-center">
              <div className="p-6 bg-white rounded-2xl shadow-sm">
                <Target className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                <div className="text-3xl font-extrabold text-slate-900">100%</div>
                <div className="text-xs text-slate-500 font-semibold uppercase mt-1">Delivery Focus</div>
              </div>
              <div className="p-6 bg-white rounded-2xl shadow-sm">
                <Users className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                <div className="text-3xl font-extrabold text-slate-900">24/7</div>
                <div className="text-xs text-slate-500 font-semibold uppercase mt-1">Direct Advisory</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
""".replace("__NAME__", b_name).replace("__INDUSTRY__", ind).replace("__SUMMARY__", summary)
            files.append(CodeFile(path="src/pages/About.jsx", content=about_page_jsx, description="React About page"))

            services_page_jsx = """import React from 'react';
import Features from '../components/Features';

export default function ServicesPage() {
  return (
    <main>
      <div className="bg-slate-900 text-white py-20 text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Our Services & Solutions</h1>
          <p className="mt-4 text-lg text-slate-300 max-w-2xl mx-auto">
            Comprehensive services tailored to meet the dynamic needs of __INDUSTRY__ leaders.
          </p>
        </div>
      </div>
      <Features />
    </main>
  );
}
""".replace("__INDUSTRY__", ind)
            files.append(CodeFile(path="src/pages/Services.jsx", content=services_page_jsx, description="React Services page"))

            portfolio_page_jsx = """import React from 'react';
import { ExternalLink } from 'lucide-react';

export default function PortfolioPage() {
  const projects = [
    { title: "Enterprise Initiative Alpha", category: "__INDUSTRY__", desc: "Comprehensive transformation delivering superior performance and measurable ROI." },
    { title: "Digital Optimization Platform", category: "Innovation", desc: "Modernized infrastructure designed for rapid scaling and operational efficiency." },
    { title: "Strategic Advisory Program", category: "Consulting", desc: "Long-term partnership driving strategic differentiation and stakeholder value." }
  ];

  return (
    <main className="py-20 bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-blue-600 font-bold text-xs uppercase tracking-widest bg-blue-50 px-3.5 py-1.5 rounded-full border border-blue-200/60">
            Case Studies
          </span>
          <h1 className="mt-4 text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            Featured Projects & Milestones
          </h1>
          <p className="mt-4 text-slate-600">
            A selection of benchmark work delivered by __NAME__.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {projects.map((p, i) => (
            <div key={i} className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm hover:shadow-md transition-all">
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider bg-blue-50 px-2.5 py-1 rounded-md">{p.category}</span>
              <h3 className="text-xl font-bold text-slate-900 mt-4 mb-2">{p.title}</h3>
              <p className="text-slate-600 text-sm leading-relaxed mb-6">{p.desc}</p>
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-blue-600 font-semibold text-sm">
                <span>View Details</span>
                <ExternalLink className="w-4 h-4" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
""".replace("__NAME__", b_name).replace("__INDUSTRY__", ind)
            files.append(CodeFile(path="src/pages/Portfolio.jsx", content=portfolio_page_jsx, description="React Portfolio page"))

            contact_page_jsx = """import React from 'react';
import Contact from '../components/Contact';

export default function ContactPage() {
  return (
    <main>
      <div className="bg-slate-900 text-white py-16 text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-4xl font-extrabold">Connect With Our Team</h1>
          <p className="mt-2 text-slate-300">We respond promptly to all project consultations and inquiries.</p>
        </div>
      </div>
      <Contact />
    </main>
  );
}
"""
            files.append(CodeFile(path="src/pages/Contact.jsx", content=contact_page_jsx, description="React Contact page"))

            case_study_page_jsx = """import React from 'react';
import { Target, CheckCircle2, TrendingUp, Award, ArrowRight } from 'lucide-react';

export default function CaseStudyPage() {
  const studies = [
    {
      title: "Enterprise Digital Acceleration",
      client: "Global Tech Enterprises",
      metric: "+320% Efficiency",
      challenge: "Legacy architecture hindering real-time cross-platform synchronization and scale.",
      solution: "Architected high-throughput cloud infrastructure and reactive micro-frontends with zero system downtime.",
      outcome: "Exceeded SLA targets and reduced operational response latency from 1.2s to 42ms."
    },
    {
      title: "High-Performance Cloud Infrastructure",
      client: "Apex Financial Partners",
      metric: "99.999% Uptime",
      challenge: "Demanding strict regulatory compliance alongside sub-millisecond transaction processing.",
      solution: "Engineered isolated deterministic data pipelines with automated failover replication.",
      outcome: "Processed 10M+ daily transactions flawlessly with industry-benchmark security compliance."
    },
    {
      title: "Next-Gen Client Experience Transformation",
      client: "Vanguard Modern Studio",
      metric: "4.9/5 CSAT",
      challenge: "Fragmented customer onboarding resulting in high conversion friction.",
      solution: "Redesigned complete interactive digital workflow with personalized automated journeys.",
      outcome: "Achieved double-digit conversion surge within 30 days post-launch."
    }
  ];

  return (
    <main className="py-20 bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-blue-600 font-bold text-xs uppercase tracking-widest bg-blue-50 px-3.5 py-1.5 rounded-full border border-blue-200/60">
            Case Studies & Proven Outcomes
          </span>
          <h1 className="mt-4 text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            Measurable Results for __NAME__ Partners
          </h1>
          <p className="mt-4 text-slate-600 text-lg">
            Detailed breakdowns of high-impact engineering, strategy, and execution milestones.
          </p>
        </div>

        <div className="space-y-10 max-w-5xl mx-auto">
          {studies.map((item, idx) => (
            <div key={idx} className="bg-white rounded-3xl p-8 sm:p-10 border border-slate-200 shadow-sm hover:shadow-md transition-all">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
                <div>
                  <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">{item.client}</span>
                  <h3 className="text-2xl font-bold text-slate-900 mt-1">{item.title}</h3>
                </div>
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 rounded-xl font-bold text-sm border border-emerald-200/60 self-start sm:self-auto">
                  <TrendingUp className="w-4 h-4" />
                  <span>{item.metric}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Challenge</h4>
                  <p className="text-slate-600 text-sm leading-relaxed">{item.challenge}</p>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Solution</h4>
                  <p className="text-slate-600 text-sm leading-relaxed">{item.solution}</p>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Outcome</h4>
                  <p className="text-slate-600 text-sm leading-relaxed">{item.outcome}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
""".replace("__NAME__", b_name)
            files.append(CodeFile(path="src/pages/CaseStudy.jsx", content=case_study_page_jsx, description="React Case Studies page"))

            custom_page_jsx = """import React from 'react';
import { Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';

export default function CustomPage({ title = "Details", setActivePage }) {
  return (
    <main className="py-20 bg-white min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-blue-600 font-bold text-xs uppercase tracking-widest bg-blue-50 px-3.5 py-1.5 rounded-full border border-blue-200/60">
            __NAME__ · Overview
          </span>
          <h1 className="mt-4 text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            {title}
          </h1>
          <p className="mt-4 text-lg text-slate-600">
            Dedicated information and premium resources from __NAME__.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 my-12">
          <div className="bg-slate-50 p-8 rounded-2xl border border-slate-200">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center mb-4">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Strategic Focus</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Every detail is calibrated to deliver premier value and clear business outcomes.
            </p>
          </div>
          <div className="bg-slate-50 p-8 rounded-2xl border border-slate-200">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center mb-4">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Verified Excellence</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Adhering to high industry standards and rigorous quality assurance.
            </p>
          </div>
          <div className="bg-slate-50 p-8 rounded-2xl border border-slate-200">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center mb-4">
              <ArrowRight className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Continuous Support</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Direct access to our specialized team whenever you need advisory.
            </p>
          </div>
        </div>

        <div className="text-center pt-8">
          <button
            onClick={() => setActivePage && setActivePage('contact')}
            className="px-8 py-4 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 shadow-lg shadow-blue-500/25 transition-all inline-flex items-center gap-2"
          >
            <span>Connect With Our Team</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </main>
  );
}
""".replace("__NAME__", b_name)
            files.append(CodeFile(path="src/pages/CustomPage.jsx", content=custom_page_jsx, description="React Generic Custom Page component"))

            # Multi-page App.jsx
            app_jsx = """import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomePage from './pages/Home';
import AboutPage from './pages/About';
import ServicesPage from './pages/Services';
import PortfolioPage from './pages/Portfolio';
import CaseStudyPage from './pages/CaseStudy';
import ContactPage from './pages/Contact';
import CustomPage from './pages/CustomPage';

export default function App() {
  const [activePage, setActivePage] = useState('home');

  const renderPage = () => {
    switch (activePage) {
      case 'about':
      case 'about-us':
        return <AboutPage />;
      case 'services':
        return <ServicesPage />;
      case 'portfolio':
      case 'projects':
        return <PortfolioPage />;
      case 'case-study':
      case 'case-studies':
        return <CaseStudyPage />;
      case 'contact':
      case 'contact-us':
        return <ContactPage />;
      case 'home':
        return <HomePage setActivePage={setActivePage} />;
      default:
        return <CustomPage title={activePage.replace('-', ' ').toUpperCase()} setActivePage={setActivePage} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white text-slate-900 antialiased selection:bg-blue-500 selection:text-white">
      <Navbar activePage={activePage} setActivePage={setActivePage} isMultiPage={true} />
      <div className="flex-1">
        {renderPage()}
      </div>
      <Footer />
    </div>
  );
}
"""
            files.append(CodeFile(path="src/App.jsx", content=app_jsx, description="Multi-page React App router component"))

        else:
            # Single-page App.jsx
            app_jsx = """import React from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Features from './components/Features';
import Contact from './components/Contact';
import Footer from './components/Footer';

export default function App() {
  const scrollToContact = () => {
    const el = document.getElementById('contact');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col bg-white text-slate-900 antialiased selection:bg-blue-500 selection:text-white">
      <Navbar activePage="home" isMultiPage={false} />
      <main className="flex-1">
        <Hero onCtaClick={scrollToContact} />
        <section id="about" className="py-20 bg-slate-50 border-t border-b border-slate-100">
          <div className="max-w-4xl mx-auto px-4 text-center">
            <span className="text-blue-600 font-bold text-xs uppercase tracking-widest bg-blue-50 px-3.5 py-1.5 rounded-full border border-blue-200/60">
              Our Vision
            </span>
            <h2 className="mt-4 text-3xl font-extrabold text-slate-900">Built to Accelerate Your Success</h2>
            <p className="mt-4 text-lg text-slate-600 leading-relaxed">
              __SUMMARY__
            </p>
          </div>
        </section>
        <Features />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}
""".replace("__SUMMARY__", summary)
            files.append(CodeFile(path="src/App.jsx", content=app_jsx, description="Single-page React App component"))

        return files

design_agent = DesignAgent()

