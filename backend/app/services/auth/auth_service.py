import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AppException, UnauthorizedException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse


class AuthService:
    """Service handling user registration, authentication, and token issuance."""

    @staticmethod
    async def register(db: AsyncSession, data: UserRegister) -> Token:
        # Check if email already registered
        query = await db.execute(select(User).where(User.email == data.email.lower()))
        existing_user = query.scalar_one_or_none()
        if existing_user:
            raise AppException(
                code="EMAIL_ALREADY_EXISTS",
                message="An account with this email already exists.",
                status_code=400,
            )

        hashed = hash_password(data.password)
        new_user = User(
            email=data.email.lower(),
            hashed_password=hashed,
            full_name=data.full_name,
            is_active=True,
        )
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user)

        token_str = create_access_token(subject=str(new_user.id))
        return Token(
            access_token=token_str,
            token_type="bearer",
            user=UserResponse.model_validate(new_user),
        )

    @staticmethod
    async def login(db: AsyncSession, data: UserLogin) -> Token:
        query = await db.execute(select(User).where(User.email == data.email.lower()))
        user = query.scalar_one_or_none()
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")

        if not user.is_active:
            raise AppException(
                code="ACCOUNT_INACTIVE",
                message="Your account is inactive. Please contact support.",
                status_code=403,
            )

        token_str = create_access_token(subject=str(user.id))
        return Token(
            access_token=token_str,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        query = await db.execute(select(User).where(User.id == user_id))
        return query.scalar_one_or_none()
