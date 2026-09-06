import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint returns 200 OK and healthy status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "MeetMind — AI Meeting Intelligence"
    assert "uptime_seconds" in data
    assert data["components"]["database"] == "healthy"
    assert data["components"]["api"] == "healthy"
