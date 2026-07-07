# TWSE MIS Rich Field Probe Evidence Review

## 1. Probe Attempts Summary

This document reviews the manual bounded TWSE MIS rich-field probes executed using `scripts/probe_twse_mis_rich_fields.py` to collect compact field evidence.

### 1.1. Initial Attempt (M7A-01B)
- **Status**: Failed
- **Failure Stage**: Session bootstrap
- **Failure Reason**: `HTTP Error 404: Not Found` when requesting the default bootstrap URL (`/stock/index.jsp`). No raw rows or field-level evidence were obtained.
- **Committed Artifact**: `research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_attempt_20260707T030255Z.json`.

### 1.2. Successful Operator Run (M7A-01D)
- **Status**: Success
- **Strategy Used**: `bootstrap_then_api`
- **Result**: Successfully obtained 6 rows and 0 failures.
- **Committed Artifact**: `research/probe_runs/m7a_twse_mis_rich_fields/m7a_twse_mis_rich_field_probe_summary_20260707T034516Z.json`.

---

## 2. Bounded Symbols Bounded Set

The manual harness requested and processed exactly the approved six-symbol set:
1. `tse_t00.tw` (Observed)
2. `tse_2330.tw` (Observed)
3. `tse_0050.tw` (Observed)
4. `otc_8069.tw` (Observed)
5. `otc_5347.tw` (Observed)
6. `tse_1435.tw` (Observed)

- **Symbols Requested**: 6
- **Symbols Observed**: 6
- **Symbols Failed**: 0

---

## 3. Successful Telemetry and Strategy Facts

- **Successful Strategy**: `bootstrap_then_api`
- **Session Bootstrap Attempts**:
  - `https://mis.twse.com.tw/stock/fibest.jsp` -> `HTTPError` 404 (failed)
  - `https://mis.twse.com.tw/stock/index.jsp` -> `HTTPError` 404 (failed)
  - `https://mis.twse.com.tw/stock/` -> 200 Success (session acquired)
- **API Request**:
  - `https://mis.twse.com.tw/stock/api/getStockInfo.jsp` -> 200 Success

---

## 4. Field Evidence Analysis

- **Field Presence Count**: 45
- **Observed Fields Count (present_count > 0)**: 41
- **Not Observed Fields (present_count == 0)**: `q`, `oa`, `ob`, `ot`
- **Newly Observed Fields (Not in Prior Inventory)**: `m`, `nu`

### 4.1. Semantic Interpretation and Constraints (Conservative)
- **v / tv (Volume Candidates)**: Remain unit-unverified. Do not assume or map to shares or lots.
- **g / f (Quantity Ladder Candidates)**: Remain displayed bid/ask quantity ladder candidates with unit unverified. Do not claim true liquidity.
- **b / a (Price Ladder Candidates)**: Remain displayed bid/ask price ladder candidates only.
- **No Support/Resistance**: Do not interpret any price point or depth levels as support, resistance, or buy/sell zones.
- **No True Liquidity**: Order book shape is displayed snapshot depth only; does not guarantee true market liquidity.
- **No Trading Signal**: No field, shape, or gap may be interpreted as buy, sell, hold, main force (主力) intention, or institutional intention.

---

## 5. Security & Governance Verification

- **Raw Payload Committed**: False
- **Headers Committed**: False
- **Cookies Committed**: False
- **Session Tokens Committed**: False
- **Raw Response Body Committed**: False

---

## 6. Recommended Next Action

The successful compact evidence has been committed and reviewed. The next step is **M7A-02** to extend the observation contract schema, followed by updating the runtime parser in **M7A-03**.
