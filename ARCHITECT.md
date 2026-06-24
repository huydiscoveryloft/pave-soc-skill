# pave-soc — Architecture

Audience: an AI agent or engineer who needs to understand how this plugin is structured and
how it executes, before reading code. For *why* decisions were made and how to extend safely,
see `MAINTAINERS.md` (plugin root) and the per-skill `MAINTAINERS.md`.

## 1. Overview
`pave-soc` is a **Claude plugin** — a container for SOC operations skills. It holds two skills:
`daily-security-report` (generates an audit-grade daily security report from Wazuh alerts and
distributes it) and `alert-triage` (triages a single alert by id through a three-role agent
chain and optionally produces an ISO 27001 incident report). The system is **orchestration over
MCP tools**: there is no long-running service and no application code that calls APIs directly.
A skill's `SKILL.md` is a procedure that Claude executes, calling MCP tools (OpenSearch,
Atlassian, Slack) and (for the daily report) a couple of deterministic local Python scripts,
and performing the analysis/summarization itself.

`alert-triage` adds a second architectural pattern alongside the daily report's source
registry: a **linear agent chain run as real subagents** (Investigator → Query agent → Threat
Hunter), with deterministic glue (JSON-array parse, finding aggregation) between roles. Its
contract is detailed in `skills/alert-triage/MAINTAINERS.md`.

Shape:
```
Plugin (pave-soc)
  └─ Skill (daily-security-report)        ← procedure in SKILL.md
       ├─ references/  (declarative config: sources, report format, publishing targets)
       ├─ scripts/     (deterministic helpers: date window, physical count)
       └─ runtime deps: MCP tools + native Claude analysis/web-search
```

## 2. Component map
| Path | Role |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest (name, version). Makes the folder a plugin. |
| `skills/daily-security-report/SKILL.md` | **The orchestrator.** Defines the 7-step pipeline Claude follows. The only "executable" entry point. |
| `references/sources.md` | **Source registry** (declarative). Per-source: OpenSearch query DSL, operation-note page, pre-process step, analysis spec. The expansion surface. |
| `references/report-format.md` | Output contract: the Tier 3 SOC 2 report template + the Tier 2 Slack message spec. |
| `references/publishing.md` | Sink configuration: Confluence cloudId/space/parent, Slack channel, write format. |
| `scripts/report_period.py` | Pure function → reporting window (UTC+7) from optional `YYYY-MM-DD`, default yesterday. |
| `scripts/physical_count.py` | Pure function → per-device access tally (markdown + ASCII tables) from collected hits. |
| `MAINTAINERS.md` (×2) | Intent, load-bearing decisions, extension recipes, changelog. |

Separation of concerns: **`SKILL.md` = control flow**, **`references/*` = declarative data
(what to query, how to format, where to publish)**, **`scripts/*` = deterministic compute**,
**Claude = the analytic/judgment layer**.

## 3. Core pattern — the source registry
The central abstraction is a registry of **sources**, each a self-contained module with a
uniform contract:

```
collect → (optional pre-process) → analyze → labeled analysis
```

A source is defined entirely by data in `references/sources.md`:
- **collect**: an OpenSearch query (index pattern + DSL with a `{{START}}`/`{{END}}` UTC+7 range filter), paginated to completion.
- **operation note** (optional): a Confluence page of known-good/false-positive context, applied during analysis.
- **pre-process** (optional): a deterministic script over the collected hits (Physical → `physical_count.py`).
- **analyze**: a prompt spec (role, focus, timezone handling, word limit) that Claude applies to produce a markdown analysis labeled with the source name.

Current sources: **OpenVPN**, **Physical access**, **Vulnerability detector**. Downstream
stages (Tier 3 fusion, Confluence child pages, Slack summary) consume *whatever sources ran*,
by label — so adding a source requires no change to those stages. This is what makes the plugin
extensible (e.g. a future AWS source).

## 4. Execution pipeline (SKILL.md, 7 steps)
```
1. Reporting period   report_period.py [date]  →  {date, start, end, report_id}   (UTC+7)
2. Per source         for each source: collect (paginate) → op-note → pre-process → analyze
                                                                   →  labeled markdown analyses
3. Tier 3 fuse        analyses  →  one SOC 2-aligned report (metadata, findings table, detail)
4. CONFIRM GATE       present report + Slack preview + write summary; WAIT for explicit approval
5. Publish            Confluence: create parent page (capture id+webUrl) → child page per source
6. Slack post         finalize Tier 2 message with real webUrl → post to channel
7. Report back        return report_id, sources run, Confluence link, post status
```
Stage boundaries (what flows): step 1 emits the time window + report id used by every query
and the report header; step 2 emits one labeled analysis per source plus the physical count
tables; step 3 emits the parent-page body; steps 5–6 are the only external writes and are
**gated** by step 4.

## 5. External integration surface
All integration is via **MCP tools**; analysis and CVE research are native Claude (no LLM/search
MCP). The plugin does not bundle these connectors — they must be connected in the host (Cowork).

| Capability | MCP server | Used for |
|---|---|---|
| Query Wazuh alerts | **OpenSearch** (`GenericOpenSearchApiTool`) | All source collection; full-body DSL with `search_after` pagination (page size cap = 100) |
| Read notes / publish | **Atlassian Rovo** | Read operation notes; create Confluence parent + child pages (`contentFormat=markdown`) |
| Distribute summary | **Slack** | Post the Tier 2 message |
| Analysis & CVE lookup | *native Claude* | Per-source analysis, Tier 3 fusion, Tier 2 summary, web search for CVE exploitation |

Fixed external identifiers live in `references/publishing.md` (Confluence cloudId
`0ab6bc10-…`, space `20480022`, parent `147226819`; Slack channel `C09V4H4H5PZ`; op-note pages
`234389695`, `235438195`). Network note: in Cowork, MCP connectors are reached from Anthropic's
cloud, so the OpenSearch endpoint must be publicly reachable.

## 6. Data-flow diagram
```
                       report_period.py ──► {window, report_id}
                                                │
            ┌───────────────────────────────────┼───────────────────────────────────┐
            ▼ (per source, in parallel concept)  ▼                                   ▼
   OpenSearch MCP ──hits──► [pre-process?] ──► Claude analysis ──► labeled analysis ─┐
   (+ Atlassian op-note)     (physical_count.py)                                     │
                                                                                     ▼
                                                                       Tier 3 fusion (Claude)
                                                                                     │
                                                                          parent-page body
                                                                                     │
                                                                        ┌──── CONFIRM GATE ────┐
                                                                        │  (user approves)     │
                                                                        ▼                      ▼
                                                          Atlassian MCP                 Slack MCP
                                                   (parent + child pages)        (Tier 2 message w/ link)
```

## 7. Invocation & control flow
- **Slash / auto:** the skill name is its slash trigger, `/daily-security-report`; Claude may
  also auto-invoke it from a matching natural-language request (no separate command file).
- **Date parameter:** optional `YYYY-MM-DD` argument (via `$ARGUMENTS` or stated in the
  request) → passed to `report_period.py`; absent → yesterday (UTC+7). Malformed → halt and ask.
- **Side-effect safety:** step 4 gates all external writes. *Interactive* runs require explicit
  user approval before publishing. *Scheduled/non-interactive* runs **auto-approve** publishing,
  but only when every source was healthy. A source malfunction (collection error or zero hits)
  halts the workflow at step 2 — interactive runs ask the user; scheduled runs skip publishing,
  post a Slack alert, and report the run halted.

## 8. Extension points
- **New source:** add an entry in `references/sources.md` + the source list in `SKILL.md`.
  Fusion/publishing/Slack pick it up by label automatically.
- **New pre-process:** add a deterministic script in `scripts/` referenced by a source's `pre_process`.
- **New sink / format:** edit `references/report-format.md` (output contract) or
  `references/publishing.md` (targets).
- **New sub-skill:** add `skills/<name>/` with its own `SKILL.md`; auto-registers as
  `pave-soc:<name>`, invokable `/<name>`.

## 9. Key invariants (summary; rationale in MAINTAINERS.md)
- `_source.excludes` lists match the original n8n payloads exactly.
- Reporting window is UTC+7; alert times are stored UTC and converted at query time (physical
  analysis converts displayed times too).
- OpenSearch returns ≤100 hits/call → collection must paginate.
- External writes are gated at step 4: interactive runs require user approval; scheduled runs
  auto-approve only when all sources are healthy. A source malfunction (error or zero hits)
  halts the run before publishing.
- Physical counts come from `physical_count.py` (deterministic), not ad-hoc tallying.
- VD analysis must web-search each CVE for active-exploitation evidence.
