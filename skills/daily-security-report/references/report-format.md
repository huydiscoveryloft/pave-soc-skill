# Report Format (SOC 2-aligned)

The daily report is audit evidence for the security-monitoring controls
(SOC 2 Common Criteria CC7.2 monitoring, CC7.3 event evaluation, CC7.4 response).
Tier 3 produces it; it is published to the Confluence parent page.

## Tier 3 — daily report template
Role: security engineer. Fuse the per-source analyses (passed in labeled by source name)
into ONE report using this exact structure. Keep the narrative body under **300 words**
(the metadata/findings tables do not count toward the limit).

```markdown
# Daily Security Report — {date}

**Report ID:** {report_id}
**Reporting period:** {date} 00:00–24:00 (UTC+7)
**Generated:** {generation_timestamp_utc+7} by Claude Cowork (Daily Security Report skill)
**Sources & scope:** {comma-separated source names that ran}
**Classification:** Confidential — Internal Use Only
**Retention:** Retain per DLVN security-records retention policy
**Control mapping:** SOC 2 CC7.2, CC7.3, CC7.4

## Summary
{2–4 sentence overview of the day's security posture.}

## Findings
| ID | Source | Severity | Finding | Disposition | Owner/Reviewer |
|---|---|---|---|---|---|
| F-1 | {source} | {Critical/High/Medium/Low/Info} | {short description} | {Reviewed / Escalated / No action} | {Pending review} |

> If a source produced no notable activity, record an explicit row stating
> "No findings — nominal activity" so the clean state is documented (CC7.2 evidence).

## Per-source detail
### OpenVPN
{OpenVPN analysis}
### Physical access
{Physical analysis, including the access-count table}
### Vulnerability detector
{VD analysis}
```

Rules:
- Severity: Critical/High/Medium/Low/Info, assigned per finding.
- Every source must appear in Findings — clean sources get an explicit "No findings" row.
- Disposition defaults to "Reviewed"; set "Escalated" for Critical/High. Owner/Reviewer
  stays "Pending review" (a human signs off in Confluence).
- Never omit the metadata block — it is the audit-evidence header.

## Tier 2 — Slack summary
Role: Tier 2 SOC engineer. Condense the Tier 3 report into ONE Slack message.
- Slack mrkdwn: titles and bold use single asterisks (`*text*`), NOT `**text**` or `#`.
- Exactly two sections, kept separate, do NOT merge:
  1. `*Cyber security*` — critical findings from OpenVPN + Vulnerability detector (+ future cyber sources).
  2. `*Physical security*` — critical findings + the physical `ascii_table`.
- All tables in ASCII (monospace) format.
- Do NOT include recommended actions (they live in the full report).
- Do NOT wrap the message in a code block.
- End with the full report link: the Confluence parent page `webUrl`.
