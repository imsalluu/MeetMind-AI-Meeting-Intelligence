from fastapi import APIRouter
from app.api.routes import auth, health, meetings

api_router = APIRouter()

# Register routes
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(meetings.router)
