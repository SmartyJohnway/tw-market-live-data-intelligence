# M8A official EOD test and fixture strategy

Status: m8a_00_official_eod_adapter_scope_and_contract_preflight_complete
Generated: 2026-07-11T10:24:35Z
Next task: M8A-01-03-OFFICIAL-EOD-ADAPTERS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE


## Fixture classes
normal TWSE row; normal TPEx row; comma-formatted numeric row; signed change row; zero/no-trade row; suspended/special-marker row; missing numeric field; invalid numeric string; invalid date; duplicate symbol; mixed instrument row; non-common-stock row; empty response; source-declared error; changed top-level schema; wrong trade date; previous trading day fallback; one-source failure / one-source success.

Fixtures must be small, curated, derived from official response shape, sanitized, accompanied by source/probe provenance, and not large raw payload dumps.

## Future tests
TWSE contract parser tests; TPEx contract parser tests; shared normalized schema tests; field-unit tests; date-semantic tests; identity tests; instrument-filter tests; failure-contract tests; currentness tests; M8 builder integration tests; conversation projection tests; controlled runtime tests; partial-success tests; default-ci no-network fixture tests; bounded live validation tests; final acceptance tests.

## Placement
Default CI: all parser, schema, mapping, fixture, M8 builder, conversation projection, and boundary tests using fixtures only. Full non-network: default plus expanded drift/edge fixture matrices. Explicit network/live validation: manual bounded probes only, never default-ci.
