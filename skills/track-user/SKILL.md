---
name: track-user
description: >-
  Track a single AWS user's activity over a time window from Control Tower CloudTrail (via the
  CloudWatch MCP) and write a chronological timeline log. Invoke with /track-user followed by
  the username and an optional window (e.g. /track-user huy.nguyen, /track-user huy.nguyen 14,
  or /track-user huy.nguyen 2026-06-01 2026-06-22). Use whenever the user asks to "track",
  "audit", "review", or "build a timeline of" what a specific person did in AWS — what they
  changed, or when and where they signed in. Requires a named user and never runs org-wide;
  defaults to the last 7 days. Queries aws-controltower/CloudTrailLogs in ca-central-1, assembles
  sign-ins and mutating actions into a UTC+7 timeline, and saves it as a Markdown log in the
  workspace folder.
disable-model-invocation: false
---

# User Activity Timeline

Tracks **one named AWS user's** activity over a time window and produces a **chronological
timeline log** (Markdown, saved to the workspace folder). It pulls the user's sign-ins, mutating
actions, and errors from the Control Tower organization CloudTrail (`aws-controltower/CloudTrailLogs`)
via the CloudWatch MCP, converts everything to UTC+7, and assembles a single ordered narrative of
what that person did, where, and from which IPs.

This skill is **single-user by design** — it never runs org-wide. If no user is given, it stops
and asks. It is **read-only** against AWS; its only write is the local Markdown log.

## Required MCP servers
- **CloudWatch** (`awslabs.cloudwatch-mcp-server`) — `execute_log_insights_query` against the
  CloudTrail log group.

If the CloudWatch MCP is unavailable, stop and tell the user — do not fabricate activity.

## Inputs
- **username** (required): a person's handle, e.g. `huy.nguyen` (the org SSO identity). Taken
  from `$ARGUMENTS` or the request. **If absent, stop and ask — never run without a named user,
  and never substitute an org-wide query.**
- **window** (optional): either an integer day count (`7`, `14`, `30d`) for a rolling window, or
  two `YYYY-MM-DD` dates for an explicit range. Default: **last 7 days**.

## Reference files (read before the matching step)
- `references/activity-query.md` — the CloudWatch query recipes, region/log-group, identity
  token, and the CloudTrail gotchas. **Load before Step 3.**
- `references/timeline-format.md` — the output contract for the timeline log. **Load before
  Step 5.**

## Workflow

### 1. Resolve the user (required)
Take the username from `$ARGUMENTS` or the request. **If none is provided, stop and ask the user
who to track.** Do not proceed org-wide. Build the identity token per `references/activity-query.md`
(e.g. `huy.nguyen` → `huy.nguyen@discoveryloft`).

### 2. Resolve the window
Run `scripts/activity_window.py` with the user's window argument(s), or no argument for the
default last 7 days:
- rolling: `python3 activity_window.py [N|Nd]`
- explicit: `python3 activity_window.py <YYYY-MM-DD> <YYYY-MM-DD>`

Capture `start`, `end`, `label`, `window_id`. On a `{"error": …}` result, show it and ask for a
valid window.

### 3. Sanity check (CloudWatch MCP)
Read `references/activity-query.md`, then run **Query A** (read/write split for the user) over
the window. This confirms the identity token matches and there is data.
- If it returns rows → proceed.
- If it returns **0/0** → re-check the three gotchas in order (region `ca-central-1`, numeric
  `readOnly`, identity token matches the ARN) before concluding "no activity." Only after those
  check out, treat the window as genuinely quiet (Step 5 still writes a header-only log).

### 4. Collect the events (CloudWatch MCP)
Run, over the same window and region:
- **Query B** — sign-ins (auth timeline).
- **Query C** — mutating actions with full detail (`@message` for resource ids). If the row
  count hits the `limit`, re-run with a higher limit or split the window, and record the
  truncation for the log.
- **Query D** — errors / denied actions.

Parse `@message` for affected resource ids (`requestParameters`, `responseElements`,
`resources[]`). De-duplicate sign-ins between Query B and Query C (logins are `readOnly = 0` and
appear in both). Optionally save raw results to `/tmp/user_activity_<user>.json`.

### 5. Build the timeline log
Read `references/timeline-format.md` and assemble the log: header metadata, a Summary, the
chronological **Timeline** (oldest first, grouped by UTC+7 calendar day, sign-in/sensitive/error
flags), and Notes & caveats. Convert all `eventTime` (UTC) to **UTC+7**. Resolve the actor to the
human via the role-session-name in the ARN. Call out security-sensitive changes (IAM, security
groups, networking, CloudTrail/Config, new instances, secrets) and any denied/error actions.

Write it to the **workspace folder** as `UA-<user>-<window_id>.md`. Present a short summary in
chat and share the file.

### 6. Report back
Summarize: who was tracked, the window, event counts (sign-ins / mutating / errors), any
security-sensitive actions or unfamiliar source IPs, and the path to the saved timeline log.

## Side-effect safety
Read-only against AWS — all four queries are reads via the CloudWatch MCP. The only write is the
local Markdown timeline log in the workspace folder (no external publish, no confirmation gate
required). If a future variant publishes to Confluence/Slack, add a confirmation gate per the
plugin-wide rule.
