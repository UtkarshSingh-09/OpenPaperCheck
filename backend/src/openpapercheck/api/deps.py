"""
FastAPI dependencies for authentication and authorization.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from openpapercheck.server.db import get_db
from openpapercheck.server.models import User
from openpapercheck.server.security import get_user_from_session
from openpapercheck.server.settings import settings


def extract_session_token(request: Request) -> str | None:
    """Extract session token from cookie or Authorization Bearer header."""
    # 1. Check HTTP-only cookie
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        return token

    # 2. Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "").strip()

    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Dependency that enforces a valid active user session."""
    token = extract_session_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )

    user = get_user_from_session(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please log in again.",
        )

    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """Dependency that returns the user if logged in, or None without raising 401."""
    token = extract_session_token(request)
    if not token:
        return None
    return get_user_from_session(db, token)
