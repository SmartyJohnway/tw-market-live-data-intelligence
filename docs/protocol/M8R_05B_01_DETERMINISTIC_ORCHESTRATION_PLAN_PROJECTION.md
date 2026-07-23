# M8R-05B-01 deterministic orchestration plan projection

## Purpose and boundary
This component projects schema-valid F3 validation plus immutable catalog, routing, handoff, inventory, and security-master bindings into `unified_market_evidence_orchestration_plan.v1`. It is offline and deterministic. `plan_ready` is not execution authorization: `execution_authorized` is always false. It performs no market-data retrieval and invokes no executor.

## Inputs and output
The planner verifies canonical hashes of F3, capability catalog, routing matrix, and handoff contract; F3 retains zero computed operations. The output schema contains executable-pending-approval, plan-only, blocked, and optional-omission categories. Derived dependencies use deterministic operation IDs.

## Routing and batching
Markets/security types are checked against routing. TAIFEX provisional variants are plan-only. `none`, `same_market`, and `same_source` batching scopes bind batch identity to full member IDs; batch membership is validated. Accounting is non-authorizing and approval composition considers executable operations only.

## CLI and security
`python -m scripts.m8r_05b_01.cli` reads only explicit local JSON inputs. `--check-only` builds and validates in memory and writes nothing. Normal writes require explicit `--output-root` and safe `--output-relative`; the root is never inferred from the destination, and the existing containment utility performs atomic replacement. Errors are machine-readable. There are no network, approval, authorization, execution, persistence, scheduler, M8R-05B-02, or M8R-05B-03 behaviors.

## Caveats and next gate
`session_status` remains blocked, TAIFEX provisional routes remain non-executable, and selected routes still require adapters and later owner approval. M8R-05B-01 accepted under PR #169 (`7ec4c3e4778ab31c7079745b65b988ea88512bfd`); final acceptance evidence sealed in `docs/acceptance/M8R_05B_01_FINAL_ACCEPTANCE.json` and `docs/acceptance/M8R_05B_01_FINAL_ACCEPTANCE.md`. Next task is M8R-05B-02.

Committed golden plans protect schema shape, operation/batch identity, dependency binding, accounting, warning/omission semantics, and non-authorization invariants.
