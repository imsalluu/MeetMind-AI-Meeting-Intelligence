from fastapi import APIRouter
from app.api.routes import (
    analytics,
    auth,
    chat,
    export,
    health,
    insights,
    meetings,
    search,
    transcription,
)

api_router = APIRouter()

# Register routes
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(search.router)
api_router.include_router(meetings.router)
api_router.include_router(transcription.router)
api_router.include_router(insights.router)
api_router.include_router(chat.router)
api_router.include_router(analytics.router)
api_router.include_router(export.router)
