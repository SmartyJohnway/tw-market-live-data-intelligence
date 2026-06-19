# M2D-02 Completion Report

## Status
**M2D_02_COMPLETED**

## Summary of Completed Work

This task successfully established the full field dictionaries and normalized EOD quote contracts for both TWSE and TPEx official OpenAPI endpoints, alongside bounded parser helpers directly incorporated into the probe flow.

### TWSE Field Dictionary
- Location: `docs/protocol/TWSE_OPENAPI_FIELD_DICTIONARY.md`
- Documented fields such as `Code`, `Name`, `OpeningPrice`, `HighestPrice`, `LowestPrice`, `ClosingPrice`, `TradeVolume`, `TradeValue`, `Transaction`, and `Date`.
- Implemented conservative mappings, noting that schema drift frequently occurs regarding the `Date` field presence.

### TPEx Field Dictionary
- Location: `docs/protocol/TPEX_OPENAPI_FIELD_DICTIONARY.md`
- Documented fields such as `SecuritiesCompanyCode`, `CompanyName`, `Open`, `High`, `Low`, `Close`, `TradingShares`, `TransactionAmount`, `TransactionNumber`, and `Date`.
- Also mapped observed secondary metrics into `unmapped_raw_fields` (e.g., `Average`, `LatestBidPrice`, `Capitals`).

### Normalized EOD Quote Contracts
- Locations: `docs/contracts/twse_openapi_normalized_eod_quote_v1.md` and `docs/contracts/tpex_openapi_normalized_eod_quote_v1.md`.
- Specified robust validation routines, missing field fallbacks, explicitly outlined strict flags (e.g. `missing_trade_date`, `malformed_close`), and mandatory metadata constants (e.g., `source_type: official_openapi`, `freshness_status: eod_batch`).
- Enforced strict pass-through for the `raw_row` and unmatched fields to `unmapped_raw_fields`.

### Probe / Normalizer Implementation
- We opted to implement the minimal bounded helper logic in M2D-02 given its simplicity and low risk.
- Modified `scripts/probe_twse_openapi.py` and `scripts/probe_tpex_openapi.py` to use `normalize_twse_openapi_row` and `normalize_tpex_openapi_row`.
- A generic `probe_openapi_utils.py` contains `safe_parse_float` and `safe_parse_int` to process string values containing commas or missing placeholder markers (`-`, `---`).
- Validated conservative missing date checks: if the `Date` string is empty or entirely missing, it securely binds to `None` and raises the `missing_trade_date` flag without imputing from system dates.
- Preserved existing standard envelope functionality: no aggressive batch scraping, scheduling, or db-ingestion was enabled.

### Offline Tests Added
- Location: `tests/unit/test_twse_openapi_normalization_v1.py` and `tests/unit/test_tpex_openapi_normalization_v1.py`.
- 100% offline edge-case coverage: includes standard mappings, `None` assignments for `-`/empty close fields, comma stripping, preserving full `raw_row`, and flag application (`missing_close`, `missing_trade_date`, `malformed_close`).

## Validation Executed
```bash
python -m compileall scripts server tests
pytest -m "not network" -v
python scripts/run_all_probes.py
```

All 49 offline tests pass. `run_all_probes.py` completed and regenerated reports. The TPEx live endpoint returned a transient/source failure (`Response ended prematurely`) in this run and was captured accurately in the generated reports; this does not represent an offline parser/test failure, but rather expected upstream fragility from the free official API.

## Files Changed/Added
- **Created**: `docs/protocol/TWSE_OPENAPI_FIELD_DICTIONARY.md`
- **Created**: `docs/protocol/TPEX_OPENAPI_FIELD_DICTIONARY.md`
- **Created**: `docs/contracts/twse_openapi_normalized_eod_quote_v1.md`
- **Created**: `docs/contracts/tpex_openapi_normalized_eod_quote_v1.md`
- **Created**: `scripts/probe_openapi_utils.py`
- **Created**: `tests/unit/test_twse_openapi_normalization_v1.py`
- **Created**: `tests/unit/test_tpex_openapi_normalization_v1.py`
- **Modified**: `scripts/probe_twse_openapi.py`
- **Modified**: `scripts/probe_tpex_openapi.py`
- **Modified**: `tests/unit/test_probes.py`
- **Modified**: `docs/protocol/TWSE_OPENAPI_PROTOCOL.md` (cross-references)
- **Modified**: `docs/protocol/TPEX_OPENAPI_PROTOCOL.md` (cross-references)
- **Modified**: `docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md` (cross-references)
- **Auto-Modified**: `frontend/public/matrix.json`, `docs/capability_matrix.md`, and Context Packs via `run_all_probes.py`.

## Remaining Caveats
- Schema drift is explicitly flagged but cannot be fully mitigated proactively if entirely new API payload structures emerge.
- Rate limiting rules apply organically as public sources.

## Deferred / Next Actions
- Since normalizer implementations were achieved cleanly here, the subsequent M2D-03 normalizer implementation phase can likely be bypassed.
- Next Recommended Milestone: **M2E-01-TARGET-TAXONOMY-AND-ASSET-CLASS-SUPPORT-MATRIX** to standardize market targets across data boundaries.
- Deep db-level full market historical backfill remains entirely deferred out of M2 scale.