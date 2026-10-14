import mimetypes
from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse, FileResponse
from backend.app.services.workspace_manager import workspace_manager

router = APIRouter(prefix="/api/v1/preview/{project_id}", tags=["Live Preview"])

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
@router.get("/index.html", response_class=HTMLResponse)
async def serve_preview_root(project_id: str):
    """Serves the generated website index.html document for live preview in an iframe."""
    if not workspace_manager.file_exists(project_id, "index.html"):
        return HTMLResponse(
            content="""<!DOCTYPE html>
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
</html>""",
            status_code=200
        )

    content = workspace_manager.read_file(project_id, "index.html")
    return HTMLResponse(content=content, status_code=200)

@router.get("/{file_path:path}")
async def serve_preview_assets(project_id: str, file_path: str):
    """Serves styles, scripts, and media assets for the live preview iframe."""
    clean_path = file_path.strip("/")
    if not clean_path or clean_path == "index.html":
        return await serve_preview_root(project_id)

    if not workspace_manager.file_exists(project_id, clean_path):
        raise HTTPException(status_code=404, detail=f"Asset not found: {clean_path}")

    target_file = workspace_manager._resolve_safe_path(project_id, clean_path)
    mime_type, _ = mimetypes.guess_type(str(target_file))

    return FileResponse(
        path=str(target_file),
        media_type=mime_type or "application/octet-stream"
    )
