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

Keep each source independent — if one source's collection fails, note it and continue; the
report records which sources ran.

### 3. Tier 3 — fuse into the daily report
Read `references/report-format.md`. Combine the labeled per-source analyses into one
SOC 2-aligned report using the exact template (metadata header, findings table with
severity + disposition, per-source detail). This markdown is the parent-page body.

### 4. Confirm before publishing (MANDATORY GATE)
Do NOT create any Confluence page or post to Slack until the user explicitly approves.
Present to the user, in chat:
- the finalized Tier 3 report (the Confluence parent-page body) and each per-source child
  page's content;
- a preview of the Slack message (Tier 2 — draft it now per `references/report-format.md`,
  using `<report link>` as a placeholder for the not-yet-created Confluence URL);
- a one-line summary of the exact write actions: "Will create 1 Confluence parent page
  + N child pages in space 20480022, and post 1 message to #wazuh-ai-report."

Then wait for a clear yes. If the user requests changes, revise and re-present. Only continue
once they confirm. If the run is non-interactive (e.g. scheduled) and no one can confirm, do
NOT publish — save the drafts and report that the run is awaiting approval.

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
- Confluence write + Slack post are the only external-write actions, and both are gated
  behind the mandatory user confirmation in Step 4 (see publishing.md).
