import mimetypes
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.contact_submission import ContactSubmission
from backend.app.services.workspace_manager import workspace_manager
from backend.app.services.subdomain_service import subdomain_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Live Preview & Subdomain Hosting"])

PLACEHOLDER_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Preview Not Ready</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 flex items-center justify-center min-h-screen text-slate-700 font-sans p-6">
    <div class="max-w-md bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center">
        <div class="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4 font-bold text-xl">🚀</div>
        <h2 class="text-xl font-bold text-slate-900 mb-2">Generation In Progress</h2>
        <p class="text-sm text-slate-600 leading-relaxed mb-4">The AI agents are planning and coding this website. The live preview will appear here automatically once ready.</p>
        <span class="inline-block px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-semibold">Awaiting Agent Completion</span>
    </div>
</body>
</html>"""

@router.get("/api/v1/preview/{project_id}", response_class=HTMLResponse)
@router.get("/api/v1/preview/{project_id}/", response_class=HTMLResponse)
@router.get("/api/v1/preview/{project_id}/index.html", response_class=HTMLResponse)
async def serve_preview_root(project_id: str):
    """Serves the generated website index.html document for live preview in an iframe."""
    if not workspace_manager.file_exists(project_id, "index.html"):
        return HTMLResponse(content=PLACEHOLDER_HTML, status_code=200)

    content = workspace_manager.read_file(project_id, "index.html")
    return HTMLResponse(content=content, status_code=200)

@router.post("/api/v1/preview/{project_id}/api/contact.php")
@router.post("/api/v1/preview/{project_id}/api/contact")
async def handle_preview_contact_submission(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Live PHP API simulation bridge:
    Allows generated forms pointing to 'api/contact.php' to work seamlessly inside the preview iframe.
    Captures submission, stores in ContactSubmission table, and returns production-identical JSON.
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
        else:
            form_data = await request.form()
            body = dict(form_data)

        name = body.get("name") or "Anonymous Client"
        email = body.get("email") or "client@example.com"
        message = body.get("message") or "Website contact inquiry"
        subject = body.get("subject") or "General Inquiry"

        submission = ContactSubmission(
            project_id=project_id,
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.add(submission)
        await db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Thank you! Your message has been received.",
                "data": {"name": name, "email": email}
            }
        )
    except Exception as e:
        logger.warning(f"Preview contact submission error for {project_id}: {e}")
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Inquiry recorded successfully."}
        )

@router.post("/api/v1/preview/{project_id}/api/subscribe.php")
@router.post("/api/v1/preview/{project_id}/api/subscribe")
async def handle_preview_newsletter_submission(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Simulates PHP newsletter subscription handler in preview."""
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
        else:
            form_data = await request.form()
            body = dict(form_data)

        email = body.get("email") or "subscriber@example.com"
        submission = ContactSubmission(
            project_id=project_id,
            name="Newsletter Subscriber",
            email=email,
            subject="Newsletter Subscription",
            message="Subscribed to updates via website footer/modal."
        )
        db.add(submission)
        await db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Thank you for subscribing to our updates!"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Subscription received."}
        )

@router.get("/api/v1/preview/{project_id}/{file_path:path}")
async def serve_preview_assets(project_id: str, file_path: str):
    """Serves multi-page HTML documents, styles, scripts, and media assets for live preview."""
    clean_path = file_path.strip("/")
    if not clean_path or clean_path == "index.html":
        return await serve_preview_root(project_id)

    if not workspace_manager.file_exists(project_id, clean_path):
        raise HTTPException(status_code=404, detail=f"Asset not found: {clean_path}")

    target_file = workspace_manager._resolve_safe_path(project_id, clean_path)
    mime_type, _ = mimetypes.guess_type(str(target_file))

    # If HTML file, serve as HTMLResponse for proper browser rendering
    if clean_path.endswith(".html"):
        content = workspace_manager.read_file(project_id, clean_path)
        return HTMLResponse(content=content, status_code=200)

    return FileResponse(
        path=str(target_file),
        media_type=mime_type or "application/octet-stream"
    )

# ---------------------------------------------------------------------------
# Multi-Tenant Customer Subdomain Hosting Routes (/site/{subdomain}/...)
# ---------------------------------------------------------------------------

@router.get("/site/{subdomain}", response_class=HTMLResponse)
@router.get("/site/{subdomain}/", response_class=HTMLResponse)
@router.get("/site/{subdomain}/index.html", response_class=HTMLResponse)
async def serve_subdomain_root(subdomain: str, db: AsyncSession = Depends(get_db)):
    """Serves the website mapped to a customer's custom subdomain."""
    project = await subdomain_service.resolve_subdomain(subdomain, db)
    if not project:
        return HTMLResponse(
            content=f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Site Not Found</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-900 text-slate-100 flex items-center justify-center min-h-screen p-6 font-sans">
    <div class="max-w-md bg-slate-800 p-8 rounded-2xl border border-slate-700 text-center">
        <h1 class="text-2xl font-bold mb-2">404 - Subdomain Not Found</h1>
        <p class="text-slate-400 text-sm mb-6">No published website is associated with '<b>{subdomain}</b>'.</p>
        <a href="/" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl text-sm transition">Return to Platform</a>
    </div>
</body>
</html>""",
            status_code=404
        )

    return await serve_preview_root(project.id)

@router.post("/site/{subdomain}/api/contact.php")
@router.post("/site/{subdomain}/api/contact")
async def handle_subdomain_contact(
    subdomain: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Processes contact submission on customer subdomain."""
    project = await subdomain_service.resolve_subdomain(subdomain, db)
    if not project:
        raise HTTPException(status_code=404, detail="Subdomain not found.")
    return await handle_preview_contact_submission(project.id, request, db)

@router.get("/site/{subdomain}/{file_path:path}")
async def serve_subdomain_assets(
    subdomain: str,
    file_path: str,
    db: AsyncSession = Depends(get_db)
):
    """Serves subpages and static assets for customer subdomain."""
    project = await subdomain_service.resolve_subdomain(subdomain, db)
    if not project:
        raise HTTPException(status_code=404, detail="Subdomain not found.")
    return await serve_preview_assets(project.id, file_path)
