---
name: daily-security-report
description: >-
  Generate the daily SOC security report for DLVN/PAVE from Wazuh alerts and publish it to
  Confluence and Slack. Invoke with /daily-security-report (optionally followed by a target
  date as YYYY-MM-DD; defaults to yesterday). Use this whenever the user asks to run,
  generate, or schedule the "daily security report", the SOC daily report, or the Wazuh
  daily report — or when a scheduled task triggers it. Collects the target day's OpenVPN,
  physical-access, and vulnerability-detector alerts from OpenSearch, analyzes each, fuses
  them into one SOC 2-aligned report, publishes a Confluence parent + per-source child pages,
  and posts a Slack summary. Also use when adding a new monitored source (e.g. AWS).
---

# Daily Security Report

Produces one audit-grade daily security report from Wazuh/OpenSearch data and distributes it.
The pipeline is **modular**: each data source is a self-contained module, and Tier 3 / Tier 2
consume whatever modules ran. Adding a source = one entry in `references/sources.md` + the
source list below.

## Required MCP servers
- **OpenSearch** — query Wazuh alert indices (`GenericOpenSearchApiTool`); used by sources 1–3.
- **CloudWatch** (`awslabs.cloudwatch-mcp-server`) — query Control Tower CloudTrail logs
  (`execute_log_insights_query`); used by the AWS source.
- **Atlassian Rovo** — read operation notes + create Confluence pages.
- **Slack** — post the summary.
Analysis and CVE web-search are done natively; no LLM/search MCP needed.

If a required server is unavailable, stop and tell the user which one — do not fabricate data.
A server is required only if a source that uses it is in the run; if just the CloudWatch
server is down, you may still run the OpenSearch sources and note AWS was skipped.

## Sources (current)
1. OpenVPN
2. Physical access
3. Vulnerability detector
4. AWS user activity

Each source declares a **backend** (`opensearch` or `cloudwatch`) and carries its query,
operation note, pre-processing, and analysis spec in `references/sources.md`. Read that file
before collecting.

## Workflow

### 1. Reporting period
Determine the target date:
- If invoked as `/daily-security-report <date>`, the trailing argument (`$ARGUMENTS`) is the
  date. If the user named a date in their request, use that.
- If no date is given (bare `/daily-security-report`, an auto-invocation, or a scheduled
  run), default to **yesterday**.

Run `python scripts/report_period.py [YYYY-MM-DD]` — pass the date when one was given, omit it
otherwise. Use the returned `date`, `start`, `end`, `report_id` throughout; the window is that
day 00:00–24:00 **UTC+7**. If the script returns an `error` (malformed date), stop and ask the
user for a valid `YYYY-MM-DD` date before doing anything else.

### 2. Per source (do for each source in the list above)
Follow `references/sources.md`:
1. **Collect** — run the source's query with `{{START}}`/`{{END}}` substituted, by backend:
   - `opensearch` → the OpenSearch query body, paginating with `search_after` until all hits
     are gathered.
   - `cloudwatch` → one `execute_log_insights_query` call (region `ca-central-1`, the log
     group, `{{START}}`/`{{END}}` as `start_time`/`end_time`, a `limit`). No `search_after`;
     if the row count hits the limit, re-run wider and note truncation.
   Save results to `/tmp/<source>_hits.json`.
2. **Operation note** — if the source has one, read that Confluence page (markdown).
3. **Pre-process** — if the source has a script (Physical → `scripts/physical_count.py`),
   run it and keep its output.
4. **Analyze** — produce a markdown analysis per the source's analysis spec. Label it with
   the source name. (VD requires a web search per CVE.)

**Malfunction halt (do NOT silently continue).** Treat a source as *malfunctioning* if its
collection step **errors/times out** OR returns **zero hits**. A malfunction is a stop
condition — do not run the rest of the workflow on a partial dataset:
- **Interactive run:** stop immediately and tell the user which source malfunctioned and why
  (error message, or zero hits for the window). Ask whether to (a) continue without that
  source, (b) retry it, or (c) abort. Only proceed once the user chooses. If they choose to
  continue, note the source as skipped in the report.
- **Scheduled / non-interactive run:** do NOT publish. Skip Steps 3–6 and **send a Slack DM to
  the maintainer** (`huy.nguyen@discoveryloft.com`) briefing what happened. Resolve the user id
  with `slack_search_users` (query the email), then `slack_send_message` with that user id as
  `channel_id`. Keep the brief minimal — only: report id + date, a halted/nothing-published
  status line, and the malfunctioning source(s) with the reason (error message or "0 hits for
  the window"). Do NOT list healthy sources, explain why the DM was sent, or suggest next steps.
  Use the exact template in `references/publishing.md`. Then report the run as halted awaiting
  review.

(Zero hits is treated as a malfunction here because, for these sources, an empty day usually
means stalled ingestion rather than genuine silence — cf. the 2026-06-19 ingestion stall.)

### 3. Tier 3 — fuse into the daily report
Read `references/report-format.md`. Combine the labeled per-source analyses into one
SOC 2-aligned report using the exact template (metadata header, findings table with
severity + disposition, per-source detail). This markdown is the parent-page body.

### 4. Confirm before publishing (GATE)
**Scheduled run (Cowork scheduled task / non-interactive):** publishing is **auto-approved** —
proceed straight to Steps 5–6 *only if every source was healthy* (Step 2 found no malfunction).
This auto-approval applies solely to publishing a clean, complete report; it does **not**
override the Step 2 malfunction halt. If any source malfunctioned, you already stopped in
Step 2 — do not publish.

**Interactive run:** do NOT create any Confluence page or post to Slack until the user
explicitly approves. Present to the user, in chat:
- the finalized Tier 3 report (the Confluence parent-page body) and each per-source child
  page's content;
- a preview of the Slack message (Tier 2 — draft it now per `references/report-format.md`,
  using `<report link>` as a placeholder for the not-yet-created Confluence URL);
- a one-line summary of the exact write actions: "Will create 1 Confluence parent page
  + N child pages in space 20480022, and post 1 message to #wazuh-ai-report."

Then wait for a clear yes. If the user requests changes, revise and re-present. Only continue
once they confirm.

### 5. Publish (only after approval)
Read `references/publishing.md`. Create the Confluence **parent page** (capture its `id`
and `webUrl`), then a **child page per source** under it.

### 6. Tier 2 — Slack post (only after approval)
Finalize the Slack message by replacing the `<report link>` placeholder with the real
Confluence parent `webUrl`, then post it to the channel in `references/publishing.md`.

### 7. Report back
Tell the user: report_id, sources that ran, the Confluence parent link, and that the Slack
message was posted.

## Notes
- Times in all output are UTC+7. OpenVPN/VD `timestamp`, Physical `data.timestamp`, and AWS
  CloudTrail `eventTime` are all stored/returned in UTC; the query windows use UTC+7 ISO
  offsets so collection is correct, but the Physical and AWS analyses must convert displayed
  event times to UTC+7.
- Confluence write + Slack post are the only external-write actions. In an interactive run
  both are gated behind the user confirmation in Step 4; in a scheduled run they are
  auto-approved, but only when every source was healthy (a Step 2 malfunction always halts
  publishing). See publishing.md.
