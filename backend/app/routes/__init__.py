from backend.app.routes.projects import router as projects_router
from backend.app.routes.agents import router as agents_router
from backend.app.routes.preview import router as preview_router
from backend.app.routes.contact import router as contact_router
from backend.app.routes.approvals import router as approvals_router
from backend.app.routes.deployment import router as deployment_router
from backend.app.routes.settings import router as settings_router

__all__ = [
    "projects_router",
    "agents_router",
    "preview_router",
    "contact_router",
    "approvals_router",
    "deployment_router",
    "settings_router"
]
