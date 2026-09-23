# Full Non-Network 7-Failure Disposition Preflight — 2026-09-23

Status: **PREFLIGHT PASS — REPAIR SCOPE IDENTIFIED, REPAIR NOT YET AUTHORIZED**

Baseline main: `bbc47b00df1abc1d310741b71b043eae512e07e7`

Source run: Full Non-Network Regression `35849449665`

Observed result:

- selected: 2737
- passed: 2717
- failed: 7
- skipped: 13
- GitHub conclusion: failure

This preflight is evidence-only. It does not repair runtime code, rewrite historical acceptance evidence, change test profiles, change markers, alter source/routing/schema authority, enter TG6-C, or enter Roadmap Phase I.

## Executive conclusion

The seven remaining failures are not one homogeneous regression set.

Disposition:

- **1 current runtime defect**
- **3 current test/fixture drift defects caused by post-H-ACT-V3 authority promotion**
- **1 current documentation/front-door drift defect**
- **2 intentionally frozen historical self-membership assertions already governed by the TG-5 rollback diagnostic gap contract**

Therefore the current Full Non-Network red state can be reduced from seven failures to the two explicitly frozen historical assertions without changing the 93-path / 778-node default authority, without weakening tests, and without touching TG6-C.

## Failure disposition

### FNN-01 — Current runtime defect — HIGH

Node:

`tests/acceptance/test_m8r_06_05_operator_acceptance.py::test_m8r_06_05_partial_source_failure_and_ui_bindings`

Observed:

- execution aggregation correctly reports `partial_success`;
- Result V3 incorrectly reports `full_success`;
- expected Result status is `partially_failed`.

Root cause:

In `scripts/m8r_05c/result_builder.py`, V3 coverage handling contains a generic artifact-free branch:

`elif binding is not None and not binding.evidence_artifacts: is_provided = True`

That branch does not require the binding to have succeeded. A failed `official_eod_reference` binding with no evidence artifacts is therefore treated as provided, suppressing the required partial failure and allowing `full_success`.

Disposition:

**CURRENT_RUNTIME_DEFECT — REPAIR REQUIRED**

Safe repair direction:

Require a succeeded binding before an artifact-free V3 binding can count as provided, while preserving explicit typed V3 evidence handling and legal no-evidence semantics. Add focused regression proof that a failed required inherited need remains missing and produces `partially_failed` when another requested need succeeded.

### FNN-02 — Frozen historical assertion — DEFER

Node:

`tests/unit/test_m7f_rich_fact_browser_final_acceptance.py::test_default_ci_includes_final_acceptance_tests`

The test records historical default-CI topology from the M7F final-acceptance milestone. TG-5 explicitly classifies this node in `TG5_ROLLBACK_DIAGNOSTIC_GAPS.v1.json` as a frozen historical self-membership assertion after cutover.

Disposition:

**FROZEN_HISTORICAL_ASSERTION — DO NOT REWRITE**

Future cleanup, if desired, belongs to the already deferred test-governance marker/physical-history work, not this repair.

### FNN-03 — Frozen historical assertion — DEFER

Node:

`tests/unit/test_m8_00_final_acceptance.py::test_default_ci_includes_m8_final_acceptance_test`

Same governance disposition as FNN-02. TG-5 explicitly permits this current-tree diagnostic failure because the file preserves milestone-era default-CI topology.

Disposition:

**FROZEN_HISTORICAL_ASSERTION — DO NOT REWRITE**

### FNN-04 — Current test authority drift — MEDIUM

Node:

`tests/unit/test_m8r_08b_mcp_tool_contracts.py::test_request_schemas_embed_committed_authority_without_placeholder`

Current production authority:

- preferred Request = V3;
- accepted Request envelope = V1 + V2 + V3;
- MCP remains exactly six tools.

The failing test still expects only V1/V2 and assumes the preferred canonical schema occupies `oneOf[1]`, which was correct before H-ACT-V3 promotion but is no longer current truth.

Disposition:

**CURRENT_TEST_DRIFT — TEST REPAIR REQUIRED**

Repair the test to assert V1/V2/V3 in deterministic order and bind the canonical preferred authority to V3 without changing production tool contracts.

### FNN-05 — Current test fixture drift — MEDIUM

Node:

`tests/unit/test_m8r_08b_mcp_tool_contracts.py::test_startup_snapshot_fails_closed_for_unusable_canonical_authority[...]-canonical_request_schema_malformed`

The malformed synthetic schema still uses the V2 canonical `$id`. Current preferred authority is V3, so the loader correctly fails earlier with `canonical_request_schema_identity_mismatch` before reaching JSON-Schema structural validation.

Disposition:

**CURRENT_TEST_FIXTURE_DRIFT — TEST FIXTURE REPAIR REQUIRED**

Use the current preferred V3 `$id` while keeping the deliberately malformed schema body, so the test once again exercises the intended `canonical_request_schema_malformed` branch.

### FNN-06 — Current test call-contract drift — MEDIUM

Node:

`tests/unit/test_m8r_08e_local_operator_action.py::test_execute_composes_existing_ticket_execution_and_mode_c`

Current production design intentionally calls:

`build_mode_c_ai_handoff(control_package_id)`

without forcing an output version, so new materialization inherits the server-owned preferred Result V3 authority. The test monkeypatch still requires keyword-only `output_schema_version` and expects explicit `"v2"`.

Disposition:

**CURRENT_TEST_DRIFT — TEST REPAIR REQUIRED**

Repair the mock/expectation to verify that the local operator action does not override the server-owned preferred output authority.

### FNN-07 — Current documentation/front-door drift — LOW/MEDIUM

Node:

`tests/unit/test_validate_v1_front_door.py::test_current_v1_front_door_is_consistent`

Validator requirement:

`docs/INDEX.md` must contain `Engineering history / protocol archive`.

Current `docs/INDEX.md` instead uses heading `Historical engineering material`, while the root README already links to the anchor:

`docs/INDEX.md#engineering-history--protocol-archive`

This makes the README anchor and validator expectation disagree with the current index heading.

Disposition:

**CURRENT_DOC_FRONT_DOOR_DRIFT — DOC REPAIR REQUIRED**

Rename the current index heading to `Engineering history / protocol archive`. Do not rewrite historical documents.

## Proposed bounded repair tranche

A single repair PR may safely address **FNN-01 + FNN-04 + FNN-05 + FNN-06 + FNN-07**.

Expected result after repair:

- Default CI remains 93 paths / 778 selected nodes and PASS.
- Windows Compatibility remains PASS.
- Full Non-Network decreases from 7 failures to exactly 2 failures.
- The remaining two failures must be exactly FNN-02 and FNN-03.
- New unexplained failures must equal 0.
- Historical TG-5 gap evidence remains unchanged.
- No test deletion.
- No test-profile selection change.
- No marker migration.
- No source/routing/frozen-schema change.
- No TG6-C.
- No Phase I.

## Explicit stop rules

Stop and do not merge if any of the following occurs:

1. Default CI selected-node authority differs from 778.
2. A new Full Non-Network failure appears.
3. FNN-01 is made green by weakening Result semantics or treating failed evidence as successful.
4. FNN-02 or FNN-03 historical files are rewritten merely to make the suite green.
5. Any test is deleted to reduce failure count.
6. Test execution profiles or CI selection paths are changed.
7. Production source activation, routing, frozen schemas, MCP tool count, TG6-C, or Phase I are changed.

## Recommended next owner gate

Authorize one bounded **Full Non-Network Current-Debt Repair** PR covering only FNN-01, FNN-04, FNN-05, FNN-06, and FNN-07.

The target is not an artificially all-green repository. The target is a truthful Full Non-Network state with only the two already-governed frozen historical assertions remaining.
