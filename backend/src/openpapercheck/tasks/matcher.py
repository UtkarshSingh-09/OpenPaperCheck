"""
Fuzzy Reference String Matcher for OpenPaperCheck.
Matches raw bibliographic citation strings against scholarly work records.
Determines when ambiguous machine matches require human verification (Task T1).
"""

from __future__ import annotations

import re
from typing import Any

YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
WORD_PATTERN = re.compile(r"[a-z0-9]+")

STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "by", "for", "with",
    "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "of", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now", "et", "al", "vol",
    "pp", "page", "pages", "issue", "no", "doi", "org", "https", "http",
}


def tokenize(text: str) -> set[str]:
    """Tokenize and remove common stopwords."""
    if not text:
        return set()
    tokens = set(WORD_PATTERN.findall(text.lower()))
    return tokens - STOPWORDS


def extract_years(text: str) -> set[int]:
    """Extract all 4-digit publication years from string."""
    if not text:
        return set()
    return {int(y) for y in YEAR_PATTERN.findall(text)}


def token_overlap_ratio(raw_tokens: set[str], candidate_tokens: set[str]) -> float:
    """
    Compute title overlap ratio.
    Balances between coverage of candidate title and match density to handle abbreviated citations.
    """
    if not raw_tokens or not candidate_tokens:
        return 0.0
    intersection = len(raw_tokens & candidate_tokens)
    if intersection == 0:
        return 0.0

    containment = intersection / len(candidate_tokens)
    # Grant density boost if 2 or more distinct key tokens match
    density_boost = min(0.35, (intersection - 1) * 0.10) if intersection >= 2 else 0.0
    return min(1.0, containment + density_boost)


def match_reference(
    raw_reference: str,
    candidate_title: str,
    candidate_year: int | str | None = None,
    candidate_journal: str | None = None,
) -> dict[str, Any]:
    """
    Score the match quality between an unstructured reference string and a candidate record.

    Returns:
        dict with confidence, title_similarity, year_match, journal_match,
        and needs_human_verification flag.
    """
    if not raw_reference or not candidate_title:
        return {
            "confidence": 0.0,
            "title_similarity": 0.0,
            "year_match": False,
            "journal_match": False,
            "needs_human_verification": False,
        }

    raw_tokens = tokenize(raw_reference)
    title_tokens = tokenize(candidate_title)

    title_similarity = token_overlap_ratio(raw_tokens, title_tokens)

    # Year checking
    raw_years = extract_years(raw_reference)
    cand_year_int = None
    if candidate_year:
        try:
            cand_year_int = int(str(candidate_year)[:4])
        except (ValueError, TypeError):
            pass

    year_match = False
    if cand_year_int and cand_year_int in raw_years:
        year_match = True

    # Journal checking
    journal_match = False
    if candidate_journal:
        j_tokens = tokenize(candidate_journal)
        if j_tokens and len(j_tokens & raw_tokens) >= max(1, len(j_tokens) // 2):
            journal_match = True

    # Compute weighted confidence score
    # Title content is 70% of score, year is 20%, journal is 10%
    score = title_similarity * 0.70
    if year_match:
        score += 0.20
    elif raw_years and cand_year_int and not year_match:
        # Conflicting year detected: penalize
        score -= 0.15

    if journal_match:
        score += 0.10

    confidence = round(max(0.0, min(1.0, score)), 3)

    # Human verification rule (per REVIEW_SYSTEM.md):
    # Needs human check if ambiguous (between 0.60 and 0.95 confidence)
    needs_human = 0.60 <= confidence < 0.95

    return {
        "confidence": confidence,
        "title_similarity": round(title_similarity, 3),
        "year_match": year_match,
        "journal_match": journal_match,
        "needs_human_verification": needs_human,
    }
