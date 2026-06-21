# Incident report — how to fill it from triage output

Used in Step 5 when the user opts in. Build the report from the triage output (the full alert,
the Investigator analysis, the query findings, and the Threat Hunter verdict), draft it locally,
then — after the confirmation gate — publish it to Confluence.

## Authoritative structure
**The report structure is defined by `../template/incident-report-template.md`** — transcribed
verbatim from the official PAVE incident report PDF (ISO/IEC 27001:2022 Annex A 5.24–5.28).
Use that file as the source of truth: copy it, then fill every `{...}` placeholder. Do **not**
invent, reorder, rename, or drop sections. Reproduce every section even when its value is
`None` / `TBD` / `Pending`. Date format follows the template: `DD Mon YYYY HH:MM:SS UTC+7`.

## How to populate each field
- **Incident ID** — next `INC-YYYY-NNN` (see `publishing.md`).
- **Incident Title** — short phrase from the Threat Hunter's `Alert:` line.
- **Detection Method** — usually "Wazuh SIEM alert".
- **Date/Time Detected / Occurred** — from the alert's `timestamp` / `data.timestamp`, shown in
  **UTC+7** (alert times are stored UTC; convert and label `UTC+7`, matching the template).
- **Incident Category** — derive from `rule.groups` / alert type (Intrusion, Malware,
  Vulnerability, Policy violation, …).
- **Severity Level** — map from `rule.level` and the verdict (Low / Medium / High / Critical);
  state the basis.
- **Priority** — P1–P4, from severity + business exposure.
- **Status** — fresh triage → "Under Investigation"; if action already taken → "Contained".
- **Executive Summary / Detailed Description / Attack Vector** — from the Investigator analysis
  + Threat Hunter assessment.
- **Affected Assets** — from alert fields (`agent.name`, `data.srcip`, host, user); `None` where
  the triage found no impact.
- **Impact / CIA** — reason from the verdict; a confirmed False Positive is typically all Low /
  None.
- **Response Actions / IOCs / Evidence** — from the query findings; if none, state so explicitly.
- **Timeline** — at minimum: Detection (alert time) and Triage (now). Add Escalation /
  Containment / Post-Incident rows only if they actually happened.
- **Root Cause / Lessons Learned / Corrective Actions** — derive where supported; otherwise
  `TBD` / `Pending` with an owner.
- **Prepared By / approvers** — `TBD` unless the user supplies names.
- Convert any relative dates to absolute (today is in the environment).

**Never fabricate.** Anything not supported by evidence is `None` / `TBD` / `Pending`.

## Output
1. Write the filled report as `INC-<YYYY>-<NNN>-<slug>.md` in the workspace folder and present it.
2. After the confirmation gate, publish per `publishing.md`.
