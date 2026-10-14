from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.setting import Setting
from backend.app.config import settings
from backend.app.schemas.setting import SettingsUpdate, ProviderStatus
from backend.app.services.ai_provider import ai_provider

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])

def _mask_secret(val: str) -> str:
    if not val:
        return ""
    if len(val) <= 8:
        return "****"
    return val[:4] + "..." + val[-4:]

@router.get("")
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    """Retrieves all application settings with secrets masked, plus provider statuses."""
    # Check DB overrides
    query = select(Setting)
    res = await db.execute(query)
    db_settings = {s.key: s for s in res.scalars().all()}

    gemini_key = db_settings.get("GEMINI_API_KEY").value if "GEMINI_API_KEY" in db_settings else settings.GEMINI_API_KEY
    gemini_model = db_settings.get("GEMINI_MODEL").value if "GEMINI_MODEL" in db_settings else settings.GEMINI_MODEL
    unsplash_key = db_settings.get("UNSPLASH_ACCESS_KEY").value if "UNSPLASH_ACCESS_KEY" in db_settings else settings.UNSPLASH_ACCESS_KEY
    vercel_tok = db_settings.get("VERCEL_TOKEN").value if "VERCEL_TOKEN" in db_settings else settings.VERCEL_TOKEN
    netlify_tok = db_settings.get("NETLIFY_AUTH_TOKEN").value if "NETLIFY_AUTH_TOKEN" in db_settings else settings.NETLIFY_AUTH_TOKEN

    providers = [
        ProviderStatus(
            provider_name="Google Gemini",
            configured=bool(gemini_key),
            valid=bool(gemini_key),
            model=gemini_model or "gemini-2.5-flash",
            message="Active and ready" if gemini_key else "Not configured. Operating in high-fidelity fallback mode."
        ),
        ProviderStatus(
            provider_name="Netlify Deployments",
            configured=bool(netlify_tok),
            valid=bool(netlify_tok),
            model=None,
            message="Ready for direct site deployments" if netlify_tok else "Requires NETLIFY_AUTH_TOKEN and SITE_ID."
        ),
        ProviderStatus(
            provider_name="Vercel Deployments",
            configured=bool(vercel_tok),
            valid=bool(vercel_tok),
            model=None,
            message="Ready for edge deployments" if vercel_tok else "Requires VERCEL_TOKEN in Settings."
        ),
        ProviderStatus(
            provider_name="Unsplash Asset CDN",
            configured=bool(unsplash_key),
            valid=True,
            model=None,
            message="Curated category CDN active with verified fallbacks."
        )
    ]

    return {
        "settings": {
            "gemini_api_key_masked": _mask_secret(gemini_key),
            "gemini_model": gemini_model or "gemini-2.5-flash",
            "unsplash_access_key_masked": _mask_secret(unsplash_key),
            "vercel_token_masked": _mask_secret(vercel_tok),
            "netlify_auth_token_masked": _mask_secret(netlify_tok),
            "require_command_approval": settings.REQUIRE_COMMAND_APPROVAL,
            "allowlisted_commands": settings.ALLOWLISTED_COMMANDS
        },
        "providers": providers
    }

@router.post("")
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    """Persists settings updates into the database."""
    async def _upsert(key: str, val: Any, is_secret: bool):
        if val is None:
            return
        rec = await db.get(Setting, key)
        if not rec:
            rec = Setting(key=key, value=str(val), is_secret=is_secret)
            db.add(rec)
        else:
            rec.value = str(val)

    if data.gemini_api_key is not None:
        await _upsert("GEMINI_API_KEY", data.gemini_api_key, True)
        settings.GEMINI_API_KEY = data.gemini_api_key
    if data.gemini_model is not None:
        await _upsert("GEMINI_MODEL", data.gemini_model, False)
        settings.GEMINI_MODEL = data.gemini_model
    if data.unsplash_access_key is not None:
        await _upsert("UNSPLASH_ACCESS_KEY", data.unsplash_access_key, True)
        settings.UNSPLASH_ACCESS_KEY = data.unsplash_access_key
    if data.vercel_token is not None:
        await _upsert("VERCEL_TOKEN", data.vercel_token, True)
        settings.VERCEL_TOKEN = data.vercel_token
    if data.netlify_auth_token is not None:
        await _upsert("NETLIFY_AUTH_TOKEN", data.netlify_auth_token, True)
        settings.NETLIFY_AUTH_TOKEN = data.netlify_auth_token
    if data.require_command_approval is not None:
        await _upsert("REQUIRE_COMMAND_APPROVAL", data.require_command_approval, False)
        settings.REQUIRE_COMMAND_APPROVAL = data.require_command_approval

    await db.commit()
    return {"status": "success", "message": "Settings updated successfully."}

@router.post("/test-gemini")
async def test_gemini_connection(db: AsyncSession = Depends(get_db)):
    """Tests the configured Gemini API key."""
    # Check if DB has key
    rec = await db.get(Setting, "GEMINI_API_KEY")
    key = rec.value if rec and rec.value else settings.GEMINI_API_KEY

    is_valid, msg, model_name = await ai_provider.test_connection(api_key=key)
    return {
        "valid": is_valid,
        "message": msg,
        "model": model_name
    }
