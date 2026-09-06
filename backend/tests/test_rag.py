from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.models.user import User
from app.services.retrieval.chunking import transcript_chunker
from app.services.retrieval.rag import cosine_similarity, rag_service


def test_transcript_chunker():
    segments = [
        TranscriptSegment(
            meeting_id=uuid.uuid4(),
            speaker="Alice",
            text="First segment discussing vector search.",
            start_time=0.0,
            end_time=5.0,
        ),
        TranscriptSegment(
            meeting_id=uuid.uuid4(),
            speaker="Bob",
            text="Second segment discussing PostgreSQL and pgvector deployment.",
            start_time=5.2,
            end_time=12.0,
        ),
    ]
    chunks = transcript_chunker.chunk_segments(segments)
    assert len(chunks) >= 1
    assert chunks[0].start_time == 0.0
    assert chunks[0].end_time == 12.0
    assert "Alice" in chunks[0].speaker
    assert "Bob" in chunks[0].speaker


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)

    v3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v3) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_rag_indexing_and_hybrid_retrieval(db_session: AsyncSession):
    # 1. Create User and Meeting
    user = User(email="rag.tester@meetmind.ai", hashed_password="pw", full_name="RAG Tester")
    db_session.add(user)
    await db_session.flush()

    meeting = Meeting(
        user_id=user.id,
        title="RAG Architecture Deep Dive",
    )
    db_session.add(meeting)
    await db_session.flush()

    # 2. Add segments
    seg1 = TranscriptSegment(
        meeting_id=meeting.id,
        speaker="Speaker 1",
        text="The pricing model was agreed at 29 dollars per month per seat.",
        start_time=20.0,
        end_time=28.5,
    )
    seg2 = TranscriptSegment(
        meeting_id=meeting.id,
        speaker="Speaker 2",
        text="We decided to use pgvector with 1536 dimensional embeddings for fast search.",
        start_time=30.0,
        end_time=42.0,
    )
    db_session.add_all([seg1, seg2])
    await db_session.commit()

    # 3. Mock OpenAI Embeddings
    # Return dummy 1536-dim vector where index 0 is 1.0
    dummy_vector = [0.0] * 1536
    dummy_vector[0] = 1.0

    mock_embeddings_response = SimpleNamespace(
        data=[
            SimpleNamespace(index=0, embedding=dummy_vector),
        ]
    )

    with patch("app.services.ai.llm.ai_client_service.client.embeddings.create", new_callable=AsyncMock) as mock_emb:
        mock_emb.return_value = mock_embeddings_response

        # Execute indexing
        indexed_chunks = await rag_service.index_meeting_transcript(
            db_session, meeting, [seg1, seg2]
        )
        await db_session.commit()

        assert len(indexed_chunks) >= 1
        assert indexed_chunks[0].chunk_index == 0

        # Execute hybrid retrieval
        retrieved = await rag_service.retrieve_relevant_chunks(
            db_session, meeting.id, query="What is the pricing model?", top_k=2
        )
        assert len(retrieved) >= 1
        assert retrieved[0].start_time == 20.0
        assert retrieved[0].end_time == 42.0
        assert "[00:20 - 00:42]" in retrieved[0].formatted_timestamp
