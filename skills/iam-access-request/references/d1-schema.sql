-- iam_* — the SOC dashboard's IAM access request tables.
-- Mirror of pentest-dashboard/migrations/0012_iamreq.sql. Lives in its OWN D1 database
-- `iamreq` (id 0d85d6ea-fcc9-445e-8a8e-85c55a43401d). The iam-access-request skill WRITES
-- iam_requests via the Cloudflare MCP; the dashboard Worker reads it AND owns every write to
-- iam_reviews (approval is a human act, with the reviewer identity taken from the Access JWT).
-- iam_reviewers is configured from the dashboard. Kept here so the skill's contract is
-- self-contained. Timestamps are unix epoch seconds.
--
-- reviewer_snapshot duplicates the configured reviewer set onto the request at insert time, so
-- later configuration edits cannot retroactively change an in-flight approval. iam_reviews uses
-- a composite key so a reviewer's second vote conflicts instead of overwriting the first.
--
-- suggestion_json is LLM-authored, and every field is optional:
-- {"identity_name":"GrafanaFinOpsCurReadRole","identity_type":"role","account":"management",
--  "trust_policy":{...},"policy":{"Version":"2012-10-17","Statement":[]},"notes":"free text"}
CREATE TABLE iam_requests (
  id                        TEXT PRIMARY KEY,
  created_at                INTEGER NOT NULL,
  updated_at                INTEGER,
  requester                 TEXT NOT NULL,
  source_type               TEXT NOT NULL CHECK (source_type IN ('slack','jira')),
  source_ref                TEXT,
  title                     TEXT NOT NULL,
  identity_type             TEXT NOT NULL CHECK (identity_type IN ('role','user')),
  suggestion_json           TEXT NOT NULL,
  setup_steps_md            TEXT,
  assumptions_md            TEXT,
  discovery_evidence_md     TEXT,
  placeholders_json         TEXT,
  crosscheck_instruction_md TEXT,
  reviewer_snapshot         TEXT NOT NULL,
  status                    TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','approved','rejected')),
  guide_md                  TEXT,
  guide_generated_at        INTEGER
);
CREATE INDEX idx_iam_requests_created ON iam_requests(created_at);
CREATE INDEX idx_iam_requests_status  ON iam_requests(status);

CREATE TABLE iam_reviews (
  request_id         TEXT NOT NULL,
  reviewer_email     TEXT NOT NULL,
  decision           TEXT NOT NULL CHECK (decision IN ('approved','rejected')),
  crosscheck_verdict TEXT,
  comment             TEXT,
  decided_at         INTEGER NOT NULL,
  PRIMARY KEY (request_id, reviewer_email)
);
CREATE INDEX idx_iam_reviews_request ON iam_reviews(request_id);

CREATE TABLE iam_reviewers (
  email     TEXT PRIMARY KEY,
  added_at  INTEGER NOT NULL
);
