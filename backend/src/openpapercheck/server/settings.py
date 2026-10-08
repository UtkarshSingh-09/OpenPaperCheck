"""
Server and runtime settings for OpenPaperCheck.
"""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database: SQLite fallback for local test/dev, PostgreSQL in production
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{Path.home()}/.cache/openpapercheck/server.db",
    )

    # Session & Auth
    SESSION_SECRET_KEY: str = "opc-dev-session-secret-change-in-production-12345678"
    SESSION_COOKIE_NAME: str = "opc_session"
    SESSION_EXPIRE_HOURS: int = 168  # 7 days
    CSRF_SECRET_KEY: str = "opc-dev-csrf-secret-change-in-production-87654321"

    # Environment
    ENVIRONMENT: str = "development"
    DEV_AUTH_ENABLED: bool = True

    # Review limits & task configuration
    DEFAULT_LEASE_MINUTES: int = 30
    REQUIRED_REVIEWS_PER_TASK: int = 3


settings = ServerSettings()
