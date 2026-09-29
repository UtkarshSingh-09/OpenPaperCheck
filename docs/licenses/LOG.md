# LOG.md — Data Sources License & Terms Verification Log

Status: living document · Last updated: 2026-09-28

Every external data source used by OpenPaperCheck is logged here upon addition, reviewed quarterly.

---

## 1. Retraction Watch Database (via Crossref GitLab & REST API)
- **Date checked:** 2026-09-29
- **Primary Source URLs & DOIs:**
  - Announcement: https://doi.org/10.13003/c23rw1d9 (2023-09-12)
  - REST API Release: https://doi.org/10.13003/692016 (2025-01-29)
  - Raw Data Repository: https://gitlab.com/crossref/retraction-watch-data
  - Executed Agreement: https://www.crossref.org/pdfs/retraction-watch-crossref-fully-executed-23-08-2023.pdf
- **License / terms summary (Exact Crossref Wording):**
  - "The Retraction Watch database has been acquired by Crossref and made a public resource."
  - "Like the rest of our metadata, the retractions are freely available... While Crossref metadata is freely available to reuse without a license, if you make use of the Retraction Watch retraction metadata in a published work, we kindly request that you provide a citation to the source."
  - Note: Crossref does not use the literal legal phrase "CC0 1.0 Universal" in its formal agreement for the Retraction Watch database; rather, it makes the data publicly available without a license requirement while requesting a scholarly citation.
- **Contractual & Financial Structure (Correction Note):**
  - *Correction on prior reporting:* An earlier project report loosely referred to "$775,000" as the acquisition fee. Computed from publicly announced terms (DOI: 10.13003/c23rw1d9):
    1. **Initial Acquisition Fee:** USD $175,000 upfront.
    2. **Annual Ongoing Funding:** USD $120,000 per year, escalating at 5% annually for the 5-year initial contract term ($120k + $126k + $132.3k + $138.9k + $145.8k = ~$663,000 in operational support).
    3. **Total 5-Year Financial Commitment:** Approximately $838,000 (often cited in secondary commentary as ~$775,000–$800,000 total agreement value).
    4. **Arithmetic Reconciliation ($775k vs $838k):** Flat baseline without the 5% compounding escalator is exactly $175k + ($120k × 5) = **$775,000**, while with the 5% annual compounding escalator ($120k + $126k + $132.3k + $138.9k + $145.9k) the cumulative total is **$838,076**.
    5. *Classification:* $175,000 is the upfront acquisition fee; $775k+ is the cumulative multi-year agreement value.
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
