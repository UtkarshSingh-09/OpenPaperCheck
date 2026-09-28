"""
Pytest configuration and shared fixtures for OpenPaperCheck tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def golden_dois(fixtures_dir: Path) -> list[dict]:
    golden_file = fixtures_dir / "golden_dois.json"
    with open(golden_file, encoding="utf-8") as f:
        return json.load(f)
