from typing import List, Union
from app.core.config import settings
from app.core.exceptions import AIProcessingException
from app.core.logging import logger
from app.services.ai.llm import ai_client_service


class EmbeddingService:
    """Centralized service for generating text embeddings via OpenAI."""

    def __init__(self, model: str = settings.OPENAI_EMBEDDING_MODEL):
        self.model = model

    async def get_embedding(self, text: str) -> List[float]:
        """Generate a single 1536-dimensional embedding vector."""
        embeddings = await self.get_embeddings_batch([text])
        return embeddings[0]

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of text chunks."""
        if not texts:
            return []

        cleaned_texts = [t.replace("\n", " ").strip() for t in texts]
        
        try:
            response = await ai_client_service.client.embeddings.create(
                input=cleaned_texts,
                model=self.model,
            )
            # Sort by index to ensure order is preserved
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]

        except Exception as e:
            logger.exception(f"OpenAI embedding generation failed: {e}")
            raise AIProcessingException(f"Failed to generate embeddings: {str(e)}")


embedding_service = EmbeddingService()
