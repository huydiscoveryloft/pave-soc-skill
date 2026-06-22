# daily-security-report — Maintainer's Note

Read this with `SKILL.md` before editing. It captures intent and the decisions a change must
not silently break. **Rule: every change appends a line to the Changelog below.**

## Origin
Ported from the n8n workflow "Daily security report" (HTTP nodes → MCP). The original's GCP
audit/cloud branches were leftovers and were dropped. Queries, exclude lists, analysis prompts,
publishing targets, and the per-device count logic were carried over faithfully.

## Architecture
Modular **source registry**. Each monitored source is a `collect → (pre-process) → analyze`
module defined in `references/sources.md`. The orchestrator (`SKILL.md`) runs every source,
then Tier 3 fuses the labeled analyses into one SOC 2-aligned report, and Tier 2 condenses
that into a Slack message. Workflow = 7 steps; **Step 4 is a mandatory confirm gate** before
any external write. Files:
- `references/sources.md` — per-source query DSL, op-note IDs, pre-process, analysis spec (+ "add a source" template).
- `references/report-format.md` — Tier 3 SOC 2 template + Tier 2 Slack spec.
- `references/publishing.md` — Confluence/Slack targets + IDs.
- `scripts/report_period.py` — reporting window (UTC+7); takes optional `YYYY-MM-DD`, default yesterday.
- `scripts/physical_count.py` — deterministic per-device access tally.

## Load-bearing decisions (don't change without knowing why)
1. **`_source.excludes` must match the original n8n payloads exactly.** OpenVPN, Physical
   (includes `@timestamp` + `timestamp`), VD each have a specific list. They were verified
   field-for-field against the export. Changing them silently alters payloads.
2. **UTC+7 reporting window.** `report_period.py` returns `[start, end)` for the day at +07:00.
   Alert times are stored UTC (`timestamp`, `data.timestamp`); range filters use +07:00 ISO
   offsets, so the window is correct at query time. The **Physical analysis must still convert
   displayed event times to UTC+7** (data is UTC).
3. **OpenSearch page size caps at 100.** `SearchIndexTool` max size = 100, so collection
   paginates with `search_after` via `GenericOpenSearchApiTool` (full body: `query` + `sort`
   on the source's time field + `_id`, repeat until <100 hits). Never assume one call returns
   everything.
4. **Step 4 confirm gate is mandatory.** Never create Confluence pages or post to Slack before
   explicit user approval. Non-interactive/scheduled run with no approver → do NOT publish;
   save drafts and report "awaiting approval."
5. **Physical count is deterministic (`physical_count.py`).** Known devices always shown
   (Cổng trước, Lock F2/F3/F4); unknown devices/results auto-added. `markdown_table` → report,
   `ascii_table` → Slack.
6. **Slack format:** mrkdwn single-asterisk `*title*`/`*bold*`; exactly two sections
   (Cyber security; Physical security with the ASCII table); ASCII tables only; no recommended
   actions; ends with the Confluence parent `webUrl`.
7. **VD analysis requires a web search per CVE** for active-exploitation evidence.
8. **report_id scheme:** `DLSR-YYYYMMDD` (from `report_period.py`).
9. **Per-source backends.** A source declares `backend: opensearch | cloudwatch` in
   `sources.md`. `opensearch` paginates with `search_after` (100/page); `cloudwatch` uses
   `execute_log_insights_query` with an explicit `limit` and **no** pagination. Both reuse the
   same `report_period.py` window — its `start`/`end` are ISO-8601 `+07:00`, valid as both
   OpenSearch range bounds and CloudWatch `start_time`/`end_time`. Don't assume new sources are
   OpenSearch.
10. **AWS CloudTrail gotchas (silent zero-match traps), all encoded in the source entry:**
   region must be `ca-central-1` (Control Tower home region; not the MCP default `us-east-1`,
   else `ResourceNotFoundException`); `readOnly` is **numeric** (`= 0` write / `= 1` read — not
   `false`/`"0"`); identity is the role-session-name in `userIdentity.arn`/`principalId`, **not**
   `userName` (which holds the permission-set role). The AWS collect query is `readOnly = 0`
   filtered to human identities, which also captures console sign-ins (they are `readOnly = 0`).
   Source of truth for the AWS query + gotchas: the source #4 entry in `references/sources.md`
   (fully self-contained — no external file is read at runtime).

## Connector IDs (also in publishing.md)
- Confluence (Atlassian Rovo): cloudId `0ab6bc10-825b-445d-a6db-6e3c267094dc` (`paveai.atlassian.net`),
  spaceId `20480022`, daily parent page `147226819`; create with `contentFormat="markdown"`.
- Operation notes: OpenVPN page `234389695`, Physical page `235438195`.
- Slack: channel `C09V4H4H5PZ` (`#wazuh-ai-report`, private).
- CloudWatch (`awslabs.cloudwatch-mcp-server`): region `ca-central-1`, log group
  `aws-controltower/CloudTrailLogs` (Control Tower org trail). Read-only `execute_log_insights_query`.

## Environment notes
- During build (2026-06-21), ingestion had stalled after ~2026-06-19 06:00 UTC+7 across all
  sources — a data-availability issue external to this skill, not a query bug. Latest complete
  day used for the dry-run was 2026-06-18.

## Extension recipes
- **Add a source (e.g. AWS):** append an entry to `references/sources.md` (query DSL with
  `{{START}}`/`{{END}}` range filter; op-note id or none; pre-process or none; analysis spec),
  and add its name to "Sources (current)" in `SKILL.md`. Tier 3, the Confluence child pages,
  and the Slack summary pick it up automatically. Decide which Slack section it belongs to
  (Cyber vs Physical) and reflect that in `references/report-format.md` if needed.
- **Add a pre-processing step:** drop a script in `scripts/` that reads the saved hits JSON
  and emits what the analysis needs; reference it from the source's `pre_process`.
- **Change the report structure / SOC 2 fields:** edit the Tier 3 template in
  `references/report-format.md` (single source of truth for the format).

## Changelog
- 2026-06-21 — Initial build from n8n export; HTTP→MCP (OpenSearch/Atlassian/Slack);
  GCP branches removed; UTC+7 windowing via `report_period.py`; `search_after` pagination;
  `physical_count.py` ported.
- 2026-06-21 — Fixed Physical `_source.excludes` to add `@timestamp` + `timestamp` (match original).
- 2026-06-21 — Added optional `YYYY-MM-DD` date param (default yesterday).
- 2026-06-21 — Adopted option-3 slash (`/daily-security-report`); removed the `/daily-report` command.
- 2026-06-21 — Added mandatory pre-publish confirmation gate (Step 4).
- 2026-06-22 — Generalized the source registry with a per-source `backend` field
  (`opensearch` | `cloudwatch`); scoped `search_after` pagination to the opensearch backend.
- 2026-06-22 — Added source #4 "AWS user activity" (Control Tower CloudTrail via CloudWatch MCP
  `execute_log_insights_query`, region `ca-central-1`, log group `aws-controltower/CloudTrailLogs`):
  collects the day's mutating actions (`readOnly = 0`) across all users + console sign-ins, with
  the numeric-`readOnly` / identity-in-ARN gotchas encoded inline. Wired into SKILL.md (required
  servers, source list, backend-aware Step 2), report-format.md (Tier 3 detail + Tier 2 Cyber
  section), and publishing.md (AWS child page). Verified the CloudWatch query against the live
  log group during build.
- 2026-06-22 — AWS source: added a **load-bearing human-identity filter**
  `userIdentity.arn like /discoveryloft.com/` to the collect query, and changed scope from "all
  users" to "all DLVN/PAVE human identities". Dry run for 2026-06-21 showed the unfiltered
  `readOnly = 0` query returns 83,578 rows/day (almost all SSM/EKS service-principal
  automation); with the filter it returns 5 (the actual human activity). Org humans authenticate
  via IAM Identity Center, so their role-session-name is their `@discoveryloft.com` email.
  Caveat documented inline: this excludes direct IAM-user/root console logins (no
  `discoveryloft.com` in ARN) — check those separately via `userIdentity.type`.
