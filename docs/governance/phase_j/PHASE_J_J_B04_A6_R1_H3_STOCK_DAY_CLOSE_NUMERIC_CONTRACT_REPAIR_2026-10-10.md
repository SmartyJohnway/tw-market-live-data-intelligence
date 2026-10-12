# J-B04-A6-R1 — H3 STOCK_DAY Close Numeric Contract Repair

**Disposition:** `J_B04_A6_R1_H3_CLOSE_NUMERIC_CONTRACT_REPAIR_PASS`

The H3 STOCK_DAY adapter now accepts valid ASCII thousands grouping in close values while rejecting malformed grouping before numeric conversion. The existing volume, date, citation, duplicate-row, transport, H2/H4, and Result/Audit contracts remain unchanged. This repair used only synthetic fixtures and offline validation; no market/source request or A6 execution occurred.

A6 exact-head review `5479029771` accepted the prior integrated session as a hard block. Its frozen observation remains HTTP 200 with HTML, 7,529 bytes, response SHA-256 `9bf1dc0caf51a596f422e4194058616a744db5dbe85c0475d1085ec19cb63f60`, and H3 `invalid_close` with zero numeric observations. A6 did not preserve the offending raw close cell. The supported conclusion is that A6 exposed a close-number lexical compatibility gap: close accepted ungrouped decimal values but not properly grouped thousands, while volume already accepted valid grouping. R1 does **not** claim comma grouping definitively caused the historical failure, and does not alter the prior A6 hard-block record.

## Repair and regression coverage

The accepted close grammar is equivalent to `(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?`. Parsing validates the full lexical form, removes ASCII grouping commas only afterward, constructs a `Decimal`, checks finiteness and non-negativity, and returns the existing float value. Invalid lexical failures carry only the bounded class `invalid_numeric_token`; the actual close token and source row are never copied into diagnostics.

Tests cover plain values, grouped values through `1,234,567.89`, malformed grouping and signs, and a synthetic network-free `TWSE:2330` example using `1,440.00` → `1440.0`. The synthetic value is not represented as an A6 source observation. The exact `--` marker remains an unusable observation with reason `close_unavailable`. Duplicate handling still compares raw source-row signatures: exact repeated rows deduplicate; conflicting rows for the same date fail closed, including lexically different `1,000.00` and `1000.00` rows.

## Validation

The implementation commit is `065460132ea9d5b81b241e252c7e2bcc627bccf6` (TREE `fa3e72c02bf009c49ffcda6e94e9a78807a8427d`). Focused unit suites passed 281 tests; Local Service, Workbench, MCP, and deterministic integrated-service tests passed 34 with 1 skipped. A6-P0, A6-P1, A6-P1-R1, the frozen A6 terminal evidence validator, and Phase-H V3 contract validation passed. Compileall, a strict duplicate-key scan of 1,056 tracked JSON files, and `git diff --check` passed. Validation ran with external network denied.

Clean-archive default-CI used the same CPython 3.12.14 environment, `TZ=Etc/UTC`, `PYTHONHASHSEED=0`, the same empty Security Master root, and external network denial for base `70b7c376b42185620a5d7f07c62e088f902c76a1` and candidate `065460132ea9d5b81b241e252c7e2bcc627bccf6`. Both collected 1,288 tests: 1,233 passed, 46 failed, 4 skipped, and 5 deselected. The 46 failed node IDs were identical; candidate-only failures were zero. The profile reports failure on both base and candidate due to those existing failures, with new failure delta 0.

The prior `scripts/validate_phase_j_b04_a6_integrated_acceptance.py` was encountered during a CLI check and raises `KeyError` on the post-session ledger because it assumes every event has a `method` field. The actual reservation event records the method and the completion event records status, response hash, and outcome. This unrelated validator was not changed in the H3 parser repair; the dedicated network-free A6 terminal evidence validator passes.

## State

- Market/source GET/HEAD/POST: `0/0/0`; TPEx and other sources: `0`.
- Security Master acquisition/bootstrap: `0`; Security Master remains `ACTIVE`, with the previously verified `TWSE:2330` identity.
- H2 remains active only for the bounded TWSE route, selected executor `phase_h_h2_twse_exright_pre_executor`.
- Historical A6 remains `J_B04_A6_INTEGRATED_LIVE_ACCEPTANCE_HARD_BLOCK`; A6 rerun is not authorized.
- J-B04 remains blocking; Phase J remains not started; MCP count remains 6.
- PR #326 remains open, Draft, and unmerged.

The evidence-only publication commit follows the tested implementation commit. No live A6 attempt was made.
