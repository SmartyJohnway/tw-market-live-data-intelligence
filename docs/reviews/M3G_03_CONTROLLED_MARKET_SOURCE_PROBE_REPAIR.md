# M3G-03 Controlled Market Source Probe Repair Review

## 1. Final Status
**M3G_03_COMPLETED_WITH_CAVEATS_READY_FOR_M3G_04**

## 2. Baseline merge SHA
`049d05355018fd1392a5b36b8a14262918c40710` (from PR #34)

## 3. Files inspected
* `scripts/generate_latest_market_snapshot.py`
* `scripts/probe_twse_mis.py`
* `scripts/probe_twse_openapi.py`
* `scripts/probe_tpex_openapi.py`
* `scripts/probe_yahoo.py`
* `config/market_targets.json`
* `docs/contracts/latest_market_snapshot_contract.md`

## 4. Files changed
* `pytest.ini` (added offline and network markers)
* `tests/helpers/mock_fixtures.py` (new helper)
* `tests/test_market_snapshot_generator.py` (new tests)
* `tests/fixtures/market_sources/*` (new fixture data files)
* `docs/reviews/M3G_03_CONTROLLED_MARKET_SOURCE_PROBE_REPAIR.md` (this report)
* `README.md` (small link added to this review)

## 5. Fixture families created
Mock fixtures were created in `tests/fixtures/market_sources/` for the following families:
* `twse_mis` (`success.json`, `empty.json`)
* `twse_openapi` (`success.json`, `empty.json`)
* `tpex_openapi` (`success.json`, `empty.json`)
* `yahoo_finance` (`success.json`, `empty.json`)

## 6. Symbols covered by fixtures
The fixtures cover the following symbols based on `config/market_targets.json`:
* `2330` (TWSE_MIS, TWSE_OpenAPI, Yahoo_Finance)
* `0050` (TWSE_MIS, TWSE_OpenAPI)
* `00929` (TWSE_OpenAPI)
* `8069` (TPEx_OpenAPI)
* `TAIEX` / `t00` (TWSE_MIS)

## 7. Parser/normalization changes
No changes to production parser logic were required. The pure normalization functions (`normalize_twse_mis_row`, `normalize_twse_openapi_row`, `normalize_tpex_openapi_row`, `normalize_yahoo_chart_result`) were already extracted and available for offline consumption.

## 8. Generator integration changes
No changes were made to the production CLI or generation logic. The existing `mock_inputs` parameter on `build_snapshot` in `scripts/generate_latest_market_snapshot.py` was used directly from within the test framework (`tests/helpers/mock_fixtures.py`).

## 9. Test coverage summary
Tests were added in `tests/test_market_snapshot_generator.py` asserting:
* Fixture files can be loaded and normalized purely offline.
* Output strictly maps `TWSE_MIS` to `live_candidate`/`unofficial_frontend`, `OpenAPI` to `eod_reference`, and `Yahoo` to `third_party`.
* Mock inputs successfully produce at least one populated symbol entry in the snapshot output.
* Missing/failed target handling remains intact.
* `watchlist_scope.full_market_scan` strictly remains `False`.
* Output correctly prohibits investment recommendations.
* Output maintains identical schema compatibility with the frontend format.

## 10. Confirmation no live probes were run
Confirmed. All validations occurred via `pytest -m "not network"` relying entirely on deterministic local fixture data.

## 11. Confirmation no external endpoints were called
Confirmed.

## 12. Confirmation no generated production artifacts were modified
Confirmed. The `research/generated/*` directory remained untouched.

## 13. Confirmation no frontend runtime external requests were introduced
Confirmed. No frontend modifications occurred.

## 14. Confirmation no investment/trading semantics were added
Confirmed. Prohibited interpretation guarantees were asserted explicitly in test.

## 15. Mock-generated non-empty output summary
The test offline snapshot successfully produced entries such as `2330` using `TWSE_MIS` as the primary live candidate (`last_price`: `1015.0`) and `8069` using `TPEx_OpenAPI` as an EOD reference (`close`: `250.0`), all correctly stamped with freshness status and caveats.

## 16. Remaining source recovery caveats
Broker sources (FinMind, Fugle, Fubon) remain deferred and untested offline. `TWSE_MIS` requires parsing out the cookie authentication flow if moved into true live integration. Timezone normalizations for non-standard EOD endpoints remain slightly sensitive to local time states.

## 17. Readiness for LEVEL_2
The parser, normalization, and generator logic are stable when fed deterministic inputs. The pipeline guarantees boundaries natively. It is ready for LEVEL_2 live probes.

## 18. Validation commands and results
```bash
python -m compileall scripts server tests
pytest -m "not network" -v
```
All offline validations passed successfully.

## 19. Recommended next milestone
**M3G-04-CONTROLLED-LIVE-PROBE-AUTHORIZATION-PREFLIGHT**