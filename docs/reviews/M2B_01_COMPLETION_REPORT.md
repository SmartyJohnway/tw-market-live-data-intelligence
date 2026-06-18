# M2B-01 Completion Report

## 1. Final Status
`M2B_01_COMPLETED`

## 2. Files Changed
1. `docs/protocol/TWSE_MIS_PROTOCOL.md` (Added)
2. `docs/protocol/TWSE_MIS_FIELD_DICTIONARY.md` (Added)
3. `docs/contracts/twse_mis_normalized_snapshot_v2_draft.md` (Added)
4. `README.md` (Updated cross-references)
5. `docs/source_catalog.md` (Updated cross-references)
6. `docs/reviews/M2A_COMPLETION_REPORT.md` (Updated with addendum)
7. `tests/unit/test_twse_mis_docs.py` (Added)

## 3. Validation Commands Executed
1. `python -m pip install -r requirements.txt`
2. `python -m compileall scripts server tests`
3. `pytest -m "not network" -v`

## 4. Terminal Output Summary
All offline tests passed, including the 4 newly added unit tests validating the protocol and field dictionary documentation (`tests/unit/test_twse_mis_docs.py`). The existing probes tests also pass correctly without network issues.

## 5. Protocol Documentation Summary
Documented the TWSE MIS source behavior across 11 key sections. The protocol highlights its unofficial, frontend-endpoint nature, the necessity of `index.jsp` for session cookies, parameter configurations, and asset channel formats. Crucially, it emphasizes that this is only suitable for bounded low-frequency watchlist AI usage, explicitly prohibiting high-frequency or algorithmic trading use due to extreme fragility and risk.

## 6. Field Dictionary Summary
Built a comprehensive table translating the obscure raw field names (e.g., `z`, `v`, `a`, `f`) into their observed meanings and normalized candidates. Applied confidence levels carefully (confirmed, observed, candidate, unknown) and detailed key caveats, notably that index rows lack bid/ask ladders.

## 7. Timestamp Semantics Summary
Documented that `tlong` represents the source time, while `retrieved_at` values represent the system processing time. Clarified that any classification of "realtime" relies entirely on derived staleness calculations, as the source itself does not guarantee real-time delivery and may be heavily delayed or cached.

## 8. Intraday vs Post-Market Behavior Summary
Explicitly documented observed differences:
- Intraday fields like `z`, `tv`, and `s` may return `"-"` prior to trades matching.
- Post-market responses generally populate these `"-"` fields and often surface additional fields like `oa`, `ob`, `oz`, indicating after-hours metrics.

## 9. Deferred Implementation Items for M2B-02
- Implementing the normalized output logic based on `twse_mis_normalized_snapshot_v2_draft.md` inside `scripts/probe_twse_mis.py`.
- Adding specific unit tests for parsing `-` string values into `None`.
- Adding specific unit tests for successfully parsing underscore-separated bid/ask arrays.
- Implementing safe parsing logic to handle index rows (e.g., `t00.tw`) that omit bid/ask ladders entirely.

## 10. Remaining Caveats and Next Milestone Recommendation
**Remaining Caveats:** The current implementation of TWSE MIS is still using the v1 payload. It remains highly susceptible to blockades, rate-limiting, and schema alterations without notice.

**Next Milestone Recommendation:**
Proceed to `M2B-02-TWSE-MIS-NORMALIZED-SNAPSHOT-V2-AND-TESTS` to fully integrate the new normalized JSON schema drafted in this milestone.
