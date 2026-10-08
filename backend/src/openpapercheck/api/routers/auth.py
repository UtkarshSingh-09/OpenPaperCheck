"""
Authentication Endpoints for OpenPaperCheck REST API (v1).
Provides POST /v1/auth/login, POST /v1/auth/logout, GET /v1/auth/session
"""

from __future__ import annotations

import re
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from openpapercheck.api.deps import extract_session_token, get_optional_user
from openpapercheck.server.db import get_db
from openpapercheck.server.models import User
from openpapercheck.server.security import (
    create_user_session,
    get_or_create_user,
    invalidate_session,
)
from openpapercheck.server.settings import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str
    display_name: str | None = Field(None, min_length=3, max_length=30)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean


class UserProfileResponse(BaseModel):
    id: str
    display_name: str
    role: str
    level: int
    tutorial_done: bool
    joined_at: str


class SessionResponse(BaseModel):
    authenticated: bool
    user: UserProfileResponse | None = None


@router.post(
    "/login",
    response_model=UserProfileResponse,
    summary="Log in or register a reviewer session",
)
def login(
    req: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """
    Authenticate reviewer.
    Creates or looks up user, generates a secure session, and sets an HTTP-only cookie.
    """
    clean_email = str(req.email).lower().strip()
    fallback_name = req.display_name or clean_email.split("@")[0]

    user = get_or_create_user(
        db=db,
        email=clean_email,
        display_name=fallback_name,
        provider="email",
    )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    raw_token = create_user_session(db, user.id, ip=client_ip, user_agent=user_agent)

    # Set HTTP-only cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
    )

    return UserProfileResponse(
        id=user.id,
        display_name=user.display_name,
        role=user.role,
        level=user.level,
        tutorial_done=bool(user.tutorial_done_at),
        joined_at=user.joined_at.isoformat(),
    )


@router.post(
    "/logout",
    summary="Log out and invalidate session",
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Invalidate session in database and clear browser session cookie."""
    token = extract_session_token(request)
    if token:
        invalidate_session(db, token)

    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return {"status": "ok", "message": "Successfully logged out"}


@router.get(
    "/session",
    response_model=SessionResponse,
    summary="Check current session authentication state",
)
def check_session(
    user: User | None = Depends(get_optional_user),
) -> SessionResponse:
    """Return whether current visitor is authenticated and basic profile."""
    if not user:
        return SessionResponse(authenticated=False, user=None)

    return SessionResponse(
        authenticated=True,
        user=UserProfileResponse(
            id=user.id,
            display_name=user.display_name,
            role=user.role,
            level=user.level,
            tutorial_done=bool(user.tutorial_done_at),
            joined_at=user.joined_at.isoformat(),
        ),
    )
