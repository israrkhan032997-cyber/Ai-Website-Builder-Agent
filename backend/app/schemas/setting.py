from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict

class SettingItem(BaseModel):
    key: str
    value: Optional[str]
    is_secret: bool
    description: Optional[str]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SettingsUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    unsplash_access_key: Optional[str] = None
    vercel_token: Optional[str] = None
    netlify_auth_token: Optional[str] = None
    require_command_approval: Optional[bool] = None

class ProviderStatus(BaseModel):
    provider_name: str
    configured: bool
    valid: bool
    model: Optional[str] = None
    message: str
