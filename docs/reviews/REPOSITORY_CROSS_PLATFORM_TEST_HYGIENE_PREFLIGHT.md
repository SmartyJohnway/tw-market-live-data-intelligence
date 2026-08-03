# Repository Cross-Platform Test Hygiene Preflight

## Status
Ready for implementation.

## Baseline Identity
`e00193d0c1719bbdbd3eea2ed9f0f21c0fd23388`

## Objective
Create a bounded cross-platform test-hygiene correction addressing Windows default CP950 decoding, implicit text encodings, and isolated pytest import-path instability.

## Scope Boundary
Address strictly the 20 environment/state-induced failures documented in `docs/acceptance/M8R_05B_03_FINAL_ACCEPTANCE.json`.
The 23 retained historical failures remain out of scope unless incidentally resolved. No production behavior, schemas, or live execution semantics will be altered.

## Target Failure Inventory
20 targeted nodes derived from M8R-05B-03 final acceptance. (See JSON for full itemized list).

## Root-Cause Categories
- `environment_state_induced_windows_encoding`
- `environment_state_induced_import_path`

## Proposed Corrections
- For encodings: Add explicit `encoding='utf-8'` and `errors='strict'` to `open`, `Path.read_text`, `Path.write_text`, and `subprocess.run` strictly within the 11 affected files.
- For import paths: Ensure package-safe imports or stable test PYTHONPATH mechanisms without brittle `sys.path` appending in individual nodes.
- For path normalization: Use `pathlib.Path` for cross-platform robustness.

## Production-Behavior Risk Assessment
Low. These are test harness and file read/write explicit typings.

## Planned Test Matrix
1. Run all 20 targeted node IDs individually.
2. Run full suites for affected files.
3. Run M8R regression safety suites (05B-03, 05B-02, explicit 05B-01, upstream gate).
4. Run full non-network profile (`pytest -m "not network" -q`).

## Stop Conditions
- Redesigning M5/M6/M8 product contracts.
- Changing live execution semantics.
- Changing accepted evidence schemas.
- Modifying more than a bounded set of encoding/import/path helpers.
- Starting M8R-05C.

## Preflight Decision
Approved. Proceeding with bounded corrections.
