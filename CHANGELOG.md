# Changelog — pave-soc

All notable changes to the `pave-soc` plugin and its skills.

This is the **single source of truth** for change history across the plugin and all skills; the
per-asset `MAINTAINERS.md` files no longer keep their own changelogs. For the *why* behind each
change, read the corresponding `MAINTAINERS.md` (intent and decisions). Format loosely follows
Keep a Changelog; versions track `.claude-plugin/plugin.json`.

## [0.9.0] — 2026-07-06

### Added
- **`webapp-pentest`: sandbox reachability preflight + local-runner fallback.** The Leading agent
  now preflights the target from the sandbox (`curl` for an HTTP status) in Step 1, and each Exploit
  agent re-checks before attacking. If the target is blocked by the egress allowlist (local/LAN
  hosts, un-allowlisted `*.trycloudflare.com` tunnels), the Exploit agent no longer fails — it emits
  a stdlib-only **local runner** into the workspace folder that the user runs on their host, writing
  results back for Claude to read. Verdict in that case is **Inconclusive (pending local run)**.
  Documents that allowlist changes only take effect in a **new session** and that tunnel URLs are
  ephemeral. Verified live against a DVWA tunnel once allowlisted.
- **`webapp-pentest`: authenticated-context support for login-gated targets.** New optional **auth**
  input (login URL, user-supplied credentials, session mechanism, anti-CSRF field, any level/mode to
  set). The Leading agent collects it (Step 1.3), the Threat-hunting agent configures an
  **authenticated ZAP context** (login method, logged-in/out indicators, active user, logout
  excluded) so the spider/active scan cover post-login pages, and each Exploit agent **logs in
  first** — scraping any anti-CSRF token, detecting and setting required app state (e.g. DVWA
  `security` level) rather than hard-coding it — before attacking authenticated endpoints. Verified
  end-to-end against DVWA's authenticated SQLi module (UNION-based extraction of DB version + a
  targeted credential row, non-destructive).

## [0.8.0] — 2026-07-01

### Added
- **New skill: `webapp-pentest`.** Runs an authorized web-application penetration test as a
  four-role **agent team** and returns a consolidated report. A **Leading agent** (the orchestrator
  context) scopes the target with the user and builds an **OWASP Top 10 (2025)** checklist; a
  **Threat-hunting agent** subagent drives the **ZAP MCP** (`mcp__zap__*`: context → spider → AJAX
  spider → passive-queue drain → active scan → report) and exports normalized findings; a
  **Report-review agent** subagent triages findings into an exploit-target list, each item carrying
  full context plus a checkable `success_criteria`; and **one Exploit agent subagent per target**
  writes and runs non-destructive Python PoCs (sandboxed shell) until the criterion is met or
  approaches are exhausted. Report-review then writes the final report. Roles run as real subagents
  (mirrors `alert-triage`); the orchestrator owns the parse/aggregate/fan-out glue. Invoked
  `/webapp-pentest <target-url>`. OWASP 2025 category list verified against owasp.org.
- **`webapp-pentest`: mandatory authorization gate.** No spider/scan/exploit runs until the user
  confirms in-scope target(s) and explicit authorization (Step 1.2). Once confirmed, scanning and
  in-scope PoC execution are **auto-approved** (no per-step confirmation) but bounded to
  **non-destructive**, in-scope actions — no data destruction/exfiltration, persistence, DoS, or
  out-of-scope pivoting. Files (report, ZAP export, PoC scripts) are written to the workspace only;
  no external publish step.
- **New required connector: ZAP** (`mcp__zap__*`) for `webapp-pentest`.

## [0.7.0] — 2026-06-26

### Added
- **New skill: `aws-firewall-review`.** Generates the DLVN/PAVE quarterly AWS firewall
  configuration review. Collects all AWS security groups across every enabled region, applies
  deterministic risk analysis (internet-exposed sensitive ports, wide CIDR ranges, permissive
  egress), then renders a findings-focused markdown report from the DLVN-SEC-TPL-002 template.
  The collect and render halves can run independently. Registered in the plugin description.
- **`aws-firewall-review`: Dockerised MCP collector.** Collection runs through the
  `aws-firewall-review` MCP server (stdio, launched via `docker run -i`) instead of a standalone
  CLI. The container reads the host's `~/.aws` mounted read-only, so credentials never pass
  through chat. Tools: `collect_security_groups(profiles?, regions?, workers?)`,
  `list_aws_profiles()`, `whoami(profile?)`. The server source lives in the `mcp_server/`
  directory at the project root, kept separate from the plugin so the skill source stays clean.
- **`aws-firewall-review`: SSO + multi-account, all-or-nothing.** `collect_security_groups`
  defaults to the standard review set — `development`, `uat`, `production` — resolving SSO cached
  tokens natively, and returns one evidence object per account under `accounts[]`. Every profile
  is authenticated up front; if any fails (e.g. an expired SSO session) the tool errors before
  collecting anything and returns the `aws sso login --profile <name>` command to fix it. No
  account is skipped, so a multi-account review is never partial. Pass `profiles=[]` for
  environment / assume-role credentials.

### Removed
- **`aws-firewall-review`: standalone CLI and n8n coupling.** The `scripts/query_security_groups.py`
  CLI is replaced by the MCP server (shared logic now in `mcp_server/collector_core.py`). Dropped
  all n8n-specific framing from the skill, references, and template (the `<<...>>` placeholder
  syntax remains, as it still avoids `{{ }}` templating collisions). Default assume-role session
  names use a `dlvn-` prefix.

## [0.6.0] — 2026-06-24

### Added
- **`track-user`: final human-friendly readable report.** After building the technical timeline
  log, the skill now re-reads it and rewrites it as a plain-language narrative (Step 6, before
  report-back). Actions are **decoupled** — one "User …" sentence per line stating intent and
  outcome (denials/errors included), identifiers inline. Saved as
  `UA-<user>-<window_id>-readable.md` and presented as the final deliverable; the technical log
  becomes the working artifact. New contract in `references/readable-report.md`.

### Fixed
- **`track-user`: timeline entries now render as separate lines.** Both format specs
  (`timeline-format.md`, `readable-report.md`) now require a blank line between every entry (and
  between the readable report's two header lines). Without it, Markdown collapsed the timeline
  into one run-on paragraph.
## [Unreleased]

### Added
- **CI: SkillSpector security scan.** New `.github/workflows/skillspector.yml` runs NVIDIA
  SkillSpector against the repo on push, pull request, and manual dispatch. Static-only
  (`--no-llm`) SARIF scan; findings render to the GitHub Actions job summary, upload as an
  artifact, and publish to code scanning.

## [0.5.1] — 2026-06-24

### Docs
- **Consolidated all change history into this `CHANGELOG.md`.** Removed the `## Changelog`
  section from every `MAINTAINERS.md` (plugin root + `daily-security-report`, `alert-triage`,
  `track-user`) and updated their "every change appends a line to the Changelog below" rule to
  point here instead. MAINTAINERS.md files now hold intent and decisions only. Updated
  `ARCHITECT.md` accordingly. Docs-only; no behavior change.

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
