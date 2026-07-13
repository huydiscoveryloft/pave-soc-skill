# Cloudflare MCP snippets — dashboard status push

Exact `mcp__cloudFlare__execute` calls the skill uses to push run status/posture to the SOC
dashboard's D1 database. See `SKILL.md` §"Status reporting (dashboard)" for when to call each.

- **Database:** D1 `dailyreport`, id `1c97153d-d9ba-4c7c-ab27-73029e5684e1`.
- **`accountId`** is preset in the MCP — use it directly.
- **Best-effort:** wrap each call so a failure is logged and ignored — never abort the report.
- **D1 rule:** params **cannot** be combined with a multi-statement `sql` (error 7400). Each
  snippet below is a single statement with positional `?` params. Timestamps are unix epoch seconds.

Let `D1 = "1c97153d-d9ba-4c7c-ab27-73029e5684e1"` and
`path = \`/accounts/${accountId}/d1/database/${D1}/query\`` in every snippet.

## 1. Start (after Step 1) — upsert the running row
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "1c97153d-d9ba-4c7c-ab27-73029e5684e1";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  return cloudflare.request({ method:"POST", path, body:{
    sql:`INSERT INTO dailyreport_runs
           (report_date, report_id, status, phase, triggered_by, created_at, started_at, updated_at)
         VALUES (?,?,'running','collecting',?,?,?,?)
         ON CONFLICT(report_date) DO UPDATE SET
           status='running', phase='collecting', report_id=excluded.report_id,
           triggered_by=excluded.triggered_by, updated_at=excluded.updated_at,
           error=NULL, finished_at=NULL`,
    params:["<DATE>", "<REPORT_ID>", "<TRIGGERED_BY>", now, now, now] }});
}
```
`<DATE>` = report_period.py `date` (YYYY-MM-DD); `<REPORT_ID>` = `DLSR-YYYYMMDD`;
`<TRIGGERED_BY>` = `"scheduled"` or the operator email.

## 2. Phase boundary (Steps 2/3/5) — advance phase + heartbeat
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "1c97153d-d9ba-4c7c-ab27-73029e5684e1";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  return cloudflare.request({ method:"POST", path, body:{
    sql:"UPDATE dailyreport_runs SET phase=?, updated_at=? WHERE report_date=?",
    params:["<PHASE>", now, "<DATE>"] }});   // <PHASE> ∈ analyzing | fusing | publishing
}
```

## 3. Success (after Steps 5–6) — done + posture
Build `sources` from the Tier 3 findings table first (one entry per source):
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "1c97153d-d9ba-4c7c-ab27-73029e5684e1";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  const sources = [
    // { name:"OpenVPN", severity:"low", count:12, note:"12 sessions, no anomalies" },
    // { name:"Physical access", severity:"high", count:0, note:"Log pipeline issue" },
    // ...one per source that ran
  ];
  const rank = { info:0, low:1, medium:2, high:3, critical:4 };
  const overall = sources.reduce((a,s)=> rank[s.severity] > rank[a] ? s.severity : a, "info");
  return cloudflare.request({ method:"POST", path, body:{
    sql:`UPDATE dailyreport_runs
           SET status='done', phase='done', severity=?, summary=?, confluence_url=?,
               sources_json=?, error=NULL, updated_at=?, finished_at=?
         WHERE report_date=?`,
    params:[overall, "<SUMMARY>", "<CONFLUENCE_WEBURL>", JSON.stringify(sources), now, now, "<DATE>"] }});
}
```

## 4. Halt (Step 2 malfunction, scheduled run) — in ADDITION to the maintainer Slack DM
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "1c97153d-d9ba-4c7c-ab27-73029e5684e1";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  const sources = [ /* partial: whatever collected before the halt, same shape as §3 */ ];
  const rank = { info:0, low:1, medium:2, high:3, critical:4 };
  const overall = sources.length ? sources.reduce((a,s)=> rank[s.severity] > rank[a] ? s.severity : a, "info") : "high";
  return cloudflare.request({ method:"POST", path, body:{
    sql:`UPDATE dailyreport_runs
           SET status='halted', phase='halted', severity=?, error=?, sources_json=?,
               updated_at=?, finished_at=?
         WHERE report_date=?`,
    params:[overall, "<SOURCE> — <REASON>", JSON.stringify(sources), now, now, "<DATE>"] }});
}
```

## 5. Failure (unexpected error)
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "1c97153d-d9ba-4c7c-ab27-73029e5684e1";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  return cloudflare.request({ method:"POST", path, body:{
    sql:"UPDATE dailyreport_runs SET status='failed', error=?, updated_at=?, finished_at=? WHERE report_date=?",
    params:["<MESSAGE>", now, now, "<DATE>"] }});
}
```

## Read-back (optional sanity check)
```js
async () => {
  const D1 = "1c97153d-d9ba-4c7c-ab27-73029e5684e1";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  return cloudflare.request({ method:"POST", path, body:{
    sql:"SELECT report_date, status, severity, phase FROM dailyreport_runs WHERE report_date=?",
    params:["<DATE>"] }});
}
```
