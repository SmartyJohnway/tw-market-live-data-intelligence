# Phase L6-A2 — Native Installation / Lifecycle Integration

Technical disposition: `L6_A2_NATIVE_INSTALLATION_LIFECYCLE_INTEGRATION_COMPLETE`

Phase L6: STARTED. A0/A1: OWNER-ACCEPTED AND MERGED. A2: AUTHORIZED; technical candidate complete / Owner acceptance PENDING. L6-A3+, Native packaging, Docker, installer, L7 and Phase M: NOT AUTHORIZED.

## Authority and base

Owner authority: `USER_CHAT_2026-10-21_PHASE_L_L6_A2_NATIVE_INSTALLATION_LIFECYCLE_INTEGRATION_AUTHORIZATION`. Exact base `430f280f9c1b4f8d0f387503bb22044214126b39`, tree `dc82faea6c08b94231b2fb4deec0ec6319bf6a38`, is PR #398 normal merge. Work uses isolated branch `phase-l/l6-a2-native-installation-lifecycle-integration`; the original Phase J checkout and its data are untouched. Frozen A1 contract and its `l6-a1-20261021T130000Z` evidence remain unchanged. L0/L1/L2/L4/L5 authorities are reused; Windows 11 x64 is the prospective Native Tier-1 baseline. Run: `l6-a2-20261021T142354Z`; work resumed and final verification performed on 2026-10-22 Asia/Taipei without changing the authorized tranche identity.

## Implementation

`scripts/tw_market_installation.py` is the single HOME/state/settings/metadata authority. HOME bootstrap is CLI > ENV > LOCALAPPDATA/TW-Market, before settings. Fresh STATE_ROOT is CLI > ENV > HOME/state; persisted installation metadata is subsequently canonical and a conflict fails closed. Host/port are CLI > ENV > strict versioned settings > defaults. Init persists default preferences, not transient CLI/ENV selections; rerun preserves identity, creation time and user preferences.

Version-1 installation metadata uses a stable UUID4 independent of APP_ROOT/user/host/port. L4 path/reparse checks reject canonical state within APP_ROOT. HOME-wide exclusive initialization, bounded writable-root probes, disk admission and atomic JSON publication keep metadata publication last. A conflicting/invalid/incomplete installation fails closed. Init creates layout and configuration only, never adopts existing business bytes or acquires data. Status/doctor/stop before init do not create HOME; start fails. An initialized installation may start with Security Master NOT_INITIALIZED.

SM/watchlists/governed roots are selected from STATE_ROOT. Cache/logs belong to HOME; process ownership and scratch use TEMP/TW-Market/installation-id. Existing PID/token/executable/duplicate/stale safeguards remain. Old checkout-hash markers are not adopted. Workbench, host stdio MCP and SM subprocesses propagate the selected installation context. Exact-six MCP contracts remain unchanged.

Explicit SM acquisition stages only within initialized installation TEMP, qualifies using existing semantics, and atomically retains finalized bytes beneath selected SM `source-bundles/<candidate>`. Relative retained snapshot identity and hash are verified on release loading/activation/rollback. Scratch paths are diagnostic only. Rejected/unqualified scratch never activates; provider URLs and classification rules are unchanged. Derived compact indexes/seals use the selected cache output. Resource packaging is deferred.

Legacy SM `--root`/ENV, Watchlist ENV, governed control ENV, event-path ENV and service URL remain explicit compatibility seams. Noncanonical roots are visible in diagnostics and never rewritten into metadata. No active SQLite copy, automatic state adoption, backup restore or migration occurs. Logical state enumeration declares roles and future L2 binding without bypassing its classifier or restoring a source installation ID as destination authority.

## Changed surfaces and gap closure

Exact source/test paths and rationale are in `implementation_scope.json` and the pre-mutation `direct_consumer_inventory.json`. Reviewed `scripts/tw_market.py` and `server/operational_diagnostics.py` require no changes. Source/executor/Catalog/Route/schema/dependency authority remains unchanged.

- A1-G01: CLOSED_A2
- A1-G02: CLOSED_A2
- A1-G03: CLOSED_A2
- A1-G04: CLOSED_A2
- A1-G05: CLOSED_A2
- A1-G06: CLOSED_A2
- A1-G07: CLOSED_A2_PART / REMAINDER_DEFER_A3
- A1-G08: CLOSED_A2
- A1-G09: CLOSED_A2
- A1-G10: CLOSED_A2
- A1-G11: CLOSED_A2
- A1-G12: CLOSED_A2
- A1-G13: CLOSED_A2
- A1-G14: CLOSED_A2
- A1-G15: CLOSED_A2_PART / REMAINDER_DEFER_A5
- A1-G16: DEFER_A3

G07 closes derived-cache placement only; application/static-resource packaging remains A3. G15 closes logical enumeration/safeguards only; full explicit L2 restore/portability/P4 remains A5. G16 remains A3. No claim closes all 16 gaps or accepts P1-P6: P1-P5 are PARTIAL readiness; P6 NOT_YET_IMPLEMENTED.

## Validation and evidence limits

Final focused suites: {'passed': 193, 'skipped': 3, 'failed': 0}. Required dependency/environment/pip/source/public-contract/Portable Catalog/Skill/L5 registration/semantic/publication/compile checks pass. Raw outputs and exact commands are retained. Exact-six snapshot passes. Default-ci: {'passed': 1249, 'failed': 41, 'skipped': 4, 'deselected': 5}; exact historical 41-node failing set unchanged, candidate-only failures 0. Those 41 failures remain unresolved and are not PASS. The passing count increases by one because the compact-index file already in the unchanged default-ci profile now includes an installation-cache output test.

The additionally invoked historical L5-A5 validator reports `A5_NEW_FAMILY_DETECTED` solely because its frozen A5 BASE git-diff gate forbids any Mode B2/C product changes. This tranche explicitly authorizes those physical-root consumers. The raw FAIL is retained, the historical validator is unchanged, and it is not treated as an A2 completion gate or converted to PASS. Current L5 registration/semantic/publication validators and affected B2/execute-once/Watchlist tests pass.

Initial failure-node extraction from serialized JSON was invalid; its record and raw output remain. Corrected extraction decodes command failure tails before comparing node IDs. Intermediate validation evidence is explicitly prefixed `intermediate-`. The first write-guard run also recorded 1248 passed / 42 failed / 4 skipped / 5 deselected, including an additional timeout-after-claim node; its raw comparison is retained and is not accepted as a PASS. The corrected-guard run is a separate full verification, not a rewrite of that failure. Only corrected-guard outputs are authoritative for final candidate code.

Provider requests/live acquisition/production-state mutations: 0. External socket attempts: 0 within Python audit-hook connect/sendto/getaddrinfo acceptance and inherited Python children, loopback allowed. Writes to actual default HOME and original checkout data/artifacts are denied by the acceptance harness. Actual default HOME was absent before and after. This is not OS-wide network/filesystem proof; Git/GitHub transport is excluded. Fixture transport calls do not count as actual provider traffic.

## Retained limitations and stop boundary

- No .git-free resource/distribution acceptance (A3)
- No Docker implementation (A4)
- No full backup/restore/P1-P6 acceptance (A5)
- No automatic existing-state adoption/migration
- Explicit legacy overrides remain noncanonical and diagnosed
- 41 exact historical default-ci failures remain failing/unresolved
- Additional A5 historical immutable-product-diff gate is scope-inapplicable to authorized A2 root integration; raw FAIL retained
- Availability-dependent sealed/local-state integration tests are not claimed passing; conditional symlink tests remain host-dependent
- Init lock left by abrupt process termination fails closed; no automatic stale-lock repair

Manifest is authored only after the content commit, using committed Git blobs with UTF-8 CRLF/CR-to-LF normalization, byte count/hash/blob identity per member and a canonical self-hash excluding self recursion. Owner review is required. No merge, auto-merge, A3+, L7 or Phase M is authorized.
