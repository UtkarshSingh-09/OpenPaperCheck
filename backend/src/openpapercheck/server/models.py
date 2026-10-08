"""
SQLAlchemy models for OpenPaperCheck Server.
Implements the relational schema defined in docs/DATABASE.md.
Strictly adheres to ETHICS.md: zero author/demographic tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from openpapercheck.server.db import Base


def utcnow() -> datetime:
    """Current UTC datetime."""
    return datetime.now(timezone.utc)


def gen_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


class User(Base):
    """Registered reviewer or administrator."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    display_name = Column(String(30), unique=True, nullable=False, index=True)
    role = Column(String(20), nullable=False, default="reviewer")  # reviewer, senior_reviewer, moderator, admin
    level = Column(Integer, nullable=False, default=1)  # 1..4
    languages = Column(JSON, nullable=False, default=lambda: ["en"])
    fields = Column(JSON, nullable=False, default=list)  # self-declared fields of study
    tutorial_done_at = Column(DateTime(timezone=True), nullable=True)
    conflict_note = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active")  # active, suspended, deleted
    joined_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    identities = relationship("AuthIdentity", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    stats = relationship("ReviewerStats", back_populates="user", uselist=False, cascade="all, delete-orphan")


class AuthIdentity(Base):
    """The only table where user contact/email lives; strictly isolated."""
    __tablename__ = "auth_identities"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(20), nullable=False)  # 'google', 'email', 'dev_mock'
    provider_subject = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="identities")

    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="uq_auth_provider_sub"),
    )


class Session(Base):
    """User browser sessions authenticated with HTTP-only cookies."""
    __tablename__ = "sessions"

    id_hash = Column(String(64), primary_key=True)  # SHA-256 hex of secret session token
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ip_hash = Column(String(64), nullable=True)
    ua_hash = Column(String(64), nullable=True)

    user = relationship("User", back_populates="sessions")


class ReviewTask(Base):
    """A human verification task holding machine-generated evidence to verify."""
    __tablename__ = "review_tasks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    paper_doi = Column(String(255), nullable=False, index=True)
    task_type = Column(String(32), nullable=False)  # ref_match, retraction_match, notice_reason, tortured_phrase, evidence_check
    payload = Column(JSON, nullable=False)  # Card data presented to the reviewer
    payload_hash = Column(String(64), nullable=False, index=True)  # Deduplication hash
    difficulty = Column(Integer, nullable=False, default=1)  # 1..4
    subject = Column(String(100), nullable=True)
    language = Column(String(10), nullable=False, default="en")
    status = Column(String(20), nullable=False, default="open", index=True)  # open, in_review, needs_senior, decided, withdrawn
    required_reviews = Column(Integer, nullable=False, default=3)
    priority = Column(Integer, nullable=False, default=0)
    is_gold = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    gold = relationship("GoldTask", back_populates="task", uselist=False, cascade="all, delete-orphan")
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="task", cascade="all, delete-orphan")
    consensus = relationship("ConsensusLabel", back_populates="task", uselist=False)

    __table_args__ = (
        UniqueConstraint("task_type", "payload_hash", name="uq_task_type_payload"),
    )


class GoldTask(Base):
    """Known benchmark task with verified ground-truth answer and tutorial explanation."""
    __tablename__ = "gold_tasks"

    task_id = Column(String(36), ForeignKey("review_tasks.id", ondelete="CASCADE"), primary_key=True)
    correct_verdict = Column(String(10), nullable=False)  # 'yes', 'no', 'unsure'
    explanation = Column(Text, nullable=False)  # Explanation shown after reviewer answers
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    task = relationship("ReviewTask", back_populates="gold")


class TaskAssignment(Base):
    """Lease management enforcing reviewer independence and expiration."""
    __tablename__ = "task_assignments"

    task_id = Column(String(36), ForeignKey("review_tasks.id", ondelete="CASCADE"), primary_key=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)  # 30-min lease
    status = Column(String(20), nullable=False, default="assigned")  # assigned, done, expired, skipped

    task = relationship("ReviewTask", back_populates="assignments")
    reviewer = relationship("User")


class Review(Base):
    """An independent human evaluation vote on a task card."""
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    task_id = Column(String(36), ForeignKey("review_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    verdict = Column(String(10), nullable=False)  # 'yes', 'no', 'unsure'
    note = Column(String(500), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    reviewer_level_at_time = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    task = relationship("ReviewTask", back_populates="reviews")
    reviewer = relationship("User")

    __table_args__ = (
        UniqueConstraint("task_id", "reviewer_id", name="uq_task_reviewer_vote"),
    )


class ConsensusLabel(Base):
    """Official decided label determined via 3-reviewer majority or senior override."""
    __tablename__ = "consensus_labels"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    task_id = Column(String(36), ForeignKey("review_tasks.id", ondelete="CASCADE"), nullable=False, unique=True)
    paper_doi = Column(String(255), nullable=False, index=True)
    task_type = Column(String(32), nullable=False)
    label = Column(String(10), nullable=False)  # 'yes', 'no'
    n_reviews = Column(Integer, nullable=False)
    n_agree = Column(Integer, nullable=False)
    agreement = Column(Float, nullable=False)
    method = Column(String(30), nullable=False)  # 'majority_3', 'senior_override'
    decided_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    task = relationship("ReviewTask", back_populates="consensus")


class ReviewerStats(Base):
    """Reviewer performance and gold accuracy stats (private to the reviewer)."""
    __tablename__ = "reviewer_stats"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    reviews_total = Column(Integer, nullable=False, default=0)
    gold_seen = Column(Integer, nullable=False, default=0)
    gold_correct = Column(Integer, nullable=False, default=0)
    agree_with_consensus = Column(Integer, nullable=False, default=0)
    decided_seen = Column(Integer, nullable=False, default=0)
    weekly_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    user = relationship("User", back_populates="stats")


class AuditLog(Base):
    """Tamper-evident record of administrative and moderation actions."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
