import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from backend.app.services.workspace_manager import workspace_manager

class GitService:
    """
    Manages real Git versioning and checkpoints for generated website projects.
    Enforces atomic commits, history tracking, and safe rollbacks.
    """

    def __init__(self):
        self.git_available = shutil.which("git") is not None

    def _run_git(self, project_id: str, args: List[str]) -> Tuple[bool, str]:
        """Runs a git command inside the project directory."""
        if not self.git_available:
            return False, "Git is not installed on this system."

        project_dir = workspace_manager.get_project_dir(project_id)
        try:
            cmd = ["git"] + args
            result = subprocess.run(
                cmd,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace"
            )
            output = result.stdout.strip() or result.stderr.strip()
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            return False, "Git command timed out after 30 seconds."
        except Exception as e:
            return False, str(e)

    def init_repository(self, project_id: str) -> Tuple[bool, str]:
        """Initialize git repo for project if not already initialized."""
        project_dir = workspace_manager.get_project_dir(project_id)
        git_dir = project_dir / ".git"

        if git_dir.exists():
            return True, "Git repository already initialized."

        success, out = self._run_git(project_id, ["init"])
        if not success:
            return False, out

        # Configure local git user to avoid errors on commit
        self._run_git(project_id, ["config", "user.name", "AI Website Builder Agent"])
        self._run_git(project_id, ["config", "user.email", "agent@builder.local"])
        self._run_git(project_id, ["branch", "-M", "main"])

        # Write .gitignore inside project workspace
        workspace_manager.write_file(
            project_id,
            ".gitignore",
            "node_modules/\ndist/\n.env\n*.log\n"
        )
        return True, "Git repository initialized."

    def create_checkpoint(self, project_id: str, message: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Stages all current project files and creates a Git commit checkpoint.
        Returns: (success, commit_hash, list_of_changed_files)
        """
        self.init_repository(project_id)

        # Stage files
        success, out = self._run_git(project_id, ["add", "."])
        if not success:
            return False, None, []

        # Check status to see changed files
        _, status_out = self._run_git(project_id, ["status", "--porcelain"])
        changed = []
        if status_out:
            for line in status_out.splitlines():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    changed.append(parts[1])

        # Commit
        commit_success, commit_out = self._run_git(project_id, ["commit", "-m", message])
        if not commit_success:
            # If nothing to commit, return latest commit hash
            if "nothing to commit" in commit_out:
                _, rev_out = self._run_git(project_id, ["rev-parse", "HEAD"])
                return True, rev_out.strip(), changed
            return False, None, changed

        # Get latest commit hash
        _, rev_out = self._run_git(project_id, ["rev-parse", "HEAD"])
        commit_hash = rev_out.strip()
        return True, commit_hash, changed

    def get_commit_history(self, project_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Retrieve commit history for the project."""
        success, out = self._run_git(
            project_id,
            ["log", f"-n{limit}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"]
        )
        if not success or not out:
            return []

        commits = []
        for line in out.splitlines():
            parts = line.strip().split("|", maxsplit=3)
            if len(parts) == 4:
                commits.append({
                    "commit_hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })
        return commits

    def rollback_to_checkpoint(self, project_id: str, commit_hash: str) -> Tuple[bool, str]:
        """Roll back workspace to a specific commit checkpoint."""
        # Sanitize commit hash
        clean_hash = "".join(c for c in commit_hash if c.isalnum())
        if len(clean_hash) < 6:
            return False, "Invalid commit hash provided."

        # Hard reset workspace to target commit
        success, out = self._run_git(project_id, ["reset", "--hard", clean_hash])
        if not success:
            return False, f"Failed to rollback: {out}"

        return True, f"Successfully rolled back to checkpoint {clean_hash[:8]}."

git_service = GitService()
