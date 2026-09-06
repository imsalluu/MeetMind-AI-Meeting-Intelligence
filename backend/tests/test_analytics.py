import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.action_item import ActionItem
from app.models.decision import Decision
from app.models.meeting import Meeting, MeetingStatus
from app.models.meeting_topic import MeetingTopic


@pytest.mark.asyncio
async def test_analytics_overview_endpoint(client: AsyncClient, db_session: AsyncSession):
    # 1. Register user
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "analytics.user@meetmind.ai", "password": "Password123!", "full_name": "Analytics User"},
    )
    token = auth_res.json()["access_token"]
    user_id = uuid.UUID(auth_res.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add two meetings with duration, actions, decisions, and topics
    m1 = Meeting(
        user_id=user_id,
        title="Sprint Planning A",
        duration_seconds=3600.0,
        status=MeetingStatus.COMPLETED.value,
    )
    m2 = Meeting(
        user_id=user_id,
        title="Sprint Planning B",
        duration_seconds=1800.0,
        status=MeetingStatus.COMPLETED.value,
    )
    db_session.add_all([m1, m2])
    await db_session.flush()

    # Add Action Items
    a1 = ActionItem(meeting_id=m1.id, task="Task 1", is_completed=True)
    a2 = ActionItem(meeting_id=m1.id, task="Task 2", is_completed=False)
    a3 = ActionItem(meeting_id=m2.id, task="Task 3", is_completed=True)
    db_session.add_all([a1, a2, a3])

    # Add Decisions
    d1 = Decision(meeting_id=m1.id, decision="Decision 1")
    d2 = Decision(meeting_id=m2.id, decision="Decision 2")
    db_session.add_all([d1, d2])

    # Add Topics
    t1 = MeetingTopic(meeting_id=m1.id, topic="Architecture")
    t2 = MeetingTopic(meeting_id=m2.id, topic="Architecture")
    t3 = MeetingTopic(meeting_id=m2.id, topic="Database")
    db_session.add_all([t1, t2, t3])

    await db_session.commit()

    # 3. Call Analytics Endpoint
    res = await client.get("/api/v1/analytics/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_meetings"] == 2
    assert data["total_duration_hours"] == 1.5
    assert data["avg_meeting_duration_minutes"] == 45.0
    assert data["total_action_items"] == 3
    assert data["completed_action_items"] == 2
    assert data["pending_action_items"] == 1
    assert data["action_item_completion_rate"] == 66.7
    assert data["total_decisions"] == 2
    assert len(data["recent_meetings"]) == 2
    assert any(t["topic"] == "Architecture" and t["count"] == 2 for t in data["top_topics"])
