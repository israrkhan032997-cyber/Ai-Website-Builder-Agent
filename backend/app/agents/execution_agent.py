import logging
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.command_executor import command_executor
from backend.app.services.git_service import git_service
from backend.app.services.deployment_service import deployment_service
from backend.app.services.workspace_manager import workspace_manager
from backend.app.models.checkpoint import Checkpoint
from backend.app.models.command_approval import CommandApproval
from backend.app.schemas.approval import DeploymentResponse

logger = logging.getLogger(__name__)

class ExecutionAgent:
    """
    Execution and Deployment Agent:
    - Gatekeeper for terminal commands and build operations.
    - Prompts user for explicit authorization prior to running commands.
    - Saves immutable Git checkpoints upon milestone approvals.
    - Performs pre-deployment structural and semantic validation.
    - Coordinates deployment requests and verifies published URLs.
    """

    AGENT_NAME = "Execution and Deployment Agent"

    async def request_command_approval(
        self,
        db: AsyncSession,
        project_id: str,
        command: str,
        purpose: str
    ) -> CommandApproval:
        """
        As depicted in the specification flowchart:
        'Execution Agent asks permission before running commands'.
        Registers a pending command approval.
        """
        return await command_executor.register_approval_request(
            db=db,
            project_id=project_id,
            command=command,
            purpose=purpose
        )

    async def execute_approved_command_and_checkpoint(
        self,
        db: AsyncSession,
        project_id: str,
        approval_id: int,
        checkpoint_message: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Executes an approved command and automatically saves a Git checkpoint:
        'Git saves a checkpoint once approved'.
        Returns: (success, execution_output, commit_hash)
        """
        approval = await db.get(CommandApproval, approval_id)
        if not approval:
            return False, "Approval record not found.", None

        if approval.status != "approved":
            return False, f"Cannot execute command with status '{approval.status}'. Approval required.", None

        # Execute command in workspace
        success, output = command_executor.execute_approved_command(
            project_id=project_id,
            command=approval.command
        )

        approval.execution_output = output
        approval.status = "executed" if success else "failed"

        commit_hash = None
        if success:
            # Save atomic git checkpoint
            git_ok, commit_hash, changed_files = git_service.create_checkpoint(
                project_id=project_id,
                message=checkpoint_message or f"Verified: {approval.purpose}"
            )
            if git_ok and commit_hash:
                checkpoint_rec = Checkpoint(
                    project_id=project_id,
                    commit_hash=commit_hash,
                    message=checkpoint_message or approval.purpose,
                    changed_files=changed_files
                )
                db.add(checkpoint_rec)

        await db.commit()
        return success, output, commit_hash

    async def prepare_and_deploy(
        self,
        project_id: str,
        provider: str = "local",
        custom_domain: Optional[str] = None
    ) -> DeploymentResponse:
        """
        Deploys project after validation:
        'Execution Agent asks permission to deploy' -> 'Live website link is ready'
        """
        valid, issues = deployment_service.validate_project_for_deployment(project_id)
        if not valid:
            return DeploymentResponse(
                project_id=project_id,
                provider=provider,
                status="failed",
                deployment_url=None,
                live_preview_url=None,
                message=f"Pre-deployment validation failed: {'; '.join(issues)}"
            )

        if provider == "netlify":
            success, url, msg = await deployment_service.deploy_netlify(project_id)
        elif provider == "vercel":
            success, url, msg = await deployment_service.deploy_vercel(project_id)
        else: # local live preview deployment
            success, url, msg = await deployment_service.deploy_local(project_id)

        return DeploymentResponse(
            project_id=project_id,
            provider=provider,
            status="deployed" if success else "failed",
            deployment_url=url if success else None,
            live_preview_url=url if success else None,
            message=msg
        )

execution_agent = ExecutionAgent()
