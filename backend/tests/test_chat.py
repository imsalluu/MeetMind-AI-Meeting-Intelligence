from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meeting import Meeting
from app.models.transcript_chunk import TranscriptChunk


@pytest.mark.asyncio
async def test_ask_this_meeting_chat_and_sources(client: AsyncClient, db_session: AsyncSession):
    # 1. Register user & create meeting
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "chat.tester@meetmind.ai", "password": "Password123!", "full_name": "Chat Tester"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/meetings",
        json={"title": "Q3 Launch Planning", "description": "Reviewing product launch deadlines."},
        headers=headers,
    )
    meeting_id = create_res.json()["id"]
    meeting_uuid = uuid.UUID(meeting_id)

    # 2. Add sample indexed vector chunk
    chunk = TranscriptChunk(
        meeting_id=meeting_uuid,
        chunk_index=0,
        text="Speaker 2: We should launch the new version next Friday at 10 AM.",
        speaker="Speaker 2",
        start_time=124.5,
        end_time=129.2,
        embedding=[0.1] * 1536,
        metadata_json={"speaker": "Speaker 2"},
    )
    db_session.add(chunk)
    await db_session.commit()

    # 3. Mock OpenAI embeddings and chat completion
    mock_emb_res = SimpleNamespace(data=[SimpleNamespace(index=0, embedding=[0.1] * 1536)])
    mock_llm_res = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="The team agreed to launch the new version next Friday at 10 AM."
                )
            )
        ]
    )

    with patch("app.services.ai.llm.ai_client_service.client.embeddings.create", new_callable=AsyncMock) as mock_emb, \
         patch("app.services.ai.llm.ai_client_service.client.chat.completions.create", new_callable=AsyncMock) as mock_llm:
        
        mock_emb.return_value = mock_emb_res
        mock_llm.return_value = mock_llm_res

        # 4. Ask meeting question
        ask_payload = {"question": "When is the new version launching?"}
        ask_res = await client.post(f"/api/v1/meetings/{meeting_id}/ask", json=ask_payload, headers=headers)
        assert ask_res.status_code == 200
        ask_data = ask_res.json()
        assert ask_data["answer"] == "The team agreed to launch the new version next Friday at 10 AM."
        assert len(ask_data["sources"]) == 1
        source = ask_data["sources"][0]
        assert source["speaker"] == "Speaker 2"
        assert source["start_time"] == 124.5
        assert source["end_time"] == 129.2
        assert source["formatted_timestamp"] == "[02:04 - 02:09]"
        session_id = ask_data["session_id"]

        # 5. Ask follow-up in same session
        mock_llm.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="The launch time was agreed for 10 AM.")
                )
            ]
        )
        followup_res = await client.post(
            f"/api/v1/meetings/{meeting_id}/ask",
            json={"question": "What time exactly?", "session_id": session_id},
            headers=headers,
        )
        assert followup_res.status_code == 200
        assert followup_res.json()["session_id"] == session_id

    # 6. Fetch chat session history
    sessions_res = await client.get(f"/api/v1/meetings/{meeting_id}/chat/sessions", headers=headers)
    assert sessions_res.status_code == 200
    sessions = sessions_res.json()
    assert len(sessions) == 1

    detail_res = await client.get(
        f"/api/v1/meetings/{meeting_id}/chat/sessions/{session_id}", headers=headers
    )
    assert detail_res.status_code == 200
    session_detail = detail_res.json()
    # 2 questions = 4 messages (2 user, 2 assistant)
    assert len(session_detail["messages"]) == 4
    assert session_detail["messages"][0]["role"] == "user"
    assert session_detail["messages"][1]["role"] == "assistant"
    assert len(session_detail["messages"][1]["sources"]) == 1
