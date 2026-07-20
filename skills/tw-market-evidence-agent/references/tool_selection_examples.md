# Prompt-Neutral Tool-Selection Examples

This document provides examples of how the AI should compose Unified Requests based on user conversation intents.

---

## Example 1: Current Quote and EOD Reference for Listed Stock

- **User Intent**: "台積電現在多少錢？跟昨天收盤比起來如何？"
- **AI Decision Process**:
  - Target: Ticker `"2330"` with market hint `"TWSE"`.
  - Data Needs: 
    - `current_observation` (priority: required) for the live-ish quote.
    - `official_eod_reference` (priority: required) for yesterday's completed close.
    - `session_status` (priority: optional) to check if the market is currently active.
- **Request Snippet**:
  ```json
  {
    "schema_version": "unified_market_evidence_request.v1",
    "request_id": "req-tsmc-quote",
    "targets": [
      {"input": "2330", "market_hint": "TWSE", "resolution_requirement": "exact"}
    ],
    "data_needs": [
      {"type": "current_observation", "priority": "required"},
      {"type": "official_eod_reference", "priority": "required"},
      {"type": "session_status", "priority": "optional"}
    ],
    "execution_mode": "preview"
  }
  ```

---

## Example 2: Official EOD for OTC Target

- **User Intent**: "給我環球晶 (6488) 昨天的收盤價與交易量。"
- **AI Decision Process**:
  - Target: Ticker `"6488"` with market hint `"TPEX"`.
  - Data Needs:
    - `official_eod_reference` (priority: required) to get completed session details.
    - `identity` (priority: optional) to confirm listing details.
- **Request Snippet**:
  ```json
  {
    "schema_version": "unified_market_evidence_request.v1",
    "request_id": "req-gwc-eod",
    "targets": [
      {"input": "6488", "market_hint": "TPEX", "resolution_requirement": "exact"}
    ],
    "data_needs": [
      {"type": "official_eod_reference", "priority": "required"},
      {"type": "identity", "priority": "optional"}
    ],
    "execution_mode": "preview"
  }
  ```

---

## Example 3: Performance Lookback Request

- **User Intent**: "台積電最近 20 天漲了多少？"
- **AI Decision Process**:
  - Target: Ticker `"2330"` with market hint `"TWSE"`.
  - Data Needs:
    - `recent_performance` (priority: required) with `lookback_trading_days` parameter.
- **Request Snippet**:
  ```json
  {
    "schema_version": "unified_market_evidence_request.v1",
    "request_id": "req-tsmc-perf",
    "targets": [
      {"input": "2330", "market_hint": "TWSE", "resolution_requirement": "exact"}
    ],
    "data_needs": [
      {
        "type": "recent_performance",
        "priority": "required",
        "parameters": {
          "lookback_trading_days": 20
        }
      }
    ],
    "execution_mode": "preview"
  }
  ```

---

## Example 4: Clarification for Ambiguous Target

- **User Intent**: "台積最近表現怎樣？"
- **AI Decision Process**:
  - Target `"台積"` is ambiguous. It could refer to 台積電 (2330) or related entities.
  - **AI Action**: Do not compose request immediately. Respond to the user:
    - *"您提到的「台積」是否指台積電 (TWSE 2330)？請確認，以便我為您產生正確的市場數據請求。"*
- **Handoff / Next Step**: Once the user confirms, compose the Request JSON using the resolved canonical code.
