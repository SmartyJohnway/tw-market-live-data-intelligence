# J-B03-A2.5 — Deterministic Representative Component Adapters

**Disposition:** `J_B03_A2_5_DETERMINISTIC_REPRESENTATIVE_COMPONENT_ADAPTERS_ACCEPTED`  
**Owner authority:** `USER_CHAT_2026-10-07_J_B03_A2_5_DETERMINISTIC_REPRESENTATIVE_COMPONENT_ADAPTERS_AUTHORIZATION`  
**Starting main:** `d3142148e0cdb4f100794c6a7c90504cfd1e0efb` / `f3bec58d3d1fbfb6db97338b7be04155ef0cef03`

## Representative adapters

The fixed offline dispatch maps TPEx attention to the existing H1 v1
`normalize_tpex_attention`, TPEx disposition to the A2.4-accepted H1 v1
`normalize_tpex_disposition`, and TPEx `tpex_cmode` to the new H1 v2
`normalize_tpex_cmode_native`. Unknown source IDs fail closed. The dispatch
does not perform network I/O.

Attention implementation and active route behavior remain unchanged.
Disposition retains the accepted seven-digit date parsing through
`parse_roc_yyyymmdd()`, raw row provenance, exact string-code binding, and one
reported item per matching row. It does not infer lifecycle or effective dates.

The cmode adapter requires all nine accepted source fields, including the
leading space in ` FinancialAnnouncements`. It accepts calendar-valid ISO
dates and seven ASCII-digit TPEx dates; the latter use the governed ROC parser.
It binds by exact non-empty string `SecuritiesCompanyCode`, preserves every
observed source marker exactly (including U+FF39 and blank), and emits only
unresolved native evidence. A single exact match produces one partial H1 v2
native observation and zero canonical coverage. More than one exact cmode row
fails closed. A successful exact search with no matching row produces partial
H1 v2 with no items or native observations, all canonical types uncovered,
and a caveat that absence does not establish normal trading or tradeability.

For a matched row, the raw Date token is retained in a caveat explicitly named
`source_native_provenance:Date=...`; the normalized date is the native
observation's `source_record_date`. This uses the frozen H1 v2 shape without
adding a schema field.

## Component composition

The adapters wrap through the existing
`build_component_record` contract with canonical evidence serialization and
deterministic component identity. The accepted ordered set remains attention
H1 v1, disposition H1 v1, and cmode H1 v2. Composite coverage is the union of
source-authority-validated canonical coverage: attention plus disposition.
Native cmode evidence and exact no-match add zero coverage, so the composite
remains `partial`; `suspension`, `changed_trading_method`, and `resumption`
remain uncovered. The composer change is restricted to the accepted cmode
no-match shape and does not relax other component validation.

Offline tests cover native U+FF39 preservation, blank and unknown markers,
ROC and ISO dates, invalid dates, unsafe field types, duplicate cmode target
rows, no-match, deterministic identities, all-three-source composition,
source mismatch, and independent component failures. They also verify that
no source evidence is promoted to a current tradeability or lifecycle claim.

## Validation

- `python scripts/validate_phase_h_v3_contracts.py`: PASS.
- `python -m compileall -q scripts server tests`: PASS.
- `git diff --check`: PASS.
- Focused adapter, H1 composition, dormant adapter, H1 freeze/projection,
  aggregation, multi-artifact, local-service, and MCP tests: **178 passed, 0
  failed**.
- `python scripts/run_test_profile.py default-ci`: **1282 passed, 0 failed,
  1 skipped, 5 deselected, 18 warnings**; the profile reports
  `network_may_have_occurred=false`.
- Market GET/HEAD/POST: **0/0/0**.
- H1 v1, H1 v2, Composite v1, Result V3, OperationResult v2, and the H0-G
  historical manifest retain all protected hashes.

No schemas, routing, catalog, registry, source activation, preferred version,
active attention behavior, or public MCP surface changed. MCP remains exactly
6 tools. `data/` was not touched, and no raw market payload was committed.

## State and next gate

H0-SRC-01E remains OPEN; H0-SRC-02 remains OPEN. J-B03 remains HOLD, J-B04
remains BLOCKING, and Phase J remains NOT STARTED. The next gate is
**J-B03-A2.6 — Representative Integrated Acceptance and Activation Decision**.
A2.5 does not activate a source or route and does not authorize A2.6 work.
