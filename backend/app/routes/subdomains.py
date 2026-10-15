import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.schemas.subdomain import (
    SubdomainCheckRequest,
    SubdomainCheckResponse,
    SubdomainAssignRequest,
    SubdomainAssignResponse
)
from backend.app.services.subdomain_service import subdomain_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/subdomains", tags=["Subdomains"])

@router.post("/check", response_model=SubdomainCheckResponse)
async def check_subdomain_availability(
    payload: SubdomainCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Checks if a desired subdomain slug is available and valid according to RFC-1035 rules.
    If unavailable or invalid, returns alternatives.
    """
    slug = subdomain_service.normalize_slug(payload.slug)
    is_valid, validation_msg = subdomain_service.validate_slug(slug)

    if not is_valid:
        suggestions = await subdomain_service.get_suggested_slugs(slug, db)
        return SubdomainCheckResponse(
            slug=slug,
            available=False,
            message=validation_msg,
            preview_url=None,
            suggested_alternatives=suggestions
        )

    is_available = await subdomain_service.check_availability(
        desired_slug=slug,
        db=db,
        exclude_project_id=payload.project_id
    )

    suggestions = []
    if not is_available:
        suggestions = await subdomain_service.get_suggested_slugs(slug, db)
        msg = f"Subdomain '{slug}' is already registered."
    else:
        msg = f"Subdomain '{slug}' is available!"

    preview_url = subdomain_service.build_subdomain_url(slug) if is_available else None

    return SubdomainCheckResponse(
        slug=slug,
        available=is_available,
        message=msg,
        preview_url=preview_url,
        suggested_alternatives=suggestions
    )

@router.post("/assign", response_model=SubdomainAssignResponse)
async def assign_subdomain_to_project(
    payload: SubdomainAssignRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Assigns and reserves a verified subdomain slug for a project.
    """
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    success, assigned_slug, err_msg = await subdomain_service.reserve_subdomain(
        project_id=payload.project_id,
        desired_slug=payload.subdomain,
        db=db
    )

    if not success:
        raise HTTPException(status_code=400, detail=err_msg)

    public_url = subdomain_service.build_subdomain_url(assigned_slug)
    return SubdomainAssignResponse(
        project_id=payload.project_id,
        subdomain=assigned_slug,
        full_url=public_url,
        message="Subdomain reserved and routed successfully."
    )
