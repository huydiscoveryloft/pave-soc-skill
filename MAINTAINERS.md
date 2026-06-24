# pave-soc — Maintainer's Note

Read this first when extending the plugin. It records *why* things are the way they are, not
just what they do. **Rule: record every change in the plugin-wide `CHANGELOG.md` (repo root) —
not here. This note holds intent and decisions only, no change history.**

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

## Change history
Recorded in the plugin-wide `CHANGELOG.md` at the repo root.
