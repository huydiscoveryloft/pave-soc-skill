# Source Registry

Each monitored source is one self-contained module: **collect → (pre-process) → analyze**.
Tier 3 fuses whatever modules ran. To add a source (e.g. AWS), append an entry here and
add it to the list in `SKILL.md`; nothing else needs rewiring.

All collection uses the **OpenSearch MCP** `GenericOpenSearchApiTool` against index
pattern `wazuh-alerts-4.x-*` with `POST /wazuh-alerts-4.x-*/_search`. Substitute `{{START}}`
and `{{END}}` with the `start` / `end` values from `report_period.py` (yesterday, UTC+7).

## Pagination (applies to every source)
`size` is capped at 100 per call, so paginate with `search_after`:
1. Send the body below. Read `hits.hits`.
2. If exactly 100 hits returned, take the last hit's `sort` array, add it as
   `"search_after": <that array>` to the body, and repeat.
3. Stop when a page returns fewer than 100 hits. Concatenate all `hits.hits`.
Save the concatenated hits to a file (e.g. `/tmp/<source>_hits.json`) for any pre-processing.

---

## 1. OpenVPN
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

---

## Adding a new source (template)
```
## N. <Name>
- operation_note: <Confluence page id or none>
- pre_process: <script or none>
- query body: <OpenSearch DSL with {{START}}/{{END}} range filter>
- analysis spec: Role / focus / timezone handling / word limit
```
Then add `<Name>` to the source list in `SKILL.md`. Tier 3, Confluence child pages, and the
Slack summary pick it up automatically.
