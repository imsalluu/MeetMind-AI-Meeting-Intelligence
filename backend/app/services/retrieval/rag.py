import math
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.models.transcript_chunk import TranscriptChunk
from app.schemas.transcript import format_seconds_to_timestamp
from app.services.ai.embeddings import embedding_service
from app.services.retrieval.chunking import transcript_chunker


class RetrievedChunk(BaseModel):
    id: uuid.UUID
    chunk_index: int
    text: str
    speaker: Optional[str] = None
    start_time: float
    end_time: float
    score: float
    metadata_json: Optional[Dict[str, Any]] = None

    @property
    def formatted_timestamp(self) -> str:
        return f"[{format_seconds_to_timestamp(self.start_time)} - {format_seconds_to_timestamp(self.end_time)}]"


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class RAGRetrievalService:
    """Hybrid Retrieval Service (pgvector semantic similarity + full-text search + Reciprocal Rank Fusion)."""

    @classmethod
    async def index_meeting_transcript(
        cls,
        db: AsyncSession,
        meeting: Meeting,
        segments: List[TranscriptSegment],
    ) -> List[TranscriptChunk]:
        """Chunk meeting transcript, generate 1536-dim vector embeddings, and save to database."""
        if not segments:
            logger.warning(f"No segments provided for meeting={meeting.id}. Skipping chunk indexing.")
            return []

        # 1. Chunk transcript
        chunk_data_list = transcript_chunker.chunk_segments(segments)
        if not chunk_data_list:
            return []

        # 2. Batch generate embeddings
        texts_to_embed = [c.text for c in chunk_data_list]
        embeddings = await embedding_service.get_embeddings_batch(texts_to_embed)

        # 3. Clean existing chunks for idempotency
        await db.execute(delete(TranscriptChunk).where(TranscriptChunk.meeting_id == meeting.id))

        # 4. Save chunks with vector embeddings
        saved_chunks: List[TranscriptChunk] = []
        for i, chunk_data in enumerate(chunk_data_list):
            emb = embeddings[i] if i < len(embeddings) else None
            db_chunk = TranscriptChunk(
                meeting_id=meeting.id,
                chunk_index=chunk_data.chunk_index,
                text=chunk_data.text,
                speaker=chunk_data.speaker,
                start_time=chunk_data.start_time,
                end_time=chunk_data.end_time,
                embedding=emb,
                metadata_json=chunk_data.metadata,
            )
            db.add(db_chunk)
            saved_chunks.append(db_chunk)

        await db.flush()
        logger.info(f"Indexed {len(saved_chunks)} vector chunks for meeting={meeting.id}")
        return saved_chunks

    @classmethod
    async def retrieve_relevant_chunks(
        cls,
        db: AsyncSession,
        meeting_id: uuid.UUID,
        query: str,
        top_k: int = 4,
    ) -> List[RetrievedChunk]:
        """Hybrid retrieval combining vector similarity and keyword search via Reciprocal Rank Fusion."""
        query_text = query.strip()
        if not query_text:
            return []

        # Fetch all chunks for this meeting
        stmt = select(TranscriptChunk).where(TranscriptChunk.meeting_id == meeting_id)
        result = await db.execute(stmt)
        all_chunks = list(result.scalars().all())

        if not all_chunks:
            logger.info(f"No chunks found in meeting={meeting_id}")
            return []

        # 1. Semantic Vector Retrieval
        query_embedding = await embedding_service.get_embedding(query_text)
        
        vector_ranked: List[tuple[TranscriptChunk, float]] = []
        for chunk in all_chunks:
            if chunk.embedding is not None:
                # Handle both list and pgvector Vector types
                emb_list = list(chunk.embedding) if hasattr(chunk.embedding, "__iter__") else []
                sim = cosine_similarity(query_embedding, emb_list)
            else:
                sim = 0.0
            vector_ranked.append((chunk, sim))

        # Sort descending by similarity score
        vector_ranked.sort(key=lambda x: x[1], reverse=True)

        # 2. Keyword Search
        query_words = set(query_text.lower().split())
        keyword_ranked: List[tuple[TranscriptChunk, float]] = []
        for chunk in all_chunks:
            chunk_lower = chunk.text.lower()
            matches = sum(1 for w in query_words if w in chunk_lower)
            score = matches / max(1, len(query_words))
            keyword_ranked.append((chunk, score))

        keyword_ranked.sort(key=lambda x: x[1], reverse=True)

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF Score = 1 / (60 + rank_vector) + 1 / (60 + rank_keyword)
        rrf_scores: Dict[uuid.UUID, float] = {}
        chunk_map: Dict[uuid.UUID, TranscriptChunk] = {c.id: c for c in all_chunks}

        for rank, (chunk, _) in enumerate(vector_ranked):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (60.0 + rank + 1))

        for rank, (chunk, _) in enumerate(keyword_ranked):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (60.0 + rank + 1))

        # Sort by RRF score descending
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        top_chunk_ids = sorted_chunk_ids[:top_k]

        retrieved: List[RetrievedChunk] = []
        for cid in top_chunk_ids:
            chunk = chunk_map[cid]
            retrieved.append(
                RetrievedChunk(
                    id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    speaker=chunk.speaker,
                    start_time=chunk.start_time,
                    end_time=chunk.end_time,
                    score=round(rrf_scores[cid], 5),
                    metadata_json=chunk.metadata_json or {},
                )
            )

        logger.info(
            f"Retrieved {len(retrieved)} relevant chunks for query='{query_text[:30]}' in meeting={meeting_id}"
        )
        return retrieved


rag_service = RAGRetrievalService()
