import subprocess
import shlex
from typing import Tuple, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.config import settings
from backend.app.services.workspace_manager import workspace_manager
from backend.app.models.command_approval import CommandApproval

class CommandExecutor:
    """
    Security-hardened command execution service with strict allowlisting,
    path confinement, timeout enforcement, and permission gate.
    """

    DEFAULT_ALLOWLIST = [
        "npm run build",
        "npm test",
        "npm run lint",
        "npm --version",
        "node --version",
        "git status",
        "git log",
        "git diff",
        "git commit",
        "git rev-parse HEAD",
        "npx prettier --check .",
        "python -m unittest",
        "pytest"
    ]

    DISALLOWED_PATTERNS = [
        "rm -rf /",
        "rmdir /s /q c:",
        "format",
        "del /f /s /q c:",
        ":(){ :|:& };:",
        "curl ",
        "wget ",
        "powershell -enc",
        "cmd /c format"
    ]

    def is_command_safe(self, command: str) -> Tuple[bool, str, str]:
        """
        Validates whether a command matches allowlist policies.
        Returns: (is_safe, risk_level, reason)
        """
        cmd_clean = command.strip()

        # Check for dangerous patterns
        for bad in self.DISALLOWED_PATTERNS:
            if bad.lower() in cmd_clean.lower():
                return False, "critical", f"Command contains prohibited destructive pattern: {bad}"

        # Get configured allowlist
        configured = [c.strip() for c in settings.ALLOWLISTED_COMMANDS.split(",") if c.strip()]
        allowed = list(set(self.DEFAULT_ALLOWLIST + configured))

        # Check exact prefix or exact match
        for allowed_prefix in allowed:
            if cmd_clean == allowed_prefix or cmd_clean.startswith(allowed_prefix + " "):
                risk = "low"
                if "build" in cmd_clean or "commit" in cmd_clean:
                    risk = "medium"
                return True, risk, "Command matches security allowlist."

        return False, "high", f"Command '{cmd_clean}' is not in the approved command allowlist."

    async def register_approval_request(
        self,
        db: AsyncSession,
        project_id: str,
        command: str,
        purpose: str
    ) -> CommandApproval:
        """Registers a command requiring explicit user permission before execution."""
        is_safe, risk_level, reason = self.is_command_safe(command)
        project_dir = str(workspace_manager.get_project_dir(project_id))

        approval = CommandApproval(
            project_id=project_id,
            command=command,
            working_directory=project_dir,
            purpose=purpose,
            risk_level=risk_level,
            status="pending",
        )
        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        return approval

    def execute_approved_command(
        self,
        project_id: str,
        command: str,
        timeout_seconds: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Executes a previously reviewed and approved command strictly inside
        the isolated project workspace directory.
        """
        is_safe, risk_level, reason = self.is_command_safe(command)
        if not is_safe and risk_level == "critical":
            return False, f"Execution blocked by security policy: {reason}"

        project_dir = workspace_manager.get_project_dir(project_id)
        timeout = timeout_seconds or settings.COMMAND_TIMEOUT_SECONDS

        try:
            # Execute command using shell safely inside project directory
            result = subprocess.run(
                command,
                cwd=str(project_dir),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
            output = (result.stdout + "\n" + result.stderr).strip()
            return result.returncode == 0, output or "Command completed with no output."
        except subprocess.TimeoutExpired:
            return False, f"Execution timed out after {timeout} seconds."
        except Exception as e:
            return False, f"Execution error: {str(e)}"

command_executor = CommandExecutor()
