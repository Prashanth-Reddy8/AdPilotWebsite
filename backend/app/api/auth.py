"""Email/password authentication routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import ConfigDep, SessionDep
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.api import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: SessionDep, settings: ConfigDep) -> TokenResponse:
    """Authenticate an active user without revealing which credential failed."""

    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user.id, settings),
        expires_in=settings.access_token_expire_minutes * 60,
    )
