# Publishing target — incident reports (Confluence)

Used only in Step 5 when the user opts into an incident report, and **only after the Step 5.2
confirmation gate**.

## Target
- **Connector:** Atlassian Rovo (Confluence).
- **cloudId:** `0ab6bc10-825b-445d-a6db-6e3c267094dc` (`paveai.atlassian.net`).
- **Space:** key `OPENAPI` (display name "PAVE Wiki", URL slug `pavewiki`). The
  `createConfluencePage` tool needs the **numeric `spaceId`**, which is not the key — resolve it
  at publish time with `getConfluenceSpaces(keys: ["OPENAPI"])` and read the returned id. (Cache
  it here once confirmed if you want to skip the lookup.)
- **Parent page:** `223773037` (the existing `INC-2026-001`). Create new incident reports as
  children of this page via `parentId: "223773037"`.
- **Content format:** create with `contentFormat: "markdown"` (matches the daily-report skill and
  the existing incident pages). Skip the `<custom data-type="date">` widgets and embedded image
  blobs from the example — use plain dates; attach evidence images manually if needed.

## Numbering — `INC-YYYY-NNN`
Incident IDs are sequential within the calendar year. To pick the next number:
1. `searchConfluenceUsingCql` with `cql: 'title ~ "INC-<YEAR>" AND type = page'` (e.g.
   `INC-2026`), in space `OPENAPI`.
2. Find the highest existing `NNN` for the current year and add 1; zero-pad to 3 digits.
3. If none exist for the year, start at `001`.

Known at build time (2026): `INC-2026-001` (page `223773037`), `INC-2026-002 (Draft)`
(page `227966978`) → next would be `INC-2026-003`.

## Page title
Use the incident id plus a short title, e.g. `INC-2026-003 SSH brute-force on agent web-01`.

## After publishing
Capture and return the page `webUrl` so the user has a direct link.
