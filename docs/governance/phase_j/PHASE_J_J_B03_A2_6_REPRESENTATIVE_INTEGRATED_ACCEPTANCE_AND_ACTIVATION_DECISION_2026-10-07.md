# J-B03-A2.6 Stage A — Integrated Acceptance and Activation Decision

**Disposition:** `J_B03_A2_6_REPRESENTATIVE_INTEGRATED_ACCEPTANCE_PASS_ACTIVATION_READY`

**Activation:** not performed. This record only establishes readiness; a separate explicit Owner authorization is required before continuing activation work in the same Draft PR.

## Authorization and entry state

Owner authority: `USER_CHAT_2026-10-07_J_B03_A2_6_REPRESENTATIVE_INTEGRATED_ACCEPTANCE_STAGE_A_AUTHORIZATION`.

Starting main: `04af1d3ea63b058317facb8763a524c453bb9093`, tree `de7095ffe36000096c1c2adbda4e84704b59f449`; PR #320 was merged/closed. Work is on `phase-j/j-b03-a2-6-integrated-composite-acceptance`.

The candidate executor is acceptance-only and is not in the production registry. The ordered source set is bound by overlay hash `c87c0b4321a2f9ab94fcbf5335f59735ac4a827ca9d5190e750fb3c5241da8ce`, included in operation parameters and plan hash; authorization, consumption binding, and execution request bind that plan. Request and plan schemas are unchanged.

Target is exactly `TPEX:6488`. The fixed source order is TPEx attention/H1 v1, TPEx disposition/H1 v1, then TPEx `tpex_cmode`/H1 v2. TLS uses the existing compatibility SSL policy with certificate and hostname verification, 60 second timeout, 4 MiB response ceiling, retry 0, redirects disabled, no fallback, GET-only.

## Offline integrated acceptance

Offline acceptance passed with **156 passed, 0 failed, 0 skipped**, and market GET/HEAD/POST `0/0/0`. The controlled payloads flowed through approval, preflight, claim, dispatch, OperationResult v2, Bundle v1, Receipt v1, lineage, Result V3, Audit V3, and the server-owned Mode C materialization/read/audit/AI-handoff path.

Coverage included the three-source composite, cmode exact no-match, multiple disposition rows, component failure independence, blank and U+FF39 native markers, authority/order/endpoint failures before transport, false authorization blocking, target/source mismatch, and artifact hash tampering. No native cmode value was promoted into suspension, and no blank or absent row was promoted into normal/tradeable status.

## Live integrated acceptance

The first authorized candidate run completed its source pipeline and made 3 GETs, but the runner looked for the composite in the outer temporary directory rather than the authorization-bound package directory. The runner failed during post-processing; temporary cleanup removed the per-source response summary. That run's HTTP results and response hashes are therefore **not available and are not inferred**.

After fixing the runner path, a second bounded acceptance repeated the same fixed candidate pipeline for auditable source metadata. This concrete rerun used three GETs, one per predeclared endpoint. It used no retries, HEAD, POST, fallback, or polling. Total A2.6 market requests are **GET 6 / HEAD 0 / POST 0**; the authorized ceiling was GET≤10 / HEAD≤10 / POST=0.

| Source | HTTP | Bytes | SHA-256 | Retrieved at (UTC) | H1 component | Status | Component SHA-256 |
|---|---:|---:|---|---|---|---|---|
| `H1-TPEX-ATTENTION-OPENAPI` | 200 | 9,536 | `bb91afe4e485ff63b04f38305573972104bd65499c876e2c2bb4e8ee4a641ec7` | `2026-10-07T08:07:45.098421Z` | H1 v1 | partial | `f1661706a9d0eefa7dc04ac85075cb149689f21e172ee0d8cf48e26b13178622` |
| `H1-TPEX-DISPOSITION-OPENAPI` | 200 | 20,222 | `fb1f07af0caf6bef5b4545bd0323736bf70c6ca70bc21368c2fd19840d5789e0` | `2026-10-07T08:07:45.231610Z` | H1 v1 | partial | `150eeea2d408ee3c5d46117b4d7f708c5295021cac8dd08471bd097bc88fc8ff` |
| `H1-TPEX-CHANGED-TRADING-OPENAPI` | 200 | 5,039 | `26c7ead445eda8427724b31255650c2c8edcc09d0e8b9abf8eae4f071003856e` | `2026-10-07T08:07:45.350017Z` | H1 v2 | partial | `6d69a11430c11466c9c3b6a4412cb7bdce40c1199f3682f5f64d222a0db411b3` |

Each successful-run response had `Content-Type: application/json`, effective URL equal to the requested official URL, TLS policy `compatibility`, redirect count 0, attempt number 1, and no source-contract drift. The exact response bodies and full-market rows were not persisted or committed.

The composite is `trading_status_context_composite.v1`, SHA-256 `adb055c3e933c2f79c3b5fe696ddae01e9f2c77124281810f5a9a3cb81b6b40d`. Its status is `partial`; canonical coverage is `attention`, `disposition`; uncovered types are `changed_trading_method`, `resumption`, `suspension`; canonical item count is 1; native observation count is 0; component count is 3. The live snapshot did not contain a matching cmode native row; this is represented as exact no-match, with zero canonical coverage. The fixture acceptance separately proves exact blank and U+FF39 preservation and unresolved caveats.

OperationResult v2 succeeded; Bundle v1, Receipt v1, lineage, Result V3, Audit V3, and Mode C handoff were validated. All three component identities, hashes, source attempts, and citations remained traceable. Handoff output remained source-separated and carried the exact no-match caveat. Component failure independence passed offline.

## Validation

- Focused integrated/regression suite: 156 passed, 0 failed, 0 skipped.
- `python scripts/validate_phase_h_v3_contracts.py`: PASS.
- `python -m compileall -q scripts server tests`: PASS.
- `git diff --check`: PASS.
- Strict duplicate-key JSON check: PASS; duplicate member names = 0.
- `python scripts/run_test_profile.py default-ci`: **1,282 passed, 0 failed, 1 skipped, 5 deselected, 18 warnings**; 376.69 seconds. Its deterministic test-profile result is reported separately from the six live GETs above.

## Protected contract hashes

All remained unchanged:

- H1 v1: `638200509cde05613d17bd4158d1676c3c086d2b10aa2f50fb85d52febe30ecf`
- H1 v2: `818de1e9c501b4c4d0bb06d6a1503dafba7b63dc60977791f7842cd8b5a31d38`
- Composite v1: `3d34a1cb2112716211e39536b221994952aabd1c2723d3ed5f61ee8b0f224106`
- Result V3: `9269fc9e5e07884fa2de791eae902ee57b3d937dbb793318ca4aff1a93fc5bcb`
- OperationResult v2: `9d6430254215ae0b4048e0352f6902c629e4069530b1c9a267f1ee50d4c5bd64`
- H0-G manifest: `6c1f23ed12a0d3bffcb7b964197eda6ee6a36d8c95ef1a8c5d6106ef31ea89f6`
- Request v1: `c56add4bdb200d7dc1a1e9c27d576fefbf434dc7a8658fd17000c4ae8ee84cac` (committed Git blob bytes; working tree has CRLF conversion)
- Request v2: `757d864c3a00d296f8ebf2eccdbb47a1d39ca8a222e9d939f34ef854f4245e3b`
- Request v3: `b0901dbf63db3a8bc44b8fec4cb0cdc90f77e153d954266f98c690453864f3f6`
- Bundle v1: `9eb901b99db3a7b56d251e70c00f83ebc99b0f0587fc77fee8aca573f9049aad`
- Receipt v1: `cd70b135e751214d467dbf7ca1924fc2ce8a61461b2276defae7bd30a23e4d26`
- Audit V3: `94208ac6f4c13bcde294de1a8c7cf6be23245d738b5dcd36fffcac1ab134c4cc`

## Activation decision and boundary

Readiness is `J_B03_A2_6_REPRESENTATIVE_INTEGRATED_ACCEPTANCE_PASS_ACTIVATION_READY`. **No production activation was performed.** The active `phase_h_h1_tpex_attention_executor` remains unchanged; disposition and cmode remain `activation_state=eligible`, `runtime_executable=false`. Routing, catalog, registry, preferred version, and MCP public surface did not change; MCP remains 6 tools.

If separately authorized later, the canonical activation surface would require changes to:

- `config/phase_h_h1_dormant_source_descriptors.json` — source activation/executability state;
- `docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json` — capability support and limitations;
- `docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json` — selected composite executor and operation policy;
- `config/m8r_06_03_executor_registry_metadata.json` — canonical executor registration;
- `scripts/m8r_06_03_production_adapter.py` — production-owned executor integration. The acceptance-only candidate is not registered.

No activation is authorized by this Stage A. Stop and wait for explicit Owner authorization before making those changes.

## Current issue state

- H0-SRC-01E: OPEN
- H0-SRC-02: OPEN
- J-B03: HOLD
- J-B04: BLOCKING
- Phase J: NOT_STARTED
- `data/`: untouched
- Raw market payload committed: no

## J-B03-A2.6 Stage B — Production Activation

**Owner authority:** `USER_CHAT_2026-10-07_J_B03_A2_6_PRODUCTION_ACTIVATION_AUTHORIZATION`
**Disposition:** `J_B03_A2_6_PRODUCTION_ACTIVATION_ACCEPTED`
**PR:** #321 remains OPEN / Draft; activation exists in this reviewed branch and has not been merged or deployed.
**Stage-B commits:** `414f904`, `d01a1cd`, `5cd743a`, `5b0d7d4`, `e6193e5`, `9c16b51`.

Stage A remains preserved above as historical acceptance evidence. Stage B promotes the production `trading_status_context` route for TPEX equities to `phase_h_h1_tpex_composite_executor`, returning `trading_status_context_composite.v1`. The approved request and active local Security Master resolved the live target to `TPEX:6488` / `TW0006488000`; production execution is not fixed to 6488. Offline tests also bound `TPEX:1234` through the same shared core.

The fixed ordered source set is TPEx attention (H1 v1), TPEx disposition (H1 v1), and TPEx `tpex_cmode` (H1 v2). The Stage-A candidate wrapper and production executor share the acquisition/normalization/persistence/composition core. No fourth source or automatic fallback is configured. The legacy attention executor remains registered for rollback but is not selected.

| Source | Activation | Runtime executable | Live result |
|---|---|---:|---|
| `H1-TPEX-ATTENTION-OPENAPI` | active | yes | H1 v1, partial, attention covered, 1 item |
| `H1-TPEX-DISPOSITION-OPENAPI` | active | yes | H1 v1, partial, disposition covered, 0 matching items |
| `H1-TPEX-CHANGED-TRADING-OPENAPI` | active | yes | H1 v2, partial exact no-match, 0 native observations |
| `H3-TWSE-DEFAULT-BOUNDED` | active | yes | pre-existing H3 source |

Active Phase-H source count is exactly **4**. Suspend-today, suspend-history, and TWSE H1 sources remain inactive. Attention route behavior remains unchanged. No preferred-version promotion or MCP surface change occurred; MCP remains six tools.

The final production-path run made exactly 3 GETs in fixed order, all HTTP 200, with TLS policy `compatibility`, redirects 0, retries 0, and no response-body persistence. Stage-B run 1 made 3 GETs but failed after source execution while the report code looked up a non-existent `source_id` field; its response metadata was not retained and its HTTP outcomes/hashes are not inferred. Run 2 made 3 GETs, all HTTP 200 with metadata captured, and completed the production checks before the report code used the wrong Bundle property name. Run 3 repaired that reporting defect and passed end to end. Stage-B total is **9 GET / 0 HEAD / 0 POST**. Stage A's accepted history remains **6 GET / 0 HEAD / 0 POST**, so A2.6 cumulative total is **15 / 0 / 0**, within the Stage-B ceiling of 10 GETs for Stage B alone.

The accepted live run used the production executor consistently in routing, plan, execution request, OperationResult, and registry. OperationResult v2 succeeded with `result_item_count=1`; Bundle v1 validated with 7 artifacts and total item count 1; Receipt v1 succeeded. Lineage, Result V3, Audit V3, and Mode C handoff passed. The composite status is `partial`, with canonical coverage `attention` + `disposition`; `changed_trading_method`, `suspension`, and `resumption` remain uncovered. It contains 1 canonical item, 0 native observations, and 3 source-separated components. The live snapshot had no matching disposition or `tpex_cmode` row for the bound target. This does not imply normal trading or tradeability. Offline tests retain coverage for blank and U+FF39 values as unresolved native evidence.

Live response evidence for the final run (full payloads were not persisted):

| Source | HTTP | Bytes | SHA-256 | Retrieved (UTC) |
|---|---:|---:|---|---|
| Attention | 200 | 9,536 | `bb91afe4e485ff63b04f38305573972104bd65499c876e2c2bb4e8ee4a641ec7` | `2026-10-07T09:32:30Z` |
| Disposition | 200 | 20,222 | `fb1f07af0caf6bef5b4545bd0323736bf70c6ca70bc21368c2fd19840d5789e0` | `2026-10-07T09:32:31Z` |
| `tpex_cmode` | 200 | 5,039 | `26c7ead445eda8427724b31255650c2c8edcc09d0e8b9abf8eae4f071003856e` | `2026-10-07T09:32:31Z` |

The final composite SHA-256 is `24a78e5e5ac30e85b7261f429a4e36173a1eb258ff142280311689dff2bbdf8b`. Its source component hashes are `ca622965ff00d93816ad5f001a934221e70feabb2ae9c7b61ae2bc3764b67848` (attention), `bbc8816ec16c70dbc8275a80c494dad84f212798e70ca5406724a2fb4b96c` (disposition), and `144bd67020cd8563743d881c9b3904c364248171402d040d4408a22c159b347b` (`tpex_cmode`).

The deterministic rollback proof restored the pre-Stage-B two-source topology in a copy; the composite route and registration were absent after rollback, while the legacy attention registration remained. No production change was reverted in the active branch.

Post-live focused Stage-B tests: **111 passed, 0 failed, 0 skipped**. Stage-B activation tests including the sanitized-report regression: **12 passed**. Pre-live broad offline suite: **332 passed, 0 failed, 0 skipped**. Repository validators, compilation, and diff checks passed. The final `default-ci` result is recorded in the paired JSON after completion.

Stage-B activation changes canonical descriptors, catalog, routing, registry, and production adapter in this branch only. No H1/Composite/Request/Result/OperationResult/Bundle/Receipt/Audit schema changed. No raw market payload was committed. The pre-existing `data/` directory was not touched.

## Current A2.6 issue state after Stage B

- H0-SRC-01E: OPEN
- H0-SRC-02: OPEN
- J-B03: HOLD
- J-B04: BLOCKING
- Phase J: NOT_STARTED
- Complete H1 coverage: not claimed
- PR #321: OPEN / Draft / unmerged

#### Phase I historical compatibility repair

The first full `default-ci` run exposed 10 historical Phase I comparison failures after the authorized A2.6 current Phase-H Catalog/Routing/Registry changes. The historical records themselves were unchanged; several validators compared the new shared current-state bytes directly with their earlier snapshots. The bounded repair now validates the exact active A2.6 H1 route and four-source authority before projecting only the authorized A2.6 overlay out of old comparisons. I3-A4 recorded hashes are checked against the committed pre-A2.6 snapshot. No Phase I source, executor, semantic contract, or historical record was changed. The previously failing Phase I focused group then passed: **210 passed, 0 failed, 0 skipped**.

The complete `default-ci` profile then passed: **1,282 passed, 0 failed, 1 skipped, 5 deselected, 18 warnings** in 304.10 seconds. The deterministic profile reported `network_may_have_occurred=false`; Stage-B market calls are accounted separately above.
