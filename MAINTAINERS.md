# pave-soc — Maintainer's Note

Read this first when extending the plugin. It records *why* things are the way they are, not
just what they do. **Rule: every change appends a line to the Changelog below.**

## Architecture
`pave-soc` is a plugin *container* for SOC operations skills. Each skill is a self-contained
folder under `skills/<name>/` with its own `SKILL.md` (+ optional `references/`, `scripts/`,
and its own `MAINTAINERS.md`). Skills are auto-discovered as `pave-soc:<name>` and invoked as
`/<name>`. The design is additive: a new sub-skill drops in without touching existing ones.

```
pave-soc/
├── .claude-plugin/plugin.json     # manifest (name, version)
├── MAINTAINERS.md                 # this file (plugin-wide)
├── README.md
└── skills/
    ├── daily-security-report/     # sub-skill (has its own MAINTAINERS.md)
    ├── alert-triage/              # sub-skill (has its own MAINTAINERS.md)
    └── track-user/                # sub-skill (has its own MAINTAINERS.md)
```

## Load-bearing decisions (plugin-wide)
1. **Slash = skill name (option 3).** No `commands/` directory. Custom commands and skills
   were merged (Claude Code v2.1.101); a skill's `name` is its slash trigger and Claude can
   also auto-invoke it. We dropped the separate `/daily-report` command so there is a single
   source of truth. Cost: the trigger is `/<skill-name>`, not a free alias.
2. **Integration is via MCP, not HTTP.** Connectors used across the plugin: **OpenSearch**
   (Wazuh indices), **Atlassian Rovo** (Confluence), **Slack**. Analysis and CVE web-search
   are native Claude — no LLM/search MCP. Per-skill connector IDs live in that skill's note.
3. **Side-effectful skills must gate external writes behind explicit user confirmation.**
   See daily-security-report Step 4. If a future skill publishes/posts/sends, do the same.

## Extension recipes
- **Add a sub-skill:** create `skills/<name>/SKILL.md` (third-person `description` with
  trigger phrases; imperative body). Add `references/`/`scripts/` as needed, plus a per-skill
  `MAINTAINERS.md`. It auto-registers as `pave-soc:<name>`, invokable `/<name>`. If it has
  side effects, include a confirmation gate; consider `disable-model-invocation: true` to
  require explicit invocation. List it under "Skills" in README.
- **Bump the version** in `.claude-plugin/plugin.json` (semver) on meaningful change.
- **Repackage:** `cd pave-soc && zip -r /tmp/pave-soc.plugin . -x "*.DS_Store" -x "*__pycache__*" -x "*.pyc" -x ".git/*"`
  then copy to the outputs dir (zip in /tmp first — writing straight to outputs can fail on
  permissions). The excludes matter: without `.git/*` the whole repo history ships in the
  plugin, and `__pycache__`/`*.pyc` bundle stale bytecode.

## Changelog
- 2026-06-21 — Plugin created. `daily-security-report` ported from the n8n "Daily security
  report" workflow. Adopted option-3 slash (skill-name trigger, no `commands/`). Added
  mandatory pre-publish confirmation gate. See the skill's MAINTAINERS.md for its detail.
- 2026-06-21 — Added `alert-triage` skill (v0.2.0). Ported the n8n "Tier-1 operator" agent chain
  (Investigator → Query agent → Threat Hunter) as real subagents; input by alert id, full-alert
  fetch via OpenSearch MCP, verdict in chat (no Slack), optional ISO 27001 incident report
  drafted locally then published to Confluence behind a confirm gate. See its MAINTAINERS.md.
- 2026-06-22 — Added plugin-wide `CHANGELOG.md`, consolidated from the per-asset MAINTAINERS.md
  changelogs (plugin root + both skills). Docs-only; no behavior change.
- 2026-06-22 — `daily-security-report` v0.3.0: added an "AWS user activity" source (Control
  Tower CloudTrail via the CloudWatch MCP) and generalized the source registry with a per-source
  `backend` field (`opensearch` | `cloudwatch`). Introduces a second collection backend alongside
  OpenSearch. See the skill's MAINTAINERS.md for the CloudTrail gotchas. Version bumped to 0.3.0.
- 2026-06-22 — Added `track-user` skill (v0.4.0; initially named `user-activity`, renamed same
  day). Single-user, read-only AWS activity tracker: queries Control Tower CloudTrail (CloudWatch
  MCP) for a named user over a window (default last 7 days) and writes a chronological UTC+7
  timeline log to the workspace folder. Shares CloudTrail mechanics with the daily report's AWS
  source but is per-user (never org-wide) and does not publish externally. See its MAINTAINERS.md.
  Version bumped to 0.4.0.
- 2026-06-24 — `daily-security-report` v0.5.0: (1) source malfunction (collection error or zero
  hits) now halts the run instead of note-and-continue; (2) scheduled/non-interactive runs
  auto-approve the Step 4 publish gate when all sources are healthy (previously they never
  published); (3) scheduled halts DM the maintainer a minimal brief instead of staying silent.
  See the skill's MAINTAINERS.md. Version bumped to 0.5.0.
