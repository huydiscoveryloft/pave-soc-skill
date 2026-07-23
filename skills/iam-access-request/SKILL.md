---
name: iam-access-request
description: Turn an AWS access request from Slack or Jira into a reviewed, least-privilege IAM suggestion on the SOC dashboard, then generate its setup guide once approved. Invoke with /iam-access-request followed by a Slack permalink or Jira key (e.g. /iam-access-request PDO-286), or a subcommand — "/iam-access-request discovery" plus a request id to resolve placeholder ARNs against the real AWS estate, "/iam-access-request challenge" plus a request id or the path to a downloaded challenge briefing to answer questions about a request (can this role reach production, what is the blast radius if its credentials leak, is there an escalation path), and "/iam-access-request guide" plus a request id to write the setup guide for an approved request. Use this WHENEVER someone asks for AWS access, permissions, an IAM role, an IAM user, a policy, or "access to" an AWS resource — even if they do not say IAM — and whenever the user asks to draft, review, challenge, or assess the blast radius of an IAM policy. Drafts the identity plus a least-privilege policy, records its assumptions, emits a portable challenge briefing, and uploads the request to the dashboard where configured reviewers approve it unanimously.
---

# IAM Access Request

Turns "please give me access to X" into an auditable, least-privilege change: a drafted
identity + policy, an explicit list of what was assumed, evidence from the real AWS estate, a
briefing a reviewer can interrogate, unanimous human approval, and only then a setup guide.

```
Slack message / Jira ticket
   │  /iam-access-request <link|KEY>
   ▼
draft: identity + policy + assumptions + challenge briefing   (placeholders allowed)
   │  INSERT into D1 `iamreq` via the Cloudflare MCP
   ▼
Dashboard ▸ Cloud Security ▸ IAM access request
   │  /iam-access-request discovery <id>   ← resolve <PLACEHOLDER> ARNs, re-upload
   │  reviewer downloads the challenge briefing and interrogates it, anywhere:
   │    /iam-access-request challenge <file>  ← "can this reach production?"
   │  reviewers approve or reject in the dashboard (unanimous; one reject closes it)
   ▼  status = approved
/iam-access-request guide <id>  → policy JSON + aws cli written to guide_md
   ▼
Dashboard offers the guide as a markdown download
```

**You draft and you evidence. You never grant.** This skill writes no AWS state at any point —
discovery is read-only, and the setup guide is a document a human runs.

## Hard limits — read before doing anything

**Nothing in this skill may change AWS state. Not once, not "just to test", not because the
user asks mid-run.** If a step seems to require a write, that is the signal to stop and hand
back to a human — it is never the signal to proceed.

### Never call these, by any route

`iam:Create*`, `iam:Put*`, `iam:Attach*`, `iam:Update*`, `iam:Delete*`, `iam:Detach*`,
`iam:Add*`, `iam:Remove*`, `iam:Tag*`, `iam:CreateAccessKey`, `iam:UpdateAssumeRolePolicy`,
`iam:CreatePolicy`, `iam:CreatePolicyVersion` — and the same families on any other service
(`s3:Put*`, `secretsmanager:Put*`, `sso-admin:*` writes, and so on). Nor `sts:AssumeRole` into
a role more privileged than the operator's own session.

**"By any route" means:** the `aws-api-mcp-server` connector, any other MCP, a `Bash` call to
the `aws` CLI, a script you write, a snippet you ask the user to paste, or a Cloudflare MCP
call. The prohibition is on the *effect*, not on a particular tool.

### Never run the AWS CLI from Bash — in any environment

Discovery goes through the `aws-api-mcp-server` connector, full stop. Do **not** shell out to
`aws` even for a read, and do **not** treat "the sandbox has no AWS egress" as the safeguard —
that is true of the Cowork sandbox and **false on an operator's own laptop**, where a live SSO
session makes `aws iam create-role` a single command away. The rule holds regardless of what
the environment happens to permit.

### Never execute the setup guide

The `guide` subcommand makes you author the exact `aws iam create-role …` commands that would
perform the grant. **Writing them is the deliverable; running them is the thing this skill
exists to prevent.** Do not run them, do not offer to run them, and if the user asks you to,
decline and point at the guide — a grant is applied by a human who has read the approved
policy. This is the single most likely way an accidental write happens.

### Confirm read-only before discovery, or stop

The connector must be running with `READ_OPERATIONS_ONLY=true`. You cannot set that yourself.
If you cannot confirm it, say so and stop rather than proceeding with a write-capable
connector. Do not "be careful instead".

> **This skill cannot technically enforce any of the above** — a `SKILL.md` gives instructions,
> not permissions. The real control is on the AWS side: the profile used for discovery should be
> a read-only role, or carry an explicit `Deny` on `iam:*` writes. Treat everything here as the
> second layer, and say so if a user assumes the skill is the guarantee.

## The four subcommands

| Invocation | Does |
|---|---|
| `/iam-access-request <slack-link\|JIRA-KEY>` | Read the source, draft the request, upload it |
| `/iam-access-request discovery <id>` | Resolve `<PLACEHOLDER>` identifiers against real AWS, regenerate the policy, update the row |
| `/iam-access-request challenge <id\|file>` | Answer questions about a request from its briefing. Read-only |
| `/iam-access-request guide <id>` | **Only if `status = approved`** — write the setup guide onto the row |

If the user just says "someone needs access to X" with no link, draft from what they tell you —
`source_type` is still `slack` or `jira`, so ask which ticket or message it came from. If there
genuinely is none, ask before inventing a `source_ref`; leave it NULL rather than fabricating.

---

## 1. Draft — `/iam-access-request <slack-link|JIRA-KEY>`

### Read the source

- **Jira key** (e.g. `PDO-286`) → `getJiraIssue` via the Atlassian MCP. Read the description
  *and* the comments; the actual requirement is often negotiated in the comments, not the body.
- **Slack permalink** → `slack_read_thread` (or `slack_read_channel` around the timestamp) via
  the Slack MCP. Read the whole thread.

**Requests arrive in any language** — Vietnamese and English are both normal here. Parse intent
in whatever language it is written; write the stored request in English so reviewers share one
reading.

### Understand before drafting

Extract, and write down which of these the source actually answers:

- **Who** needs it — a person, a service, or a workload?
- **What** they need to do, in verbs, not permission names ("read the CUR files and query them
  through Athena", not "s3 and athena access").
- **Which account and region** it lives in.
- **How long** — permanent, or for a task?

Read `references/system-facts.md` for the estate layout before you decide which account anything
lives in. **Anything the source does not answer is an assumption**, and every assumption goes in
`assumptions_md` verbatim. Ask the operator about the ones that change the policy shape; record
the answers as resolved assumptions rather than deleting them — a reviewer needs to see what the
request did *not* say.

### Least-privilege rules — these are the point of the skill

1. **Prefer extending an existing team role or permission set over minting a new identity.**
   A new role is a new thing to review, rotate and eventually forget. Say explicitly in
   `assumptions_md` which existing identity you considered and why it did or did not fit.
2. **Workloads get roles with trust policies. Never IAM users, never long-lived access keys.**
   If the request literally asks for an access key, draft the role instead and explain the
   substitution in `assumptions_md`. A human can overrule that; you do not pre-concede it.
3. **Database access is not RDS API access.** "Access to the database" means a Secrets Manager
   read for the credential, or `rds-db:connect` for IAM auth, plus a network path (usually SSM
   Session Manager to a bastion). It does **not** mean `rds:*`. Granting RDS API permissions to
   someone who wanted to run a query is one of the classic over-grants.
4. **Scope every resource ARN you can.** `"Resource": "*"` is acceptable only where the API
   genuinely does not support resource-level permissions (e.g. some `glue:Get*` catalog reads) —
   and where you use it, say in a comment or in `assumptions_md` *why* it is unavoidable.
5. **Read-only unless writing was actually asked for.** Do not add `Put*`/`Delete*` "for
   convenience".
6. **Deliberate exclusions are part of the deliverable.** Note in `assumptions_md` what a
   careless draft would have included and you left out. That is what a reviewer checks fastest.

### Placeholders — never guess an identifier

Any account id, bucket ARN, workgroup ARN, role ARN, VPC or subnet you cannot confirm goes in
as a literal `<PLACEHOLDER_NAME>` — e.g. `<CUR_BUCKET_ARN>` — and is listed in
`placeholders_json`. **A plausible-looking wrong ARN in an IAM policy is worse than an obvious
gap:** the gap gets fixed, the wrong ARN gets applied. Resolve them with `discovery`, not with
inference.

### The challenge briefing

Write `challenge_prompt_md` as a **portable context bundle**, not a request for a verdict. A
reviewer downloads it from the dashboard and hands it to whatever LLM they trust, which must then
be able to answer questions about the request — *can this role reach production?*, *if the
credential leaks, what is the blast radius?*, *is there an escalation path out of here?*

That means it carries the original ask, the drafted identity and both policies, the assumptions,
the discovery evidence, the unresolved placeholders, the deliberate exclusions — **and the slice
of estate context those questions need**: which account this lives in, what else runs there, and
what trusts what. A briefing without that cannot answer a blast-radius question at all, which is
what made the first version unusable.

See `references/challenge-prompt.md` for the required shape. Tell the reader, in the opening line,
to use a *different* model than the one that drafted the policy — a model reviewing its own output
agrees with itself.

### Upload

Insert the row into D1 `iamreq` with the Cloudflare MCP — see `references/cf-snippets.md` for
the exact calls, and `references/d1-schema.sql` for the schema.

**`reviewer_snapshot` is copied from the current `iam_reviewers` table at insert time.** That
frozen set is what unanimity is measured against; later configuration edits deliberately do not
follow an in-flight request. If `iam_reviewers` is empty, stop and tell the operator to add
reviewers on the dashboard's Configuration tab first — a request with an empty snapshot can
never be approved.

Then give the user the dashboard link and a short summary of what you drafted, what you assumed,
and what is still a placeholder.

---

## 2. Discovery — `/iam-access-request discovery <id>`

Resolves placeholders against the real estate. **Read-only, always.**

- Runs through the awslabs **`aws-api-mcp-server`** connector with
  `READ_OPERATIONS_ONLY=true`, riding the operator's own AWS SSO sessions. If it is not
  connected, or you cannot confirm it is read-only, **say so and stop** — never fall back to the
  `aws` CLI over Bash. See *Hard limits*.
- **Only read verbs.** `describe-*`, `list-*`, `get-*`, `lookup-*` and nothing else. If a lookup
  seems to need a mutating call to answer, it does not — leave the identifier as a placeholder
  and say why.
- **Verify every account before you read from it:** `sts get-caller-identity` first, and check
  the returned account id against `references/system-facts.md`. Talking to the wrong account
  produces evidence that is confidently wrong.
- Keep it to **5–10 targeted calls**. This is a lookup, not an inventory sweep. Example shapes:
  `s3api list-buckets` / `s3api get-bucket-location`, `athena list-work-groups`,
  `iam list-roles --path-prefix`, `ec2 describe-vpcs`, `rds describe-db-instances`.
- Write what you ran and what came back into `discovery_evidence_md` — the command, the account,
  and the identifier it produced. A reviewer must be able to re-run it.
- Regenerate the policy with the real ARNs, shrink `placeholders_json` to whatever is still
  unresolved, and `UPDATE` the row.

**Re-runnable.** Running discovery again on the same request fills in whatever is still
unresolved and leaves the rest alone. If something cannot be resolved (the resource does not
exist yet, or nobody can say which account it will live in), leave the placeholder and say so
in `discovery_evidence_md` — do not quietly drop it from the list.

Discovery does **not** change `status`, `reviewer_snapshot`, or any review rows.

---

## 3. Challenge — `/iam-access-request challenge <id|file>`

Answer questions about a request. **Read-only, always** — this subcommand writes nothing: not D1,
not AWS, not a review. It exists so a reviewer can interrogate a proposal before approving it.

Two ways in, and both must work:

- **`challenge <request-id>`** — read the row from D1 (snippet 3 in `references/cf-snippets.md`,
  which returns `challenge_prompt_md`) and work from that.
- **`challenge <path-to-file>`** — the briefing downloaded from the dashboard. **This is the
  important one.** The point of a portable briefing is that a reviewer can run it in a session
  with no access to this estate, no Cloudflare MCP and no AWS — including a different model than
  the one that drafted the policy. If you are handed a file, work only from it and say so when it
  does not contain enough to answer.

### How to answer

Open with a two-line orientation — what identity, in which account, at what status — then take
questions. Typical ones, and what a good answer looks like:

- **"Can this reach production?"** Trace it: what the policy allows, what the trust policy lets
  assume it, whether any resource ARN or wildcard crosses an account boundary. Name the path, or
  say plainly that nothing in the briefing grants it.
- **"What is the blast radius if the credentials leak?"** Enumerate concretely — which resources,
  read or write, in which account — and separate what the identity can do *directly* from what it
  can reach by assuming something else.
- **"Is there an escalation path?"** Look for `iam:PassRole`, policy-attachment actions, `sts`
  permissions, and write access to anything that runs code with a role attached.
- **"Is this least privilege?"** Compare the granted actions against the stated need, and name
  specific statements rather than judging the policy as a whole.

**Ground every answer in the briefing.** If the answer depends on something not written there — a
resource policy, an SCP, what a bucket actually contains — say which fact is missing rather than
assuming the reassuring case. `<PLACEHOLDER>` values mean the real scope is still unknown, and any
answer about them is provisional; say that too.

**Do not soften the finding to be agreeable.** A reviewer running this is trying to find the
problem, and a challenge session that agrees with everything is worth nothing.

### After the questions

Offer to summarise what the session surfaced, in a form the reviewer can paste into the
dashboard's **Challenge findings** field on their review. Do not paste it for them and do not
submit the review — approval is theirs, made in the dashboard where the Access JWT identifies
them.

---

## 4. Guide — `/iam-access-request guide <id>`

**Refuse unless `status = approved`.** Read the row first and check. A guide for a `pending`
request invites someone to apply an unreviewed policy; for a `rejected` one it is worse. Say
plainly which status it is in and stop.

When approved, write `guide_md` (and `guide_generated_at`) containing:

1. What is being created, in one sentence, and in which account.
2. The final policy JSON, and the trust policy where the identity is a role.
3. `aws cli` commands to create it — role/policy creation, attachment, and the verification
   command that proves it worked.
4. A rollback line: how to remove what step 3 created.
5. Any placeholder still unresolved, called out at the top as a blocker rather than buried.

The dashboard picks this up automatically and offers it as a download. Do not paste the whole
guide into chat — link the dashboard and summarise.

---

## Rules that hold across all four

- **Never write AWS state, and never execute the setup guide.** See *Hard limits* above for the
  deny list and why the environment's egress restrictions are not the safeguard. The deliverable
  is always a document a human applies.
- **Never guess an identifier.** Placeholders exist for this.
- **Never modify `status`, `reviewer_snapshot`, or `iam_reviews` from the skill.** Approval is a
  human act performed in the dashboard, where the reviewer's identity comes from the Access JWT.
  The skill writing an approval would defeat the entire control.
- **Secrets never transit chat.** You will not need a credential for any of this; if something
  seems to require one, that is a sign the design went wrong — stop and say so.
- **Say what you assumed.** Every time. A policy without its assumptions is unreviewable.

## Dashboard

Requests appear at **Cloud Security ▸ IAM access request** on
`https://dashboard.aisoc.center/cloud-security/iam-access-request`. Reviewers approve or reject
there; the page shows the policy, assumptions, discovery evidence, challenge briefing, per-
reviewer status, and the guide download once generated.

## References

| File | What it holds |
|---|---|
| `references/system-facts.md` | Estate facts that change what a draft should say: accounts, what runs where, the placement rule. **Read before drafting.** Facts only — no status, no dates. |
| `references/cf-snippets.md` | Exact Cloudflare MCP calls for insert / discovery update / guide write |
| `references/d1-schema.sql` | The `iamreq` schema this skill writes (mirror of the dashboard's migration `0012`) |
| `references/challenge-prompt.md` | Required shape of the portable challenge briefing |
