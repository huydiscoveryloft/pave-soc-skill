---
name: aws-firewall-review
description: Generate a DLVN/PAVE quarterly AWS firewall configuration review. Collects all AWS security groups via the read-only aws-firewall-review MCP server (Dockerised boto3 collector, SSO-capable), applies deterministic risk analysis (internet-exposed sensitive ports, wide ranges, permissive egress), then renders a findings-focused markdown report from the DLVN-SEC-TPL-002 template. Use this WHENEVER the user wants to review, audit, or report on AWS security groups or firewall rules, run the quarterly firewall review, turn security-group data into a report, or check for security groups open to 0.0.0.0/0 — even if they don't say "DLVN" or "SOC 2". Also use it when the user has existing collector JSON output and wants a report written from it.
---

# AWS Firewall Configuration Review

This skill produces DiscoveryLoft Vietnam (DLVN) / PAVE quarterly AWS firewall
reviews. It has two halves that can run independently:

1. **Collect** — call the `aws-firewall-review` MCP server's
   `collect_security_groups` tool to produce structured JSON evidence of every
   security group with pre-computed risk findings (one object per account).
2. **Render** — turn that evidence JSON into a finished markdown report using the
   template in `assets/report_template.md` and the rules in `references/render_rules.md`.

The user may want both halves, or just one (e.g. they already have evidence JSON
and only need the report, or they only need the raw inventory).
Figure out which they need before starting.

## Decision: which half do I need?

- User asks to "run the firewall review" / "audit our security groups" end-to-end → do **both** (Collect, then Render).
- User provides a JSON file (or points at one) and wants a report → **Render only**.
- User wants to set up the collector / scheduled runs → focus on **Collect** setup; the MCP server source and its build/registration guide live in the `mcp_server/` directory at the project root (maintained separately from this plugin); IAM and SSO details are in `references/aws_setup.md`.
- User wants only the raw data / inventory → **Collect only**.

## Collect

Collection runs through the **`aws-firewall-review` MCP server** — a read-only,
Dockerised boto3 collector that reads the host's `~/.aws` (mounted read-only),
so credentials never pass through chat. The server source and its build /
registration guide live in the `mcp_server/` directory at the project root
(separate from this plugin); IAM and SSO setup are in `references/aws_setup.md`.

If the MCP server is not yet connected, point the user at the `mcp_server/`
directory's README to build the image
(`docker build -t pave/aws-firewall-review-mcp:latest .`) and register it, then
have them `aws sso login` to each account on the host.

**Standard run — the review targets three account profiles by default:
`development`, `uat`, and `production`.** Call the tool with no arguments to use
that set:

```
collect_security_groups()
# subset:        collect_security_groups(profiles=["development", "uat"])
# specific regions: collect_security_groups(regions=["ap-southeast-1", "us-east-1"])
# env credentials:  collect_security_groups(profiles=[])
```

It returns `{"accounts": [<evidence>, ...]}` — one evidence object per account,
each with the `metadata` / `global_summary` / `regions` shape the renderer
expects. Render one report per account.

**The run is all-or-nothing.** If any profile fails to authenticate (e.g. its SSO
session is missing or expired), the tool errors before collecting anything — it
does NOT skip the account. The error names the profile and the exact
`aws sso login --profile <name>` command to run on the host. When this happens,
relay the message to the user and stop; do not render with a partial set. Once
they have re-authenticated, call the tool again.

Helper tools: `list_aws_profiles()` confirms the container can see the mounted
`~/.aws`; `whoami(profile=...)` is a quick single-account auth check.

Key behaviours to know:
- **Credentials:** profiles are read from the mounted `~/.aws` with SSO cached tokens and role chaining resolved natively. `profiles=[]` falls back to environment / assume-role credentials inside the container.
- **Multiple accounts are all-or-nothing:** every profile is authenticated up front; if any fails, nothing is collected. No account is skipped.
- Region selection: `regions` arg → `AWS_REGIONS` env var → all enabled regions.
- The collector enriches each SG with attached-ENI data so unused/orphaned SGs are identifiable, and tags each rule with deterministic risk findings (HIGH/MEDIUM/LOW).
- SCP-denied regions are captured as `regions[].error` — this is expected, not a failure.

After collecting, summarise for the user (per account): total SGs, how many in
use, and the HIGH/MEDIUM/LOW finding counts (all available in `global_summary`).

## Render

Renders the evidence JSON into the report. **Before rendering, read
`references/render_rules.md` in full** — it defines the marker syntax, the
evidence shape, finding-ID ordering, owner/due-date defaults, the assessment-rating
thresholds, the Section 4 observation patterns, and the output style rules.

The template lives at `assets/report_template.md`. It uses three markers:
`HINT:` lines (instructions to strip), `LOOP: ... ENDLOOP` blocks (repeat per
item), and `<<PLACEHOLDER>>` tokens (substitute). The `<<...>>` syntax is
deliberate — it avoids collision with common `{{ }}` templating engines.

Process:
1. Load the evidence JSON and the template.
2. Walk the template top to bottom, applying the rules from `references/render_rules.md`.
3. Run the self-check at the end of `render_rules.md` before delivering.
4. Save the report to a `.md` file and present it. Name it
   `DLVN-SEC-REV-<NNN>_AWS_Firewall_Review_<QUARTER>.md`.

The report structure (already encoded in the template) is: Document Control →
Executive Summary (with findings summary table + key findings + overall
assessment) → Detailed Findings (HIGH blocks, MEDIUM table, LOW table) →
Additional Observations → Sign-Off → Appendix A (SCP-denied regions) → Appendix B
(full SG inventory) → Appendix C (evidence & tool references).

`references/example_report.md` is a complete worked example (the Q2 2026 report)
— consult it if you need to see the expected tone, depth, and table formatting.

## Status reporting (dashboard)

A full quarterly review (Collect **and** Render) backs the SOC dashboard's **Firewall
review** page. On such a run the skill pushes one row per **quarter** into the D1 database
`fwreview` (id `78dde69f-cc9a-4b43-a265-03ae835fbc8c`) via the Cloudflare MCP
(`mcp__cloudFlare__execute`). The dashboard only reads; the skill is the sole writer.

- **When to report.** Only for an end-to-end review (Collect → Render → publish). A
  render-only or collect-only ad-hoc run does **not** push unless the user asks. Decide once
  at the start.
- **Best-effort.** Every emit is wrapped so a failure is logged and ignored — a failed push
  must never abort or alter the review.
- **Keying.** One row per `quarter` (`YYYYQn`, from `metadata.generated_at`), upserted, so a
  re-run supersedes that quarter. `status` (running/done/failed) is the pipeline state;
  `assessment` (the render-rules rating) is the security posture — two independent signals.
- **`triggered_by`** = `"scheduled"` for an unattended run, else the operator's email.

The exact `mcp__cloudFlare__execute` calls are in `references/cf-snippets.md`; the table
shape is in `references/d1-schema.sql`. Emit points:
1. **Collect start** — upsert `status='running'`, `phase='collecting'`, `review_id`,
   `triggered_by` (cf-snippets §1).
2. **Phase boundaries** — `phase` → `analyzing` → `rendering` → `publishing`, bumping the
   heartbeat (§2).
3. **Success** — after all accounts are rendered and published: `status='done'`,
   `assessment` (worst across accounts), `total_high/medium/low`, `total_sgs`, `unused_sgs`,
   and `accounts_json` — one element per account with its counts, per-account `assessment`,
   `confluence_url`, and the **full `findings[]`** (each `{finding_id, severity, group_id,
   region, category, detail}`, reusing the report's stable `F-NNN` ids). The dashboard
   flattens these into one severity-sorted "All findings" table (§3).
4. **Failure** — the collector is all-or-nothing: if any profile fails to authenticate, or an
   unexpected error occurs, write `status='failed'` with `error` naming the profile and the
   exact `aws sso login --profile <name>` command (§4).

## Confluence notes

The review **auto-publishes** to Confluence so the dashboard's per-account "View report"
links resolve. For each end-to-end run:

- Publish into the **`pavewiki` space** (space id `20480022`, cloudId
  `0ab6bc10-825b-445d-a6db-6e3c267094dc`), under the existing **`AWS Firewall Review Report`
  folder** (id `312508532`,
  `https://paveai.atlassian.net/wiki/spaces/pavewiki/folder/312508532`). Create a **parent
  page** for the quarter (e.g. `AWS Firewall Review — <QUARTER>`) with `parentId` = the folder
  id `312508532`, then **one child page per account** (`parentId` = that quarter page) whose
  body is the account's rendered `DLVN-SEC-REV-<NNN>` markdown. Use the Atlassian MCP
  `createConfluencePage`.
- Capture each child page's `webUrl` and put it in that account's `confluence_url` in the
  Success emit (§3 above). The parent page's `webUrl` can go in `summary` or be linked from
  the children.
- **Publish failure is non-fatal.** If a page can't be created, leave that account's
  `confluence_url` null (the dashboard card shows "report not published") and continue — the
  review still completes and reports `done`.
- Keep the `<<...>>` placeholder syntax out of published pages (it's a render-time marker); if
  the user maintains the *template* in Confluence, the placeholders stay only in the template.

## Important constraints

- **No emojis** anywhere in the report.
- **No external compliance framework references** (SOC 2, ISO 27001, etc.) unless
  the user explicitly asks — the report's stated driver is DLVN-SEC-POL-002.
- **Do not invent findings** beyond the deterministic `risk_findings[]` in the
  evidence. Grouping and prioritising is fine; fabricating is not.
- Finding IDs must be **stable across re-runs** — follow the sort order in
  `references/render_rules.md` so cross-references don't break between quarters.
