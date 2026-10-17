import pytest
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database import init_db
from backend.app.services.workspace_manager import workspace_manager
from backend.app.models.project import Project

@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_a_exact_logo_url_preservation():
    """
    Test A: Exact logo URL
    User supplies an exact logo URL with query parameters.
    Website MUST use that exact URL in the actual code across pages without AI approximation.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create a multi-page project
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Alpha Corp",
            "industry": "Technology",
            "description": "High-throughput cloud software systems.",
            "website_type": "multi-page",
            "selected_pages": ["home", "about", "services", "contact"]
        })
        assert create_res.status_code == 201
        project_id = create_res.json()["id"]

        # Generate initial bundle
        gen_res = await ac.post(f"/api/v1/projects/{project_id}/generate")
        assert gen_res.status_code == 200

        # 2. User supplies exact logo URL with query parameters
        exact_logo_url = "https://example.com/assets/brands/alpha-logo.png?v=4.2&variant=dark"
        edit_payload = {
            "instruction": f"Replace my current website logo with this exact logo: {exact_logo_url}"
        }
        edit_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json=edit_payload)
        assert edit_res.status_code == 200
        edit_data = edit_res.json()
        assert edit_data["status"] == "success"

        # 3. Check actual website source code in index.html
        index_html = workspace_manager.read_file(project_id, "index.html")
        assert exact_logo_url in index_html, "Exact logo URL must be present in index.html"
        assert f'src="{exact_logo_url}"' in index_html or f"src='{exact_logo_url}'" in index_html

        # 4. Check that logo is also updated on about.html (multi-page consistency)
        if workspace_manager.file_exists(project_id, "about.html"):
            about_html = workspace_manager.read_file(project_id, "about.html")
            assert exact_logo_url in about_html, "Exact logo URL must persist across multi-page navigation"

        # 5. Aspect ratio check
        assert "object-contain" in index_html or "w-auto" in index_html


@pytest.mark.asyncio
async def test_b_exact_image_url_preservation():
    """
    Test B: Exact image URL
    User supplies an exact banner/hero image URL.
    The hero section MUST use that exact URL without AI-generated substitution.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Beacon Labs",
            "industry": "Artificial Intelligence",
            "description": "Enterprise AI workflow infrastructure."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        exact_banner_url = "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1600&q=85"
        edit_payload = {
            "instruction": f"Replace the hero section background image with {exact_banner_url}"
        }
        edit_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json=edit_payload)
        assert edit_res.status_code == 200

        index_html = workspace_manager.read_file(project_id, "index.html")
        assert exact_banner_url in index_html, "Hero section must contain the exact banner URL without substitution"


@pytest.mark.asyncio
async def test_c_change_only_one_element_preserves_everything_else():
    """
    Test C: Change only one element
    User asks to change only the logo.
    All other content, sections, headlines, and styles must remain completely untouched.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Precision Dynamics",
            "industry": "Consulting",
            "description": "Strategic advisory and risk optimization solutions."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        # Capture original content
        original_html = workspace_manager.read_file(project_id, "index.html")
        original_headline = "Precision Dynamics"

        # Apply edit to ONLY the logo
        new_logo = "https://example.com/standalone-logo.png"
        edit_payload = {
            "instruction": f"Change only the logo to {new_logo}"
        }
        edit_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json=edit_payload)
        assert edit_res.status_code == 200

        updated_html = workspace_manager.read_file(project_id, "index.html")
        assert new_logo in updated_html

        # Verify unrelated sections and text are preserved
        assert original_headline in updated_html
        assert "contactForm" in updated_html or "contact" in updated_html
        # Main structure tags preserved
        assert "<main" in updated_html and "</main>" in updated_html
        assert "<footer" in updated_html and "</footer>" in updated_html


@pytest.mark.asyncio
async def test_d_exact_text_verbatim_replacement():
    """
    Test D: Exact text
    User provides replacement text. The website must display the exact supplied text.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Quantum Shield",
            "industry": "Cybersecurity",
            "description": "Military-grade post-quantum cryptography."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        exact_headline = "Next-Gen Quantum Defense & Threat Neutralization Platform"
        edit_payload = {
            "instruction": f"Update the headline to '{exact_headline}'"
        }
        edit_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json=edit_payload)
        assert edit_res.status_code == 200

        updated_html = workspace_manager.read_file(project_id, "index.html")
        assert exact_headline in updated_html, "Headline must match the exact user-supplied text verbatim"


@pytest.mark.asyncio
async def test_e_multiple_sequential_edits_persist_without_overwriting():
    """
    Test E: Multiple sequential edits
    User changes logo, then primary color, then headline.
    Each change must persist and not revert earlier changes.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Omni Health",
            "industry": "Healthcare",
            "description": "Personalized longevity diagnostics."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        # 1. Edit Logo
        logo_url = "https://example.com/omni-logo-v1.png"
        r1 = await ac.post(f"/api/v1/projects/{project_id}/edit", json={
            "instruction": f"Replace my logo with {logo_url}"
        })
        assert r1.status_code == 200

        # 2. Edit Brand Color
        r2 = await ac.post(f"/api/v1/projects/{project_id}/edit", json={
            "instruction": "Update the primary color to emerald"
        })
        assert r2.status_code == 200

        # 3. Edit Headline
        headline_text = "Pioneering Cellular Longevity Science"
        r3 = await ac.post(f"/api/v1/projects/{project_id}/edit", json={
            "instruction": f"Update the headline to '{headline_text}'"
        })
        assert r3.status_code == 200

        # Verify all 3 modifications persist simultaneously
        final_html = workspace_manager.read_file(project_id, "index.html")
        assert logo_url in final_html, "Edit 1 (Logo) must still persist"
        assert "#10b981" in final_html or "emerald" in final_html, "Edit 2 (Emerald color) must still persist"
        assert headline_text in final_html, "Edit 3 (Headline) must still persist"


@pytest.mark.asyncio
async def test_f_invalid_image_url_returns_honest_error():
    """
    Test F: Invalid image URL
    System must report the loading problem and must not silently substitute another image.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Test Site",
            "industry": "Retail",
            "description": "Online store."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        orig_html = workspace_manager.read_file(project_id, "index.html")

        # Non-existent domain with failed DNS
        invalid_url = "https://invalid-domain-does-not-exist-999999.xyz/broken-logo.png"
        edit_payload = {
            "instruction": f"Replace the logo with {invalid_url}"
        }
        edit_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json=edit_payload)

        # Must fail with 400
        assert edit_res.status_code == 400
        detail = edit_res.json()["detail"]
        assert "cannot be accessed" in detail.lower() or "dns" in detail.lower() or "invalid" in detail.lower()

        # Workspace HTML must remain unmodified (no silent fake replacement)
        current_html = workspace_manager.read_file(project_id, "index.html")
        assert current_html == orig_html, "Workspace files must not be altered when URL verification fails"


@pytest.mark.asyncio
async def test_g_preview_updates_without_premature_deployment():
    """
    Test G: Preview without deployment
    Edits must update preview immediately without deploying the website automatically.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Starlight Travel",
            "industry": "Hospitality",
            "description": "Bespoke safari tours and private island retreats."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        # Edit headline
        new_headline = "Exclusive Luxury Expeditions & Island Escapes"
        await ac.post(f"/api/v1/projects/{project_id}/edit", json={
            "instruction": f"Update the headline to '{new_headline}'"
        })

        # Check preview endpoint serves the updated HTML
        prev_res = await ac.get(f"/api/v1/preview/{project_id}/index.html")
        assert prev_res.status_code == 200
        assert new_headline in prev_res.text

        # Check project deployment status remains unchanged (NOT deployed)
        proj_res = await ac.get(f"/api/v1/projects/{project_id}")
        assert proj_res.status_code == 200
        proj_data = proj_res.json()
        assert proj_data["deployment_status"] in ["unassigned", "draft", "ready"]
        assert proj_data["deployment_status"] != "deployed"


@pytest.mark.asyncio
async def test_section_removal_and_targeted_hero_background():
    """
    Tests:
    - Clean removal of pricing section without modifying other sections.
    - Targeted hero background change without affecting overall site theme.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Aero Cloud",
            "industry": "SaaS",
            "description": "Serverless edge compute platform."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        # 1. Remove pricing section
        del_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json={
            "instruction": "Remove the pricing section"
        })
        assert del_res.status_code == 200
        html_after_del = workspace_manager.read_file(project_id, "index.html")
        assert 'id="pricing"' not in html_after_del
        # Other sections intact
        assert 'id="hero"' in html_after_del
        assert 'id="contact"' in html_after_del

        # 2. Targeted hero background change (does not change whole site theme)
        bg_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json={
            "instruction": "Change the hero background to blue"
        })
        assert bg_res.status_code == 200
        html_after_bg = workspace_manager.read_file(project_id, "index.html")
        assert "background-color" in html_after_bg or "bg-blue" in html_after_bg


@pytest.mark.asyncio
async def test_logo_replacement_in_react_jsx_and_html():
    """
    Issue 1 Test: User provides exact logo URL.
    - Updates actual logo component in HTML and React JSX (src/components/Navbar.jsx).
    - Preserves aspect ratio (object-contain, h-9 w-auto).
    - Source code read-back verification passes.
    - Checkpoints recorded and rollback works as expected.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Nexus Dynamics",
            "industry": "Robotics",
            "description": "Autonomous robotic logistics systems."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        exact_logo_url = "https://example.com/branding/nexus-icon.svg?v=1.0.4"
        edit_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json={
            "instruction": f"Replace my current logo with this exact logo: {exact_logo_url}"
        })
        assert edit_res.status_code == 200
        edit_data = edit_res.json()
        assert edit_data["status"] == "success"

        # 1. HTML index.html verification
        index_html = workspace_manager.read_file(project_id, "index.html")
        assert exact_logo_url in index_html
        assert "object-contain" in index_html

        # 2. React JSX Navbar.jsx verification (if generated)
        if workspace_manager.file_exists(project_id, "src/components/Navbar.jsx"):
            navbar_jsx = workspace_manager.read_file(project_id, "src/components/Navbar.jsx")
            assert exact_logo_url in navbar_jsx
            assert "object-contain" in navbar_jsx

        # 3. Checkpoint created
        chk_res = await ac.get(f"/api/v1/projects/{project_id}/checkpoints")
        assert chk_res.status_code == 200
        checkpoints = chk_res.json()
        assert len(checkpoints) >= 2
        initial_commit = checkpoints[-1]["commit_hash"]

        # 4. Rollback works
        rollback_res = await ac.post(f"/api/v1/projects/{project_id}/rollback", json={
            "commit_hash": initial_commit
        })
        assert rollback_res.status_code == 200


@pytest.mark.asyncio
async def test_webpage_url_rejected_with_helpful_error():
    """
    Asset Validation Test:
    When user provides a URL that points to a webpage instead of a direct image,
    it must return HTTP 400 explaining that it is a webpage and asking for a direct image URL.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_res = await ac.post("/api/v1/projects", json={
            "name": "Solaris Energy",
            "industry": "CleanTech",
            "description": "Commercial solar grid solutions."
        })
        project_id = create_res.json()["id"]
        await ac.post(f"/api/v1/projects/{project_id}/generate")

        # Provide a webpage URL
        webpage_url = "https://example.com/company-overview-page"
        edit_res = await ac.post(f"/api/v1/projects/{project_id}/edit", json={
            "instruction": f"Set my logo to {webpage_url}"
        })
        assert edit_res.status_code == 400
        error_detail = edit_res.json()["detail"]
        assert "webpage" in error_detail.lower()
        assert "direct image" in error_detail.lower()

