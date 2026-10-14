import logging
from typing import Dict, List, Optional
from backend.app.schemas.agent import WebsitePlan, AssetManifest, CodeFile
from backend.app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)

class DesignAgent:
    """
    Design Agent:
    - Generates clean, responsive, production-ready frontend code (HTML, CSS, JS).
    - Implements modern design patterns tailored to the business brand.
    - Assembles complete component sections (Navbar, Hero, Features, About, Testimonials, Pricing, Contact, Footer).
    - Applies natural language design modifications accurately.
    """

    AGENT_NAME = "Design Agent"

    def generate_website_bundle(
        self,
        project_id: str,
        plan: WebsitePlan,
        assets: AssetManifest
    ) -> List[CodeFile]:
        """
        Produces a complete, responsive frontend bundle:
        - index.html (semantic, accessible, Tailwind CSS styled, Lucide icons)
        - styles.css (design tokens, subtle animations, typography)
        - main.js (mobile navigation, interactions, client form submission)
        """
        html_content = self._render_html(project_id, plan, assets)
        css_content = self._render_css(plan)
        js_content = self._render_js(project_id)

        return [
            CodeFile(path="index.html", content=html_content, description="Main website entrypoint"),
            CodeFile(path="styles.css", content=css_content, description="Custom styling and design tokens"),
            CodeFile(path="main.js", content=js_content, description="Interactive client behaviors and form handling")
        ]

    def _render_html(self, project_id: str, plan: WebsitePlan, assets: AssetManifest) -> str:
        """Renders comprehensive, modern HTML5 document."""
        p_col = plan.color_scheme.primary
        s_col = plan.color_scheme.secondary
        a_col = plan.color_scheme.accent

        # Find section images
        hero_img = next((img.url for img in assets.images if img.type == "hero_image"), "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80")
        about_img = next((img.url for img in assets.images if img.type == "about_image"), "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80")

        # Build Navigation links
        nav_desktop = ""
        nav_mobile = ""
        for item in plan.navigation:
            if item.is_cta:
                nav_desktop += f'<a href="{item.href}" class="inline-flex items-center justify-center px-5 py-2.5 text-sm font-semibold text-white rounded-lg shadow-sm hover:opacity-95 transition-all" style="background-color: {p_col}">{item.label}</a>'
                nav_mobile += f'<a href="{item.href}" class="block px-4 py-2 text-base font-semibold text-white rounded-lg text-center" style="background-color: {p_col}">{item.label}</a>'
            else:
                nav_desktop += f'<a href="{item.href}" class="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">{item.label}</a>'
                nav_mobile += f'<a href="{item.href}" class="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50">{item.label}</a>'

        # Build Features Section Items
        features_spec = next((s for s in plan.sections if s.type == "features"), None)
        features_html = ""
        if features_spec and features_spec.items:
            for item in features_spec.items:
                badge_html = f'<span class="inline-block px-2.5 py-0.5 mb-3 text-xs font-semibold rounded-full bg-blue-50 text-blue-700">{item.badge}</span>' if item.badge else ''
                features_html += f"""
                <div class="relative p-8 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                    <div class="w-12 h-12 flex items-center justify-center rounded-xl mb-5" style="background-color: {p_col}15; color: {p_col};">
                        <i data-lucide="{item.icon or 'Sparkles'}" class="w-6 h-6"></i>
                    </div>
                    {badge_html}
                    <h3 class="text-xl font-bold text-slate-900 mb-2">{item.title}</h3>
                    <p class="text-slate-600 leading-relaxed text-sm">{item.description}</p>
                </div>"""

        # Build Testimonials Section Items
        test_spec = next((s for s in plan.sections if s.type == "testimonials"), None)
        testimonials_html = ""
        if test_spec and test_spec.items:
            for item in test_spec.items:
                testimonials_html += f"""
                <div class="p-8 bg-slate-50 rounded-2xl border border-slate-100 flex flex-col justify-between">
                    <div>
                        <div class="flex items-center space-x-1 text-amber-400 mb-4">
                            <i data-lucide="Star" class="w-4 h-4 fill-current"></i>
                            <i data-lucide="Star" class="w-4 h-4 fill-current"></i>
                            <i data-lucide="Star" class="w-4 h-4 fill-current"></i>
                            <i data-lucide="Star" class="w-4 h-4 fill-current"></i>
                            <i data-lucide="Star" class="w-4 h-4 fill-current"></i>
                        </div>
                        <p class="text-slate-700 italic text-sm mb-6 leading-relaxed">"{item.description}"</p>
                    </div>
                    <div class="border-t border-slate-200/60 pt-4">
                        <p class="font-bold text-slate-900 text-sm">{item.title}</p>
                        <p class="text-xs text-slate-500">{item.badge or 'Verified Client'}</p>
                    </div>
                </div>"""

        # Build Pricing Section Items
        pricing_spec = next((s for s in plan.sections if s.type == "pricing"), None)
        pricing_html = ""
        if pricing_spec and pricing_spec.items:
            for idx, item in enumerate(pricing_spec.items):
                is_featured = idx == 1
                border_cls = f"ring-2 ring-offset-2" if is_featured else "border border-slate-200"
                ring_style = f"ring-color: {p_col};" if is_featured else ""
                pricing_html += f"""
                <div class="p-8 bg-white rounded-2xl shadow-sm flex flex-col justify-between {border_cls}" style="{ring_style}">
                    <div>
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-bold text-slate-900">{item.title}</h3>
                            {f'<span class="text-xs px-2.5 py-1 rounded-full font-semibold text-white" style="background-color: {p_col}">Popular</span>' if is_featured else ''}
                        </div>
                        <div class="mb-4">
                            <span class="text-4xl font-extrabold text-slate-900">{item.badge or '$99/mo'}</span>
                        </div>
                        <p class="text-sm text-slate-600 mb-6">{item.description}</p>
                        <ul class="space-y-3 text-sm text-slate-600 mb-8">
                            <li class="flex items-center"><i data-lucide="Check" class="w-4 h-4 mr-2 text-emerald-500"></i> Full platform access</li>
                            <li class="flex items-center"><i data-lucide="Check" class="w-4 h-4 mr-2 text-emerald-500"></i> Standard integrations</li>
                            <li class="flex items-center"><i data-lucide="Check" class="w-4 h-4 mr-2 text-emerald-500"></i> Priority email support</li>
                        </ul>
                    </div>
                    <a href="#contact" class="block w-full text-center py-2.5 px-4 rounded-lg font-semibold text-sm transition-all {'text-white' if is_featured else 'text-slate-800 bg-slate-100 hover:bg-slate-200'}" style="{'background-color: ' + p_col if is_featured else ''}">Choose {item.title}</a>
                </div>"""

        # Hero Spec
        hero_spec = next((s for s in plan.sections if s.type == "hero"), None)
        hero_title = hero_spec.title if hero_spec else plan.business_name
        hero_sub = hero_spec.subtitle if hero_spec else plan.summary

        # About Spec
        about_spec = next((s for s in plan.sections if s.type == "about"), None)
        about_title = about_spec.title if about_spec else f"About {plan.business_name}"
        about_sub = about_spec.subtitle if about_spec else plan.summary

        # Contact Spec
        contact_spec = next((s for s in plan.sections if s.type == "contact"), None)
        contact_title = contact_spec.title if contact_spec else "Get In Touch"
        contact_sub = contact_spec.subtitle if contact_spec else "Send us a message and our team will get back to you shortly."

        html = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plan.seo_meta.get("title", plan.business_name)}</title>
    <meta name="description" content="{plan.seo_meta.get("description", plan.summary)}">
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons CDN -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <link rel="stylesheet" href="styles.css">
</head>
<body class="bg-white text-slate-800 antialiased font-sans flex flex-col min-h-screen">

    <!-- Header / Navbar -->
    <header class="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <a href="#" class="flex items-center space-x-2">
                    <img src="{assets.logo.url}" alt="{plan.business_name} Logo" class="h-9 w-auto">
                </a>
            </div>

            <!-- Desktop Nav -->
            <nav class="hidden md:flex items-center space-x-8">
                {nav_desktop}
            </nav>

            <!-- Mobile Hamburger Button -->
            <button id="mobileMenuBtn" aria-label="Toggle Navigation" class="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100">
                <i data-lucide="Menu" class="w-6 h-6"></i>
            </button>
        </div>

        <!-- Mobile Drawer -->
        <div id="mobileDrawer" class="hidden md:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-6 space-y-3">
            {nav_mobile}
        </div>
    </header>

    <main class="flex-grow">
        <!-- Hero Section -->
        <section id="hero" class="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28 bg-gradient-to-b from-slate-50 to-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                    <div class="lg:col-span-7 space-y-6">
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider text-slate-800 bg-white border border-slate-200 shadow-sm">
                            <i data-lucide="Sparkles" class="w-3.5 h-3.5 mr-1.5" style="color: {p_col}"></i>
                            {hero_spec.badge if hero_spec and hero_spec.badge else plan.industry}
                        </span>
                        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
                            {hero_title}
                        </h1>
                        <p class="text-lg sm:text-xl text-slate-600 leading-relaxed max-w-2xl">
                            {hero_sub}
                        </p>
                        <div class="flex flex-col sm:flex-row gap-4 pt-4">
                            <a href="#contact" class="inline-flex items-center justify-center px-7 py-3.5 text-base font-semibold text-white rounded-xl shadow-md hover:opacity-95 transition-all" style="background-color: {p_col}">
                                Get In Touch <i data-lucide="ArrowRight" class="w-4 h-4 ml-2"></i>
                            </a>
                            <a href="#features" class="inline-flex items-center justify-center px-7 py-3.5 text-base font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-all">
                                Explore Services
                            </a>
                        </div>
                    </div>
                    <div class="lg:col-span-5">
                        <div class="relative mx-auto rounded-2xl overflow-hidden shadow-2xl border-4 border-white">
                            <img src="{hero_img}" alt="{plan.business_name} Hero" class="w-full h-80 sm:h-96 object-cover transform hover:scale-105 transition-transform duration-500">
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features / Capabilities Section -->
        <section id="features" class="py-20 bg-white border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16">
                    <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">{features_spec.badge if features_spec and features_spec.badge else "Capabilities"}</span>
                    <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900 mt-2 mb-4">{features_spec.title if features_spec else "Core Capabilities"}</h2>
                    <p class="text-slate-600">{features_spec.subtitle if features_spec else "Purpose-built solutions tailored to your unique objectives."}</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {features_html}
                </div>
            </div>
        </section>

        <!-- About Section -->
        <section id="about" class="py-20 bg-slate-50 border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                    <div class="lg:col-span-6">
                        <img src="{about_img}" alt="About {plan.business_name}" class="rounded-2xl shadow-xl w-full h-96 object-cover">
                    </div>
                    <div class="lg:col-span-6 space-y-6">
                        <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Our Mission</span>
                        <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900">{about_title}</h2>
                        <p class="text-slate-600 leading-relaxed">{about_sub}</p>
                        <div class="grid grid-cols-2 gap-6 pt-4">
                            <div class="p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                                <p class="text-3xl font-extrabold text-slate-900" style="color: {p_col}">99.9%</p>
                                <p class="text-xs text-slate-500 font-medium mt-1">Operational Reliability</p>
                            </div>
                            <div class="p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                                <p class="text-3xl font-extrabold text-slate-900" style="color: {p_col}">100+</p>
                                <p class="text-xs text-slate-500 font-medium mt-1">Enterprise Partners</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Testimonials Section -->
        <section id="testimonials" class="py-20 bg-white border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16">
                    <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Testimonials</span>
                    <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900 mt-2 mb-4">{test_spec.title if test_spec else "What Clients Say"}</h2>
                    <p class="text-slate-600">{test_spec.subtitle if test_spec else "Feedback from organizations that rely on our expertise."}</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
                    {testimonials_html}
                </div>
            </div>
        </section>

        <!-- Pricing Section -->
        <section id="pricing" class="py-20 bg-slate-50 border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center max-w-3xl mx-auto mb-16">
                    <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Transparent Pricing</span>
                    <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900 mt-2 mb-4">{pricing_spec.title if pricing_spec else "Plans & Packages"}</h2>
                    <p class="text-slate-600">{pricing_spec.subtitle if pricing_spec else "Straightforward tiers designed for transparent value."}</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                    {pricing_html}
                </div>
            </div>
        </section>

        <!-- Interactive Contact Section with Functional Submission -->
        <section id="contact" class="py-20 bg-white border-t border-slate-100">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
                    <div class="lg:col-span-5 space-y-6">
                        <span class="text-xs font-bold uppercase tracking-wider" style="color: {p_col}">Direct Inquiries</span>
                        <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900">{contact_title}</h2>
                        <p class="text-slate-600">{contact_sub}</p>
                        <div class="space-y-4 pt-4 text-sm text-slate-600">
                            <div class="flex items-center space-x-3">
                                <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-slate-100 text-slate-700">
                                    <i data-lucide="Mail" class="w-5 h-5"></i>
                                </div>
                                <span>{plan.contact_email or "contact@company.com"}</span>
                            </div>
                            <div class="flex items-center space-x-3">
                                <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-slate-100 text-slate-700">
                                    <i data-lucide="Phone" class="w-5 h-5"></i>
                                </div>
                                <span>{plan.contact_phone or "+1 (555) 019-2834"}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Live Contact Form Component -->
                    <div class="lg:col-span-7">
                        <div class="bg-slate-50 p-8 sm:p-10 rounded-2xl border border-slate-200 shadow-sm">
                            <form id="contactForm" class="space-y-6" novalidate>
                                <input type="hidden" id="projectIdField" value="{project_id}">
                                <!-- Anti-spam honeypot -->
                                <div style="display:none;" aria-hidden="true">
                                    <input type="text" name="website_hp" id="websiteHp" tabindex="-1" autocomplete="off">
                                </div>

                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                    <div>
                                        <label for="senderName" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Your Name *</label>
                                        <input type="text" id="senderName" required placeholder="Jane Doe" class="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                                    </div>
                                    <div>
                                        <label for="senderEmail" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Email Address *</label>
                                        <input type="email" id="senderEmail" required placeholder="jane@example.com" class="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                                    </div>
                                </div>

                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                    <div>
                                        <label for="senderPhone" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Phone Number</label>
                                        <input type="tel" id="senderPhone" placeholder="+1 (555) 000-0000" class="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                                    </div>
                                    <div>
                                        <label for="senderSubject" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Subject</label>
                                        <input type="text" id="senderSubject" placeholder="Project inquiry" class="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm">
                                    </div>
                                </div>

                                <div>
                                    <label for="senderMessage" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Your Message *</label>
                                    <textarea id="senderMessage" rows="4" required placeholder="Tell us about your project or inquiry..." class="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm"></textarea>
                                </div>

                                <!-- Live Status Notification Banner -->
                                <div id="formStatus" class="hidden p-4 rounded-lg text-sm font-medium"></div>

                                <button type="submit" id="submitBtn" class="w-full py-3.5 px-6 rounded-xl font-bold text-white shadow-md hover:opacity-95 transition-all flex items-center justify-center space-x-2" style="background-color: {p_col}">
                                    <span>Send Message</span>
                                    <i data-lucide="Send" class="w-4 h-4 ml-1"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                <div class="flex items-center space-x-3">
                    <span class="text-white font-bold text-lg">{plan.business_name}</span>
                </div>
                <div class="flex space-x-6 text-sm">
                    <a href="#hero" class="hover:text-white transition-colors">Home</a>
                    <a href="#features" class="hover:text-white transition-colors">Services</a>
                    <a href="#about" class="hover:text-white transition-colors">About</a>
                    <a href="#pricing" class="hover:text-white transition-colors">Pricing</a>
                    <a href="#contact" class="hover:text-white transition-colors">Contact</a>
                </div>
            </div>
            <div class="border-t border-slate-800 mt-8 pt-8 text-center text-xs text-slate-500">
                <p>© {plan.business_name}. All rights reserved. Generated by AI Website Builder Agent.</p>
            </div>
        </div>
    </footer>

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
        return html

    def _render_css(self, plan: WebsitePlan) -> str:
        """Generates supporting CSS with design tokens."""
        return f"""/* Custom Theme Variables & Interactions */
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

/* Clean focus outline for accessibility */
button:focus-visible, a:focus-visible {{
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}}
"""

    def _render_js(self, project_id: str) -> str:
        """Generates client script connecting contact form to real backend endpoint."""
        return f"""// Client Interaction and Form Submission Logic
document.addEventListener('DOMContentLoaded', () => {{
    // Mobile navigation toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mobileDrawer = document.getElementById('mobileDrawer');
    if (mobileBtn && mobileDrawer) {{
        mobileBtn.addEventListener('click', () => {{
            mobileDrawer.classList.toggle('hidden');
        }});
    }}

    // Real Contact Form Handler
    const form = document.getElementById('contactForm');
    const statusBox = document.getElementById('formStatus');
    const submitBtn = document.getElementById('submitBtn');

    if (form) {{
        form.addEventListener('submit', async (e) => {{
            e.preventDefault();

            const name = document.getElementById('senderName').value.trim();
            const email = document.getElementById('senderEmail').value.trim();
            const phone = document.getElementById('senderPhone').value.trim();
            const subject = document.getElementById('senderSubject').value.trim();
            const message = document.getElementById('senderMessage').value.trim();
            const hp = document.getElementById('websiteHp').value;
            const projectId = document.getElementById('projectIdField').value || '{project_id}';

            // Validate required inputs
            if (!name || !email || !message) {{
                showStatus('Please complete all required fields.', false);
                return;
            }}

            // Disable submit button while sending
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.6';
            submitBtn.querySelector('span').innerText = 'Sending...';

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
                    const data = await response.json();
                    showStatus('Thank you! Your message has been sent successfully.', true);
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
                submitBtn.querySelector('span').innerText = 'Send Message';
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
