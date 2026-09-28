# SIGNALS_AND_ML.md — What we compute, how we word it, how we test it

Status: draft v1 · Last updated: 2026-09-28

A **signal** is a small, explainable fact about a paper with evidence attached. A signal is **not** a verdict about the paper or its authors. Signals feed (a) the public page when they are external facts, and (b) the review queue when they need a human to confirm the evidence.

---

## 1. Fairness and safety rules (mandatory, tested in CI)

1. **Never use author names, author country, institution or nationality as a feature, a filter, a sort key, or a grouping key.** Not in rules, not in ML, not in analytics.
2. **Never rank or score people.** No author pages, no author leaderboards.
3. **Journal and publisher context is shown as context**, e.g. "This journal has N retractions listed by Retraction Watch with reason 'Paper Mill'". It is never worded as blame and is never used as a per-paper penalty in v1.
4. **A signal that is not an external fact stays internal** until ETHICS moderation is live and a signal-specific review has passed.
5. **Words that are banned in public text and LLM output:** fake, fraud, fabricated, scam, cheat, guilty, misconduct (except when quoting an authority's own notice, in quotation with attribution), paper mill (only as a verbatim Retraction Watch reason tag with attribution).
6. **Absence of a flag is not evidence of quality.** No signal ever produces "safe", "trusted" or "verified".
7. **CI check:** a test greps the `signals/` and `ml/` packages for imports or column names matching the deny-list (`author`, `country`, `nationality`, `institution`, `affiliation`, `name`) and fails the build. A second test asserts the ingest allow-list.

---

## 2. Signal catalogue (v1, rules only)

Each signal has: ID, definition, inputs, output, public?, wording, false-positive risks, tests.

### S-001 `retracted`
- **Definition:** an external source lists a retraction notice for this DOI.
- **Inputs:** `retraction_evidence` (RW and Crossref).
- **Output:** `value_bool`, evidence = list of {source, date, notice url, RW record id, reasons verbatim}.
- **Public:** yes (external fact).
- **Wording:** "Retracted according to Retraction Watch (record #…) and/or Crossref. Reason(s) listed by Retraction Watch: …" Attribution and link required.
- **Risks:** wrong DOI match (mitigated by exact DOI equality; fuzzy matches go to `retraction_match` tasks); reinstated papers (S-003).
- **Tests:** golden set of 20 retracted DOIs → all true; 20 non-retracted → all false; a paper with retraction then reinstatement → false with note.

### S-002 `expression_of_concern`
- **Definition:** a source lists an expression of concern.
- **Public:** yes. **Wording:** "An expression of concern has been recorded (source, date)."
- **Risks:** EoC later resolved; store timeline.

### S-003 `reinstated_or_corrected`
- **Definition:** a correction or reinstatement exists. Shown as timeline context next to S-001/S-002.
- **Public:** yes.

### S-010 `cites_retracted_count`
- **Definition:** number of references whose DOI is in `retracted_dois`. Follows the 3-tier reporting rule: counts references with DOIs checked against retraction data, explicitly notes unstructured references without DOIs, and flags missing/restricted reference deposits.
- **Output:** `value_num` plus list of the retracted references with retraction dates and cited-before vs. cited-after classification.
- **Public:** yes, but only the **count and list** as facts, no threshold language.
- **Wording:** "5 of 55 references with DOIs are listed as retracted (list). 7 references without DOIs were not checked. This is context, not a judgement of the paper."

### S-011 `cites_retracted_share`
- **Definition:** S-010 divided by references with DOIs. Also report `refs_with_doi / refs_total` so readers see coverage.
- **Public:** internal in v0.1; public when the coverage note is designed.

### S-012 `cites_after_retraction_count`
- **Definition:** count of references that were **already retracted when this paper was published** (citing paper date later than retraction date).
- **Why:** citing a paper that was retracted afterwards is normal and not the citing authors' fault. Citing something already retracted, without acknowledging it, is a stronger context signal.
- **Public:** internal until `citation_context` review exists (v0.4). Full-text context is needed to know whether the citation acknowledged the retraction.
- **Risks:** publication date vs online-first date differences; use the earliest date available and state it.

### S-020 `tortured_phrase_hits`
- **Definition:** title/abstract contains one or more phrases from the fingerprint list.
- **Algorithm:** lowercase, normalise whitespace and hyphens, tokenise; match phrases as **whole-word token sequences** (not substring). Skip matches inside quotation marks or when the paper is itself about tortured phrases (title contains "tortured phrase(s)", "paper mill", "fingerprint"). Record `phrase`, `expected_term`, `snippet` (max 200 chars), `field_hint`.
- **Output:** list of hits; value_num = number of distinct fingerprints hit.
- **Public:** **no.** Internal, feeds `tortured_phrase` review tasks. After consensus confirms a hit, the page may show "Volunteer reviewers agreed this phrase is an unusual substitute for '<expected term>'" with the snippet, and only once ETHICS moderation is live.
- **Risks:** legitimate non-native English usage, quoted material, homonyms in other fields. Human confirmation is mandatory.
- **Tests:** unit tests with positive, negative, quoted and meta-paper examples; snapshot test of the matcher against a small hand-labelled set.

### S-030 `journal_context_rw_reasons`
- **Definition:** for the paper's journal, the count of RW records and the share carrying each reason tag (e.g., a tag containing "Paper Mill").
- **Public:** as context on the paper page under "About this journal in Retraction Watch data" with a denominator and a date range; **never** as a paper-level flag.
- **Risks:** large journals have more retractions in absolute numbers. Always show per-10,000-papers rate only if the denominator is reliable (OpenAlex counts); otherwise show counts with the caveat.

### S-040 `data_coverage`
- **Definition:** which sources answered, whether the reference list was available, share of references with DOI.
- **Public:** yes. This is how "No flags found" stays honest.

### Candidate signals for later (not built now)
- Duplicate/near-duplicate title within the corpus.
- Unusual reference patterns (e.g., high self-citation) — needs care to avoid targeting individuals; would be journal-level only.
- Missing or dead data-availability links.
- Cell-line or reagent identity problems (needs specialist lists).
Each candidate needs an ADR and an ETHICS review before it is coded.

---

## 3. Public label logic

| Public state | Condition | Text shown |
|---|---|---|
| `retracted_external` | S-001 true from RW or Crossref | "Retracted (per Retraction Watch / Crossref)" + reasons verbatim + links |
| `needs_review` | Any public signal true (S-002, S-010 above display threshold, etc.) | "Some external facts are worth checking" + list |
| `no_flags_found` | Sources answered, no public signal | "No flags found in the sources we check (list, date). This is not an endorsement." |
| `insufficient_data` | DOI unknown or metadata/reference data unavailable | "We could not check this paper fully: <what was missing>" |

There is **no "Confirmed" label** from us. "Confirmed" would suggest we investigated. The strongest state is `retracted_external`, which credits the authority. (This replaces the first plan's "Confirmed".)

---

## 4. Reference matching (needed for S-010/S-012 accuracy)

Problem: many reference entries lack a DOI. Wrong matches create false accusations.

Pipeline:
1. Use deposited DOI when present (`match_method = 'deposited_doi'`, confidence 1.0).
2. Otherwise, fuzzy match on normalised title + year + first-page + journal against `papers` and Crossref query results, only if title similarity ≥ 0.92 and year equal. Store `match_confidence`.
3. Matches below 0.98 that would change a public signal (i.e., match is to a retracted paper) create `ref_match` review tasks. The signal counts the reference only after human confirmation, or shows it as "possible match, awaiting verification" internally.
4. Track precision from `ref_match` consensus; publish it.

---

## 5. Evidence-card agent (recap of constraints)

See `TECH_STACK.md` section 7. Signals are the *only* facts the agent may use, plus metadata from `papers`. The verifier code, not the model, decides whether a card may enter review.

---

## 6. ML plan (v0.4)

### 6.1 What we predict
"Similarity to previously retracted papers whose RW reasons include paper-mill-related tags" — reported as a **similarity score**, not a fake probability. Public wording, if ever shown: "Text is similar to papers previously retracted for reasons Retraction Watch tags as X." Never shown on the paper page in v1.

### 6.2 Dataset construction
- Positives: papers with a retraction whose reason tags match a defined list (stored in `ml/config/reason_groups.yaml`, reviewed and versioned).
- Negatives: papers **not** retracted, sampled to match positives on journal, year and subject (matched sampling) to avoid a model that just learns journal or year.
- Ratio: report results at natural prevalence and at balanced sampling; do not only report balanced.
- Text: title + abstract fetched by the researcher (not redistributed).

### 6.3 Leakage checklist (must pass before any number is published)
- [ ] Remove tokens like "retracted", "retraction", "withdrawn", "notice", "erratum" from text.
- [ ] Remove publisher boilerplate and DOIs from text.
- [ ] Time split: train ≤ year T, test > T; also journal-held-out split.
- [ ] Baselines: journal-only, year-only, title-length-only. The model must beat them.
- [ ] Inspect top 100 positive features by hand; delete any that are bookkeeping tokens.
- [ ] Check duplicates between train and test (near-duplicate titles).
- [ ] Label circularity: are labels derived from the same source as features (e.g., RW-derived features used to predict RW labels)? Remove.
- [ ] Report per-subject performance to spot subject shortcuts.

### 6.4 Metrics
PR-AUC (primary, prevalence is low), precision@k, recall@k, calibration curve + expected calibration error, confusion matrix at a stated threshold, per-journal and per-subject breakdown, bootstrap confidence intervals.

### 6.5 Fairness audit for ML
Because we have no author or country features, audit for proxies: language-quality features may correlate with non-native English writing. Report performance on (a) papers with tortured-phrase hits vs. without, (b) subjects with different English-writing norms. State limits in the model card: "The model may flag non-native English writing. It must not be used to judge authors."

### 6.6 Benchmark
- `benchmark/` folder: frozen test split (hashes only for text; IDs list), evaluation script, submission JSON schema, leaderboard generator.
- Rules: no external labels from RW at test time; no author features; document data sources; submissions via pull request.
- Release with model card and dataset card (see `WORKFLOW.md` release section).

---

## 6.7 Model card skeleton (`ml/MODEL_CARD.md`)
Intended use · Out-of-scope use (judging people, automatic rejection) · Training data and dates · Evaluation data and splits · Metrics with intervals · Known failure modes · Fairness audit · Update policy · Contact.

---

## 7. Testing signals

| Test | Purpose |
|---|---|
| Golden DOI set (`tests/fixtures/golden_dois.json`) | Known retracted and non-retracted; regression guard |
| Property tests | DOI normaliser idempotent; consensus permutation-invariant |
| Snapshot tests | Wording templates never contain banned words |
| Contract tests | Real recorded Crossref/OpenAlex JSON parse correctly |
| Deny-list test | No author/country/institution fields reach signals or ML |
| Mutation spot-check | Flip a retraction date; S-012 must change |

---

## 8. Signal change process
1. Open an issue with the "signal proposal" template: definition, inputs, evidence shape, public or internal, wording, risks, test plan.
2. Discuss in GitHub Discussions for at least 7 days.
3. ADR recorded; ETHICS owner signs off if public.
4. Implement with tests; bump `signal_definitions.version`.
5. Add to the release notes.
