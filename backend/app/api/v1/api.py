from fastapi import APIRouter
from app.api.routes import auth, health

api_router = APIRouter()

# Register routes
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
