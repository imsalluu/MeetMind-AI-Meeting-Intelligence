import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.meeting import Meeting, MeetingStatus, ProcessingStage
from app.models.transcript import TranscriptSegment
from app.models.transcript_chunk import TranscriptChunk
from app.models.action_item import ActionItem
from app.models.decision import Decision
from app.models.meeting_topic import MeetingTopic
from app.models.meeting_insight import MeetingInsight
from app.models.chat import ChatSession, ChatMessage


@pytest.mark.asyncio
async def test_meeting_models_and_cascade(db_session: AsyncSession):
    # 1. Create User
    user = User(
        email="testuser@meetmind.ai",
        hashed_password="hashed_secret_pw",
        full_name="Alice Engineer",
    )
    db_session.add(user)
    await db_session.flush()

    assert user.id is not None
    assert user.email == "testuser@meetmind.ai"

    # 2. Create Meeting
    meeting = Meeting(
        user_id=user.id,
        title="Q3 Strategy & AI Roadmap",
        description="Quarterly planning meeting",
        duration_seconds=1800.0,
        status=MeetingStatus.COMPLETED.value,
        processing_stage=ProcessingStage.READY.value,
    )
    db_session.add(meeting)
    await db_session.flush()

    # 3. Create Transcript Segments
    seg1 = TranscriptSegment(
        meeting_id=meeting.id,
        speaker="Alice",
        text="Welcome everyone to our Q3 planning session.",
        start_time=0.0,
        end_time=4.5,
        segment_order=0,
    )
    seg2 = TranscriptSegment(
        meeting_id=meeting.id,
        speaker="Bob",
        text="We should launch the new pgvector RAG pipeline by Friday.",
        start_time=4.8,
        end_time=9.2,
        segment_order=1,
    )
    db_session.add_all([seg1, seg2])

    # 4. Create Transcript Chunk
    chunk = TranscriptChunk(
        meeting_id=meeting.id,
        chunk_index=0,
        text="Alice: Welcome everyone. Bob: We should launch the new pgvector RAG pipeline by Friday.",
        speaker="Alice, Bob",
        start_time=0.0,
        end_time=9.2,
        metadata_json={"speaker_count": 2},
    )
    db_session.add(chunk)

    # 5. Create Action Item
    action = ActionItem(
        meeting_id=meeting.id,
        task="Deploy pgvector RAG pipeline to staging",
        assignee="Bob",
        deadline="Friday 5 PM",
        source_timestamp=4.8,
    )
    db_session.add(action)

    # 6. Create Decision
    decision = Decision(
        meeting_id=meeting.id,
        decision="Adopt pgvector for transcript semantic search",
        source_timestamp=4.8,
    )
    db_session.add(decision)

    # 7. Create Topic
    topic = MeetingTopic(
        meeting_id=meeting.id,
        topic="RAG Architecture",
        summary="Discussion on vector indexing and hybrid search",
    )
    db_session.add(topic)

    # 8. Create Insight
    insight = MeetingInsight(
        meeting_id=meeting.id,
        executive_summary="Team agreed to deploy pgvector RAG pipeline by Friday.",
        short_summary="Q3 AI roadmap review.",
        detailed_summary="Full architectural discussion covering STT, RAG, and deployment schedules.",
        key_points=["pgvector chosen for RAG", "Target release Friday"],
        risks=["Tight deadline for staging verification"],
        questions=["Who owns load testing?"],
    )
    db_session.add(insight)

    # 9. Create Chat Session and Message
    chat_session = ChatSession(
        meeting_id=meeting.id,
        user_id=user.id,
        title="Q3 Strategy Q&A",
    )
    db_session.add(chat_session)
    await db_session.flush()

    msg = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content="The team agreed to deploy the pgvector RAG pipeline by Friday.",
        sources=[{"speaker": "Bob", "start_time": 4.8, "end_time": 9.2}],
    )
    db_session.add(msg)
    await db_session.flush()

    # Verify query
    query = await db_session.execute(select(Meeting).where(Meeting.id == meeting.id))
    retrieved_meeting = query.scalar_one()
    assert retrieved_meeting.title == "Q3 Strategy & AI Roadmap"
    assert len(retrieved_meeting.transcript_segments) == 2
    assert len(retrieved_meeting.action_items) == 1
    assert retrieved_meeting.action_items[0].assignee == "Bob"
    assert retrieved_meeting.insight.executive_summary is not None

    # Test cascade delete: deleting user deletes meeting and all associated child entities
    await db_session.delete(user)
    await db_session.flush()

    meetings_after = (await db_session.execute(select(Meeting).where(Meeting.id == meeting.id))).all()
    assert len(meetings_after) == 0
