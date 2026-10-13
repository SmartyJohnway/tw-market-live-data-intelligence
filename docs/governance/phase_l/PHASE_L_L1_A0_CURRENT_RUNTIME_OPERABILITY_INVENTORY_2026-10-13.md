# Phase L L1-A0 — Current Runtime Operability Inventory

日期：2026-10-13。原始盤點曾觸發 `L1_A0_ARCHITECTURE_CONFLICT`；經 A0R 最小修復及下列非網路回歸後，disposition 更新為 **`L1_A0_RUNTIME_OPERABILITY_INVENTORY_COMPLETE`**。
本文件記錄衝突、修復及完整 A0 inventory；不是 L1-A1 授權。

## 1. Executive finding

- Current Native runtime 已有 Workbench/Local Service launcher、offline preload、HTTP liveness、identity status、capability projection 與獨立 stdio MCP。
- 最大一般性 gap 是 lifecycle UX fragmentation；不能將這些既有 substrate 全部視為 ADD。
- `/api/health` 只表示 service alive；identity、route 與 SDK readiness 分別由其他 surface 表達。
- Canonical Audit/receipt 已有 request/execution identity、hash、source timing/currentness 與 failure/accounting；不應重建一份 operational truth。
- Product stop、process ownership、統一 read-only doctor、operational correlation/timing 尚未在 inspected current entry points 找到完整機制。
- **已修復阻斷項：** current H2/H3 production path 不再依賴 A6 transport accounting；三個指定 current modules 可在 Windows import。
- A6 acceptance accounting 保留作歷史材料，未 port 成 product subsystem；H2/H3 governed route 與 execution contract 保持不變。
- 修復沒有引入新產品架構；只把歷史 acceptance instrumentation 從 current product path 解耦。

## 2. Authority、identity 與 stop evidence

僅在 `D:\Codex-Workspace\projects\tw-market-live-data-intelligence-phase-l-l1` 工作。
Branch `phase-l/l1-runtime-operability`；starting HEAD `e8454bf13df87e542d51e9dc815d143ff110e47b`；起始 porcelain 空白。
本機 `origin/main` 等於 HEAD，HEAD commit subject 為 Merge PR #333: Phase L L0 Production Boundary & Architecture Contract。
本機 `main` ref 落後於 `origin/main`；未切換、fetch 或改 refs，因此不聲稱重新驗證了 remote 最新狀態。

依序 recovery：`README.md`、`PROJECT.md`、`ROADMAP.md`、`HANDOFF.md`、`AGENTS.md`、
`docs/governance/phase_l/PHASE_L_L0_PRODUCTION_BOUNDARY_AND_ARCHITECTURE_CONTRACT_2026-10-13.md`。
L0 `PHASE_L_L0_ARCHITECTURE_CONTRACT_FROZEN` 是不可違反的 boundary。
部分舊 Phase H/K prose/checklist 仍留在 front-door/operator 文件；本次以 current Phase L header、L0 與 current implementation 為準，不修改歷史或其他 authority。

### 原始 architecture conflict（保留發現與證據）

| Evidence | Finding |
|---|---|
| `scripts/a6_session_transport.py:1-6` | 自稱 A6-only durable pre-dispatch accounting；頂層 `import fcntl`。 |
| `scripts/m8r_06_03_production_adapter.py:766-767` | Current H3 bounded month fetch 無條件 import `operation_context`；不是由 `A6_SESSION_ROOT` gate 保護 import。 |
| `server/services/phase_h_h2_twse_exright_executor.py:266-267` | Current H2 execution 同樣無條件 import。 |
| `server/services/phase_h_h3_twse_stock_day_adapter.py:97`；H2 executor `:68` | Source transport 亦引用 A6 reserve/complete accounting。 |
| Current V3 routing matrix；`config/m8r_06_03_executor_registry_metadata.json` | H3 normal production route 與 H2 `phase_h_h2_twse_exright_pre_executor` 屬 current executable/registered route；不能將上述引用當作純歷史檔案排除。 |
| `python -B -c "import scripts.a6_session_transport"` | 本機 Python 3.13.7 / Windows 10：`ModuleNotFoundError: No module named 'fcntl'`，在任何 source request 前失敗。 |

`_paths()` 在無 `A6_SESSION_ROOT` 時可 return None，**無法避開頂層 import failure**。
有該 ENV 時會使用 `session.json` / `transport-ledger.jsonl`、A6 attempt budget 與固定 2330 accounting。
未執行 H3/H2 source acquisition，未消耗 authorization；不推定所有 runtime 能力皆失敗。
Startup checks 與 capability metadata PASS 不足以證明實際 Windows route operability。

### Architecture conflict remediation — `REMOVE_A6_ACCEPTANCE_INSTRUMENTATION_FROM_CURRENT_PRODUCT_PATH`

Root cause與注入來源：commit `79dcb1a7` 同時引入合法 H2 activation 與 Phase J A6 acceptance instrumentation；其後 instrumentation 被注入 H2/H3 product call path。修復只移除 instrumentation，不 revert H2 activation，也不改 capability/catalog/routing/MCP/schema。

| Repair surface | Change | Preserved contract |
|---|---|---|
| `scripts/m8r_06_03_production_adapter.py` | H3 orchestration恢復直接呼叫 `fetch_twse_stock_day_month(...)`；移除 A6 `operation_context`/`A6_ATTEMPT`。 | target/month binding、lookback/month ceiling、timeout、compatibility SSL、response cap、projection/citations。 |
| `server/services/phase_h_h3_twse_stock_day_adapter.py` | 移除 A6 reserve/complete hooks、`_a6_reservation` 與 A6 imports；恢復原 bounded opener/read flow。 | no redirect、TLS policy、timeout、byte cap、HTTP/status/content/target/month validation、normalization/failure codes。 |
| `server/services/phase_h_h2_twse_exright_executor.py` | 移除 A6 reserve/complete/context 與 `A6_ATTEMPT`；移除因此無用的 `os` import。 | exact endpoint、single request/no retry、4 MiB cap、H3 exact dependency、H2 evidence/materialization、failure codes、H4 derivation。 |
| `scripts/m8r_05b_03/orchestrator.py` | 將 H2 H4 derivation import移入 approved execute branch，解除 direct H2 import circularity，保持執行時 derivation不變。 | approved execution仍呼叫同一 `derive_h4_for_completed_plan`。 |
| `scripts/phase_i_i3_a4_compat.py` | 歷史 normalizer接納舊 A6-wrapped snapshot並轉成baseline，也接納 current uninstrumented product call。 | 舊snapshot compatibility及I3 comparison仍可用；不把wrapper加回product。 |
| `tests/unit/test_m8r_06_03_production_adapter.py`、`tests/unit/test_phase_i_i3_a4_compat.py` | 加入三個 current source AST import guard；固定歷史 normalizer兩種輸入行為。 | 不對全repository禁用A6；historical A6 tests/evidence保留。 |

**Windows import result：** 三條指定 `python -B -c "import ..."` 命令均 exit 0；載入H2/H3後 `scripts.a6_session_transport` 不在 `sys.modules`。未設定 `A6_SESSION_ROOT`，亦無 A6 session。

**No-network result：** transport cases使用injected responses/mock opener；stdio integration使用隨機loopback mock service。此 tranche market/source acquisition = 0、SM/Watchlist mutation = 0、authorization consumption = 0。A6 module與Phase J historical tests/evidence保留，沒有以Windows locking重建A6 subsystem。

## 3. Current topology

```text
operator browser → Workbench static UI ─┐
                                      ├→ HTTP Local Service → governed runtime
Agent host → separate stdio MCP process┘                        │
                     (loopback HTTP)                           ├ identity/watchlists
                                                               └ authorize → bounded child → Result/Audit
```

`run_unified_workbench.py` 以 Uvicorn 啟動同一 process 的 Local Service，UI 無獨立 backend daemon。
`run_unified_market_evidence_mcp.py` 是 host 啟動的獨立 stdio process，不建立 HTTP listener、不自動啟動 Local Service。
Execution child 是 `unified_mode_b2_execution.py` 用 `sys.executable`、固定 wrapper、repo cwd 與最大 130 秒 deadline 啟動的 bounded subprocess。
Optional Tunnel/DPAPI/ChatGPT connector 不在 core topology 或 readiness prerequisite。

## 4. Inventory matrix（stop 前確認的範圍）

| Area | Existing mechanism | Evidence/path | Classification | Gap | L1 action |
|---|---|---|---|---|---|
| A startup | Workbench preload + `--startup-check`；`--host`/`--port` | `scripts/run_unified_workbench.py` | REUSE / WRAP | 與其他 status commands 分散 | 重用 preload，不新增 startup acquisition |
| A dependency | JSON report、import checks、Python 3.11/3.13、mcp 1.29.0 guard | `scripts/verify_environment.py` | REUSE | 無完整 product doctor aggregation | 包裝既有 checks |
| A identity | `status/history/update --live/rollback/migrate-legacy-active`、`--root` | `scripts/manage_security_master.py` | REUSE / WRAP | Software update 與 identity refresh UX 尚未統一 | 保留 explicit init/update boundary；A0 不執行 mutation |
| B shutdown | Foreground Uvicorn；MCP SDK stdio context | 兩個 current launchers | WRAP / ADD | 無 product stop、PID ownership 或 duplicate-start arbitration | 後續定義小型 owned-process lifecycle；不預設大型 manager |
| C alive | `/`；`GET /api/health` 固定 healthy | `server/main.py` | REUSE | 無 dependency/product readiness summary | 保留 liveness，另聚合 readiness |
| C ready | schema/catalog preload；SM fail-closed；catalog→route→executor projection | `unified_mode_a.py`、`unified_local_service.py` | REUSE / WRAP | 不是 single status；registration 不保證 import/execute 健康 | 統一 read-only status，保留各層差異 |
| D failures | HTTP reason codes/trace_id、MCP sanitized errors、child timeout/protocol errors | `unified_workbench_router.py`、`unified_mcp/error_mapping.py`、`unified_mode_b2_execution.py` | REUSE / WRAP | trace_id 多在錯誤時生成，非完整跨 process correlation | 接到 operational events，不改 canonical packages |
| D telemetry | receipt/Audit IDs/hash；source observed time、attempt governance、I3 bytes/HTTP/TLS/retries/failure_phase | Audit V3 schema、production adapter、`phase_i_i3_production_transport.py` | REUSE | source semantic time 不等於 elapsed adapter duration | 保留 canonical truth；僅補缺少的 operational duration |
| D logs | launcher JSON/text stdout；MCP diagnostics stderr；Uvicorn default operational output | 兩個 current launchers | WRAP / ADD | 未找到統一 structured sink、resource sample、bounded log lifecycle | lean events + bounded output；不建 logging framework |
| E paths | `__file__` repo roots；SM/Watchlist ENV；control root ENV | loader、Watchlist store、Mode B2/C | REUSE / WRAP | checkout/state coupled，部分 relative ENV 依 cwd | 顯示 resolved paths/來源；physical relocation 後續處理 |
| F config | Workbench CLI defaults；MCP CLI > ENV > default | launchers、Local Service client | REUSE / WRAP | 無 shared user config、全域 precedence resolver | 後續最小 resolver，不能 A0 refactor |
| G MCP | SDK guard、schema snapshot、service-contract check、exact static six tools | `server/unified_mcp/`、stdio launcher | REUSE | 依賴 running Local Service；不驗 SM 或 route import | 保留六工具，包裝 startup diagnosis |
| H regression | current MCP contracts/errors、service projection、HTTP/static health、real stdio loopback | 本文件 §10 tests | REUSE | 未涵蓋發現的 Windows route import conflict | 衝突先裁決，不能讓 mocked PASS 遮蔽問題 |
| H older diagnosis | environment_checks 檢查 M5F/observation/source-health/舊 readonly UI | `scripts/operator_workbench.py`、`run_environment_diagnostics.py` | HISTORICAL_ONLY / selective REUSE | 含 live-probe suggestions 與較舊 Python policy | 只抽取適用 checks，不照搬 readiness |
| H release | release checklist 舊 `server/mcp_server.py` startup、M5F/M5Q；Windows smoke 同樣偏 M5 | `docs/release/RELEASE_CHECKLIST.md`、`.github/workflows/windows-compatibility-smoke.yml` | HISTORICAL_ONLY / DEFER | 不是 current six-tool release operability gate | L7 review，不作 L1 core prerequisite |
| Conflict (remediated) | A6 transport import/optional session accounting 原殘留於 current H3/H2 | §2 evidence + remediation below | HISTORICAL_ONLY；current dependency已移除 | audited H2/H3 chain無A6 product dependency | REUSE current bounded transport；A6保留historical-only |

## 5. Startup / shutdown / status / health

Workbench default `127.0.0.1:8000`，CLI 可改 port；只接受 `127.0.0.1` / `localhost` / `::1`。
Normal startup preload schema/catalog/active identity，無 startup fetch；`NOT_INITIALIZED` 返回合法 preload report，service 可啟動。
其他 preload exception 以 exception class 與 `governed_runtime_preload_failed` 表達並 exit 1。
Dependency import 若在 argparse 前失敗，仍可能是 Python traceback，非完整 normalized error。
Readiness：identity-required HTTP operation 在未初始化時 503 `SECURITY_MASTER_NOT_INITIALIZED`；dependency missing/malformed 為 500；capability authority failure 可為 409。

Launcher 沒有 product-level stop/PID file/ownership registry/reuse-existing-service decision。
Duplicate bind/occupied port 委由 Uvicorn/socket failure；無產品 stale-process recovery，不應自動 kill port owner。
Ctrl-C/graceful shutdown 使用 Uvicorn/SDK 自身 lifecycle；repo 未提供 Windows-specific terminal-close guarantee。
本次未啟動真实 Local Service daemon、未測 Ctrl-C/terminal close 或 occupied-port exit，因此這些 OS 行為不標示 empirically PASS。
MCP 正常結束依 SDK stdio stream/context 與 host process lifecycle，無另外 product stop semantic。

組成 unified status/doctor 的大部分 substrate 已有；真正需補的是聚合、read-only path/state inspection、owned-process identity 與 normalized operational outcome。
`PersistentWatchlistStore.__init__` 會 mkdir 與 `_initialize()`；read-only doctor **不能為了檢查而建構 production store**。

## 6. Diagnostics

**Audit = governed truth；operational log = runtime diagnosis。**
Audit V3 有 request/authorization/receipt/evidence identity/hash與 verification；operation/evidence sidecar 保留 source timing、currentness、citations與attempt outcomes。
I3 transport 已有 GET/retry count、HTTP/MIME、partial/full bytes、hash、TLS/redirect policy、failure phase，不應複製 raw evidence 到 log。
Execution child 已有 timeout、protocol-invalid、transport/accounting flags；HTTP/MCP 已有 bounded failure codes。
但 retrieved/published/effective time 是 evidence semantics，不是 process latency；未確認一致的 monotonic source/adapter duration、CPU/RSS/disk samples 或 end-to-end operational request correlation。
Inspected product server 沒有自訂 Python logger/basicConfig framework；launcher text/JSON、MCP stderr 與 Uvicorn output 是現有 operational diagnostics。
需補的 lean events 應只包含 status、既有 IDs/reference、elapsed duration、reason code、bounded resource sample；限制輸出，不記 secrets/raw payload。
A6 ledger 不是可直接 REUSE 的 product logging substrate。

## 7. Path / config / portability

| Path/config | 現況與風險 |
|---|---|
| application | launchers/server/schema/catalog/frontend 多由 `Path(__file__)` derive repo root，通常不依 original checkout 字串；需要完整 layout。 |
| identity | default `data/security_master`，active release process-lifetime cache；runtime loader 支援 `TW_MARKET_SECURITY_MASTER_ROOT`。Manager `--root` default constant，未讀同 ENV，可能 status 檢查到與 service 不同 root。 |
| watchlists | default `data/watchlists/watchlists.sqlite3`；`TW_MARKET_WATCHLIST_ROOT`、SM ENV 可 override，expanduser/resolve；root constructor 有寫入。 |
| governed packages | `artifacts/m8r_06_03_workbench`；`M8R_06_03_CONTROL_ROOT` 同用於 Mode B2/C/child；Result/Audit/control/claims/evidence 由 package-contained paths 管理。 |
| temp/cache | source-operation memory caches、process identity cache 已存在；stdio test 使用 tempfile/mock server 並 context cleanup。無統一 product temp/cache/log root；A0 停止前未完成全 repo derived-state enumeration。 |
| hard-coded path | inspected current launchers/server/config 未搜到必要的 `C:\Users\<specific-user>` 或 `D:\...` core root；不聲稱整 repo 無此字串。Historical pointer/test/provenance 絕對路徑不能當 runtime default。 |
| cwd/home/user | relative ENV roots 經 resolve 會依 cwd；SM loader Path(value) 與 Watchlist expanduser policy 不一致；未有統一 AppData/home state contract。換 user/machine 不能靠舊 data/venv/session 達成 PASS。 |
| precedence | Workbench CLI > default；MCP `--service-url` > `UNIFIED_MARKET_EVIDENCE_SERVICE_URL` > default；root functions/manager各自處理。未有 L0 CLI > ENV > user config > default 的完整 shared resolver。 |
| exposure | Workbench host guard、MCP loopback URL validator、HTTP only/explicit port/no credentials/query/redirect；client `trust_env=False`。直接 `uvicorn server.main:app` 可繞過 launcher host/preload guard，應視 developer path，不推薦代替 product start。 |

Application/state 現在預設共置 checkout；ENV seams 可重用，但未證明完整 P1-P6 portability。
Windows `fcntl` 是已實證的 machine/platform blocker；checkout/user state耦合與 config drift 是其他風險。
Physical durable-state mapping、migration/backup/restore、Docker packaging 與跨機 acceptance 分別 DEFER L2/L6；L1只診斷與一致傳遞既有 roots。

## 8. MCP operability

Current launcher先驗 `mcp==1.29.0`、build canonical schema/tool snapshot，再 GET `/api/unified/capabilities` 比對 Local Service contract。
SDK mismatch exit 4；tool config failure exit 2；Local Service error exit 3；successful startup-check exit 0，diagnostics 寫 stderr。
Module import failure（例如根本缺 SDK）可能早於 guard，以 traceback 結束。
Runtime `_serve` 使用同一 check、靜態 snapshot；`list_tools`/dispatch 只提供既有六工具，未有 generic REST proxy。
六工具 exposure 由 current contracts/server 保證，且本次 real stdio test 驗證 exact list。
Startup-check 不自動啟動 service、不 fetch market、不初始化 SM；也不证明 source executor Windows import readiness。
HTTP client為loopback、15 秒普通 deadline、145 秒 action deadline、無retry；request/response已有 byte bounds。
Unreachable為 `local_service_unavailable`；timeout/protocol/contract mismatch各自 reason code；tool failure `isError=true`、sanitized structuredContent/trace_id。
Launcher diagnostics stderr，SDK stdout 用作protocol；real stdio test成功可證正常路徑未污染protocol，不能聲稱所有第三方exception都已覆蓋。
Exact SDK pin 是**目前 L1 operational prerequisite**；read-only doctor應報告mismatch。是否放寬 range 屬 L7，不是理由先改 pin。

## 9. Decision summary / proposed minimum L1-A1

| Classification | 決策 |
|---|---|
| REUSE | offline preload、dependency verifier、SM status/active release loader、liveness、capability projection、six-tool MCP、canonical Audit/accounting/failure codes、bounded child/client。 |
| WRAP | 單一 lifecycle entry point、各層 status/doctor聚合、CLI/ENV有效設定與root來源、現有 diagnostic輸出。 |
| ADD | 最小 owned-process start/stop identity與duplicate/occupied-port outcome；無寫入的state inspection；structured operational correlation/duration與bounded output。未證明需要大型process manager或新logging framework。 |
| DEFER | L2 replay/retention/migration/backup；L3 source drift；L4 broader security/load/resource ceilings；L5 extension；L6 physical packaging/Docker/P1-P6 acceptance；L7 SDK range/release/CI overhaul。 |
| HISTORICAL_ONLY | 舊M5 operator/readiness/release machinery、J/K hostfixtures/distribution與A6 acceptance accounting；不得成為stable core prerequisites。 |

**A1未授權且被本次architecture conflict阻斷。** 解決衝突後，最小候選先做 lifecycle/read-only status/doctor wrapper：重用foreground launcher/preload/client，明確 alive/identity/route/SDK各層狀態、effective paths/config與停止所有權。
補少量missing operational events，沿用existing canonical IDs/reference；不改Request/Result/Audit或authorization/execute-once。
先定義 acceptance：無market startup、doctor不建DB、不kill非owned process、bounded cleanup、arbitrary cwd/root、protocol stdout乾淨。此處只提案，未實作。

## 10. Actual bounded checks and limits

| Check actually run | Outcome |
|---|---|
| Git identity / status / local refs / worktree metadata | expected worktree/branch/HEAD；起始clean；HEAD=local origin/main。 |
| `python -B scripts/verify_environment.py` | exit 0，PASS；本機Python3.13.7、mcp1.29.0；只作本次觀察，不是developer machine-specific acceptance prerequisite。 |
| `python -B scripts/run_unified_workbench.py --startup-check` | exit 0，not_initialized；schema/catalog loaded；network_on_startup=false。 |
| `python -B scripts/manage_security_master.py status` | exit 0，NOT_INITIALIZED；未update/init/rollback。 |
| `python -B -m pytest -p no:cacheprovider tests/unit/test_m8r_08b_mcp_tool_contracts.py tests/unit/test_m8r_08b_mcp_error_mapping.py tests/unit/test_m8r_07b_local_service_contract.py -q` | 30 passed /31.82s。 |
| `python -B -m pytest -p no:cacheprovider tests/integration/test_unified_workbench_api.py::test_mode_a_workbench_routes_and_health -q` | 1 passed /2.20s；in-process TestClient/static/health。 |
| real stdio loopback integration `tests/integration/test_m8r_08b_mcp_stdio_local_service.py`，同上述pytest flags；`PYTHONDONTWRITEBYTECODE=1` | 1 passed /8.20s；random loopback mock HTTP、SDK stdio child；context shutdown/join/server_close及stdio cleanup；mock fetch不是source acquisition。 |
| Conflict discovery | 修復前offline A6 import | expected nonzero `ModuleNotFoundError: fcntl`；保留為原始blocker證據，沒有市場連線。 |
| R1 Windows Native import | 三個指定 current modules，各自以 `python -B -c "import ..."` 載入；檢查A6不在 `sys.modules` | 三條 exit 0；未設A6 ENV/session。 |
| R2 A6 dependency guard | `test_current_h2_h3_production_files_do_not_import_a6_acceptance_transport` | focused regression PASS；只檢查三個 current product files。 |
| R3 H3 deterministic transport | H3 adapter與walker unit tests | exact target/month、bounded read、normalization、source failure、no retry PASS；mock-only。 |
| R4 H2 deterministic transport | H2 executor unit tests | H3 dependency、H2 evidence materialization、typed source failure PASS；無A6 context/ENV，mock-only。 |
| R5 route/capability/MCP invariants | catalog、routing matrix、executor metadata、MCP tool contracts | H2/H3 active routes不變；四份 authority hash等於starting HEAD；六工具contract tests PASS。 |
| R6 focused current regression | H2/H3, activation, V3 contract, local service, MCP, portability tests及I3 historical normalizer tests | 190 passed /53.86s。 |
| Six-tool stdio integration | `tests/integration/test_m8r_08b_mcp_stdio_local_service.py` with mock loopback service | 1 passed /12.41s；六工具 exact list與stdout/stderr protocol separation驗證通過。 |
| R7 no market acquisition | 此 tranche command/test record | market/source acquisition = 0；無SM/Watchlist/authorization mutation。 |

未跑 full default-ci；未跑Windows terminal-close/occupied-port/real source execution；不把historical clean-room evidence當作本次fresh-machine PASS。這些限制不阻礙本次source inventory與指定A0R acceptance。
Final source/test diff的 `git diff --check` exit 0；inventory亦經UTF-8/trailing-whitespace檢查PASS。
`git status --short --untracked-files=all` 為五個tracked source/helper修改、一個tracked test修改、inventory及一個test新增；未改catalog/routing/metadata/MCP contracts。
`data/`、`.pytest_cache`、`artifacts/m8r_06_03_workbench` 均不存在；本次launcher process count=0；HEAD/branch未變。

## 11. Explicit non-goals / stopping boundary

未實作CLI/refactor/logging framework、L1-A1或L2-L7；未修改six tools/contracts/evidence families/capabilities/authorization。
無market/source acquisition、production SM/Watchlist mutation、single-use authorization消耗；無Docker/migration/backup/replay implementation。
無新長時間daemon、host/tunnel requirement、commit/push/PR/merge。只建立本文件。
A0R修復及回歸解除原Architecture conflict；A0 inventory完成並標記 `L1_A0_RUNTIME_OPERABILITY_INVENTORY_COMPLETE`。停在A0，不開始L1-A1。
