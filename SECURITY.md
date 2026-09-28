# SECURITY.md — Vulnerability reporting and security policies

Status: active · Last updated: 2026-09-28

OpenPaperCheck takes the security of its infrastructure and the privacy of its contributors seriously.

---

## 1. Reporting a Vulnerability

**Please do NOT report security vulnerabilities via public GitHub issues.**

Instead, report vulnerabilities via:
1. **GitHub Private Security Advisory:** Open an advisory under our repository's `Security` tab.
2. **Email:** Send details to `security@openpapercheck.org` (or maintainer direct contact).

Include:
- Type of issue (e.g. CSRF, SQL injection, authentication bypass, data leak).
- Clear step-by-step reproduction instructions or a minimal proof of concept.
- Expected vs. actual behavior.

---

## 2. Response Commitments and SLAs

| Milestone | Target SLA |
|---|---|
| Initial acknowledgement | Within 48 hours |
| Vulnerability triage and severity confirmation | Within 5 working days |
| Security patch release (SEV-1 / Critical) | Within 24–48 hours |
| Standard patch release | Within 14 days |

All security fixes are credited in our public release notes (unless the reporter requests anonymity).

---

## 3. Data Breach & Wrong-Flag Emergencies
- If a security bug compromises personal data (reviewer emails) or causes a wrongful public flag on an innocent paper, our **SEV-1 Incident Protocol** activates immediately:
  - Containment within **1 hour** (page hidden, credentials rotated).
  - Affected parties notified promptly.
  - A blameless post-mortem published in `docs/incidents/` within 5 days.

---

## 4. Out of Scope
- Factual corrections to external retraction data (e.g. claiming a publisher notice is wrong): use the `/appeal` form or email `appeals@openpapercheck.org`.
- Theoretical vulnerabilities without practical exploit scenarios.
- Denial of Service (DDoS) against our rate limits.
