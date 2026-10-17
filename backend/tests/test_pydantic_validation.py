import pytest
from pydantic import ValidationError

from backend.app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    NaturalLanguageEditRequest,
    SUPPORTED_TECH_STACKS,
    SUPPORTED_WEBSITE_TYPES,
    SUPPORTED_PAGE_SLUGS,
    RESERVED_SUBDOMAINS,
)
from backend.app.schemas.chat import RequirementsReview
from backend.app.schemas.approval import DeploymentApprovalRequest
from backend.app.services.subdomain_service import subdomain_service


def get_base_project_data():
    return {
        "name": "PepsiCo Global",
        "industry": "Beverages & Consumer Goods",
        "description": "Leading carbonated beverages and snack solutions for retail and consumers.",
        "target_audience": "Global consumers and retail partners"
    }


# ===========================================================================
# 1. Tech Stack Validation & Consistent Default (react)
# ===========================================================================

def test_tech_stack_default_and_supported():
    """Default must be 'react', and only explicitly supported stacks allowed."""
    data = get_base_project_data()
    project = ProjectCreate(**data)
    assert project.tech_stack == "react"


def test_tech_stack_rejects_unsupported_values():
    """Unsupported tech stacks must raise a clear ValidationError and not be silently coerced."""
    data = get_base_project_data()
    invalid_stacks = ["vue", "django", "pure-react", "react-php", "html-tailwind-php", "nextjs", "angular", "flask"]
    for stack in invalid_stacks:
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(**data, tech_stack=stack)
        err_msg = str(exc_info.value)
        assert "Unsupported tech_stack" in err_msg or "supported" in err_msg.lower()
        assert "react" in err_msg


def test_tech_stack_in_project_update():
    """ProjectUpdate validates tech_stack when provided."""
    update_valid = ProjectUpdate(tech_stack="react")
    assert update_valid.tech_stack == "react"

    with pytest.raises(ValidationError) as exc_info:
        ProjectUpdate(tech_stack="invalid-stack")
    assert "Unsupported tech_stack" in str(exc_info.value)



# ===========================================================================
# 2. Website Type Restriction ('single-page' | 'multi-page')
# ===========================================================================

def test_website_type_default_and_validation():
    """website_type defaults to 'single-page' and accepts 'multi-page'."""
    data = get_base_project_data()
    p_single = ProjectCreate(**data)
    assert p_single.website_type == "single-page"

    p_multi = ProjectCreate(
        **data,
        website_type="multi-page",
        selected_pages=["home", "about", "services"]
    )
    assert p_multi.website_type == "multi-page"


def test_website_type_rejects_invalid_types():
    """Invalid website types must raise a ValidationError."""
    data = get_base_project_data()
    invalid_types = ["landing", "spa", "portal", "custom", "ecommerce", ""]
    for t in invalid_types:
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(**data, website_type=t)
        assert "Invalid website_type" in str(exc_info.value)


# ===========================================================================
# 3. Selected Pages Validation & Consistency with Website Type
# ===========================================================================

def test_selected_pages_slug_normalization():
    """Slugs must be lowercased, spaces hyphenated, and aliases mapped."""
    data = get_base_project_data()
    p = ProjectCreate(
        **data,
        website_type="multi-page",
        selected_pages=["Home", "About Us", "Contact Us", "projects"]
    )
    assert p.selected_pages == ["home", "about", "contact", "portfolio"]


def test_selected_pages_rejects_reserved_and_invalid_slugs():
    """Reserved routes and malformed slugs must raise a ValidationError."""
    data = get_base_project_data()

    # Reserved platform route
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            **data,
            website_type="multi-page",
            selected_pages=["home", "admin"]
        )
    assert "reserved platform route" in str(exc_info.value)

    # Invalid characters / format
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            **data,
            website_type="multi-page",
            selected_pages=["home", "invalid page with symbols!@#"]
        )
    assert "Invalid page slug format" in str(exc_info.value)

    # Empty slug entry
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            **data,
            website_type="multi-page",
            selected_pages=["home", "   "]
        )
    assert "cannot be empty" in str(exc_info.value)


def test_selected_pages_supports_valid_custom_slugs_and_decomposition():
    """Custom valid slugs (case-study, our-team) and compound action entries must be cleanly supported."""
    data = get_base_project_data()

    # Custom slugs: case-study, our-team
    p1 = ProjectCreate(
        **data,
        website_type="multi-page",
        selected_pages=["home", "case-study", "our-team"]
    )
    assert p1.selected_pages == ["home", "case-study", "our-team"]

    # Exact failing input regression: ['Home', 'Add Portfolio About', 'Case Study']
    p2 = ProjectCreate(
        **data,
        website_type="multi-page",
        selected_pages=["Home", "Add Portfolio About", "Case Study"]
    )
    assert p2.selected_pages == ["home", "portfolio", "about", "case-study"]

    # Regression: Prompt-polluted slugs like 'use-selected-pages:-home' must be cleanly stripped and normalized
    p3 = ProjectCreate(
        **data,
        website_type="multi-page",
        selected_pages=["home", "use-selected-pages:-home", "pricing", "contact"]
    )
    assert p3.selected_pages == ["home", "pricing", "contact"]

    # Regression: Prompt sentences like 'Use selected pages: Home, Pricing, Contact'
    p4 = ProjectCreate(
        **data,
        website_type="multi-page",
        selected_pages=["home", "Use selected pages: Home, Pricing, Contact"]
    )
    assert p4.selected_pages == ["home", "pricing", "contact"]

    # Regression: Instruction noise string like 'use-selected-pages' alongside legitimate pages
    p5 = ProjectCreate(
        **data,
        website_type="multi-page",
        selected_pages=["home", "use-selected-pages", "pricing", "contact"]
    )
    assert p5.selected_pages == ["home", "pricing", "contact"]


def test_single_page_consistency():
    """single-page website can only have ['home'] in selected_pages."""
    data = get_base_project_data()

    # None defaults to ['home']
    p1 = ProjectCreate(**data, website_type="single-page", selected_pages=None)
    assert p1.selected_pages == ["home"]

    # Explicit ['home'] is valid
    p2 = ProjectCreate(**data, website_type="single-page", selected_pages=["home"])
    assert p2.selected_pages == ["home"]

    # Multiple pages for single-page must be rejected
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            **data,
            website_type="single-page",
            selected_pages=["home", "about"]
        )
    assert "must only contain ['home']" in str(exc_info.value)

    # Missing home for single-page must be rejected
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            **data,
            website_type="single-page",
            selected_pages=["about"]
        )
    assert "must only contain ['home']" in str(exc_info.value)


def test_multi_page_consistency():
    """multi-page website must have at least 2 distinct pages and include 'home'."""
    data = get_base_project_data()

    # Valid multi-page
    p = ProjectCreate(
        **data,
        website_type="multi-page",
        selected_pages=["home", "about", "services"]
    )
    assert len(p.selected_pages) >= 2
    assert "home" in p.selected_pages

    # Less than 2 pages rejected
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            **data,
            website_type="multi-page",
            selected_pages=["home"]
        )
    assert "at least 2 distinct pages" in str(exc_info.value)

    # Missing 'home' rejected
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(
            **data,
            website_type="multi-page",
            selected_pages=["about", "services"]
        )
    assert "must include 'home'" in str(exc_info.value)


# ===========================================================================
# 4. Subdomain Validation & Normalization (RFC-1035 Compliance)
# ===========================================================================

def test_subdomain_normalization_and_valid_cases():
    """Subdomain must be trimmed, lowercased, and validate standard RFC-1035 hostnames."""
    data = get_base_project_data()

    p = ProjectCreate(**data, subdomain="  Pepsi-Beverages  ")
    assert p.subdomain == "pepsi-beverages"

    p2 = ProjectCreate(**data, subdomain="studio360")
    assert p2.subdomain == "studio360"

    p_none = ProjectCreate(**data, subdomain=None)
    assert p_none.subdomain is None

    p_empty = ProjectCreate(**data, subdomain="   ")
    assert p_empty.subdomain is None


def test_subdomain_rejects_invalid_hostnames():
    """Subdomain rejects consecutive hyphens, leading/trailing hyphens, and bad characters."""
    data = get_base_project_data()

    # Short (< 3)
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(**data, subdomain="ab")
    assert "between 3 and 63 characters" in str(exc_info.value)

    # Consecutive hyphens
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(**data, subdomain="pepsi--co")
    assert "consecutive hyphens" in str(exc_info.value)

    # Leading hyphen
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(**data, subdomain="-pepsi")
    assert "Invalid subdomain hostname" in str(exc_info.value)

    # Trailing hyphen
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(**data, subdomain="pepsi-")
    assert "Invalid subdomain hostname" in str(exc_info.value)

    # Invalid characters (dots, underscores, symbols)
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(**data, subdomain="pepsi.com")
    assert "Invalid subdomain hostname" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(**data, subdomain="pepsi_co")
    assert "Invalid subdomain hostname" in str(exc_info.value)


def test_subdomain_rejects_reserved_names():
    """Platform reserved hostnames must be rejected."""
    data = get_base_project_data()
    reserved_samples = ["admin", "api", "app", "dashboard", "preview", "static", "www", "localhost"]
    for r in reserved_samples:
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(**data, subdomain=r)
        assert "reserved platform hostname" in str(exc_info.value)


# ===========================================================================
# 5. Custom Domain Validation & Ownership Verification
# ===========================================================================

def test_custom_domain_normalization_and_validation():
    """custom_domain strips protocols and paths, rejects ports and malformed FQDNs."""
    data = get_base_project_data()

    # Valid FQDN with protocol and trailing slash stripped
    p1 = ProjectCreate(**data, custom_domain="https://pepsi.com/")
    assert p1.custom_domain == "pepsi.com"

    p2 = ProjectCreate(**data, custom_domain="shop.pepsico.co.uk")
    assert p2.custom_domain == "shop.pepsico.co.uk"

    # Rejects port
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(**data, custom_domain="pepsi.com:8080")
    assert "must not include a port number" in str(exc_info.value)

    # Rejects invalid domain without TLD
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(**data, custom_domain="not-a-domain")
    assert "Fully Qualified Domain Name" in str(exc_info.value)


def test_custom_domain_ownership_verification():
    """subdomain_service.verify_custom_domain_ownership tests format and resolution."""
    # Test domains verify for local/dev
    ok, msg = subdomain_service.verify_custom_domain_ownership("example.com")
    assert ok is True

    ok_local, msg_local = subdomain_service.verify_custom_domain_ownership("my-site.test")
    assert ok_local is True

    # Malformed domain fails
    fail_syntax, msg_syntax = subdomain_service.verify_custom_domain_ownership("invalid_domain_with_underscores")
    assert fail_syntax is False


# ===========================================================================
# 6. Natural Language Edit Request Validation (section_id & page_slug)
# ===========================================================================

def test_natural_language_edit_request_optional_fields():
    """section_id and page_slug are optional, but strictly validated when supplied."""
    # Instruction only is valid
    req1 = NaturalLanguageEditRequest(instruction="Make the hero banner background darker navy")
    assert req1.instruction == "Make the hero banner background darker navy"
    assert req1.section_id is None
    assert req1.page_slug is None

    # Valid section_id and page_slug
    req2 = NaturalLanguageEditRequest(
        instruction="Update header button colors",
        section_id="hero",
        page_slug="About Us"
    )
    assert req2.section_id == "hero"
    assert req2.page_slug == "about"

    # Invalid section_id
    with pytest.raises(ValidationError) as exc_info:
        NaturalLanguageEditRequest(
            instruction="Update header",
            section_id="hero with invalid spaces!"
        )
    assert "Invalid section_id" in str(exc_info.value)

    # Invalid page_slug
    with pytest.raises(ValidationError) as exc_info:
        NaturalLanguageEditRequest(
            instruction="Update contact info",
            page_slug="non-existent-blog-archive-xyz"
        )
    assert "Unsupported page_slug" in str(exc_info.value)


# ===========================================================================
# 7. RequirementsReview Schema Validation
# ===========================================================================

def test_requirements_review_validation():
    """RequirementsReview in chat.py validates tech_stack, website_type, and pages."""
    rr = RequirementsReview(
        business_name="Acme Studio",
        industry="Architecture & Construction",
        description="Award-winning luxury residential architecture and interior design.",
        target_audience="Homeowners and developers",
        website_type="multi-page",
        selected_pages=["home", "about", "services", "portfolio", "contact"],
        tech_stack="react"
    )
    assert rr.tech_stack == "react"
    assert rr.website_type == "multi-page"
    assert "home" in rr.selected_pages

    # Inconsistent single-page with multi-page selections
    with pytest.raises(ValidationError) as exc_info:
        RequirementsReview(
            business_name="Acme Studio",
            industry="Architecture",
            description="Award-winning luxury residential architecture.",
            target_audience="Homeowners",
            website_type="single-page",
            selected_pages=["home", "about", "services"],
            tech_stack="react"
        )
    assert "must only contain ['home']" in str(exc_info.value)



# ===========================================================================
# 8. DeploymentApprovalRequest Validation
# ===========================================================================

def test_deployment_approval_request_validation():
    """DeploymentApprovalRequest validates providers and custom_domain."""
    req = DeploymentApprovalRequest(provider="local", confirm=True)
    assert req.provider == "local"

    req_custom = DeploymentApprovalRequest(
        provider="vercel",
        custom_domain="https://pepsico.com",
        confirm=True
    )
    assert req_custom.custom_domain == "pepsico.com"

    with pytest.raises(ValidationError) as exc_info:
        DeploymentApprovalRequest(provider="aws-s3")
    assert "Unsupported deployment provider" in str(exc_info.value)
