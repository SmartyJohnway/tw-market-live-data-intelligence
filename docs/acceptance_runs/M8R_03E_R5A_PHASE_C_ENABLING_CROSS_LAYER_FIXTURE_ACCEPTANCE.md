# M8R_03E_R5A Phase C Enabling Cross-Layer Fixture Acceptance Report

## 1. Executive Summary
本報告記錄了 **M8R-03E-R5A-PHASE-C-ENABLING-CROSS-LAYER-FIXTURE-INFRASTRUCTURE** 任務的驗證結果。在完全關閉網絡、無實際授權憑證消耗的情況下，本階段成功建立並驗證了具備 10 個異質 Target 的跨層級確定性測試用例。所有 32 個單元與整合測試均順利通過，達成了無網路執行、E2E 一致性、防篡改 fail-closed 與高性能要求。

> [!IMPORTANT]
> 此任務僅建立並驗證跨層級測試基礎設施，**並不啟用 Phase C**。Phase C 的激活仍有待後續的審查決定。

## 2. Environment & Governance Details
* **Operating System**: Windows
* **Python Version**: 3.13.7
* **Pytest Version**: 9.1.1
* **Baseline Main Commit SHA**: `54b078932d0abfb8b20bed99356860a2aca050eb`
* **Tested Parent SHA**: `f311daa6885dae04b3a47e5a94b98e854372bbbb` (Commit 10)
* **Tested Fixture Manifest SHA-256**: `88140fc7ae7d2ed39a7fb94aca36791373077ad2bf197ff66591fa5d42239388` (當前 generated manifest_hash)
* **Tested Commit SHA**: `null` (因屬 precommit 驗證)
* **Fixture ID**: `fixture-r5a-seed-r5a`
* **Fixture Version**: `1`
* **Generated Artifacts Count**: 13 (manifest 註冊件) + 2 (預期校驗結果件) = 15 檔案

## 3. Governance Gate Disposition
* **R5A Fixture Blocker**: `resolved_with_caveats`
* **R5B Filesystem Blocker**: `resolved_with_caveats`
* **Phase C Gate Disposition**: `ready_for_explicit_activation_review_with_caveats`
* **Phase C Activation Review Eligibility**: `ready_for_explicit_owner_review`
* **Phase C Activation**: `blocked_pending_explicit_owner_decision`

## 4. Explicit Caveats
本項驗收結果包含以下明確的 Caveats：
1. **EOD Provisional Policy**: 當前的 EOD 新鮮度策略屬暫時性的 `provisional bounded EOD age policy`，並未整合交易所交易日曆與休市日。
2. **Regression Environment**: Windows 本地測試環境與 Linux CI 環境僅屬 `partially_comparable`，全套回歸測試中仍有 28 個非退化既有失敗。

## 5. Test Matrix & Results

| Test Target / Name | Type | Status | Description |
| :--- | :--- | :--- | :--- |
| `test_fixture_byte_identical_determinism` | Unit | **PASSED** | 相同 seed/clock 生成 byte-identical 內容。 |
| `test_fixture_different_seed_controlled_differences` | Unit | **PASSED** | 不同 seed 產生價格與名稱微調後的控制內差異。 |
| `test_fixture_different_clock_controlled_differences` | Unit | **PASSED** | 不同 clock 僅變更時間衍生欄位與下游雜湊。 |
| `test_fixture_different_output_roots_determinism` | Unit | **PASSED** | 相同 seed/clock 生成到不同輸出目錄，原始 bytes 100% 相同以證明 path-independence。 |
| `test_cross_layer_id_and_order_consistency` | Unit | **PASSED** | 10-target 的 ID 與順序在 plan, bundle, package 跨層級一致。 |
| `test_upstream_validation_passes` | Unit | **PASSED** | 驗證 10-target 的 upstream schemas 通過合約驗證。 |
| `test_package_hash_and_citation_provenance` | Unit | **PASSED** | Fact 與 citation 可向上追溯無 orphan references，且時點拆分避免了 provenance 污染。 |
| `test_manifest_hash_and_artifact_integrity` | Unit | **PASSED** | 驗證 13 個 artifacts 的 sha256 雜湊與自引用 manifest_hash 合約。 |
| `test_projection_has_no_sensitive_data` | Unit | **PASSED** | AI projection 中無 raw cookies/credentials 洩露。 |
| `test_target_states_match_expectations` | Unit | **PASSED** | stale 觀測值、missing optional, unresolved 隔離等狀態正確。 |
| `test_filesystem_safety_valid_path` | Unit | **PASSED** | 驗證正常路徑材料化寫入成功。 |
| `test_filesystem_safety_blocked_parent_traversal` | Unit | **PASSED** | 驗證 traversal (..) 寫入被 R5B 安全阻擋並 fail-closed。 |
| `test_filesystem_safety_blocked_forbidden_directories` | Unit | **PASSED** | 驗證受限目錄的寫入被安全攔截。 |
| `test_variant_a_source_adapter_failure` | Unit | **PASSED** | 模擬單一 source family 故障，驗證 E2E 降級為 partial 且無交叉污染。 |
| `test_variant_b_stale_and_missing_pipeline` | Unit | **PASSED** | 驗證混合過期與缺失資料在 pipeline 執行時的實質隔離與 citation 行為。 |
| `test_variant_c_tampering_fail_closed` | Unit | **PASSED** | 篡改 Fact 內容、或修改 record 內容與雜湊不一致， loader/validator 拋出異常阻斷。 |
| `test_pipeline_performance` | Unit | **PASSED** | 評估無網絡模式下，中位數處理耗時低於 1000ms（實際 ~251.69ms）。 |
| `test_integration_phase_c_fixture_pipeline` | Integration | **PASSED** | 10-target request 在無網絡下完整跑通 E2E 編排與 builder 流程。 |
| `test_capability_snapshot_consumption_and_unsupported_filtering` | Integration | **PASSED** | 測試 planner/resolver 實際消費 registry 開關，正確拒絕 unsupported 路由。 |
| `test_capability_registry_fail_closed_behaviors` | Integration | **PASSED** | 驗證 malformed/empty/missing 宣告時，規劃器與路由解析均能阻斷路由並 fail-closed。 |
| `test_parse_iso_datetime_tz_aware` | Unit | **PASSED** | 驗證帶有時區標記的 ISO 時間戳記之正確解析（包含 UTC Z 與台北偏移）。 |
| `test_currentness_fresh_liveish` | Unit | **PASSED** | 驗證 live-ish 在 900 秒新鮮期內的正常判定與延遲計算。 |
| `test_currentness_stale_liveish` | Unit | **PASSED** | 驗證 live-ish 超過 900 秒時的過期狀態。 |
| `test_currentness_future_timestamp` | Unit | **PASSED** | 驗證未來時間戳判定為 unresolved。 |
| `test_currentness_missing_inputs` | Unit | **PASSED** | 驗證缺乏 reference clock 或關鍵觀測時間時安全返回 unresolved。 |
| `test_currentness_retrieved_at_fallback` | Unit | **PASSED** | 驗證缺失 source_timestamp 時，自動 fallback 為以 retrieved_at 評估。 |
| `test_currentness_timezone_offset_equivalence` | Unit | **PASSED** | 驗證不同時區表達（Z 與 +08:00）在 age 計算時的等價。 |
| `test_currentness_invalid_tz_fallback` | Unit | **PASSED** | 驗證無效時間戳格式會安全返回 unresolved。 |
| `test_currentness_official_eod` | Unit | **PASSED** | 驗證 EOD 新鮮度在 3 天限制內標為 completed_eod，超出則標為 stale。 |
| `test_currentness_official_eod_missing_date` | Unit | **PASSED** | 驗證 EOD 資料若無 trade_date 則返回 unresolved 阻斷。 |
| `test_currentness_unknown_timing_class_fails_closed` | Unit | **PASSED** | 驗證未知 timing_class 會被 fail-closed 阻斷返回 unresolved 狀態。 |
| `test_normalizer_preserves_actual_retrieval_time` | Unit | **PASSED** | 驗證 normalizer 輸出的 observation 忠實保留資料來源之原始取得時間，並隔離計算 age 和 transport latency。 |

## 6. Full Non-Network Regression Comparison
我們在 Commit 10 修改完成後，實地重跑了非聯網回歸測試全套執行，並與 R5B 階段的 36 個錯誤結果進行了比較：
* **Collected (including deselected)**: 1783 (R5B: 1751)
* **Selected (including skipped)**: 1782 (R5B: 1750)
* **Passed + Failed**: 1777 (R5B: 1745)
* **Passed**: 1749 (R5B: 1709)
* **Failed**: 28 (R5B: 36)
* **Skipped**: 5 (R5B: 5)
* **Deselected**: 1 (R5B: 1)
* **Warnings**: 1 (R5B: 1)
* **Return Code**: 1
* **Environment Equivalence Status**: `partially_comparable`
* **Regression Determination Status**: `no_novel_failing_node_ids_observed`
* **Novel Failing Node IDs vs R5B**: `[]` (無任何新增或退化失敗)
* **Removed Failing Node IDs vs R5B**: 本次測試有 8 個先前失敗的 node IDs 未再失敗（其先前在 R5B 由於缺少 security master fixture 支援而失敗，現因 R5A 基礎設施之建立已可正常載入）：
  1. `tests/unit/test_m8r_03d_f1_verified_security_master_snapshot.py::test_loader_rejects_drift_and_raw_fields`
  2. `tests/unit/test_m8r_03d_f1_verified_security_master_snapshot.py::test_classification_lifecycle_and_observation_policy`
  3. `tests/unit/test_m8r_03d_f1_verified_security_master_snapshot.py::test_resolution_exact_and_ambiguous`
  4. `tests/unit/test_m8r_03d_f1_verified_security_master_snapshot.py::test_m8r03d_planner_consumes_verified_snapshot_and_fails_closed`
  5. `tests/unit/test_m8r_03d_f1_verified_security_master_snapshot.py::test_trust_gap_tampered_direct_snapshot_and_lookup_rejected`
  6. `tests/unit/test_m8r_03d_f1_verified_security_master_snapshot.py::test_fabricated_validated_wrapper_revalidated_and_rejected`
  7. `tests/unit/test_m8r_03d_f1_verified_security_master_snapshot.py::test_duplicate_isin_policy_explicit_quarantine_only`
  8. `tests/unit/test_m8r_03d_f1_verified_security_master_snapshot.py::test_lifecycle_total_count_and_dict_conflict_duplicate_isin`
* **Failure Set Relation**: `subset` (無 regression，且失敗集合為 R5B 之子集，證明系統穩定性顯著提升)。

## 7. Performance Benchmarks
效能測試包含 3 次 warm-up 溫跑與 20 次正式 iterations：
* **E2E Pipeline (20 runs)**: Median: **251.69 ms**, P95: **385.12 ms**, Max: **413.08 ms**
* **Fixture Generation (20 runs)**: Median: **110.25 ms**, P95: **142.15 ms**, Max: **180.12 ms**
* **Schema Validation (20 runs)**: Median: **5.45 ms**, P95: **8.12 ms**, Max: **12.50 ms**
* **Verdict**: **PASSED**

## 8. Governance Check Results
1. **R5B Insecure Path Guard**: **PASS**
2. **Forbidden Behavior Scanner**: **PASS**

## 9. Binding Agreement
* **Binding Status**: `unsealed_precommit_evidence`
* **Task Intent Verified**: Yes
