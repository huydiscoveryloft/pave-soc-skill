# AWS Firewall Configuration Review

**Document Reference:** DLVN-SEC-REV-002
**Version:** 1.2
**Review Date:** 21 April 2026
**Next Review:** 21 July 2026 (quarterly cadence)
**Classification:** Confidential — Internal Use Only

---

## 1. Document Control

### 1.1 Document Information

| Field | Value |
|---|---|
| Document Title | AWS Firewall Configuration Review |
| Document Reference | DLVN-SEC-REV-002 |
| Version | 1.2 |
| Review Date | 21 April 2026 |
| Prepared By | Huy — Security Engineer, DiscoveryLoft Vietnam |
| Approved By | [Head of Security / CTO] |
| Next Review | 21 July 2026 (quarterly cadence) |
| Classification | Confidential — Internal Use Only |

### 1.2 Revision History

| Version | Date | Author | Change Summary |
|---|---|---|---|
| 1.0 | 21 April 2026 | Huy | Initial issue. First automated quarterly AWS security group review. |
| 1.1 | 21 April 2026 | Huy | Generalised report scope; removed external-framework-specific references. |
| 1.2 | 21 April 2026 | Huy | Streamlined structure; focus on findings and remediation. |

---

## 2. Executive Summary

This report documents the Q2 2026 review of Amazon Web Services (AWS) security group configurations within the DiscoveryLoft Vietnam (DLVN) production AWS account (`088420203827`), conducted to satisfy **DLVN-SEC-POL-002 (Network Security Policy)** quarterly review requirements.

**Scope:** 13 security groups across 6 accessible AWS regions were reviewed. 11 of 17 commercial regions are blocked by an organisation-level Service Control Policy (`p-k05gg3jy`) and are out of scope by design — see Appendix A for the confirmed denied regions. Only `ap-southeast-1` contains provisioned workloads. Evidence was collected using the aws-firewall-review collector (DLVN-SEC-TOOL-004) with read-only API permissions.

### 2.1 Findings Summary

| Severity | Count | Distinct SGs Affected | Action Required |
|---|:-:|:-:|---|
| **HIGH** | 2 | 2 | Immediate remediation within 7 days |
| **MEDIUM** | 8 | 5 | Remediation within 30 days |
| **LOW** | 12 | 12 | Risk-accept or remediate within 90 days |

### 2.2 Key Findings

Two high-severity findings, both in `ap-southeast-1`, represent unrestricted ingress from the public internet:

- **`sg-03b73e8d26abc59d8` (sgr-mgmt-vm-common)** — attached to four active network interfaces, permits all protocols inbound from `0.0.0.0/0`. Used as a common baseline for management VMs, this is the most significant exposure identified in this review.
- **`sg-06d9e2a0ef977a7af` (EKS cluster SG for eks-mgmt-ap-southeast-1)** — contains an ingress rule annotated `tmp-8080-alb` allowing all protocols from `0.0.0.0/0` to EKS control-plane and managed worker interfaces. The `tmp` prefix indicates this rule was never removed after its temporary purpose ended.

Medium-severity findings centre on non-standard application ports exposed directly to the internet rather than fronted by a WAF or load balancer ACL. Low-severity findings are permissive egress rules, accepted for this quarter pending AWS Network Firewall implementation in Q3 2026.

### 2.3 Overall Assessment

> **PARTIALLY EFFECTIVE** — design of controls is adequate; operating effectiveness is compromised by the two HIGH findings, which are scheduled for remediation within 7 days.

---

## 3. Detailed Findings

### 3.1 HIGH Severity

#### F-001 — Unrestricted ingress from `0.0.0.0/0` on common VM security group

| Field | Detail |
|---|---|
| Severity | **HIGH** |
| Security Group | `sg-03b73e8d26abc59d8` (sgr-mgmt-vm-common) |
| Region / VPC | ap-southeast-1 / `vpc-0abc94aa354af2fe6` |
| In Use | Yes — attached to 4 active ENIs |
| Offending Rule | Ingress: protocol ALL, ports ALL, source `0.0.0.0/0` (no description) |
| **Owner** | DevSecOps — Huy (Security Engineer) |
| **Due Date** | 28 April 2026 |
| **Status** | Open |

**Observation:** The security group used as a common baseline for management VMs permits all protocols on all ports from the entire public internet. Any EC2 instance attached to this group is fully exposed regardless of other firewall rules, as AWS security group rules are permissive-union. A second ingress rule on port `8069/tcp` (Odoo XML-RPC) from `0.0.0.0/0` is annotated `tmp`, indicating it was intended to be temporary and is now stale.

**Remediation:**

1. Remove the ingress rule *ALL from 0.0.0.0/0* and replace with explicit rules scoped to VPC CIDR (`10.100.48.0/20`) or the VPN security group (`sg-0679e62cbbc633bb9`).
2. Remove the `tmp` rule on `8069/tcp` and route Odoo access through the internal ALB.
3. Add tags `owner`, `reviewer`, and `expires` to any future temporary rules and enforce via IaC policy.

---

#### F-002 — Unrestricted ingress on EKS cluster security group

| Field | Detail |
|---|---|
| Severity | **HIGH** |
| Security Group | `sg-06d9e2a0ef977a7af` (eks-cluster-sg-eks-mgmt-ap-southeast-1-37556452) |
| Region / VPC | ap-southeast-1 / `vpc-0abc94aa354af2fe6` |
| In Use | Yes — attached to 4 active ENIs (EKS control plane and managed worker nodes) |
| Offending Rule | Ingress: protocol ALL, ports ALL, source `0.0.0.0/0` (description: `tmp-8080-alb`) |
| **Owner** | DevOps Lead |
| **Due Date** | 28 April 2026 |
| **Status** | Open |

**Observation:** The AWS-managed security group for the `eks-mgmt-ap-southeast-1` cluster contains an ingress rule permitting all protocols from `0.0.0.0/0`. The description `tmp-8080-alb` indicates this rule was added as a temporary workaround for an ALB migration and was not removed. This rule applies to both EKS control-plane and managed worker-node ENIs, exposing the Kubernetes API surface and all container ports to the public internet.

**Remediation:**

1. Remove the `tmp-8080-alb` rule.
2. If traffic on port 8080 is genuinely required, route it through the existing external ALB (`sg-0efcb9a996f77f13a`) and reference the ALB security group as the source.
3. Validate Kubernetes Network Policies are in place as defence-in-depth.

---

### 3.2 MEDIUM Severity

Each entry below represents a non-standard service port exposed directly to the public internet rather than through an approved inbound path (WAF, CDN, or load balancer).

| ID | Security Group | Exposed Port | In Use | Owner | Due | Recommended Action |
|---|---|---|:-:|---|---|---|
| F-003 | `sg-0679e62cbbc633bb9` (sgr-mgmt-vpn-server) | `1194/udp` (OpenVPN) | Yes (1 ENI) | Huy | 21 May | Accepted risk — document in risk register. OpenVPN exposure to `0.0.0.0/0` is required. Ensure TLS-Auth / tls-crypt and MFA are enforced. |
| F-004 | `sg-0efcb9a996f77f13a` (sgr-mgmt-external-alb) | `8080/tcp` | Yes (6 ENIs) | DevOps Lead | 21 May | Move to port 443 behind TLS termination or restrict to office CIDRs. Port 8080 should not be internet-facing. |
| F-005 | `sg-0efcb9a996f77f13a` (sgr-mgmt-external-alb) | `8069/tcp` (Odoo) | Yes (6 ENIs) | DevOps Lead | 21 May | Remove. Odoo should only be reachable through the internal ALB on 8069, accessed via VPN. |
| F-006 | `sg-0a8a02e870410df61` (sgr-mgmt-vpc-endpoints) | `3100/tcp` (Loki) | Yes (16 ENIs) | Huy | 5 May | **HIGH PRIORITY MEDIUM.** Loki should never be internet-facing. Restrict source to VPC CIDR or to the Grafana SG only. |
| F-007 | `sg-0a8a02e870410df61` (sgr-mgmt-vpc-endpoints) | `3101/tcp` (Loki UAT) | Yes (16 ENIs) | Huy | 5 May | Same remediation as F-006. |
| F-008 | `sg-03b73e8d26abc59d8` (sgr-mgmt-vm-common) | `8069/tcp` (Odoo) | Yes (4 ENIs) | Huy | 28 Apr | Remove the rule annotated `tmp`. Resolved as part of F-001 remediation. |
| F-009 | `sg-00eebb01a683702f4` (sgr-mgmt-wazuh-server) | `1514/tcp` (Wazuh) | Yes (1 ENI) | Huy | 21 May | Restrict to known agent-originating CIDRs (office, GCP NAT, EKS NAT). `0.0.0.0/0` not appropriate for SIEM enrollment port. |
| F-010 | `sg-0bdf57210b935ed82` (devsecops) | `943/tcp` (OpenVPN-AS admin UI) | Yes (6 ENIs) | Huy | 5 May | Restrict the OpenVPN-AS admin UI to office CIDRs (`118.69.58.236/32`, `202.151.174.226/32`) only. |

### 3.3 LOW Severity

Twelve LOW findings relate to egress rules permitting `0.0.0.0/0` on all protocols — the AWS default across every security group in the environment. DLVN currently does not restrict egress at the security group layer; data-exfiltration risk is mitigated by compensating controls (VPC Flow Logs forwarded to Wazuh, GuardDuty DNS-exfiltration findings, and planned AWS Network Firewall implementation in Q3 2026).

| Finding | Treatment | Owner | Due |
|---|---|---|---|
| F-011 to F-022 (all 12 SGs with permissive egress) | Risk-accepted for Q2 2026. Remediation tracked under Q3 2026 AWS Network Firewall project. | Security Eng. | 30 Sep 2026 |

---

## 4. Additional Observations

The following are not classified as findings but warrant attention.

| ID | Observation | Recommendation | Owner | Due |
|---|---|---|---|---|
| Obs 4.1 | `sg-0cf287ad9a5144a65` (sgr-mgmt-eks-nodegroup) has 0 attached ENIs but is still referenced by other SGs. Suggests EKS node group was migrated and original SG retained. | Deprovision once references confirmed safe to remove. | DevOps Lead | 21 Jul 2026 |
| Obs 4.2 | `sg-0d62d4e19dc89d97d` (temp-allow-from-gcp-wazuh) permits SSH from GCP NAT (`34.142.157.128/32`) — residual from ongoing GCP-to-AWS migration. | Retire if GCP-side Wazuh agents have been fully migrated. | Huy | 21 Jul 2026 |
| Obs 4.3 | Two default VPC SGs exist (ap-southeast-1, us-east-2). Neither is attached to any ENI — consistent with best practice. | No action; monitor in future reviews. | — | — |
| Obs 4.4 | Tagging coverage is uneven. IaC-managed SGs (`sgr-mgmt-*`) carry the expected tag set; several manually-created SGs (`devsecops`, `temp-allow-from-gcp-wazuh`, `sgr-mgmt-wazuh-server`) have no tags. | Enforce mandatory tag policies via AWS Organizations. | Security Eng. | 21 Jul 2026 |
| Obs 4.5 | Multiple ingress rules annotated `mannuly` [sic] or `tmp` — direct evidence of manual hot-fixes outside the IaC pipeline. | Enable AWS Config rule `restricted-common-ports`; add custom rule flagging any SG missing `tag:ChangeTicket`. | Security Eng. | 21 Jul 2026 |

---

## 5. Sign-Off

**Approved by [Name], [Role], DLVN — Date: ____________**

---

## Appendix A — Regions Denied by Service Control Policy

The following regions returned `UnauthorizedOperation` responses, confirming the Service Control Policy (`arn:aws:organizations::491072886100:policy/o-25trl9624l/service_control_policy/p-k05gg3jy`) is enforcing the intended preventive control:

- ap-northeast-1 (Tokyo)
- ap-northeast-2 (Seoul)
- ap-northeast-3 (Osaka)
- ap-south-1 (Mumbai)
- ap-southeast-2 (Sydney)
- eu-central-1 (Frankfurt)
- eu-north-1 (Stockholm)
- eu-west-2 (London)
- eu-west-3 (Paris)
- sa-east-1 (São Paulo)
- us-west-1 (N. California)

`ca-central-1`, `eu-west-1`, `us-east-1`, `us-east-2`, `us-west-2` are accessible but returned zero security groups (no resources provisioned). `ap-southeast-1` is the only region with provisioned workloads.

---

## Appendix B — Complete Security Group Inventory

| Group ID | Group Name | Region | In Use | ENIs | Findings H/M/L |
|---|---|---|:-:|:-:|:-:|
| `sg-0cf287ad9a5144a65` | sgr-mgmt-eks-nodegroup | ap-southeast-1 | No | 0 | 0/0/1 |
| `sg-046cfabaacc48da97` | sgr-mgmt-internal-alb | ap-southeast-1 | Yes | 5 | 0/0/1 |
| `sg-0679e62cbbc633bb9` | sgr-mgmt-vpn-server | ap-southeast-1 | Yes | 1 | 0/1/0 |
| `sg-03b73e8d26abc59d8` | sgr-mgmt-vm-common | ap-southeast-1 | Yes | 4 | **1**/1/1 |
| `sg-0c4c4c307cf750670` | default | ap-southeast-1 | No | 0 | 0/0/1 |
| `sg-0efcb9a996f77f13a` | sgr-mgmt-external-alb | ap-southeast-1 | Yes | 6 | 0/2/1 |
| `sg-0a8a02e870410df61` | sgr-mgmt-vpc-endpoints | ap-southeast-1 | Yes | 16 | 0/2/1 |
| `sg-06d9e2a0ef977a7af` | eks-cluster-sg-eks-mgmt-ap-southeast-1 | ap-southeast-1 | Yes | 4 | **1**/0/1 |
| `sg-00eebb01a683702f4` | sgr-mgmt-wazuh-server | ap-southeast-1 | Yes | 1 | 0/1/1 |
| `sg-0bdf57210b935ed82` | devsecops | ap-southeast-1 | Yes | 6 | 0/1/1 |
| `sg-0d62d4e19dc89d97d` | temp-allow-from-gcp-wazuh | ap-southeast-1 | Yes | 2 | 0/0/1 |
| `sg-0da83a199b8950a2c` | sgr-mgmt-eks-cluster | ap-southeast-1 | Yes | 2 | 0/0/1 |
| `sg-02fbdd078f9339b96` | default | us-east-2 | No | 0 | 0/0/1 |

---

## Appendix C — Evidence and Tool References

- **Raw JSON evidence:** `firewall_review_sg.json` — Confluence *OPENAPI > DevSecOps > Evidence > 2026-Q2*
- **CloudTrail:** `sts:AssumeRole` and `ec2:DescribeSecurityGroups` events against role `FirewallReviewReadOnly` on 21 April 2026
- **Tool:** DLVN-SEC-TOOL-004 — aws-firewall-review MCP server (Dockerised, Python boto3) in DLVN DevSecOps repository
- **IAM role:** `arn:aws:iam::088420203827:role/FirewallReviewReadOnly` with `ec2:DescribeRegions`, `ec2:DescribeSecurityGroups`, `ec2:DescribeNetworkInterfaces`, `sts:GetCallerIdentity`
- **Related:** DLVN-SEC-POL-002 (Network Security Policy), DLVN-SEC-POL-003 (Vulnerability Management Policy), DLVN-SEC-PROC-004 (AWS Change Management Procedure)

---

*— End of Document —*
