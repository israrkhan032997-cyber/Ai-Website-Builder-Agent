import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import HTTPException
from backend.app.config import settings

class WorkspaceManager:
    """
    Manages isolated filesystem workspaces for generated projects.
    Enforces strict path security, prevents directory traversal, and handles
    file creation, listing, reading, and packaging.
    """

    def __init__(self, base_storage_dir: Optional[str] = None):
        self.base_dir = Path(base_storage_dir or settings.PROJECTS_STORAGE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_id: str) -> Path:
        """Get absolute path to project workspace with directory traversal protection."""
        # Sanitize project_id to alphanumeric and hyphens only
        clean_id = "".join(c for c in project_id if c.isalnum() or c in "-_")
        if not clean_id:
            raise HTTPException(status_code=400, detail="Invalid project ID format.")

        project_path = (self.base_dir / clean_id).resolve()
        # Verify boundary
        if not str(project_path).startswith(str(self.base_dir)):
            raise HTTPException(status_code=403, detail="Access denied: Path traversal detected.")

        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    def _resolve_safe_path(self, project_id: str, relative_path: str) -> Path:
        """Resolves and validates a relative path inside the project workspace."""
        project_dir = self.get_project_dir(project_id)
        # Normalize and remove leading slashes
        clean_rel = os.path.normpath(relative_path.strip("/\\"))
        if clean_rel.startswith("..") or "/../" in clean_rel or "\\..\\" in clean_rel:
            raise HTTPException(status_code=403, detail="Access denied: Directory traversal detected.")

        target = (project_dir / clean_rel).resolve()
        if not str(target).startswith(str(project_dir)):
            raise HTTPException(status_code=403, detail="Access denied: File outside project root.")

        return target

    def write_file(self, project_id: str, relative_path: str, content: str) -> str:
        """Safely write content to a file in the project workspace."""
        target_path = self._resolve_safe_path(project_id, relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return str(target_path)

    def read_file(self, project_id: str, relative_path: str) -> str:
        """Safely read content from a file in the project workspace."""
        target_path = self._resolve_safe_path(project_id, relative_path)
        if not target_path.exists() or not target_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {relative_path}")
        return target_path.read_text(encoding="utf-8", errors="replace")

    def file_exists(self, project_id: str, relative_path: str) -> bool:
        """Check if file exists in project workspace."""
        try:
            target_path = self._resolve_safe_path(project_id, relative_path)
            return target_path.exists() and target_path.is_file()
        except HTTPException:
            return False

    def list_files(self, project_id: str) -> List[Dict[str, any]]:
        """List all files in project workspace with sizes and relative paths."""
        project_dir = self.get_project_dir(project_id)
        file_list = []

        for root, dirs, files in os.walk(project_dir):
            # Ignore hidden directories like .git
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for file in files:
                if file.startswith("."):
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(project_dir).as_posix()
                file_list.append({
                    "path": rel_path,
                    "size_bytes": full_path.stat().st_size,
                    "is_entry": rel_path in ["index.html", "package.json"]
                })

        return sorted(file_list, key=lambda x: x["path"])

    def create_project_zip(self, project_id: str, output_zip_path: Optional[Path] = None) -> Path:
        """Create a zip archive of all project files excluding .git."""
        project_dir = self.get_project_dir(project_id)
        if not output_zip_path:
            output_zip_path = self.base_dir / f"{project_id}_export.zip"

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for file in files:
                    if file.startswith("."):
                        continue
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(project_dir)
                    zipf.write(full_path, arcname=rel_path)

        return output_zip_path

    def delete_project_workspace(self, project_id: str) -> bool:
        """Deletes project directory safely."""
        project_dir = self.get_project_dir(project_id)
        if project_dir.exists():
            shutil.rmtree(project_dir, ignore_errors=True)
            return True
        return False

workspace_manager = WorkspaceManager()
