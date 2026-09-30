"""
Deterministic Rule-Based Signals Registry for OpenPaperCheck.
Computes standardized factual signals S-001, S-002, S-003, S-010, S-040.
Adheres strictly to ETHICS.md and SIGNALS_AND_ML.md.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from openpapercheck.core.models import CitationTiming, evaluate_citation_timing


class SignalId(str, Enum):
    S_001 = "S-001"  # Retracted target paper
    S_002 = "S-002"  # Expression of concern on target paper
    S_003 = "S-003"  # Correction / Reinstatement on target paper
    S_010 = "S-010"  # Cites retracted papers count and details
    S_040 = "S-040"  # Data coverage and reference deposit status


class Signal(BaseModel):
    id: SignalId
    name: str
    category: str  # "target_paper" | "references" | "coverage"
    is_public: bool = True
    value: Any
    description: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)


def compute_signals(
    canonical_doi: str,
    paper_retraction: dict[str, Any] | None,
    work_data: dict[str, Any],
    retracted_refs_map: dict[str, dict[str, Any]],
) -> list[Signal]:
    """
    Compute deterministic signals for a paper and its bibliography.
    Produces zero personal opinions; every claim links to an authority.
    """
    signals: list[Signal] = []
    pub_date = work_data.get("published_date") or ""
    refs_meta = work_data.get("references", {})
    deposit_status = refs_meta.get("deposit_status", "missing")
    with_doi = refs_meta.get("with_doi", [])
    without_doi = refs_meta.get("without_doi", [])
    total_listed = refs_meta.get("total_listed", len(with_doi) + len(without_doi))

    nature = (paper_retraction.get("nature") or "") if paper_retraction else ""

    # S-001: Target paper retracted
    is_retracted = nature.lower() == "retraction"
    s001_evidence: list[dict[str, Any]] = []
    if is_retracted and paper_retraction:
        s001_evidence.append({
            "source": "Retraction Watch",
            "rw_record_id": paper_retraction.get("rw_record_id"),
            "nature": paper_retraction.get("nature"),
            "retraction_date": paper_retraction.get("retraction_date"),
            "original_date": paper_retraction.get("original_date"),
            "notice_doi": paper_retraction.get("retraction_doi"),
            "reasons": paper_retraction.get("reasons", []),
            "notice_urls": paper_retraction.get("notice_urls", ""),
        })
    signals.append(
        Signal(
            id=SignalId.S_001,
            name="retracted",
            category="target_paper",
            is_public=True,
            value=is_retracted,
            description=(
                f"Retracted according to Retraction Watch (Record #{paper_retraction.get('rw_record_id')}, "
                f"{paper_retraction.get('retraction_date')})."
                if is_retracted and paper_retraction
                else "No retraction recorded for this DOI in Retraction Watch."
            ),
            evidence=s001_evidence,
        )
    )

    # S-002: Expression of concern
    is_eoc = nature.lower() == "expression of concern"
    s002_evidence: list[dict[str, Any]] = []
    if is_eoc and paper_retraction:
        s002_evidence.append({
            "source": "Retraction Watch",
            "rw_record_id": paper_retraction.get("rw_record_id"),
            "nature": "Expression of concern",
            "retraction_date": paper_retraction.get("retraction_date"),
            "notice_doi": paper_retraction.get("retraction_doi"),
            "reasons": paper_retraction.get("reasons", []),
        })
    signals.append(
        Signal(
            id=SignalId.S_002,
            name="expression_of_concern",
            category="target_paper",
            is_public=True,
            value=is_eoc,
            description=(
                f"An Expression of Concern has been recorded by Retraction Watch (Record #{paper_retraction.get('rw_record_id')})."
                if is_eoc and paper_retraction
                else "No expression of concern recorded for this DOI."
            ),
            evidence=s002_evidence,
        )
    )

    # S-003: Reinstated or corrected
    is_correction = nature.lower() in ("correction", "reinstatement")
    s003_evidence: list[dict[str, Any]] = []
    if is_correction and paper_retraction:
        s003_evidence.append({
            "source": "Retraction Watch",
            "rw_record_id": paper_retraction.get("rw_record_id"),
            "nature": nature,
            "date": paper_retraction.get("retraction_date"),
            "notice_doi": paper_retraction.get("retraction_doi"),
            "reasons": paper_retraction.get("reasons", []),
        })
    signals.append(
        Signal(
            id=SignalId.S_003,
            name="reinstated_or_corrected",
            category="target_paper",
            is_public=True,
            value=is_correction,
            description=(
                f"A publisher notice of type '{nature}' has been recorded (Record #{paper_retraction.get('rw_record_id')})."
                if is_correction and paper_retraction
                else "No correction or reinstatement notice recorded."
            ),
            evidence=s003_evidence,
        )
    )

    # S-010: Cites retracted papers count and breakdown
    retracted_refs_count = len(retracted_refs_map)
    s010_evidence: list[dict[str, Any]] = []
    for r in with_doi:
        r_doi = r["doi"]
        if r_doi in retracted_refs_map:
            info = retracted_refs_map[r_doi]
            ret_date = info.get("retraction_date") or ""
            timing = evaluate_citation_timing(pub_date, ret_date)
            s010_evidence.append({
                "reference_doi": r_doi,
                "position": r.get("position"),
                "retraction_date": ret_date,
                "nature": info.get("nature", "Retraction"),
                "timing": timing.value,
                "rw_record_id": info.get("rw_record_id"),
                "reasons": info.get("reasons", []),
            })

    s010_desc = (
        f"{retracted_refs_count} of {len(with_doi)} references with DOIs are recorded as retracted."
        if retracted_refs_count > 0
        else f"0 of {len(with_doi)} references with DOIs are recorded as retracted."
    )
    if without_doi:
        s010_desc += f" {len(without_doi)} unstructured references without DOIs could not be checked."

    signals.append(
        Signal(
            id=SignalId.S_010,
            name="cites_retracted_count",
            category="references",
            is_public=True,
            value=retracted_refs_count,
            description=s010_desc,
            evidence=s010_evidence,
        )
    )

    # S-040: Data coverage & deposit honesty
    signals.append(
        Signal(
            id=SignalId.S_040,
            name="data_coverage",
            category="coverage",
            is_public=True,
            value={
                "deposit_status": deposit_status,
                "total_listed_references": total_listed,
                "references_with_doi_count": len(with_doi),
                "unstructured_without_doi_count": len(without_doi),
                "doi_coverage_ratio": (len(with_doi) / total_listed) if total_listed > 0 else 0.0,
            },
            description=(
                f"Publisher reference deposit status: '{deposit_status}'. "
                f"Checked {len(with_doi)} DOI references out of {total_listed} total listed."
            ),
            evidence=[{
                "provider": "Crossref",
                "deposit_status": deposit_status,
                "has_references": bool(with_doi or without_doi),
            }],
        )
    )

    return signals
