# track-user — Maintainer's Note

Read this with `SKILL.md` before editing. It records intent and the decisions a change must not
silently break. **Rule: record every change in the plugin-wide `CHANGELOG.md` (repo root) —
not here. This note holds intent and decisions only, no change history.**

## Origin
Built to turn DLVN/PAVE's hand-written runbook for querying user activity from Control Tower
CloudTrail (via the CloudWatch MCP) into a repeatable procedure with a fixed deliverable. The
runbook's mechanics are now captured self-contained in `references/activity-query.md`.

User-chosen shape (clarified at build time, 2026-06-22):
1. **Track one user's actions over a period → write a timeline log.** The deliverable is a
   chronological Markdown timeline, not a chat-only answer and not a published report.
2. **A named user is mandatory.** The skill must not run without one and must **never** fall back
   to the org-wide `discoveryloft.com` view (that is the daily report's job). Step 1 stops and
   asks if no user is given.
3. **Default window = last 7 days** (rolling), overridable by a day count or an explicit date
   range.

## Architecture
A linear, read-only procedure (no agent chain, no subagents):
`resolve user → resolve window → sanity check → collect (sign-ins + mutating + errors) →
build timeline log → report`. Files:
- `scripts/activity_window.py` — deterministic UTC+7 window calc. Default last 7 days; accepts
  `N`/`Nd` (rolling) or two `YYYY-MM-DD` dates (inclusive calendar range). Emits
  `start`/`end`/`days`/`label`/`window_id`. Mirrors `daily-security-report/scripts/report_period.py`
  style (ISO-8601 `+07:00`, JSON, error+nonzero on bad input).
- `references/activity-query.md` — the CloudWatch query recipes (A sanity / B sign-ins /
  C mutating detail / D errors), region/log-group, the single-user identity token, and the three
  CloudTrail gotchas. Self-contained source of truth for the query mechanics.
- `references/timeline-format.md` — the timeline-log output contract (header, summary,
  chronological day-grouped entries with sign-in/sensitive/error flags, caveats).

## Relationship to daily-security-report's AWS source
Both read the **same** log group (`aws-controltower/CloudTrailLogs`, `ca-central-1`) via the
**same** CloudWatch MCP, and share the CloudTrail gotchas. They differ deliberately:
- **Scope:** daily report = *all* org humans (`arn like /discoveryloft.com/`); this skill =
  *one* named user (`arn like /<user>@discoveryloft/`). Do not let this skill go org-wide.
- **Window:** daily report = one calendar day (yesterday); this skill = arbitrary, default 7d.
- **Output:** daily report = SOC-2 report fused with Wazuh sources, published to
  Confluence/Slack; this skill = a standalone Markdown timeline saved locally, read-only.
If the CloudTrail query mechanics (gotchas, region) ever change, update **both**
`references/activity-query.md` here and `daily-security-report/references/sources.md` §4.

## Load-bearing decisions (don't change without knowing why)
1. **Single-user only.** The whole point is per-person auditing. The org-wide filter is
   intentionally *not* offered; that path belongs to the daily report.
2. **`readOnly` is numeric (`0`/`1`).** `= false` / `= "0"` silently match nothing. See gotcha 1
   in `references/activity-query.md`.
3. **Identity is the role-session-name in the ARN**, not `userIdentity.userName` (which is the
   permission-set role). Match on `userIdentity.arn` / `principalId` with `like`. Gotcha 2.
4. **Region `ca-central-1` is mandatory** — the org trail's home region, not the MCP default.
   Omitting it → `ResourceNotFoundException`. 
5. **Sign-ins appear twice.** `ConsoleLogin`/`GetSigninToken` are `readOnly = 0`, so they show up
   in both Query B and Query C — de-duplicate when building the timeline.
6. **Read-only; only the local log is written.** No external publish, so no confirmation gate
   (the plugin-wide gate rule applies only to external writes). If a variant publishes, add one.
7. **No fabrication / no over-reading MFA.** `MFAUsed: No` on SSO logins is expected (IdC
   enforces MFA) and is not a finding on its own.

## Connector IDs / fixed identifiers
- CloudWatch MCP: `awslabs.cloudwatch-mcp-server` → `execute_log_insights_query`.
- Log group `aws-controltower/CloudTrailLogs`; region `ca-central-1`.
- Network note: in Cowork the CloudWatch MCP is reached from Anthropic's cloud; AWS creds/region
  are configured on the connector, not here.

## Extension recipes
- **Change which events feed the timeline:** edit the queries in `references/activity-query.md`
  (e.g. add a read-only-highlights query). Keep the identity filter and numeric `readOnly`.
- **Change the log layout:** edit `references/timeline-format.md` (single source of truth for the
  deliverable).
- **Add publishing (Confluence/Slack):** add a step after Step 5 and a confirmation gate; reuse
  `daily-security-report/references/publishing.md` targets.
- **Different window semantics:** edit `scripts/activity_window.py`.

## Change history
Recorded in the plugin-wide `CHANGELOG.md` at the repo root.
