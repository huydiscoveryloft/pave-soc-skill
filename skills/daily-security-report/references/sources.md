# Source Registry

Each monitored source is one self-contained module: **collect → (pre-process) → analyze**.
Tier 3 fuses whatever modules ran. To add a source, append an entry here and add it to the
list in `SKILL.md`; nothing else needs rewiring.

## Backends
Each source declares a **backend** — the system its `collect` step queries. Two are supported:

- **`opensearch`** — the **OpenSearch MCP** `GenericOpenSearchApiTool` against index
  pattern `wazuh-alerts-4.x-*` with `POST /wazuh-alerts-4.x-*/_search`. Collection paginates
  with `search_after` (see below). Sources 1–3 (Wazuh) use this.
- **`cloudwatch`** — the **CloudWatch MCP** (`awslabs.cloudwatch-mcp-server`)
  `execute_log_insights_query`, a CloudWatch Logs Insights query against a log group.
  No `search_after`; bound results with an explicit `limit`. Source 4 (AWS) uses this.

Both backends take the **same reporting window**: substitute `{{START}}` / `{{END}}` with the
`start` / `end` values from `report_period.py` (yesterday, UTC+7). Those values are ISO-8601
with a `+07:00` offset — usable directly in OpenSearch range filters *and* as CloudWatch
`start_time` / `end_time`.

## Pagination (opensearch backend only)
`size` is capped at 100 per call, so paginate with `search_after`:
1. Send the body below. Read `hits.hits`.
2. If exactly 100 hits returned, take the last hit's `sort` array, add it as
   `"search_after": <that array>` to the body, and repeat.
3. Stop when a page returns fewer than 100 hits. Concatenate all `hits.hits`.
Save the concatenated hits to a file (e.g. `/tmp/<source>_hits.json`) for any pre-processing.

---

## 1. OpenVPN
- **backend**: `opensearch`.
- **operation_note**: Confluence page `234389695` (read via Atlassian MCP `getConfluencePage`, `contentFormat=markdown`).
- **pre_process**: none.
- **query body**:
```json
{
  "size": 100,
  "sort": [{"timestamp": "asc"}, {"_id": "asc"}],
  "_source": {"excludes": ["full_log", "location", "decoder", "input", "manager", "agent"]},
  "query": {"bool": {"must": [
    {"term": {"rule.groups": "Openvpnas"}},
    {"range": {"timestamp": {"gte": "{{START}}", "lt": "{{END}}", "format": "strict_date_optional_time"}}}
  ]}}
}
```
- **analysis spec** — Role: security engineer. Analyze the OpenVPN Access Server logs and
  write a short report focused on detecting malicious behavior. Apply the operation note
  (it flags known false positives). Report all times in **UTC+7**. Keep under **300 words**.

## 2. Physical access
- **backend**: `opensearch`.
- **operation_note**: Confluence page `235438195`.
- **pre_process**: run `scripts/physical_count.py <hits.json>` → keep `markdown_table`
  (for the report) and `ascii_table` (for Slack).
- **query body**:
```json
{
  "size": 100,
  "sort": [{"data.timestamp": "asc"}, {"_id": "asc"}],
  "_source": {"excludes": ["full_log", "agent", "manager", "location", "decoder", "id", "input", "predecoder", "@timestamp", "timestamp"]},
  "query": {"bool": {"must": [
    {"term": {"rule.groups": "physical_authentication"}},
    {"range": {"data.timestamp": {"gte": "{{START}}", "lt": "{{END}}", "format": "strict_date_optional_time"}}}
  ]}}
}
```
- **analysis spec** — Role: security operator. The log timestamps are **UTC**; convert to
  **UTC+7** before analysis. Detect malicious activity: tailgating, key-card cloning, social
  engineering. Apply the operation note (allowed behaviors). Embed the `markdown_table` from
  the count script in the report. Keep under **250 words**.

## 3. Vulnerability detector
- **backend**: `opensearch`.
- **operation_note**: none.
- **pre_process**: none.
- **query body**:
```json
{
  "size": 100,
  "sort": [{"timestamp": "asc"}, {"_id": "asc"}],
  "_source": {"excludes": ["full_log", "agent", "manager", "location", "decoder", "id", "input", "predecoder"]},
  "query": {"bool": {"must": [
    {"range": {"rule.level": {"gte": 10}}},
    {"terms": {"rule.groups": ["vulnerability-detector"]}},
    {"range": {"timestamp": {"gte": "{{START}}", "lt": "{{END}}", "format": "strict_date_optional_time"}}}
  ]}}
}
```
- **analysis spec** — Role: Tier 1 SOC engineer. Analyze the vulnerability-detector alerts,
  then **web-search** each referenced CVE for evidence of active/ongoing exploitation, and
  write a summarized report. Keep under **250 words**.

## 4. AWS user activity (Control Tower CloudTrail)
- **backend**: `cloudwatch` — CloudWatch MCP (`awslabs.cloudwatch-mcp-server`)
  `execute_log_insights_query`. **Not** OpenSearch; this source does **not** use `search_after`.
- **region**: `ca-central-1` — Control Tower home region where the org trail's log group lives.
  This is **not** the MCP default (`us-east-1`). Wrong/omitted region → `ResourceNotFoundException`.
- **log group**: `aws-controltower/CloudTrailLogs` — the Control Tower **organization** trail;
  one group aggregates management events from **all member accounts and all regions**
  (`awsRegion` = where the event happened, `recipientAccountId` = which account).
- **operation_note**: none.
- **pre_process**: none.
- **collection** — call `execute_log_insights_query` (no pagination; bound with `limit`):
  ```
  region          = "ca-central-1"
  log_group_names = ["aws-controltower/CloudTrailLogs"]
  start_time      = {{START}}        # report_period.py 'start' (ISO-8601 +07:00), use directly
  end_time        = {{END}}          # report_period.py 'end'
  limit           = 1000
  query_string    = (the mutating-actions detail query below)
  ```
  query_string:
  ```
  fields eventTime, eventName, eventSource, awsRegion, recipientAccountId, sourceIPAddress, userAgent, userIdentity.arn, userIdentity.principalId, errorCode
  | filter readOnly = 0
  | filter userIdentity.arn like /discoveryloft.com/
  | sort eventTime asc
  | limit 1000
  ```
  The `userIdentity.arn like /discoveryloft.com/` filter is **load-bearing**: without it this
  query returns tens of thousands of rows/day of automated service-principal activity (SSM
  agent heartbeats, EKS ENI/log-stream churn, auto-mode DryRun calls) that drown the human
  signal. DLVN/PAVE humans authenticate via IAM Identity Center, so their role-session-name —
  the tail of `userIdentity.arn` — is their `<name>@discoveryloft.com` email; this substring
  match keeps exactly the human actors. **Caveat:** it also excludes any direct IAM-user or
  root console login (whose ARN has no `discoveryloft.com`); surface those separately if needed
  with a `userIdentity.type in ["IAMUser","Root"]` check.
  Save results to `/tmp/aws_user_activity_hits.json`. If the returned row count equals the
  `limit`, the day was truncated — re-run with a higher limit (or split the window) and note
  the truncation in the analysis. Recommended optional pre-check before pulling detail:
  `fields eventTime | filter readOnly = 0 | stats count(*) as cnt by eventName | sort cnt desc`
  to see the write-action distribution and confirm the filter matches (a `0`-row result almost
  always means a gotcha below, not a quiet day).
- **CloudTrail gotchas (each causes silent zero-match results):**
  1. **`readOnly` is numeric**, coerced to `1` (read) / `0` (write). Use `filter readOnly = 0`
     for mutating actions / `= 1` for read-only. `= false` or `= "0"` → **0 matches, silently**.
  2. **Identity lives in the ARN, not `userName`.** For SSO (IAM Identity Center) users the
     human is the role-session-name at the end of `userIdentity.arn`, e.g.
     `…/AWSReservedSSO_<PermissionSet>_<id>/huy.nguyen@discoveryloft.com`. `userIdentity.userName`
     holds the permission-set **role** name, not the person. To scope to one user:
     `filter (userIdentity.arn like /<username>/ or userIdentity.principalId like /<username>/)`.
  3. **Some List/Get calls are tagged `readOnly = 0`** (e.g. `ListOrganizationsFeatures`,
     Amazon Q `SendMessage`) — judge significance by `eventName`, not the flag alone.
  - Console sign-ins (`ConsoleLogin` / `GetSigninToken`, `signin.amazonaws.com`) are
    `readOnly = 0`, so this one query captures the **auth timeline** alongside changes. SSO
    logins record `additionalEventData.MFAUsed: No` (MFA is enforced at the IdC portal) — do
    not read that as missing MFA. `eventTime` is **UTC** (global services like IAM/STS/Q log
    `awsRegion = us-east-1` even though the trail group is in `ca-central-1`).
- **analysis spec** — Role: Tier 1 SOC engineer (cloud security). Scope: **all DLVN/PAVE human
  identities** (org SSO users, via the `discoveryloft.com` ARN filter — not service principals).
  From the day's mutating CloudTrail events: (a) summarize **console sign-ins**
  per identity with source IPs, flagging unfamiliar IPs or failures (`responseElements.ConsoleLogin
  = "Failure"`); (b) summarize **resource-changing actions** grouped by identity →
  `eventName`/`eventSource`, calling out security-sensitive changes (IAM, security groups,
  networking, CloudTrail/Config, new instances). Resolve each actor to the human via the
  role-session-name in the ARN. Note any denied/error actions (`errorCode` present). Report all
  times in **UTC+7** (`eventTime` is UTC). Keep under **300 words**.

---

## Adding a new source (template)
```
## N. <Name>
- backend: opensearch | cloudwatch
- operation_note: <Confluence page id or none>
- pre_process: <script or none>
- collect: opensearch → query body (DSL with {{START}}/{{END}} range filter, search_after paginated)
           cloudwatch → execute_log_insights_query call (region, log group, {{START}}/{{END}}, limit, query_string)
- analysis spec: Role / focus / timezone handling / word limit
```
Then add `<Name>` to the source list in `SKILL.md`. Tier 3, Confluence child pages, and the
Slack summary pick it up automatically.
