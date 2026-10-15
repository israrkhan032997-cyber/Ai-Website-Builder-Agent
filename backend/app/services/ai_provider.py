import json
import logging
import re
from typing import Type, TypeVar, Optional, Dict, Any, Tuple
from pydantic import BaseModel
from google import genai
from google.genai import types
from backend.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class AIProviderService:
    """
    Manages genuine Google Gemini AI integrations with secure key retrieval,
    structured schema validation, retry handling, and fallback resilience.
    """

    def __init__(self):
        self._cached_api_key: Optional[str] = None
        self._client: Optional[genai.Client] = None

    def get_api_key(self, override_key: Optional[str] = None) -> Optional[str]:
        """Resolves active API key from override, environment, or settings."""
        if override_key and override_key.strip():
            return override_key.strip()
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            return settings.GEMINI_API_KEY.strip()
        return None

    def get_client(self, api_key: Optional[str] = None) -> Optional[genai.Client]:
        """Instantiates or caches Google GenAI client."""
        resolved_key = self.get_api_key(api_key)
        if not resolved_key:
            return None

        if self._client is None or self._cached_api_key != resolved_key:
            self._cached_api_key = resolved_key
            self._client = genai.Client(api_key=resolved_key)

        return self._client

    def is_configured(self, api_key: Optional[str] = None) -> bool:
        """Checks if a Gemini API key is currently configured."""
        return bool(self.get_api_key(api_key))

    async def test_connection(self, api_key: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Validates the Gemini API key by making a lightweight test ping.
        Returns: (is_valid, message, model_name)
        """
        resolved_key = self.get_api_key(api_key)
        if not resolved_key:
            return False, "Gemini API key is not configured. Provide an API key in Settings.", None

        try:
            client = genai.Client(api_key=resolved_key)
            model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
            response = client.models.generate_content(
                model=model_name,
                contents="Respond with only the word: OK",
            )
            if response and response.text:
                return True, "Successfully connected to Google Gemini API.", model_name
            return False, "Empty response from Gemini provider.", model_name
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Gemini test connection failed: {err_msg}")
            return False, f"Gemini connection failed: {err_msg}", None

    def _extract_json(self, raw_text: str) -> Dict[str, Any]:
        """Extracts JSON object from text, stripping markdown fences if present."""
        text = raw_text.strip()
        # Remove markdown code fences
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            text = fence_match.group(1).strip()

        # Find first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]

        return json.loads(text)

    async def generate_structured(
        self,
        prompt: str,
        schema_class: Type[T],
        system_instruction: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Tuple[Optional[T], str]:
        """
        Calls Gemini to generate structured output conforming to the Pydantic schema.
        Returns: (parsed_pydantic_instance, log_message)
        """
        client = self.get_client(api_key)
        if not client:
            return None, "No active Gemini API key configured."

        candidate_models = [model_name] if model_name else [settings.GEMINI_MODEL, "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"]
        # Filter unique and non-empty
        models_to_try = [m for i, m in enumerate(candidate_models) if m and m not in candidate_models[:i]]

        sys_prompt = system_instruction or "You are an expert AI software architect and UI designer. You always return valid, complete JSON matching the requested schema."
        full_prompt = f"{prompt}\n\nStrict requirement: Output only valid JSON matching this schema: {schema_class.model_json_schema()}"

        last_err = ""
        for model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    response_mime_type="application/json",
                    temperature=0.3
                )
                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config=config
                )

                if not response or not response.text:
                    continue

                data = self._extract_json(response.text)
                instance = schema_class.model_validate(data)
                return instance, f"Successfully generated via {model}."
            except Exception as e:
                last_err = str(e)
                logger.warning(f"Structured generation with model {model} failed: {e}")
                continue

        return None, f"Gemini generation error across models: {last_err}"

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Generates freeform text using Gemini with resilient model fallback.
        """
        client = self.get_client(api_key)
        if not client:
            return None

        candidate_models = [model_name] if model_name else [settings.GEMINI_MODEL, "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"]
        models_to_try = [m for i, m in enumerate(candidate_models) if m and m not in candidate_models[:i]]

        sys_prompt = system_instruction or "You are a professional, helpful conversational AI assistant."

        for model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    temperature=0.7
                )
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Text generation with model {model} failed: {e}")
                continue

        return None

ai_provider = AIProviderService()

