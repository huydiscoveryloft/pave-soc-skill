# Publishing

## Confluence (Atlassian Rovo MCP)
- **cloudId**: `0ab6bc10-825b-445d-a6db-6e3c267094dc` (site `paveai.atlassian.net`)
- **spaceId**: `20480022`
- **parent of the daily page**: `147226819`
- Create pages with `createConfluencePage`, `contentFormat="markdown"` (pass the markdown
  report directly; the MCP renders headings/tables).

Order:
1. **Parent page** — title `{date} Daily Security Report`, parentId `147226819`,
   body = the Tier 3 report. Capture the returned page `id` and `webUrl`.
2. **Child pages** — one per source that ran, parentId = the parent page `id`:
   - `OpenVPN {date}` — OpenVPN analysis
   - `Physical access {date}` — Physical analysis (with count table)
   - `Vulnerability detector {date}` — VD analysis
   - `AWS user activity {date}` — AWS CloudTrail analysis
   (Future sources add their own child page automatically.)

## Slack (Slack MCP)
- **channel**: `C09V4H4H5PZ` (`#wazuh-ai-report`, private)
- Send the Tier 2 message with `slack_send_message` to that channel.
- The message must already contain the Confluence parent `webUrl` at the end.

### Maintainer DM (scheduled-run halt alert)
- **recipient**: `huy.nguyen@discoveryloft.com` (resolve to user id with `slack_search_users`,
  then `slack_send_message` with that id as `channel_id` — a DM, not the channel).
- Used only when a **scheduled** run halts on a Step 2 malfunction. Keep it minimal: report id +
  date, halted/nothing-published status, and the malfunctioning source(s) with the reason. Do
  **not** list healthy sources, explain why the DM was sent, or suggest next steps.
- **Template** (mrkdwn; one `• *Source*` bullet per malfunctioning source):
  ```
  :rotating_light: *Daily Security Report — run halted (scheduled)*

  *Report:* {report_id} ({date}, UTC+7)
  *Status:* Halted at collection — nothing published (no Confluence pages, no channel post).

  *Malfunctioning source*
  • *{source}* — {reason: "returned *0 hits* for the window. Zero hits on this source usually
    means stalled ingestion rather than a genuinely quiet day (cf. the 2026-06-19 ingestion
    stall)." | the collection error message}
  ```

## Side-effect note
Confluence page creation and the Slack post are the only external-write steps, gated by
SKILL.md Step 4. In an **interactive** run, never create pages or post to Slack until the user
has explicitly approved the drafted report and Slack preview. In a **scheduled /
non-interactive** run, publishing is **auto-approved** — but only when every source was healthy;
a Step 2 malfunction always blocks publishing (instead, DM the maintainer the malfunction brief
— see "Maintainer DM" below — and report the run halted).
