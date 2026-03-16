"""
GeminiClient — wraps google-generativeai to call Gemini 1.5 Flash.

Configuration via settings:
  - GEMINI_API_KEY   : required; raises RuntimeError if missing
  - GEMINI_MODEL     : default "gemini-1.5-flash"
  - LLM_TIMEOUT_SECONDS : applied as a generation timeout hint

The SDK call is blocking, so we run it in a thread pool executor to keep
the FastAPI event loop free.
"""
import asyncio
from typing import Optional

import google.generativeai as genai

from app.config import settings
from app.llm.base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file or set USE_MOCK_LLM=true."
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def is_available(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    async def generate(self, prompt: str) -> str:
        """
        Call Gemini in a thread-pool executor (SDK is synchronous).
        Raises RuntimeError on API error or timeout.
        """
        loop = asyncio.get_event_loop()
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(None, self._call_sync, prompt),
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
            return response
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Gemini API call timed out after {settings.LLM_TIMEOUT_SECONDS}s"
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini API error: {exc}") from exc

    def _call_sync(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        return response.text
