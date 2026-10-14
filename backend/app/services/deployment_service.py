import os
import httpx
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
from backend.app.config import settings
from backend.app.services.workspace_manager import workspace_manager

class DeploymentService:
    """
    Manages genuine deployment integrations (Local Preview, Netlify, Vercel).
    Validates projects before deployment and returns truthful live published URLs.
    """

    def validate_project_for_deployment(self, project_id: str) -> Tuple[bool, List[str]]:
        """Validates that project files are structurally complete and ready for deployment."""
        issues = []
        if not workspace_manager.file_exists(project_id, "index.html"):
            issues.append("Missing primary entrypoint 'index.html'.")

        index_content = ""
        try:
            index_content = workspace_manager.read_file(project_id, "index.html")
            if len(index_content.strip()) < 100:
                issues.append("index.html is suspiciously short or empty.")
            if "<!DOCTYPE html>" not in index_content and "<html" not in index_content:
                issues.append("index.html does not appear to be valid HTML document.")
        except Exception as e:
            issues.append(f"Could not read index.html: {str(e)}")

        return len(issues) == 0, issues

    async def deploy_local(self, project_id: str, host: Optional[str] = None, port: Optional[int] = None) -> Tuple[bool, str, str]:
        """
        Deploys project to the local live preview server.
        Returns: (success, live_url, message)
        """
        valid, issues = self.validate_project_for_deployment(project_id)
        if not valid:
            return False, "", f"Deployment validation failed: {', '.join(issues)}"

        h = host or settings.HOST
        p = port or settings.PORT
        preview_url = f"http://{h}:{p}/api/v1/preview/{project_id}/index.html"
        return True, preview_url, "Successfully published to local high-performance preview server."

    async def deploy_netlify(
        self,
        project_id: str,
        auth_token: Optional[str] = None,
        site_id: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Deploys project to Netlify using the official Netlify Deploy API.
        Uploads zip archive of project workspace.
        """
        valid, issues = self.validate_project_for_deployment(project_id)
        if not valid:
            return False, "", f"Validation failed before Netlify deploy: {', '.join(issues)}"

        token = auth_token or settings.NETLIFY_AUTH_TOKEN
        site = site_id or settings.NETLIFY_SITE_ID

        if not token:
            return False, "", "Netlify deployment requires NETLIFY_AUTH_TOKEN in Settings or environment."
        if not site:
            return False, "", "Netlify deployment requires NETLIFY_SITE_ID in Settings or environment."

        zip_path = workspace_manager.create_project_zip(project_id)

        try:
            url = f"https://api.netlify.com/api/v1/sites/{site}/deploys"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/zip"
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(zip_path, "rb") as f:
                    response = await client.post(url, headers=headers, content=f.read())

            if response.status_code in [200, 201]:
                data = response.json()
                live_url = data.get("ssl_url") or data.get("url") or data.get("deploy_ssl_url")
                return True, live_url, f"Published to Netlify! Deploy state: {data.get('state', 'ready')}"
            else:
                return False, "", f"Netlify API error ({response.status_code}): {response.text}"
        except Exception as e:
            return False, "", f"Netlify deployment network exception: {str(e)}"
        finally:
            if zip_path.exists():
                zip_path.unlink(missing_ok=True)

    async def deploy_vercel(
        self,
        project_id: str,
        auth_token: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Deploys project to Vercel using the Vercel Deployments API.
        """
        valid, issues = self.validate_project_for_deployment(project_id)
        if not valid:
            return False, "", f"Validation failed before Vercel deploy: {', '.join(issues)}"

        token = auth_token or settings.VERCEL_TOKEN
        if not token:
            return False, "", "Vercel deployment requires VERCEL_TOKEN in Settings or environment."

        files_list = workspace_manager.list_files(project_id)
        vercel_files = []
        for f in files_list:
            content = workspace_manager.read_file(project_id, f["path"])
            vercel_files.append({
                "file": f["path"],
                "data": content
            })

        try:
            url = "https://api.vercel.com/v13/deployments"
            if team_id or settings.VERCEL_ORG_ID:
                url += f"?teamId={team_id or settings.VERCEL_ORG_ID}"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "name": f"site-{project_id[:8]}",
                "files": vercel_files,
                "projectSettings": {
                    "framework": None
                }
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)

            if response.status_code in [200, 201]:
                data = response.json()
                raw_url = data.get("url")
                live_url = f"https://{raw_url}" if raw_url and not raw_url.startswith("http") else raw_url
                return True, live_url, f"Successfully deployed to Vercel: {live_url}"
            else:
                return False, "", f"Vercel API error ({response.status_code}): {response.text}"
        except Exception as e:
            return False, "", f"Vercel deployment network exception: {str(e)}"

deployment_service = DeploymentService()
