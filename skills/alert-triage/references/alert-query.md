# Fetch the full alert by id (OpenSearch)

The triage chain needs the **complete** alert document, not the truncated copy that may appear
in a Slack/notification message. Fetch it from the Wazuh alert indices via the OpenSearch MCP.

- **Index pattern:** `wazuh-alerts-4.x-*`
- **Tool:** `GenericOpenSearchApiTool` (POST `_search`) — or `SearchIndexTool` with the same body.
- **Match on the Wazuh alert id** (`id` is the alert document's own id, a `<digits>.<digits>`
  string). The original n8n workflow scraped this id out of a Slack message; here it is the
  skill's input argument.

## Query body
```json
{
  "size": 1,
  "sort": [{ "timestamp": { "order": "desc" } }],
  "query": {
    "match": { "id": "<ALERT_ID>" }
  }
}
```

Substitute `<ALERT_ID>` with the validated input id.

## Handling results
- **1 hit** → use `hits.hits[0]._source` as the full alert JSON passed to the Investigator.
- **0 hits** → no alert matches that id; tell the user and stop (do not invent an alert).
- **>1 hit** → the `sort` returns the most recent first; use it and note the ambiguity.

## Notes
- Keep the entire `_source`. The Investigator references full JSON field paths (e.g.
  `data.srcip`, `rule.id`, `agent.name`) when writing its investigative queries, so nothing
  should be dropped before analysis.
- Do **not** add a `.keyword` suffix to `id` — it is matched as-is.
- All access goes through the OpenSearch MCP (no raw HTTP), unlike the n8n original which hit
  `wazuh.../wazuh-alerts-4.x-*/_search` directly over basic-auth HTTPS.
