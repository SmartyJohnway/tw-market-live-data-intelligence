# J-B04-A5-L1-P0 live-runner hardening

Disposition: `J_B04_A5_L1_P0_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW`.

This tranche adds the exact-head live CLI and its network-free acceptance path. The command requires `--live-acceptance`, `--execution-environment`, and an external `--owner-authorization-json`. The authorization binds exact HEAD, tree, canonical main, the explicit environment class, the byte-exact Owner statement, its SHA-256, and `consumed: false`. Tracked staged or unstaged changes block before consumption.

The runner rechecks the P0-R2 Security Master outcome and canonical dormancy immediately before consumption. A clean cloud `NOT_INITIALIZED` state retains `acceptance_only_predeclared_source_target`, `production_identity_verified=false`, and `A6_identity_reverification_required=true`; an invalid Security Master blocks.

The deterministic run directory is derived from the Owner statement hash. The runner atomically creates `owner_authorization_consumed.json` exclusively before invoking the production `official_get_once` transport. Existing consumption rejects reuse. The run then replays the captured response through the production H2 executor, selects the stage witness offline, and invokes the frozen `derive_h4_for_completed_plan` path. It writes only governed normalized evidence, H4 evidence, sanitized telemetry and receipts. The artifact manifest verifies hashes and sizes; package validation rejects unlisted artifacts and forbidden raw fields.

Raw bytes and decoded source rows live only in `EphemeralLiveCapture` during processing. Persisted telemetry is limited to HTTP status, content type, effective URL, byte count, response hash, JSON root type, row count, retrieval time, call counters, retry count and redirect result. CLI output contains only sanitized outcome data.

Exact stage witness rule:

> prefer normalizable TWSE:2330; otherwise lexicographically smallest (Code, Date, canonical raw-row SHA-256) among normalizable rows

The 2330 source descriptor remains unchanged. Security Master bootstrap is not part of this gate.

No live source or Security Master acquisition was performed. Owner live authorization is `NOT PRESENT`. Market GET/HEAD/POST remains `0/0/0`. H2 remains `INACTIVE`, selected executor remains `null`, J-B04 remains `BLOCKING`, Phase J remains `NOT_STARTED`, and MCP remains 6. PR #326 remains Draft.

## Validation

- A5 P0-R2 tests: 34 passed.
- A5 L1-P0 network-denied tests: 22 passed.
- Focused Phase-H/J regressions: 207 passed.
- Mode A / Security Master lifecycle / identity tests: 41 passed, 2 skipped.
- A1/A2/A3, Phase-H V3, Phase-J GHI, catalog and runtime-guide validators: passed.
- P0-R2 and L1-P0 validators: passed.
- Compileall and `git diff --check`: passed.
- Strict duplicate-key JSON scan: 1,010 files passed.

`default-ci` was run against immutable base and candidate source worktrees with the same CPython 3.12.14 environment, `TZ=Etc/UTC`, `PYTHONHASHSEED=0`, and `/tmp/a5test-venv`. Candidate implementation head `6675b64a2a84632edd64e948e1adf6a2b88fc24e` (tree `b22adc8c96de9446a3b82e1c90f1396c827eaf98`) was the tested head. Both sides collected 1,230 nodes, selected 1,225 and stopped at collection with the same five `ModuleNotFoundError: requests` nodes. There were no executed test pass/fail counts. The shared collection-error set is recorded in the JSON ledger; new failure delta is 0. The profile recorded `network_may_have_occurred=false`.
