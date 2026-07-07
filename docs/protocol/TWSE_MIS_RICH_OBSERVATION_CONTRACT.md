# TWSE MIS rich observation contract (M7A-02)

## Purpose

M7A-02 defines a backward-compatible, schema-only contract for future TWSE MIS rich observation facts. The contract gives later parser work a stable place to put raw MIS field values, candidate normalized facts, evidence status, and AI exposure guardrails without changing the current normalized observation shape.

## Scope and runtime status

This document and `scripts/observation_contract.py::build_empty_twse_mis_rich_facts` define the contract only. M7A-02 does not populate rich facts from live MIS rows, does not call the optional attach helper from runtime parser code, and does not change FastAPI, MCP, frontend, source-health, scheduler, startup, conversation context, or `scripts/m5k_common.py` behavior.

The backward compatibility rule is: existing top-level observation fields remain authoritative for current runtime output until a later task explicitly changes parser behavior. In particular, `price_like_value`, `price_source_field`, `source_timestamp`, `reference_only`, `data_quality_flags`, `source_risk_flags`, and `caveats` must be preserved by any optional copy-and-attach workflow.

## Evidence and official-documentation policy

No official public TWSE MIS data dictionary is known for `mis.twse.com.tw/stock/api/getStockInfo.jsp`. Therefore this contract sets `official_documented: false` and uses candidate/evidence language only.

Evidence basis for this schema is limited to:

- M7A-01D successful bounded probe evidence.
- User/operator-provided `tse_2330.tw` response and UI screenshot cross-check.
- User/operator-provided `tse_t00.tw` index response and UI screenshot cross-check.
- Community reverse-engineering references, which are not official TWSE documentation.

## Security rows vs index rows

TWSE MIS rows need row context before interpreting fields. A security row such as `tse_2330.tw` can expose equity price candidates, displayed depth candidates, volume candidates, and limit/reference candidates. An index row such as `tse_t00.tw` uses fields such as `z`, `y`, `o`, `h`, and `l` as index levels, not equity prices, and may not contain displayed depth, limit up/down, or security-volume fields.

The contract therefore includes `instrument_facts.instrument_kind_candidate` and `price_facts.price_domain`. Future parser values may include `security`, `index`, or `unknown` for instrument kind, and `equity_price`, `index_level`, or `unknown` for price domain.

## Price facts and z/y fallback preservation

`price_facts` reserves `last_value`, `previous_close`, `open`, `high`, and `low` with source fields `z`, `y`, `o`, `h`, and `l`. For security rows these are equity-price candidates. For index rows such as `tse_t00.tw`, they are index-level candidates.

M7A-02 does not change the existing `z`/`y` parser fallback. If `z` is a placeholder such as `-`, the parser must not infer a current last price from bid/ask midpoint, previous close, or any other field. Existing `y` fallback and `reference_only` behavior are preserved until a later parser task explicitly changes them.

## Displayed depth snapshot policy

`displayed_depth_facts` is schema for security-row displayed-depth snapshots only. Candidate fields are `b`/`g` for displayed bid price/quantity ladders and `a`/`f` for displayed ask price/quantity ladders. Quantity units remain `market_context_required` and `quantity_unit_verified: false`.

For index rows, a future parser may set `applicable: false` with `applicability_reason: index_observation_has_no_displayed_depth_fields`. M7A-02 does not populate that value.

Displayed depth must not be described as support/resistance, true liquidity, order-book truth, main force, or a trading signal.

## Volume and unit-unverified policy

`volume_facts` reserves raw `v`, `tv`, and `ps`. A community default candidate may be regular-board lots, but the schema does not mark lots, shares, `f`, `g`, `v`, `tv`, `ps`, `m`, or `r` units as official or verified. These remain `market_context_required` or `unverified` until row-context and source evidence are added.

## Limit/reference and auction/trial candidates

`limit_or_reference_facts` reserves `u`, `w`, `pz`, `bp`, and `ps`. For index rows, a future parser may set `applicable: false` with `index_observation_has_no_limit_up_down_fields`.

`auction_or_trial_facts` exists because `ps`, `pz`, and possibly `bp` may represent closing-auction or trial-reference candidates. Current samples are mostly placeholders, so these fields remain candidate-only pending auction-window evidence.

## Index market facts and m/r policy

`index_market_facts` reserves `m` and `r` for index rows such as `tse_t00.tw`, where operator UI cross-checks support candidate meanings of market traded lots and market trade count. This is not an official data dictionary and must not be applied globally to security rows.

## Raw-only fields

The raw-only unknown set includes `pid`, `#`, `m%`, `mt`, `ip`, `i`, `it`, `p`, `s`, `ts`, `q`, `oa`, `ob`, `ot`, `m`, and `nu`. `m` can have an index-specific candidate meaning in `index_market_facts`, but globally it remains raw-only unless row context justifies a candidate field. `nu` remains unknown/preserve-raw-only/not-safe-yet.

Fields `q`, `oa`, `ob`, and `ot` were not observed in the M7A-01D successful probe and remain conservative raw/candidate fields.

## Timestamps

`timestamp_facts` reserves raw `d`, `t`, `tlong`, `%`, `^`, and `ot`. The contract distinguishes source timestamp candidates from retrieval time and does not assert realtime status.

## Semantic confidence model

`semantic_confidence` defaults to schema-only values: `official_documented: false`, `probe_observed: false`, `ui_cross_checked: false`, `community_supported: false`, `runtime_validated: false`, `unit_verified: false`, and `evidence_level: schema_only`. M7A-03 may populate field-specific confidence from parser evidence, but M7A-02 does not.

## AI exposure policy and forbidden interpretations

The empty rich facts contract is not safe for AI context because it is defined but not runtime-populated. Forbidden interpretations include buy signal, sell signal, hold, target price, support/resistance, main force, true liquidity, order-book truth, realtime guarantee, and execution feed.

## Future M7A-03 work

M7A-03 may populate this contract from MIS rows, set row-context applicability for security versus index rows, carry raw values into the proper groups, record placeholder/malformed fields, and add field-specific evidence confidence. M7A-03 must still preserve the no-official-dictionary policy unless official TWSE documentation is found.
