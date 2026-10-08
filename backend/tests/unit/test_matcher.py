"""
Unit tests for the fuzzy reference string matcher.
"""

from __future__ import annotations

from openpapercheck.tasks.matcher import extract_years, match_reference, tokenize


def test_tokenize_removes_stopwords():
    tokens = tokenize("Effects of Hydroxychloroquine on COVID-19 in Lancet")
    assert "effects" in tokens
    assert "hydroxychloroquine" in tokens
    assert "covid" in tokens
    assert "19" in tokens
    assert "lancet" in tokens
    assert "of" not in tokens
    assert "on" not in tokens
    assert "in" not in tokens


def test_extract_years():
    assert extract_years("Smith et al. (2020) Nature 580:123") == {2020}
    assert extract_years("Compare 1998 Wakefield to 2010 retraction") == {1998, 2010}
    assert extract_years("No date in this reference") == set()


def test_match_reference_high_confidence():
    raw = "Wakefield AJ et al. Ileal-lymphoid-nodular hyperplasia. Lancet. 1998; 351: 637-641."
    cand_title = "Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasive developmental disorder in children"
    res = match_reference(raw, cand_title, candidate_year=1998, candidate_journal="Lancet")
    assert res["confidence"] >= 0.70
    assert res["year_match"] is True
    assert res["journal_match"] is True


def test_match_reference_conflicting_year_penalized():
    raw = "Smith J. Genetic markers. Science 2022."
    cand_title = "Genetic markers in plant populations"
    res_2022 = match_reference(raw, cand_title, candidate_year=2022)
    res_1995 = match_reference(raw, cand_title, candidate_year=1995)
    assert res_2022["confidence"] > res_1995["confidence"]
    assert res_1995["year_match"] is False


def test_match_reference_ambiguous_needs_human_check():
    raw = "Doe et al. Study of neural networks. 2021."
    cand_title = "Deep neural networks for image synthesis"
    res = match_reference(raw, cand_title, candidate_year=2021)
    # Ambiguous partial match should trigger human verification
    assert 0.40 <= res["confidence"] <= 0.95
