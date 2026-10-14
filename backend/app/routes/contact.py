from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.contact_submission import ContactSubmission
from backend.app.schemas.contact import (
    ContactSubmissionCreate, ContactSubmissionResponse, ContactSubmissionStatusUpdate
)
from backend.app.agents.backend_agent import backend_agent

router = APIRouter(prefix="/api/v1/projects/{project_id}/contact", tags=["Contact Submissions"])

@router.post("", status_code=201)
async def submit_contact_form(
    project_id: str,
    data: ContactSubmissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Genuine server-side contact submission handler for generated websites.
    Validates input, filters automated spam bots, and persists inquiry in the database.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    ip_addr = request.client.host if request.client else None
    success, msg, rec_id = await backend_agent.process_contact_submission(
        db=db,
        project_id=project_id,
        data=data,
        ip_address=ip_addr
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "status": "success",
        "message": msg,
        "submission_id": rec_id
    }

@router.get("", response_model=List[ContactSubmissionResponse])
async def list_project_submissions(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves all real contact messages submitted to this project's website."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    query = (
        select(ContactSubmission)
        .where(ContactSubmission.project_id == project_id)
        .order_by(desc(ContactSubmission.created_at))
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/{submission_id}", response_model=ContactSubmissionResponse)
async def update_submission_status(
    project_id: str,
    submission_id: int,
    data: ContactSubmissionStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Marks a contact inquiry as read or archived."""
    submission = await db.get(ContactSubmission, submission_id)
    if not submission or submission.project_id != project_id:
        raise HTTPException(status_code=404, detail="Submission record not found.")

    submission.status = data.status
    await db.commit()
    await db.refresh(submission)
    return submission
