# TWSE MIS Rich Observation Contract Schema

## 1. Purpose

M7A-02 defines an optional nested rich-facts contract for future `TWSE_MIS` observation rows. The contract records where validated TWSE MIS candidates may eventually live while preserving the current thin M5K/M5N observation output.

## 2. Schema-only scope

This milestone is schema-only. It adds a deterministic helper, `scripts/observation_contract.py::build_empty_twse_mis_rich_facts`, and tests the shape. The current runtime parser does not populate the rich groups in M7A-02.

## 3. Backward compatibility rule

Existing top-level fields such as `price_like_value`, `value`, `price_source_field`, `reference_only`, `source_timestamp`, `data_quality_flags`, `source_risk_flags`, and `caveats` remain unchanged. If a future caller opts into `attach_empty_twse_mis_rich_facts`, it must receive a copy and must not mutate the original observation.

## 4. Fact groups and raw MIS source fields

The schema defines these groups:

- `price_facts`: `z`, `y`, `o`, `h`, and `l` candidates.
- `volume_facts`: raw `v` and `tv` candidates with units unverified.
- `displayed_depth_facts`: raw ladder fields `b`, `g`, `a`, and `f` as displayed-depth snapshot candidates only.
- `limit_or_reference_facts`: `u`, `w`, `pz`, `bp`, and `ps` candidates.
- `identity_facts`: `c`, `ch`, `ex`, `n`, `nf`, plus unknown identity-like fields `m` and `nu` preserved without assigning semantics.
- `timestamp_facts`: `d`, `t`, `tlong`, `%`, and `ot` candidates.
- `quality_facts`: field presence, placeholder, malformed, ladder mismatch, unit-unverified, and unknown/raw-only tracking.
- `ai_exposure_policy`: explicit non-exposure and forbidden interpretation guardrails.

## 5. Evidence basis from M7A-01D

M7A-01D committed compact successful evidence at `research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_summary_20260707T034516Z.json`. That evidence used `bootstrap_then_api`, observed all six requested bounded symbols, and preserved newly observed unknown fields `m` and `nu`.

## 6. Unknown fields `m` and `nu`

`m` and `nu` remain unknown, preserve-raw-only, not-safe-yet fields. M7A-02 adds them to the known forensic field list and to the rich schema's unknown identity field placeholders, but does not assign semantics or expose them as AI facts.

## 7. Unit-unverified policy for `v`, `tv`, `g`, and `f`

The schema keeps `v`, `tv`, `g`, and `f` unit-unverified. Future parser work must not label them as shares, lots, or any stronger unit until evidence and review support that claim.

## 8. Displayed depth snapshot policy

`b`, `a`, `g`, and `f` are represented only as displayed-depth snapshot candidates. The schema does not treat them as a complete book, guaranteed executable depth, or market intention.

## 9. z/y fallback preservation rule

Existing behavior remains authoritative: numeric `z` is preferred as the current price-like value; numeric `y` is used only as a reference fallback when `z` is unavailable. Defining `price_facts.previous_close` does not change fallback behavior.

## 10. `reference_only` preservation rule

A row that is `reference_only` under existing M5K logic must remain `reference_only` if rich facts are attached later. Rich facts must never make a `y` fallback appear current.

## 11. AI exposure policy

The empty rich schema sets `safe_for_ai_context = false` because M7A-02 defines the schema but does not populate or validate runtime rich facts. Future exposure requires parser implementation, tests, and evidence review.

## 12. Forbidden interpretations

The contract forbids interpretation categories including `buy_signal`, `sell_signal`, `hold`, `target_price`, `support_resistance`, `main_force`, `true_liquidity`, `order_book_truth`, and `realtime_guarantee`.

## 13. M7A-03 parser scope

M7A-03 may populate this schema from TWSE MIS raw rows after review. That future task must preserve current top-level observation fields, `z`/`y` fallback behavior, `reference_only`, source timestamps, caveats, source risk flags, and non-trading guardrails.
