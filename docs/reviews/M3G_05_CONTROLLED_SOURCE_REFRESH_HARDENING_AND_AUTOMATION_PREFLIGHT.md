# M3G-05 Controlled Source Refresh Hardening and Automation Preflight Review

## 1. Final Status
`pass`

## 2. Exact Files Changed
- `scripts/run_m3g04_controlled_live_probe.py`
- `scripts/probe_yahoo.py`
- `tests/test_m3g04_controlled_live_probe.py`
- `tests/unit/test_yahoo_probe_classification.py`

## 3. Tests Run and Results
The following test suites were successfully run completely offline (`pytest -m "not network" -v`):
- `tests/test_m3g04_controlled_live_probe.py`: All 10 tests passed.
- `tests/unit/test_yahoo_probe_classification.py`: All 10 tests passed.

## 4. Mapping Contract Table
The explicit target bounded mapping was successfully extracted into the testable `map_targets_for_source` helper.

| Target Source | Requested | Mapped To |
| --- | --- | --- |
| Yahoo_Finance | 2330 | 2330.TW |
| Yahoo_Finance | 0050 | 0050.TW |
| Yahoo_Finance | 00929 | 00929.TW |
| Yahoo_Finance | 8069 | 8069.TWO |
| Yahoo_Finance | TAIEX | ^TWII |
| TWSE_MIS | 2330 | tse_2330.tw |
| TWSE_MIS | 0050 | tse_0050.tw |
| TWSE_MIS | 00929 | tse_00929.tw |
| TWSE_MIS | 8069 | otc_8069.tw |
| TWSE_MIS | TAIEX | tse_t00.tw |
| TWSE_OpenAPI | 2330 | 2330 (Raw) |
| TPEx_OpenAPI | 8069 | 8069 (Raw) |

## 5. Yahoo Identity Mismatch Test Result
The Yahoo mismatch detection logic was successfully fortified and rigorously unit-tested:
- Test: Suffix drop detection (e.g. `0050.TW` matched to `0050`).
- Test: Japan OTC exchange detection (e.g. `JSD` exchange).
- Test: Specific known mismatch names (e.g. "For-side.com").
All scenarios now accurately generate a strict `identity_mismatch` contract_status, blocking execution-grade outputs.

## 6. Summary Semantics Contract Result
The output of bounded probes per source was standardized into the testable `build_summary_entry` pure helper, preserving explicitly failure states (`contract_status`, `http_ok`, `parse_status`, `normalization_status`, `failed_targets`, `errors`) and blocking generic "completed" reporting when sources internally fail.

## 7. Explicit Confirmations
I explicitly confirm that the following were **not modified** during this task:
- `research/generated/*`
- `frontend/public/*`
- `config/market_targets.json`
- `broker/auth/*`

## 8. Remaining Caveats
None. The engineering constraints placed on M3G-04 regarding the purity, testing, and fragility of mapping have been resolved.