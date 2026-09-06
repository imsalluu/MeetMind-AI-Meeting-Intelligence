import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_meeting_lifecycle_and_ownership(client: AsyncClient):
    # 1. Register User A
    user_a_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@meetmind.ai", "password": "Password123!", "full_name": "Alice"},
    )
    token_a = user_a_res.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    user_b_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@meetmind.ai", "password": "Password123!", "full_name": "Bob"},
    )
    token_b = user_b_res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates a meeting
    meeting_payload = {
        "title": "Product Architecture Sprint",
        "description": "Weekly deep dive on FastAPI and pgvector RAG pipeline.",
    }
    create_res = await client.post("/api/v1/meetings", json=meeting_payload, headers=headers_a)
    assert create_res.status_code == 201
    meeting_a = create_res.json()
    assert meeting_a["title"] == "Product Architecture Sprint"
    assert meeting_a["status"] == "PENDING"
    meeting_id = meeting_a["id"]

    # 4. User A uploads audio to the meeting
    dummy_wav_content = b"RIFF....WAVEfmt ....data...."
    files = {"file": ("test_recording.wav", io.BytesIO(dummy_wav_content), "audio/wav")}
    upload_res = await client.post(
        f"/api/v1/meetings/{meeting_id}/upload", files=files, headers=headers_a
    )
    assert upload_res.status_code == 200
    uploaded_data = upload_res.json()
    assert uploaded_data["audio_filename"] == "test_recording.wav"
    assert uploaded_data["file_size_bytes"] == len(dummy_wav_content)

    # 5. Invalid file format upload should fail
    bad_files = {"file": ("malware.exe", io.BytesIO(b"executable binary"), "application/octet-stream")}
    bad_upload_res = await client.post(
        f"/api/v1/meetings/{meeting_id}/upload", files=bad_files, headers=headers_a
    )
    assert bad_upload_res.status_code == 422
    assert bad_upload_res.json()["error"]["code"] == "VALIDATION_ERROR"

    # 6. User A lists meetings
    list_res = await client.get("/api/v1/meetings", headers=headers_a)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == meeting_id

    # 7. User A searches meetings with query
    search_res = await client.get("/api/v1/meetings?q=Architecture", headers=headers_a)
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1

    search_nomatch = await client.get("/api/v1/meetings?q=NonExistent", headers=headers_a)
    assert search_nomatch.json()["total"] == 0

    # 8. User B attempts to access User A's meeting -> 403 Forbidden
    unauthorized_res = await client.get(f"/api/v1/meetings/{meeting_id}", headers=headers_b)
    assert unauthorized_res.status_code == 403
    assert unauthorized_res.json()["error"]["code"] == "FORBIDDEN"

    # User B attempts to delete User A's meeting -> 403 Forbidden
    unauthorized_delete = await client.delete(f"/api/v1/meetings/{meeting_id}", headers=headers_b)
    assert unauthorized_delete.status_code == 403

    # 9. User A retrieves status
    status_res = await client.get(f"/api/v1/meetings/{meeting_id}/status", headers=headers_a)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "PENDING"

    # 10. User A streams audio
    audio_res = await client.get(f"/api/v1/meetings/{meeting_id}/audio", headers=headers_a)
    assert audio_res.status_code == 200
    assert audio_res.content == dummy_wav_content

    # 11. User A deletes meeting
    del_res = await client.delete(f"/api/v1/meetings/{meeting_id}", headers=headers_a)
    assert del_res.status_code == 200

    # Verify meeting is gone
    get_res = await client.get(f"/api/v1/meetings/{meeting_id}", headers=headers_a)
    assert get_res.status_code == 404
