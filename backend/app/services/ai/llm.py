import os
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.exceptions import AIProcessingException
from app.core.logging import logger


class OpenAIService:
    """Centralized OpenAI client factory and error handler."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self._client:
            # Fallback for dev/testing when key might not be populated
            key = self.api_key or os.environ.get("OPENAI_API_KEY") or "mock_key_for_testing"
            self._client = AsyncOpenAI(api_key=key)
        return self._client


ai_client_service = OpenAIService()
