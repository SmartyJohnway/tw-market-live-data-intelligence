# J-B03-S1 — TPEx Current Suspend Source Authority

**Disposition:** `J_B03_S1_HOLD_EXACT_LICENSE_MAPPING_UNRESOLVED`

## Decision

This review did not establish an exact official license/data.gov mapping for `H1-TPEX-SUSPEND-TODAY-OPENAPI` (`https://www.tpex.org.tw/openapi/v1/tpex_spendi_today`). The route remains inactive, and `H0-SRC-01E` remains open.

The official data.gov.tw record [#48665](https://data.gov.tw/dataset/48665) is titled **上櫃歷史公布暫停/恢復交易股票**. It identifies an irregularly updated historical dataset with fields for suspension and resumption dates/times and lists ODGL 1.0. That record is evidence for the historical dataset only. It does not identify the current-day endpoint, so its license cannot be transferred to the current route by similarity.

The data.gov.tw [ODGL 1.0 terms](https://data.gov.tw/license) describe the general license. They do not establish which TPEx route is covered. TPEx's [OpenAPI documentation](https://www.tpex.org.tw/openapi/) and [Swagger metadata](https://www.tpex.org.tw/openapi/swagger.json) returned HTTP 403 through the research path, so route-level metadata, current-day field descriptions, API status, and cadence could not be verified independently.

**Mapping confidence:** `INSUFFICIENT`. No current-day data.gov dataset ID was proven. The exact publisher/license/resource relation for `tpex_spendi_today` remains unresolved.

## Current blocker state

- `H0-SRC-01E`: historical state `OPEN`; current state `OPEN`.
- `H0-SRC-02`: remains open as an aggregate H1 lifecycle/completeness constraint; S1 did not attempt to resolve it.
- J-B03 remains `HOLD`; J-B04 remains `BLOCKING`; Phase J remains `NOT STARTED`.

The smallest next evidence needed is an accessible official metadata record linking the exact `tpex_spendi_today` URL or a stable dataset ID to its publisher, license, API/automation authority, current-day scope, fields, and update cadence—or a direct authoritative TPEx statement making that mapping.

## Boundary

This was official metadata research only. Market-data GET/HEAD/POST counts are all zero. No market payload endpoint or source-shape endpoint was accessed. No production code, schema, catalog, routing, executor registry, route activation, or MCP surface changed. MCP remains exactly six tools. The existing untracked `data/` directory was left untouched.

Full provenance and source-by-source observations are recorded in the adjacent JSON record.
