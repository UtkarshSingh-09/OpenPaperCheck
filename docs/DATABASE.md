# DATABASE.md — Schema, constraints, and consensus logic

Status: draft v1 for v0.1–v0.3 · Last updated: 2026-09-28
Engine: PostgreSQL. Migrations: Alembic, one migration per PR, never edit an applied migration.
Naming: `snake_case`, plural table names, `id uuid` primary keys unless a natural key is better (DOI).

---

## 1. Design principles

1. **DOI is the natural key for papers**, always stored normalised (lowercase, no URL prefix).
2. **Facts and judgements are separate tables.** Facts come from sources (`retraction_records`). Judgements come from rules or people (`signals`, `reviews`, `consensus_labels`).
3. **Nothing is overwritten silently.** Signals are versioned; consensus labels keep history; audit log records admin actions.
4. **Minimal personal data.** Reviewer email is isolated in `auth_identities`. Everything else uses `user_id`.
5. **No person-level tables about authors.** There is no `authors` table. This is intentional and enforced by the fairness rule.
6. **Every table that ingests external data has `source`, `source_version`, `fetched_at`.**

### 1.1 Storage tiers: Server (PostgreSQL) vs. CLI (SQLite Snapshot)
- **Server Tier (PostgreSQL):** Implements the full transactional schema below via Alembic migrations. Handles paper ingestion, reference graphs, user auth, review tasks leasing, and consensus calculations.
- **CLI Tier (SQLite Snapshot):** The standalone `openpapercheck` package uses Python stdlib `sqlite3` without PostgreSQL or SQLAlchemy. A nightly server job compiles allow-listed retraction records into a compact, read-only SQLite database (`retraction_records.sqlite.gz`, ~5MB compressed) containing:
  - `retraction_records` (subset of allow-listed columns: rw_record_id, original_doi, nature, reasons, retraction_date, original_date).
  - `retracted_dois` (lookup index: `doi`, `first_retraction_date`).
  - `manifest` (`as_of_date`, `schema_version`, `sha256`).
- Benchmark in Week 1 to verify that 50k rows in SQLite with an index on `lower(original_doi)` executes lookups in under 2 ms.

---

## 2. Entity overview

```
papers ──< paper_references
  │
  ├──< retraction_evidence >── retraction_records
  ├──< signals >── signal_definitions
  ├──< review_tasks ──< task_assignments >── users ──< reviews
  │         │                                   │
  │         └── gold_tasks                      └── reviewer_stats
  ├──< consensus_labels ──> dataset_releases
  ├──< evidence_cards
  └──< appeals

ingest_runs   job_runs   audit_log   data_quality_events   takedowns
```

---

## 3. DDL (copy into the first Alembic migrations)

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS citext;

-- Enumerations
CREATE TYPE retraction_nature AS ENUM
  ('retraction','correction','expression_of_concern','reinstatement','other');

CREATE TYPE task_type AS ENUM
  ('ref_match','retraction_match','notice_reason','tortured_phrase','evidence_check');

CREATE TYPE task_status AS ENUM
  ('open','in_review','needs_senior','decided','withdrawn');

CREATE TYPE verdict AS ENUM
  ('yes','no','unsure');   -- meaning is per task type; see REVIEW_SYSTEM.md

CREATE TYPE public_state AS ENUM
  ('no_flags_found','needs_review','retracted_external','insufficient_data');

CREATE TYPE user_role AS ENUM
  ('reviewer','senior_reviewer','moderator','admin');

-- Ingest bookkeeping ---------------------------------------------------------
CREATE TABLE ingest_runs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source        text NOT NULL,                 -- 'rw_csv','crossref','openalex'
  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz,
  status        text NOT NULL DEFAULT 'running' CHECK (status IN ('running','ok','failed','no_change')),
  file_sha256   text,
  source_version text,                         -- git commit hash, API version, etc.
  rows_in       integer, rows_new integer, rows_changed integer, rows_rejected integer,
  message       text
);

-- Papers --------------------------------------------------------------------
CREATE TABLE papers (
  doi              text PRIMARY KEY CHECK (doi = lower(doi) AND doi ~ '^10\.\d{4,9}/\S+$'),
  title            text,
  journal          text,
  publisher        text,
  publication_date date,
  publication_year smallint,
  openalex_id      text UNIQUE,
  pmid             text,
  subject          text,                       -- coarse field, used to route review tasks
  references_source text CHECK (references_source IN ('crossref','openalex','none')),
  reference_count  integer,
  metadata_source  text NOT NULL,
  first_seen_at    timestamptz NOT NULL DEFAULT now(),
  last_fetched_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX papers_title_trgm ON papers USING gin (title gin_trgm_ops);
CREATE INDEX papers_journal_year ON papers (journal, publication_year);

CREATE TABLE paper_references (
  paper_doi        text NOT NULL REFERENCES papers(doi) ON DELETE CASCADE,
  position         integer NOT NULL,
  ref_doi          text CHECK (ref_doi IS NULL OR ref_doi = lower(ref_doi)),
  ref_raw          text,                        -- unstructured reference text as deposited
  source           text NOT NULL,
  match_method     text,                        -- 'deposited_doi','fuzzy','human'
  match_confidence numeric(4,3),
  human_verified   boolean NOT NULL DEFAULT false,
  PRIMARY KEY (paper_doi, position)
);
CREATE INDEX paper_references_ref_doi ON paper_references (ref_doi) WHERE ref_doi IS NOT NULL;

-- Retraction data -----------------------------------------------------------
CREATE TABLE retraction_records (
  rw_record_id      bigint PRIMARY KEY,         -- Retraction Watch Record ID
  original_doi      text,                        -- may be NULL (no DOI in source)
  retraction_doi    text,
  original_pmid     text,
  retraction_pmid   text,
  title             text,
  journal           text,
  publisher         text,
  subject           text,
  nature            retraction_nature NOT NULL,
  reasons           text[] NOT NULL DEFAULT '{}',-- parsed, verbatim tags
  retraction_date   date,
  original_date     date,
  notice_urls       text[] NOT NULL DEFAULT '{}',
  paywalled         boolean,
  notes             text,                        -- internal only until reviewed
  ingest_run_id     uuid NOT NULL REFERENCES ingest_runs(id),
  updated_at        timestamptz NOT NULL DEFAULT now()
  -- NOTE: no author, institution or country columns. By design.
);
CREATE INDEX rr_original_doi ON retraction_records (lower(original_doi));
CREATE INDEX rr_nature ON retraction_records (nature);

-- Each source's verdict about a paper, so disagreements stay visible
CREATE TABLE retraction_evidence (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_doi     text NOT NULL REFERENCES papers(doi) ON DELETE CASCADE,
  source        text NOT NULL,                  -- 'retraction_watch','crossref','openalex'
  nature        retraction_nature NOT NULL,
  event_date    date,
  url           text,
  rw_record_id  bigint REFERENCES retraction_records(rw_record_id),
  raw           jsonb,                          -- allow-listed fields only
  fetched_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (paper_doi, source, nature, event_date)
);

-- Signals -------------------------------------------------------------------
CREATE TABLE signal_definitions (
  key           text PRIMARY KEY,               -- 'S-001-retracted', etc.
  version       integer NOT NULL,
  description   text NOT NULL,
  public        boolean NOT NULL DEFAULT false, -- may it appear on public pages?
  wording_template text,                        -- reviewed wording, see ETHICS.md
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE signals (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_doi     text NOT NULL REFERENCES papers(doi) ON DELETE CASCADE,
  signal_key    text NOT NULL REFERENCES signal_definitions(key),
  signal_version integer NOT NULL,
  value_bool    boolean,
  value_num     numeric,
  value_text    text,
  evidence      jsonb NOT NULL,                 -- list of {evidence_id, source, url, fact}
  computed_at   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (paper_doi, signal_key, signal_version)
);
CREATE INDEX signals_key_value ON signals (signal_key, value_bool);

-- Users ---------------------------------------------------------------------
CREATE TABLE users (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name  text NOT NULL CHECK (char_length(display_name) BETWEEN 3 AND 30),
  role          user_role NOT NULL DEFAULT 'reviewer',
  level         smallint NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 4),
  languages     text[] NOT NULL DEFAULT '{en}',
  fields        text[] NOT NULL DEFAULT '{}',   -- self-declared fields of study, optional
  tutorial_done_at timestamptz,
  conflict_note text,                           -- optional self-declared COI (free text)
  status        text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','deleted')),
  joined_at     timestamptz NOT NULL DEFAULT now(),
  last_active_at timestamptz
);
CREATE UNIQUE INDEX users_display_name_ci ON users (lower(display_name));

CREATE TABLE auth_identities (                 -- the ONLY place email lives
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider      text NOT NULL CHECK (provider IN ('google','email')),
  provider_subject text,                        -- Google 'sub'
  email         citext NOT NULL,
  email_verified_at timestamptz,
  UNIQUE (provider, provider_subject),
  UNIQUE (email)
);

CREATE TABLE sessions (
  id_hash       bytea PRIMARY KEY,              -- sha256 of cookie value
  user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at    timestamptz NOT NULL DEFAULT now(),
  expires_at    timestamptz NOT NULL,
  ip_hash       bytea, ua_hash bytea
);

-- Review tasks --------------------------------------------------------------
CREATE TABLE review_tasks (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_doi     text NOT NULL REFERENCES papers(doi) ON DELETE CASCADE,
  task_type     task_type NOT NULL,
  payload       jsonb NOT NULL,                 -- exactly what the card shows
  payload_hash  bytea NOT NULL,                 -- dedupe identical tasks
  difficulty    smallint NOT NULL DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 4),
  subject       text,
  language      text NOT NULL DEFAULT 'en',
  status        task_status NOT NULL DEFAULT 'open',
  required_reviews smallint NOT NULL DEFAULT 3,
  priority      integer NOT NULL DEFAULT 0,
  is_gold       boolean NOT NULL DEFAULT false,
  created_at    timestamptz NOT NULL DEFAULT now(),
  decided_at    timestamptz,
  UNIQUE (task_type, payload_hash)
);
CREATE INDEX review_tasks_queue ON review_tasks (status, difficulty, priority DESC, created_at);

CREATE TABLE gold_tasks (
  task_id       uuid PRIMARY KEY REFERENCES review_tasks(id) ON DELETE CASCADE,
  correct_verdict verdict NOT NULL,
  explanation   text NOT NULL,                  -- shown after answering in tutorial
  created_by    uuid REFERENCES users(id),
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE task_assignments (                -- enforces independence and no repeats
  task_id       uuid NOT NULL REFERENCES review_tasks(id) ON DELETE CASCADE,
  reviewer_id   uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  assigned_at   timestamptz NOT NULL DEFAULT now(),
  expires_at    timestamptz NOT NULL,           -- lease; e.g. 30 minutes
  status        text NOT NULL DEFAULT 'assigned' CHECK (status IN ('assigned','done','expired','skipped')),
  PRIMARY KEY (task_id, reviewer_id)
);

CREATE TABLE reviews (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id       uuid NOT NULL REFERENCES review_tasks(id) ON DELETE CASCADE,
  reviewer_id   uuid REFERENCES users(id) ON DELETE SET NULL, -- NULL after account deletion
  verdict       verdict NOT NULL,
  note          text CHECK (note IS NULL OR char_length(note) <= 500),
  duration_ms   integer CHECK (duration_ms >= 0),
  reviewer_level_at_time smallint NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (task_id, reviewer_id)
);

CREATE TABLE reviewer_stats (
  user_id       uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  reviews_total integer NOT NULL DEFAULT 0,
  gold_seen     integer NOT NULL DEFAULT 0,
  gold_correct  integer NOT NULL DEFAULT 0,
  agree_with_consensus integer NOT NULL DEFAULT 0,
  decided_seen  integer NOT NULL DEFAULT 0,
  weekly_count  integer NOT NULL DEFAULT 0,
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- Consensus and releases ------------------------------------------------------
CREATE TABLE consensus_labels (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id       uuid NOT NULL REFERENCES review_tasks(id),
  paper_doi     text NOT NULL,
  task_type     task_type NOT NULL,
  label         verdict NOT NULL,
  n_reviews     smallint NOT NULL,
  n_agree       smallint NOT NULL,
  agreement     numeric(4,3) NOT NULL,
  method        text NOT NULL,                  -- 'majority_3','senior_override','weighted_v1'
  decided_by    uuid REFERENCES users(id),      -- senior reviewer if escalated
  decided_at    timestamptz NOT NULL DEFAULT now(),
  superseded_by uuid REFERENCES consensus_labels(id),
  released_in   text                            -- FK added below, after dataset_releases exists
);

CREATE TABLE dataset_releases (
  version       text PRIMARY KEY,               -- '0.1.0'
  released_at   timestamptz NOT NULL,
  row_counts    jsonb NOT NULL,
  sha256        jsonb NOT NULL,                 -- per file
  zenodo_doi    text, hf_url text,
  changelog     text NOT NULL
);

ALTER TABLE consensus_labels
  ADD CONSTRAINT consensus_labels_released_in_fk
  FOREIGN KEY (released_in) REFERENCES dataset_releases(version);

-- Evidence cards -------------------------------------------------------------
CREATE TABLE evidence_cards (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_doi     text NOT NULL REFERENCES papers(doi) ON DELETE CASCADE,
  evidence_hash text NOT NULL,
  summary       jsonb NOT NULL,                 -- sentences with evidence_ids
  model         text NOT NULL, model_version text, prompt_hash text NOT NULL,
  schema_version integer NOT NULL,
  verifier_passed boolean NOT NULL,
  status        text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','in_review','approved','rejected')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (paper_doi, evidence_hash, schema_version)
);

-- Governance ---------------------------------------------------------------
CREATE TABLE appeals (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_doi     text NOT NULL,
  submitter_email citext NOT NULL,
  submitter_role text,                          -- 'author','publisher','reader','other' (self-declared)
  message       text NOT NULL,
  status        text NOT NULL DEFAULT 'received' CHECK (status IN ('received','under_review','resolved_changed','resolved_no_change','withdrawn')),
  received_at   timestamptz NOT NULL DEFAULT now(),
  acknowledged_at timestamptz,
  resolved_at   timestamptz,
  resolution_note text,
  handled_by    uuid REFERENCES users(id)
);

CREATE TABLE takedowns (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_doi     text NOT NULL,
  reason        text NOT NULL,
  scope         text NOT NULL CHECK (scope IN ('hide_page','remove_labels','remove_from_next_release')),
  requested_at  timestamptz NOT NULL DEFAULT now(),
  effective_at  timestamptz,
  decided_by    uuid REFERENCES users(id)
);

CREATE TABLE audit_log (
  id            bigserial PRIMARY KEY,
  at            timestamptz NOT NULL DEFAULT now(),
  actor_id      uuid REFERENCES users(id),
  action        text NOT NULL,
  object_type   text NOT NULL, object_id text NOT NULL,
  detail        jsonb
);

CREATE TABLE data_quality_events (
  id            bigserial PRIMARY KEY,
  at            timestamptz NOT NULL DEFAULT now(),
  kind          text NOT NULL,                  -- 'openalex_rw_mismatch','rw_bad_row', ...
  paper_doi     text, detail jsonb
);

CREATE TABLE job_runs (
  id            bigserial PRIMARY KEY,
  name          text NOT NULL,
  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz,
  status        text NOT NULL DEFAULT 'running',
  message       text
);
```

---

## 4. Derived view: public state of a paper

```sql
CREATE VIEW paper_public_state AS
SELECT p.doi,
  CASE
    WHEN EXISTS (SELECT 1 FROM retraction_evidence e
                 WHERE e.paper_doi = p.doi AND e.nature = 'retraction')
      THEN 'retracted_external'::public_state
    WHEN EXISTS (SELECT 1 FROM signals s JOIN signal_definitions d ON d.key = s.signal_key
                 WHERE s.paper_doi = p.doi AND d.public AND s.value_bool)
      THEN 'needs_review'::public_state
    WHEN p.metadata_source IS NULL OR p.reference_count IS NULL
      THEN 'insufficient_data'::public_state
    ELSE 'no_flags_found'::public_state
  END AS state
FROM papers p;
```
Design note: the UI text for `no_flags_found` is "No flags found in the sources we check (list, date)". It is never phrased as an endorsement.

---

## 5. Key queries

### 5.1 Retracted references of a paper
```sql
SELECT r.position, r.ref_doi, e.nature, e.event_date, rr.reasons, rr.rw_record_id
FROM paper_references r
JOIN retraction_evidence e ON e.paper_doi = r.ref_doi AND e.nature = 'retraction'
LEFT JOIN retraction_records rr ON rr.rw_record_id = e.rw_record_id
WHERE r.paper_doi = $1
ORDER BY r.position;
```
Note: `retraction_evidence` only holds rows for papers we have in `papers`. For reference DOIs not in `papers`, join `retraction_records` on `lower(original_doi)` directly. Use a `UNION` or a materialised view `retracted_dois(doi, first_retraction_date)` refreshed after ingest. **Prefer the materialised view**: one table of ~50k DOIs, indexed, fast.

### 5.2 "Cited after retraction" flag
```sql
-- reference was already retracted when the citing paper was published
SELECT count(*) FILTER (WHERE p.publication_date > rd.first_retraction_date) AS cites_after_retraction,
       count(*) FILTER (WHERE p.publication_date <= rd.first_retraction_date) AS cites_later_retracted
FROM paper_references r
JOIN retracted_dois rd ON rd.doi = r.ref_doi
JOIN papers p ON p.doi = r.paper_doi
WHERE r.paper_doi = $1;
```
Citing a paper that was retracted **later** is not the citing author's fault; it is context only.

### 5.3 Queue fetch (next task for reviewer)
```sql
WITH me AS (SELECT id, level, languages, fields FROM users WHERE id = $1)
SELECT t.*
FROM review_tasks t, me
WHERE t.status IN ('open','in_review')
  AND t.difficulty <= me.level
  AND t.language = ANY (me.languages)
  AND NOT EXISTS (SELECT 1 FROM task_assignments a
                  WHERE a.task_id = t.id AND a.reviewer_id = me.id)
  AND (SELECT count(*) FROM task_assignments a
       WHERE a.task_id = t.id AND a.status IN ('assigned','done')) < t.required_reviews
ORDER BY (t.subject = ANY (me.fields)) DESC, t.priority DESC, t.created_at
FOR UPDATE OF t SKIP LOCKED
LIMIT 1;
```
Then insert into `task_assignments` with a 30-minute lease in the same transaction. A cleanup job flips expired leases to `expired`.

---

## 6. Consensus algorithm (v1: majority of 3)

Inputs: the votes for one task. Independence is guaranteed because reviewers never see each other's votes and because `UNIQUE (task_id, reviewer_id)`.

```python
from collections import Counter

def decide(votes: list[str], required: int = 3) -> dict:
    """votes: list of 'yes'|'no'|'unsure'. Returns decision dict."""
    if len(votes) < required:
        return {"status": "waiting"}
    counts = Counter(votes)
    top, n_top = counts.most_common(1)[0]
    if top != "unsure" and n_top >= 2:
        return {"status": "decided", "label": top, "n_agree": n_top,
                "agreement": n_top / len(votes), "method": "majority_3"}
    # No majority, or majority says "unsure": escalate
    return {"status": "needs_senior"}
```
Rules:
- `unsure` never becomes a label by itself. Two "unsure" votes send the task to a senior reviewer.
- A senior decision is stored with `method = 'senior_override'` and `decided_by`.
- If a senior is also unsure, the task is withdrawn and marked `unresolved` (kept out of the dataset).
- Tests (`hypothesis`): decision is permutation-invariant; never returns a label with fewer than 2 agreeing votes; is deterministic.

### 6.1 Later (v0.4): weighted consensus
Use a Dawid–Skene style model (estimates each reviewer's confusion matrix using all tasks) or simple weights from gold accuracy. Keep majority as the published baseline and report how often weighted differs.

### 6.2 Agreement metrics
- Percent agreement per task type.
- Fleiss' kappa (multi-rater) or Krippendorff's alpha per task type per month.
- Gold accuracy per reviewer and per level.
- Published in every dataset release. Target for `ref_match`: alpha ≥ 0.75; below 0.6 means the task design is bad, not the reviewers.

---

## 7. Data retention

| Data | Retention |
|---|---|
| Papers, references, retraction records | Kept while source lists them; refreshed |
| Signals | Keep last 3 versions per paper/key |
| Reviews | Kept; reviewer link removed on account deletion |
| Sessions | Expired rows purged daily |
| Appeals | 3 years (resolved), then contact email scrubbed |
| audit_log | 2 years |
| Backups | 7 daily, 4 weekly, 6 monthly |

---

## 8. Migration plan by week

| Week | Migration set |
|---|---|
| 0–1 | `ingest_runs`, `papers`, `paper_references`, `retraction_records`, `retraction_evidence`, materialised view `retracted_dois` |
| 3–4 | `signal_definitions`, `signals`, `paper_public_state` view |
| 5 | `users`, `auth_identities`, `sessions`, `review_tasks`, `task_assignments`, `reviews`, `consensus_labels`, `reviewer_stats` |
| 6 | `gold_tasks` |
| 7–8 | `evidence_cards` |
| 10 | `appeals`, `takedowns`, `audit_log`, `data_quality_events` |
| 12 | `dataset_releases` |
