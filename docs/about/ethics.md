# OpenPaperCheck Ethics & Integrity Charter

Scholarly evaluation requires high ethical rigor, humility, and transparency. OpenPaperCheck operates under strict ethical constraints to prevent algorithmic harm and protect academic freedom.

---

## 1. Zero Personal Profiling (Audit Works, Not People)

OpenPaperCheck audits **papers and their citations**, never human researchers.

- **No Author Demographics:** We never ingest, compute, or store author gender, nationality, race, ethnicity, or country of origin.
- **No Institutional Ranking:** We never weight papers based on university prestige or geographic location.
- **No Personal Scores:** We do not compute author "risk scores", "credibility metrics", or h-index penalties.
- **No Blacklists:** Algorithms must never maintain blacklists of individuals.

---

## 2. Banned Words Standard

Subjective, emotional, and accusatory language damages scientific communication and peer evaluation. OpenPaperCheck strictly bans the following terms across all API payloads, CLI terminal outputs, and web views:

```text
"fake", "fraud", "fraudulent", "scam", "cheat", "guilty", "criminal", "shady", "predatory"
```

### Automated Enforcement:
Automated continuous integration tests (`test_fairness_allowlist.py` and `test_api.py`) inspect all templates and string outputs. Any pull request introducing a banned term fails automatically.

### Factual Replacement:
Instead of subjective characterizations, OpenPaperCheck reports strictly verifiable facts:
- *Instead of "fraudulent paper":* "Retracted according to Retraction Watch (Record #4036, notice date 2010-02-06)."
- *Instead of "scam citations":* "2 of 28 references with persistent DOIs are recorded as retracted."

---

## 3. Absence of a Flag is Not Endorsement

A state of `NO FLAGS FOUND` strictly indicates that no formal retraction notices or expressions of concern exist within the indexed snapshot.

> **Important:** It is **NOT** a certificate of scientific correctness, replicability, statistical validity, or integrity. Peer review, scientific replication, and critical community evaluation on platforms like PubPeer remain essential.

---

## 4. Moderation & Dispute Resolution

If an author or institution believes a paper report is displayed erroneously or subject to active legal dispute:
1. **Administrative Moderation Stub:** Administrators can temporarily hide a paper report via `opc hide <doi> --reason "..."`.
2. **RFC 9457 HTTP 451:** When hidden, the API returns standard HTTP 451 (Unavailable For Legal / Administrative Reasons) explaining the moderation status.
3. **Upstream Correction:** Because OpenPaperCheck mirrors authoritative registries (Retraction Watch, Crossref), corrections made at the upstream authority propagate automatically to OpenPaperCheck within 24 hours via nightly snapshot ingests.
