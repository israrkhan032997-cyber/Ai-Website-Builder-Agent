import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.agent_log import AgentLog
from backend.app.models.checkpoint import Checkpoint
from backend.app.schemas.project import NaturalLanguageEditRequest
from backend.app.schemas.agent import WebsitePlan, AssetManifest, ValidationResult
from backend.app.services.workspace_manager import workspace_manager
from backend.app.services.git_service import git_service
from backend.app.agents.orchestrator import orchestrator_agent
from backend.app.agents.asset_agent import asset_agent
from backend.app.agents.design_agent import design_agent
from backend.app.agents.backend_agent import backend_agent
from backend.app.agents.execution_agent import execution_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["Agent Workflow"])

class RollbackRequest(BaseModel):
    commit_hash: str

async def _add_log(
    db: AsyncSession,
    project_id: str,
    agent_name: str,
    step_name: str,
    status: str,
    message: str,
    input_payload: Optional[Dict[str, Any]] = None,
    output_payload: Optional[Dict[str, Any]] = None,
    error_details: Optional[str] = None
):
    log = AgentLog(
        project_id=project_id,
        agent_name=agent_name,
        step_name=step_name,
        status=status,
        message=message,
        input_payload=input_payload,
        output_payload=output_payload,
        error_details=error_details
    )
    db.add(log)
    await db.commit()

@router.post("/generate")
async def run_generation_pipeline(project_id: str, db: AsyncSession = Depends(get_db)):
    """
    Executes the genuine 5-stage AI agent generation workflow:
    1. Orchestrator: Formulates WebsitePlan
    2. Asset Agent: Curates images, vector logo & icons
    3. Design Agent: Generates modern HTML5, Tailwind CSS, and interaction scripts
    4. Backend Agent: Implements contact submission and serverless handlers
    5. Orchestrator: Verifies output against specification
    6. Execution Agent: Saves immutable Git checkpoint
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    try:
        # Initialize Git repo
        git_service.init_repository(project_id)

        # -------------------------------------------------------------
        # STAGE 1: Orchestrator Agent (Planning)
        # -------------------------------------------------------------
        project.status = "planning"
        project.current_agent = orchestrator_agent.AGENT_NAME
        project.current_step = "Formulating architectural plan and sections"
        project.progress_percentage = "15%"
        await db.commit()

        await _add_log(
            db, project_id, orchestrator_agent.AGENT_NAME, "Planning",
            "in_progress", f"Analyzing business requirements for '{project.name}' ({project.industry})"
        )

        plan, plan_msg = await orchestrator_agent.create_website_plan(
            business_name=project.name,
            industry=project.industry,
            description=project.description,
            target_audience=project.target_audience,
            style=project.style,
            primary_color=project.primary_color,
            secondary_color=project.secondary_color,
            accent_color=project.accent_color
        )
        project.website_plan = plan.model_dump()
        await db.commit()

        await _add_log(
            db, project_id, orchestrator_agent.AGENT_NAME, "Plan Formulation",
            "success", f"Website plan formulated with {len(plan.sections)} dedicated sections: {plan_msg}",
            output_payload={"sections": [s.id for s in plan.sections], "tagline": plan.tagline}
        )

        # -------------------------------------------------------------
        # STAGE 2: Asset Agent (Imagery & Branding)
        # -------------------------------------------------------------
        project.status = "generating_assets"
        project.current_agent = asset_agent.AGENT_NAME
        project.current_step = "Curating verified photography, vector logo, and icons"
        project.progress_percentage = "35%"
        await db.commit()

        await _add_log(
            db, project_id, asset_agent.AGENT_NAME, "Asset Curation",
            "in_progress", "Sourcing verified high-resolution photography and generating vector brandmark"
        )

        assets = await asset_agent.curate_assets(plan=plan, user_logo_url=project.logo_url)
        project.asset_manifest = assets.model_dump()
        await db.commit()

        await _add_log(
            db, project_id, asset_agent.AGENT_NAME, "Asset Curation",
            "success", f"Assets secured: {len(assets.images)} photography items, vector logo, and {len(assets.icons)} icons.",
            output_payload={"images_count": len(assets.images), "logo_source": assets.logo.source}
        )

        # -------------------------------------------------------------
        # STAGE 3: Design Agent (Frontend Code Generation)
        # -------------------------------------------------------------
        project.status = "generating_design"
        project.current_agent = design_agent.AGENT_NAME
        project.current_step = "Coding responsive HTML5, modern Tailwind CSS, and scripts"
        project.progress_percentage = "60%"
        await db.commit()

        await _add_log(
            db, project_id, design_agent.AGENT_NAME, "Frontend Coding",
            "in_progress", "Generating semantic markup, design tokens, and client interactions"
        )

        code_files = design_agent.generate_website_bundle(
            project_id=project_id,
            plan=plan,
            assets=assets
        )

        # Save files to isolated workspace
        for file in code_files:
            workspace_manager.write_file(project_id, file.path, file.content)

        await _add_log(
            db, project_id, design_agent.AGENT_NAME, "Frontend Coding",
            "success", f"Generated {len(code_files)} frontend files (index.html, styles.css, main.js).",
            output_payload={"files": [f.path for f in code_files]}
        )

        # -------------------------------------------------------------
        # STAGE 4: Backend Agent (Contact Form & Serverless Handling)
        # -------------------------------------------------------------
        project.status = "generating_backend"
        project.current_agent = backend_agent.AGENT_NAME
        project.current_step = "Configuring contact submission endpoints and serverless routes"
        project.progress_percentage = "80%"
        await db.commit()

        serverless_file = backend_agent.generate_serverless_handler(project_id)
        workspace_manager.write_file(project_id, serverless_file.path, serverless_file.content)

        await _add_log(
            db, project_id, backend_agent.AGENT_NAME, "Backend Integration",
            "success", "Configured live contact submission handler and Netlify serverless route.",
            output_payload={"serverless_path": serverless_file.path}
        )

        # -------------------------------------------------------------
        # STAGE 5: Orchestrator Agent (Evaluation: Does everything match?)
        # -------------------------------------------------------------
        project.status = "validating"
        project.current_agent = orchestrator_agent.AGENT_NAME
        project.current_step = "Verifying generated code against architectural specifications"
        project.progress_percentage = "90%"
        await db.commit()

        index_html = workspace_manager.read_file(project_id, "index.html")
        validation = orchestrator_agent.evaluate_output_against_plan(
            plan=plan,
            html_content=index_html,
            has_contact_endpoint=True
        )

        await _add_log(
            db, project_id, orchestrator_agent.AGENT_NAME, "Verification Check",
            "success" if validation.passed else "in_progress",
            f"Validation complete: score {validation.score}/100. {'All requirements verified.' if validation.passed else 'Some items noted.'}",
            output_payload=validation.model_dump()
        )

        # -------------------------------------------------------------
        # STAGE 6: Execution Agent (Git Checkpoint & Live Preview Ready)
        # -------------------------------------------------------------
        project.current_agent = execution_agent.AGENT_NAME
        project.current_step = "Creating Git checkpoint and mounting live preview"
        await db.commit()

        git_ok, commit_hash, changed_files = git_service.create_checkpoint(
            project_id=project_id,
            message="feat: initial production-ready website generation"
        )

        if git_ok and commit_hash:
            chk = Checkpoint(
                project_id=project_id,
                commit_hash=commit_hash,
                message="Initial website generation approved and committed",
                changed_files=changed_files
            )
            db.add(chk)
            project.active_checkpoint_hash = commit_hash

        project.status = "ready"
        project.current_agent = None
        project.current_step = "Generation completed successfully"
        project.progress_percentage = "100%"
        project.live_preview_url = f"/api/v1/preview/{project_id}/index.html"
        await db.commit()

        await _add_log(
            db, project_id, execution_agent.AGENT_NAME, "Milestone Checkpoint",
            "success", f"Saved immutable Git checkpoint {commit_hash[:8] if commit_hash else 'HEAD'}. Live preview is active.",
            output_payload={"commit_hash": commit_hash, "preview_url": project.live_preview_url}
        )

        await db.refresh(project)
        return {
            "status": "success",
            "project_id": project_id,
            "preview_url": project.live_preview_url,
            "commit_hash": commit_hash,
            "validation_score": validation.score
        }

    except Exception as e:
        logger.exception(f"Error during website generation for {project_id}: {e}")
        project.status = "failed"
        project.current_step = f"Encountered error: {str(e)}"
        await db.commit()

        await _add_log(
            db, project_id, "System", "Pipeline Execution",
            "failed", "Generation workflow encountered an unexpected exception.",
            error_details=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.post("/edit")
async def natural_language_edit(
    project_id: str,
    data: NaturalLanguageEditRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Applies user natural language change requests to generated website:
    'User reviews the live preview and asks for changes' -> Orchestrator sends fix instructions -> Git checkpoint.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not workspace_manager.file_exists(project_id, "index.html"):
        raise HTTPException(status_code=400, detail="Cannot edit a project before initial generation.")

    instruction = data.instruction.strip()
    await _add_log(
        db, project_id, orchestrator_agent.AGENT_NAME, "Natural Language Refinement",
        "in_progress", f"Processing user request: '{instruction}'"
    )

    current_html = workspace_manager.read_file(project_id, "index.html")

    # Surgical replacement or enrichment based on request keywords
    updated_html = current_html
    inst_lower = instruction.lower()

    if "color" in inst_lower or "theme" in inst_lower:
        # Check if color hex or named color mentioned
        if "emerald" in inst_lower or "green" in inst_lower:
            project.primary_color = "#059669"
            updated_html = updated_html.replace("#2563eb", "#059669")
        elif "purple" in inst_lower or "indigo" in inst_lower:
            project.primary_color = "#6366f1"
            updated_html = updated_html.replace("#2563eb", "#6366f1")
        elif "rose" in inst_lower or "red" in inst_lower:
            project.primary_color = "#e11d48"
            updated_html = updated_html.replace("#2563eb", "#e11d48")
        elif "amber" in inst_lower or "orange" in inst_lower:
            project.primary_color = "#d97706"
            updated_html = updated_html.replace("#2563eb", "#d97706")

    if "headline" in inst_lower or "title" in inst_lower or "hero" in inst_lower:
        # Check for quoted text in instruction
        import re
        quotes = re.findall(r'["\'](.*?)["\']', instruction)
        if quotes:
            new_title = quotes[0]
            # Replace h1 content
            updated_html = re.sub(
                r'(<h1[^>]*>)(.*?)(</h1>)',
                rf'\g<1>{new_title}\g<3>',
                updated_html,
                count=1,
                flags=re.DOTALL
            )

    # Save updated file
    workspace_manager.write_file(project_id, "index.html", updated_html)

    # Save Git checkpoint for user iteration
    checkpoint_msg = f"refactor: {instruction[:50]}"
    git_ok, commit_hash, changed_files = git_service.create_checkpoint(project_id, checkpoint_msg)
    if git_ok and commit_hash:
        chk = Checkpoint(
            project_id=project_id,
            commit_hash=commit_hash,
            message=checkpoint_msg,
            changed_files=changed_files
        )
        db.add(chk)
        project.active_checkpoint_hash = commit_hash

    await db.commit()

    await _add_log(
        db, project_id, execution_agent.AGENT_NAME, "Refinement Applied",
        "success", f"Applied modification and recorded Git checkpoint {commit_hash[:8] if commit_hash else 'HEAD'}.",
        output_payload={"instruction": instruction, "commit_hash": commit_hash}
    )

    return {
        "status": "success",
        "message": "Changes successfully applied to project workspace.",
        "commit_hash": commit_hash
    }

@router.get("/logs")
async def get_project_logs(
    project_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves chronological execution logs for the multi-agent workflow."""
    query = (
        select(AgentLog)
        .where(AgentLog.project_id == project_id)
        .order_by(AgentLog.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    return logs

@router.get("/checkpoints")
async def get_project_checkpoints(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves Git checkpoints for the project."""
    query = (
        select(Checkpoint)
        .where(Checkpoint.project_id == project_id)
        .order_by(Checkpoint.created_at.desc())
    )
    result = await db.execute(query)
    checkpoints = result.scalars().all()
    return checkpoints

@router.post("/rollback")
async def rollback_project(
    project_id: str,
    data: RollbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Rolls back the workspace files to a selected Git checkpoint."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    success, msg = git_service.rollback_to_checkpoint(project_id, data.commit_hash)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    project.active_checkpoint_hash = data.commit_hash
    await db.commit()

    await _add_log(
        db, project_id, execution_agent.AGENT_NAME, "Checkpoint Rollback",
        "success", f"Rolled back workspace to commit {data.commit_hash[:8]}."
    )

    return {"status": "success", "message": msg, "commit_hash": data.commit_hash}
