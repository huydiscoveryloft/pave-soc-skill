HINT: This is a template for the "Quarterly Firewall Review". Render it into a finalised markdown report from the JSON output of the aws-firewall-review collector (DLVN-SEC-TOOL-004). Strip every HINT/LOOP/ENDLOOP marker from the output. Substitute every <<PLACEHOLDER>>.

# AWS Firewall Configuration Review

**Document Reference:** DLVN-SEC-REV-<<REPORT_SEQUENCE>>
**Version:** <<VERSION>>
**Review Date:** <<REVIEW_DATE>>
**Next Review:** <<NEXT_REVIEW_DATE>> (quarterly cadence)
**Classification:** Confidential — Internal Use Only

## 1. Document Control

### 1.1 Document Information

| Field | Value |
|---|---|
| Document Title | AWS Firewall Configuration Review |
| Document Reference | DLVN-SEC-REV-<<REPORT_SEQUENCE>> |
| Version | <<VERSION>> |
| Review Date | <<REVIEW_DATE>> |
| Prepared By | <<PREPARER_NAME>> — <<PREPARER_ROLE>>, DiscoveryLoft Vietnam |
| Approved By | <<APPROVER_NAME>> — <<APPROVER_ROLE>> |
| Next Review | <<NEXT_REVIEW_DATE>> (quarterly cadence) |
| Classification | Confidential — Internal Use Only |

### 1.2 Revision History

HINT: Preserve all rows from the previous version's revision history. Append one new row recording the current revision.

| Version | Date | Author | Change Summary |
|---|---|---|---|
LOOP: per revision history entry
| <<VERSION>> | <<DATE>> | <<AUTHOR>> | <<CHANGE_SUMMARY>> |
ENDLOOP

## 2. Executive Summary

This report documents the <<QUARTER_LABEL>> review of Amazon Web Services (AWS) security group configurations within the DiscoveryLoft Vietnam (DLVN) production AWS account (`<<AWS_ACCOUNT_ID>>`), conducted to satisfy **DLVN-SEC-POL-002 (Network Security Policy)** quarterly review requirements.

**Scope:** <<TOTAL_SG_COUNT>> security groups across <<ACCESSIBLE_REGION_COUNT>> accessible AWS regions were reviewed. <<DENIED_REGION_COUNT>> of <<TOTAL_REGION_COUNT>> commercial regions are blocked by an organisation-level Service Control Policy (`<<SCP_POLICY_ID>>`) and are out of scope by design — see Appendix A. Only <<REGIONS_WITH_WORKLOADS>> contains provisioned workloads. Evidence was collected using the aws-firewall-review collector (DLVN-SEC-TOOL-004) with read-only API permissions.

### 2.1 Findings Summary

HINT: HIGH_COUNT/MEDIUM_COUNT/LOW_COUNT come from global_summary.findings_by_severity. *_SG_COUNT is the count of distinct SGs where risk_summary.<severity> > 0.

| Severity | Count | Distinct SGs Affected | Action Required |
|---|:-:|:-:|---|
| **HIGH** | <<HIGH_COUNT>> | <<HIGH_SG_COUNT>> | Immediate remediation within 7 days |
| **MEDIUM** | <<MEDIUM_COUNT>> | <<MEDIUM_SG_COUNT>> | Remediation within 30 days |
| **LOW** | <<LOW_COUNT>> | <<LOW_SG_COUNT>> | Risk-accept or remediate within 90 days |

### 2.2 Key Findings

HINT: Write 1-3 bullet points covering the most material HIGH findings. For each: SG ID, SG name, attached ENI count, one-sentence reason it matters. If zero HIGH findings, write "No HIGH severity findings identified in this review period." then bullet the most material MEDIUM findings instead.

<<KEY_FINDINGS_BULLETS>>

HINT: One short paragraph summarising the MEDIUM finding pattern (typically: non-standard ports exposed without WAF/LB ACL).

<<MEDIUM_FINDINGS_NARRATIVE_PARAGRAPH>>

HINT: One sentence on LOW posture, naming the compensating control or upcoming project that will retire the risk.

<<LOW_FINDINGS_NARRATIVE_SENTENCE>>

### 2.3 Overall Assessment

HINT: Choose ONE rating using these thresholds, then justify in one sentence:
  EFFECTIVE             — zero HIGH findings AND 3 or fewer MEDIUM
  PARTIALLY EFFECTIVE   — any HIGH findings OR more than 3 MEDIUM
  NOT EFFECTIVE         — 2+ HIGH findings AND no remediation plan documented

> **<<ASSESSMENT_RATING>>** — <<ASSESSMENT_JUSTIFICATION>>

## 3. Detailed Findings

### 3.1 HIGH Severity

HINT: If zero HIGH findings, write "No HIGH severity findings identified in this review period." and skip the loop. Otherwise loop the block below per HIGH finding.

LOOP: per HIGH finding
#### <<FINDING_ID>> — <<FINDING_TITLE>>

| Field | Detail |
|---|---|
| Severity | **HIGH** |
| Security Group | `<<SG_ID>>` (<<SG_NAME>>) |
| Region / VPC | <<REGION>> / `<<VPC_ID>>` |
| In Use | <<IN_USE_STATUS>> — attached to <<ENI_COUNT>> active ENIs |
| Offending Rule | <<RULE_DESCRIPTION>> |
| **Owner** | <<OWNER>> |
| **Due Date** | <<DUE_DATE>> |
| **Status** | <<STATUS>> |

**Observation:** <<OBSERVATION_PARAGRAPH>>

**Remediation:**

<<REMEDIATION_NUMBERED_LIST>>

ENDLOOP

### 3.2 MEDIUM Severity

HINT: One row per rule exposure (a single SG with multiple MEDIUM rules gets multiple rows). Prefix RECOMMENDED_ACTION with "**HIGH PRIORITY MEDIUM.**" when the exposure is an internal observability/data-store service (Loki, Prometheus, ES, Mongo, Redis, etc.) reachable from 0.0.0.0/0. If zero MEDIUM findings, replace the table with: "No MEDIUM severity findings identified in this review period."

| ID | Security Group | Exposed Port | In Use | Owner | Due | Recommended Action |
|---|---|---|:-:|---|---|---|
LOOP: per MEDIUM finding
| <<FINDING_ID>> | `<<SG_ID>>` (<<SG_NAME>>) | `<<PORT_PROTOCOL>>` (<<SERVICE_NAME>>) | <<IN_USE_STATUS>> (<<ENI_COUNT>> ENIs) | <<OWNER>> | <<DUE_DATE_SHORT>> | <<RECOMMENDED_ACTION>> |
ENDLOOP

### 3.3 LOW Severity

HINT: LOW findings are typically permissive egress (the AWS default). Group them into a single row unless something is genuinely distinct. Name the compensating control and the project that will retire the risk.

<<LOW_FINDINGS_NARRATIVE_PARAGRAPH>>

| Finding | Treatment | Owner | Due |
|---|---|---|---|
| <<LOW_FINDING_RANGE>> (<<LOW_SG_LIST_SUMMARY>>) | <<LOW_TREATMENT>> | <<LOW_OWNER>> | <<LOW_DUE_DATE>> |

## 4. Additional Observations

HINT: Patterns to surface here (NOT formal findings — hygiene/change-management items):
  - SG with attached_eni_count == 0 but referenced by other SGs (orphaned)
  - SG name or rule description contains "tmp", "temp", "manual", "mannuly", "test"
  - Default VPC SGs (group_name == "default")
  - SGs with empty tags
  - Migration residue (names/descriptions mentioning gcp, azure, on-prem)
HINT: If no observations apply, omit this entire section (heading and table).

| ID | Observation | Recommendation | Owner | Due |
|---|---|---|---|---|
LOOP: per observation
| Obs 4.<<N>> | <<OBSERVATION_TEXT>> | <<RECOMMENDATION_TEXT>> | <<OWNER>> | <<DUE_DATE>> |
ENDLOOP

## 5. Sign-Off

**Approved by <<APPROVER_NAME>>, <<APPROVER_ROLE>>, DLVN — Date: ____________**

## Appendix A — Regions Denied by Service Control Policy

HINT: Loop every region from input where regions[].error contains "UnauthorizedOperation". Then state which accessible regions returned zero SGs and which region(s) contained workloads.

The following regions returned `UnauthorizedOperation` responses, confirming the Service Control Policy (`<<SCP_POLICY_ARN>>`) is enforcing the intended preventive control:

LOOP: per denied region
- <<REGION_CODE>> (<<REGION_FRIENDLY_NAME>>)
ENDLOOP

<<ACCESSIBLE_EMPTY_REGIONS_LIST>> are accessible but returned zero security groups (no resources provisioned). <<REGIONS_WITH_WORKLOADS>> is the only region with provisioned workloads.

## Appendix B — Complete Security Group Inventory

HINT: One row per SG, sorted by region then group_name. Findings column format: H/M/L. Bold the H count when greater than 0.

| Group ID | Group Name | Region | In Use | ENIs | Findings H/M/L |
|---|---|---|:-:|:-:|:-:|
LOOP: per security group
| `<<SG_ID>>` | <<SG_NAME>> | <<REGION>> | <<IN_USE_YN>> | <<ENI_COUNT>> | <<H_COUNT>>/<<M_COUNT>>/<<L_COUNT>> |
ENDLOOP

## Appendix C — Evidence and Tool References

- **Raw JSON evidence:** `firewall_review_sg.json` — Confluence *OPENAPI > DevSecOps > Evidence > <<QUARTER_FOLDER>>*
- **CloudTrail:** `sts:AssumeRole` and `ec2:DescribeSecurityGroups` events against role `<<IAM_ROLE_NAME>>` on <<REVIEW_DATE>>
- **Tool:** DLVN-SEC-TOOL-004 — aws-firewall-review MCP server (Dockerised, Python boto3) in DLVN DevSecOps repository
- **IAM role:** `arn:aws:iam::<<AWS_ACCOUNT_ID>>:role/<<IAM_ROLE_NAME>>` with `ec2:DescribeRegions`, `ec2:DescribeSecurityGroups`, `ec2:DescribeNetworkInterfaces`, `sts:GetCallerIdentity`
- **Related:** DLVN-SEC-POL-002 (Network Security Policy), DLVN-SEC-POL-003 (Vulnerability Management Policy), DLVN-SEC-PROC-004 (AWS Change Management Procedure)
