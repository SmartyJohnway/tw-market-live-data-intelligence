# M8R-07B Local Service Implementation Review

## Baseline and scope

- Baseline: `8232582abef8af3acfc9ae1681a8b52448092ad6` (PR #194 merge).
- Contract version: `unified_market_evidence_local_service.v1`.
- Scope: thin additions to the accepted `/api/unified/*` transport only.

## Changed files and reuse proof

`server/services/unified_local_service.py` projects the committed capability catalog, 05B routing matrix, and existing `load_production_executor_metadata()` output. `server/unified_workbench_router.py` transports it at GET `/capabilities` and adds GET verified handoff. `server/services/unified_mode_c.py` reuses `build_mode_c_result_package()` and verified Audit reading; it does not add a projector or renderer.

Authority versions: catalog `unified_market_evidence_capability_catalog.v1`; routing `m8r_05b_capability_to_executor_routing_matrix.v1.draft`; executor metadata `m8r_05b_03_executor_registry_metadata.v1`. SHA-256 values: catalog `3bb0d8508d2b33353cd5a53c40811d68d9adedd5cfce1f007970821469e24f8f`; routing `c8ef622a05d939058d6ee1d9740086bcf876cdd13159bf958c026c96f04f2c4f`; production metadata `cf469b82d3f31df3b27305952bef76383e1c482833224bfa6d2b0aee10ee2093`. Authorities are verified structurally at request time; contradictory resolved registration fails closed.

## Contract closure

Capabilities preserve executable/plan-only/blocked/provisional distinctions and do not infer plan-only from missing production metadata. Missing, schema-invalid, and duplicate production metadata routes are normalized to bounded Local Service failures without path leakage. Handoff citations come from verified Audit lineage, cover all successful materialized evidence, and exclude raw evidence/rich facts. Request mode and execution outcome are separately transported; the latter is from the finalized receipt. Handoff uses `additional_market_network_executed:false` to state that the read itself made no new market request without making a claim about prior execution.

Existing validate, preview, authorization, execution, Result, and Audit routes are unchanged. Authorization, execution/network confirmation, atomic claim, and replay behavior remain inherited from Phase D.

## Verification and network accounting

- Focused Local Service/Mode C tests: `18 passed, 1 warning`.
- Relevant Mode A/B1/B2/execute-once/Mode C/Workbench/API/AI handoff/operator acceptance selection: `96 passed, 1 warning`.
- `default-ci` final HEAD: `913 passed, 0 failed, 0 skipped, 1 warning`, return code `0`.
- Startup check: localhost `127.0.0.1`, `network_on_startup=false`, canonical schema, Security Master, and capability catalog loaded.
- `compileall server scripts tests`, both required frontend `node --check` commands, and `git diff --check`: passed.
- Sealed local Security Master candidate executed in `default-ci` and passed.
- Automatic test external market-network calls: `0`.

## Carried debt and recommendation

Deferred unchanged: current-observation failure observability, current-observation reliability, EOD currentness integration, Markdown freshness duplication, and CORS `Origin: null` hardening. Closed at transport layer only: citation completeness and request-mode versus execution-outcome wording.

No blocker is identified. M8R-08 and MCP implementation remain unauthorized.
