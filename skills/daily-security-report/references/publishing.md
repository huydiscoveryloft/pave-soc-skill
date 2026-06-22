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

## Side-effect note
Confluence page creation and the Slack post are the only external-write steps, and they are
**always gated** behind the mandatory confirmation in SKILL.md Step 4 — never create pages or
post to Slack until the user has explicitly approved the drafted report and Slack preview.
