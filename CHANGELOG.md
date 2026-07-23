# Changelog — pave-soc

All notable changes to the `pave-soc` plugin and its skills.

This is the **single source of truth** for change history across the plugin and all skills. Each
entry should capture both what changed and the *why* behind it. Format loosely follows Keep a
Changelog; versions track `.claude-plugin/plugin.json`.

## [Unreleased]

## [0.21.0] — 2026-07-23

### Changed
- **`iam-access-request`: `references/` now contains only what a skill run reads.** The discovery
  identity's CloudFormation template and setup procedure were shipping as skill references, but
  they are one-time operator artifacts deployed by a human, never read during a run — they
  appeared in the references table and nowhere else in the procedure, which is what gave it away.
  Moved out of the plugin to the project's `infra/` directory.
  - Remaining references, each cited inline by the step that uses it: `system-facts.md` (estate
    facts, before drafting), `cf-snippets.md` (the Cloudflare MCP calls, at write time),
    `crosscheck-prompt.md` (prompt shape, at draft time), `d1-schema.sql` (the write contract —
    lets a failed INSERT be self-corrected against the CHECK constraints without a round trip,
    and matches the sibling D1-writing skills).
  - Corrected a pointer in `system-facts.md` that named a file no longer shipped with the skill.

## [0.20.0] — 2026-07-23

### Changed
- **`iam-access-request`: reference files are now split by audience and lifetime**, not by topic.
  `references/deployment.md` had become a mix of durable estate facts, operator procedure and
  dated status, which made every part of it harder to trust.
  - **`references/system-facts.md`** (new, replaces `deployment.md`) holds **only** facts that
    change what a draft should say: account ids, what runs where, the placement rule, regions,
    CloudTrail location. It states its own inclusion rule at the top — *a fact belongs here only
    if not knowing it would make a draft wrong, and only if it will still be true in six months
    without anyone editing it.*
  - **Status moved out.** The `ProwlerScanRole` unverified-permissions warning and the note that
    the AWS MCP proxy has no read-only mode are current state, not facts, and now live in a dated
    *Current state* section of `references/discovery-setup.md`. The read-only rationale moved
    there too, as *Why read-only*.
  - Why it matters: a stale estate note produces confidently wrong drafts, which is the exact
    failure this skill exists to prevent. Mixing durable facts with dated status is how notes go
    stale.
  - The pattern is recorded in the Obsidian component note (`Architecture Description/IAM Access
    Request`) so future work on this skill follows it: for any new reference file, ask who reads
    it and how long it stays true.

## [0.19.1] — 2026-07-23

### Changed
- **`iam-access-request`: split the deployment note by audience.** It had grown to serve two
  readers at once — the skill, which reads it before every draft, and an operator standing up the
  discovery identity. The setup procedure now lives in `references/discovery-setup.md`, written
  for an experienced engineer: commands first, and only the non-obvious constraints spelled out
  (management deploys first because a trust policy resolves its principal ARN at save time;
  `ExternalId` only if the connector can send one; the access key out of band; keys before stacks
  on teardown).
- **`references/deployment.md` trimmed 146 → 84 lines**, keeping what shapes a draft (accounts,
  what runs where, the placement rule and its two-identity corollary) and reducing the read-only
  discussion to the rule, the pointer, and the `ProwlerScanRole` warning.
  - **Fixed a contradiction**: the header still said `management` was unconfirmed while the table
    listed `088420203827`.

## [0.19.0] — 2026-07-23

### Changed
- **`iam-access-request`: the two discovery templates are now one.**
  `discovery-hub-user.yaml` and `discovery-role.yaml` are replaced by
  `references/discovery-setup.yaml`, deployed once per account. `CreateHubUser=true` (management
  only) creates the hub user **and** the role, wiring the role's trust policy to the user with
  `!GetAtt` — CloudFormation infers the dependency and orders the two itself, so no ARN is copied
  by hand and the deploy-order trap fixed in 0.18.1 cannot recur. The other three accounts deploy
  the same file with `CreateHubUser=false` and the ARN as a parameter.
  - **Why one file rather than two:** two templates each defining the same role is two things to
    keep in step. One definition cannot drift from itself.
  - **Why the other accounts still need a parameter:** a stack acts on a single account and
    region, `!GetAtt` cannot cross that boundary, and cross-stack `Export`s are account and
    region scoped as well. Documented **StackSets** as the way to automate the fan-out without
    changing the template.
  - **No dependency cycle:** the role's trust policy references the user with `!GetAtt`, while the
    user's policy builds the role ARNs with `!Sub` from account ids. Using `!GetAtt` in both
    directions would deadlock the stack, and three of the four roles are in other accounts
    anyway.
  - Guardrails, the optional `ExternalId`, and the refusal to create an access key in
    CloudFormation are unchanged.

## [0.18.1] — 2026-07-23

### Fixed
- **`iam-access-request`: the documented deploy order was backwards and would have failed.** Both
  `discovery-hub-user.yaml` and `references/deployment.md` said to deploy the target roles before
  the hub user. IAM resolves a trust policy's `Principal` ARN to that principal's unique id when
  the policy is saved, so a role naming a user that does not exist yet fails with
  `MalformedPolicyDocument: Invalid principal in policy`. Corrected to **hub user first, then the
  roles**, with the failure named so the next reader understands why the order is not arbitrary.
  The reverse dependency is harmless: the user's identity policy may reference role ARNs that do
  not exist yet.

## [0.18.0] — 2026-07-23

### Added
- **`iam-access-request`: `references/discovery-hub-user.yaml`** — the management-account half of
  the discovery pair, matching the operator's chosen design: one IAM user in `management` whose
  access keys configure the AWS MCP connector, assuming a read-only role in each target account.
  - **The user holds no permissions of its own.** `sts:AssumeRole` on exactly four role ARNs
    (one per account, listed explicitly so a same-named role in an unrelated account is not
    reachable) plus `sts:GetCallerIdentity`, and an explicit `Deny` with `NotAction` on
    everything else. A leaked key therefore grants read-only discovery and nothing more, and
    stays that way even if `AdministratorAccess` is attached to the user later.
  - **The template deliberately does not create the access key.** `AWS::IAM::AccessKey` writes
    the secret into the stack's outputs and state, readable by anyone with
    `cloudformation:DescribeStacks`. The key is created out of band and pasted straight into the
    connector.

### Fixed
- **`discovery-role.yaml`: a mandatory `ExternalId` could have bricked discovery.** The trust
  policy required `sts:ExternalId` unconditionally, but the AWS MCP connector may have no way to
  send one — in which case every `AssumeRole` fails and discovery is dead on arrival. It is now
  optional: an empty value omits the condition entirely, via a CloudFormation `Condition` and
  `AWS::NoValue`. A `StringEquals` against `""` would have been unsatisfiable and would have
  locked the role permanently.

### Changed
- **`references/deployment.md`** documents both halves, the deploy order (roles, then hub user,
  then the key by hand), and why the key never goes in CloudFormation.

## [0.17.1] — 2026-07-23

### Changed
- **`iam-access-request`: recorded the estate placement rule.** Roles that a management tool or
  shared service runs as (Grafana, Prowler, Prometheus, Wazuh, Pritunl, OpenVPN) live in the
  **`management`** account, never in an environment account. A draft that would put a tooling
  identity in `development` / `uat` / `production` is in the wrong account and must say so in
  `assumptions_md`.
  - Documented the corollary, which is where drafts usually go wrong: reaching *into* an
    environment account is **two** identities, not one — the tool's own identity in `management`
    plus a per-account role in the target account trusting it. So `ProwlerScanRole` sitting in
    `development` is the target side of that pair, not a violation. What must never sit in an
    environment account is the tool's own identity or long-lived keys for it.
- **`management` account id recorded**: `088420203827`. No `<PLACEHOLDER>` account ids remain in
  `references/deployment.md`.
- **`discovery-role.yaml` now enforces the rule.** `TrustedPrincipalArn` carries an
  `AllowedPattern` pinning it to `088420203827`, so CloudFormation rejects a principal outside
  `management` at deploy time rather than leaving it to reviewer attention. The role the stack
  creates is the target side of the pair and still deploys per account.

## [0.17.0] — 2026-07-23

### Added
- **`iam-access-request`: `references/discovery-role.yaml`** — a CloudFormation template for
  `SOCDiscoveryReadOnlyRole`, the read-only role the discovery connector should assume. Deploy
  once per account. Drafted, not applied; applying it is a human action, per the skill's own
  rules.
  - Grants **`ViewOnlyAccess` + `SecurityAudit`** (verified against the AWS managed-policy
    reference: "view resources and basic metadata" and "read security configuration metadata").
    Both are maintained by AWS as new services launch, so the role does not rot.
  - **Deliberately not `ReadOnlyAccess`**, which permits data-plane reads such as `s3:GetObject`.
    Discovery needs resource *names and ARNs*, never resource *contents*.
  - **Explicit `Deny` on IAM writes** by verb wildcard rather than a list of API names, so a
    newly launched IAM action cannot fall outside the guardrail. Covers all eight known direct
    privilege-escalation actions plus `iam:PassRole`, which combined with a create call on a
    compute service escalates to any passable role in the account.
  - **Explicit `Deny` on secret and data reads.** Discovery evidence is uploaded to the SOC
    dashboard and rendered on a request page, so anything the agent can read can end up stored
    and displayed to reviewers.
  - **Explicit `Deny` on `sts:AssumeRole`**, making the role a leaf that cannot chain into a more
    privileged one. An explicit `Deny` beats any inherited `Allow`, so the guardrail survives
    someone later attaching a broad policy to this role.
  - Trust policy is parameterised and requires an `ExternalId` (confused-deputy protection);
    `MaxSessionDuration` is 1 hour. A `VerifyCommand` output prints the read-only
    `simulate-principal-policy` check to run after deploying.

### Changed
- **`iam-access-request`: real account ids recorded** in `references/deployment.md` —
  `development` `824155916596` (confirmed from a live `sts get-caller-identity`), `uat`
  `477088859175` and `production` `379495554125` (operator-supplied). `management` remains
  `<PLACEHOLDER>`.
- **Flagged that discovery currently runs as `ProwlerScanRole`** in `development`, whose
  permissions are unverified. It belongs to the withdrawn Prowler scan pipeline, so its
  permissions will drift for reasons unrelated to this skill. Note says to verify with
  `simulate-principal-policy` before pointing discovery at `uat` or `production`.

## [0.16.2] — 2026-07-23

### Security
- **`iam-access-request`: hardened against the agent performing an actual IAM write.** The
  0.16.0 skill relied on three lines of prose ("you never grant"), which is guidance, not a
  control. Added a prominent **Hard limits** section up front:
  - An explicit **deny list of AWS write APIs** (`iam:Create*`, `Put*`, `Attach*`, `Update*`,
    `Delete*`, `Detach*`, `Add*`, `Remove*`, `Tag*`, `CreateAccessKey`,
    `UpdateAssumeRolePolicy`, `CreatePolicy*`, plus write families on other services and
    `sts:AssumeRole` into a more privileged role) — the prohibition is on the **effect**, by any
    route: MCP, Bash, a script, or a snippet handed to the user to paste.
  - **Never run the `aws` CLI from Bash, in any environment.** The old text leaned on "the
    sandbox has no AWS egress", which is true of the Cowork sandbox and **false on an operator's
    laptop**, where a live SSO session puts `aws iam create-role` one command away. An
    environment's egress limits are not a safeguard the skill may depend on.
  - **Never execute the setup guide.** The `guide` subcommand has the agent author the exact
    `aws iam create-role …` commands that perform the grant, so "shall I run these?" is the most
    likely path to an accidental write. Writing them is the deliverable; running them is the
    thing the skill exists to prevent.
  - **Confirm `READ_OPERATIONS_ONLY=true` before discovery, or stop** — the skill cannot set
    that connector flag itself, so it must refuse rather than proceed write-capable. Discovery
    is further restricted to `describe-*` / `list-*` / `get-*` / `lookup-*`.
  - Stated plainly that **the skill enforces nothing** — a `SKILL.md` gives instructions, not
    permissions — so nobody mistakes it for the guarantee.
- **`references/deployment.md`: documented the control that does enforce it.** Discovery must
  run under a read-only role (`ReadOnlyAccess` / `SecurityAudit`) or a profile carrying an
  explicit `Deny` on the IAM write actions, since an explicit `Deny` beats an inherited admin
  `Allow`. Also records why a **permission boundary on the drafted role does not help**: it
  bounds what the new identity can do, not what the agent can do while drafting it.

## [0.16.1] — 2026-07-23

### Fixed
- **`iam-access-request`: plugin validation rejected the skill description.** It used
  `<id>` as a placeholder for a request id, and the validator reads anything in angle brackets
  as an XML tag (`SKILL.md description cannot contain XML tags`), so the whole plugin failed to
  install. Rewritten as prose. Angle brackets in the skill *body* and its reference files
  (`<PLACEHOLDER_NAME>`, `<UUID>`) are unaffected — the rule applies only to frontmatter
  descriptions. The other six skills were checked and none used the pattern.

## [0.16.0] — 2026-07-23

### Added
- **New skill `iam-access-request`.** Turns an AWS access request from Slack or Jira into a
  reviewed, least-privilege IAM suggestion on the SOC dashboard: draft → read-only discovery →
  unanimous human approval → setup guide. Three subcommands (draft, `discovery`, `guide`),
  writing `iam_requests` in the new D1 `iamreq` via the Cloudflare MCP.
  - **The skill drafts and evidences; it never grants.** It writes no AWS state at any point —
    discovery is read-only through the awslabs `aws-api-mcp-server` with
    `READ_OPERATIONS_ONLY=true`, and the guide is a document a human applies.
  - **It also never approves.** No write to `iam_reviews` or `status`; approval is a human act
    in the dashboard, where the reviewer's identity comes from the Access JWT. A skill-written
    review would defeat the control the feature exists to provide.
  - **Unresolved identifiers stay `<PLACEHOLDER>` and are never guessed** — a plausible-looking
    wrong ARN in an IAM policy is worse than an obvious gap, because the gap gets fixed and the
    wrong ARN gets applied. `discovery` resolves them against the real estate and is re-runnable.
  - **The cross-check prompt is self-contained and answered elsewhere.** It embeds the request,
    policy, assumptions and evidence inline so an external model needs no other context, and it
    asks to be run in a *different* model than the one that drafted the policy — a model
    reviewing its own output agrees with itself. The verdict is pasted back by the reviewer;
    the platform deliberately holds no model credentials.
  - Org topology lives in `references/deployment.md` bundled with the skill, not in D1 — it
    changes with the estate, is read by an LLM rather than queried, and the dashboard has no use
    for it. Account ids ship as `<PLACEHOLDER>` for an operator to fill in.

### Changed
- **Docs: rewrote `README.md` for readability.** Restructured into a quick-start plus a
  scannable skills table, documented the two previously-missing skills (`aws-firewall-review`,
  `pentest-job-runner`), consolidated required connectors into a table, and refreshed the
  project layout. No behavior change.
- **Docs: dropped stale `MAINTAINERS.md` references.** The `MAINTAINERS.md` files no longer
  exist; removed the pointers to them from `README.md` and the `CHANGELOG.md` preamble. The
  `CHANGELOG.md` is now the single place for both what changed and why. No behavior change.

## [0.15.0] — 2026-07-13

### Added
- **`aws-firewall-review`: dashboard status hooks + Confluence auto-publish.** New *Status
  reporting* section: on a full quarterly review the skill now pushes one row per quarter to the
  SOC dashboard's D1 database `fwreview` (id `78dde69f-cc9a-4b43-a265-03ae835fbc8c`) via the
  Cloudflare MCP (best-effort — a failed emit never blocks the review). The row carries `status`
  (running/done/failed), a separate `assessment` (EFFECTIVE/PARTIALLY EFFECTIVE/NOT EFFECTIVE
  from the render rules), summed HIGH/MEDIUM/LOW + SG counts, and an `accounts_json` with each
  account's counts, per-account assessment, Confluence link, and full `findings[]` (stable F-NNN
  ids) — backing the dashboard's per-account cards and combined severity-sorted findings table.
  The render step now also **auto-publishes** to Confluence (a quarter parent page + one child
  page per account under the `AWS Firewall Review Report` folder, id `312508532`, in the
  `pavewiki` space) and records each child's `webUrl`; publish failure is non-fatal. Backs the
  "Firewall review" dashboard page. Ships `references/cf-snippets.md` (exact
  `mcp__cloudFlare__execute` calls) and `references/d1-schema.sql`.

## [0.14.0] — 2026-07-13

### Added
- **`daily-security-report`: dashboard status hooks.** New *Status reporting* section: the skill
  now pushes each run's pipeline status and per-source security posture to the SOC dashboard's D1
  database `dailyreport` via the Cloudflare MCP (best-effort — a failed emit never blocks the
  report). One upserted row per report date carries `status` (running/done/halted/failed) and a
  separate `severity` (info/low/medium/high/critical, reused from the Tier 3 findings table) plus
  a per-source `sources_json` (`{name,severity,count,note}`). Backs the "Daily security health"
  dashboard page (D1 `dailyreport`, id `1c97153d-d9ba-4c7c-ab27-73029e5684e1`). Ships
  `references/cf-snippets.md` (exact `mcp__cloudFlare__execute` calls) and
  `references/d1-schema.sql`.

## [0.13.0] — 2026-07-12

### Added
- **New skill `pentest-job-runner`.** A generic harness that drains the Cloudflare pentest job queue
  and runs one `webapp-pentest` per tick: reconciles crashed runs, acquires a single-machine D1 lock,
  pulls a job (via the Cloudflare MCP), drives `webapp-pentest`, uploads the report to R2, writes the
  terminal status to D1, and acknowledges the message. Backs the self-service pentest dashboard
  (D1 `pentest`, queue `pentest-jobs`, bucket `pentest-reports`). Ships `references/cf-snippets.md`
  (exact `mcp__cloudFlare__execute` calls) and `references/d1-schema.sql`.
- **`webapp-pentest`: dashboard status reporting.** New *Status reporting* section. In automated mode
  (the invocation carries `job_id`/`d1`), the Leading agent emits a free-text `phase` at each step
  boundary (`scoping`/`recon`/`exploit`/`pivot`/`reporting`) to D1 via the Cloudflare MCP, bumps the
  runner-lock heartbeat, and returns the report path for R2 upload. Best-effort (never blocks the
  pentest) and gated on a passed `job_id`; interactive runs are unchanged and emit nothing.

### Fixed
- **`webapp-pentest`: description length.** Trimmed the `SKILL.md` frontmatter `description` to stay
  under the 1024-character plugin-validation limit (it had exceeded the limit since the 0.12.0
  subcommand refactor, failing `.plugin` packaging). Trigger phrases and invocation forms preserved.

## [0.12.0] — 2026-07-08

### Added
- **`webapp-pentest`: stage subcommands.** The engagement can now run **one stage at a time** as well
  as end-to-end. `/webapp-pentest <url>` (no subcommand) still runs the whole pipeline; the new
  `/webapp-pentest scope`, `/webapp-pentest recon`, and `/webapp-pentest exploit` each run a single
  stage. Stages share a per-engagement state directory in the workspace folder
  (`webapp-pentest-<slug>/`) — `scope` writes `engagement.json`; `recon` writes `sitemap.json`,
  `targets.json`, `session.json`; `exploit` writes `exploit-results.json`, the PoC artifacts, and the
  final report. A subcommand resolves the engagement from its `[url]` arg or the most recent
  `engagement.json`, reads the prior stage's artifacts (stopping with a clear message if absent), and
  re-checks the recorded authorization before touching the target. Raw credentials are never
  persisted.

### Changed
- **`webapp-pentest`: four-role team → three-role team.** Removed the separate **Report-review**
  agent. Its two jobs are redistributed: the **Recon agent** (renamed from *Threat-hunting*) now owns
  **crawl + sitemap + target-marking** — it emits the exploit-target list (each item with a
  `success_criteria` and `non_destructive_bound`) directly from the crawl, so the standalone triage
  pass is gone; and the **Leading agent** now **writes the final report** itself. The pivot loop is
  now **recon → exploit → pivot-review** (was crawl → triage → exploit → pivot-review); the
  authorization gate, non-destructive rules, and 3-round cap are unchanged. Updated `SKILL.md`,
  `references/agent-team.md`, `references/burp-recon.md`, `references/exploit-agent.md`,
  `references/owasp-checklist.md`, the report template, and the README.

## [0.11.0] — 2026-07-07

### Changed
- **`webapp-pentest`: replaced ZAP with Burp Suite + a real-browser crawl.** The discovery half of
  the skill no longer uses an automated scanner. The Threat-hunting agent now **crawls the target in
  a real browser (Claude in Chrome) routed through Burp**, then builds the sitemap/attack surface
  from **Burp's proxy history** (`get_proxy_http_history`), and the Exploit agents craft and replay
  HTTP requests through the **Burp MCP** (`send_http1_request`/`send_http2_request`, Intruder/Repeater
  handoff, encode-decode helpers) instead of running Python PoCs in the sandbox. Benefits: the whole
  pipeline runs on the user's **local** Burp + browser, so local/LAN/tunnel targets work with no
  egress-allowlist/new-session dance and **no local-runner fallback**; login-gated targets are
  handled by logging in through the real browser form (capturing the session in Burp history), which
  **eliminates the ZAP re-auth/redirect loop**; and HTTP/2 testing is now native. Trade-off: no
  automated passive/active scan — **vulnerability detection is agent-driven**, so a **proxy-wiring
  preflight** (Chrome → Burp `127.0.0.1:8080` + trusted CA) is required or discovery finds nothing.
  Replaced `references/zap-scanning.md` with `references/burp-recon.md`; rewrote `SKILL.md`,
  `references/agent-team.md`, `references/exploit-agent.md`, `references/owasp-checklist.md`, and the
  report template. Pivot loop and authorization gate unchanged. Updated README and plugin manifest
  (ZAP → Burp Suite + Claude in Chrome).

## [0.10.0] — 2026-07-07

### Added
- **`webapp-pentest`: iterative pivot loop.** The engagement is no longer a single linear pass —
  when an Exploit agent confirms a vulnerability, it now reports a **`new_access`** list of resources
  the exploit unlocked (new endpoints/paths, admin/API surface, escalated role/session, revealed
  internal hosts, recovered credentials). A new **pivot-review** stage (Step 4.5, run by the Leading
  agent) unions and **filters that access to the confirmed scope**, then loops back to the ZAP scan
  on the newly reachable resources — threading any elevated session/credentials as updated auth
  context — so the scan → triage → exploit cycle repeats and follows access deeper. The loop
  terminates when a round surfaces **no new in-scope resources** or after a hard **iteration cap
  (default 3 rounds)**. Out-of-scope resources discovered via an exploit are **logged and skipped**,
  never followed — the loop widens coverage within scope, never the scope itself. The final report
  now includes an **attack-path / pivot narrative** (which exploit unlocked what, round by round) and
  notes any in-scope surface left untested when the cap was hit. Updated `SKILL.md`,
  `references/agent-team.md`, `references/exploit-agent.md`, and `template/pentest-report-template.md`.

## [0.9.0] — 2026-07-06

### Added
- **`webapp-pentest`: sandbox reachability preflight + local-runner fallback.** The Leading agent
  now preflights the target from the sandbox (`curl` for an HTTP status) in Step 1, and each Exploit
  agent re-checks before attacking. If the target is blocked by the egress allowlist (local/LAN
  hosts, un-allowlisted `*.trycloudflare.com` tunnels), the Exploit agent no longer fails — it emits
  a stdlib-only **local runner** into the workspace folder that the user runs on their host, writing
  results back for Claude to read. Verdict in that case is **Inconclusive (pending local run)**.
  Documents that allowlist changes only take effect in a **new session** and that tunnel URLs are
  ephemeral. Verified live against a DVWA tunnel once allowlisted.
- **`webapp-pentest`: authenticated-context support for login-gated targets.** New optional **auth**
  input (login URL, user-supplied credentials, session mechanism, anti-CSRF field, any level/mode to
  set). The Leading agent collects it (Step 1.3), the Threat-hunting agent configures an
  **authenticated ZAP context** (login method, logged-in/out indicators, active user, logout
  excluded) so the spider/active scan cover post-login pages, and each Exploit agent **logs in
  first** — scraping any anti-CSRF token, detecting and setting required app state (e.g. DVWA
  `security` level) rather than hard-coding it — before attacking authenticated endpoints. Verified
  end-to-end against DVWA's authenticated SQLi module (UNION-based extraction of DB version + a
  targeted credential row, non-destructive).

## [0.8.0] — 2026-07-01

### Added
- **New skill: `webapp-pentest`.** Runs an authorized web-application penetration test as a
  four-role **agent team** and returns a consolidated report. A **Leading agent** (the orchestrator
  context) scopes the target with the user and builds an **OWASP Top 10 (2025)** checklist; a
  **Threat-hunting agent** subagent drives the **ZAP MCP** (`mcp__zap__*`: context → spider → AJAX
  spider → passive-queue drain → active scan → report) and exports normalized findings; a
  **Report-review agent** subagent triages findings into an exploit-target list, each item carrying
  full context plus a checkable `success_criteria`; and **one Exploit agent subagent per target**
  writes and runs non-destructive Python PoCs (sandboxed shell) until the criterion is met or
  approaches are exhausted. Report-review then writes the final report. Roles run as real subagents
  (mirrors `alert-triage`); the orchestrator owns the parse/aggregate/fan-out glue. Invoked
  `/webapp-pentest <target-url>`. OWASP 2025 category list verified against owasp.org.
- **`webapp-pentest`: mandatory authorization gate.** No spider/scan/exploit runs until the user
  confirms in-scope target(s) and explicit authorization (Step 1.2). Once confirmed, scanning and
  in-scope PoC execution are **auto-approved** (no per-step confirmation) but bounded to
  **non-destructive**, in-scope actions — no data destruction/exfiltration, persistence, DoS, or
  out-of-scope pivoting. Files (report, ZAP export, PoC scripts) are written to the workspace only;
  no external publish step.
- **New required connector: ZAP** (`mcp__zap__*`) for `webapp-pentest`.

## [0.7.0] — 2026-06-26

### Added
- **New skill: `aws-firewall-review`.** Generates the DLVN/PAVE quarterly AWS firewall
  configuration review. Collects all AWS security groups across every enabled region, applies
  deterministic risk analysis (internet-exposed sensitive ports, wide CIDR ranges, permissive
  egress), then renders a findings-focused markdown report from the DLVN-SEC-TPL-002 template.
  The collect and render halves can run independently. Registered in the plugin description.
- **`aws-firewall-review`: Dockerised MCP collector.** Collection runs through the
  `aws-firewall-review` MCP server (stdio, launched via `docker run -i`) instead of a standalone
  CLI. The container reads the host's `~/.aws` mounted read-only, so credentials never pass
  through chat. Tools: `collect_security_groups(profiles?, regions?, workers?)`,
  `list_aws_profiles()`, `whoami(profile?)`. The server source lives in the `mcp_server/`
  directory at the project root, kept separate from the plugin so the skill source stays clean.
- **`aws-firewall-review`: SSO + multi-account, all-or-nothing.** `collect_security_groups`
  defaults to the standard review set — `development`, `uat`, `production` — resolving SSO cached
  tokens natively, and returns one evidence object per account under `accounts[]`. Every profile
  is authenticated up front; if any fails (e.g. an expired SSO session) the tool errors before
  collecting anything and returns the `aws sso login --profile <name>` command to fix it. No
  account is skipped, so a multi-account review is never partial. Pass `profiles=[]` for
  environment / assume-role credentials.

### Removed
- **`aws-firewall-review`: standalone CLI and n8n coupling.** The `scripts/query_security_groups.py`
  CLI is replaced by the MCP server (shared logic now in `mcp_server/collector_core.py`). Dropped
  all n8n-specific framing from the skill, references, and template (the `<<...>>` placeholder
  syntax remains, as it still avoids `{{ }}` templating collisions). Default assume-role session
  names use a `dlvn-` prefix.

## [0.6.0] — 2026-06-24

### Added
- **`track-user`: final human-friendly readable report.** After building the technical timeline
  log, the skill now re-reads it and rewrites it as a plain-language narrative (Step 6, before
  report-back). Actions are **decoupled** — one "User …" sentence per line stating intent and
  outcome (denials/errors included), identifiers inline. Saved as
  `UA-<user>-<window_id>-readable.md` and presented as the final deliverable; the technical log
  becomes the working artifact. New contract in `references/readable-report.md`.

### Fixed
- **`track-user`: timeline entries now render as separate lines.** Both format specs
  (`timeline-format.md`, `readable-report.md`) now require a blank line between every entry (and
  between the readable report's two header lines). Without it, Markdown collapsed the timeline
  into one run-on paragraph.
## [Unreleased]

### Added
- **CI: SkillSpector security scan.** New `.github/workflows/skillspector.yml` runs NVIDIA
  SkillSpector against the repo on push, pull request, and manual dispatch. Static-only
  (`--no-llm`) SARIF scan; findings render to the GitHub Actions job summary, upload as an
  artifact, and publish to code scanning.

## [0.5.1] — 2026-06-24

### Docs
- **Consolidated all change history into this `CHANGELOG.md`.** Removed the `## Changelog`
  section from every `MAINTAINERS.md` (plugin root + `daily-security-report`, `alert-triage`,
  `track-user`) and updated their "every change appends a line to the Changelog below" rule to
  point here instead. MAINTAINERS.md files now hold intent and decisions only. Updated
  `ARCHITECT.md` accordingly. Docs-only; no behavior change.

## [0.5.0] — 2026-06-24

### Changed
- **`daily-security-report`: source malfunction now halts the run.** A source whose collection
  errors/times out **or returns zero hits** is treated as malfunctioning and stops the workflow
  (was "note it and continue"). Interactive runs ask the user (continue-without / retry / abort);
  scheduled runs skip publishing. Zero hits counts as a malfunction because, for these sources,
  an empty day usually means stalled ingestion (cf. the 2026-06-19 stall).
- **`daily-security-report`: scheduled runs auto-approve publishing.** A Cowork scheduled /
  non-interactive run now auto-approves the Step 4 publish gate and distributes the report —
  but only when every source was healthy (previously scheduled runs never published). The
  malfunction halt always overrides auto-approval. Interactive runs are unchanged (explicit
  approval still required).

### Added
- **`daily-security-report`: scheduled-halt maintainer DM.** When a scheduled run halts on a
  malfunction, it DMs the maintainer (`huy.nguyen@discoveryloft.com`, resolved via
  `slack_search_users`) a minimal brief — report id + date, halted/nothing-published status, and
  the malfunctioning source(s) with the reason. Template lives in
  `skills/daily-security-report/references/publishing.md`.

## [0.4.0] — 2026-06-22

### Added
- **`track-user` skill.** Single-user, read-only AWS activity tracker. Given a **named** user and
  a window (default last 7 days; also accepts a day count or an explicit `YYYY-MM-DD` range), it
  queries Control Tower CloudTrail (`aws-controltower/CloudTrailLogs`, `ca-central-1`) via the
  CloudWatch MCP for the user's sign-ins, mutating actions (`readOnly = 0`), and errors, then
  assembles a chronological **UTC+7 timeline log** saved as Markdown in the workspace folder.
  Invoked `/track-user <username> [window]`. Requires a named user — never runs org-wide — and
  makes no external writes (no confirmation gate needed). New helper `scripts/activity_window.py`
  (UTC+7 window calc). Reuses the CloudTrail gotchas documented for the daily report's AWS source.
  (Initially named `user-activity`; renamed to `track-user` the same day.)

## [0.3.0] — 2026-06-22

### Added
- **`daily-security-report`: AWS user activity source.** Added a fourth monitored source
  covering AWS Control Tower CloudTrail, queried via the CloudWatch MCP
  (`awslabs.cloudwatch-mcp-server` → `execute_log_insights_query`, region `ca-central-1`, log
  group `aws-controltower/CloudTrailLogs`). Collects the day's mutating actions
  (`readOnly = 0`) across all users plus console sign-ins; analysis groups changes by identity
  (resolved from the role-session-name in the CloudTrail ARN) and flags security-sensitive
  changes. Verified against the live log group during build.

### Changed
- **`daily-security-report`: generalized the source registry with a per-source `backend`
  field** (`opensearch` | `cloudwatch`). `search_after` pagination is now scoped to the
  opensearch backend; cloudwatch sources use `execute_log_insights_query` with an explicit
  `limit`. Both reuse the same UTC+7 window from `report_period.py`. Wired the new source into
  the Tier 3 report template, the Tier 2 Slack Cyber section, and the Confluence child pages.
- **`daily-security-report`: scoped the AWS source to human identities** with a load-bearing
  `userIdentity.arn like /discoveryloft.com/` filter. A 2026-06-21 dry run showed the
  unfiltered query returns 83,578 rows/day of service-principal automation vs 5 human-activity
  rows with the filter. Caveat (excludes direct IAM-user/root logins) documented inline in the
  source entry.

## [0.2.0] — 2026-06-21

### Added
- **`alert-triage` skill.** Ported the n8n "Tier-1 operator" agent chain
  (Investigator → Query agent → Threat Hunter) as real subagents. Input by alert id; full-alert
  fetch via the OpenSearch MCP; TP/FP verdict returned in chat (no Slack). Includes an optional
  ISO 27001 incident report drafted locally then published to Confluence (parent `223773037`)
  behind a confirmation gate.
- **Incident report template.** Replaced the hand-authored template with
  `template/incident-report-template.md`, transcribed verbatim from the official PAVE incident
  report PDF (`OPENAPI-INC-2026-001`). `references/incident-report.md` reduced to field-derivation
  guidance.
- **Verdict-driven follow-up (alert-triage).** Trial run on alert `1781758278.30199963`
  (RDP, rule 92658) confirmed the chain end-to-end (False Positive). Step 5 now branches on
  verdict: False Positive → advisory rule-tuning recommendation, no report; True Positive /
  Inconclusive → offer the incident report.

## [0.1.0] — 2026-06-21

### Added
- **Plugin created.** `pave-soc` container for SOC operations skills; skills auto-discovered as
  `pave-soc:<name>` and invoked as `/<name>`.
- **`daily-security-report` skill.** Ported from the n8n "Daily security report" workflow
  (HTTP → MCP via OpenSearch/Atlassian/Slack). GCP audit/cloud branches dropped. UTC+7 windowing
  via `report_period.py`; `search_after` pagination; `physical_count.py` ported.

### Changed
- Fixed Physical `_source.excludes` to add `@timestamp` + `timestamp`, matching the original n8n payload.
- Added optional `YYYY-MM-DD` date parameter to `daily-security-report` (defaults to yesterday).
- Adopted option-3 slash convention plugin-wide (skill name is the slash trigger; no `commands/`
  directory). Removed the separate `/daily-report` command.

### Security
- Added a mandatory pre-publish confirmation gate before any external write (Confluence/Slack).
  `daily-security-report` Step 4; established as a plugin-wide rule for all side-effectful skills.
