import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.routes import (
    projects_router,
    agents_router,
    preview_router,
    contact_router,
    approvals_router,
    deployment_router,
    settings_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_website_builder")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes persistent database tables and verify storage directories."""
    logger.info("Initializing AI Website Builder Agent database...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down AI Website Builder Agent.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Professional multi-agent system for planning, designing, coding, previewing, and deploying websites.",
    version="1.0.0",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check server logs for details."}
    )

# Register API Routers
app.include_router(projects_router)
app.include_router(agents_router)
app.include_router(preview_router)
app.include_router(contact_router)
app.include_router(approvals_router)
app.include_router(deployment_router)
app.include_router(settings_router)

@app.get("/api/v1/health", tags=["Health"])
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint returning system status."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "storage_ready": True
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
