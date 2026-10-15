from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.agent_log import AgentLog
from backend.app.schemas.approval import DeploymentApprovalRequest, DeploymentResponse
from backend.app.agents.execution_agent import execution_agent
from backend.app.services.deployment_service import deployment_service
from backend.app.services.subdomain_service import subdomain_service

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["Deployment"])

@router.get("/deployment-status")
async def get_deployment_readiness(project_id: str, db: AsyncSession = Depends(get_db)):
    """Checks pre-deployment validation readiness."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    ready, issues = deployment_service.validate_project_for_deployment(project_id)
    return {
        "project_id": project_id,
        "is_ready": ready,
        "validation_issues": issues,
        "deployment_status": project.deployment_status,
        "deployment_provider": project.deployment_provider,
        "deployment_url": project.deployment_url,
        "live_preview_url": project.live_preview_url
    }

@router.post("/deploy", response_model=DeploymentResponse)
async def trigger_deployment(
    project_id: str,
    data: DeploymentApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Explicit user deployment authorization:
    Validates the generated website, invokes the configured deployment provider,
    and returns verified live URL.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not data.confirm:
        raise HTTPException(status_code=400, detail="Deployment confirmation was not granted.")

    # Validate and verify domain ownership if custom domain is requested
    target_custom_domain = data.custom_domain or project.custom_domain
    if target_custom_domain:
        is_verified, verify_msg = subdomain_service.verify_custom_domain_ownership(target_custom_domain)
        if not is_verified:
            raise HTTPException(
                status_code=400,
                detail=f"Custom domain verification failed: {verify_msg}"
            )

    # Record agent log
    log = AgentLog(
        project_id=project_id,
        agent_name=execution_agent.AGENT_NAME,
        step_name="Deployment Authorization",
        status="in_progress",
        message=f"Deploying project to provider: {data.provider}"
    )
    db.add(log)
    await db.commit()

    # Execute deployment
    result = await execution_agent.prepare_and_deploy(
        project_id=project_id,
        provider=data.provider,
        custom_domain=data.custom_domain
    )

    # Update project record
    project.deployment_status = result.status
    project.deployment_provider = data.provider
    if result.status == "deployed" and result.deployment_url:
        project.deployment_url = result.deployment_url

    # Finalize log
    log.status = "success" if result.status == "deployed" else "failed"
    log.message = result.message
    log.output_payload = {"url": result.deployment_url}
    await db.commit()

    return result
