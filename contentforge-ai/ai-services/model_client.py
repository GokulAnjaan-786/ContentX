import json
import logging
import re
from typing import Any, Dict, Optional, Type
import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


def clean_json_string(raw_text: str) -> str:
    """Extract and sanitize JSON from model output (handling code fences, leading text)."""
    text = raw_text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # Find outer bracket or brace if surrounded by commentary
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        return match.group(1).strip()
    return text


class ModelClient:
    """
    Swappable LLM client wrapper interfacing with local Ollama service
    or mock providers during testing.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self.mock_handler = None  # Optional callable for deterministic test fixtures

    def set_mock_handler(self, handler):
        """Set a custom mock handler for testing: handler(prompt, system) -> dict or str."""
        self.mock_handler = handler

    async def generate_raw(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """Call Ollama /api/generate endpoint."""
        if self.mock_handler is not None:
            res = self.mock_handler(prompt, system)
            if isinstance(res, dict):
                return json.dumps(res)
            return str(res)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
            },
        }

        timeout_config = httpx.Timeout(self.timeout, connect=2.0)
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def generate_structured(
        self,
        prompt: str,
        system: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        max_retries: int = 1,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON and optionally validate against a Pydantic schema.
        Retries once with a stricter correction prompt if the response is malformed.
        """
        current_prompt = prompt
        attempts = 0

        while attempts <= max_retries:
            attempts += 1
            try:
                raw_response = await self.generate_raw(
                    prompt=current_prompt,
                    system=system,
                    temperature=temperature,
                )
                cleaned = clean_json_string(raw_response)
                parsed = json.loads(cleaned)

                # Validate with Pydantic if schema provided
                if schema is not None:
                    validated = schema.model_validate(parsed)
                    return validated.model_dump()

                return parsed

            except (httpx.ConnectError, httpx.ConnectTimeout) as conn_err:
                logger.warning(f"Ollama LLM host '{self.base_url}' is unreachable ({conn_err}). Triggering fallback engine.")
                raise conn_err
            except Exception as e:
                logger.warning(
                    f"Model output parsing or schema validation error (attempt {attempts}/{max_retries + 1}): {e}"
                )
                if attempts <= max_retries:
                    # Retry with corrective prompt
                    current_prompt = (
                        f"{prompt}\n\n"
                        f"CRITICAL FIX REQUIRED: Your previous response failed with error: {str(e)}.\n"
                        f"You must return ONLY a strictly valid JSON object matching the requested schema. "
                        f"Do not include any prose, explanations, or code block markers."
                    )
                else:
                    raise ValueError(f"Failed to generate valid structured output after {attempts} attempts: {e}")


# Global default client instance
model_client = ModelClient()
