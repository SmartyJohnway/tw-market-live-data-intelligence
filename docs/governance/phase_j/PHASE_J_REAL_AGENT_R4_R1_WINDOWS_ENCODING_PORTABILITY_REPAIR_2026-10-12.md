# Phase J Real-Agent R4-R1 — Windows Fixture Encoding Repair

## Disposition

`PHASE_J_REAL_AGENT_R4_R1_WINDOWS_ENCODING_PORTABILITY_REPAIR_READY_FOR_INDEPENDENT_REVIEW`

R4 remains the immutable terminal failure `PHASE_J_REAL_AGENT_R4_HARD_BLOCK_PREPARATION_EXECUTION_FAILED`. Its one-shot authorization remains consumed. R4-R1 performed no scenario execution and gives no real-agent closure credit.

## Root cause

With Python 3.13.7 and `PYTHONUTF8=0`, this Windows environment reports `locale.getpreferredencoding(False) == "cp950"`. Reading the committed UTF-8 fixture `tests/fixtures/phase_j/closure_r1/source_rows.json` through implicit `Path.read_text()` reproduces `UnicodeDecodeError: 'cp950' codec can't decode byte 0xe5 in position 150`. The fixture SHA-256 is `3eafcfd3b70c213cdebc67500093a1880ba9914f07d84fa41163d40c04819cb6` and its bytes are unchanged.

The narrow acceptance transport helper read the fixture without an encoding. In the execute-once child, `UnicodeDecodeError` enters the existing `ValueError` catch and is converted to the fixed child error; the parent maps exit code 2 to `mode_b2_execution_unavailable`. This is a test/acceptance helper Windows portability defect, not a production Mode B2, adapter, MCP, Result/Audit, currentness, or persistence defect.

## Repair and diagnostics

`tests/helpers/phase_j_closure_r1_transport.py` now reads the committed fixture with explicit UTF-8 through `load_source_rows_fixture()`. Fixture bytes and deterministic transport behavior are unchanged. The new subprocess regression disables Python UTF-8 mode, confirms the implicit CP950 read fails, confirms the helper read and transport installation succeed, and confirms installation creates no source invocation marker.

The preserved partial R4 authorization was inspected read-only: `load_control_package()` passed; authorization/binding and preflight hash checks passed; rebuilding preflight produced an identical object; no claim existed; source invocation count was zero. No execute-once, claim, dispatch, or finalization was performed. The failed R4 runtime directory and R4 governance record remain unchanged.

## Validation and boundaries

- Encoding portability and explicit-package proxy tests: **5 passed**.
- Partial-package non-consuming diagnostic: **PASS**.
- Fixture hash unchanged: **PASS**.
- Closure-R2-R1 immutable-authority validation: **PASS**.
- Strict duplicate-key JSON, compileall, and `git diff --check`: **PASS**.
- Default-CI: **not run** because the available profile would execute the prohibited J1-21 acceptance scenario again.

R4-R1 counts: J1-21 scenario attempts `0`; execute API calls `0`; source fixture invocations `0`; market GET/HEAD/POST `0/0/0`; MCP semantic calls `0`; provider inference `0`; real-agent sessions `0`; host Security Master acquisition/mutation `0/0`; pushes `0`. Production files changed: `0`.

The remaining obligation is `real_agent_layer`; Phase J remains `STARTED`, Roadmap Phase J remains unchecked, Phase K remains `NOT_STARTED`, and PR #326 remains OPEN/Draft/unmerged. R4-R1 does not authorize R4-R2, a fresh J1-21 package, or real-agent Attempt #3.
