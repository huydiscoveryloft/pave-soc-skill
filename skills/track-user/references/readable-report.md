# Readable Report — Output Contract

The **final deliverable** for a human reader. It is built by re-reading the technical timeline
log (`UA-<user>-<window_id>.md`) and rewriting it as a plain-language narrative timeline that a
non-engineer can skim. Same facts, no new information — every line still traces to a real
CloudTrail event. No fabrication.

Filename: `UA-<user>-<window_id>-readable.md` (next to the technical log in the workspace folder).

## Decouple actions
The technical log packs `eventName`, `eventSource`, account, region, IP and resource ids onto one
dense line. For the readable report, **decouple** each event into one self-contained sentence:

- **One action per line.** If a single API call did several things (e.g. a security-group change
  that opened multiple ports), or one line in the technical log folded multiple events together,
  split them into separate lines.
- **Describe intent + outcome in plain words.** Translate the API name into what the person was
  doing ("User logged into AWS", "User modified security group", "User tried to upload a file").
- **State the result, especially failures.** If the call was denied or errored, say so in plain
  language ("…but got denied").
- **Keep the concrete identifiers** that matter to a reader: account id, IP, resource id, bucket
  name, region — inline, in prose, not as a key/value dump.
- **Drop the flag emojis and the `eventSource` parentheticals** — the prose carries the meaning.

## Structure

```markdown
# AWS Activity — <user> (readable)

**Window:** <window label> · <start> → <end> (UTC+7)

**Identity:** <user> (<resolved role-session-name>)

## What happened (plain summary)
One short paragraph: what the person mainly did this window, anything notable
(security-sensitive changes, denied actions, unfamiliar IPs).

## Timeline

### 2026-06-16

08:41:12 - User logged into AWS, account 088420203827 from IP 203.0.113.4, SSO login.

09:02:55 - User modified security group sg-0d16ade6006de6c1c, opened tcp/22 to 0.0.0.0/0.

09:02:55 - User tries to upload a file into S3, bucket `public-scripts` but got denied.

09:02:55 - User subscribed a OpenVPN Access Server service on AWS Marketplace.
```

## Rules
- **Oldest-first**, grouped by UTC+7 calendar day with a `### YYYY-MM-DD` heading — same ordering
  as the technical log.
- **`HH:MM:SS - <plain sentence>`** per line. Start the sentence with "User …".
- **One blank line between every entry** (and between the two header lines). Markdown collapses
  adjacent non-blank lines into one paragraph, so without the blank line the timeline renders as
  a single run-on block.
- **Same UTC+7 times** as the technical log; do not re-convert from scratch — read them from the
  log you already produced.
- **No new facts.** If it is not in the technical log, it does not go in the readable report.
- **Highlight failures and sensitive changes** in plain words; let them stand out in the prose
  rather than with flags.
- If the window was entirely quiet, write the header + "No activity recorded in this window."
