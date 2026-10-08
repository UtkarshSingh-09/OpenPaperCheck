"""
Unit tests for paper moderation stub (opc hide / unhide / hidden)
and RFC 9457 HTTP 451 response from API.
"""

from pathlib import Path

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from openpapercheck.api.main import create_app
from openpapercheck.cli import app
from openpapercheck.core.storage import (
    hide_doi,
    is_doi_hidden,
    list_hidden_dois,
    unhide_doi,
)

runner = CliRunner()


def test_storage_hide_and_unhide(tmp_path: Path):
    db_file = tmp_path / "test_records.sqlite"
    doi = "10.1016/s0140-6736(97)11096-0"

    # Initially not hidden
    hidden, reason = is_doi_hidden(doi, db_path=db_file)
    assert not hidden
    assert reason is None

    # Hide DOI
    assert hide_doi(doi, reason="GDPR Article 17 request", db_path=db_file)
    hidden, reason = is_doi_hidden(doi, db_path=db_file)
    assert hidden is True
    assert reason == "GDPR Article 17 request"

    # List hidden
    all_hidden = list_hidden_dois(db_path=db_file)
    assert len(all_hidden) == 1
    assert all_hidden[0]["doi"] == doi

    # Unhide
    assert unhide_doi(doi, db_path=db_file)
    hidden, _ = is_doi_hidden(doi, db_path=db_file)
    assert not hidden
    assert len(list_hidden_dois(db_path=db_file)) == 0


def test_api_hidden_paper_returns_451(monkeypatch):
    client = TestClient(create_app())
    doi = "10.1016/s0140-6736(97)11096-0"

    # Mock is_doi_hidden to return True
    monkeypatch.setattr(
        "openpapercheck.api.routers.check.is_doi_hidden",
        lambda d: (True, "Under administrative review"),
    )

    resp = client.get(f"/v1/check/{doi}")
    assert resp.status_code == 451
    assert resp.headers["content-type"] == "application/problem+json"
    data = resp.json()
    assert data["status"] == 451
    assert "Under administrative review" in data["detail"]
    assert data["title"] == "Paper Report Hidden by Moderator"


def test_cli_hide_unhide_commands():
    doi = "10.1038/nature99999"

    # Hide via CLI
    res = runner.invoke(app, ["hide", doi, "--reason", "Dispute ongoing"])
    assert res.exit_code == 0
    assert "PAGE HIDDEN FROM PUBLIC VIEW" in res.output

    # List hidden
    res = runner.invoke(app, ["hidden"])
    assert res.exit_code == 0
    assert doi in res.output

    # Unhide via CLI
    res = runner.invoke(app, ["unhide", doi])
    assert res.exit_code == 0
    assert "PAGE UNHIDDEN" in res.output
