# 市場證據結果 (Market Evidence Result)

**整體狀態**: ✅ 完整成功
**結果 ID**: `umeresult-v2-086aa982ed49f66a0695`
**請求 ID**: `req-v2`
**生成時間**: 2026-09-15T21:31:00+08:00

## 請求摘要
- **執行模式**: execute_once
- **目標數量**: 1
- **請求的資料需求**: material_disclosures, monthly_revenue
- **選擇性需求**: monthly_revenue

## 目標 1
- **解析狀態**: ✅ 已解析
- **規範目標 ID**: `TWSE:2330`
- **證券代碼**: 2330
- **證券名稱**: 台積電
- **市場**: TWSE
- **已提供資料需求**: material_disclosures, monthly_revenue

### 證據

#### material_disclosures
- **狀態**: available
- **覆蓋範圍**:
  - `mode`: latest_completed_official_daily_batch
  - `source_report_date`: 2026-09-15
  - `coverage_through`: 2026-09-14
  - `truncated`: False
- **時效**:
  - `status`: current_within_source_contract
  - `observed_at`: 2026-09-15T21:30:00+08:00
- **來源**:
  - `source_family`: MOPS_MATERIAL_DISCLOSURE_OPEN_DATA
  - `source_contract_id`: t187ap04_L
  - `market`: TWSE
  - `transport`: official_csv
  - `fallback_used`: False

- **發言時間**: 2026-09-14T15:02:01+08:00
  - **事實發生日**: 2026-09-14
  - **主旨**: 重大訊息
  - **說明**: 官方說明
  - **引用**: `cite-abfd342106826487`
- **引用 IDs**: `cite-abfd342106826487`

#### monthly_revenue
- **狀態**: available
- **覆蓋範圍**:
  - `mode`: latest_available_reporting_period
  - `source_report_date`: 2026-09-15
  - `reporting_period`: 2026-08
- **時效**:
  - `status`: current_within_source_contract
  - `observed_at`: 2026-09-15T21:30:00+08:00
- **來源**:
  - `source_family`: MOPS_MONTHLY_REVENUE_OPEN_DATA
  - `source_contract_id`: t187ap05_L
  - `market`: TWSE
  - `transport`: official_csv
  - `fallback_used`: False
- **數值**:
  - `currency`: TWD
  - `unit`: thousand
  - `current_month_revenue`: 1
  - `previous_month_revenue`: 2
  - `previous_year_same_month_revenue`: 3
  - `mom_pct`: None
  - `yoy_pct`: None
  - `ytd_revenue`: 4
  - `previous_year_ytd_revenue`: 5
  - `ytd_yoy_pct`: None
  - `note`: 官方備註
- **引用 IDs**: `cite-cb9d79fdfc183231`

### 引用來源
- `cite-abfd342106826487` — 來源: MOPS_MATERIAL_DISCLOSURE_OPEN_DATA | 擷取時間: 2026-09-20T00:00:00Z | 參考: `evidence/g1.json`
- `cite-cb9d79fdfc183231` — 來源: MOPS_MONTHLY_REVENUE_OPEN_DATA | 擷取時間: 2026-09-20T00:00:00Z | 參考: `evidence/g2.json`

## 審計包參考
- **審計包 ID**: `umeap-v2-33a635aedcec39a4dacf`
- **相對路徑**: `audit/unified_market_evidence_audit_package.v2.json`

> ℹ️ 審計包 (`unified_market_evidence_audit_package.v2`) 包含完整作業系譜、人工製品清單、引用對應表與重播說明。審計包與 AI 對話結果分開保存。

---
> ⚠️ 本結果由確定性投影層 (M8R-05C) 生成，僅呈現來源事實、覆蓋範圍與限制。 所有時效語義由來源 evidence artifact 和執行收據決定。