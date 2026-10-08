"""
Unit and property tests for the deterministic majority-of-3 consensus algorithm.
"""

from __future__ import annotations

import itertools

import pytest

from openpapercheck.consensus.majority import decide


def test_decide_waiting_when_insufficient_votes():
    assert decide(["yes"], required=3)["status"] == "waiting"
    assert decide(["yes", "no"], required=3)["status"] == "waiting"
    assert decide([], required=3)["status"] == "waiting"


@pytest.mark.parametrize(
    "votes,expected_label,expected_agree",
    [
        (["yes", "yes", "yes"], "yes", 1.0),
        (["no", "no", "no"], "no", 1.0),
        (["yes", "yes", "no"], "yes", 0.667),
        (["no", "no", "yes"], "no", 0.667),
        (["yes", "yes", "unsure"], "yes", 0.667),
        (["no", "no", "unsure"], "no", 0.667),
    ],
)
def test_decide_conclusive_majorities(votes, expected_label, expected_agree):
    res = decide(votes, required=3)
    assert res["status"] == "decided"
    assert res["label"] == expected_label
    assert res["n_agree"] >= 2
    assert res["agreement"] == expected_agree
    assert res["method"] == "majority_3"


@pytest.mark.parametrize(
    "votes",
    [
        ["yes", "no", "unsure"],  # 3-way split
        ["unsure", "unsure", "yes"],  # 2 unsures
        ["unsure", "unsure", "no"],  # 2 unsures
        ["unsure", "unsure", "unsure"],  # 3 unsures
    ],
)
def test_decide_escalates_to_senior_on_ties_or_unsure(votes):
    res = decide(votes, required=3)
    assert res["status"] == "needs_senior"


def test_decide_permutation_invariance():
    """Consensus must produce identical outcomes regardless of vote submission order."""
    test_cases = [
        ["yes", "yes", "no"],
        ["no", "yes", "no"],
        ["yes", "unsure", "yes"],
        ["yes", "no", "unsure"],
        ["unsure", "unsure", "no"],
    ]
    for case in test_cases:
        expected = decide(case)
        for perm in itertools.permutations(case):
            res = decide(list(perm))
            assert res["status"] == expected["status"]
            if res["status"] == "decided":
                assert res["label"] == expected["label"]
                assert res["agreement"] == expected["agreement"]
