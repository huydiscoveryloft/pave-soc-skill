-- fwreview_runs — the SOC dashboard's Firewall review table.
-- Mirror of pentest-dashboard/migrations/0003_fwreview.sql. Lives in its OWN D1 database
-- `fwreview` (id 78dde69f-cc9a-4b43-a265-03ae835fbc8c). The aws-firewall-review skill WRITES
-- this table via the Cloudflare MCP; the dashboard Worker only reads it. Kept here so the
-- skill's contract is self-contained. Timestamps are unix epoch seconds.
--
-- One row per review QUARTER. A re-run of the same quarter UPSERTs (supersedes) its row.
-- `status` is the pipeline state; `assessment` is the render-rules security rating — two
-- independent signals. The collector is all-or-nothing across profiles, so there is no
-- `halted` state (a partial collect never publishes).

CREATE TABLE fwreview_runs (
  quarter        TEXT PRIMARY KEY,               -- '2026Q2' (from metadata.generated_at)
  review_id      TEXT NOT NULL,                  -- 'DLVN-SEC-REV-NNN'
  status         TEXT NOT NULL DEFAULT 'running'
                 CHECK (status IN ('running','done','failed')),
  assessment     TEXT,                           -- EFFECTIVE | PARTIALLY EFFECTIVE | NOT EFFECTIVE (worst across accounts)
  total_high     INTEGER NOT NULL DEFAULT 0,     -- summed across accounts
  total_medium   INTEGER NOT NULL DEFAULT 0,
  total_low      INTEGER NOT NULL DEFAULT 0,
  total_sgs      INTEGER,
  unused_sgs     INTEGER,
  phase          TEXT,                           -- free-text stage; NULL until first emit
  summary        TEXT,
  accounts_json  TEXT,                           -- JSON array of per-account objects (see below)
  error          TEXT,                           -- failure/auth reason; NULL when healthy
  triggered_by   TEXT NOT NULL,                  -- 'scheduled' or an operator email
  created_at     INTEGER NOT NULL,
  started_at     INTEGER,
  updated_at     INTEGER,                        -- HEARTBEAT: bumped on every phase emit
  finished_at    INTEGER
);

-- accounts_json element (one per collected account profile):
--   { "profile":"production", "account_id":"123456789012",
--     "high":2, "medium":5, "low":3, "total_sgs":48, "unused_sgs":6,
--     "assessment":"PARTIALLY EFFECTIVE",
--     "confluence_url":"https://.../pages/1472...",
--     "findings":[ { "finding_id":"F-001", "severity":"HIGH", "group_id":"sg-0abc",
--                    "region":"ap-southeast-1", "category":"internet_exposed_sensitive_service",
--                    "detail":"22/tcp open to 0.0.0.0/0" } ] }
-- `findings` is the account's full risk_findings[] (severity HIGH|MEDIUM|LOW), reusing the
-- report's stable F-NNN ids so the dashboard's sort never churns between quarters.
