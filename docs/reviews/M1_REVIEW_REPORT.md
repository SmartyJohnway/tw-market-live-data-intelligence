# M1 目標檢驗報告 (Deliverable MVP Workbench)

## 1. Executive Summary

本次檢驗對 `main` 分支進行了全面性驗收，目的是確認是否滿足 **M1 — Deliverable MVP Workbench** 的目標。
檢驗過程中嚴格遵循「不修改程式碼」的原則，在獨立的虛擬環境中實際執行了各項指令與靜態審查，確認基本指令可運行，且產生的報告具備動態證據效力。
整體而言，MVP 架構已經落實，並且移除了先前的危險開源 Proxy (serverless functions)。然而，程式碼與功能中仍有一些注意事項 (caveats)，將於後續細節說明。

---

## 2. Final M1 Status

**判定結果: M1_ACCEPTED_FOR_M1_SCOPE**
**repo_status = deliverable_mvp_completed**
**overall_project_status = completed_with_deferred_caveats**

本專案實作滿足了 M1 不追求即時看盤體驗、重於 MVP 架構可用性的目標，基礎建設 (API, Probes, Tests, Report Generators) 皆已齊全。存在的 Caveats 主要不影響當前 M1 架構的正常運行與驗收，可作為後續 M2/M3 優化參考。

---

## 3. Validation Commands Executed

在檢驗中實際執行了以下指令：
```bash
# 1. 建立隔離環境
python3 -m venv venv
source venv/bin/activate

# 2. 安裝依賴 (M1.1)
python -m pip install -r requirements.txt

# 3. 語法檢查 (M1.1)
python -m compileall scripts server tests

# 4. 執行離線測試 (M1.1)
pytest -m "not network" -v

# 5. 執行全部 Probe 獲取資料並生成報告 (M1.2, M1.4)
python scripts/run_all_probes.py

# 6. 啟動 FastAPI 服務 (M1.5)
uvicorn server.main:app --host 127.0.0.1 --port 8000 &
sleep 2 && curl -s http://127.0.0.1:8000/api/health
curl -s http://127.0.0.1:8000/api/matrix
kill $(lsof -t -i :8000)
```

---

## 4. Terminal Output Summary

*   **`pip install -r requirements.txt`**: 成功安裝所有套件 (FastAPI, pytest, pandas, uvicorn 等)。
*   **`python -m compileall`**: 沒有任何編譯錯誤。
*   **`pytest -m "not network" -v`**: 10 個離線測試全部通過。
*   **`python scripts/run_all_probes.py`**: 依序探測 TWSE, TPEx, Yahoo, TWSE MIS, FinMind, Fugle, Fubon 成功產出報告 (`docs/`, `research/`, `frontend/`)。其中 FinMind `TaiwanFutureDaily` TX 遇到 HTTP 422 預期錯誤，Yahoo Finance 對於 `TX.TW`, `FUNDA.TW` 回傳 404，皆被 Envelope 成功捕捉到並放在 `errors` 與 `failed_targets` 欄位，沒有導致 Runner 崩潰。
*   **`uvicorn server.main:app`**: 成功啟動，`/api/health` 正常回應 `{"status":"healthy"}`，`/api/matrix` 正確回傳靜態 json 檔案。

---

## 5. File/Document Review Summary

檢查了以下文件與程式碼：
*   **`README.md`**: 包含清楚的安裝、測試、Probe 執行、Local API 與 Frontend 說明，並聲明了安全注意事項 (No Open Proxies, Secrets Management)。
*   **`server/main.py`**: CORS 明確限定在 `localhost` 與 `127.0.0.1`。不再包含任何可能外流的 Proxy 邏輯。
*   **`frontend/public/index.html`**: 為真正的 HTML 網頁，具有基本的 CSS 樣式與 JS 邏輯來載入 `matrix.json`。
*   **`scripts/probe_utils.py`**: 確實實作了完整的 Data Contract Envelope，支援了 `doc_only`, `auth_required` 狀態標記。

---

## 6. M1.1 Repository Health

- **Expected Criteria**: Repo 可 clone、安裝、編譯、測試。Python 檔案有效，requirements 正確，無假 HTML 或明顯空檔案，無 secrets 寫死。
- **Actual Evidence**: `pip install`, `compileall`, `pytest` 皆成功通過。無發現 token 寫死在程式碼中。
- **Commands / Files Checked**: `python -m compileall scripts server tests`, `python -m pip install -r requirements.txt`, `pytest -m "not network" -v`
- **Result**: Pass
- **Caveats**: 沒有發現阻擋 M1 的 Caveats。
- **Severity**: None
- **Proposed Next Action**: Proceed to M2.

## 7. M1.2 Probe Framework Baseline

- **Expected Criteria**: 可低頻探測目標，每個 Probe 獨立執行且回傳標準 Envelope、標示 source_type 與 contract_status。失敗不崩潰，doc_only/auth_required 不誤標。
- **Actual Evidence**: `run_all_probes.py` 正確捕捉並紀錄 FinMind 和 Yahoo 探測的局部 422/404 失敗，並將 Fubon API / Fugle API 標記為 `doc_only` 和 `auth_required`，同時確保它們的 `is_usable_now` 判定為 `false`。
- **Commands / Files Checked**: `python scripts/run_all_probes.py`, `scripts/probe_utils.py`
- **Result**: Pass
- **Caveats**:
  - 部分 Live Network Probe 由於缺少 Credentials (如 FinMind 未提供 Token 時受到 Free-tier Rate limit 限制) 會導致部分預期探測失敗，或 Yahoo 的 `TX.TW` (期貨) 等不支援。
- **Severity**: Minor
- **Proposed Next Action**: 這在 M1 是完全可以接受且預期的行為，Framework 成功容錯處理，留待 M2 新增更多 Auth 測試與 Mock。

## 8. M1.3 Standard Envelope

- **Expected Criteria**: 資料來源輸出統一結構 (包含必要的 `probe_id`, `schema_fingerprint`, `is_usable_now` 等欄位)。
- **Actual Evidence**: 從 `matrix.json` 中抽樣確認，每一個 Probe 產出的資料均包含所有要求的必要欄位，並確實針對 `auth_required` 給出 `is_usable_now: false`。
- **Commands / Files Checked**: `cat frontend/public/matrix.json`, `scripts/probe_utils.py`
- **Result**: Pass
- **Caveats**:
  - Semantic Caveats: `delay_status` 與 `freshness_status` 目前大多基於靜態判斷寫死 (例如: `delay_status: eod` 或 `delay_status: realtime`)，而未動態根據 Request Time 與 Target Data Time 進行時間戳驗證的精準計算。
- **Severity**: Minor
- **Proposed Next Action**: 可以在 M2 階段強化針對 `staleness_seconds` 動態計算和 `freshness_status` 推論的穩定性。

## 9. M1.4 Report Generator

- **Expected Criteria**: 自動產生文件 `capability_matrix.md`, `source_catalog.md`, `probe_log.md`, `matrix.json`, `ai_context_pack.json/md`。
- **Actual Evidence**: 所有對應的文件在 `docs/`, `frontend/public/`, `research/`, `research/generated/` 中均正確產出。
- **Commands / Files Checked**: `ls -l docs/ frontend/public/ research/ research/generated/`
- **Result**: Pass
- **Caveats**:
  - Formatting Caveats: 輸出的 Markdown 表格過長、AI Context Pack 稍微偏大，人類閱讀或 Token 消耗在後續可能會帶來輕微負擔。
- **Severity**: Minor
- **Proposed Next Action**: Deferred 到 M2/M3 可以考慮實作 Report 的分頁或更精細的資料抽樣。

## 10. M1.5 Local API / Frontend

- **Expected Criteria**: FastAPI 可啟動，CORS 限制 localhost，Frontend 為真 HTML 且可讀取 matrix.json，無 open proxy。
- **Actual Evidence**: `uvicorn` 成功在 port 8000 啟動，CORS 寫死 localhost/127.0.0.1，Frontend 的 index.html 架構正常，無代理外部請求邏輯。
- **Commands / Files Checked**: `server/main.py`, `frontend/public/index.html`, `curl` 測試。
- **Result**: Pass
- **Caveats**:
  - Local-only Caveats: 當前純粹為本地測試介面，目前未配置 Docker 或 Production 佈署機制。
- **Severity**: Deferred (M2/M4)
- **Proposed Next Action**: 不影響 M1，保留至未來階段處理。

---

## 11. Blocking Issues
無。

## 12. Major Caveats
無明顯 Major Caveats。

## 13. Minor Caveats
1. **Probe Framework Failures on Network/Source Limitations:** FinMind Rate Limits 或是 Yahoo 不支援的 Targets 預期回報失敗，系統已妥善捕捉，但需要更多真實 API Credentials 驗證。
2. **Standard Envelope Dynamic Calculation:** 時間戳跟 Freshness 狀態推斷依賴部份硬編碼，未全面落實時間差精準計算。

## 14. Deferred M2/M3/M4 Items
1. **Production Deployment & Dockerization:** API / Frontend 的非 Local 佈署方式。
2. **Report Formatting Optimizations:** JSON/MD 產生的結果壓縮與排版優化。
3. **MCP Server Integration:** 如果要正式對接 Claude MCP，需確保 Server 規格完全相容與註冊。

---

## 15. Deferred Caveats
**Deferred to M2A:**
- Add GitHub Actions CI for compileall and offline pytest.
- Fix documentation consistency, especially any obsolete Netlify proxy references.
- Fix capability_matrix Markdown formatting / escaping for URLs containing pipe characters.

**Deferred to M2B:**
- Build TWSE MIS protocol documentation.
- Build TWSE MIS field dictionary.
- Expand TWSE MIS normalized snapshot fields and tests.

**Deferred to M3:**
- AI context pack v2.
- latest_market_snapshot.json.
- chatgpt_briefing.md.

**Deferred to M4:**
- MCP server consistency with config/market_targets.json.
- Read-only MCP tools before explicit live probe tools.

---

## 16. Proposed Next Milestone
本專案已達標，無須阻擋 M1 驗收。即將進入 M2A 階段：`M2A-CI-DOC-CONSISTENCY-AND-MATRIX-FORMAT-HARDENING`。

## 17. Clear Acceptance Decision

**M1_ACCEPTED_FOR_M1_SCOPE**
