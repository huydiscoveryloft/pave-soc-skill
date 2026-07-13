-- dailyreport_runs — the SOC dashboard's "Daily security health" table.
-- Canonical copy for the skill side (mirrors the dashboard repo's
-- migrations/0002_dailyreport.sql). Lives in D1 database `dailyreport`
-- (id 1c97153d-d9ba-4c7c-ab27-73029e5684e1). Provisioned + applied 2026-07-13.
--
-- The skill WRITES this table via the Cloudflare MCP (see cf-snippets.md); the dashboard
-- Worker only READS it. One row per report DATE (UTC+7); a re-run UPSERTs that day's row.
-- `status` = pipeline state; `severity` = security posture (two independent signals).

CREATE TABLE dailyreport_runs (
  report_date    TEXT PRIMARY KEY,               -- 'YYYY-MM-DD' (UTC+7), report_period.py `date`
  report_id      TEXT NOT NULL,                  -- 'DLSR-YYYYMMDD', report_period.py `report_id`
  status         TEXT NOT NULL DEFAULT 'running' -- pipeline state
                 CHECK (status IN ('running','done','halted','failed')),
  severity       TEXT,                           -- posture: info|low|medium|high|critical (max across sources)
  phase          TEXT,                           -- free-text stage; NULL until first emit
  summary        TEXT,                           -- short one-line result summary
  confluence_url TEXT,                           -- parent page webUrl; NULL until published
  sources_json   TEXT,                           -- JSON array of {name,severity,count,note}
  error          TEXT,                           -- malfunction/halt reason; NULL when healthy
  triggered_by   TEXT NOT NULL,                  -- 'scheduled' or an operator email
  created_at     INTEGER NOT NULL,
  started_at     INTEGER,
  updated_at     INTEGER,                        -- HEARTBEAT: bumped on every phase emit
  finished_at    INTEGER
);
