import time
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_db

router = APIRouter()
start_time = time.time()


@router.get("/health", summary="Service Health & Liveness Check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Return health status of API, database connectivity, and uptime."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(time.time() - start_time, 2),
        "components": {
            "database": db_status,
            "api": "healthy",
        },
    }
