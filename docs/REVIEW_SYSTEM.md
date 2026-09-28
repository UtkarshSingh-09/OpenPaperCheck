# REVIEW_SYSTEM.md — How non-coders verify evidence

Status: draft v1 · Last updated: 2026-09-28

Reviewers never need GitHub. They use a normal website: log in with Google or email, see one card at a time, tap a button, move on.

---

## 1. The most important design decision

**Volunteers do not judge whether a paper is "good" or "fake". They verify whether a piece of machine-generated evidence is correct.**

Why:
- Some checks (does this reference list contain a retracted paper?) are deterministic and belong to code. A human adds nothing there, and asking a volunteer to "judge" it invites guesswork.
- The valuable human work is the part machines get wrong: matching a messy reference string to the right paper, confirming that a record refers to the same paper, reading a notice, deciding whether an odd phrase is genuinely a nonsense substitute.
- Framing tasks as "is this evidence right?" keeps volunteers away from accusing anyone, lowers legal risk, and yields cleaner labels (closed questions with a checkable answer).

So the three buttons stay (Yes / No / Not sure, worded per task) but their meaning is always about the *evidence*.

---

## 2. Task types

| ID | Task | Question on the card | Buttons | Difficulty | Skills needed | Why it exists |
|---|---|---|---|---|---|---|
| T1 `ref_match` | Reference to DOI match | "Is the reference text the same paper as the matched record?" Shows raw reference string and matched title, year, journal | Same paper / Different paper / Not sure | 1 (easy) | Reading | Prevents false "cites a retracted paper" flags |
| T2 `retraction_match` | Retraction record to paper match | "Is this Retraction Watch record about this paper?" Shows record title, journal, dates vs our paper | Same paper / Different paper / Not sure | 2 | Reading | Fixes records with missing or conflicting DOIs |
| T3 `notice_reason` | Notice supports reason | "Does the retraction notice support the listed reason tag?" Shows link to open notice and RW reason tags | Supported / Not supported / Not sure | 3 | Reading a notice; open-access notices only | Quality-checks reason tags for the dataset |
| T4 `tortured_phrase` | Unusual phrase check | "In this sentence, is the phrase an odd substitute for the standard term?" Shows snippet, phrase, standard term | Yes, odd substitute / No, normal usage / Not sure | 2–3 (field-routed) | Field knowledge helps | Human confirmation is mandatory before any public use |
| T5 `evidence_check` | Card sentence vs source | "Does this sentence match its cited source?" One sentence + source snippet | Accurate / Not accurate / Not sure | 3 | Careful reading | Catches LLM errors before publication |
| T6 `citation_context` (later, v0.4) | Does the citing sentence acknowledge the retraction? | Needs full text | Acknowledges / Does not / Not sure | 4 | Reading in context | Distinguishes careless from careful citation |

Verdict enum in DB is `yes | no | unsure`; the UI maps first button = yes, second = no.

---

## 3. What a reviewer sees (screens)

### 3.1 Login
Two buttons: **Continue with Google**, **Email me a link**. One line: "We store your email only to log you in. Your display name is public; choose a pseudonym."

### 3.2 First run: 2-minute tutorial
Shown once; can be replayed. Uses **3 gold tasks** with instant feedback:
1. T1 easy, obvious "Same paper" (title and year match, formatting differs).
2. T1 with a near-miss: same title words, different year and journal, correct answer "Different paper".
3. T4 example with a clear normal usage in context: correct answer "No, normal usage".
After each answer: green/red banner + one-sentence explanation. After three: "You're ready. Start with easy tasks."
Completion flag `tutorial_done_at` unlocks the queue. Tutorial results are not counted as real reviews.

### 3.3 The card (mobile layout, 360 px)
```
┌───────────────────────────────┐
│ Task 12 of today   ●●●○○      │  progress dots (session goal)
├───────────────────────────────┤
│ Is this the same paper?       │  question, plain language, 1 sentence
│                               │
│ Reference text                │
│ “Smith J. 2018. Effects of…”  │
│                               │
│ Matched record                │
│ Title • Journal • Year        │
│ [Open source page ↗]          │  external link opens new tab
├───────────────────────────────┤
│ [ Same paper ]                │  48px+ buttons
│ [ Different paper ]           │
│ [ Not sure ]                  │
│ + Add a short note (optional) │
└───────────────────────────────┘
```
Rules:
- One task per screen, no scrolling for the core content; details behind "Why am I seeing this?" (a 2-line explanation).
- After a tap: a 1.5 s "Saved" toast with **Undo**; then the next card.
- "Skip" exists but is limited (does not count against the reviewer, but logs frequency; too many skips on one type informs task design).
- Keyboard shortcuts on desktop: 1/2/3 for buttons.
- All text translatable; right-to-left layout supported by design tokens (test with one RTL language).

### 3.4 After each task
Never show other reviewers' votes for the same task. Show gold feedback only on gold tasks ("This one had a known answer: …").

### 3.5 Progress page (`/me`)
- "You reviewed 20 papers this week" (count).
- Your accuracy on known-answer tasks (private, shown as a range once ≥ 10 gold seen).
- Level and what unlocks next.
- Optional opt-in **public** display name on the leaderboard.
- Export or delete my data buttons.

### 3.6 Leaderboard: design so it does not corrupt quality
Ranking by *volume* rewards rushing. Therefore:
- Rank by **weekly accuracy-weighted contribution** (= reviews × gold accuracy, only if accuracy ≥ 80%), not raw counts.
- Show **teams/classes** (e.g., "Biology 101 group") instead of only individuals, to encourage classroom adoption.
- Opt-in only; pseudonymous.
- Streaks capped and never lost harshly (a "rest day" token) to avoid pressure.
- Minimum time on card (see anti-abuse) so speed-tapping does not count.

---

## 4. Levels

| Level | How to reach | Tasks unlocked | Notes |
|---|---|---|---|
| 1 Newcomer | Finish tutorial | T1 | Goal: 30 reviews with ≥ 85% gold accuracy |
| 2 Reviewer | 30 T1 reviews, gold accuracy ≥ 85%, agreement with consensus ≥ 80% | T2, T4 (field-matched) | |
| 3 Trusted | 150 reviews total, gold ≥ 88%, agreement ≥ 85% over last 100 | T3, T5 | Reviews here can be weighted higher later |
| 4 Senior | Invitation by maintainers; ≥ 500 reviews; gold ≥ 90% | Escalations, tutorial authoring, gold authoring | Not a job title; a responsibility |

Demotion: accuracy rolling over last 50 gold tasks below the floor for the level → move down one level, with a friendly message and a refresher. Suspension only for abuse (see section 7).

---

## 5. Task generation and routing

### 5.1 Where tasks come from
- **T1:** every reference with a fuzzy match (< 0.98 confidence) that would flip a public signal; plus a random 2% audit sample of deposited-DOI matches to measure matcher precision.
- **T2:** RW records with no DOI, or with a DOI conflicting with title/journal.
- **T3:** RW records with open-access notices; sample by reason tag to balance the dataset.
- **T4:** every S-020 hit.
- **T5:** every generated evidence-card sentence.
- **Gold:** ~10% of tasks in the queue are gold (see 6).

### 5.2 Queue size
Keep between 200 and 2,000 open tasks. If the queue is short, raise generation; if it is long, throttle generation and prioritise tasks affecting public pages.

### 5.3 Routing
Order by: matches reviewer's declared field → higher priority (affects a page many people view) → older first. Never route the same task twice to the same reviewer. Language preference respected for T3/T4/T5 where text is language-specific.

### 5.4 Leases
A task is leased to a reviewer for 30 minutes; if not answered it returns to the pool.

---

## 6. Gold tasks (known answers)

- Created by senior reviewers or maintainers from unambiguous cases, each with a one-sentence explanation.
- About 10% of a reviewer's tasks; at least 1 in the first 10 tasks.
- Used to: (a) measure accuracy, (b) decide level changes, (c) detect spammers, (d) train new reviewers.
- Rotate: a gold task is shown at most once per reviewer, retired after 200 exposures.
- Log which gold tasks most people miss; those often reveal confusing wording. Fix the wording.

---

## 7. Anti-abuse and quality controls

| Threat | Control |
|---|---|
| Random tapping | Minimum time per task (e.g., 4 s for T1, 15 s for T3); reviews under the minimum are stored but excluded and counted |
| Always-the-same answer | Detect answer-pattern entropy; flag reviewers who answer > 90% one way on mixed tasks |
| Sock puppets | Turnstile at signup, per-IP and per-email limits, disposable-email blocklist, duplicate device/IP-hash heuristics; same-IP votes on the same task count as one |
| Coordinated brigading on a paper | Random assignment (no browsing of papers); cap reviews per reviewer per paper; anomaly alert |
| Reviewer knows the authors (conflict) | "I have a conflict with this task" button (skips, logged); optional profile note; T1/T2 show minimal personal info |
| Data scraping of queue | Auth required; rate limits; only one active task per reviewer |
| Harassment in notes | Notes ≤ 500 chars, never shown publicly, moderator-only; profanity filter; notes about individuals trigger review |
| Leaked gold answers | Rotation; new gold tasks monthly |

---

## 8. Consensus and escalation
- 3 independent reviewers per task. Majority of the *same* verdict among non-"unsure" votes decides (details in `DATABASE.md` section 6).
- Disagreement or 2+ "unsure" → senior queue (Level 4). Senior decision is labelled `senior_override`.
- If unresolved, task is withdrawn, never released as a label.
- Publish per-task-type agreement (Fleiss' kappa / Krippendorff's alpha) in every release.
- If a task type's agreement is poor, **change the task**, not the reviewers: shorten, add examples, split into two questions.

---

## 9. Recruiting the first 20 reviewers (Week 6)

| Group | How to reach | What to offer |
|---|---|---|
| Classmates in biology, medicine, engineering | Ask a professor for 10 minutes in class; QR code to the tutorial | "Research integrity" mini-activity; certificate of contribution |
| PhD and research students | Department mailing lists; lab meetings | Credit in the dataset paper's acknowledgements (opt-in) |
| Librarians | Local and international library networks; research-integrity librarians | Tool they can use in information-literacy sessions |
| Research-integrity communities | Forums and mailing lists of the integrity community | Transparent methods and open data |
| Wikipedia / open-science volunteers | Open-science Slack/Discord communities | Ready-made "micro-task" workflow |

Rules: never pay per task (perverse incentives); recognise contributors publicly if they opt in; be honest that the project is new.

---

## 10. Reviewer wellbeing and accessibility
- Tasks show titles and short evidence only; no graphic content. Still, retraction reasons can mention misconduct; add a content note and let people skip topics.
- Session goals are soft ("5 tasks, then a break").
- WCAG AA contrast; screen-reader labels; keyboard navigation; text resizing; no colour-only feedback.
- Low-bandwidth mode (no images, minimal JS) for phones on slow networks.

---

## 11. Reviewer code of conduct (short version shown at signup)
1. Review the evidence, not the people.
2. If you are not sure, press **Not sure**. That is a good answer.
3. Do not discuss specific tasks publicly while they are open.
4. Do not try to identify or contact authors about tasks.
5. Notes are private; keep them factual.
6. Report anything that feels wrong.

---

## 12. Metrics for this subsystem
| Metric | Target by launch |
|---|---|
| Tutorial completion | ≥ 70% of signups |
| Median time per T1 task | 20–60 s |
| Gold accuracy (T1) | ≥ 88% median |
| Agreement (T1) alpha | ≥ 0.75 |
| Weekly active reviewers | ≥ 20 |
| 7-day return rate | ≥ 30% |
| Tasks decided per week | ≥ 300 |
| Escalation rate | ≤ 15% |

---

## 13. Paper prototype test (Week 0)
Before writing any UI: draw the T1 card on paper (or Figma), show it to 3 people who have never seen the project, ask them to answer 10 sample cards aloud. Record: where they hesitated, what they misread, and whether "Not sure" was used sensibly. Write findings in `docs/research/2026-xx-paper-prototype.md`.

---

## 14. Tutorial script (draft copy)

**Screen 0:** "You'll check machine-found evidence about scientific papers. You will not decide whether a paper is good or bad. Ready? (2 minutes)"
**Screen 1 (T1 gold):** "A computer thinks these two are the same paper. Are they?" → explanation: "The title and year match. Different formatting is fine."
**Screen 2 (T1 near-miss):** → explanation: "Similar words, but different year and journal. These are different papers."
**Screen 3 (T4 gold):** "Is the underlined phrase an odd substitute for a standard term?" → explanation: "In this field this is the normal term, so the answer is No."
**Screen 4:** "It's fine to press Not sure. We'd rather have an honest 'not sure' than a guess."
**Screen 5:** "You're ready."
