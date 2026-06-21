<!--
Incident Report Template — SOURCE OF TRUTH
Transcribed verbatim from the official PAVE incident report PDF (example: INC-2026-001).
Aligns with ISO/IEC 27001:2022 Annex A controls A.5.24–A.5.28.

For agents: this file defines the EXACT structure of a PAVE incident report — section order,
headings, table columns, and field labels. Do NOT invent or reorder sections. Fill every
`{...}` placeholder; where a value is unknown or not applicable, write `None`, `TBD`, or
`Pending` (never fabricate). Reproduce every section even if empty. Field-derivation guidance
(how to populate this from alert-triage output) lives in `../references/incident-report.md`.
-->

# {INC-YYYY-NNN}

**CLASSIFICATION: CONFIDENTIAL**

| Field | Value |
| --- | --- |
| **Document ID** | {INC-YYYY-NNN} |
| **Date Prepared** | {DD Mon YYYY} |
| **Prepared By** | {Name / Role} |
| **Version** | {1.0} |

---

## 1. Incident Identification

### Basic Information

| Field | Value |
| --- | --- |
| **Incident ID** | {INC-YYYY-NNN} |
| **Incident Title** | {short title} |
| **Date/Time Detected** | {DD Mon YYYY HH:MM:SS UTC+7} |
| **Date/Time Occurred** | {DD Mon YYYY HH:MM:SS UTC+7} |
| **Date/Time Reported** | {DD Mon YYYY HH:MM:SS UTC+7} |
| **Reported By** | {Name / Role} |
| **Detection Method** | {e.g. Wazuh SIEM alert / User report} |

### Classification

| Field | Value |
| --- | --- |
| **Incident Category** | {e.g. Vulnerability / Intrusion / Malware / Policy violation} |
| **Severity Level** | {Low / Medium / High / Critical} |
| **Priority** | {P1 / P2 / P3 / P4} |
| **Status** | {Under Investigation / Contained / Closed} |

---

## 2. Incident Description

### Executive Summary

{2–3 sentence summary of what happened and the verdict.}

### Detailed Description

{Detailed technical description of the activity.}

### Attack Vector / Method

1. {step 1}
2. {step 2}
3. {step 3}

_(Use "Not applicable" for a confirmed False Positive.)_

---

## 3. Affected Assets & Scope

| Field | Value |
| --- | --- |
| **Affected Systems** | {hosts / agents, or None} |
| **Affected Data** | {or None} |
| **Data Records Affected** | {or None} |
| **Affected Users** | {or None} |
| **Business Processes Impacted** | {or None} |
| **Geographic Scope** | {e.g. Global, or None} |

---

## 4. Impact Assessment (per A.5.25)

### CIA Triad Impact

| Dimension | Rating | Description |
| --- | --- | --- |
| **Confidentiality** | {Low / Medium / High} | {description} |
| **Integrity** | {Low / Medium / High} | {description} |
| **Availability** | {Low / Medium / High} | {description} |

### Business Impact

| Field | Value |
| --- | --- |
| **Operational Impact** | {or None} |
| **Financial Impact** | {or None} |
| **Reputational Impact** | {or None} |
| **Legal/Regulatory** | {or None} |
| **Contractual Impact** | {or None} |

---

## 5. Response Actions (per A.5.26)

### 5.1 Containment

{Containment actions taken, or "None taken — under investigation".}

| Field | Value |
| --- | --- |
| **Containment Time** | {DD Mon YYYY HH:MM:SS UTC+7, or -} |
| **Containment Type** | {Short-term / Long-term / -} |

### 5.2 Eradication

{Eradication actions / verification method, or Pending.}

| Field | Value |
| --- | --- |
| **Eradication Verified** | {Yes / Pending} |

### 5.3 Recovery

{Recovery actions, or "No system affected — no recovery needed".}

| Field | Value |
| --- | --- |
| **Recovery Time** | {timestamp, or -} |
| **Service Restored** | {timestamp, or -} |

---

## 6. Evidence & Indicators of Compromise

### Indicators of Compromise (IOCs)

{IOCs found, or "No compromise detected".}

### Evidence Collected

{Evidence / log references, or "None".}

---

## 7. Incident Timeline

| Date/Time (UTC) | Phase | Action / Event |
| --- | --- | --- |
| {DD Mon YYYY HH:MM:SS UTC+7} | Detection | {event} |
| {DD Mon YYYY HH:MM:SS UTC+7} | Triage | Initial assessment and classification |
| {DD Mon YYYY HH:MM:SS UTC+7} | Escalation | {only if real} |
| {DD Mon YYYY HH:MM:SS UTC+7} | Containment | {only if real} |
| {DD Mon YYYY HH:MM:SS UTC+7} | Post-Incident | {only if real} |

---

## 8. Communication & Notification

| Stakeholder | Date Notified | Method | Notified By |
| --- | --- | --- | --- |
| {stakeholder, or TBD} | {date, or TBD} | {method} | {name} |

---

## 9. Root Cause Analysis

### Root Cause

{Root cause, or "Under investigation".}

---

## 10. Lessons Learned (per A.5.27)

### What Worked Well

{or TBD}

### What Needs Improvement

{or TBD}

### Recommendations

{or TBD}

---

## 11. Corrective Actions & Remediation Plan

| # | Action Item | Owner | Due Date | Status |
| --- | --- | --- | --- | --- |
| 1 | {action} | {owner, or TBD} | {TBD} | {Open} |

---

## 12. Approval & Sign-Off

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| DevOps lead | {name, or TBD} |  | {TBD} |
| Security lead | {name, or TBD} |  | {TBD} |

---

## Appendices

* **Appendix A:** Supporting Evidence (logs, screenshots, packet captures)
* **Appendix B:** Chain of Custody Log
* **Appendix C:** Communication Records
* **Appendix D:** Network Diagrams / Attack Path Visualization
* **Appendix E:** Regulatory Notification Copies

---

_This template aligns with ISO/IEC 27001:2022 Annex A controls A.5.24 through A.5.28 for information security incident management. It should be reviewed and updated annually or after significant incidents. Distribution is restricted to authorized personnel only._
