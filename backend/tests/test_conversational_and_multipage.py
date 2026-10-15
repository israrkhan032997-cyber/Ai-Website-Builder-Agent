import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.database import init_db
from backend.app.services.conversational_assistant import conversational_assistant
from backend.app.services.subdomain_service import subdomain_service
from backend.app.agents.backend_agent import backend_agent
from backend.app.agents.design_agent import design_agent
from backend.app.agents.orchestrator import orchestrator_agent
from backend.app.schemas.agent import AssetManifest, AssetItem

@pytest.mark.asyncio
async def test_conversational_assistant_progression():
    """Tests that conversational turns sequentially prompt and extract data."""
    # Step 1: Business name
    res1 = await conversational_assistant.process_chat_turn(
        user_message="Pepsi Beverage Co",
        current_step="business_name",
        collected_data={}
    )
    assert res1.next_step in ["industry", "description", "target_audience", "website_type"]
    assert "Pepsi" in res1.updated_data["business_name"]
    assert len(res1.suggested_options) > 0

    # Step 2: Industry
    res2 = await conversational_assistant.process_chat_turn(
        user_message="Food & Hospitality",
        current_step="industry",
        collected_data=res1.updated_data
    )
    assert res2.next_step in ["description", "target_audience", "website_type"]
    assert "Food" in res2.updated_data["industry"] or "Beverage" in res2.updated_data["industry"]

    # Step 3: Description
    res3 = await conversational_assistant.process_chat_turn(
        user_message="We manufacture world-class refreshing beverages and snacks.",
        current_step="description",
        collected_data=res2.updated_data
    )
    assert res3.next_step in ["target_audience", "website_type"]

    # Step 5: Multi-page selection
    res4 = await conversational_assistant.process_chat_turn(
        user_message="Multi-page website",
        current_step="website_type",
        collected_data=res3.updated_data
    )
    assert res4.next_step == "page_selection"
    assert res4.updated_data["website_type"] == "multi-page"
    assert "Home" in res4.updated_data["selected_pages"]

@pytest.mark.asyncio
async def test_php_backend_bundle_generation():
    """Tests that BackendAgent produces full PHP backend files."""
    files = backend_agent.generate_php_backend_bundle(
        project_id="test_proj_12345",
        business_name="Acme Corp",
        admin_email="admin@acme.com"
    )
    paths = [f.path for f in files]
    assert "api/config.php" in paths
    assert "api/database.sql" in paths
    assert "api/contact.php" in paths
    assert "api/subscribe.php" in paths
    assert "README_PHP.md" in paths

    contact_php = next(f for f in files if f.path == "api/contact.php")
    assert "mail(" in contact_php.content

    sql_file = next(f for f in files if f.path == "api/database.sql")
    assert "CREATE TABLE IF NOT EXISTS `contacts`" in sql_file.content
    assert "CREATE TABLE IF NOT EXISTS `newsletter_subscribers`" in sql_file.content

@pytest.mark.asyncio
async def test_multipage_design_bundle_generation():
    """Tests that DesignAgent generates separate HTML pages for multipage sites."""
    plan, _ = await orchestrator_agent.create_website_plan(
        business_name="Atlas Architecture",
        industry="Architecture & Construction",
        description="Award winning sustainable interior and modern building architecture.",
        website_type="multi-page",
        selected_pages=["Home", "About Us", "Services", "Portfolio", "Contact Us"]
    )

    logo_item = AssetItem(
        id="logo_1",
        type="logo",
        name="Atlas Logo",
        description="Vector logo",
        url="/logo.svg",
        alt="Atlas Architecture Logo"
    )
    image_item = AssetItem(
        id="img_1",
        type="hero_image",
        name="Hero Image",
        description="Modern building",
        url="https://images.unsplash.com/photo-1",
        alt="Atlas Architecture Exterior"
    )

    assets = AssetManifest(
        logo=logo_item,
        images=[image_item],
        icons=["Building", "Compass", "Layers"]
    )

    bundle = design_agent.generate_website_bundle(
        project_id="test_atlas_arch",
        plan=plan,
        assets=assets,
        website_type="multi-page",
        selected_pages=["Home", "About Us", "Services", "Portfolio", "Contact Us"]
    )
    bundle_paths = [f.path for f in bundle]

    assert "index.html" in bundle_paths
    assert "about-us.html" in bundle_paths
    assert "services.html" in bundle_paths
    assert "contact-us.html" in bundle_paths
    assert "styles.css" in bundle_paths
    assert "main.js" in bundle_paths

@pytest.mark.asyncio
async def test_subdomain_normalization_and_validation():
    """Tests RFC-1035 slug generation and validation."""
    slug = subdomain_service.normalize_slug("Pepsi & Co. Architecture!!")
    assert slug == "pepsi-co-architecture"

    valid, _ = subdomain_service.validate_slug("pepsi-brand")
    assert valid is True

    valid_bad, msg = subdomain_service.validate_slug("-invalid-")
    assert valid_bad is False

@pytest.mark.asyncio
async def test_api_health_and_subdomain_endpoints():
    """Tests HTTP endpoints via ASGI client."""
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        health_resp = await ac.get("/api/v1/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        # Check subdomain availability
        sub_resp = await ac.post("/api/v1/subdomains/check", json={"slug": "mytestbusiness"})
        assert sub_resp.status_code == 200
        data = sub_resp.json()
        assert data["slug"] == "mytestbusiness"
        assert "available" in data
