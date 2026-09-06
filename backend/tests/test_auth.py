import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_full_flow(client: AsyncClient):
    # 1. Register new user
    register_payload = {
        "email": "sarah.connor@meetmind.ai",
        "password": "SecurePassword123!",
        "full_name": "Sarah Connor",
    }
    reg_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_response.status_code == 201
    data = reg_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "sarah.connor@meetmind.ai"
    assert data["user"]["full_name"] == "Sarah Connor"
    token = data["access_token"]

    # 2. Duplicate registration should fail
    dup_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert dup_response.status_code == 400
    dup_data = dup_response.json()
    assert dup_data["error"]["code"] == "EMAIL_ALREADY_EXISTS"

    # 3. Login with correct credentials
    login_payload = {
        "email": "sarah.connor@meetmind.ai",
        "password": "SecurePassword123!",
    }
    login_response = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == "sarah.connor@meetmind.ai"

    # 4. Login with wrong password should fail with 401
    bad_login_payload = {
        "email": "sarah.connor@meetmind.ai",
        "password": "WrongPassword999!",
    }
    bad_login_response = await client.post("/api/v1/auth/login", json=bad_login_payload)
    assert bad_login_response.status_code == 401

    # 5. Access /me with valid Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "sarah.connor@meetmind.ai"
    assert me_data["full_name"] == "Sarah Connor"

    # 6. Access /me with missing or invalid token should fail with 401
    unauth_response = await client.get("/api/v1/auth/me")
    assert unauth_response.status_code == 401

    invalid_token_response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert invalid_token_response.status_code == 401
