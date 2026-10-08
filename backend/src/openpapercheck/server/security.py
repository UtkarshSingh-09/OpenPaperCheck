"""
Authentication, session hashing, and security utilities for OpenPaperCheck Server.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DBSession

from openpapercheck.server.models import AuthIdentity, ReviewerStats, Session, User
from openpapercheck.server.settings import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_session_token() -> str:
    """Generate a cryptographically secure random session token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Compute SHA-256 hex digest of a token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user_session(
    db: DBSession,
    user_id: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> str:
    """
    Create a new persistent user session in the database.
    Returns the raw unhashed session token for the HTTP cookie.
    """
    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    expires_at = utcnow() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)

    ip_hash = hash_token(ip) if ip else None
    ua_hash = hash_token(user_agent) if user_agent else None

    session_record = Session(
        id_hash=token_hash,
        user_id=user_id,
        created_at=utcnow(),
        expires_at=expires_at,
        ip_hash=ip_hash,
        ua_hash=ua_hash,
    )
    db.add(session_record)

    # Update user last_active_at
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_active_at = utcnow()

    db.commit()
    return raw_token


def get_user_from_session(db: DBSession, raw_token: str | None) -> User | None:
    """Validate a raw session token and return the active User, or None."""
    if not raw_token:
        return None

    token_hash = hash_token(raw_token)
    session_record = (
        db.query(Session)
        .filter(Session.id_hash == token_hash, Session.expires_at > utcnow())
        .first()
    )
    if not session_record:
        return None

    user = db.query(User).filter(User.id == session_record.user_id, User.status == "active").first()
    if user:
        # Refresh last active timestamp
        user.last_active_at = utcnow()
        db.commit()
    return user


def invalidate_session(db: DBSession, raw_token: str | None) -> bool:
    """Delete a session by raw token upon logout."""
    if not raw_token:
        return False
    token_hash = hash_token(raw_token)
    session_record = db.query(Session).filter(Session.id_hash == token_hash).first()
    if session_record:
        db.delete(session_record)
        db.commit()
        return True
    return False


def get_or_create_user(
    db: DBSession,
    email: str,
    display_name: str,
    provider: str = "dev_mock",
    provider_subject: str | None = None,
    role: str = "reviewer",
) -> User:
    """
    Get an existing user by email or create a new user with an AuthIdentity and ReviewerStats.
    Email is stored strictly in AuthIdentity; User table contains only pseudonym display_name.
    """
    clean_email = email.strip().lower()
    identity = db.query(AuthIdentity).filter(AuthIdentity.email == clean_email).first()

    if identity:
        return identity.user

    # Create new User
    # Ensure display_name is unique
    base_name = display_name.strip()[:24]
    name_candidate = base_name
    idx = 1
    while db.query(User).filter(User.display_name == name_candidate).first():
        name_candidate = f"{base_name}_{idx}"
        idx += 1

    new_user = User(
        display_name=name_candidate,
        role=role,
        level=1,
        languages=["en"],
        fields=[],
        status="active",
        joined_at=utcnow(),
        last_active_at=utcnow(),
    )
    db.add(new_user)
    db.flush()

    new_identity = AuthIdentity(
        user_id=new_user.id,
        provider=provider,
        provider_subject=provider_subject or secrets.token_hex(8),
        email=clean_email,
        email_verified_at=utcnow(),
    )
    db.add(new_identity)

    new_stats = ReviewerStats(
        user_id=new_user.id,
        reviews_total=0,
        gold_seen=0,
        gold_correct=0,
        agree_with_consensus=0,
        decided_seen=0,
        weekly_count=0,
        updated_at=utcnow(),
    )
    db.add(new_stats)

    db.commit()
    db.refresh(new_user)
    return new_user
