from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.command_approval import CommandApproval
from backend.app.schemas.approval import (
    CommandApprovalResponse, CommandApprovalDecision
)
from backend.app.agents.execution_agent import execution_agent

router = APIRouter(prefix="/api/v1", tags=["Command Approvals"])

@router.get("/projects/{project_id}/approvals", response_model=List[CommandApprovalResponse])
async def list_project_approvals(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves all pending and executed command approval requests for a project."""
    query = (
        select(CommandApproval)
        .where(CommandApproval.project_id == project_id)
        .order_by(desc(CommandApproval.created_at))
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/approvals/{approval_id}/decision", response_model=CommandApprovalResponse)
async def decide_command_approval(
    approval_id: int,
    decision: CommandApprovalDecision,
    db: AsyncSession = Depends(get_db)
):
    """
    Explicit user authorization gate:
    User reviews the command, its purpose, and risk level, then grants or denies permission.
    """
    approval = await db.get(CommandApproval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval request already has status '{approval.status}'.")

    if decision.decision == "approve":
        approval.status = "approved"
    else:
        approval.status = "rejected"
        approval.execution_output = f"Execution rejected by user: {decision.reason or 'No reason provided'}"

    approval.decided_at = datetime.utcnow()
    await db.commit()
    await db.refresh(approval)
    return approval

@router.post("/approvals/{approval_id}/execute")
async def execute_approved_command(approval_id: int, db: AsyncSession = Depends(get_db)):
    """
    Runs the approved command inside the isolated project workspace
    and automatically saves a Git checkpoint.
    """
    approval = await db.get(CommandApproval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    if approval.status != "approved":
        raise HTTPException(status_code=400, detail="Command must be approved before execution.")

    success, output, commit_hash = await execution_agent.execute_approved_command_and_checkpoint(
        db=db,
        project_id=approval.project_id,
        approval_id=approval_id,
        checkpoint_message=f"verify: {approval.purpose}"
    )

    return {
        "status": "success" if success else "failed",
        "output": output,
        "commit_hash": commit_hash
    }
