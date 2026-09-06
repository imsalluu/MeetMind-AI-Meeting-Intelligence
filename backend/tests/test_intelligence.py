import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.services.ai.meeting_analyzer import meeting_analyzer_service


@pytest.mark.asyncio
async def test_meeting_intelligence_pipeline_and_apis(client: AsyncClient, db_session: AsyncSession):
    # 1. Register user & create meeting
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "intel.tester@meetmind.ai", "password": "Password123!", "full_name": "Intel Tester"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/meetings",
        json={"title": "Q4 AI Strategy Alignment", "description": "Discussing pgvector RAG deployment."},
        headers=headers,
    )
    meeting_id = create_res.json()["id"]
    meeting_uuid = uuid.UUID(meeting_id)
    meeting = await db_session.get(Meeting, meeting_uuid)

    # 2. Add sample transcript segments
    seg1 = TranscriptSegment(
        meeting_id=meeting_uuid,
        speaker="Speaker 1",
        text="Let's agree on the launch plan. We will deploy the pgvector index on Friday.",
        start_time=10.0,
        end_time=15.5,
    )
    seg2 = TranscriptSegment(
        meeting_id=meeting_uuid,
        speaker="Speaker 1",
        text="Alice will write the hybrid search module by Thursday 5 PM.",
        start_time=16.0,
        end_time=22.0,
    )
    db_session.add_all([seg1, seg2])
    await db_session.commit()

    # 3. Mock OpenAI Chat Completion response for Meeting Intelligence
    mock_intelligence_json = {
        "executive_summary": "The team agreed to deploy the pgvector index on Friday and assigned hybrid search development to Alice.",
        "short_summary": "Q4 AI Strategy aligned on pgvector and hybrid search deployment.",
        "detailed_summary": "### Deployment Plan\nThe team finalized the launch plan for pgvector vector indexing on Friday.\n\n### Task Assignment\nAlice will deliver the hybrid search module by Thursday.",
        "key_points": [
            "Deploy pgvector index on Friday",
            "Alice owns hybrid search module due Thursday",
        ],
        "action_items": [
            {
                "task": "Write hybrid search module",
                "assignee": "Alice",
                "deadline": "Thursday 5 PM",
                "source_timestamp": 16.0,
            }
        ],
        "decisions": [
            {
                "decision": "Deploy the pgvector index on Friday",
                "source_timestamp": 10.0,
            }
        ],
        "topics": [
            {
                "topic": "Vector Search Architecture",
                "summary": "Agreed on pgvector indexing and hybrid search implementation.",
            }
        ],
        "risks": ["Tight deadline for staging testing"],
        "questions": ["Who will monitor indexing throughput?"],
    }

    mock_chat_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(mock_intelligence_json)
                )
            )
        ]
    )

    with patch("app.services.ai.llm.ai_client_service.client.chat.completions.create", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_chat_response

        # Execute analyzer service
        result = await meeting_analyzer_service.analyze_meeting(db_session, meeting, [seg1, seg2])
        await db_session.commit()

        assert result.executive_summary.startswith("The team agreed")
        assert len(result.action_items) == 1
        assert result.action_items[0].assignee == "Alice"
        assert result.action_items[0].source_timestamp == 16.0
        assert len(result.decisions) == 1
        assert result.decisions[0].decision.startswith("Deploy the pgvector")

    # 4. Test Summary API
    summary_res = await client.get(f"/api/v1/meetings/{meeting_id}/summary", headers=headers)
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["executive_summary"].startswith("The team agreed")
    assert len(summary_data["key_points"]) == 2

    # 5. Test Actions API & Toggle Complete
    actions_res = await client.get(f"/api/v1/meetings/{meeting_id}/actions", headers=headers)
    assert actions_res.status_code == 200
    actions_list = actions_res.json()
    assert len(actions_list) == 1
    action_id = actions_list[0]["id"]
    assert actions_list[0]["is_completed"] is False
    assert actions_list[0]["assignee"] == "Alice"

    # Toggle complete
    patch_res = await client.patch(
        f"/api/v1/meetings/{meeting_id}/actions/{action_id}",
        json={"is_completed": True},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_completed"] is True

    # 6. Test Decisions API
    decisions_res = await client.get(f"/api/v1/meetings/{meeting_id}/decisions", headers=headers)
    assert decisions_res.status_code == 200
    dec_list = decisions_res.json()
    assert len(dec_list) == 1
    assert dec_list[0]["source_timestamp"] == 10.0

    # 7. Test Topics API
    topics_res = await client.get(f"/api/v1/meetings/{meeting_id}/topics", headers=headers)
    assert topics_res.status_code == 200
    assert len(topics_res.json()) == 1

    # 8. Test Combined Insights Overview API
    overview_res = await client.get(f"/api/v1/meetings/{meeting_id}/insights", headers=headers)
    assert overview_res.status_code == 200
    overview_data = overview_res.json()
    assert overview_data["summary"]["executive_summary"] is not None
    assert len(overview_data["action_items"]) == 1
    assert len(overview_data["decisions"]) == 1
    assert len(overview_data["topics"]) == 1
