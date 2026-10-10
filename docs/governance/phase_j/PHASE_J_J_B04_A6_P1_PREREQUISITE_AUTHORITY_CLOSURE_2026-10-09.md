# J-B04-A6-P1 — Prerequisite Authority Closure

Disposition: **`J_B04_A6_P1_BOOTSTRAP_DISPATCH_BOUND_NOT_PROVEN`**. This is a network-free prerequisite result. The Security Master bootstrap is not authorized or executed; A6 live execution remains unauthorized.

## Reviewed baseline and current state

The reviewed starting revision was HEAD `6a8209d622447d0116659ee316db8cf181e7d18d`, tree `6dc2a310a231a95b5122403a230bad3e116b7023`, with `origin/main` `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. A6-P0 is **PASS AS BLOCKED** because the production Security Master is `NOT_INITIALIZED`; production identity is not verified.

## P1-A — Security Master bootstrap contract

The only formal production bootstrap remains the explicit operator command:

```bash
python scripts/manage_security_master.py update --live
```

The manager invokes the existing `m8r_06_01b_materialize_production_inputs.py`, selects its generated `dryrun_snapshot.json`, builds a candidate using `m8r_08g_security_master_releases.py`, qualifies it, activates the qualified release by atomically writing `active.json`, and reports `restart_required=true`. The new process must use the Mode A production loader; no legacy Candidate-B or fixture fallback is permitted.

The materializer has **5 logical official probes**:

1. TWSE listed ISIN, mode 2.
2. TPEx listed ISIN, mode 4, through the TWSE ISIN source.
3. TWSE delisted lifecycle.
4. TPEx delisted lifecycle.
5. TWSE ETN expiry lifecycle.

The exact initial URLs, hosts, effective parser contracts, method, timeout, response ceiling, redirect behavior, and raw-retention policy are machine-recorded in the companion JSON. The current source manifest does not assign stable `source_contract_id` values to these five probes. Successful response bodies are retained in ignored installation-local input-bundle `raw_payloads`; this is existing behavior and was not changed.

Although each `probe()` call makes one initial urllib open and the handler restricts redirects to HTTPS allowlisted hosts, `SafeRedirectHandler` does not declare a redirect-count ceiling and the materializer has no whole-bootstrap dispatch ceiling. Consequently the **maximum actual HTTP dispatches are NOT PROVEN**. Five logical probes must not be reported as five HTTP dispatches. No bootstrap authorization template is emitted. Before a later bootstrap gate can authorize network activity, a separately reviewed hardening must impose and test deterministic per-probe and total dispatch ceilings. P1 does not alter transport behavior.

### Persistence and Cloud task loss

The bundle, raw payloads, snapshot, candidate, qualified release, qualification report, manifest/index hashes, and `active.json` are installation-local under ignored Security Master storage. The production loader is process-lifetime immutable, so post-activation identity verification requires a new process. Bootstrap and a later A6 process could technically run in one task if that state survives, but separate reviewed gates are required. If the task is destroyed, installation-local ignored state may disappear. **No portable restore contract exists**; no release copying or restoration is authorized here.

After bootstrap, require manager status `ACTIVE`, release `QUALIFIED`, manifest/hash validation, production loader success, and exact `runtime.identity_service.resolve("TWSE:2330", market_hint="TWSE")` results: `resolved`, `exact_listing_id`, TWSE/code 2330, `company_share`/`common_share`, execution `allowed`. Capture release ID, manifest hash, release index hash, active selector, and ISIN. A5’s predeclared source target is not production identity authority.

## P1-B — TWSE H3 authority

Disposition: **`J_B04_A6_H3_AUTOMATION_AUTHORITY_ACCEPTED`** for the Owner-authorized, bounded local-first product use of the existing TWSE `STOCK_DAY` H3 route. The specific authority is `PHASE_H_H3_TWSE_CONTROLLED_USE_OWNER_DECISION_2026-09-24.json` and its referenced Owner product-inclusion decision. Technical accessibility is documented separately in the H-ACT-H3 acceptance ledger.

The authority distinction remains explicit: the source is the official TWSE web surface; the Owner authorized this product use; provider automation permission remains `NOT_ESTABLISHED_TERMS_CONFLICTED`; no TWSE approval is claimed; redistribution permission is not established. The accepted scope is the existing `phase_h_h3_twse_recent_performance_executor` only. This does not authorize TPEx H3, Yahoo, browser fallback, or another provider.

## A6 readiness and activation boundary

| Prerequisite | Status |
| --- | --- |
| A5 source acceptance | PASS |
| A6-P0 architecture | PASS |
| Security Master ACTIVE/QUALIFIED | BLOCKED / future bootstrap |
| TWSE:2330 production identity | BLOCKED / future |
| H3 automation authority | Owner-authorized bounded use; provider terms conflict preserved |
| H2 source acceptance | PASS from A5 |
| H2 canonical activation | NOT AUTHORIZED |
| H4 | READY |
| Result V3 | READY |
| Audit V3 | READY + transport ledger requirement |
| Live bounded contract | NOT AUTHORIZED |

H2 remains `INACTIVE`, unselected, and `plan_only`. A later activation tranche must separately govern the H2 catalog fields (`runtime_executable`, `phase_h_activation_state`) and route fields (`runtime_executable`, `routing_status`, `selected_executor_id`), with generated catalog/guide synchronization and activation/rollback authority. P1 changes none of them.

The proposed integrated vertical has at most three H3 TWSE `STOCK_DAY` month GETs (`response=html`, date parameter for each required ROC month, exact `stockNo=2330`) followed by one H2 `TWT48U_ALL` GET: four dispatches maximum for a complete integrated vertical. Both existing transports use retry zero and reject redirects. The future session ceiling remains 10 total official GET dispatches. A session-wide slot must be reserved before each dispatch, and a new full integrated attempt must not start unless its maximum remaining envelope fits the budget. Exact H3 date/month derivation and session reservation must be bound in the later A6 live contract. No live authorization or lease is created.

## Validation and terminal state

The P1 unit suite passed **6/6**; the broader selected network-free integration/regression group passed **182**, skipped **1**. The P1 validator passed. A1, A2, A3, Phase-H V3, Phase-J GHI, A6-P0, portable catalog, and runtime Skill/guide validators passed. The A6-P0 check confirmed the A5 closeout and both historical A5 sessions were unchanged. Strict duplicate-key JSON validation passed for **1,042 files**; compileall and `git diff --check` passed.

Default-CI was run at base `6a8209d622447d0116659ee316db8cf181e7d18d` and implementation commit `11f593d2052da2ce75f8f182e1a02e12efa32aed`, with identical Python 3.12.14, dependency environment, profile command, and test selection. Both had 1,288 collected, 1,283 selected, 1,251 passed, 28 failed, 4 skipped, and 5 deselected. All 28 failures were the same Phase-I A4 tests requiring an active local Security Master, which is intentionally `NOT_INITIALIZED` in this Cloud installation. New failure delta: **0**. Resolved failure delta: **0**. The exact failed node IDs are in the companion JSON. `network_may_have_occurred=false` in both reports.

Market GET/HEAD/POST remained `0/0/0`; Security Master live acquisition was `0`; bootstrap was not executed. H2 is `INACTIVE`, selected executor is `null`, J-B04 is `BLOCKING`, Phase J is `NOT_STARTED`, and MCP remains 6.

The exact bootstrap probe inventory and machine checks are in the companion JSON and `scripts/validate_phase_j_b04_a6_p1_prerequisite_authority.py`. No Owner authorization template is included because the transport dispatch ceiling is unproven.
