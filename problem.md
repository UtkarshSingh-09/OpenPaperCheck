# problem.md — What problem OpenPaperCheck solves (and what it does not)

Status: draft v1 · Last updated: 2026-09-28
Facts below come from sources checked on 2026-09-28 (listed at the end). Numbers move; verify before quoting.

---

## 1. Problem statement (one paragraph)
Retracted and problematic papers keep circulating: readers cite them, students learn from them, and new papers build on them. The information that a paper has been retracted exists, but it is scattered across publisher pages, Retraction Watch, Crossref, and tools that require technical skill or a publisher contract. A student, librarian or busy researcher who has a DOI cannot easily get a plain, sourced answer to "has anything been recorded against this paper, and does it lean on retracted work?" Meanwhile, the labelled data needed to build better open detection tools is scarce, partly because verifying evidence takes human time that no open project has organised.

## 2. Who has the problem

| Persona | Situation | Pain today | What they need from us |
|---|---|---|---|
| P1 Student / early researcher | Reading or citing a paper for an assignment or thesis | Doesn't know retractions exist; no habit of checking | Paste DOI → clear answer in seconds, on a phone |
| P2 Librarian / information-literacy teacher | Teaching source evaluation | Tools are fragmented; no teaching-friendly one | A tool for demos, with explanations and no accusations |
| P3 Researcher checking a reference list | Before submitting or citing | Manual checks, reference by reference | Reference-list check ("N of M references are listed as retracted") |
| P4 Volunteer reviewer | Wants to help research integrity in spare minutes | No low-barrier way to contribute | 2-minute tasks, no jargon, no GitHub |
| P5 Developer / data scientist | Builds detection tools | Few open labelled datasets with known quality | CC-BY labels with measured agreement |
| P6 Author / publisher | Their paper appears on a page | Fear of unfair labels; no clear route to correct errors | Attribution to sources, an appeal path, correction speed |
| P7 Journalist / science communicator (secondary) | Checking claims | Needs quick, citable evidence | Stable links to sources and timestamps |

## 3. Evidence that the problem is real (as reported in sources)
- The Retraction Watch database, acquired by Crossref in 2023 and published openly, held roughly 43k records then; combined with Crossref's own retraction metadata about 50k retractions overall. It is updated on working days.
- Retraction data do not always propagate everywhere: one 2026 user report describes a paper marked retracted by its publisher months before the RW CSV showed it, and reference managers that rely on RW alone would miss such cases.
- Integrity tooling exists mainly on the **publisher side**: the STM Integrity Hub runs about 20 detection tools, integrating third-party services such as Clear Skies and PubPeer, used by publishers on submissions. These are not reader-facing and are largely closed.
- The Problematic Paper Screener scans on the order of 130 million publications weekly and lists over 5,000 tortured-phrase fingerprints, with human assessment recorded on PubPeer. It shows that *machine detection + volunteer verification* works, but it is not an open labelled dataset with published agreement statistics.
- Volunteer investigation communities already exist around PubPeer; the missing piece is an organised, low-barrier, quality-controlled contribution path for people who are not specialists.
- Post-2025 changes to data access (OpenAlex keys and pricing; Crossref rate-limit revisions) show that open infrastructure needs careful, cost-aware design.

## 4. Gap analysis (existing tools vs OpenPaperCheck)

| Tool | Audience | Open? | What it does | What it does not do (our opening) |
|---|---|---|---|---|
| Retraction Watch database / Crossref | Everyone (data) | Open data | Lists retractions, corrections, EoCs, reasons | Not a reader-facing reference-list check; no volunteer verification |
| Zotero retraction alerts | Zotero users | Open source | Flags retracted items in a library | Depends on RW data only; no explanation of references; only within Zotero |
| Problematic Paper Screener | Sleuths, publishers | Public site, data rights per agreements | Weekly detectors (tortured phrases, etc.) | Not a general DOI check; no open labelled dataset with agreement stats |
| STM Integrity Hub | Publishers | Closed, membership | Multi-signal screening on submissions | Not for readers; not open |
| Clear Skies Papermill Alarm | Publishers | Commercial | Traffic-light risk for submissions | Closed; not open data |
| PubPeer | Community | Site open; automated access restricted | Post-publication comments | Not structured labels; terms restrict bulk use |
| **OpenPaperCheck** | Readers + volunteers + developers | Open code and open labels | DOI → sourced facts; reference-list check; volunteer verification; CC-BY dataset | Not a fraud detector; not a judge of people |

**Our niche in one line:** a *reader-facing, open, evidence-first* DOI checker whose *human verification loop* produces an *open labelled dataset* with published agreement statistics.

## 5. Goals (measurable)
| Goal | Measure | By |
|---|---|---|
| G0 CLI user gets an offline answer in under 2 seconds | `opc check <doi>` execution time using local SQLite snapshot | Week 2 |
| G1 A web reader gets a sourced answer in under 3 seconds (cached) | p95 latency, task-completion in user tests | Week 4 |
| G2 Accuracy of retraction status matches sources | 100% match on golden DOI set; weekly OpenAlex-vs-RW mismatch report | Week 4 |
| G3 Reference check is trustworthy | Precision of fuzzy matches ≥ 95% after volunteer verification; 3-tier honesty rule | Week 9 |
| G4 Volunteers can contribute in ≤ 2 minutes per task | Median time per T1 task 20–60 s; tutorial completion ≥ 70% | Week 6–8 |
| G5 Label quality is measurable | Krippendorff's alpha ≥ 0.75 for T1; published per release | Week 12 |
| G6 Open dataset released | v0.1.0 on Hugging Face + Zenodo DOI, with dataset card | Week 12 |
| G7 Community forms | ≥ 20 weekly active reviewers; ≥ 5 external contributors within 3 months of launch | Week 12 + 12 |

## 6. Non-goals (what we will not do)
- Decide whether a paper is fake, fraudulent or "good".
- Rank, score or profile authors, institutions or countries.
- Detect image manipulation (specialised commercial tools exist).
- Replace peer review or editorial investigations.
- Sell data, run ads, or offer paid tiers.
- Scrape sources whose terms forbid it.
- Publish anonymous accusations.

## 7. Key assumptions and how to test them (hypotheses)

| # | Hypothesis | Risk if false | Cheapest test | When | Pass criterion |
|---|---|---|---|---|---|
| H1 | Readers want a DOI-paste check and will use it | No users | 10 people (students, librarians) try a paper prototype/skeleton; observe | Week 0–4 | ≥ 7 of 10 complete a check unaided and say they'd use it again |
| H2 | Non-expert volunteers can verify T1 tasks reliably | Labels are noise | Pilot 10 volunteers × 30 tasks with 20 gold | Week 6 | Gold accuracy ≥ 85%; alpha ≥ 0.7 |
| H3 | Fuzzy reference matching produces many wrong matches without human help | We over-flag | Sample 200 fuzzy matches, hand-check | Week 5 | Measure precision; if < 95% keep humans in the loop (design already does) |
| H4 | Enough volunteers exist to keep the queue moving | Queue stalls | Recruit via 3 classes and 2 online communities | Week 6–8 | ≥ 20 reviewers, ≥ 300 tasks/week |
| H5 | Retraction data from RW + Crossref suffices for a useful v0.1 | Product feels empty | Check 50 random DOIs in a topic area; how many show anything? | Week 3 | Users still find value via reference-check and coverage notes |
| H6 | Authors can be treated fairly with attribute-not-accuse wording | Legal/ethical harm | Mentor + advisor review; test wording with 3 authors | Week 9–10 | No reviewer flags wording as accusatory |
| H7 | Tortured-phrase confirmations by volunteers are consistent | Signal unusable | Pilot 100 hits, 3 reviewers each | Week 8 | Alpha ≥ 0.6 (if lower, redesign or drop) |
| H8 | A solo part-time maintainer can run this | Burnout | Track hours weekly | Continuous | ≤ 15 h/week average; cut list used when slipping |

## 8. Risks specific to the problem
| Risk | Why it matters | Mitigation |
|---|---|---|
| A wrong or misread flag harms a real person | Reputation, legal exposure | External facts only; attribution; appeals; hide-in-1-hour drill |
| Users read "No flags found" as "safe" | False reassurance | Wording, `insufficient_data` state, coverage notes |
| Source changes (terms, pricing, schema) | Product breaks | Local data, caching, license log, quarterly review |
| Duplication of existing work | Wasted effort | Position as complementary; contact PPS; open data |
| Volunteer fatigue | Queue stalls | Small tasks, soft goals, classroom adoption, recognition |
| Label circularity | ML learns retraction words | Leakage checklist; time and journal splits |
| Maintainer burnout | Project dies | Small scope, governance, co-maintainers early |

## 9. Success looks like (12 months)
- Librarians use it in teaching sessions.
- A paper on the dataset is cited by an integrity or scientometrics study.
- At least three external contributors have merged pull requests.
- Agreement statistics improve release over release.
- No unresolved wrong-flag incident older than 14 days.

## 10. Open research questions (to study, not to assume)
1. Which task types do non-experts do best, and how does field-matching change accuracy?
2. What is the false-match rate of reference matching per publisher and per year?
3. How often do RW and Crossref disagree, and in which direction?
4. Does showing evidence in plain language change how readers cite retracted papers? (User study, later.)

## 11. Sources checked (2026-09-28)
- Crossref documentation and blog posts on the Retraction Watch acquisition, CSV in GitLab (updated on working days), inclusion in the REST API, metadata licensing (CC0 except abstracts), REST API rate-limit changes.
- OpenAlex announcements and docs on mandatory API keys (from 2026-02-13) and usage-based pricing; free CC0 snapshot.
- PubPeer terms of service and FAQ (automated access restrictions; API by request).
- Problematic Paper Screener descriptions (Cabanac et al.; The Conversation; Science news on tortured acronyms).
- STM Integrity Hub pages and articles (Science Editor; Scholarly Kitchen; Chemistry World).
- Zotero forum discussion (2026) about RW vs Crossref retraction propagation.
- arXiv analysis of retractions in OpenAlex (2024): data-quality issues in `is_retracted`.
- Original plan's references (Open Food Facts, Common Voice, launch guides, Nature and bioRxiv paper-mill items) — kept as background, **not re-verified** in this pass.
