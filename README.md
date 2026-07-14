# pave-soc

**Security operations, automated.** `pave-soc` is a Claude plugin that turns routine SOC work at PAVE/DLVN — daily reporting, alert triage, user auditing, firewall review, and web-app pentesting — into slash commands you can run in chat or on a schedule.

Each capability is a self-contained skill under `skills/`. New skills drop in without touching the ones already there, so the plugin grows with your SOC.

## What it does

| Skill | Command | What you get |
|-------|---------|--------------|
| Daily security report | `/daily-security-report [date]` | A SOC 2-aligned daily report fused from Wazuh alerts, published to Confluence + summarized in Slack |
| Alert triage | `/alert-triage <alert-id>` | A True/False Positive verdict on a single alert, with an optional ISO 27001 incident report |
| Track user | `/track-user <username> [window]` | A chronological timeline of one AWS user's sign-ins and changes |
| AWS firewall review | `/aws-firewall-review` | A quarterly security-group audit flagging internet-exposed ports and permissive rules |
| Web-app pentest | `/webapp-pentest <url>` | An authorized OWASP Top 10 pentest run by an agent team, with a consolidated report |
| Pentest job runner | `/pentest-job-runner` | Drains one queued pentest from the Cloudflare job queue and reports status to the dashboard |

## Getting started

1. Install the plugin so its skills are discovered as `pave-soc:<name>`.
2. Connect the [required connectors](#required-connectors) for the skills you plan to use.
3. Run a skill by its command, or just ask — Claude invokes the right skill when you describe the task ("triage alert 1750412345.6789012", "review our firewall rules").

> [!TIP]
> Most skills accept plain-language requests. You don't have to memorize the commands — they're there for precision and for scheduled runs.

## Skills

### daily-security-report
Collects the target day's OpenVPN, physical-access, and vulnerability-detector alerts from Wazuh (OpenSearch), analyzes each source, and fuses them into one SOC 2-aligned report. Publishes a Confluence parent page with per-source child pages and posts a Slack summary.

```
/daily-security-report            # yesterday (UTC+7)
/daily-security-report 2026-07-13 # a specific day
```

### alert-triage
Investigates a single Wazuh alert through a three-role agent chain — an **Investigator** plans the queries, a **Query agent** runs them against OpenSearch, and a **Threat Hunter** concludes — then returns a True/False Positive verdict. On approval, it drafts an ISO 27001 incident report and publishes it to Confluence.

```
/alert-triage 1750412345.6789012
```

### track-user
Builds a chronological UTC+7 timeline of one named AWS user's activity — sign-ins, mutating actions, and errors — from Control Tower CloudTrail. Read-only, and always scoped to a named user (never org-wide). Output is saved as Markdown in your workspace.

```
/track-user huy.nguyen                       # last 7 days
/track-user huy.nguyen 14                     # last 14 days
/track-user huy.nguyen 2026-06-01 2026-06-22 # explicit window
```

### aws-firewall-review
Collects every AWS security group via a read-only Dockerised MCP collector, then applies deterministic risk analysis — internet-exposed sensitive ports, overly wide ranges, permissive egress — and renders a findings-focused quarterly report from the DLVN-SEC-TPL-002 template. On a full review it auto-publishes to Confluence and pushes status to the SOC dashboard.

```
/aws-firewall-review
```

### webapp-pentest
Runs an authorized web-app penetration test as a three-role agent team. A **Leading agent** scopes the target and builds an OWASP Top 10 (2025) checklist; a **Recon agent** crawls the app in a real browser (Claude in Chrome) through **Burp** and marks the exploitable targets; and one **Exploit agent** per target crafts non-destructive proof-of-concept requests via the Burp MCP. A confirmed exploit that unlocks new in-scope resources re-runs the recon→exploit loop (3-round cap) before the report is written.

```
/webapp-pentest https://staging.example.com  # full pipeline
/webapp-pentest scope                         # one stage at a time
/webapp-pentest recon
/webapp-pentest exploit
```

> [!WARNING]
> `webapp-pentest` requires explicit authorization for the target before any testing begins.

### pentest-job-runner
The unattended companion to `webapp-pentest`. On each tick it reconciles crashed runs, takes a single-machine lock, pulls one job from the Cloudflare Queue, drives a pentest, uploads the report to R2, and records the terminal status in D1. One job per tick; the lock guarantees a single pentest at a time. Meant to be fired by a scheduled task.

```
/pentest-job-runner
```

## Required connectors

Connect only what the skills you use need. Analysis and CVE lookups are handled natively by Claude — no separate LLM or search connector is required.

| Connector | Used by |
|-----------|---------|
| OpenSearch | daily-security-report, alert-triage |
| AWS CloudWatch (`awslabs.cloudwatch-mcp-server`) | daily-security-report (AWS source), track-user |
| AWS firewall-review MCP (Dockerised collector) | aws-firewall-review |
| Atlassian Rovo (Confluence) | daily-security-report, alert-triage, aws-firewall-review |
| Slack | daily-security-report |
| Burp Suite (`mcp__burp__*`) | webapp-pentest, pentest-job-runner |
| Claude in Chrome (`mcp__claude-in-chrome__*`) | webapp-pentest, pentest-job-runner |
| Cloudflare (`mcp__cloudFlare__*`) | pentest-job-runner |

## Project layout

```
pave-soc/
├── .claude-plugin/plugin.json   # plugin manifest
├── CHANGELOG.md                 # single source of truth for change history
└── skills/
    ├── daily-security-report/   # SKILL.md + references/ + scripts/
    ├── alert-triage/            # SKILL.md + references/ + template/
    ├── track-user/              # SKILL.md + references/ + scripts/
    ├── aws-firewall-review/     # SKILL.md + references/ + assets/
    ├── webapp-pentest/          # SKILL.md + references/ + template/
    └── pentest-job-runner/      # SKILL.md + references/
```

## Extending

Add a skill by creating `skills/<name>/SKILL.md` (plus optional `references/` and `scripts/`). It's auto-discovered as `pave-soc:<name>` and invokable as `/<name>` — no wiring needed.

> [!NOTE]
> Before changing a skill, add an entry to the top-level `CHANGELOG.md` on every change — capturing both what changed and the *why* behind it.
