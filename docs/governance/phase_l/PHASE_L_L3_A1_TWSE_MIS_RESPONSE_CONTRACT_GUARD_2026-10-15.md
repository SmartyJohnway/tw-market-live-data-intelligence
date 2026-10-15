# Phase L L3-A1 — TWSE MIS Returned Identity & Response Contract Guard

**Base:** `689bd30480a4e640ee522f44b4966842c634db4d`
**Branch:** `phase-l/l3-a1-mis-response-contract-guard`
**Authority:** frozen L0; L2 Owner closure; merged and Owner-accepted L3-A0; the explicit Owner authorization in the A1 tranche instruction.
**Technical disposition:** `L3_A1_TWSE_MIS_RESPONSE_CONTRACT_GUARD_ACCEPTANCE_REVIEW_PASS`
**Owner acceptance:** not recorded.
**Scope:** current TWSE MIS current-observation seam in `scripts/m5k_common.py` only; no fresh source access.

## Predecessor and reproduced defect

L0 is frozen, L1 and L2 are closed, and L3 is started. L3-A0 is Owner-accepted and merged through PR #355; PR #356 reconciled its closure at this base. A0 recorded G01 as a blocking correctness gap: the batch map selected a row by request-channel `key`, then `normalize_twse_mis_row` attached the caller's identity without first checking the returned row.

The retained A0 witness used requested `TWSE:2330` with a matching `key=tse_2330.tw_20261015` and `ch=2330.tw`, but `c=2317` and `ex=otc`. Before A1 the runtime emitted a successful caller-bound observation with value `1015.0`. The A1 regression injects the same contradictory shape and now produces no observation and a typed identity failure.

## Returned identity contract

The current complete accepted MIS rows in `tests/fixtures/market_sources/twse_mis/success.json` and `normalization_v2_matrix.json` contain `c`, `ex`, and `ch`; those fixtures include TWSE, TPEX/OTC, ETF, and the `t00` TAIEX route. The historical accepted rich-facts rows retain `key` with the channel followed by an opaque suffix. Based on those current source artifacts:

| Field | Contract | Validation |
|---|---|---|
| `c` | Required | Must be a non-empty string and equal the requested source symbol from the planned MIS channel, case-insensitively. For TAIEX the source symbol is `t00`, not the caller label `TAIEX`. |
| `ex` | Required | Must be `tse` or `otc`, case-insensitively, and agree with the planned market route. |
| `ch` | Required | Must be `<source-symbol>.tw`; its symbol must agree with `c` and the planned route. It does not itself encode exchange. |
| `key` | Optional, if absent | If present, it must be a string whose canonical route is `tse_<symbol>.tw` or `otc_<symbol>.tw`; a trailing underscore suffix is treated as opaque metadata and is not identity. Its route must agree with `c`, `ex`, `ch`, and the requested channel. |

The explicit route mapping is `twse → tse`, `tpex/otc → otc`. It is based on `source_plan_for_instrument` and the current route semantics; no substring or nearest-match heuristic is used. All returned claims are checked together. A coherent returned identity for a different target is a mismatch; contradictory claims are a conflict. A matching `key` never overrides contradictory `c`, `ex`, or `ch`.

In a batch, key, channel, code, and exchange facts are used only to find candidate requested targets. Each row must then independently validate before normalization. An ambiguous row claiming multiple requested targets is rejected. Multiple rows claiming one target are rejected as `source_response_duplicate_ambiguous`, including byte-equivalent decoded rows; there is no last-write-wins behavior. An unrelated extra row is not assigned to a requested target. A requested target with no coherent row keeps the existing `missing_from_source_response:<channel>` result.

## Response, decoding, and failures

The MIS response body must be strict UTF-8 and valid JSON with an object root, a list-valued `msgArray` containing only objects, and a non-empty `rtcode`/`rtCode` equal to the retained success code `0000`. If both aliases are present, they must agree. Duplicate JSON object keys are rejected. Invalid bytes produce `source_response_decode_failed`; malformed JSON/envelope/status produces `source_response_contract_invalid`; non-200 HTTP status and other acquisition failures remain typed transport failures. When fallback is disabled, acquisition failure stays a source failure rather than being relabeled as a missing row. Contract failures do not trigger individual fallback. Existing bounded individual fallback remains available only after batch transport failure, follows the same strict response/identity checks, and is not attempted after an identity mismatch.

An empty `msgArray` with a valid success envelope remains legitimate no-row evidence and yields the existing missing-target failure; it is not recast as schema drift or a successful observation. Bounded failure summaries carry expected market/symbol/channel and only returned `c`, `ex`, `ch`, and `key` identity facts. They do not include a raw row or response body.

The new bounded reason vocabulary is:

```text
source_response_identity_mismatch
source_response_identity_conflict
source_response_duplicate_ambiguous
source_response_contract_invalid
source_response_decode_failed
source_failed:http_status
source_failed:transport
```

Existing `reference_value_only`, `value_unavailable`, missing-target, timestamp/currentness, and partial-observation semantics remain in their existing paths. `z` remains the current/last value candidate; `y` remains reference-only when `z` is unavailable. Identity checks precede normalization and are separate from freshness. Current observation normalization is unchanged.

## Scope containment

- TWSE and TPEX/OTC MIS equity/ETF routes share the guard. `tse` and `otc` cross-market rows fail closed.
- The TAIEX `tse_t00.tw` route is covered and remains valid with returned `c=t00`, `ex=tse`, and `ch=t00.tw`.
- TAIFEX MIS is a separate source and is unchanged.
- Individual fallback policy and request bounds are unchanged; identity/contract rejection does not trigger fallback or a refetch.
- No Catalog, route, executor, activation, public HTTP/MCP, Unified Request, Result/Audit schema, authorization, or evidence-family change.
- No CP950/research CSV or other source encoding policy change.

## Verification

Focused deterministic gate, run behind a socket guard permitting only loopback and replacing MIS `urlopen` with in-memory responses:

```text
PowerShell: $a1GatePath = Join-Path $env:TEMP 'tw-market-l3-a1-offline-gate.py'
python -X utf8 -B $a1GatePath
12 selected test modules: 167 passed, 0 failed, 0 warnings
L3_A1_EXTERNAL_SOCKET_ATTEMPTS=0
```

The gate runs `pytest.main` with `-q` and these exact modules:

```text
tests/unit/test_l3_a1_twse_mis_response_contract.py
tests/unit/test_m5k_workflow.py
tests/unit/test_m5l_live_source_adapter_matrix.py
tests/unit/test_m6d_ssl_policy.py
tests/unit/test_twse_mis_normalization_v2.py
tests/unit/test_twse_mis_rich_facts_compatibility.py
tests/unit/test_twse_mis_rich_facts_parser.py
tests/unit/test_twse_mis_rich_field_probe_helpers.py
tests/unit/test_twse_mis_rich_observation_contract.py
tests/unit/test_m7g_twse_mis_market_route_semantics.py
tests/unit/test_m8r_06_03_production_adapter.py
tests/unit/test_m8r_08b_mcp_tool_contracts.py
```

The new A1 module alone passes **35 passed, 0 failed** with `python -X utf8 -B -m pytest -q tests/unit/test_l3_a1_twse_mis_response_contract.py`.

Additional validators:

```text
python -X utf8 -B scripts/validate_source_registry.py       PASS
python -X utf8 -B scripts/validate_portable_catalog_sync.py PASS
python -X utf8 -B scripts/validate_runtime_skill_guide_sync.py PASS; tool_count=6
python -X utf8 -B scripts/validate_v1_public_contracts.py   PASS; tool_count=6
```

Every new runtime test injects response bytes and patches `urlopen`; the guarded suite recorded zero external socket attempts. `write_latest=False` is used throughout. No Security Master, Watchlist, Result/Audit, or other production state was initialized or mutated. No live market/source GET or POST occurred.

## Remaining boundary

This closes the A0 G01 MIS wrong-binding path for the covered seam. A0 G03 EOD result-diagnostic propagation remains a separate candidate gap, not included here. Other A0 hardening/probe/fixture gaps remain deferred. No fresh live probe was needed or authorized. L3-A2 is not authorized; L4-L7 remain not authorized. This technical disposition is a candidate for independent exact-head review, not Owner acceptance or L3 closure.
