---
name: alert-triage
description: >-
  Triage a single Wazuh/OpenSearch security alert end-to-end and, on request, produce an
  ISO 27001-aligned incident report. Invoke with /alert-triage followed by the Wazuh alert
  id (e.g. /alert-triage 1750412345.6789012). Use whenever the user asks to "triage",
  "investigate", or "analyze" a specific alert by id, or to determine whether an alert is a
  True Positive or False Positive. Fetches the full alert from OpenSearch, runs a three-role
  agent chain (Investigator plans queries -> Query agent runs them via OpenSearch -> Threat
  Hunter concludes), returns a TP/FP verdict in chat, then offers to draft an incident report
  and (on approval) publish it to Confluence.
disable-model-invocation: false
---

# Alert Triage

Investigates one Wazuh alert by id and returns a **True Positive / False Positive** verdict.
The core is a **three-role agent chain** (ported from the n8n "Tier-1 operator" workflow):
an **Investigator** plans investigative queries, a **Query agent** executes them against
OpenSearch, and a **Threat Hunter** fuses everything into a final verdict. After the verdict,
the skill optionally drafts and publishes an ISO 27001-aligned incident report.

This skill differs from the n8n original in three ways: the alert is supplied **by id** (not
scraped from a Slack thread), **all** OpenSearch access goes through the OpenSearch **MCP**
(no raw HTTP), and the verdict is returned **in chat** (no Slack post).

## Required MCP servers
- **OpenSearch** — fetch the full alert and run the Investigator's queries
  (`GenericOpenSearchApiTool` / `SearchIndexTool`).
- **Atlassian Rovo** — create the Confluence incident-report page (only if the user opts in).

If a required server is unavailable, stop and tell the user which one — do not fabricate data.

## Inputs
- **alert id** (required): a Wazuh alert id such as `1750412345.6789012`, taken from
  `$ARGUMENTS` or the user's request. If absent or malformed, **stop and ask** — never guess.

## Reference files (read before running the matching step)
- `references/alert-query.md` — OpenSearch DSL to fetch the full alert by id.
- `references/agent-chain.md` — the three role prompts (Investigator, Query agent, Threat
  Hunter) and the parse/aggregate glue between them. **Load this before Step 3.**
- `references/incident-report.md` — field-derivation guidance for the incident report. **Load
  this only if the user opts into a report (Step 5).**
- `template/incident-report-template.md` — the **authoritative** ISO 27001 report structure
  (transcribed from the official PAVE PDF). Copy and fill this when building a report.
- `references/publishing.md` — Confluence target (cloudId, space, parent, numbering).

## Workflow

### 1. Resolve the alert id
Take the id from `$ARGUMENTS` or the request. Validate it looks like a Wazuh id
(`<digits>.<digits>`). If missing or malformed, stop and ask the user for it.

### 2. Fetch the full alert (OpenSearch MCP)
Run the query in `references/alert-query.md` to retrieve the complete alert document from
`wazuh-alerts-4.x-*`. Keep the full `_source` JSON — every downstream role needs it.
- 0 hits → tell the user no alert matches that id and stop.
- >1 hit → use the most recent; note the ambiguity to the user.

### 3. Run the agent chain (three subagents)
Read `references/agent-chain.md`, then run the chain using **real subagents** (the Agent/Task
tool, `subagent_type: general-purpose`) so each role has an isolated context, mirroring the
original three-agent workflow.

1. **Investigator** — spawn a subagent with the Investigator prompt + the full alert JSON.
   It returns a short activity description, a Yes/No on whether deeper investigation is
   warranted, and a **JSON array of numbered, single-condition investigative queries**
   (`query_number`, `description`, `filter_criteria` with full JSON field paths, `timeframe`).
   - If it answers **No** (not worth investigating), skip to Step 4 with the Investigator's
     reasoning as the basis for a likely-False-Positive verdict (record that no queries ran).
2. **Parse** the JSON array deterministically (strip any ```` ```json ```` fence, parse).
3. **Query agent** — for **each** requirement, spawn a subagent with the Query-agent prompt +
   that one requirement. It uses the OpenSearch **MCP** (`SearchIndexTool`) against
   `wazuh-alerts-4.x-*` and returns a short summarized finding (no DSL dumps). Collect all
   findings into one `query_result` list. Prefer a lightweight model (e.g. Haiku) for this role.
4. **Threat Hunter** — spawn a subagent with the Threat-Hunter prompt + the Investigator's
   analysis + the aggregated `query_result`. It returns the final **TP/FP** determination with
   key findings and an assessment.

See `references/agent-chain.md` for the exact prompts, model hints, and the output structure.

### 4. Return the verdict (in chat)
Present the Threat Hunter's verdict **in the chat response** using this plain structure
(this is chat, not Slack — use normal formatting):

```
Alert:    <alert id + one-line what it is>
Verdict:  <True Positive | False Positive | Inconclusive>
Key Findings:
  - <finding 1>
  - <finding 2>
Assessment: <short assessment>
```

### 5. Follow-up — driven by the verdict
Branch on the Threat Hunter's verdict. **An incident report is only for a real (or suspected)
incident — never for a False Positive.**

**If the verdict is False Positive →** do **not** write an incident report. Instead produce a
short **rule-tuning recommendation** and end. It should cover: the rule id + why it fired, the
evidence that makes it benign, a proposed tuning (least-broad first: downgrade severity → scope
an exception by source range/logon type → narrow user+host+IP whitelist), the conditions under
which the rule should still alert (the true-positive signals to preserve), and residual risk.
The recommendation is **advisory only** — never apply rule changes automatically. Offer to save
it as a Markdown file in the workspace folder if the user wants.

**If the verdict is True Positive or Inconclusive →** ask plainly:
**"Do you want me to write an incident report for this alert? (yes/no)"**
- **No** → end. Report what was done (alert id, verdict).
- **Yes** → read `references/incident-report.md` and:
  1. **Draft locally first.** Copy `template/incident-report-template.md` (the authoritative
     structure) and fill it from the triage output per `references/incident-report.md`; write
     it as a Markdown file in the workspace folder (`INC-<YYYY>-<NNN>-<slug>.md`). Present the
     draft to the user.
  2. **CONFIRM GATE (mandatory).** Ask for explicit approval to publish. Do **not** create the
     Confluence page before the user approves. If running non-interactively with no approver,
     stop after the draft and report "awaiting approval."
  3. **Publish on approval.** Create the Confluence page per `references/publishing.md` (resolve
     the numeric `spaceId`, pick the next `INC-YYYY-NNN`, create under the configured parent),
     then return the page `webUrl`.

### 6. Report back
Summarize: alert id, verdict, and the follow-up — for a False Positive, the tuning
recommendation; otherwise whether a report was drafted/published and the Confluence link if one
was created.

## Side-effect safety
The only external write is the Confluence incident page (Step 5, True Positive / Inconclusive
path), gated behind the Step 5.2 confirmation. The False Positive path and Steps 1–4 are
read-only.
