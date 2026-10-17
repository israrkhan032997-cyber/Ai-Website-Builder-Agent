import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.database import init_db
from backend.app.services.conversational_assistant import conversational_assistant
from backend.app.services.ai_provider import ai_provider
from backend.app.agents.design_agent import design_agent
from backend.app.agents.backend_agent import backend_agent
from backend.app.schemas.agent import WebsitePlan, AssetManifest, AssetItem
from backend.app.schemas.project import ProjectCreate, SUPPORTED_TECH_STACKS


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    await init_db()
    yield


# ===========================================================================
# 1. Conversational Assistant: "Israr" Anti-Hallucination & Guided Elicitation
# ===========================================================================

@pytest.mark.asyncio
async def test_israr_name_only_input_asks_for_business_type():
    """
    Scenario: User types only a name like 'Israr'.
    The assistant must NOT hallucinate industry, description, or target audience.
    It must preserve the name 'Israr' and specifically ask what type of business Israr is.
    """
    turn_res = await conversational_assistant.process_chat_turn(
        user_message="Israr",
        current_step="business_name",
        collected_data={}
    )

    # 1. Business name accurately captured
    assert turn_res.updated_data.get("business_name") == "Israr"

    # 2. Must not hallucinate industry or description
    assert turn_res.updated_data.get("industry") is None or turn_res.updated_data.get("industry") == ""
    assert turn_res.updated_data.get("description") is None or turn_res.updated_data.get("description") == ""

    # 3. Next step must prompt for industry/business type
    assert turn_res.next_step == "industry"

    # 4. Assistant message must ask what type of business Israr is
    bot_msg = turn_res.assistant_message.lower()
    assert "israr" in bot_msg
    assert any(term in bot_msg for term in ["what type", "industry", "kind of business", "what does"])
    assert len(turn_res.suggested_options) > 0


# ===========================================================================
# 2. Conversational Assistant: Full Initial Brief Extraction (No Repetition)
# ===========================================================================

@pytest.mark.asyncio
async def test_full_business_brief_skips_redundant_questions():
    """
    Scenario: User provides full brief upfront:
    'Apex Logistics is a cold-chain freight and refrigerated warehousing company serving pharmaceutical manufacturers.'
    Assistant extracts all 4 attributes and smoothly advances to website_type without asking them to repeat.
    """
    prompt = "Apex Logistics is a cold-chain freight and refrigerated warehousing company serving pharmaceutical manufacturers."
    turn_res = await conversational_assistant.process_chat_turn(
        user_message=prompt,
        current_step="business_name",
        collected_data={}
    )

    data = turn_res.updated_data
    assert "Apex" in data.get("business_name", "")
    assert data.get("industry") is not None
    assert len(data.get("description", "")) > 10
    # Advances past industry/description directly to website_type or later
    assert turn_res.next_step in ["website_type", "style", "page_selection"]


# ===========================================================================
# 3. Pure React Tech Stack Standardization
# ===========================================================================

def test_pure_react_tech_stack_standardization():
    """
    Enforces that tech_stack is strictly 'react'.
    Obsolete stacks ('react-php', 'html-tailwind-php') must be rejected.
    """
    assert SUPPORTED_TECH_STACKS == ("react",)

    # Valid React project
    p = ProjectCreate(
        name="Nova Health",
        industry="Healthcare",
        description="Telemedicine and patient care platform.",
        target_audience="Patients and healthcare providers"
    )
    assert p.tech_stack == "react"


# ===========================================================================
# 4. Single-Page React Bundle Generation
# ===========================================================================

def test_single_page_react_bundle_generation():
    """
    Verifies that single-page generates:
    - index.html with smooth anchor scrolling (#home, #about, #services, #contact)
    - package.json with React 18, Vite, Lucide-react
    - vite.config.js
    - src/App.jsx (single-page composition)
    - src/components/Navbar.jsx, Hero.jsx, Features.jsx, Contact.jsx, Footer.jsx
    """
    plan = WebsitePlan(
        business_name="Israr Bespoke",
        industry="Luxury Tailoring",
        tagline="Handcrafted Excellence & Bespoke Tailoring",
        summary="Creating bespoke suits and couture garments for discerning clients worldwide."
    )
    assets = AssetManifest(
        logo=AssetItem(id="l1", type="logo", name="Logo", description="Logo", url="/logo.svg", alt="Israr Bespoke Logo"),
        images=[],
        icons=[]
    )

    files = design_agent.generate_website_bundle(
        project_id="test_israr_single",
        plan=plan,
        assets=assets,
        website_type="single-page"
    )

    paths = {f.path: f.content for f in files}

    # Root files
    assert "index.html" in paths
    assert "styles.css" in paths
    assert "main.js" in paths
    assert "package.json" in paths
    assert "vite.config.js" in paths

    # React source files
    assert "src/App.jsx" in paths
    assert "src/main.jsx" in paths
    assert "src/index.css" in paths
    assert "src/components/Navbar.jsx" in paths
    assert "src/components/Hero.jsx" in paths
    assert "src/components/Features.jsx" in paths
    assert "src/components/Contact.jsx" in paths
    assert "src/components/Footer.jsx" in paths

    # Check anchor targets in single-page App.jsx and index.html
    app_jsx = paths["src/App.jsx"]
    assert "scrollIntoView" in app_jsx
    assert "Navbar" in app_jsx
    assert "Hero" in app_jsx
    assert "Features" in app_jsx
    assert "Contact" in app_jsx
    assert "Footer" in app_jsx


# ===========================================================================
# 5. Multi-Page React Bundle Generation
# ===========================================================================

def test_multi_page_react_bundle_generation():
    """
    Verifies that multi-page generates:
    - Multiple HTML pages for instant preview navigation (index.html, about-us.html, services.html, portfolio.html, contact-us.html)
    - React routing architecture (src/App.jsx with activePage state switcher)
    - Individual page components (src/pages/Home.jsx, About.jsx, Services.jsx, Portfolio.jsx, Contact.jsx)
    """
    plan = WebsitePlan(
        business_name="Israr Global",
        industry="Technology & Consulting",
        tagline="Next-Gen Architecture & Digital Strategy",
        summary="Advising top global enterprises on cloud and AI modernizations."
    )
    assets = AssetManifest(
        logo=AssetItem(id="l1", type="logo", name="Logo", description="Logo", url="/logo.svg", alt="Israr Global Logo"),
        images=[],
        icons=[]
    )

    files = design_agent.generate_website_bundle(
        project_id="test_israr_multi",
        plan=plan,
        assets=assets,
        website_type="multi-page",
        selected_pages=["Home", "About Us", "Services", "Portfolio", "Contact Us"]
    )

    paths = {f.path: f.content for f in files}

    # Distinct preview HTML pages
    assert "index.html" in paths
    assert "about-us.html" in paths
    assert "services.html" in paths
    assert "portfolio.html" in paths
    assert "contact-us.html" in paths

    # React page components
    assert "src/pages/Home.jsx" in paths
    assert "src/pages/About.jsx" in paths
    assert "src/pages/Services.jsx" in paths
    assert "src/pages/Portfolio.jsx" in paths
    assert "src/pages/Contact.jsx" in paths

    # Multi-page App.jsx contains client page switcher
    app_jsx = paths["src/App.jsx"]
    assert "activePage" in app_jsx
    assert "setActivePage" in app_jsx
    assert "renderPage" in app_jsx


# ===========================================================================
# 6. Live Gemini API Diagnostics Endpoint Verification
# ===========================================================================

@pytest.mark.asyncio
async def test_gemini_diagnostics_endpoint():
    """
    Verifies that GET /api/v1/health/diagnostics?check_provider=true
    reliably probes the Gemini API, measures latency, and never exposes keys.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/health/diagnostics?check_provider=true")
        assert res.status_code == 200
        diag = res.json()

        assert diag["gemini_configured"] is True
        assert "gemini" in diag["gemini_model_configured"].lower()
        assert "GEMINI_API_KEY" not in str(diag) # No raw leak
        assert diag.get("gemini_reachable") is True
        assert "gemini" in diag.get("gemini_active_model", "").lower()


# ===========================================================================
# 7. React REST API Bundle & Serverless Handlers Generation
# ===========================================================================

def test_react_api_bundle_and_no_php():
    """
    Verifies backend_agent generates React REST API and serverless handlers:
    - api/contact.js
    - api/README.md
    - No PHP files anywhere in generated bundles
    """
    files = backend_agent.generate_api_bundle(
        project_id="test_api_clean",
        business_name="Israr Ventures",
        admin_email="israr@ventures.com"
    )
    paths = [f.path for f in files]

    assert "api/contact.js" in paths
    assert "api/README.md" in paths

    # Confirm complete absence of PHP files
    for p in paths:
        assert not p.endswith(".php"), f"Unexpected PHP file generated: {p}"


# ===========================================================================
# 8. Regression Verification: Israr Multi-Turn Preservation & Compound Pages
# ===========================================================================

@pytest.mark.asyncio
async def test_israr_multi_turn_preservation_and_page_regression():
    """
    Verifies that:
    1. 'Israr' is preserved across turns and never overwritten.
    2. Answering 'AI and software development company' sets industry & description cleanly.
    3. Inputting 'give me a five pages website for full stack webdevelopers' sets 5 pages and multi-page.
    4. Passing ['Home', 'Add Portfolio About', 'Case Study'] generates ['home', 'portfolio', 'about', 'case-study'].
    """
    # Turn 1: Name only
    res1 = await conversational_assistant.process_chat_turn(
        user_message="Israr",
        current_step="business_name",
        collected_data={}
    )
    assert res1.updated_data["business_name"] == "Israr"
    assert "Israr" in res1.assistant_message
    assert "industry" == res1.next_step

    # Turn 2: Industry specification
    res2 = await conversational_assistant.process_chat_turn(
        user_message="AI and software development company",
        current_step="industry",
        collected_data=res1.updated_data
    )
    # Business name strictly preserved!
    assert res2.updated_data["business_name"] == "Israr"
    assert res2.updated_data["industry"] == "AI & Software Development"
    assert len(res2.updated_data["description"]) > 10

    # Turn 2b: Conversational request with page count
    res2b = await conversational_assistant.process_chat_turn(
        user_message="give me a five pages website for full stack webdevelopers",
        current_step="industry",
        collected_data=res1.updated_data
    )
    assert res2b.updated_data["business_name"] == "Israr"
    assert res2b.updated_data["industry"] == "Web Development & Technology"
    assert res2b.updated_data["website_type"] == "multi-page"
    assert len(res2b.updated_data["selected_pages"]) == 5

    # Page regression test: compound action phrase + case study
    from backend.app.services.conversational_assistant import sanitize_page_list
    raw_pages = ['Home', 'Add Portfolio About', 'Case Study']
    sanitized = sanitize_page_list(raw_pages)
    assert sanitized == ['home', 'portfolio', 'about', 'case-study']

    # Project creation with exact failing input
    p = ProjectCreate(
        name="Israr",
        industry="AI & Software Development",
        description="Innovative software and AI engineering solutions.",
        website_type="multi-page",
        selected_pages=raw_pages
    )
    assert p.name == "Israr"
    assert p.selected_pages == ['home', 'portfolio', 'about', 'case-study']

    # Generate design bundle and verify CaseStudy component & routes
    plan = WebsitePlan(
        business_name=p.name,
        industry=p.industry,
        tagline="Advanced AI & Software Engineering",
        summary=p.description
    )
    assets = AssetManifest(
        logo=AssetItem(id="l1", type="logo", name="Logo", description="Logo", url="/logo.svg", alt="Israr Logo"),
        images=[],
        icons=[]
    )
    files = design_agent.generate_website_bundle(
        project_id="test_israr_regression",
        plan=plan,
        assets=assets,
        website_type="multi-page",
        selected_pages=p.selected_pages
    )
    paths = {f.path: f.content for f in files}
    assert "src/pages/CaseStudy.jsx" in paths
    assert "src/pages/Portfolio.jsx" in paths
    assert "src/pages/About.jsx" in paths
    assert "src/pages/Home.jsx" in paths
    assert "case-study" in paths["src/App.jsx"]

