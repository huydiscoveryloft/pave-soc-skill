# Changelog — pave-soc

All notable changes to the `pave-soc` plugin and its skills.

This file is consolidated from the per-asset `MAINTAINERS.md` changelogs (plugin root,
`skills/daily-security-report/`, `skills/alert-triage/`). For the *why* behind each change,
read the corresponding `MAINTAINERS.md`. Format loosely follows Keep a Changelog; versions
track `.claude-plugin/plugin.json`.

## [0.5.0] — 2026-06-24

### Changed
- **`daily-security-report`: source malfunction now halts the run.** A source whose collection
  errors/times out **or returns zero hits** is treated as malfunctioning and stops the workflow
  (was "note it and continue"). Interactive runs ask the user (continue-without / retry / abort);
  scheduled runs skip publishing. Zero hits counts as a malfunction because, for these sources,
  an empty day usually means stalled ingestion (cf. the 2026-06-19 stall).
- **`daily-security-report`: scheduled runs auto-approve publishing.** A Cowork scheduled /
  non-interactive run now auto-approves the Step 4 publish gate and distributes the report —
  but only when every source was healthy (previously scheduled runs never published). The
  malfunction halt always overrides auto-approval. Interactive runs are unchanged (explicit
  approval still required).

### Added
- **`daily-security-report`: scheduled-halt maintainer DM.** When a scheduled run halts on a
  malfunction, it DMs the maintainer (`huy.nguyen@discoveryloft.com`, resolved via
  `slack_search_users`) a minimal brief — report id + date, halted/nothing-published status, and
  the malfunctioning source(s) with the reason. Template lives in
  `skills/daily-security-report/references/publishing.md`.

## [0.4.0] — 2026-06-22

### Added
- **`track-user` skill.** Single-user, read-only AWS activity tracker. Given a **named** user and
  a window (default last 7 days; also accepts a day count or an explicit `YYYY-MM-DD` range), it
  queries Control Tower CloudTrail (`aws-controltower/CloudTrailLogs`, `ca-central-1`) via the
  CloudWatch MCP for the user's sign-ins, mutating actions (`readOnly = 0`), and errors, then
  assembles a chronological **UTC+7 timeline log** saved as Markdown in the workspace folder.
  Invoked `/track-user <username> [window]`. Requires a named user — never runs org-wide — and
  makes no external writes (no confirmation gate needed). New helper `scripts/activity_window.py`
  (UTC+7 window calc). Reuses the CloudTrail gotchas documented for the daily report's AWS source.
  (Initially named `user-activity`; renamed to `track-user` the same day.)

## [0.3.0] — 2026-06-22

### Added
- **`daily-security-report`: AWS user activity source.** Added a fourth monitored source
  covering AWS Control Tower CloudTrail, queried via the CloudWatch MCP
  (`awslabs.cloudwatch-mcp-server` → `execute_log_insights_query`, region `ca-central-1`, log
  group `aws-controltower/CloudTrailLogs`). Collects the day's mutating actions
  (`readOnly = 0`) across all users plus console sign-ins; analysis groups changes by identity
  (resolved from the role-session-name in the CloudTrail ARN) and flags security-sensitive
  changes. Verified against the live log group during build.

### Changed
- **`daily-security-report`: generalized the source registry with a per-source `backend`
  field** (`opensearch` | `cloudwatch`). `search_after` pagination is now scoped to the
  opensearch backend; cloudwatch sources use `execute_log_insights_query` with an explicit
  `limit`. Both reuse the same UTC+7 window from `report_period.py`. Wired the new source into
  the Tier 3 report template, the Tier 2 Slack Cyber section, and the Confluence child pages.
- **`daily-security-report`: scoped the AWS source to human identities** with a load-bearing
  `userIdentity.arn like /discoveryloft.com/` filter. A 2026-06-21 dry run showed the
  unfiltered query returns 83,578 rows/day of service-principal automation vs 5 human-activity
  rows with the filter. Caveat (excludes direct IAM-user/root logins) documented inline in the
  source entry.

## [0.2.0] — 2026-06-21

### Added
- **`alert-triage` skill.** Ported the n8n "Tier-1 operator" agent chain
  (Investigator → Query agent → Threat Hunter) as real subagents. Input by alert id; full-alert
  fetch via the OpenSearch MCP; TP/FP verdict returned in chat (no Slack). Includes an optional
  ISO 27001 incident report drafted locally then published to Confluence (parent `223773037`)
  behind a confirmation gate.
- **Incident report template.** Replaced the hand-authored template with
  `template/incident-report-template.md`, transcribed verbatim from the official PAVE incident
  report PDF (`OPENAPI-INC-2026-001`). `references/incident-report.md` reduced to field-derivation
  guidance.
- **Verdict-driven follow-up (alert-triage).** Trial run on alert `1781758278.30199963`
  (RDP, rule 92658) confirmed the chain end-to-end (False Positive). Step 5 now branches on
  verdict: False Positive → advisory rule-tuning recommendation, no report; True Positive /
  Inconclusive → offer the incident report.

## [0.1.0] — 2026-06-21

### Added
- **Plugin created.** `pave-soc` container for SOC operations skills; skills auto-discovered as
  `pave-soc:<name>` and invoked as `/<name>`.
- **`daily-security-report` skill.** Ported from the n8n "Daily security report" workflow
  (HTTP → MCP via OpenSearch/Atlassian/Slack). GCP audit/cloud branches dropped. UTC+7 windowing
  via `report_period.py`; `search_after` pagination; `physical_count.py` ported.

### Changed
- Fixed Physical `_source.excludes` to add `@timestamp` + `timestamp`, matching the original n8n payload.
- Added optional `YYYY-MM-DD` date parameter to `daily-security-report` (defaults to yesterday).
- Adopted option-3 slash convention plugin-wide (skill name is the slash trigger; no `commands/`
  directory). Removed the separate `/daily-report` command.

### Security
- Added a mandatory pre-publish confirmation gate before any external write (Confluence/Slack).
  `daily-security-report` Step 4; established as a plugin-wide rule for all side-effectful skills.
