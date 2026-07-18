# M8R-03E Phase C Owner Activation Decision Contract

## 1. Phase C Readiness Assessment

目前 Phase C 已完成 R5A 跨層 Fixture 合約與 R5B 跨平台檔案系統安全機制的建置，並達到 `resolved_with_caveats` 的狀態。PR #157 (merge commit `fa4cf6c155eba54fd4891dfb2055965f447f5cd7`) 已成功合併，為明文明確的 Activation Decision 提供了必要的技術基礎。

## 2. Owner Decision Definition
Owner 正式核准以下決策：
**APPROVE_PHASE_C_CONVERSATION_DRIVEN_ACTIVATION_WITH_EXPANSION_PATH**

### 核心原則與規範
1. **對話觸發單次獲取**：現階段僅允許使用者在對話中明確確認後，執行一次真實網路的台股/ derivatives 觀察與獲取。
2. **執行預覽合約**：任何真實網路執行前必須先產生可讀的 `Execution Preview`。
3. **自然語言確認**：使用者以自然語言確認即可（例如：「執行」、「同意」、「可以」），不要求輸入技術雜湊、Technical token 或 cryptographic receipts。
4. **可稽核的一次性執行**：每次執行仍是一個 bounded、可追蹤、可稽核的 one-shot 執行，並保存 detailed evidence bundle。
5. **Registry 驅動控制**：由 canonical source capability registry 控制哪些 source family 可被啟用與執行。
6. **未來重複執行支持**：架構上必須允許未來外部 AI agent 或 automation 重複呼叫同一個 one-shot contract，保留擴充性。
7. **嚴格禁止事項**：
   - 不啟用 repository 內部的 scheduler、daemon、polling。
   - 不啟用自動的 LLM follow-up 獲取。
   - 嚴格禁止交易與下單（`Prohibited`）。
   - 不啟用未經授權的外部發布。

---

## 3. Activation Profile

本階段正式啟用 `phase_c_conversation_driven_one_shot.v1` 設定檔，其規格如下：

```json
{
  "activation_profile_id": "phase_c_conversation_driven_one_shot.v1",
  "activation_state": "enabled_with_caveats",
  "execution_mode": "conversation_triggered_one_shot",
  "approval_mode": "conversation_explicit_approval",
  "execution_preview_required": true,
  "repository_internal_scheduler_enabled": false,
  "repository_internal_polling_enabled": false,
  "persistent_autonomous_watchlist_enabled": false,
  "automatic_llm_followup_execution_enabled": false,
  "future_external_agent_repeated_execution_supported": true,
  "future_repeated_execution_activated": false
}
```

### 功能啟用對照表

| 功能分類 | 產品能力 / 端點類型 | 目前啟用狀態 | 未來擴充路徑與 Caveat |
| :--- | :--- | :--- | :--- |
| **已啟用** | Network Retrieval, Normalized Observation, Currentness Evaluation, Evidence Bundle, Citation Map, Provenance Manifest, AI-safe Projection, Conversation Handoff, Bounded Artifact Retention | `Activated` | 僅限於 one-shot 對話觸發執行。 |
| **未啟用** | Repository-owned Scheduler, Background Daemon, Continuous Polling, Persistent Autonomous Watchlist, Automatic LLM Follow-up Retrieval, Automatic Retry Loop, Frontend Publication, External MCP Exposure | `Not Activated` | 未在當前 Profile 啟用，未來需要獨立的 Owner Activation Decision。 |
| **嚴格禁止** | Trading, Order Execution | `Prohibited` | 永久禁止（在此 Phase C 範圍內）。 |

---

## 4. Resource Bounds and Rejection Policy

為了防止濫用或無限遞迴呼叫，實施以下資源限制邊界：

* **Normal Scope**：
  * Targets 數量 $\le 10$ 且 Operations 數量 $\le 30$。
  * 正常進行 preview 並於 approval 後執行。
* **Expanded Scope**：
  * Targets 數量介於 $11 \sim 50$ 或 Operations 數量介於 $31 \sim 100$ 之間。
  * 允許執行，但 Execution Preview 中必須標記 `expanded_scope = true` 並列出具體的 target/operation 數量與預估網路呼叫。
* **Hard Rejection**：
  * Targets 數量 $> 50$ 或 Operations 數量 $> 100$。
  * 執行器必須在產生任何 side-effects（建立暫存檔、寫入 artifacts 等）前立即拒絕執行，回傳 `rejected_resource_bound` 錯誤。

---

## 5. Successor Roadmap

本決策合約完成後，後續的獨立任務將登記為：
`M8R-03E-EOD-EXPECTED-TRADE-DATE-AND-NATURAL-DISASTER-SESSION-STATUS`
用以整合官方交易日曆、台北市停班停課天然災害停開市狀態、以及官方 EOD合理發布延遲評估，而非在本任務中強制解析。
