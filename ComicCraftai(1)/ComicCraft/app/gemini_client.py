from __future__ import annotations

from typing import Type, TypeVar

from pydantic import BaseModel

from .config import get_settings

T = TypeVar("T", bound=BaseModel)


class GeminiError(RuntimeError):
    """Raised when a Gemini request cannot be completed."""


class GeminiClient:
    def __init__(self) -> None:
        from google import genai

        settings = get_settings()
        if not settings.gemini_api_key:
            raise GeminiError(
                "GEMINI_API_KEY is not configured. Add it to .env or use IMAGE_PROVIDER=mock for tests."
            )
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate_structured(
        self,
        model: str,
        prompt: str,
        schema: Type[T],
    ) -> T:
        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.9,
                ),
            )
            text = getattr(response, "text", None)
            if not text:
                raise GeminiError("Gemini returned an empty response.")
            return schema.model_validate_json(text)
        except Exception as exc:
            if isinstance(exc, GeminiError):
                raise
            raise GeminiError(f"Gemini request failed: {exc}") from exc

    def generate_text(self, model: str, prompt: str) -> str:
        try:
            from google.genai import types

            response = self.client.models.generate_content(model=model, contents=prompt)
            text = getattr(response, "text", "")
            if not text.strip():
                raise GeminiError("Gemini returned an empty response.")
            return text.strip()
        except Exception as exc:
            if isinstance(exc, GeminiError):
                raise
            raise GeminiError(f"Gemini request failed: {exc}") from exc
