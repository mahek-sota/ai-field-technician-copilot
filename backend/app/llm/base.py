"""
BaseLLMClient — abstract interface all LLM backends must implement.

Contract:
  - generate(prompt: str) -> str
      Sends prompt to the LLM and returns the raw text response.
      Must be async.
      Must raise an exception (e.g., RuntimeError, httpx.TimeoutException) on failure.
      Should respect settings.LLM_TIMEOUT_SECONDS.

  - is_available() -> bool
      Returns True if the client is configured and ready.
      Synchronous check (no network call).

Implementations:
  - GeminiClient  : uses google-generativeai SDK to call Gemini 1.5 Flash
  - MockLLMClient : returns deterministic canned responses for testing
"""
from abc import ABC, abstractmethod


class LLMError(Exception):
    """Raised when an LLM call fails or times out."""
    pass


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generate a response for the given prompt.

        Args:
            prompt: The full prompt string to send to the LLM.

        Returns:
            Raw text response from the LLM.

        Raises:
            RuntimeError: If the LLM call fails or times out.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this client is properly configured."""
        ...
