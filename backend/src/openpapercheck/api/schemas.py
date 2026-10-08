"""
Pydantic Schemas for OpenPaperCheck REST API (v1).
Strictly follows API_SPEC.md, SIGNALS_AND_ML.md, and ETHICS.md.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from openpapercheck.core.models import PaperPublicState
from openpapercheck.signals.registry import Signal


class ProblemDetail(BaseModel):
    """RFC 9457 / RFC 7807 Problem Details for HTTP APIs."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="URI reference identifying problem type")
    title: str = Field(..., description="Short, human-readable summary of problem")
    status: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Human-readable explanation specific to this occurrence")
    instance: str | None = Field(None, description="URI reference identifying specific occurrence")


class PaperMetadata(BaseModel):
    """Bibliographic metadata for target paper."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Primary title of the paper")
    journal: str = Field("", description="Container / journal title")
    publisher: str = Field("", description="Publisher name")
    publication_date: str = Field(
        "", description="ISO date of publication (YYYY, YYYY-MM, or YYYY-MM-DD)"
    )
    doi: str = Field(..., description="Canonical normalised DOI")


class RetractedRefInfo(BaseModel):
    """Information regarding a single retracted or problematic reference."""

    model_config = ConfigDict(extra="forbid")

    position: int | None = Field(None, description="Position index in reference list")
    doi: str = Field(..., description="Normalised DOI of cited paper")
    nature: str = Field("Retraction", description="Notice type (Retraction, Expression of concern)")
    retraction_date: str = Field("", description="ISO date of retraction notice")
    timing: str = Field(
        "unknown", description="cited_after_retraction | cited_before_retraction | unknown"
    )
    rw_record_id: int | None = Field(None, description="Retraction Watch Record ID")
    reasons: list[str] = Field(
        default_factory=list, description="Verbatim reasons from Retraction Watch"
    )


class ReferenceBreakdown(BaseModel):
    """3-Tier Reference integrity breakdown."""

    model_config = ConfigDict(extra="forbid")

    available: bool = Field(..., description="True if reference list is deposited and open")
    deposit_status: str = Field(..., description="open | restricted | missing")
    source: str = Field("crossref", description="Source provider of citation metadata")
    total: int = Field(..., description="Total references listed by publisher")
    with_doi: int = Field(..., description="References containing a valid persistent DOI")
    without_doi: int = Field(
        ..., description="Unstructured text references lacking persistent DOIs"
    )
    retracted: list[RetractedRefInfo] = Field(
        default_factory=list, description="Retracted references identified"
    )


class CoverageInfo(BaseModel):
    """Provenance and answering sources."""

    model_config = ConfigDict(extra="forbid")

    sources_answered: list[str] = Field(default_factory=list)
    sources_failed: list[str] = Field(default_factory=list)


class CheckResponse(BaseModel):
    """Full check response payload for a DOI."""

    model_config = ConfigDict(extra="forbid")

    doi: str = Field(..., description="Canonical normalised DOI")
    state: PaperPublicState = Field(
        ...,
        description="Public state: retracted_external | needs_review | no_flags_found | insufficient_data",
    )
    headline: str = Field(..., description="Honest human-readable headline summary")
    paper: PaperMetadata = Field(..., description="Paper bibliographic metadata")
    signals: list[Signal] = Field(
        default_factory=list, description="Standardized deterministic signals"
    )
    references: ReferenceBreakdown = Field(..., description="Reference list audit")
    coverage: CoverageInfo = Field(..., description="Source coverage details")
    data_as_of: dict[str, str] = Field(..., description="Freshness dates per data source")
    external_links: dict[str, str] = Field(
        default_factory=dict, description="External authority search links (PubPeer, etc.)"
    )
    disclaimer: str = Field(
        ..., description="Ethical disclaimer: reports external facts, not personal judgement"
    )


class HealthResponse(BaseModel):
    """Health check response for monitoring and uptime probes."""

    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    version: str
    db: str = "ok"
    as_of: str
    records_count: int | None
    is_sample: bool = False


class SourceMetadata(BaseModel):
    """Metadata for upstream scholarly data authority."""

    model_config = ConfigDict(extra="forbid")

    name: str
    authority: str
    license: str
    records_count: int | None
    as_of_date: str
    description: str


class SourcesResponse(BaseModel):
    """Transparency response listing all active data sources."""

    model_config = ConfigDict(extra="forbid")

    sources: list[SourceMetadata]
