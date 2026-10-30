# S5 Integrated Recertification Report

## Disposition

`BLOCKED_BY_RELEASE_RECERTIFICATION`。這是 S5 再認證與停止交接紀錄，不是 Owner acceptance。`POST_V1_5_STABILIZATION_NOT_CLOSED`。兩個目前 release-blocking failure 未獲既有 runner 的歷史豁免；不修復、不擴大 diagnostic allowlist、不 repin release authority。

Date: 2026-10-30 (Asia/Taipei). Evidence: `C:/twmarket_temp/s5-20261030/`；全部保留、不清理。Owner 的本次 S5 附件是範圍授權；較早 root next-work prose 不是拒絕此授權的依據，也不是新階段授權。

## 1. Baseline

變更前獨立核對：branch main；HEAD = origin/main = `766c2b3973bae806bd68f3d27ed0f16718636cb7`；working tree clean；staged 0；ahead/behind 0/0。origin/main 為本地 tracking ref，未 fetch。Rollback reference 為此 HEAD，只適用 S5 candidate；未 reset、rollback 或刪除。

已依序閱讀 PROJECT、HANDOFF、ROADMAP、AGENTS、docs/INDEX，再閱讀 S1/S2/S3-R1/S4-R1 紀錄與實際 machine/runtime authority。Owner 指定 S1 `13dc831f`、S3/R1 through `581928b0`、S2 `c77b6d01`、S4/R1 `766c2b39` 為已完成 merged baseline。舊 implementation record 中當時的 blocked/review-pending 文字保留歷史意義，不改寫成新的 acceptance。

## 2. Integrated authority matrix

下表是證據導航，不建立新權威。變更前版本完整保存在 `authority-matrix.md`；變更前全部 5401 tracked paths 的 bytes hash 在 `tracked-before.json`。

| Area | Canonical authority | Derived authority | Validator/test | Immutable anchor | Known debt | Current status |
|---|---|---|---|---|---|---|
| A V3 | schemas/unified_market_evidence_*.v3.schema.json; validate_phase_h_v3_contracts.py | service preferred V3 | test_current_v3_validation_authority | frozen v1.5 schema; historical J-B04-A3 context | historical diagnostic distinct from current | PASS / unchanged; bounded evidence described below |
| B test governance | config/test_governance_authority.json; test_execution_profiles.json | profile runner | validate_current_test_governance; validate_test_governance_tg5 | TG2/TG4/TG5 hashes | 12 known diagnostics | PASS / unchanged; bounded evidence described below |
| C merge | config/current_test_coverage_floor.v1.json; run_current_merge_gate.py | merge verdict | test_current_test_governance | exact floor IDs and digest | observation stability needs 2 runs | PASS assertions: verify attempt files / same candidate |
| D onboarding | docs/operator/QUICK_START.md; verify_environment.py | README/operator references | test_source_onboarding_first_run | accepted S2 commit c77b6d0 | dependencies preinstalled, no fresh-machine claim | PASS / unchanged; bounded evidence described below |
| E installation | scripts/tw_market_installation.py; tw_market_lifecycle.py | launcher status | test_tw_market_lifecycle; test_l6_a2_lifecycle_integration | baseline source bytes | no dependency reinstall | PASS / unchanged; bounded evidence described below |
| F identity | installation-local Security Master; unified_mode_a.py | service identity status | S2 first-run; lifecycle tests | ISIN and explicit activation | fresh NOT_INITIALIZED is valid | PASS / unchanged; bounded evidence described below |
| G service | server/services/unified_local_service.py; server/main.py | HTTP API | S2 first-run; test_unified_workbench_api | canonical request/result and loopback boundary | no new provider execution | PASS / unchanged; bounded evidence described below |
| H Workbench | frontend/unified-workbench; unified_workbench_router.py | local UI | S2 first-run; API tests | existing service-backed contract | browser E2E forbidden in S5 | PASS / unchanged; bounded evidence described below |
| I MCP | server/unified_mcp/tool_contracts.py; server.py; local_service_client.py | MCP describe | test_m8r_08b_mcp_tool_contracts; S2 | exactly six tools | not independent runtime | PASS / unchanged; bounded evidence described below |
| J Catalog | docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json | describe/portable | test_s4_catalog_mcp_current_truth | committed S4 bytes | session metadata semantic distinction | PASS / unchanged; bounded evidence described below |
| K Route | docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json | planner | test_m8r_06_03_route_aware_registry | entire route-before.json | no expansion | PASS / unchanged; bounded evidence described below |
| L registry | config/m8r_06_03_executor_registry_metadata.json; scripts/m8r_06_03_production_adapter.py | runtime registrations | route-aware registry tests | IDs/mappings/callables/activation snapshot | no activation | PASS / unchanged; bounded evidence described below |
| M publication | committed Catalog and Route; generate_portable_catalog.py | portable JSON; quick guide; MCP_REFERENCE | portable/runtime-guide/L5 validators | committed lineage; CRLF byte contract | no regeneration unless real mismatch | PASS after one lineage correction |
| N historical | pinned contracts, TG ledgers, compatibility projections | diagnostic profile | historical-milestone-replay; test_l5_a4_r1_compatibility_projection | historical hashes and Git objects | whole-profile canonical context to determine | PRESERVED; diagnostic 4 red; canonical context found |
| O release | v1.5.0 tag; config/release_blocking_ci.v1.json | deterministic release runner | release-blocking-ci | acaf726a commit / d44f66dc tree | remote assets not fetched under no-network scope | BLOCKED: 2 release failures |
| P P1 | frozen P1-A1/A2; P1-A3-R2/R5 records and launcher | Windows launcher | test_p1_a3_windows_launcher | commit 3059531; frozen records | no reopening or GUI rerun | PASS / unchanged; bounded evidence described below |

## 3. S1 V3 recertification

`python -B scripts/validate_phase_h_v3_contracts.py` PASS；`test_current_v3_validation_authority.py` 全部 18 tests PASS。Result V3 SHA-256 `700e13779757300699e6cf4dd2c81768dbd56eb853befc9f9cf218102b6a7b3a` 與 frozen v1.5.0 Git blob raw bytes 相等。V1/V2 guards 保留；J-B04-A3 舊 fingerprint 屬其 historical Git context。未 repin schema fingerprint，未修改 schema。

## 4. S3 test-governance recertification

`validate_current_test_governance.py`、`validate_test_governance_tg5.py` PASS。精確 roles 未改：merge=current-merge-gate；ci=default-ci；broad_current=full-current；release_blocking=release-blocking-ci；release_preflight=release-preflight-current；historical=historical-milestone-replay；mixed_historical=mixed-historical-diagnostic；rollback=pre-tg5-default-ci。TG2/TG4/TG5/rollback/gap manifests 未改。

## 5. S2 source-onboarding recertification

`tests/integration/test_source_onboarding_first_run.py`: 3 passed。現有測試以 fresh isolated application state、offline init、READY installation / NOT_INITIALIZED Security Master、loopback Local Service、Workbench、MCP startup-check、identity-dependent fail-closed、子程序 audit/fence 與 clean teardown 驗證，未繼承實際使用者狀態、未外連。

`verify_environment.py` PASS：Windows 11、Python 3.13.7、mcp 1.29.0，現有 dependencies 可用。這不是 fresh-machine dependency installation；未 reinstall 或下載 dependencies。

## 6. S4 Catalog/MCP recertification

S4 current truth 11 tests PASS；L5-A4-R1 exact compatibility projection 46 tests PASS。H1=bounded TPEx attention/disposition + source-native cmode / zero canonical cmode coverage；H2=TWSE TWT48U_ALL bounded preannouncement，需 successful same-target H3；H3=bounded TWSE，TPEx blocked；H4=derived / zero additional network / 非獨立 request capability；session_status=modelled / Route blocked。

所有 production/runtime/source/Route 內容不變。S4 在 release current-equivalent test 的整合相容性仍有阻擋，詳第 17 節；這不是推翻已接受 S4 summary 內容，也不把未同步的 release authority 宣告正常。

## 7. session_status adjudication

`SEMANTICALLY_CONSISTENT_NON_EXECUTABLE`。

Catalog `support_status=runtime_executable` 與 Route `capability_status_source` 表示 runtime-compatible 語意標記，不等於已選取、可達的 Unified executor。Route 同時明載 `blocked`、`selected_executor_id=null`、完整 closure evidence 尚未由 approved executor 綁定；runtime registration=0。既有 Catalog schema enum 不保證 activation，schemas 中未發現獨立 Route schema；不為填表新增 schema。

Planner `scripts/m8r_05b_01/planner.py:129-136` 在計算 eligibility 前先擋 required blocked route／省略 optional blocked route；resolved、語意支援、非 provisional 與有效 executor 才能繼續。Local Service 投影 blocked/provisional 且 production_executor_available=false。MCP server 六個 action 均委派 UnifiedLocalServiceClient，沒有另一個 hidden execution stack。

出版邏輯 `generate_portable_catalog.py:78-83` 的條件確為 Catalog runtime-compatible AND Route runtime_executable=true AND routing_status=resolved AND selected_executor exists AND not provisional。不是只看一個 true flag；也不宣稱每個 planner 的內部 predicate 都與 publication 完全相同。`network_required=true` 描述完整證據取得需求，不代表已發出請求。

完整 inputs 在 `session-status-evidence.json`，read-oriented 判定在 `session-status-adjudication.md`。未修改 Route。

## 8. Route invariance

`ROUTE_FUNCTIONAL_VIEW_CHANGED = NO`；`ROUTE_CHANGED = NO`。完整 JSON before/after equality（比 functional view 更強）；無新 route、selected executor、市場啟用、blocked→resolved、network/source policy 變動。

## 9. Executor registry invariance

`EXECUTOR_REGISTRY_CHANGED = NO`。17 registrations / 9 distinct executor IDs；IDs、capability/market mappings、security types、metadata、adapter/batch callable module+qualname、network/activation 狀態 before/after 相同。保存 metadata/source bytes hashes，沒有呼叫 provider。

## 10. MCP tool-surface invariance

完整六工具 contracts before/after 相同：market_describe_capabilities、market_export_ai_handoff、market_fetch_evidence、market_preview_request、market_read_result、market_validate_request。Tool names/count/schema 均未變。

## 11. Portable/publication validation

初次三個 validator 確實失敗，原始 `.log` 全部保留：portable deep equality、runtime skill guide sync、L5 `A4_PORTABLE_LINEAGE_DRIFT`。原因只有 portable metadata `generated_from_commit` 還是合併前 `2ea228fa43b82f8d8abc5d8b178ea9c56e3e2fd6`；目前 canonical Catalog 的 Git lineage 是 `766c2b3973bae806bd68f3d27ed0f16718636cb7`。

依 Owner 附件第 18 節「validation proves a real mismatch / inspect exact diff first」的條件授權，先在外部生成 expected output 並保留精確 diff，再只替換這一個 metadata 字串。Canonical content SHA `b78d85c7e0b7f4c4089e5aaa5c979914b4b55740a7063800676e939a1ce621b8`、blob `774facc2051f6b13d39d368a69907dfb52d4ac79`、所有 capability 內容、generator 與檔尾 bytes 均保留。沒有整批 refresh；Quick Guide 的 expected diff 為空，未改。

更正後三個 validators 均 PASS：`portable-corrected.log`、`guide-corrected.log`、`publication-corrected.log`。兩個指定 artifacts 的 bare LF=0、bare CR=0，CRLF contract 保留。此修正是 bounded derived-lineage candidate，尚未獨立接受／提交。

## 12. Frozen v1.5 authority

本地 tag v1.5.0 commit=`acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`；tree=`d44f66dc154c21326ac8b105d2f15fd793f6071b`。Phase L CLOSED，Phase M NOT_AUTHORIZED。Tag、frozen records、release contract、release source 未修改；未連線重新下載／核驗 GitHub 六個 assets，未宣稱有當次 remote asset audit。沒有 release、Registry 或 Docker publication。

Release contract SHA-256 保持 `b80476b43307d670a5a3000e84e84c3b617085db6c68373fc9b522c92708d2e7`。

## 13. P1 preservation

P1-A1/A2 frozen records、P1-A3/R1/R2/R5 evidence 與 launcher bytes 未改。Focused P1 launcher/lifecycle/package integration 保護通過；未重開 P1，也未跑 Sandbox GUI/browser acceptance 或 launcher redesign。

## 14. Historical authority preservation

所有原有歷史／治理檔案 bytes 不變。TG2 semantic manifest、TG4/TG5 ledgers、rollback/replay-gap contracts、Phase I/J acceptance 與 historical tests 保留。初始 whole tracked snapshot 與 final audit 提供 byte-level containment；不得以 current-tree red 改寫其歷史 gate truth。

## 15. Historical-milestone current-tree diagnostic

Exit 1：collected=94、selected=94、passed=90、failed=4、skipped=0、deselected=0。原 runner 對 absent zero skipped field 輸出 null；零 skip 由 pytest summary 交叉確認，沒有更改 runner parser。

- `tests/unit/test_m7f_rich_fact_browser_final_acceptance.py::test_default_ci_includes_final_acceptance_tests`
- `tests/unit/test_m8_00_final_acceptance.py::test_default_ci_includes_m8_final_acceptance_test`
- `tests/unit/test_m8a_final_acceptance.py::test_readme_static_contracts_and_registry_roles`
- `tests/unit/test_m8_through_m8b_consolidated_acceptance.py::test_docs_and_boundaries`

## 16. Historical execution-context determination

`CANONICAL_HISTORICAL_REPLAY_CONTEXT_FOUND`。

TG5_ACCEPTANCE_LEDGER_2026-09-23.json 的 rollback 明載 authoritative_baseline_commit=`2ff9707d901f40c1a108dd1317fce2f03cc79735`、baseline_historical_selected_nodes=94、baseline_historical_status=PASS。獨立 Git object 檢查證實該 commit 的 `tg2-historical-acceptance-shadow` 與目前 historical-milestone-replay 的 pytest_paths、pytest_expression 完全相同；TG6-C 記錄其改名對應。

沒有執行該歷史 context，沒有宣稱重現其當時 PASS，也未建立歷史 detached checkout。只用 Git objects 判定 context 即足夠；證據 `historical-context.json`。Frozen integrity 另由 pinned ledgers/hashes、exact compatibility projections 與 current-equivalent tests 保護；但本次有一項 release current-equivalent FAIL，不掩蓋它。

## 17. Release-blocking recertification

Attempt 1：由 canonical D 槽 checkout 指向 C 槽 output，exit 1；原 runner 在 pytest collection 前拒絕 `CI output must be under the isolated workspace parent`。這是 invocation boundary failure，沒有 selection/member/guard result。保留 `release-blocking-ci.log`，不以後來結果覆寫它。

Attempt 2：新的本機 `--local --no-hardlinks` independent clone 位於 `release-workspace/repo`（無 borrowed alternates）；逐一複製、比對當前 5401 tracked 檔案，copy mismatches=0，包含 portable metadata correction。未拷貝 ignored user state。以原 runner 執行：

```text
python -B scripts/run_test_profile.py release-blocking-ci --json
  --output-root C:/twmarket_temp/s5-20261030/release-workspace/gate
```

結果 FAIL、return code=1：selected=1930、passed=1924、failed=2、errors=0、skipped=4；authoritative historical exclusions=15；全部 deselected=20（另 5 個 marker 排除）。guard_events=415、guard_denials=[]、unexpected_skips=[]。完整 members、JUnit、guard log、result 都保留。

真正阻擋的 exact IDs：

- `tests/unit/test_phase_l_l4_a5_dependency_supply_chain.py::test_active_install_guidance_allowlist_uses_locked_core`
- `tests/unit/test_l7_a1_deterministic_ci.py::test_current_public_authorities_match_accepted_entry`

第一項仍要求 README.md / README.zh-TW.md 直接出現 requirements-lock.txt；S2 現行 README 委派 Quick Start，而 Quick Start / Troubleshooting / runbook 仍有 lock authority。第二項將目前 Catalog 與 release anchor `405bf16f5f82f4d37062d036ca6815eba27f7c4d` 做 strict equality；差異恰為 S4 接受的三個 descriptions/limitations 值（詳 `release-blocker-adjudication.json`）。

兩個 IDs 都不在 authoritative runner 的 historical_diagnostics 內，也不在 default/full-current path enrollment。**均為 BLOCKING_CURRENT_AUTHORITY_DEFECT，不能因看似相容性債務而豁免。** 未修改 release contract、anchor、test、assertion 或 skip。沒有以重試把真正 release FAIL 換成 PASS；沒有再次執行有效 release gate。需要新的 Owner-bound repair scope 與後續獨立 review。

## 18. Focused recertification tests

12 paths、collected=224：223 passed、1 authorized historical witness skipped、0 failed，exit 0。S2=3、S4=11、S4 compatibility=46；包括 current V3/governance/TG5、route-aware registry、MCP contract、P1 launcher、lifecycle、Local Service/Workbench API。Exact command 在 execution-summary.json，完整輸出 focused.log。

唯一 skip：`tests/integration/test_unified_workbench_api.py::test_real_sealed_candidate_is_not_a_production_fallback`，reason=`governed local candidate is Git-ignored`，為原 release optional witness，未新增 skip/xfail。

Focused 開始於初始驗證之後；portable 單行更正是在 relevant S4/publication tests 執行前完成，沒有 test/code/config mutation；最後兩個 gates 另完整執行固定 final candidate。

## 19. Required validators

六個 required current validators 最終全部 PASS。前三項初次即 PASS；三個 publication validators 初次 FAIL→最小 lineage correction 後 PASS，保留兩階段結果，不聲稱 baseline 原本全綠。`compileall` exit 0（pycache_prefix 在 evidence root 外置 cache，未改 production source）；`git -c core.whitespace=cr-at-eol diff --check` PASS。

## 20. Raw default-ci

Exit 1；collected=1386、selected=1381、passed=1365、failed=12、skipped=4、deselected=5。Failed set 與原 12 known diagnostics 完全相同，無新增 current failure；IDs 見第 25 節。完整原 runner JSON 保存在 `default-ci.log`。

## 21. Raw full-current

Exit 1；collected=1759、selected=1754、passed=1738、failed=12、skipped=4、deselected=5。Failed set 與原 12 known diagnostics 完全相同，無新增 current failure；IDs 見第 25 節。完整原 runner JSON 保存在 `full-current.log`。

## 22. Merge-gate stability

以下為 final-candidate 預先寫定的驗證斷言；只在 named result/log 與 manifest 實際滿足時才可作為結果引用。失敗不得刪除／覆寫，也不得在 handoff 宣稱此表成立。

| Attempt | HEAD / candidate bytes | Result assertion | blocking | diagnostics | coverage | harness error |
|---|---|---|---:|---:|---|---|
| 1 | 766c2b39 / candidate-before-merge.json | PASS | 0 | 12 | PASS / missing=[] | none |
| 2 | 相同完整 manifest | PASS | 0 | 12 | PASS / missing=[] | none |

Evidence: `merge-attempt-1.json/.log`, `merge-attempt-2.json/.log`, `merge-attempt-history.json`。兩次均須 known_diagnostic_now_passing=[]、missing_required_nodes=[]、exit 0，且 before/after candidate digest 相同。

`CONSECUTIVE_MERGE_GATE_PASSES = 2` 是本表待外部結果核實的斷言；final-audit.json / handoff 必須引用實際結果。兩次之間與之後均不修改本 candidate；若斷言不成立即維持 blocked 並如實揭露，不編造 PASS。

這些 current merge PASS 不會凌駕第 17 節 release FAIL，也不形成 S5 closure。Candidate manifest 定義為所有 tracked source bytes 加本紀錄；不把 ignored pytest cache 當成 code candidate。每次都保留獨立 result/log；若有失敗必須保留並重設 consecutive count。

## 23. Production mutation

```text
PRODUCTION_RUNTIME_CHANGED = NO
SCHEMA_CHANGED = NO
ROUTE_CHANGED = NO
ROUTE_FUNCTIONAL_VIEW_CHANGED = NO
EXECUTOR_REGISTRY_CHANGED = NO
MCP_TOOL_CONTRACT_CHANGED = NO
SOURCE_ACTIVATION_CHANGED = NO
NETWORK_POLICY_CHANGED = NO
```

## 24. Current coverage floor

default-ci=123 paths / 1381 nodes；full-current=170 paths / 1754 nodes。removed governed paths=0；removed governed nodes=0。未新增 test、validator、floor、snapshot authority 或 governance enrollment。既有 validators 已抓到 lineage 問題；release 也已抓到 cross-authority 缺口，修復需另授權，不為 closure 新造一個 waiver layer。

## 25. Known diagnostics

default/full-current failed IDs 與原 floor 的 12 known diagnostics exact set equality；未新增或擴大分類，未使用 wildcard。完整 exact IDs：

- `tests/unit/test_phase_i_i3_a0_preflight.py::test_current_hold_record_and_runtime_containment`
- `tests/unit/test_phase_i_i3_a0_preflight.py::test_p0_validator_cannot_claim_pass_or_rearm`
- `tests/unit/test_phase_i_i3_a0_p1_adjudication.py::test_p1_governance_validator_passes_under_network_denial`
- `tests/unit/test_phase_i_i3_a0_p3.py::test_p3_validator_production_containment_and_readiness`
- `tests/unit/test_phase_i_i3_a0_p3_r1.py::test_r1_validator`
- `tests/unit/test_phase_i_i3_a1.py::test_a1_validator_and_immutable_a0_anchors`
- `tests/unit/test_phase_i_i3_a3_attempt_2_bounded_live.py::test_exact_mapping_and_frozen_candidate_and_production_containment`
- `tests/unit/test_phase_i_i3_a3_r3_http520_lifecycle.py::test_committed_attempt4_pass_lineage_and_containment`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_current_record`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_unchecked_g_h_do_not_themselves_block_pass`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-08]`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-10]`

所有 4 optional historical skips 由原 runner/floor 模型處理；沒有新增 skip/xfail。Release 的兩個新失敗不加入上述清單。

## 26. Remaining debt

| Item | Classification | Treatment |
|---|---|---|
| README/S2 lock-reference 與原 release current assertion 不相容 | BLOCKING_CURRENT_AUTHORITY_DEFECT | S5 blocker；保留測試及 release contract，不自行修 |
| S4 三值修正與 release accepted-entry equality 未整合 | BLOCKING_CURRENT_AUTHORITY_DEFECT | S5 blocker；不可改成 historical diagnostic |
| session_status semantic flag 命名清晰度 | ACCEPTED_NON_BLOCKING_DEBT | 語意／可達性已區分，全部 execution paths fail closed，Route 不改 |
| current-tree historical red | ACCEPTED_NON_BLOCKING_DEBT | 4 failures 如實列示，不重寫 historical tests |
| fresh dependency-environment / fresh-machine reproducibility | POST_STABILIZATION_FOLLOWUP | 未執行、未宣稱；現有 dependencies verifier PASS |
| root frontdoor 的較早 P1 / deferred-summary stopping prose | POST_STABILIZATION_FOLLOWUP | 本次 explicit scope 與 accepted S1–S4 chain 優先；不藉 S5 擴大 root mutation |
| merge observation stability | ACCEPTED_NON_BLOCKING_DEBT | 需要兩次完整 consecutive PASS 的具體證據；不把它升格成長期零 flaky 保證 |
| portable committed lineage mismatch | POST_STABILIZATION_FOLLOWUP | 一行修正 candidate 已通過既有 validators，尚待 review/acceptance |

## 27. Files changed

- `skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json`：只改 generated_from_commit 一值，Owner §18 mismatch exception。
- 本 S5 governance record：新檔。

其餘 tracked bytes 不變；docs/governance/INDEX.md 無需新增導航。沒有 production/test/schema/config 修改。

## 28. Stabilization closure decision

```text
POST_V1_5_STABILIZATION_NOT_CLOSED
POST_V1_5_CURRENT_AUTHORITY_STABILIZATION = NOT_CLOSED
```

阻擋原因是有效、未豁免的 release recertification FAIL；current merge stability 與 release acceptance 是不同 authority，不能互相替代。

This closure does NOT authorize P2–P5.
This closure does NOT authorize Phase M.
This closure does NOT modify the frozen v1.5.0 release.
This closure does NOT claim all historical tests pass in the current source tree.
This closure does NOT claim fresh-machine dependency installation verification.

以上限制適用於此未結案紀錄；不存在成功 closure 宣告。

## 29. Authorization boundary after S5

P2–P5 = NOT_AUTHORIZED；Phase M = NOT_AUTHORIZED。沒有 new capability、route/source/executor activation、scheduler、polling、external acquisition、browser E2E、Security Master acquisition。只有現有 deterministic loopback tests。COMMIT / PUSH / PR / DELETE 均未授權、未執行；證據與隔離 clone 保留。

## 30. Git state

branch=main；HEAD=origin/main=`766c2b3973bae806bd68f3d27ed0f16718636cb7`；staged=0；unstaged tracked=1；untracked candidate=1；ahead/behind=0/0。Final audit 記錄 precise status、candidate digest、route/registry/tool equality、CRLF 與 changed-file containment。沒有 commit/push/PR。

## 31. ChatGPT review handoff

1. 優先重看 release result/JUnit/members：兩個 FAIL 都不在原 historical exclusions，不能以 default/current merge PASS 取代；確認 5401 tracked bytes 的隔離來源 equality。
2. 直接核對 public-authority anchor 與現在 Catalog 僅三值差異，及 S2 README 委派 lock authority 的改變。判斷下一個獨立授權的最小修復範圍；S5 未自行修復。
3. 核對 portable generated_from_commit 一行修正的 §18 授權、Git lineage、內容/blob SHA 與 CRLF bytes；保留原失敗及更正後 validators。
4. 獨立檢查 session_status 的 schema/Route/planner/publication/MCP 邏輯；不要只依本紀錄的分類。
5. 檢查兩個 merge result 原始完整 observation coverage、12 exact diagnostics、now-passing=[]、候選完整 bytes hash 相同，以及所有 attempt 均保留。
6. 確認 TG5 歷史 context 的明確 baseline 與舊 profile selection equality；這不是執行過歷史 replay 的宣稱。
7. 確認 release/P1/歷史/production bytes 不變、只有上述兩個 candidate files、staged=0、HEAD/refs 未移動；S5 維持 NOT_CLOSED。

External evidence index: `execution-summary.json`, `profile-summaries.json`, `focused.log`, six validator logs plus corrected publication logs, `release-summary.json`, `release-isolated.json`, `release-failure-details.json`, `release-blocker-adjudication.json`, `release-source-copy.json`, `historical-context.json`, `session-status-evidence.json`, `session-status-adjudication.md`, `route-before.json`, `registry-before.json`, `tools-before.json`, `byte-contracts.json`, `candidate-before-merge.json`, merge attempt files, `final-audit.json`, `evidence-hashes.json`. These are retained verification evidence, not new runtime or acceptance authority.

---

# S5-R1 Implementation Report

## Disposition

`READY_WITH_NOTES` — bounded implementation / recertification candidate for independent ChatGPT review, not an independent review or commit authorization. The closure assertion below applies only once the named final-candidate gate artifacts and `final-audit.json` substantiate it. This appendix is frozen before the two new merge executions so documentation bytes are included in their identical candidate manifests.

**Initial S5 disposition remains `BLOCKED_BY_RELEASE_RECERTIFICATION`.** The entire preceding S5 record is preserved byte for byte, including the original two release blockers, failed release evidence and NOT_CLOSED decision. Sequence: S5 integrated recertification → release FAIL → NOT CLOSED → Owner-authorized S5-R1 exact compatibility correction → recertification. No S1–S4 tranche is reopened.

Date: 2026-10-30 (Asia/Taipei). S5-R1 evidence root: `C:/twmarket_temp/s5-r1-20261030/`; original evidence root `C:/twmarket_temp/s5-20261030/` remains untouched. All evidence and isolated source copies are preserved.

## R1.1. Baseline / candidate containment

Before R1 mutation independently verified main; HEAD=origin/main=`766c2b3973bae806bd68f3d27ed0f16718636cb7`; staged=0; ahead/behind=0/0. Existing S5 candidate was exactly one tracked portable lineage correction plus this untracked governance record. Saved original record bytes in `original-s5-blocked-prefix.md`, both original test files, starting byte manifest of all 5401 tracked files plus the S5 record, and Git baseline state.

Allowed R1 mutation: assertions in the two specified test files and this appendix only. Original portable S5 correction is preserved without further byte mutation. Rollback reference is the saved R1 starting bytes / HEAD; no rollback/reset/delete executed. No new test paths, nodes, validators or config changes. Final four-file candidate is enumerated in R1.24.

## R1.2. Original two release blockers

- `tests/unit/test_phase_l_l4_a5_dependency_supply_chain.py::test_active_install_guidance_allowlist_uses_locked_core`
- `tests/unit/test_l7_a1_deterministic_ci.py::test_current_public_authorities_match_accepted_entry`

Neither ID is added to diagnostics or skips; both execute as release-blocking tests. The original S5 FAIL result is not overwritten or retrospectively reclassified.

## R1.3. S2 documentation-topology root cause

Independent review root cause accepted by this Owner task: stale release assertion after accepted S2 documentation authority evolution. Quick Start is PRIMARY_ONBOARDING_AUTHORITY; README.md / README.zh-TW.md are SECONDARY_REFERENCE. They already link exactly to `docs/operator/QUICK_START.md#source-first-run`. Direct install/remediation lives in Quick Start, Troubleshooting and developer onboarding runbook, each explicitly containing requirements-lock.txt. LOCAL_WORKBENCH contains a delegated Quick Start link and does not directly prescribe dependency installation, so it remains covered by the all-ACTIVE_DOCS unlocked-command ban without inventing a direct-install role.

This is documentation topology, not unlocked dependency usage. README, primary docs and S2 accepted procedures were not edited or reverted.

## R1.4. S2 release assertion correction

`test_active_install_guidance_allowlist_uses_locked_core` keeps the original loop over **all six ACTIVE_DOCS** rejecting literal `pip install -r requirements.txt` unchanged. It then requires lock authority in exactly the three current direct installation/remediation docs:

- docs/operator/QUICK_START.md
- docs/operator/TROUBLESHOOTING.md
- docs/runbooks/DEVELOPER_ONBOARDING_LOCAL_FIRST.md

Both README frontdoors must instead contain the actual Markdown destination `](docs/operator/QUICK_START.md#source-first-run)`. This does not accept an arbitrary mention of Quick Start or require duplicated procedures. No README edits.

Existing complete-file checks remain: exact MCP pin in direct+lock authorities, direct lock coverage, browser lock inheritance and exact browser pin, PEP 508 validity, URL/VCS/editable/custom-index rejection, operator lock remediation and no package installer in active runtime. No dependency policy or requirement files changed.

## R1.5. S4 public-authority root cause

The old release current-equivalent assertion strictly compared the current four public authorities to anchor `405bf16f5f82f4d37062d036ca6815eba27f7c4d`. S5 independently showed only the exact accepted S4 three Catalog leaves differed; Routing, executor metadata and I2 source authority were equal. This Owner task authorizes recognizing that exact later descriptive delta while keeping historical release authority intact.

## R1.6. Exact S4 release compatibility projection

`assert_current_authorities` now loads the unchanged accepted_authorities(), applies existing `project_s4_catalog(relative, document, accepted[relative])` to each current authority, then performs **strict projected == accepted equality** with the original drift error. No fields, documents or keys are filtered out. No string triples are duplicated in this file. `scripts/s4_catalog_compat.py` is byte unchanged.

The helper validates exact historical predecessor and exact current successor/cardinality/positions, deep-copies Catalog and restores only the three authorized leaves. Non-Catalog documents remain unchanged. Unrelated Catalog drift remains present and must fail final equality.

The existing four-surface parameterized mutation test passes unchanged. Existing S4 compatibility tests cover exact predecessor/successor rejection. Additional read-only evidence calls through this very release assertion accepted the exact current view and rejected four unrelated authority drifts plus all three altered S4 successors (`release-seam-negative-evidence.json`). These are external manual proofs, not new pytest paths/nodes or a new compatibility authority.

## R1.7. Release anchor preservation

```text
PUBLIC_AUTHORITY_ANCHOR_CHANGED = NO
public_authority_anchor = 405bf16f5f82f4d37062d036ca6815eba27f7c4d
```

accepted_authorities() continues reading Git objects from that exact unchanged anchor; it does not use current HEAD as an acceptance baseline.

## R1.8. Release contract preservation

```text
RELEASE_BLOCKING_CONTRACT_CHANGED = NO
```

`config/release_blocking_ci.v1.json` SHA-256 remains `b80476b43307d670a5a3000e84e84c3b617085db6c68373fc9b522c92708d2e7`. public_authority_anchor, public_authorities, historical diagnostics, four optional witnesses, network/state/timeout/failure policies all byte unchanged. No skip, xfail, wildcard or diagnostic allowance added.

## R1.9. Focused 2-blocker rerun

The first post-correction rerun used exactly:

```text
python -B -m pytest -q -o addopts= tests/unit/test_phase_l_l4_a5_dependency_supply_chain.py::test_active_install_guidance_allowlist_uses_locked_core tests/unit/test_l7_a1_deterministic_ci.py::test_current_public_authorities_match_accepted_entry
```

Result: **2 passed**, exit 0. Evidence: `focused-two-blockers.log`, `focused-two-blockers-exit.txt`. No failing R1 two-blocker attempt.

## R1.10. Focused regression suite

**133 passed, 0 failed, 0 skipped**, exit 0. Complete paths:

- tests/unit/test_phase_l_l4_a5_dependency_supply_chain.py
- tests/unit/test_l7_a1_deterministic_ci.py
- tests/integration/test_source_onboarding_first_run.py
- tests/unit/test_s4_catalog_mcp_current_truth.py
- tests/unit/test_l5_a4_r1_compatibility_projection.py
- tests/unit/test_run_test_profile.py

This covers dependency verifier, original four authority-mutation nodes, exact S4 helper compatibility, source first-run, S4 current truth and release-profile routing/deadline/boundary behavior. Source onboarding remains 3 passed; no fresh dependency installation claim. Only existing deterministic loopback tests; no browser/live execution. Exact command and duration in execution-summary.json; full log focused-regression.log.

## R1.11. Release-blocking recertification

One valid R1 release attempt in fresh `release-workspace/repo`, an independent local --no-hardlinks clone with no borrowed object alternates. Copied/compared all 5401 tracked candidate files, mismatches=0; post-run comparison also mismatches=0. Executed unchanged authoritative profile:

```text
python -B scripts/run_test_profile.py release-blocking-ci --json --output-root C:/twmarket_temp/s5-r1-20261030/release-workspace/gate
```

Outer profile status=pass; deterministic result=PASS; return code=0; selected/member count=1930; passed=1926; failed=0; errors=0; skipped=4; explicit historical exclusions=15; all deselected=20 (15 exact historical nodes plus 5 marker exclusions). Guard events=415; guard_denials=[]; unexpected_skips=[]; exact_optional_skip_set=true. Both original blocker IDs have included=true, excluded_historical=false, skipped=false, junit_passed=true in release-summary.json. All four allowed optional witness identities match the unchanged contract. Full JUnit/member/guard/result records retained.

The original S5 two blockers now execute and pass; neither is skipped/deselected. Original runner, release contract and guard are unchanged. No new network permission or inherited production state. No dependency installation. Source clone and evidence are not deleted.

## R1.12. Required validators

All six explicitly rerun with `python -B` and exited 0:

- validate_current_test_governance.py
- validate_test_governance_tg5.py
- validate_phase_h_v3_contracts.py
- validate_portable_catalog_sync.py
- validate_runtime_skill_guide_sync.py
- validate_l5_extension_publication_conformance.py

`python -X pycache_prefix=C:/twmarket_temp/s5-r1-20261030/compile-cache -B -m compileall -q scripts server tests` exits 0 with compiled output outside source. CRLF-aware `git -c core.whitespace=cr-at-eol diff --check` passes. No config or runtime edits follow these validator runs; only this governance appendix is added before the final merge pair.

## R1.13. Portable lineage / byte contract

Preserved original S5 portable bytes exactly: generated_from_commit=`766c2b3973bae806bd68f3d27ed0f16718636cb7`, canonical_sha256=`b78d85c7e0b7f4c4089e5aaa5c979914b4b55740a7063800676e939a1ce621b8`, canonical_git_blob_sha=`774facc2051f6b13d39d368a69907dfb52d4ac79`. Current canonical Catalog and Quick Guide unchanged. Both portable artifacts have bare LF=0, bare CR=0. No regeneration, newline normalization or further metadata update in R1.

## R1.14. Raw default-ci

Exit 1; collected=1386, selected=1381, passed=1365, failed=12, skipped=4, deselected=5. Exact failed set equals the existing 12 governed diagnostic IDs; no new current failure. See default-ci.log and profile-summaries.json.

## R1.15. Raw full-current

Exit 1; collected=1759, selected=1754, passed=1738, failed=12, skipped=4, deselected=5. Exact failed set equals the existing 12 governed diagnostic IDs; no new current failure. See full-current.log and profile-summaries.json.

Raw default/full remain transparently red only for the exact governed set; no failure filtering or new diagnostic enrollment. Exact current IDs:

- `tests/unit/test_phase_i_i3_a0_preflight.py::test_current_hold_record_and_runtime_containment`
- `tests/unit/test_phase_i_i3_a0_preflight.py::test_p0_validator_cannot_claim_pass_or_rearm`
- `tests/unit/test_phase_i_i3_a0_p1_adjudication.py::test_p1_governance_validator_passes_under_network_denial`
- `tests/unit/test_phase_i_i3_a0_p3.py::test_p3_validator_production_containment_and_readiness`
- `tests/unit/test_phase_i_i3_a0_p3_r1.py::test_r1_validator`
- `tests/unit/test_phase_i_i3_a1.py::test_a1_validator_and_immutable_a0_anchors`
- `tests/unit/test_phase_i_i3_a3_attempt_2_bounded_live.py::test_exact_mapping_and_frozen_candidate_and_production_containment`
- `tests/unit/test_phase_i_i3_a3_r3_http520_lifecycle.py::test_committed_attempt4_pass_lineage_and_containment`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_current_record`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_unchecked_g_h_do_not_themselves_block_pass`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-08]`
- `tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-10]`

## R1.16. Historical diagnostic

Exit 1; collected=94, selected=94, passed=90, failed=4, skipped=0, deselected=0. The raw parser emits null when a zero skipped field is absent; pytest summary independently shows no skips. Exact failures:

- `tests/unit/test_m7f_rich_fact_browser_final_acceptance.py::test_default_ci_includes_final_acceptance_tests`
- `tests/unit/test_m8_00_final_acceptance.py::test_default_ci_includes_m8_final_acceptance_test`
- `tests/unit/test_m8a_final_acceptance.py::test_readme_static_contracts_and_registry_roles`
- `tests/unit/test_m8_through_m8b_consolidated_acceptance.py::test_docs_and_boundaries`

Historical tests/ledgers are unchanged. Original S5 Git-object context finding remains valid: TG5 explicitly pins `2ff9707d901f40c1a108dd1317fce2f03cc79735`; the old historical-shadow profile matches current selection. No historical checkout/replay was executed and no old live acceptance rerun. Current-tree red is neither hidden nor substituted for release PASS.

## R1.17. Merge-gate attempt history

The prior S5 pair is historical and **does not count** for this new test-authority candidate. All R1 modifications, including this appendix, are frozen before the new pair. The following rows are predeclared verification assertions, usable as results only if the named raw artifacts and final audit actually verify them; any failure must remain preserved and resets the consecutive counter.

| R1 attempt | HEAD / candidate | Required result | blocking | known diagnostics | coverage / missing | harness error |
|---|---|---|---:|---:|---|---|
| 1 | 766c2b39 / candidate-before-merge.json | PASS / exit 0 | 0 | 12 | PASS / [] | none |
| 2 | identical complete candidate manifest | PASS / exit 0 | 0 | 12 | PASS / [] | none |

Both require known_diagnostic_now_passing=[] and missing_required_nodes=[]. Exact observations, durations and candidate hash live in `merge-attempt-history.json` and separate `merge-attempt-1.json/.log`, `merge-attempt-2.json/.log`. No result files overwrite older S5 attempts.

`CONSECUTIVE_MERGE_GATE_PASSES = 2` is verified by final-audit.json against actual executions, not inferred from the old S5 pair. Candidate includes all tracked files plus this record; ignored pytest cache is not candidate code. No code/test/document bytes may change between/after the accepted pair. If these assertions fail, this appendix must not be represented as accepted closure.

## R1.18. Coverage-floor preservation

default-ci remains 123 paths / 1381 selected nodes; full-current remains 170 paths / 1754 selected nodes. removed paths=0; removed nodes=0. Floor/config/roles/markers/diagnostic mapping are byte unchanged. The two corrected paths were already release-governed; no default/full enrollment added or removed. No test function or parameterized node was added or removed.

## R1.19. session_status adjudication

`SEMANTICALLY_CONSISTENT_NON_EXECUTABLE` retained. runtime_executable is the semantic/runtime-compatible flag; routing_status=blocked, selected_executor_id=null and zero runtime registrations prevent a currently reachable selected route. No new contrary evidence; S5 read-oriented schema/planner/publication/Local Service reasoning and current S4 tests remain applicable. Catalog and Route unchanged.

## R1.20. Route / registry / MCP invariance

```text
ROUTE_FUNCTIONAL_VIEW_CHANGED = NO
EXECUTOR_REGISTRY_CHANGED = NO
MCP_TOOL_CONTRACT_CHANGED = NO
```

Current Route JSON and original source bytes unchanged. Registry remains 17 registrations / 9 executor IDs, with same capability/market mapping, callable references, metadata and activation. Full six-tool names/schema contracts match original S5 snapshot. The same baseline source bytes were independently rechecked at R1 start; materialized exports are compared again at final audit.

## R1.21. Production mutation

```text
PRODUCTION_RUNTIME_CHANGED = NO
SCHEMA_CHANGED = NO
SOURCE_ACTIVATION_CHANGED = NO
NETWORK_POLICY_CHANGED = NO
```

No production source, source activation, executor, schema, Catalog, Routing, Workbench, Local Service, Security Master, Watchlist or MCP contract change. No seventh tool, background task, polling or network acquisition. R1 changes current release test assertions only.

## R1.22. Frozen release / historical preservation

v1.5.0 tag remains commit `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`, tree `d44f66dc154c21326ac8b105d2f15fd793f6071b`. Phase L CLOSED. No remote asset re-audit/publication, tag mutation, Registry/Docker publication or release snapshot change. TG ledgers/rollback/gap manifests and Phase I/J historical evidence remain unchanged. This current test compatibility correction does not rewrite historical acceptance.

Original S5 blocked record prefix and original portable S5 candidate are preserved, verified by starting hashes and final byte-prefix equality.

## R1.23. Remaining debt

| Item | Classification | Treatment |
|---|---|---|
| Original two release assertion incompatibilities | Corrected in S5-R1 candidate | Remain recorded as S5 blockers; no diagnostic reclassification; current focused/release PASS evidence required |
| Current-tree historical diagnostics and exact existing 12 current diagnostic mix | ACCEPTED_NON_BLOCKING_DEBT | Visible red results retained; no added waiver or historical rewrite |
| session_status naming clarity | ACCEPTED_NON_BLOCKING_DEBT | Proven non-executable route; no metadata mutation |
| Fresh-machine / clean dependency-environment reproducibility | POST_STABILIZATION_FOLLOWUP | Not performed or claimed; dependencies already available |
| Earlier root stopping-point / deferred-summary prose | POST_STABILIZATION_FOLLOWUP | Not a competing runtime authority or expanded mutation scope; explicit accepted S1–S4 and current Owner instructions govern this task |
| Previous transient merge observation issue | ACCEPTED_NON_BLOCKING_DEBT | Require two new complete fixed-byte passes; no long-term zero-flake claim |
| Independent ChatGPT review / Owner acceptance | POST_STABILIZATION_FOLLOWUP | Not performed by implementation agent; no commit authorization implied |

No remaining BLOCKING_CURRENT_AUTHORITY_DEFECT / BLOCKING_TEST_HARNESS_DEFECT may be hidden in this table if final execution evidence fails. Final handoff must report actual blocker status instead.

## R1.24. Files changed

Final candidate versus HEAD is exactly:

1. skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json — preserved original S5 one-value lineage correction.
2. tests/unit/test_phase_l_l4_a5_dependency_supply_chain.py — current S2 topology assertions only.
3. tests/unit/test_l7_a1_deterministic_ci.py — import/use exact existing S4 projector, keep strict equality.
4. This untracked governance record — original S5 prefix intact; R1 appended only.

No config, helper, source docs, release contract, production source or other historical record mutation. No new test paths/nodes. No deletion.

## R1.25. Stabilization closure

Once release PASS, all six current validators and the two new final-candidate merge assertions above are verified by `final-audit.json`:

```text
POST_V1_5_STABILIZATION_CLOSED
POST_V1_5_CURRENT_AUTHORITY_STABILIZATION = CLOSED
```

This is the implementation recertification closure candidate for ChatGPT independent review, not fabricated retroactive S5 success. The original S5 remained NOT_CLOSED at its own stopping point; only this separately authorized correction and new evidence support the later closure assertion.

This closure does NOT authorize P2–P5.
This closure does NOT authorize Phase M.
This closure does NOT modify the frozen v1.5.0 release.
This closure does NOT claim all historical tests pass in the current source tree.
This closure does NOT claim fresh-machine dependency installation verification.

## R1.26. Authorization boundary

```text
P2–P5 = NOT_AUTHORIZED
Phase M = NOT_AUTHORIZED
v1.5.0 frozen release = UNCHANGED
COMMIT = NOT_AUTHORIZED / NOT_PERFORMED
PUSH = NOT_AUTHORIZED / NOT_PERFORMED
PR = NOT_AUTHORIZED / NOT_PERFORMED
DELETE = NOT_AUTHORIZED / NOT_PERFORMED
```

No later productization, live source work, cleanup, release/Registry publication or Phase M work starts from this candidate.

## R1.27. Git state

main; HEAD=origin/main=`766c2b3973bae806bd68f3d27ed0f16718636cb7`; staged=0; unstaged tracked=3; untracked candidate=1; ahead/behind=0/0. No branch creation needed. Final Git state and exact changed-file containment in final-audit.json. No stage/commit/push/PR/reset or operator cleanup performed.

## R1.28. ChatGPT review handoff

1. Compare this record with original-s5-blocked-prefix.md; require exact prefix preservation and both original S5 blockers/FAIL/NOT_CLOSED still present. Treat S5 evidence and R1 evidence as separate sequences.
2. Inspect all ACTIVE_DOCS: unchanged unlocked-command guard over six docs; exact three direct lock authorities; both README primary-source fragment links; no README procedure duplicated.
3. Confirm unchanged accepted_authorities() anchor and helper source; verify exact validated S4 projector followed by strict equality over all four documents. Reproduce four authority mutations plus altered S4 successors; no generic prose filtering.
4. Reproduce the two targeted nodes, six complete focused files (133 passed), and authoritative isolated release PASS; verify both formerly failing nodes are included and neither is skipped/excluded.
5. Verify release contract SHA, all 15 historical exclusions and exact four optional witnesses, guard denials=[], unexpected skips=[], current raw exact-12 sets and unchanged floor identities.
6. Inspect both fresh R1 merge outputs and logs, complete candidate manifest equality including this appendix, now-passing=[], missing=[], and actual consecutive count=2. Old S5 pair is not sufficient.
7. Verify original portable bytes/CRLF, unchanged Route/registry/MCP/runtime/schema/release/historical authority, four-file containment, HEAD/tracking refs/staged=0; do not infer commit/push authorization.

Evidence index: baseline.json; starting-bytes.json; original-s5-blocked-prefix.md; focused-two-blockers.log; focused-regression.log; execution-summary.json; six validator logs; release-seam-negative-evidence.json; release-source-copy.json; release-isolated.json; release-summary.json; release-workspace/gate/release-blocking-ci/{result.json,members.json,report.xml,guard.jsonl}; profile-summaries.json; candidate-before-merge.json; merge-attempt-history.json; separate merge result/log files; final-audit.json; evidence-hashes.json. All evidence is retained outside the repository and is verification evidence, not a new runtime/selection authority.
