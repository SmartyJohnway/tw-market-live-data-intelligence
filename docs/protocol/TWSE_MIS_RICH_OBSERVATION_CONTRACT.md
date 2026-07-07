# TWSE MIS rich observation contract (M7A-02/M7A-02A)

## Purpose

M7A-02 defined a backward-compatible, schema-only contract for future TWSE MIS rich observation facts. M7A-02A aligned that schema with operator-observed closing-auction, post-close, market-mode, and index evidence. M7A-03/M7A-04 now populate that contract from TWSE MIS runtime rows while preserving the existing top-level normalized observation shape.

## Scope and runtime status

Historically, M7A-02/M7A-02A and `scripts/observation_contract.py::build_empty_twse_mis_rich_facts` defined the contract only. Those tasks did not populate rich facts from live MIS rows and did not call the optional attach helper from runtime parser code. After M7A-03/M7A-04, TWSE MIS runtime normalization attaches populated candidate rich facts for TWSE MIS rows only; FastAPI, MCP, frontend, source-health, scheduler, startup, and conversation-context exposure remain unchanged.

The backward compatibility rule is: existing top-level observation fields remain authoritative for current runtime output until a later task explicitly changes parser behavior. In particular, `price_like_value`, `price_source_field`, `source_timestamp`, `reference_only`, `data_quality_flags`, `source_risk_flags`, and `caveats` must be preserved by any optional copy-and-attach workflow.


## M7A-03/M7A-04 runtime parser and fixture status

M7A-03 attaches `twse_mis_rich_facts` in the TWSE MIS runtime normalization path. The attachment is source-scoped to `TWSE_MIS` observations and is performed after existing top-level fields are normalized.

The M7A-03 parser preserves existing top-level observation behavior:

- Existing `z`/`y` fallback is preserved.
- Existing `reference_only` semantics are preserved.
- `pz` does not override the top-level last price or `price_like_value`.
- `ps` does not override top-level current volume behavior.
- Rich facts remain conservative runtime-parsed candidates and do not claim official API field-dictionary validation.
- `safe_for_ai_context` remains `false`.

M7A-04 added network-free fixtures and tests for closing auction, post-close, index, placeholder, malformed numeric, regular-session, missing-field, and ladder-mismatch cases.

M7A-05/M7A-06 remain responsible for downstream FastAPI/MCP/frontend/conversation compatibility checks and final acceptance closure.

## Evidence and official-documentation policy

No official public TWSE MIS API field dictionary is known for `mis.twse.com.tw/stock/api/getStockInfo.jsp`. Therefore this contract sets `official_documented: false`, `api_field_dictionary_available: false`, and uses candidate/evidence language only.

Evidence basis for this schema is limited to:

- M7A-01D successful bounded probe evidence.
- User/operator-provided `tse_2330.tw` response and UI screenshot cross-check.
- User/operator-provided `tse_t00.tw` index response and UI screenshot cross-check.
- User/operator-provided closing-auction and post-close MIS detail-item evidence from 2026-07-07.
- Community reverse-engineering references, which are not official TWSE documentation.

## Closing-auction operator evidence: 2026-07-07 13:27

Operator evidence for regular-board `2330` during the closing-auction/trial window observed:

```text
ps=3552
pz=2440.0000
z="-"
tv="-"
ts=1
```

Interpretation for schema purposes only: `ps`/`pz` are closing-auction reference candidates, and `z`/`tv` may remain placeholders during the trial window. This evidence supports state-dependent candidate fields, not runtime normalization and not official API dictionary validation.

## Post-close official MIS detail-item evidence: 2026-07-07 13:33

Operator evidence for regular-board `2330` after final match observed:

```text
z=2440.0000
tv=3721
ps=3721
pz=2440.0000
s=3721
v=27734
ts=0
```

The official MIS regular-board UI showed cumulative volume `27734`, trade price `2440.00`, trade volume `3721`, and visible trial reference fields as `-`.

Interpretation for schema purposes only: `ps`/`pz` are state-dependent reference or match fields, not trial-only fields. `s` is a match-volume shadow/raw candidate. `ts` is a session/trial-state flag candidate. This is operator evidence supported by official MIS UI cross-checks, but it is not an official API field dictionary.

## Market mode and quantity unit policy

Official MIS regular-board and intraday odd-lot UI evidence labels units as `元，交易單位`. Because the API field dictionary is unavailable and TWSE market modes have different trading semantics, market mode is required before runtime unit normalization. Do not mix intraday odd-lot semantics into regular-board rows.

The reusable schema policy is:

```text
official_mis_ui_unit_label = 交易單位
api_field_dictionary_available = false
market_mode_required = true
unit_verified_for_runtime_normalization = false
```

Any regular-board lot-style interpretation remains non-authoritative and market-mode-dependent.

## Security rows vs index rows

TWSE MIS rows need row context before interpreting fields. A security row such as `tse_2330.tw` can expose equity price candidates, displayed depth candidates, volume candidates, state-dependent auction/reference candidates, session-state candidates, and limit/reference candidates. An index row such as `tse_t00.tw` uses fields such as `z`, `y`, `o`, `h`, and `l` as index levels, not equity prices, and may not contain displayed depth, limit up/down, or security-volume fields.

The contract therefore includes `market_mode_facts`, `instrument_facts.instrument_kind_candidate`, and `price_facts.price_domain`. Future parser values may include `regular_board`, `intraday_odd_lot`, `index`, or `unknown` for market mode; `security`, `index`, or `unknown` for instrument kind; and `equity_price`, `index_level`, or `unknown` for price domain.

## Price facts and z/y fallback preservation

`price_facts` reserves `last_value`, `previous_close`, `open`, `high`, and `low` with source fields `z`, `y`, `o`, `h`, and `l`. For security rows these are equity-price candidates. For index rows such as `tse_t00.tw`, they are index-level candidates.

M7A-02/M7A-02A did not change the existing `z`/`y` parser fallback. M7A-03 preserves that existing top-level fallback: if `z` is unavailable, existing top-level normalization may still use numeric `y` as a reference value with `reference_only`, but rich `price_facts.last_value` does not infer a current last price from bid/ask midpoint, previous close, `ps`, `pz`, or any other field. Rich `price_facts.fallback_reference_field` records `y` only as fallback metadata when `z` is placeholder or malformed and `y` parses numeric.

## Displayed depth snapshot policy

`displayed_depth_facts` is schema for security-row displayed-depth snapshots only. Candidate fields are `b`/`g` for displayed bid price/quantity ladders and `a`/`f` for displayed ask price/quantity ladders. Quantity units follow the shared `交易單位` policy and remain `market_context_required` with runtime normalization unverified.

For index rows, a future parser may set `applicable: false` with `applicability_reason: index_observation_has_no_displayed_depth_fields`. M7A-02/M7A-02A does not populate that value.

Displayed depth must not be described as support/resistance, true liquidity, order-book truth, main force, or a trading signal.

## Volume and unit-unverified policy

`volume_facts` reserves raw `v`, `tv`, and `ps`. A regular-board quantity interpretation is only a non-authoritative, market-mode-dependent candidate. The schema does not mark lots, shares, `f`, `g`, `v`, `tv`, `ps`, `s`, `m`, or `r` units as official API field-dictionary values or verified for runtime normalization.

## Limit/reference and state-dependent auction/reference candidates

`limit_or_reference_facts` reserves `u`, `w`, `pz`, `bp`, and `ps`. For index rows, a future parser may set `applicable: false` with `index_observation_has_no_limit_up_down_fields`.

`auction_or_reference_facts` supersedes the earlier trial-only framing because `ps`, `pz`, `s`, and `ts` are state-dependent. Closing-auction evidence supports `ps`/`pz` as reference candidates while post-close evidence supports `ps`/`pz` as final match/reference candidates, `s` as a match-volume shadow candidate, and `ts` as a session/trial-state flag candidate.

## Session-state candidates

`session_state_candidate_facts` reserves `ip`, `p`, `s`, and `ts`. Operator evidence observed `ts=1` during the closing-auction trial window and `ts=0` after final match. This supports only a candidate state flag, not a validated official API definition.

## Index market facts and t00 evidence

For `tse_t00.tw`, operator evidence observed:

```text
z=45479.11
m=15235848
r=4629735
```

The official MIS UI showed `成交數量` and `筆數`. The schema therefore uses `m_candidate_semantic: index_market_traded_quantity_candidate` and `r_candidate_semantic: index_market_trade_count_candidate`, with `evidence_level: official_mis_ui_cross_checked_not_field_dictionary`. This is not official API field dictionary validation and must not be applied globally to security rows.

## Raw-only fields

The raw-only unknown set includes `pid`, `#`, `m%`, `mt`, `ip`, `i`, `it`, `p`, `q`, `oa`, `ob`, `ot`, and `nu`. `s` and `ts` are not treated as purely unknown because they also appear in state-dependent auction/reference and session-state candidate groups. `nu` remains unknown/preserve-raw-only/not-safe-yet.

Fields `q`, `oa`, `ob`, and `ot` were not observed in the M7A-01D successful probe and remain conservative raw/candidate fields.

## Timestamps

`timestamp_facts` reserves raw `d`, `t`, `tlong`, `%`, `^`, and `ot`. The contract distinguishes source timestamp candidates from retrieval time and does not assert realtime status.

## Semantic confidence model

`semantic_confidence` defaults to schema-only values in the empty M7A-02/M7A-02A helper: `official_documented: false`, `probe_observed: false`, `ui_cross_checked: false`, `community_supported: false`, `runtime_validated: false`, `unit_verified: false`, and `evidence_level: schema_only`. M7A-03 populated runtime-parsed candidate confidence for attached rich facts while keeping `official_documented: false` and `unit_verified: false`.

## AI exposure policy and forbidden interpretations

The empty rich facts contract is not safe for AI context, and the M7A-03 runtime-populated candidate rich facts also remain not safe for AI context pending downstream compatibility and exposure decisions. Forbidden interpretations include buy signal, sell signal, hold, target price, support/resistance, main force, true liquidity, order-book truth, realtime guarantee, and execution feed.

## Future compatibility and acceptance work

M7A-03 populated this contract from MIS rows, set row-context applicability for security versus index rows, carried raw values into the proper groups, recorded placeholder/malformed fields, and added conservative runtime-parsed candidate confidence. M7A-05/M7A-06 must verify downstream compatibility and final acceptance while preserving the no-official-API-dictionary policy unless official TWSE API field documentation is found.
