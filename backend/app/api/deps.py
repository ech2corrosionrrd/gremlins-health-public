"""Shared FastAPI dependencies."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# auto_error=True -> a missing/!Bearer header is a 401 before we run.
# There is deliberately no "demo user" fallback: an unauthenticated request
# must never resolve to a real account.
bearer_scheme = HTTPBearer(auto_error=True)

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _UNAUTHENTICATED

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()

    # A token for a deleted user is an authentication failure, not a 404 -
    # returning 404 would leak which user ids exist.
    if user is None:
        raise _UNAUTHENTICATED
    if not bool(user.is_active):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )
    return user
