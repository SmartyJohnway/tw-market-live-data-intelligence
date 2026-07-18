# Phase C Activation Decision Inventory

本文件記錄了目前 Phase C 在 `ag/m8r-03e-phase-c-activation-decision` 分支中的技術實作、執行進入點、控制參數與本任務的具體修改點。

## 1. 系統執行與規劃進入點

* **Network Execution 入口**：
  * 主要由 `scripts/m8r_03d_watchlist_controlled_executor.py` 中的 [execute_watchlist](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_03d_watchlist_controlled_executor.py#L34-L81) 函數負責。
  * `execute_watchlist` 內部調用 [build_execution_plan](file:///p:/tw-market-live-data-intelligence-main/scripts/m8r_03d_watchlist_execution_plan.py#L151-L235) 進行執行規劃。
* **Handoff 與 AI Context 產出**：
  * 使用 `scripts/m8r_03e_watchlist_ai_context_builder.py` 與 `scripts/m8r_03e_conversation_handoff_builder.py` 產出 normalized observations、context projection 與 citation map。

## 2. 當前 Approval 實現
* **舊版安全合約**：先前由 `scripts/m8r_03d_watchlist_execution_plan.py` 中的 `validate_authorization` 提供技術認證，需傳入包含 `authorized_request_hash`、`one_shot_nonce`、以及 `operator_approval` 的 authorization 字典。
* **新版對話式核准機制**：
  * 本任務將引入 `conversation_explicit_approval` 模式。
  * 使用者可以使用自然語言回答，由上層 Agent 將其正規化為標準的 `m8r_phase_c_conversation_approval.v1` 結構：
    ```json
    {
      "schema_version": "m8r_phase_c_conversation_approval.v1",
      "approval_mode": "conversation_explicit_approval",
      "preview_id": "preview-...",
      "request_id": "request-...",
      "approval_status": "approved",
      "approved_utc": "...",
      "approved_text_summary": "使用者同意"
    }
    ```

## 3. Current Source Registry 與 Planner 選擇邏輯
* **Registry 檔案**：[m8_source_capability_registry.json](file:///p:/tw-market-live-data-intelligence-main/docs/data_capabilities/m8_source_capability_registry.json)。
* **Planner 選擇邏輯**：
  * 只有符合以下條件之來源方能納入規劃：
    1. 存在於 registry 且 `runtime_available == true` 且 `runtime_executable == true`。
    2. 其 `phase_c_activation_state` 在當前 profile 下為 `enabled_one_shot`。
    3. 來源並非 `quarantined` 或 `deprecated`。

## 4. Current Bounds 限制
* **正常範圍**：Targets $\le 10$, Operations $\le 30$。
* **擴展範圍**：Targets $\le 50$, Operations $\le 100$。在此範圍時，Preview 的 `expanded_scope` 將設為 `true`。
* **超限拒絕**：任何 Targets $> 50$ 或 Operations $> 100$ 的請求將在任何副作用發生前 Fail-Closed，回傳 `rejected_resource_bound` 錯誤。

## 5. Artifact 輸出與 Handoff 政策
* **輸出目錄**：符合 R5B 的安全路徑限制，寫入 `artifacts/m8r_03d/{run_id}/` 下。
* **包含項目**：
  * `execution_request.json`
  * `execution_preview.json` (或附加於 plan 內)
  * `approval_record.json`
  * `execution_plan.json`
  * `normalized_observations.json`
  * `execution_result.json`
* **Retention 政策**：預設保存 30 天，本任務不實作自動清理 scheduler，僅標記 `expired_artifact_behavior = eligible_for_cleanup`。

## 6. Scheduler / Polling 旗標與未來擴充點
* 旗標 `repository_internal_scheduler_enabled` 與 `repository_internal_polling_enabled` 於當前 profile 中明確設為 `false`。
* 保留 `future_external_agent_repeated_execution_supported = true` 作為未來擴充路徑。

## 7. 本任務實際修改點
1. **`docs/data_capabilities/m8_source_capability_registry.json`**：新增 `phase_c_activation_status` 等外層旗標，並為 Sources 條目寫入 `phase_c_activation_state`。
2. **`scripts/m8r_03d_watchlist_execution_plan.py`**：
   * 加入 Targets 與 Operations 計算，判斷是否為 `expanded_scope` 或 `rejected_resource_bound`。
   * 新增來源 `phase_c_activation_state` 檢查。
   * 產出 `execution_preview`。
3. **`scripts/m8r_03d_watchlist_controlled_executor.py`**：
   * 在 `execute_watchlist` 中加上 `preview` 與 `approval` 的輸入與合法性判定。
   * 強制檢查 `preview` 與 `plan` 的一致性（不可包含 preview 中未提及的 target, source_family, operation_type, timing_class）。
   * 將 explicit approval 與 preview 的 metadata 寫入最後的 `execution_result.json` 並落盤保存。
