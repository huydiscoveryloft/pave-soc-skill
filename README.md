# pave-soc

SOC automation plugin for PAVE/DLVN. A container for security operations skills; designed so
new sub-skills (e.g. `triage`) drop in under `skills/` without touching existing ones.

## Skills
- **daily-security-report** — Builds the daily SOC report from Wazuh alerts (OpenVPN, physical
  access, vulnerability detector), fuses a SOC 2-aligned report, publishes it to Confluence,
  and posts a Slack summary.
  - Invoke with **`/daily-security-report [YYYY-MM-DD]`** — runs the report for that date;
    defaults to **yesterday** (UTC+7) when no date is given. Claude can also invoke it
    automatically when you ask for the daily security report.
- **alert-triage** — Triages a single Wazuh alert via a three-role agent chain (Investigator →
  Query agent → Threat Hunter), returns a True/False Positive verdict in chat, then optionally
  drafts and publishes an ISO 27001 incident report to Confluence.
  - Invoke with **`/alert-triage <alert-id>`** (e.g. `/alert-triage 1750412345.6789012`). Claude
    can also invoke it when you ask to triage/investigate an alert by id.

## Required connectors (MCP)
- **OpenSearch** — query Wazuh alert indices (both skills)
- **Atlassian Rovo** — read operation notes + create Confluence pages (both skills)
- **Slack** — post the daily-report summary (daily-security-report only)

Analysis and CVE web-search are handled natively by Claude; no LLM/search MCP is required.

## Layout
```
pave-soc/
├── .claude-plugin/plugin.json
└── skills/
    ├── daily-security-report/
    │   ├── SKILL.md
    │   ├── references/   (sources, report-format, publishing)
    │   └── scripts/      (report_period.py, physical_count.py)
    └── alert-triage/
        ├── SKILL.md
        ├── references/   (alert-query, agent-chain, incident-report, publishing)
        └── template/     (incident-report-template.md — from the official PDF)
```

## Adding a sub-skill later
Create `skills/<name>/SKILL.md` (plus optional `references/` and `scripts/`). It is
auto-discovered as `pave-soc:<name>` and invokable as `/<name>`.

## Maintaining / extending
Before changing anything, read `MAINTAINERS.md` (plugin-wide intent + decisions) and the
relevant skill's own `MAINTAINERS.md` (e.g. `skills/daily-security-report/MAINTAINERS.md`).
Append a Changelog line on every change.
