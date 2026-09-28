# GOVERNANCE.md — How decisions are made in OpenPaperCheck

Status: active · Last updated: 2026-09-28

This document describes how the OpenPaperCheck project is governed, how maintainers are appointed, and how technical and ethical decisions are made.

---

## 1. Principles of Governance
1. **Openness:** All technical discussions, feature roadmaps, and policy debates happen in public on GitHub Discussions and Issues.
2. **Evidence-Based:** Architectural and ethical choices are backed by data, benchmarks, or peer-reviewed literature.
3. **Lazy Consensus:** For routine technical changes, silence is consent. Proposals remain open for at least 72 hours; if no objections are raised, they proceed.
4. **Zero Pay-for-Flags:** No financial donation, sponsorship, or institutional affiliation can alter, suppress, or create a public flag on any paper. Ever.

---

## 2. Roles and Responsibilities

### Maintainers
- Review and merge pull requests.
- Hold deployment and release credentials.
- Enforce the Code of Conduct and the [ETHICS.md](ETHICS.md) policy.
- Lead authoring of Architecture Decision Records (ADRs).

### Moderators
- Manage author and publisher appeals via `/v1/moderation/appeals`.
- Have authority to trigger the 1-hour emergency hide drill for factual errors.
- Review volunteer notes and suspend malicious or brigading accounts.
- **Requirement:** At least two distinct individuals must hold moderator rights before community-derived signals become public.

### Senior Reviewers (Level 4)
- Handle escalated review tasks where volunteers disagreed or marked "unsure".
- Author gold-standard tutorial and quality-check tasks.

### Contributors
- Anyone who submits a pull request, translates UI strings, audits datasets, or reviews cards.

---

## 3. Path to Maintainership
We actively encourage contributors to become maintainers:
1. **Contributor:** After 3 merged pull requests or substantial review verification, you will be invited to the GitHub organization triage team.
2. **Maintainer:** Contributors with **10+ merged non-trivial PRs** who demonstrate sustained commitment and align with our ethical principles will be nominated for full maintainership. Appointment requires unanimous consent among existing maintainers.

---

## 4. Decision Making & ADRs
- **Routine Changes:** Handled via Pull Requests with at least 1 maintainer approval (2 approvals required for `auth/`, `consensus/`, and public signals).
- **Major Architectural & Policy Changes:** Require an **Architecture Decision Record (ADR)** in `docs/adr/NNNN-title.md` and a 7-day discussion period on GitHub Discussions.
