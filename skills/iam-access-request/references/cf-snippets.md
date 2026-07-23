# Cloudflare MCP snippets — IAM access request

Exact `mcp__cloudFlare__execute` calls this skill uses to push requests into the SOC dashboard's
D1. See `SKILL.md` for when to call each.

- **Database:** D1 `iamreq`, id `0d85d6ea-fcc9-445e-8a8e-85c55a43401d`.
- **`accountId`** is preset in the MCP — use it directly.
- **D1 rule:** params **cannot** be combined with a multi-statement `sql` (error 7400). Every
  snippet below is a single statement with positional `?` params. Timestamps are unix epoch
  seconds.
- **Not best-effort.** Unlike the firewall review's status pushes, these writes *are* the
  deliverable — if one fails, say so and stop. Do not report a request as uploaded when it was
  not.

## 0. Read the reviewer set — always before an insert

`reviewer_snapshot` is frozen onto the request at insert time. Read the configured set first.

```js
async () => {
  const D1 = "0d85d6ea-fcc9-445e-8a8e-85c55a43401d";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  const res = await cloudflare.request({ method:"POST", path, body:{
    sql:"SELECT email FROM iam_reviewers ORDER BY email" }});
  return res.result?.[0]?.results?.map(r => r.email);
}
```

**If this returns an empty list, stop.** A request whose snapshot is empty can never reach
`approved` — the dashboard requires an `approved` row from every email in the snapshot. Tell the
operator to add reviewers on the dashboard's Configuration tab, then retry.

## 1. Insert the drafted request

`id` is a uuid you generate. `suggestion_json`, `placeholders_json` and `reviewer_snapshot` are
JSON strings. Emails in the snapshot must be lowercase — the API compares them lowercased.

```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "0d85d6ea-fcc9-445e-8a8e-85c55a43401d";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  const suggestion = {
    identity_name: "<IDENTITY_NAME>",
    identity_type: "role",              // role | user
    account: "<PROFILE>",               // management | development | uat | production
    trust_policy: { /* omit entirely for an IAM user */ },
    policy: { Version: "2012-10-17", Statement: [ /* ... */ ] },
    notes: "<free text>",
  };
  const reviewers = ["<lowercased emails from step 0>"];
  return cloudflare.request({ method:"POST", path, body:{
    sql:`INSERT INTO iam_requests
           (id, created_at, updated_at, requester, source_type, source_ref, title,
            identity_type, suggestion_json, setup_steps_md, assumptions_md,
            discovery_evidence_md, placeholders_json, challenge_prompt_md,
            reviewer_snapshot, status)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending')`,
    params:[
      "<UUID>", now, now,
      "<REQUESTER>",                    // who asked, as named in the source
      "<slack|jira>", "<SOURCE_REF>",   // permalink or issue key/URL; NULL if genuinely none
      "<TITLE>",
      "<role|user>",                    // must match suggestion.identity_type
      JSON.stringify(suggestion),
      "<SETUP_STEPS_MD>", "<ASSUMPTIONS_MD>", "<DISCOVERY_EVIDENCE_MD>",
      JSON.stringify(["<PLACEHOLDER_NAME>"]),   // [] when nothing is unresolved
      "<CHALLENGE_PROMPT_MD>",
      JSON.stringify(reviewers),
    ] }});
}
```

Markdown fields are ordinary strings passed as params — real newlines, **not** `\n` escapes.
(SQLite stores a literal backslash-n verbatim; it would render as `\n` on the dashboard.)

## 2. Discovery update — resolved ARNs, evidence, shrunken placeholder list

Only ever touches these four columns plus `updated_at`. **Never** `status`,
`reviewer_snapshot`, or anything in `iam_reviews`.

```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "0d85d6ea-fcc9-445e-8a8e-85c55a43401d";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  return cloudflare.request({ method:"POST", path, body:{
    sql:`UPDATE iam_requests
           SET suggestion_json=?, discovery_evidence_md=?, placeholders_json=?,
               setup_steps_md=?, updated_at=?
         WHERE id=?`,
    params:[ JSON.stringify(/* regenerated suggestion */ {}),
             "<DISCOVERY_EVIDENCE_MD>",
             JSON.stringify([/* still unresolved */]),
             "<SETUP_STEPS_MD>", now, "<UUID>" ] }});
}
```

## 3. Read one request — before discovery, a challenge session, or writing a guide

```js
async () => {
  const D1 = "0d85d6ea-fcc9-445e-8a8e-85c55a43401d";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  const res = await cloudflare.request({ method:"POST", path, body:{
    sql:`SELECT id, title, status, identity_type, suggestion_json, placeholders_json,
                assumptions_md, discovery_evidence_md, reviewer_snapshot,
                challenge_prompt_md,
                guide_md IS NOT NULL AS has_guide
         FROM iam_requests WHERE id=?`,
    params:["<UUID>"] }});
  return res.result?.[0]?.results?.[0];
}
```

## 4. Write the setup guide — **approved requests only**

The `WHERE status='approved'` clause is a second line of defence, not the first: check the
status in step 3 and refuse there. Confirm `result[0].meta.changes === 1` afterwards — `0` means
the request was not approved and nothing was written.

```js
async () => {
  const now = Math.floor(Date.now()/1000);
  const D1 = "0d85d6ea-fcc9-445e-8a8e-85c55a43401d";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  const res = await cloudflare.request({ method:"POST", path, body:{
    sql:`UPDATE iam_requests
           SET guide_md=?, guide_generated_at=?, updated_at=?
         WHERE id=? AND status='approved'`,
    params:["<GUIDE_MD>", now, now, "<UUID>"] }});
  return { changes: res.result?.[0]?.meta?.changes };   // must be 1
}
```

## 5. List recent requests — to find an id

```js
async () => {
  const D1 = "0d85d6ea-fcc9-445e-8a8e-85c55a43401d";
  const path = `/accounts/${accountId}/d1/database/${D1}/query`;
  const res = await cloudflare.request({ method:"POST", path, body:{
    sql:`SELECT id, title, status, created_at FROM iam_requests
         ORDER BY created_at DESC LIMIT 20` }});
  return res.result?.[0]?.results;
}
```

## Never do this

- **No `INSERT`/`UPDATE`/`DELETE` on `iam_reviews`.** Approval is a human act in the dashboard,
  where the reviewer's identity is derived from the Access JWT. A skill-written review would
  defeat the control the whole feature exists to provide.
- **No `UPDATE ... SET status=...`.** The dashboard's Worker recomputes status from review rows.
- **No `UPDATE ... SET reviewer_snapshot=...`** on an existing request. The snapshot is frozen
  by design; editing it would retro-change an in-flight approval.
- **No `DELETE FROM iam_requests`.** A withdrawn request is a rejection with a comment, made by
  a human.
