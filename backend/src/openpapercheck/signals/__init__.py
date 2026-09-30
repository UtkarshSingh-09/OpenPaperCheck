"""
Signals package for OpenPaperCheck.
Deterministic evidence signals (S-001, S-002, S-003, S-010, S-040).
Strictly adheres to ETHICS.md and SIGNALS_AND_ML.md:
- Zero personal, geographic, or organizational demographics.
- No banned words in descriptions.
- Sourced facts only.
"""

from openpapercheck.signals.registry import (
    Signal,
    SignalId,
    compute_signals,
)

__all__ = ["Signal", "SignalId", "compute_signals"]
