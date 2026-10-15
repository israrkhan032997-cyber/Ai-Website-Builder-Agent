import uuid
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.contact_submission import ContactSubmission
from backend.app.models.checkpoint import Checkpoint
from backend.app.models.command_approval import CommandApproval
from backend.app.models.website_page import WebsitePage
from backend.app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse
)
from backend.app.services.workspace_manager import workspace_manager

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new project record and prepares isolated workspace."""
    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        name=data.name.strip(),
        industry=data.industry.strip(),
        description=data.description.strip(),
        target_audience=data.target_audience.strip() if data.target_audience else None,
        style=data.style or "Modern & Clean",
        website_type=data.website_type or "single-page",
        selected_pages=data.selected_pages or ["Home"],
        tech_stack=data.tech_stack or "react-php",
        subdomain=data.subdomain,
        custom_domain=data.custom_domain,
        primary_color=data.primary_color or "#2563eb",
        secondary_color=data.secondary_color or "#0f172a",
        accent_color=data.accent_color or "#38bdf8",
        logo_url=data.logo_url,
        status="draft",
        progress_percentage="0%"
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Initialize workspace folder
    workspace_manager.get_project_dir(project_id)
    return project

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lists saved projects ordered by last updated date."""
    query = select(Project).order_by(desc(Project.updated_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Gets complete project details including counts and metadata."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Query counts
    sub_count_q = select(func.count(ContactSubmission.id)).where(ContactSubmission.project_id == project_id)
    sub_count = (await db.execute(sub_count_q)).scalar() or 0

    chk_count_q = select(func.count(Checkpoint.id)).where(Checkpoint.project_id == project_id)
    chk_count = (await db.execute(chk_count_q)).scalar() or 0

    appr_count_q = select(func.count(CommandApproval.id)).where(
        CommandApproval.project_id == project_id,
        CommandApproval.status == "pending"
    )
    appr_count = (await db.execute(appr_count_q)).scalar() or 0

    resp = ProjectDetailResponse.model_validate(project)
    resp.submissions_count = sub_count
    resp.checkpoints_count = chk_count
    resp.pending_approvals_count = appr_count
    return resp

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, data: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    """Updates project properties."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Permanently deletes a project, its records, and workspace files."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    await db.delete(project)
    await db.commit()

    # Safely delete disk workspace
    workspace_manager.delete_project_workspace(project_id)
    return {"message": "Project deleted successfully", "id": project_id}

@router.get("/{project_id}/files")
async def list_project_files(project_id: str, db: AsyncSession = Depends(get_db)):
    """Lists all files in project workspace."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    files = workspace_manager.list_files(project_id)
    return {"project_id": project_id, "files": files}

@router.get("/{project_id}/files/content")
async def get_file_content(
    project_id: str,
    path: str = Query(..., description="Relative path to file, e.g. index.html"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves file content safely."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    content = workspace_manager.read_file(project_id, path)
    return {"path": path, "content": content}

@router.get("/{project_id}/pages")
async def get_project_pages(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves all registered website pages (Home, About, Services, etc.) for this project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    query = (
        select(WebsitePage)
        .where(WebsitePage.project_id == project_id)
        .order_by(WebsitePage.order_index.asc(), WebsitePage.created_at.asc())
    )
    result = await db.execute(query)
    pages = result.scalars().all()
    
    # If no pages recorded yet but index.html exists, return default
    if not pages and workspace_manager.file_exists(project_id, "index.html"):
        return [{
            "id": "home",
            "project_id": project_id,
            "title": "Home",
            "slug": "index",
            "file_path": "index.html",
            "is_home": True,
            "order_index": 0
        }]

    return pages

@router.get("/{project_id}/export")
async def export_project_zip(project_id: str, db: AsyncSession = Depends(get_db)):
    """Creates and returns downloadable ZIP archive of the generated website."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    zip_file = workspace_manager.create_project_zip(project_id)
    clean_name = "".join(c for c in project.name if c.isalnum() or c in "-_") or "website"
    return FileResponse(
        path=str(zip_file),
        filename=f"{clean_name}-website.zip",
        media_type="application/zip"
    )

