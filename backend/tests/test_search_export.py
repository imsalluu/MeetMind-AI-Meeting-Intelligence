import json
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.action_item import ActionItem
from app.models.decision import Decision
from app.models.meeting import Meeting, MeetingStatus
from app.models.meeting_insight import MeetingInsight
from app.models.meeting_topic import MeetingTopic
from app.models.transcript import TranscriptSegment


@pytest.mark.asyncio
async def test_search_and_export_endpoints(client: AsyncClient, db_session: AsyncSession):
    # 1. Register user & setup meeting with transcript, action, decision, topic, and insight
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "search.export@meetmind.ai", "password": "Password123!", "full_name": "Search Tester"},
    )
    token = auth_res.json()["access_token"]
    user_id = uuid.UUID(auth_res.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    meeting = Meeting(
        user_id=user_id,
        title="Enterprise Architecture Sync",
        description="Reviewing FastAPI backend and pgvector RAG deployment.",
        duration_seconds=1200.0,
        status=MeetingStatus.COMPLETED.value,
    )
    db_session.add(meeting)
    await db_session.flush()

    seg = TranscriptSegment(
        meeting_id=meeting.id,
        speaker="Speaker 1",
        text="The pricing strategy was finalized at 49 dollars per seat.",
        start_time=15.0,
        end_time=20.0,
    )
    db_session.add(seg)

    action = ActionItem(
        meeting_id=meeting.id,
        task="Prepare pricing tier documentation",
        assignee="Sarah",
        deadline="Next Monday",
        source_timestamp=15.0,
    )
    db_session.add(action)

    decision = Decision(
        meeting_id=meeting.id,
        decision="Adopted 49 dollar monthly pricing tier",
        source_timestamp=15.0,
    )
    db_session.add(decision)

    topic = MeetingTopic(
        meeting_id=meeting.id,
        topic="Pricing Strategy",
        summary="Finalized pricing at $49/seat.",
    )
    db_session.add(topic)

    insight = MeetingInsight(
        meeting_id=meeting.id,
        executive_summary="Team agreed on pricing and architecture milestones.",
        key_points=["$49 monthly seat pricing finalized"],
        detailed_summary="Full pricing review completed.",
    )
    db_session.add(insight)
    await db_session.commit()

    # 2. Test Global Search
    search_res = await client.get("/api/v1/meetings/search?q=pricing", headers=headers)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_matches"] >= 3
    match_types = [item["match_type"] for item in search_data["results"]]
    assert "transcript" in match_types
    assert "action_item" in match_types
    assert "decision" in match_types

    # 3. Test Markdown Export
    md_res = await client.get(f"/api/v1/meetings/{meeting.id}/export/markdown", headers=headers)
    assert md_res.status_code == 200
    assert "text/markdown" in md_res.headers["content-type"]
    assert "# Enterprise Architecture Sync" in md_res.text
    assert "Prepare pricing tier documentation" in md_res.text
    assert "Adopted 49 dollar monthly pricing tier" in md_res.text

    # 4. Test JSON Export
    json_res = await client.get(f"/api/v1/meetings/{meeting.id}/export/json", headers=headers)
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]
    payload = json_res.json()
    assert payload["meeting"]["title"] == "Enterprise Architecture Sync"
    assert len(payload["action_items"]) == 1
    assert len(payload["decisions"]) == 1
    assert len(payload["transcript_segments"]) == 1

    # 5. Test TXT Export
    txt_res = await client.get(f"/api/v1/meetings/{meeting.id}/export/txt", headers=headers)
    assert txt_res.status_code == 200
    assert "text/plain" in txt_res.headers["content-type"]
    assert "MEETMIND TRANSCRIPT" in txt_res.text
    assert "[00:15 - 00:20] Speaker 1: The pricing strategy was finalized" in txt_res.text
