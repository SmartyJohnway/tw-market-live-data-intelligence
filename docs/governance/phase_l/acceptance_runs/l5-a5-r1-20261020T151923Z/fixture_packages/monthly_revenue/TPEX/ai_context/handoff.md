# 市場證據結果 (Market Evidence Result)

**整體狀態**: ✅ 完整成功
**結果 ID**: `umeresult-v3-10a4b2c178693f08d460`
**請求 ID**: `a5-monthly_revenue-TPEX-available`
**生成時間**: 2026-09-22T00:00:00Z

## 請求摘要
- **執行模式**: preview
- **目標數量**: 1
- **請求的資料需求**: monthly_revenue

## 目標 1
- **解析狀態**: ✅ 已解析
- **規範目標 ID**: `TPEX:6488`
- **證券代碼**: 6488
- **證券名稱**: 台積電
- **市場**: TPEX
- **已提供資料需求**: monthly_revenue

### 證據

#### monthly_revenue
- **狀態**: available
- **覆蓋範圍**:
  - `mode`: latest_available_reporting_period
  - `source_report_date`: 2026-09-15
  - `reporting_period`: 2026-08
- **時效**:
  - `status`: current_within_source_contract
  - `observed_at`: 2026-09-16T00:00:00Z
- **來源**:
  - `source_family`: MOPS_MONTHLY_REVENUE_OPEN_DATA
  - `source_contract_id`: t187ap05_O
  - `market`: TPEX
  - `transport`: official_csv
  - `fallback_used`: False
- **數值**:
  - `currency`: TWD
  - `unit`: thousand
  - `current_month_revenue`: 100
  - `previous_month_revenue`: -2
  - `previous_year_same_month_revenue`: 90
  - `mom_pct`: None
  - `yoy_pct`: 11.1
  - `ytd_revenue`: 800
  - `previous_year_ytd_revenue`: 700
  - `ytd_yoy_pct`: None
  - `note`: 官方備註
- **引用 IDs**: `cite-75ca58d5c90801e2`

### 引用來源
- `cite-75ca58d5c90801e2` — 來源: MOPS_MONTHLY_REVENUE_OPEN_DATA | 擷取時間: 2026-09-22T00:00:00Z | 參考: `evidence/monthly_revenue/TPEX_6488.json`

## 審計包參考
- **審計包 ID**: `umeap-v3-6d72c5854e361aaaf1fb`
- **相對路徑**: `audit/unified_market_evidence_audit_package.v3.json`

> ℹ️ 審計包 (`unified_market_evidence_audit_package.v3`) 包含完整作業系譜、人工製品清單、引用對應表與重播說明。審計包與 AI 對話結果分開保存。

---
> ℹ️ 本結果由確定性投影層 (M8R-05C) 生成，僅呈現已驗證事實、覆蓋範圍、時間基礎與解讀護欄。