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
- **track-user** — Tracks a single named AWS user's activity over a time window from Control
  Tower CloudTrail (via the CloudWatch MCP) and writes a chronological UTC+7 timeline log
  (sign-ins, mutating actions, errors) as Markdown in the workspace folder. Read-only; requires
  a named user (never org-wide).
  - Invoke with **`/track-user <username> [window]`** — e.g. `/track-user huy.nguyen`,
    `/track-user huy.nguyen 14`, or `/track-user huy.nguyen 2026-06-01 2026-06-22`. Window
    defaults to the **last 7 days**. Claude can also invoke it when you ask to track/audit what a
    specific person did in AWS.
- **webapp-pentest** — Runs an authorized web-app penetration test as a three-role agent team:
  a **Leading agent** scopes the target, builds an OWASP Top 10 (2025) checklist, and writes the
  final report; a **Recon agent** crawls the app in a real browser (Claude in Chrome) through
  **Burp**, maps the attack surface from proxy history, and **marks the exploitable targets** (each
  with a success criterion); and one **Exploit agent** per target crafts non-destructive HTTP-request
  PoCs via the **Burp MCP**. A confirmed exploit that unlocks new in-scope resources loops the
  recon→exploit cycle (pivot loop, 3-round cap) before the consolidated report is written to the
  workspace. Requires explicit authorization before testing.
  - Invoke with **`/webapp-pentest <target-url>`** (e.g. `/webapp-pentest https://staging.example.com`)
    to run the whole pipeline, or run one stage at a time with **`/webapp-pentest scope`**,
    **`/webapp-pentest recon`**, or **`/webapp-pentest exploit`** — each stage persists its artifacts
    to a per-engagement folder so the next stage can pick up. Claude can also invoke it when you ask
    to pentest or Burp-scan a web target.

## Required connectors (MCP)
- **OpenSearch** — query Wazuh alert indices (daily-security-report, alert-triage)
- **AWS CloudWatch** (`awslabs.cloudwatch-mcp-server`) — query Control Tower CloudTrail
  (daily-security-report AWS source, track-user)
- **Atlassian Rovo** — read operation notes + create Confluence pages (daily-security-report,
  alert-triage)
- **Slack** — post the daily-report summary (daily-security-report only)
- **Burp Suite** (`mcp__burp__*`) — proxy-history capture + crafted HTTP requests (webapp-pentest)
- **Claude in Chrome** (`mcp__claude-in-chrome__*`) — real-browser crawl through Burp (webapp-pentest)

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
    ├── alert-triage/
    │   ├── SKILL.md
    │   ├── references/   (alert-query, agent-chain, incident-report, publishing)
    │   └── template/     (incident-report-template.md — from the official PDF)
    ├── track-user/
    │   ├── SKILL.md
    │   ├── references/   (activity-query, timeline-format)
    │   └── scripts/      (activity_window.py)
    └── webapp-pentest/
        ├── SKILL.md
        ├── references/   (agent-team, owasp-checklist, burp-recon, exploit-agent)
        └── template/     (pentest-report-template.md)
```

## Adding a sub-skill later
Create `skills/<name>/SKILL.md` (plus optional `references/` and `scripts/`). It is
auto-discovered as `pave-soc:<name>` and invokable as `/<name>`.

## Maintaining / extending
Before changing anything, read `MAINTAINERS.md` (plugin-wide intent + decisions) and the
relevant skill's own `MAINTAINERS.md` (e.g. `skills/daily-security-report/MAINTAINERS.md`).
Append a Changelog line on every change.
