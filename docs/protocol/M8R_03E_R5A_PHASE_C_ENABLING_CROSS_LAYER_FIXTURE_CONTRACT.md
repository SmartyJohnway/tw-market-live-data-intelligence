# M8R-03E-R5A: Phase C Enabling Cross-Layer Fixture Contract

## 1. Objectives
本合約定義了 M8R-03E-R5A 階段中 10-target 跨層級（Cross-layer）確定性 Fixture 資料集的資料格式、雜湊計算規約、一致性不變量（Invariants）與安全邊界。此 Fixture 的目的在於驗證 Phase C pipeline 在無網絡、無實際授權消耗的情況下，能執行完整的身份解析、計畫編排、觀測值對齊、新鮮度評估與 AI Context Handoff 封裝。

## 2. 10-Target Heterogeneous Composition
為了完整覆蓋生產環境中的各種邊角案例（Edge Cases），Fixture 包含 exactly 10 個 Targets。

### 替換說明（Substitution Details）
由於 Watchlist 執行框架限制了支援的來源家族僅限於 `TWSE_MIS`、`TWSE_OPENAPI` 與 `TPEX_OPENAPI`。本合約遵循「使用 repository 支援的識別符」原則，將原本建議的 TAIFEX 衍生品替換為支援的 TWSE/TPEX 股票與 ETF，並藉由人為引進的觀測值狀態來模擬 heterogenous routes。

### Target 清單與狀態映射
1. **TWSE Listed Equity — Live-ish + EOD 正常雙軌**
   - **ID**: `TWSE:2330` (台積電)
   - **Status**: Live-ish (`TWSE_MIS` fresh) + EOD (`TWSE_OPENAPI` fresh) 正常。
2. **TWSE Listed Equity — Live-ish 失敗但 EOD Fallback 成功**
   - **ID**: `TWSE:2317` (鴻海)
   - **Status**: `TWSE_MIS` 失敗 (source_failure)，但 EOD (`TWSE_OPENAPI` fresh) 成功。
3. **TPEX Listed Equity — EOD 單軌**
   - **ID**: `TPEX:6488` (環球晶)
   - **Status**: 僅有 EOD (`TPEX_OPENAPI` fresh) 數據，live-ish 無觀測值。
4. **TWSE ETF — 正常雙軌**
   - **ID**: `TWSE:0050` (元大台灣50)
   - **Status**: Live-ish (`TWSE_MIS` fresh) + EOD (`TWSE_OPENAPI` fresh) 正常。
5. **TPEX Listed Equity — 正常雙軌**
   - **ID**: `TPEX:5347` (世界)
   - **Status**: Live-ish (`TWSE_MIS` fresh) + EOD (`TPEX_OPENAPI` fresh) 正常。
6. **TWSE ETF — 正常雙軌 (Index-like)**
   - **ID**: `TWSE:0056` (元大高股息)
   - **Status**: Live-ish (`TWSE_MIS` fresh) + EOD (`TWSE_OPENAPI` fresh) 正常。
7. **TWSE Listed Equity — 數據過期（Stale but Usable）**
   - **ID**: `TWSE:2308` (台達電)
   - **Status**: `TWSE_MIS` 成功，但 timestamp 大於 fresh 閾值（assessment 為 `'stale'`，但依舊被 bundle/package 引用）。
8. **TWSE Listed Equity — 缺失非必要資料（Missing Optional Evidence）**
   - **ID**: `TWSE:2382` (廣達)
   - **Status**: Request 中列為 `useful_evidence`，但在 execution result 及 bundle 中顯示為未請求或缺失，不影響 usable 狀態。
9. **TWSE Listed Equity — 單軌 Fallback**
   - **ID**: `TWSE:3008` (大立光)
   - **Status**: `TWSE_MIS` 遭遇 source failure，順利 fallback 到 EOD `TWSE_OPENAPI` 且資料正常。
10. **TWSE Listed Equity — 隔離/未解析（Quarantined/Unresolved）**
    - **ID**: `TWSE:9999` (未上市或異常代碼)
    - **Status**: 於 Security Master 中不存在或標記為 blocked。在規劃時即被判定為 `identity_unresolved`，無後續觀測值，在 AI context package 內被正確標記為 missing evidence。

## 3. Determinism Contract
Fixture 產生器在相同的 `seed` 與 `clock` 輸入下，必須產出 byte-identical 的結果。
* **Fixed Reference Clock**: `2026-07-16T03:00:00Z`
* **Stable Sort Ordering**:
  - Targets 排序均以 Request 的 `persistent_watchlist_reference.enabled_target_ids` 的輸入順序為準。
  - 產生的 JSON 鍵值（Keys）必須以 ASCII 字典序排序 (`sort_keys=True`)，無 random UUID（除非使用 seed 衍生出的確定性雜湊）。
  - 所有浮點數與數字必須以穩定的科學記號或小數表示。

## 4. Cross-Layer Invariants
* **ID 一致性**：所有層級的 `request_id` 必須一致為 `m8r03c-snapshot`。
* **雜湊鏈驗證**：
  - `execution_plan` 與 `execution_result` 內部的 `request_hash` 必須等於 `canonical_request_hash(request)`。
  - `package` 內部所有 citation 的 `value_hash` 必須與其在 `bundle` 中的對應值雜湊一致。
  - `manifest` 內部的雜湊值必須等於對應 package 與 handoff 的真實 JSON 雜湊。
* **Orphan References**：不存在 dangling citations。所有 citations 的 JSON pointer path 均能解析到 package 中的實質 Fact 值，且所有 cited citation_id 都在 package 的 `citation_index` 註冊表中。

## 5. Security & Safety Boundaries
* **網際網路調用次數為零** (`network_call_count = 0`)：不發起任何 HTTP/WebSocket 請求。
* **授權額度消耗次數為零** (`authorization_consumption_count = 0`)：在驗證過程中，不得向 `AUTHORIZATION_CONSUMPTION_ROOT` 寫入非確定性的 receipt。
* **禁止洩露敏感欄位**：AI context projection 與 handoff 中嚴禁包含 `raw_payload`、`cookies`、`headers`、`access_token` 等在 `FORBIDDEN_FIELDS` 中的欄位。

## 6. Verification and Acceptance
此合約由 Commit 3 的單元測試與整合測試，以及 Commit 4 的效能與 Fail-closed 檢驗來予以強制執行。
