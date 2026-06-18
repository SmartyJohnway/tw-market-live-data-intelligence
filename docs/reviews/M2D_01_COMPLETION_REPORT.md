# M2D-01 Completion Report

## 1. M2D-01 Final Status
**Status:** `M2D_01_COMPLETED`

## 2. Upstream Workbench Reconciliation
- **Cloned:** Yes
- **Inspected Path:** `/tmp/tw-market-source-contract-workbench`
- **Upstream Branch/Commit:** `eb86bee6b3f1688a6663852b0748a29a9053fa10` (HEAD of default branch, cloned with depth=1)
- **Files Inspected:** `README.md`, `index.html`.
- **Reconciliation Outcome:**
  - The upstream repo did *not* contain identical probe scripts like `scripts/probe_twse_openapi.py`. Instead, it functions as a Netlify-ready HTML/JS workbench that tracks source governance matrices dynamically inside `index.html`. No `scripts/` or `docs/` protocol files were present in the inspected upstream checkout.
  - The upstream workbench provided critical context on source classifications: classifying `TWSE OpenAPI` and `TPEx OpenAPI` as `authoritative_candidate` for contract scouting, but explicitly warning that it is for EOD/contract preview, not production execution.
  - The current repository implementation (where probes output standardized envelopes) successfully supersedes the upstream HTML-based approach. We carry forward the caveat that these are "official candidate sources" but remain strict EOD feeds.

## 3. Probe Classification Review
- Inspected `scripts/probe_twse_openapi.py` and `scripts/probe_tpex_openapi.py`.
- **Findings:** The current probes correctly return standard envelopes with `source_type="official_openapi"`, `freshness_status="eod_batch"`, `delay_status="eod"`, and properly assign `unsupported_targets` for indices, futures, and funds. Network exceptions and HTTP failures are safely caught and categorized as `failed`.
- **Action Taken:** No code changes were needed because the probe classification is already highly accurate and complies with the data contract directives.
- **Tests Added:** No code changes were required after probe classification review, so no new offline tests were added in M2D-01. Existing offline tests were still run and passed.

## 4. Deliverables Produced
- **`docs/protocol/TWSE_OPENAPI_PROTOCOL.md`:** Documented the exact endpoint URL, response array shape, authentication needs (none), EOD limitation, and minimal observed fields (e.g. `Code`, `ClosingPrice`). Full dictionary deferred to M2D-02.
- **`docs/protocol/TPEX_OPENAPI_PROTOCOL.md`:** Documented the TPEx OTC quote endpoint, JSON array shape, EOD limitations, and observed fields (e.g. `SecuritiesCompanyCode`, `Close`).
- **`docs/protocol/OFFICIAL_OPENAPI_SOURCE_SEMANTICS.md`:** Clarified that "official" means official EOD reference, not live tick data. Delineated exact semantic boundaries between OpenAPI, TWSE MIS, Yahoo Finance, Commercial, and Broker APIs.

## 5. Validation Commands Executed
```bash
python -m pip install -r requirements.txt
python -m compileall scripts server tests
pytest -m "not network" -v
python scripts/run_all_probes.py
```

## 6. Terminal Output Summary
- `pytest` executed 41 unit tests. All offline tests passed successfully.
- `run_all_probes.py` executed cleanly, probing TWSE OpenAPI, TPEx OpenAPI, Yahoo Finance, TWSE MIS, and FinMind. Generated matrix reports were updated successfully.

## 7. Deferred Items (M3/M4)
- **M2D-02:** Full standalone field dictionaries and complete schema normalization contracts.
- **M3/M4:** Production database materialization, real-time historical backfill pipelines, automated execution schemas, or AI market-session aware context generation.

## 8. Remaining Caveats
- TWSE/TPEx OpenAPI are rate-limited public APIs. Running them rapidly or inside tight loops is prohibited.

## 9. Next Milestone Recommendation
Proceed to **`M2D-02-TWSE-TPEX-OPENAPI-FIELD-DICTIONARY-AND-NORMALIZATION-CONTRACT`** to build full field dictionaries and establish strict validation schemas for the EOD official quotes.
