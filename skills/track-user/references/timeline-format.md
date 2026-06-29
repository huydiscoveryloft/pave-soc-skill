# Timeline Log — Output Contract

The deliverable is a **chronological timeline log** of one user's AWS activity, written as a
Markdown file in the workspace folder. Filename: `UA-<user>-<window_id>.md` (e.g.
`UA-huy.nguyen-UA20260615-20260622.md`), using the `window_id` from `activity_window.py`.

Principles: **chronological**, **factual**, **UTC+7**, **no fabrication**. Every entry traces to
a real CloudTrail event; if a field is absent, omit it rather than guess. Times are converted
from the UTC `eventTime` to UTC+7 (ICT).

## Structure

```markdown
# AWS Activity Timeline — <user>

| | |
|---|---|
| **User** | <user> (resolved identity: <role-session-name from ARN>) |
| **Window** | <window label> · <start> → <end> (UTC+7) |
| **Source** | Control Tower CloudTrail · `aws-controltower/CloudTrailLogs` (ca-central-1) |
| **Generated** | <now, UTC+7> |
| **Window ID** | <window_id> |

## Summary
- **Sign-ins:** <n> (<n failed>) from <distinct source IPs / locations>
- **Mutating actions:** <n> across <n accounts> · <n distinct eventNames>
- **Security-sensitive actions:** <count + one-line list, or "none observed">
- **Errors / denied:** <count, or "none">
- **Accounts touched:** <recipientAccountId list>
- **Source IPs:** <list; flag any unfamiliar>
- One- or two-sentence plain-language characterization of what the user did this window.

## Timeline
Each event on its own line, oldest first, **with one blank line between every entry** (Markdown
collapses adjacent non-blank lines into one paragraph). Group by calendar day (UTC+7) with a
`### YYYY-MM-DD` heading. Per entry:

`HH:MM:SS` — **<eventName>** (`<eventSource>`) · acct `<recipientAccountId>` · `<awsRegion>` · from `<sourceIPAddress>` — <short plain description of what changed, incl. resource id(s) parsed from @message> [flags]

Flags (append only when they apply):
- `🔐 sign-in` — ConsoleLogin / GetSigninToken (note MFA + success/failure)
- `⚠️ sensitive` — IAM / security-group / networking / CloudTrail-Config / new-instance / secret change
- `❌ error: <errorCode>` — the call failed or was denied

### 2026-06-16

08:41:12 — **ConsoleLogin** (`signin.amazonaws.com`) · acct 088420203827 · us-east-1 · from 203.0.113.4 — successful SSO console sign-in (MFA enforced at IdC) 🔐 sign-in

09:02:55 — **AuthorizeSecurityGroupIngress** (`ec2.amazonaws.com`) · acct 088420203827 · ap-southeast-1 · from 203.0.113.4 — opened tcp/22 to 0.0.0.0/0 on sg-0d16ade6006de6c1c ⚠️ sensitive

...

## Notes & caveats
- Truncation: if any query hit its row limit, say so and which (re-run with a wider limit/split window).
- Non-SSO logins (direct IAM-user/root) are not covered by the identity filter — note if a
  separate check was or wasn't run.
- `MFAUsed: No` on SSO logins is expected (IdC enforces MFA) — not a finding on its own.
```

## Rules
- **Oldest-first.** A timeline reads top-to-bottom in time order.
- **De-duplicate** sign-ins between the sign-in query and the mutating-actions query (logins are
  `readOnly = 0` and appear in both) — list each sign-in once.
- **Resolve the actor** to the human via the role-session-name in the ARN; state it once in the
  header, don't repeat per line.
- **Call out** security-sensitive changes and any error/denied actions in both the Summary and
  inline flags.
- Keep per-entry descriptions to one line; put the affected resource id(s) in that line. Do not
  dump raw `@message` JSON into the log.
- If the window is entirely quiet (Query A confirms genuine zero after the gotcha checks), still
  write the log with the header + a "No activity recorded in this window" note.
