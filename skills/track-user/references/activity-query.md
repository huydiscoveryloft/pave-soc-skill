# Activity Queries — Control Tower CloudTrail (single user)

How to pull one person's AWS activity for the timeline. This file is the self-contained source
of truth for the queries and the CloudTrail gotchas. **Read this before Step 3.**

## System
- **Backend / tool:** CloudWatch MCP (`awslabs.cloudwatch-mcp-server`) →
  `execute_log_insights_query`.
- **Log group:** `aws-controltower/CloudTrailLogs` — the Control Tower **organization** trail.
  One group aggregates management events from **all member accounts and all regions**
  (`awsRegion` = where the event happened, `recipientAccountId` = which account).
- **region:** `ca-central-1` — the Control Tower home region. This is **not** the MCP default
  (`us-east-1`). Wrong/omitted region → `ResourceNotFoundException`.
- **Window:** substitute `{{START}}` / `{{END}}` with `start` / `end` from
  `scripts/activity_window.py` (ISO-8601 `+07:00`). Pass them directly as `start_time` /
  `end_time`. Always include a `limit`.

## Three gotchas (each causes silent zero-match results)
1. **`readOnly` is numeric** — coerced to `1` (read) / `0` (write). Use `filter readOnly = 0`
   for mutating actions, `= 1` for read-only. `= false` or `= "0"` → **0 matches, silently**.
2. **Identity lives in the ARN, not `userName`.** For SSO (IAM Identity Center) users the human
   is the **role-session-name** at the tail of `userIdentity.arn`, e.g.
   `…/AWSReservedSSO_<PermissionSet>_<id>/huy.nguyen@discoveryloft.com`.
   `userIdentity.userName` holds the permission-set **role** name — do not filter on it. Match
   the person on `userIdentity.arn` / `userIdentity.principalId` with `like`.
3. **Some List/Get calls are tagged `readOnly = 0`** (e.g. `ListOrganizationsFeatures`, Amazon Q
   `SendMessage`). Judge significance by `eventName`, not the flag alone.

## Identity token (`<USER>`)
The skill requires a username. Derive a substring token that matches the role-session-name —
use the bare handle without assuming the domain, e.g. user `huy.nguyen` →
`<USER>` = `huy.nguyen@discoveryloft` (the trailing `.com` is optional; a substring `like`
catches both). Reuse the same identity filter in every query below:
```
filter (userIdentity.arn like /<USER>/ or userIdentity.principalId like /<USER>/)
```

## Tool call skeleton
```
execute_log_insights_query(
  region          = "ca-central-1",
  log_group_names = ["aws-controltower/CloudTrailLogs"],
  start_time      = {{START}},        # activity_window.py 'start'
  end_time        = {{END}},          # activity_window.py 'end'
  query_string    = "<a query below>",
  limit           = <see each query>
)
```

---

## Query A — Sanity check (run first)
Confirms the identity filter matches and shows the read/write split. A `0`/`0` result almost
always means a gotcha above, not a quiet week.
```
fields eventTime, readOnly
| filter (userIdentity.arn like /<USER>/ or userIdentity.principalId like /<USER>/)
| stats count(*) as cnt by readOnly
| sort cnt desc
```
limit: 20.

## Query B — Sign-ins (auth timeline)
```
fields eventTime, eventName, sourceIPAddress, recipientAccountId, awsRegion, additionalEventData.MFAUsed, responseElements.ConsoleLogin, errorMessage
| filter (userIdentity.arn like /<USER>/ or userIdentity.principalId like /<USER>/)
| filter eventName in ["ConsoleLogin","GetSigninToken"]
| sort eventTime asc
```
limit: 200. `responseElements.ConsoleLogin = "Failure"` marks a failed login. `MFAUsed: No` on
SSO logins is **expected** (MFA is enforced at the IdC portal) — do not read it as missing MFA.

## Query C — Mutating actions, full detail (the spine of the timeline)
```
fields eventTime, eventName, eventSource, awsRegion, recipientAccountId, sourceIPAddress, userAgent, errorCode, @message
| filter (userIdentity.arn like /<USER>/ or userIdentity.principalId like /<USER>/)
| filter readOnly = 0
| sort eventTime asc
```
limit: 1000 (raise/split the window if the row count hits the limit — note truncation in the
log). `@message` is the full CloudTrail record JSON; parse `requestParameters`,
`responseElements`, and `resources[]` for the affected resource IDs. Note: `ConsoleLogin` /
`GetSigninToken` are `readOnly = 0`, so they also surface here — de-duplicate against Query B
when building the timeline.

## Query D — Errors / denied actions
```
fields eventTime, eventName, eventSource, errorCode, errorMessage, sourceIPAddress
| filter (userIdentity.arn like /<USER>/ or userIdentity.principalId like /<USER>/)
| filter ispresent(errorCode)
| sort eventTime asc
```
limit: 200. Use to flag `AccessDenied` / `UnauthorizedOperation` and failures in the timeline.

---

## Reading the results
- **Account vs region:** `recipientAccountId` = which account; `awsRegion` = where the action
  ran. Global services (IAM, STS, Amazon Q) log `awsRegion = us-east-1` even though the trail
  group lives in `ca-central-1`.
- **Time zone:** `eventTime` is **UTC**. Convert to **UTC+7 (ICT)** for the timeline and state
  the zone.
- **Security-sensitive `eventName`s to call out:** IAM changes, security-group / networking
  changes, CloudTrail/Config changes, new instances (`RunInstances`), key/secret access.
- If Query A returns `0`/`0`, re-check in order: (1) region is `ca-central-1`, (2) `readOnly`
  comparison is numeric, (3) identity token matches the ARN — before concluding "no activity."

## Caveat — non-SSO logins
The identity filter assumes an IAM Identity Center (SSO) user whose role-session-name carries
`<name>@discoveryloft.com`. A **direct IAM-user or root** console login has no such ARN and will
be missed. If that's a concern for the target, run a separate check:
```
fields eventTime, eventName, userIdentity.type, userIdentity.userName, sourceIPAddress
| filter userIdentity.type in ["IAMUser","Root"]
| sort eventTime asc
```
and reconcile by name/IP. These are rare and security-relevant.
