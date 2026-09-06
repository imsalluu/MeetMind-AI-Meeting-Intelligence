import uuid
from typing import AsyncGenerator
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth.auth_service import AuthService

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that authenticates the user via JWT Bearer header."""
    if not auth or not auth.credentials:
        raise UnauthorizedException("Authentication token is missing.")

    payload = decode_access_token(auth.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload missing subject identifier.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user ID format in token.")

    user = await AuthService.get_by_id(db, user_uuid)
    if not user:
        raise UnauthorizedException("User associated with token no longer exists.")

    if not user.is_active:
        raise UnauthorizedException("User account is disabled.")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify user is active."""
    return current_user
