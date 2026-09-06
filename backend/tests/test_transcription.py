import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meeting import Meeting, MeetingStatus
from app.models.user import User
from app.services.ai.transcription import transcription_service
from app.services.storage.local_storage import storage_service


@pytest.mark.asyncio
async def test_transcription_pipeline_and_api(client: AsyncClient, db_session: AsyncSession):
    # 1. Register user and create meeting
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "transcribe.tester@meetmind.ai", "password": "Password123!", "full_name": "Transcribe User"},
    )
    token = auth_res.json()["access_token"]
    user_id = auth_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/meetings",
        json={"title": "Weekly Engineering Sync", "description": "Reviewing system milestones."},
        headers=headers,
    )
    meeting_id = create_res.json()["id"]

    # 2. Upload dummy audio
    audio_content = b"TEST_AUDIO_STREAM"
    rel_path = f"meetings/{user_id}/{meeting_id}/audio.wav"
    await storage_service.upload(audio_content, rel_path)

    # Update meeting audio_path
    meeting_uuid = uuid.UUID(meeting_id)
    meeting = await db_session.get(Meeting, meeting_uuid)
    meeting.audio_path = rel_path
    meeting.audio_filename = "audio.wav"
    await db_session.commit()

    # 3. Mock OpenAI Whisper API response
    mock_segments = [
        {"id": 0, "start": 0.0, "end": 5.4, "text": "Good morning team, let's discuss our architecture."},
        {"id": 1, "start": 5.8, "end": 12.1, "text": "We decided to implement pgvector for hybrid retrieval."},
        {"id": 2, "start": 12.5, "end": 18.0, "text": "Alice will deploy the backend API by Wednesday."},
    ]
    mock_whisper_response = SimpleNamespace(
        text="Good morning team... Alice will deploy the backend API by Wednesday.",
        duration=18.0,
        segments=mock_segments,
    )

    with patch("app.services.ai.llm.ai_client_service.client.audio.transcriptions.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_whisper_response

        # Execute transcription service
        segments, duration = await transcription_service.transcribe_meeting(db_session, meeting)
        await db_session.commit()

        assert len(segments) == 3
        assert duration == 18.0
        assert segments[0].text == "Good morning team, let's discuss our architecture."
        assert segments[0].start_time == 0.0
        assert segments[0].end_time == 5.4
        assert segments[1].start_time == 5.8
        assert segments[2].speaker == "Speaker 1"

    # 4. Fetch transcript via API
    api_res = await client.get(f"/api/v1/meetings/{meeting_id}/transcript", headers=headers)
    assert api_res.status_code == 200
    data = api_res.json()
    assert data["meeting_id"] == meeting_id
    assert data["total_segments"] == 3
    assert data["duration_seconds"] == 18.0
    assert data["segments"][0]["formatted_start"] == "00:00"
    assert data["segments"][1]["formatted_start"] == "00:05"
    assert data["segments"][2]["formatted_start"] == "00:12"
