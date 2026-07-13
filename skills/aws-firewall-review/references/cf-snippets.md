# Cloudflare MCP snippets — dashboard status push

Exact `mcp__cloudFlare__execute` calls the skill uses to push each review's status and
findings to the SOC dashboard's D1 database. See `SKILL.md` §"Status reporting (dashboard)"
for when to call each.

- **Database:** D1 `fwreview`, id `78dde69f-cc9a-4b43-a265-03ae835fbc8c`.
- **`accountId`** is preset in the MCP — use it directly.
- **Best-effort:** wrap each call so a failure is logged and ignored — never abort the review.
- **D1 rule:** params **cannot** be combined with a multi-statement `sql` (error 7400). Each
  snippet below is a single statement with positional `?` params. Timestamps are unix epoch
  seconds. Key each row by `quarter` (e.g. `2026Q2`, derived from `metadata.generated_at`).

## 1. Start (collect begins) — upsert the running row
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "78dde69f-cc9a-4b43-a265-03ae835fbc8c";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  return cloudflare.request({ method:"POST", path, body:{
    sql:`INSERT INTO fwreview_runs
           (quarter, review_id, status, phase, triggered_by, created_at, started_at, updated_at)
         VALUES (?,?,'running','collecting',?,?,?,?)
         ON CONFLICT(quarter) DO UPDATE SET
           status='running', phase='collecting', review_id=excluded.review_id,
           triggered_by=excluded.triggered_by, updated_at=excluded.updated_at,
           error=NULL, finished_at=NULL`,
    params:["<QUARTER>", "<REVIEW_ID>", "<TRIGGERED_BY>", now, now, now] }});
}
```
`<QUARTER>` = `YYYYQn` from `metadata.generated_at`; `<REVIEW_ID>` = `DLVN-SEC-REV-NNN`;
`<TRIGGERED_BY>` = `"scheduled"` or the operator email.

## 2. Phase boundary — advance phase + heartbeat
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "78dde69f-cc9a-4b43-a265-03ae835fbc8c";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  return cloudflare.request({ method:"POST", path, body:{
    sql:"UPDATE fwreview_runs SET phase=?, updated_at=? WHERE quarter=?",
    params:["<PHASE>", now, "<QUARTER>"] }});   // <PHASE> ∈ analyzing | rendering | publishing
}
```

## 3. Success — done + per-account findings
Build `accounts` from the collector evidence + rendered reports first (one entry per account
profile). `findings` is that account's full `risk_findings[]`, each tagged with the report's
stable `F-NNN` id; `confluence_url` is the per-account child page's `webUrl` (see §Confluence).
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "78dde69f-cc9a-4b43-a265-03ae835fbc8c";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  const accounts = [
    // { profile:"production", account_id:"123456789012",
    //   high:2, medium:5, low:3, total_sgs:48, unused_sgs:6,
    //   assessment:"PARTIALLY EFFECTIVE", confluence_url:"https://.../pages/1472...",
    //   findings:[ { finding_id:"F-001", severity:"HIGH", group_id:"sg-0abc",
    //                region:"ap-southeast-1", category:"internet_exposed_sensitive_service",
    //                detail:"22/tcp open to 0.0.0.0/0" } ] },
    // ...one per collected account
  ];
  const rank = { EFFECTIVE:0, "PARTIALLY EFFECTIVE":1, "NOT EFFECTIVE":2 };
  const worst = accounts.reduce((a,x)=> rank[x.assessment] > rank[a] ? x.assessment : a, "EFFECTIVE");
  const sum = (k) => accounts.reduce((n,x)=> n + (x[k]||0), 0);
  return cloudflare.request({ method:"POST", path, body:{
    sql:`UPDATE fwreview_runs
           SET status='done', phase='done', assessment=?,
               total_high=?, total_medium=?, total_low=?, total_sgs=?, unused_sgs=?,
               summary=?, accounts_json=?, error=NULL, updated_at=?, finished_at=?
         WHERE quarter=?`,
    params:[worst, sum("high"), sum("medium"), sum("low"), sum("total_sgs"), sum("unused_sgs"),
            "<SUMMARY>", JSON.stringify(accounts), now, now, "<QUARTER>"] }});
}
```

## 4. Failure (collector auth all-or-nothing, or unexpected error)
```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "78dde69f-cc9a-4b43-a265-03ae835fbc8c";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  return cloudflare.request({ method:"POST", path, body:{
    sql:`UPDATE fwreview_runs SET status='failed', error=?, updated_at=?, finished_at=? WHERE quarter=?`,
    params:["<ERROR — name the profile + the aws sso login command>", now, now, "<QUARTER>"] }});
}
```
If the start row (§1) was never written (failure before collect began), use the §1 upsert
shape but with `status='failed'` and the error set.
