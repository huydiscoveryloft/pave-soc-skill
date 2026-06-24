# alert-triage — Maintainer's Note

Read this with `SKILL.md` before editing. It captures intent and the decisions a change must
not silently break. **Rule: record every change in the plugin-wide `CHANGELOG.md` (repo root) —
not here. This note holds intent and decisions only, no change history.**

## Origin
Ported from the n8n workflow **"Tier-1 operator"** (Slack-triggered alert triage). The user
asked to keep **only the agent chain** and re-shape the rest. Three intentional departures from
the original:
1. **Input by alert id**, not scraped from a Slack thread. The n8n flow listened for an
   `app_mention` containing "investigate", pulled the thread, and regex-extracted the alert `id`
   from a Slack attachment. We drop all of that — the id is the skill's argument.
2. **All OpenSearch access via MCP.** The original fetched the full alert with a raw basic-auth
   HTTPS call to `wazuh.uat.paveapi.com:9200` and only the query agent used the MCP. We unify on
   the OpenSearch MCP for both the full-alert fetch and the investigative queries.
3. **Verdict returned in chat**, not posted to Slack. No Slack connector is used.

Added beyond the original: an optional **ISO 27001 incident report** (Step 5), drafted locally
then published to Confluence, modeled on the existing `INC-2026-001` page.

## Architecture
A linear three-role **agent chain** run as **real subagents** (Agent/Task tool) for context
isolation, mirroring n8n's three separate agents:
`Investigator → Query agent (per query) → Threat Hunter`. Deterministic glue between roles:
fence-strip + JSON-parse of the Investigator's query array, and aggregation of query findings.
Files:
- `references/alert-query.md` — OpenSearch DSL to fetch the full alert by `id`.
- `references/agent-chain.md` — the three role prompts (ported verbatim, with the two
  adaptations noted above) + parse/aggregate glue + model hints.
- `template/incident-report-template.md` — **authoritative** 12-section ISO 27001 report
  structure, transcribed verbatim from the official PAVE PDF (example `INC-2026-001`). Source of
  truth for report structure; copy + fill it.
- `references/incident-report.md` — field-derivation guidance only (how to populate the template
  from triage output); defers structure to the template file.
- `references/publishing.md` — Confluence target + `INC-YYYY-NNN` numbering.

## Load-bearing decisions (don't change without knowing why)
1. **The three prompts are ported faithfully.** Their wording was carried over from the n8n
   nodes (Initial Analyze / Query agent / Triage agent). The Investigator's constraints are
   load-bearing: single-condition queries, FULL JSON field paths in `filter_criteria`, exact
   timeframes, **no network/firewall queries** (the org collects no router/firewall data),
   <300-word output. Don't loosen these — the Query agent (a small model) depends on them.
2. **Real subagents, not inline reasoning.** The user explicitly chose true subagents over
   native sequential reasoning. Use `subagent_type: general-purpose` so the Query subagent has
   the OpenSearch MCP. Model hints: Investigator/Threat Hunter strong (Sonnet/Opus), Query agent
   lightweight (Haiku) — matching the original's model assignment.
3. **`SearchIndexTool` field names take no `.keyword` suffix** (per the Query-agent prompt) and
   the full-alert `match` on `id` is matched as-is.
4. **Threat Hunter outputs chat-plain text**, not Slack `mrkdwn`. The original's elaborate
   mrkdwn-conversion block was dropped because the verdict is delivered in chat. If a future
   variant posts to Slack, reinstate mrkdwn conversion.
5. **Confirmation gate before publishing the incident report** (Step 5.2), per the plugin-wide
   rule for side-effectful skills. The draft is written locally first; nothing is created in
   Confluence before explicit approval. Triage itself (Steps 1–4) is read-only and ungated.
6a. **Report structure is the PDF template, not invented.** `template/incident-report-template.md`
   was transcribed verbatim from the official PAVE incident report PDF (the original embedded
   template in `references/incident-report.md` was replaced). Keep it the single source of truth
   for section order, headings, table columns, and field labels; if the official form changes,
   re-transcribe the template rather than editing structure ad hoc. `references/incident-report.md`
   holds only field-derivation guidance.
5a. **Verdict drives follow-up; a False Positive never produces an incident report.** Step 5
   branches on the Threat Hunter verdict: False Positive → a short, advisory **rule-tuning
   recommendation** (and stop, no Confluence write); True Positive / Inconclusive → offer the
   incident report. Rationale: incident reports are for real/suspected incidents; FPs are better
   served by tuning the noisy rule. Tuning recommendations are advisory only — never auto-apply
   rule changes.
6. **Incident report = local draft → Confluence on approval.** Numbering `INC-YYYY-NNN`,
   sequential per year; new pages are children of parent `223773037` in space `OPENAPI`. The
   numeric `spaceId` is resolved at publish time from the key (not hardcoded) to avoid staleness.
7. **No fabrication.** Unsupported report fields are `None` / `TBD` / `Pending`. The full alert
   `_source` is preserved end-to-end so the Investigator can reference real field paths.

## Connector IDs (also in publishing.md)
- Confluence (Atlassian Rovo): cloudId `0ab6bc10-825b-445d-a6db-6e3c267094dc`
  (`paveai.atlassian.net`), space key `OPENAPI` (slug `pavewiki`), incident parent page
  `223773037`. Create with `contentFormat="markdown"`.
- OpenSearch: index `wazuh-alerts-4.x-*` via `GenericOpenSearchApiTool` / `SearchIndexTool`.

## Environment notes
- Reference incident pages at build time (2026-06-21): `INC-2026-001` (`223773037`),
  `INC-2026-002 (Draft)` (`227966978`) → next id `INC-2026-003`.
- `getConfluenceSpaces` was declined during the build, so the numeric `pavewiki` spaceId was not
  captured; the skill resolves it at runtime. Cache it in `publishing.md` once confirmed.

## Extension recipes
- **Change a role's behavior:** edit the matching prompt in `references/agent-chain.md` (single
  source of truth). Keep the Investigator's hard constraints (see decision 1).
- **Different alert source / index:** edit `references/alert-query.md`.
- **Change the report structure:** edit `references/incident-report.md`; keep section parity with
  the live `INC-*` pages.
- **Re-add Slack delivery:** add a Slack post step after Step 4 and reinstate the mrkdwn
  conversion rules in the Threat Hunter prompt.

## Change history
Recorded in the plugin-wide `CHANGELOG.md` at the repo root.
