from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.services.auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, summary="Register new user")
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Register a new user and receive a JWT access token."""
    return await AuthService.register(db, data)


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK, summary="User login")
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate with email and password to receive a JWT access token."""
    return await AuthService.login(db, data)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK, summary="Get current profile")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve profile data for the authenticated user."""
    return UserResponse.model_validate(current_user)
