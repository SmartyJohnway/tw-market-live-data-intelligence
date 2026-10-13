# Phase L L1-A1 — Minimum Runtime Lifecycle, Status & Doctor

**Disposition:** `L1_A1_OWNER_ACCEPTED_FOR_MERGE`
**Technical review:** `L1_A1_ACCEPTANCE_REVIEW_PASS`
**Authority:** L0 `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN`; A0 `L1_A0R_ACCEPTANCE_MACHINERY_DECOUPLED` and `L1_A0_RUNTIME_OPERABILITY_INVENTORY_COMPLETE`.

## Product surface and reuse

Added `python -m scripts.tw_market` (or direct `scripts/tw_market.py`) with `start`, `status`, `stop`, and `doctor`. It is a standard-library argparse wrapper around the existing Workbench launcher. `start` delegates to its existing preload/server path, defaults to loopback port 8000, accepts CLI host/port overrides, and permits the Workbench's existing `NOT_INITIALIZED` startup behavior. Startup has no market acquisition, identity initialization, Watchlist writes, authorization use, tunnel, connector, or Docker behavior.

| Existing surface | A1 treatment |
|---|---|
| `scripts/run_unified_workbench.py` launcher, localhost guard, preload and startup-check | REUSE through the managed child; no server fork |
| `scripts/verify_environment.py` | REUSE from bounded doctor check |
| `scripts/manage_security_master.py` status substrate / existing pointer state | WRAP as read-only `NOT_INITIALIZED` / `ACTIVE` summary; no init/update/rollback |
| `GET /api/health` | REUSE as liveness only |
| Existing schema/catalog preload and MCP tool contract snapshot | REUSE; doctor checks exact six static tools and calls MCP `--startup-check` |
| Lifecycle command, stable JSON, process ownership and correlated invocation metadata | ADD; no suitable product surface existed |
| Full user-config resolver, durable state relocation, Docker lifecycle, persistent operational logging/telemetry | DEFER to later authorized work |
| A6 session accounting and Phase J acceptance harness | HISTORICAL_ONLY; lifecycle sources do not import it |

## Lifecycle, ownership and status

The child process calls the existing Workbench `main()` with only validated loopback host and port. A private ownership record is stored under the OS temporary directory, namespaced by a hash of the resolved checkout and port. It contains schema, checkout root, PID, OS process creation token, executable, instance UUID, endpoint and start timestamp. Creation is exclusive. `stop` checks PID plus creation token and executable before signaling; on Windows it requests CTRL_BREAK, waits three seconds, then terminates only the still-open, token-verified process handle. Ownership records are ephemeral and are not governed evidence. Missing service reports `NOT_RUNNING`; occupied unowned endpoint reports `PORT_OCCUPIED_NOT_OWNED`; invalid or mismatched metadata reports `STALE_PROCESS_OWNERSHIP`. No port-based kill exists.

`status` is observational. It reports process ownership, HTTP `/api/health` liveness, Workbench preload/schema/catalog readiness, Security Master state/root/release identity when readable, MCP SDK/service status, effective endpoint and state roots. If service is alive but Security Master is fresh, status is `SERVICE_ALIVE / IDENTITY_NOT_INITIALIZED`; liveness does not imply product readiness. Capability routes are checked through the existing bounded `/api/unified/capabilities` projection when reachable, otherwise unknown. `doctor` adds bounded environment verification, read-only path checks, Workbench startup-check, exact-six tool snapshot and MCP startup-check. Fresh identity, absent optional state roots, or unavailable service are warnings/setup conditions; doctor does not initialize, create, repair, or remove those paths.

## Configuration, paths and output

Lifecycle host and port use CLI > `TW_MARKET_HOST` / `TW_MARKET_PORT` > product defaults (`127.0.0.1`, `8000`). CLI endpoint overrides take precedence over the existing `UNIFIED_MARKET_EVIDENCE_SERVICE_URL`; otherwise that MCP setting is reused. Existing Security Master, Watchlist and control-root environment variables are reported as effective roots. There is no user-config-file resolver in the current substrate, so that precedence layer remains deferred. Application resources resolve relative to the entry point, including when invoked from a different working directory. The ownership path is runtime temp state; this does not choose a durable `%LOCALAPPDATA%` layout.

Human output is short; `--json` produces sorted, bounded output with high-level stable fields. Each invocation includes UUID `operation_id`, UTC `started_at`, `duration_ms`, and typed reason codes. No persistent log framework was needed. Output does not include raw environment, secrets, authorization, Result, Audit, or evidence bodies. Governed Audit remains canonical truth; this output is runtime diagnosis.

## Read-only and network guarantees

`status` and `doctor` do not instantiate the Watchlist store. Root checks use filesystem metadata/readability only. Security Master status delegates read-only to the existing `manage_security_master.py status`; it does not call update/init. Startup and checks use existing local preload/loopback behavior. MCP checks use deterministic local tool contracts and the existing bounded service startup-check. No Secure Tunnel, DPAPI secret, ChatGPT connector, or key is required. No `scripts.a6_session_transport` import, A6 session, or historical Phase J harness is used.

The local-only start/status/doctor/stop smoke used alternate port 18763 with a fresh `NOT_INITIALIZED` installation: start returned `STARTED`, status returned service alive with identity not initialized, doctor returned `WARN` with setup/unavailable checks, stop returned `STOPPED`, and subsequent status returned `NOT_RUNNING`. A second status/doctor check used port 18764 from `%TEMP%` via the absolute script path. No market/source URL was contacted; market/source acquisition count, Security Master mutation count, Watchlist mutation count, and authorization consumption count were all zero. The startup-check and health request were local.

## Verification

- `tests/unit/test_tw_market_lifecycle.py`: 16 passed, including deterministic reservation, timeout cleanup, and doctor severity cases.
- Focused lifecycle, H2/H3, adapter, route/catalog, MCP, Local Service, Workbench API/UI, Watchlist, portability and identity-service regression selection: 245 passed, 1 skipped.
- The previously run broader selection including `test_m8r_03d_f1_verified_security_master_snapshot.py` had 8 failures in that existing fixture suite, all reporting `current_skill_contract_hash_mismatch`; 232 tests passed and 1 skipped in that run. This remains `PRE_EXISTING_TEST_AUTHORITY_FOLLOW_UP`, not repaired here. Current skill contract hash: `bf0670e00b0c9a69ffa5b31efed6eb9219bc068e7c1237062787daba4e5a5573`; fixture embedded hash: `488b3e04af2e318cd387b0dfdcbad02be4f2c3f495539c3e436698464f37d77a`. The skill directory, fixture, and exporter/adapter were not changed.
- `scripts/verify_environment.py`, Workbench `--startup-check`, MCP `--startup-check` and exact-six tool snapshot were exercised by doctor; fresh `NOT_INITIALIZED` preload passed.
- Windows native start/health/status/stop smoke passed; no background service remained.
- `git diff --check` and changed-file containment are checked at tranche completion.

## Owner review repair

The initial A1 implementation was held for three bounded lifecycle correctness findings; this record preserves that sequence rather than implying they were absent in the first implementation.

1. **Stale `starting` reservation:** the initial record lacked creator identity, so a CLI crash could leave an unclassifiable reservation. It now records creator PID, process creation token, executable, instance ID, checkout root, endpoint and UTC creation time. A live matching creator returns `START_IN_PROGRESS`. A missing creator, PID reuse/token mismatch, executable mismatch, or invalid witness is `STALE_PROCESS_OWNERSHIP`. Status and doctor only report it. Start may remove a proven stale record and retry; stop may remove it and returns `STALE_PROCESS_OWNERSHIP_CLEANED`. File age is not authority.
2. **`START_TIMEOUT` cleanup:** once the child has a verified PID/token/executable ownership record, deadline expiry requests termination only through `_terminate_owned`; if needed, it retries through the same verified `Popen` child handle. It waits boundedly and removes ownership metadata on confirmed stop. The result remains `START_TIMEOUT` and includes `cleanup_status` and `child_terminated`. Deterministic tests force a never-ready health check without waiting 15 seconds and assert only the verified child is passed for termination.
3. **Doctor severity:** overall status now uses FAIL > WARN > PASS. `PASS` and `WARN` exit zero; `FAIL` exits nonzero. `NOT_INITIALIZED` remains a setup WARN, while dependency/environment, exact-six contract, reachable-service MCP startup, unreadable identity, and route projection failures can produce FAIL. Tests exercise an exact-six mismatch and a reachable-service MCP startup failure.
4. **Stop exit mapping:** follow-up Owner review found `STOP_FAILED` was missing from the CLI failure exit-code set. It is now nonzero; the regression asserts `STOP_FAILED` → 1 and normal `STOPPED` → 0. The bounded repair preserves the accepted A1 technical scope; final technical review is `L1_A1_ACCEPTANCE_REVIEW_PASS`.

Repair regression: lifecycle unit tests **16 passed**; focused suite **245 passed, 1 skipped**. Native Windows alternate-port smoke completed start, already-running, status, doctor, stop and post-stop status; doctor saw 14 capability projections and exactly six MCP tools. Deterministic tests covered stale-start recovery/cleanup and forced timeout termination. A6 remained unimported by all current lifecycle/H2/H3 product modules. Source acquisitions and governed-state/authorization mutations remained zero.

## Deferred gaps and next boundary

The CLI currently has no `init` mutation command; operators continue to use the explicit existing Security Master flow. There is no product user-config resolver, durable cross-machine state layout, bounded persistent event log, installer/updater, service supervisor, Docker profile, migration/backup/replay, or capability readiness API beyond existing projection. These are not blockers for this minimum lifecycle surface. Owner acceptance and merge authorization are recorded for A1. After merge, select the next smallest L1 operability tranche from the frozen L0/L1 obligations plus A0 inventory and the merged A1 surface; do not pre-name or infer authorization for L1-A2 here.

## Explicit non-goals

No public MCP tool changes (still exactly six), Request/Result/Audit or authorization changes, evidence-family/capability changes, market acquisition, A6 product dependency, Docker work, persistent migration, logging platform, installer, or L2-L7 implementation occurred. Roadmap Phase L remains in progress.
