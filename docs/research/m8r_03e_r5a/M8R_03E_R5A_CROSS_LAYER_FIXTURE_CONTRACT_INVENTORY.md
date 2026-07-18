# M8R_03E_R5A Cross-Layer Fixture Contract Inventory

本文件記錄了由 `m8r_03e_r5a_cross_layer_fixture.py` 確定性生成並材料化輸出至 `tests/fixtures/m8r_03e_r5a/` 下的 15 個測試數據（Fixture）合約。

## 1. Top-Level Fixture Manifest
* **檔名**: `fixture_manifest.json`
* **合約**: `m8r_03e_r5a_cross_layer_fixture_manifest.v1`
* **說明**: Fixture 的總控文件。定義不可歧義的 manifest hash contract，排除最外層的 `manifest_hash` 後計算的 sha256 雜湊與欄位完全吻合，且第一個 artifacts 條目的 `sha256` 設為空字串以避免自引用循環。
* **關聯 Targets**: 10 targets

## 2. Security Master Snapshot & Manifest
* **檔名**: `security_identity_snapshot.json` / `security_identity_snapshot_manifest.json`
* **合約**: `twse_security_master_snapshot.v1` / `twse_security_master_manifest.v1`
* **說明**: 提供 10 個異質 target 的身份及屬性定義，已被驗證能透過 production adapter 與 loader 載入並正式取得 validated SM 證書。
* **關聯 Targets**: 10 targets

## 3. Source Capability Registry Snapshot
* **檔名**: `source_capability_snapshot.json`
* **合約**: `m8_source_capability_registry.v1`
* **說明**: 複製自治理的 capability 註冊表。已由 production planner 與 execution resolver 實際消費以過濾非執行期 family 與禁用 route。
* **關聯 Targets**: None

## 4. Input Bounded Request
* **檔名**: `bounded_request.json`
* **合約**: `m8r_ai_evidence_request.v1`
* **說明**: 模擬 AI 助手發起的觀察清單上下文請求，限制 `MAX_TARGETS = 10`。
* **關聯 Targets**: 10 targets

## 5. Execution Plan
* **檔名**: `execution_plan.json`
* **合約**: `m8r_03d_watchlist_execution_plan.v1`
* **說明**: 根據 request 與 capability 規劃出的雙軌/單軌獲取計畫，支援非聯網執行。
* **關聯 Targets**: 10 targets

## 6. Raw Observations
* **檔名**: `source_observations.json`
* **合約**: `m8r_watchlist_source_data.v1`
* **說明**: 10 個 target 的 raw 觀測資料，包含 stale status、時間差等。
* **關聯 Targets**: 10 targets

## 7. Downstream Output Artifacts
* **檔名**: `evidence_bundle.json`
  - **合約**: `m8r_watchlist_snapshot_bundle.v1`
  - **說明**: 包含已收集的 Facts 數據與 missing_evidence。
* **檔名**: `provenance_manifest.json`
  - **合約**: `m8r_watchlist_provenance.v1`
  - **說明**: 事實的起源與傳播鏈。
* **檔名**: `citation_map.json`
  - **合約**: `m8r_watchlist_citation_index.v1`
  - **說明**: 雜湊與事實對齊的引用索引用於防篡改。
* **檔名**: `missing_evidence_register.json`
  - **合約**: `m8r_watchlist_missing_evidence.v1`
  - **說明**: 記錄未滿足或失敗的資料獲取。
* **檔名**: `context_projection.json`
  - **合約**: `m8r_watchlist_ai_context_package.v2`
  - **說明**: 最終投射至 AI 助手的上下文 package。
* **檔名**: `currentness_assessment.json`
  - **合約**: `m8r_watchlist_currentness_assessment.v1`
  - **說明**: 由 timestamp 自行推導出新鮮度的評估結果。
* **檔名**: `expected_validation_result.json`
  - **合約**: 預期校正結果定義。
  - **說明**: 用於檢校 package 校正有效性。
* **檔名**: `expected_partial_failure_result.json`
  - **合約**: 模擬失敗狀態結果定義。
  - **說明**: 用於 Variant A/B/C 的狀態預期驗證。
