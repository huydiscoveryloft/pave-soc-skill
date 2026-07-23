# DLVN / PAVE AWS estate — system facts

Durable facts about the estate that change what an IAM draft should say. Read before drafting.

> **What belongs in this file:** a fact that would make a draft *wrong* if the skill did not know
> it — an account id, where a service runs, a placement rule, a region, a naming convention.
>
> **What does not:** current state, status, open items, migrations in flight, verification
> results, anything with a date on it, and anything about how the skill or its tooling is
> operated. Those belong in the SOC Platform notes or the infrastructure repo, not here. A fact in
> this file should still be true in six months without anyone editing it.
>
> Account ids are safe to store. Access keys, secret keys and external ids are not, and must never
> appear here.

## Accounts

| Profile | Purpose | Account id |
|---|---|---|
| `management` | Shared tooling and security services | `088420203827` |
| `development` | Development workloads | `824155916596` |
| `uat` | UAT / staging workloads | `477088859175` |
| `production` | Production workloads | `379495554125` |

Profile names match the ones `aws-firewall-review` collects. Never guess an account id — confirm
with `sts get-caller-identity` and record it here.

## What runs where

`management` hosts the shared tooling: **Grafana** (dashboards and FinOps; reads CUR through
Athena), **Pritunl** and **OpenVPN** (VPN; OpenVPN access logs feed the daily security report),
**Wazuh** (SIEM behind `daily-security-report` and `alert-triage`).

`development` / `uat` / `production` hold the application workloads. A request naming an
environment almost always means one of those; a request about dashboards, monitoring, VPN or
logging almost always means `management`.

## Placement rule — tooling identities belong in `management`

**A role that a management tool or shared service runs as lives in `management`, never in an
environment account.** Grafana, Prowler, Prometheus, Wazuh, Pritunl, OpenVPN and that family. A
request that would put a tooling identity in `development` / `uat` / `production` is in the wrong
account: draft it in `management` and say so in `assumptions_md`.

**The corollary, and where drafts usually go wrong** — reaching *into* an environment account is
two identities, not one:

| Identity | Lives in | Purpose |
|---|---|---|
| The tool's own identity (`prowler-hub`, Grafana's service role) | `management` | What the tool authenticates as |
| The per-account access role (`ProwlerScanRole`, a CUR read role) | the target account | What the tool assumes to read there |

A per-account role in `development` is therefore the target side of the pair, not a violation.
What must never sit in an environment account is the tool's *own* identity, or long-lived keys for
it.

That shape is also the answer for most cross-account requests: a role in the data's account with a
trust policy naming the `management` principal — not a user, and not credentials copied across.

## Regions and logging

- Primary region is `ap-southeast-1`. Confirm per resource during discovery; some services are
  elsewhere.
- CloudTrail is aggregated in Control Tower at `aws-controltower/CloudTrailLogs` in
  `ca-central-1`. Relevant to any request about reading audit logs; the `track-user` skill already
  queries that log group.
