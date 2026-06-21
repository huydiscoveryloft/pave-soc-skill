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
    └── alert-triage/              # sub-skill (has its own MAINTAINERS.md)
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
- **Repackage:** `cd pave-soc && zip -r /tmp/pave-soc.plugin . -x "*.DS_Store"` then copy to
  the outputs dir (zip in /tmp first — writing straight to outputs can fail on permissions).

## Changelog
- 2026-06-21 — Plugin created. `daily-security-report` ported from the n8n "Daily security
  report" workflow. Adopted option-3 slash (skill-name trigger, no `commands/`). Added
  mandatory pre-publish confirmation gate. See the skill's MAINTAINERS.md for its detail.
- 2026-06-21 — Added `alert-triage` skill (v0.2.0). Ported the n8n "Tier-1 operator" agent chain
  (Investigator → Query agent → Threat Hunter) as real subagents; input by alert id, full-alert
  fetch via OpenSearch MCP, verdict in chat (no Slack), optional ISO 27001 incident report
  drafted locally then published to Confluence behind a confirm gate. See its MAINTAINERS.md.
