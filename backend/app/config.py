import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
STORAGE_DIR = BASE_DIR / "storage"
PROJECTS_DIR = STORAGE_DIR / "projects"

class Settings(BaseSettings):
    APP_NAME: str = "AI Website Builder Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8008
    HOST: str = "127.0.0.1"
    SECRET_KEY: str = "dev-ai-website-builder-agent-secure-secret-key-32b"

    DATABASE_URL: str = f"sqlite+aiosqlite:///{STORAGE_DIR / 'website_builder.db'}"
    PROJECTS_STORAGE_DIR: str = str(PROJECTS_DIR)

    # Gemini AI configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Unsplash API configuration
    UNSPLASH_ACCESS_KEY: str = ""

    # Email / SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    NOTIFICATION_EMAIL: str = ""

    # Deployment
    VERCEL_TOKEN: str = ""
    VERCEL_ORG_ID: str = ""
    VERCEL_PROJECT_ID: str = ""
    NETLIFY_AUTH_TOKEN: str = ""
    NETLIFY_SITE_ID: str = ""

    # Command Execution Security
    REQUIRE_COMMAND_APPROVAL: bool = True
    ALLOWLISTED_COMMANDS: str = "npm run build,npm test,npm run lint,git status,git log,git diff,git commit"
    COMMAND_TIMEOUT_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(BASE_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure critical storage folders exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
