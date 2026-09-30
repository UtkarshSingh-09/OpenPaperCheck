"""
DOI Inspection Endpoints for OpenPaperCheck REST API (v1).
Provides GET /v1/check/{doi:path}
Strictly follows API_SPEC.md, ETHICS.md, and SIGNALS_AND_ML.md.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Query

from openpapercheck import __version__
from openpapercheck.core.crossref import CrossrefClient
from openpapercheck.core.doi import is_valid_doi, normalize_doi
from openpapercheck.core.models import (
    CitationTiming,
    PaperPublicState,
    determine_paper_state,
    evaluate_citation_timing,
)
from openpapercheck.core.storage import (
    check_reference_dois,
    get_manifest,
    get_retraction,
    has_snapshot,
    is_doi_hidden,
)
from openpapercheck.signals.registry import compute_signals
from openpapercheck.api.errors import (
    DoiNotFoundError,
    InvalidDoiError,
    PaperHiddenError,
    UpstreamServiceError,
)
from openpapercheck.api.schemas import (
    CheckResponse,
    CoverageInfo,
    PaperMetadata,
    ReferenceBreakdown,
    RetractedRefInfo,
)

router = APIRouter(tags=["Check"])

ETHICAL_DISCLAIMER = (
    "This tool reports external sourced facts. Absence of a flag is not endorsement. "
    "Every claim links to an authority. It is not a judgement of paper quality or of any person."
)


@router.get(
    "/check/{doi:path}",
    response_model=CheckResponse,
    summary="Inspect a paper and its references for retractions",
    description="Returns public integrity state, deterministic signals, and reference breakdown for any DOI.",
)
async def check_paper(
    doi: str,
    email: str | None = Query(None, description="Optional email for Crossref polite pool priority"),
) -> CheckResponse:
    # 1. Clean and normalize DOI
    canonical_doi = normalize_doi(doi)
    if not canonical_doi or not is_valid_doi(canonical_doi):
        raise InvalidDoiError(doi)

    # Check administrative moderation status
    hidden, reason = is_doi_hidden(canonical_doi)
    if hidden:
        raise PaperHiddenError(canonical_doi, reason)

    manifest = get_manifest() or {}
    as_of_date = manifest.get("as_of", "local database")
    is_sample = manifest.get("is_sample", False)
    rows_count = manifest.get("rows_count")

    # 2. Fetch bibliographic metadata and references from Crossref
    client = CrossrefClient(mailto=email)
    try:
        work = client.get_work(canonical_doi)
    except httpx.TimeoutException as exc:
        raise UpstreamServiceError("Crossref API", "Connection timed out querying Crossref.") from exc
    except httpx.RequestError as exc:
        raise UpstreamServiceError("Crossref API", f"Network error reaching api.crossref.org: {exc}") from exc
    except Exception as exc:
        raise UpstreamServiceError("Crossref API", str(exc)) from exc

    if not work:
        raise DoiNotFoundError(canonical_doi)

    # 3. Check target paper retraction in local database
    paper_retraction = None
    if has_snapshot():
        paper_retraction = get_retraction(canonical_doi)

    # 4. Check references
    refs_meta = work.get("references", {})
    deposit_status = refs_meta.get("deposit_status", "missing")
    with_doi = refs_meta.get("with_doi", [])
    without_doi = refs_meta.get("without_doi", [])
    total_listed = refs_meta.get("total_listed", len(with_doi) + len(without_doi))

    retracted_refs_map: dict[str, dict] = {}
    if has_snapshot() and with_doi:
        ref_dois = [r["doi"] for r in with_doi if "doi" in r]
        retracted_refs_map = check_reference_dois(ref_dois)

    # 5. Evaluate deterministic state and signals
    state = determine_paper_state(paper_retraction, refs_meta, retracted_refs_map)
    signals = compute_signals(canonical_doi, paper_retraction, work, retracted_refs_map)

    # 6. Format headline
    if state == PaperPublicState.RETRACTED_EXTERNAL:
        nature = paper_retraction.get("nature", "Retraction") if paper_retraction else "Retraction"
        nature_label = "RETRACTED" if nature.lower() == "retraction" else nature.upper()
        headline = f"Paper is {nature_label} according to Retraction Watch"
    elif state == PaperPublicState.NEEDS_REVIEW:
        if paper_retraction and paper_retraction.get("nature") == "Expression of concern":
            headline = "Paper has an Expression of Concern recorded"
        else:
            headline = f"Cites {len(retracted_refs_map)} flagged or retracted reference(s)"
    elif state == PaperPublicState.INSUFFICIENT_DATA:
        if deposit_status == "restricted":
            headline = "Publisher has restricted open access to references"
        else:
            headline = "No reference list was deposited for this work in Crossref"
    else:
        headline = "No retractions or flagged references recorded"

    # 7. Construct reference breakdown
    retracted_refs_list: list[RetractedRefInfo] = []
    pub_date = work.get("published_date") or ""
    for r in with_doi:
        r_doi = r["doi"]
        if r_doi in retracted_refs_map:
            info = retracted_refs_map[r_doi]
            ret_date = info.get("retraction_date") or ""
            timing = evaluate_citation_timing(pub_date, ret_date)
            retracted_refs_list.append(
                RetractedRefInfo(
                    position=r.get("position"),
                    doi=r_doi,
                    nature=info.get("nature") or "Retraction",
                    retraction_date=ret_date,
                    timing=timing.value,
                    rw_record_id=info.get("rw_record_id"),
                    reasons=info.get("reasons") or [],
                )
            )

    references_breakdown = ReferenceBreakdown(
        available=deposit_status in ("open", "deposited"),
        deposit_status=deposit_status,
        source="crossref",
        total=total_listed,
        with_doi=len(with_doi),
        without_doi=len(without_doi),
        retracted=retracted_refs_list,
    )

    data_as_of_map = {
        "retraction_watch": as_of_date,
        "crossref": "live-api",
    }
    if is_sample:
        data_as_of_map["sample_mode_notice"] = f"{rows_count or 11} test records only (run opc update for full database)"

    # PubPeer search link
    pubpeer_url = f"https://pubpeer.com/search?q={canonical_doi}"

    return CheckResponse(
        doi=canonical_doi,
        state=state,
        headline=headline,
        paper=PaperMetadata(
            title=work.get("title") or "Untitled Paper",
            journal=work.get("journal") or "",
            publisher=work.get("publisher") or "",
            publication_date=pub_date,
            doi=canonical_doi,
        ),
        signals=signals,
        references=references_breakdown,
        coverage=CoverageInfo(
            sources_answered=["crossref", "retraction_watch"] if has_snapshot() else ["crossref"],
            sources_failed=[],
        ),
        data_as_of=data_as_of_map,
        external_links={
            "pubpeer": pubpeer_url,
            "pubpeer_search": pubpeer_url,
            "doi_resolver": f"https://doi.org/{canonical_doi}",
        },
        disclaimer=ETHICAL_DISCLAIMER,
    )
