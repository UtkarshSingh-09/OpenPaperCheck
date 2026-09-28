# LOG.md — Data Sources License & Terms Verification Log

Status: living document · Last updated: 2026-09-28

Every external data source used by OpenPaperCheck is logged here upon addition, reviewed quarterly.

---

## 1. Retraction Watch Database (via Crossref GitLab)
- **Date checked:** 2026-09-28
- **URL of terms:** https://gitlab.com/crossref/retraction-watch-data
- **License / terms summary:** Crossref publishes the Retraction Watch database openly. Bibliographic metadata is dedicated to the public domain under CC0 1.0 Universal.
- **What we store:** Record ID, original DOI, retraction DOI, nature, reasons verbatim, retraction date, original date, notice URLs.
- **What we drop at ingest:** Author, Institution, Country (Fairness non-negotiable).
- **What we redistribute in open dataset:** Verified labels, agreement stats, DOIs, verbatim reasons. No abstracts.
- **Attribution text:** "Retraction data provided by the Retraction Watch database, published by Crossref."
- **Re-check date:** 2026-12-28

---

## 2. Crossref REST API
- **Date checked:** 2026-09-28
- **URL of terms:** https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- **License / terms summary:** Metadata CC0 1.0 Universal, except abstracts which remain under author/publisher copyright.
- **Rate limits / pool:** Polite pool requires `mailto:` in User-Agent / query params. Dynamic rate limit reading via `x-rate-limit-*` headers.
- **What we store:** Title, journal, publisher, publication date, reference DOIs, reference position, update relationships.
- **What we redistribute in open dataset:** Reference graph links (DOIs only). Never redistribute abstracts.
- **Re-check date:** 2026-12-28

---

## 3. OpenAlex API
- **Date checked:** 2026-09-28
- **URL of terms:** https://openalex.org/pricing
- **License / terms summary:** Data CC0. API keys mandatory since 2026-02-13. Free tier allowance (~$1/day).
- **Usage:** Optional fallback client only. Budget guard terminates fallback lookups if daily quota is < 20%.
- **Re-check date:** 2026-12-28
