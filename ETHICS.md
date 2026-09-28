# ETHICS.md — Review, wording, appeals and privacy policy

Status: **DRAFT v0.1 — must be read by a mentor and a legal advisor before any community flag becomes public.**
Last updated: 2026-09-28 · Policy owner: maintainer (until a moderation group exists)
This file is not legal advice. It is the project's own rulebook.

---

## 1. Purpose
OpenPaperCheck helps readers see **external, sourced facts** about a paper and helps volunteers verify machine-found evidence. It exists to make careful reading easier, not to accuse anyone.

## 2. Principles
1. **Evidence over opinion.** Every public statement links to a source and shows when it was checked.
2. **Attribute, don't accuse.** We credit authorities ("according to Retraction Watch") instead of making our own claims.
3. **Retraction is not misconduct.** Many retractions are for honest error or publisher error. We show reasons exactly as the source lists them.
4. **Absence of a flag is not endorsement.**
5. **People are not the subject.** No author profiles, rankings or scores. No use of names, countries or institutions.
6. **Humans decide.** No automated system publishes a judgement.
7. **Fix mistakes fast, in public.** Corrections are logged.
8. **Minimum data.** Collect only what we need; delete on request.
9. **Open by default,** unless openness would harm a person or violate a license.

## 3. What we publish (v0.1–v0.3)

| Allowed publicly | Not allowed publicly |
|---|---|
| Retraction / expression of concern / correction records from external sources, with source links | Any statement that a paper or person is fake, fraudulent, fabricated, a scam, or guilty |
| Count and list of references listed as retracted (facts) | A "fake probability" or "trust score" |
| Data coverage notes ("reference list not available") | Volunteer votes on individual papers (until moderation is live) |
| Journal-level counts from external data as context, with denominators and dates | Author-level or institution-level anything |
| Volunteer-confirmed evidence corrections (e.g., "a matched reference was wrong") | Comments or text from PubPeer (unless permission is granted) |

Community-derived flags (e.g., confirmed tortured phrases) are **not** public until: (a) this policy is reviewed, (b) the appeal process below is operating, (c) a moderator can hide a page within 24 hours.

## 4. Public labels and reference reporting

| Label | Meaning | Never means |
|---|---|---|
| Retracted (per <authority>) | An external authority lists a retraction | That we investigated it |
| Needs review | Some sourced facts are worth a reader's attention (listed) | That the paper is bad |
| No flags found in the sources we check | Our sources list nothing | That the paper is correct, safe or endorsed |
| Could not check fully | Missing data (stated) | Anything about quality |

### 4.1 Truth in reference reporting (no false reassurance)
It is a serious ethical violation to print "0 retracted references" when references were missing, incomplete, or restricted by the publisher. All outputs (CLI and Web) must clearly separate:
1. **References with DOIs checked** against our retraction dataset (with "data as of" date and explicit note if cited before vs. after retraction).
2. **References without DOIs** (unstructured citations that cannot be verified offline).
3. **Missing or restricted bibliographies:** If Crossref returns no references because the publisher restricted or omitted them, the system must display *"References not deposited by publisher"*, never *"0 retracted references"*.

## 5. Wording rules
- Banned words in public text and LLM output: fake, fraud, fabricated, scam, cheat, guilty, and "misconduct" except when quoting a source verbatim with attribution.
- Prefer: "according to", "listed as", "the source records", "this may be worth checking".
- Never name an individual in a flag.
- Every wording template is stored in `signal_definitions.wording_template`, reviewed, and covered by a snapshot test that checks for banned words.
- The LLM agent may only restate evidence items; a code verifier enforces this.

## 6. Appeals and corrections

Anyone (author, publisher, reader) can submit `/appeal` with the DOI and a message. No account needed.

| Step | Target time |
|---|---|
| Automatic acknowledgement | immediately |
| Human acknowledgement | 3 working days |
| Page hidden while under review, if the request credibly claims a factual error | 24 hours after receipt |
| Decision | 14 days |
| Outcome recorded in `appeals`, public changelog entry (without personal data) | on decision |

Possible outcomes: no change (with explanation); data corrected; page hidden; label removed from the next dataset release (`takedowns`). Appeals about **external** facts (e.g., the retraction itself) are redirected to the source (Retraction Watch, publisher, Crossref); we update once the source does.
The appeal contact address is displayed in the footer, in `SECURITY.md` and in `README.md`.

## 7. Privacy and data minimisation

| Data | Purpose | Retention |
|---|---|---|
| Reviewer email | Login only | Until account deletion |
| Display name (pseudonym) | Attribution, leaderboard (opt-in) | Until deletion |
| Review verdicts, notes, timings | Labels and quality checks | Kept; link to the reviewer removed on deletion |
| IP and user agent | Abuse prevention | Stored as salted hashes, 30 days |
| Appeal submitter email | Reply | 3 years after resolution, then scrubbed |

- No advertising, no data sales, no third-party trackers.
- Any analytics must be cookieless and self-hosted.
- Rights: access, export, correction, deletion. Provided by `/me` and by email.
- Privacy law may apply depending on where reviewers live (for example the EU GDPR or India's data-protection law). **Ask the legal advisor** what a small open project must do (privacy notice, lawful basis, breach process). Publish a plain-language privacy notice before public launch.
- Report and handle breaches per `SECURITY.md`; notify affected people promptly.

## 8. Reviewer conduct
See `docs/REVIEW_SYSTEM.md` section 11. Violations: warning → temporary suspension → removal. All actions recorded in `audit_log`.

## 9. Conflicts of interest
- Reviewers can mark a task "I have a conflict".
- Maintainers and moderators recuse themselves from appeals about their own work or employer.
- The project does not accept payment to change, hide or add flags. Ever.

## 10. Use of AI
- LLM output is a draft, verified by code and by humans, and stored with model name and version.
- We disclose on the methodology page which models are used.
- We do not send reviewer personal data to any model.
- Models are never trained on reviewer notes without consent.

## 11. Data releases and licensing
- Code: Apache-2.0. Verified labels: CC-BY 4.0. Upstream sources keep their own licenses; `DATA_LICENSE.md` lists them.
- Releases contain DOIs, labels, agreement statistics, signals — **no abstracts, no reviewer identities, no author fields**.
- A `takedowns` request removes labels from the *next* release and from the live site; already-published versions are marked with a notice in the changelog.

## 12. Moderation and governance
- A moderator can hide a page, remove a label, or suspend a reviewer; each action is logged.
- Decisions that change policy go through a GitHub Discussion and an ADR.
- At least two people (maintainer + one other) must hold moderator rights before community flags go public. Until then, all public output is external facts only.

## 13. Safety review checklist (before enabling any new public signal)
- [ ] Is it an external fact or a community/model judgement?
- [ ] Does it use or correlate with author, country, institution?
- [ ] Wording reviewed, banned-word test passing?
- [ ] False-positive rate measured on a labelled sample?
- [ ] Appeal path tested end to end?
- [ ] Mentor or legal advisor consulted (if community-derived)?
- [ ] Rollback plan (feature flag) ready?

## 14. Review schedule
This policy is re-read every quarter and at every dataset release. Changes are dated at the bottom.

### Change log
- 2026-09-28 — v0.1 draft created.
