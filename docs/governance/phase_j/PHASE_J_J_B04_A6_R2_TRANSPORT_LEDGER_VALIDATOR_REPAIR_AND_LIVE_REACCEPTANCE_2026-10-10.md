# J-B04-A6-R2 — Transport Ledger Repair and Integrated Live Re-acceptance

**Disposition:** `J_B04_A6_R2_INTEGRATED_LIVE_REACCEPTANCE_PASS`

The network-free repair aligned reservation/completion ledger schemas and rebound the current runner to the fresh R2 authority. After Stage 1 checks passed, one fresh Local Service/MCP integrated run executed for `TWSE:2330`. Its three source dispatches were accounted for, and the runner froze network before stored-result reads.

## Authority and Stage 1

- Starting HEAD/TREE: `8a56fcd3204fa852a7444363485bfc8af264e74c` / `c3e245b8a31a600e45c3552cd90a778baff6288e`; `origin/main`: `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`.
- Owner authorization SHA-256: `a78b43ae8d251c96604820ac0e3f985eb5b92ea23d9020880ea0425cb8369252`.
- Implementation commit/TREE: `0f610dca09c34e101d8d7eb70755b0c0e0a7525d` / `0366ef3399b59a28e9ea76392024fc349b2f76ac`. The single `fix(a6):` commit is directly after the authorized base.
- The old completion event omitted `method`. The repaired validator joins by `reservation_id` and derives that one legacy value only from its matching reservation. New completions carry `method`. It rejects duplicate/orphan pairs, mismatched identity, unapproved source/URL/target, non-GET, retries, redirects, noncontiguous dispatches, and budget violations.
- The runner is now anchored to the R2 HEAD/TREE and authorization hash. It rejects the consumed A6 authority, wrong tree, unrelated commit history, and tracked modifications.
- Network-denied A6 ledger/authority tests: **22 passed**. Current H3/H2/H4, Result/Audit, Service, Workbench, MCP, and loader focused suites: **314 passed, 1 skipped**; one existing default-CI pointer-loader failure was deselected. Two additional old P1 tests still assert pre-A6 H2 inactivity; the separate P1 and P1-R1 historical validators pass and explicitly confirm current authorized A6 supersession.
- Historical A6-P0, A6-P1, A6-P1-R1, A6-R1, integrated-ledger, and terminal-evidence validators: PASS. Compileall, strict duplicate-key scan (1,057 tracked JSON files), and `git diff --check`: PASS. Stage 1 market/source calls: GET/HEAD/POST `0/0/0`; Security Master acquisition `0`.

Default-CI used clean detached Git worktrees at the exact base and candidate, CPython 3.12.14, `TZ=Etc/UTC`, `PYTHONHASHSEED=0`, the same empty Security Master root, and an external-network-denied/loopback-only guard. Both collected 1,288 tests (1,283 selected): **1,249 passed, 30 failed, 4 skipped, 5 deselected**. The exact same 30 existing failed nodes occurred on both commits; candidate-only failures: 0; new failure delta: 0. Both profile statuses remain `fail` due to that identical baseline set.

## Fresh preflight and live result

- Fresh-process preflight: PASS. Security Master release `security-master-20261010T112837Z`, manifest `e23d5a60053aec9733764adc49908b3a238d2108cd70ac6e3965d99a1e2a26bc`; `TWSE:2330` resolved by `exact_listing_id`, market TWSE, code 2330, ISIN `TW0002330008`, company/common share, execution allowed. H2 is selected only for the bounded TWSE route; H3 remains the TWSE route; MCP tools: 6. Preflight source calls: 0.
- One integrated attempt made two H3 monthly GETs and one H2 GET. Total dispatches: 3; HEAD/POST: 0/0; retries/redirects: 0/0. No Security Master acquisition, TPEx, TAIFEX, browser, fallback, trading, order, broker, or recommendation operation occurred.
- H3 returned complete evidence: 20 valid observations for the requested 20 trading days, `2026-09-08` through `2026-10-07`, with an available 21-close baseline window ending `2026-10-08`. H3 artifact SHA-256: `4efbfeb51fc550f10cebdcb09853db4bf90a2926a7e575d24ff0074e44fa6246`.
- H2 TWT48U retrieval and schema validation succeeded for the exact H3-derived window `2026-09-08` through `2026-10-08`. Exact-target search succeeded and returned zero matching events in this retrieved source slice. H2 is partial because the source does not cover all declared corporate-action subtypes; this is not a claim of historical absence. H2 artifact SHA-256: `3e70ae05bf8bf9dcefa347f923c191ceb2014aea05148203b99bc70463199c24`.
- H4 derived `coverage_incomplete` and blocked ordinary-return interpretation with `CORPORATE_ACTION_COVERAGE_INCOMPLETE`. H4 artifact SHA-256: `6f4e6874de53a2efb8f419b485e8d3780b1fac73ede98515a4f244e60cbb3bbc`.
- Result V3 and Audit V3 both validate. Result status is `full_success`; Audit verifies artifact, bundle, receipt, and result hashes. The H4 guard is visible in the AI handoff; recommendation language is absent. Local Service, `market_read_result`, `market_export_ai_handoff`, and Workbench result/audit/handoff surfaces reused the same stored execution; additional market executions: 0.
- The runner's intermediate status was `REQUIRES_SANITIZED_RESULT_REVIEW`. Exact local evidence adjudication with the repaired ledger validator establishes the R2 PASS. Network is frozen.

## Transport and binding

The local ledger `/tmp/j-b04-a6-r2/transport-ledger.jsonl` contains 3 reservations and 3 matching completions; SHA-256: `a503355bab396b729963e803b29dab194d3a6de6065c0f1a324e02d129f192ab`. Its three HTTPS GETs returned HTTP 200: October H3, 7,529 bytes (`9bf1dc0caf51a596f422e4194058616a744db5dbe85c0475d1085ec19cb63f60`); September H3, 17,932 bytes (`c21f4b19e9bdc1d6862c01e1ef037ff6c17755c468a98cfcc2ce894c9f333baa`); and H2 TWT48U, 15,728 bytes (`eaeb52d866a371f7062dd019c38aee13534f024a44fc47d24b7ec3f591533640`).

The evidence binds control package `umea-v1-55386b4d1e28bf5866ec`, claim `umecl-v1-52c7cf0e5f6856c5681c`, receipt `umerec-v1-41d3d90af8924d94c544` (hash `41d3d90af8924d94c54463230e89026a45e908b53399b5ba70a9eba314448cb2`), authorization `umea-v1-55386b4d1e28bf5866ec`, all H3/H2/H4 artifact hashes above, Result V3 hash `ec1666e600a1d90167f894a913db0d749e7a458be86d188f2995310d015cb133`, Audit V3 package hash `83200ede745933ac8b13f3080757984dfc6fa18d7a5d90c8692c105b42fba645`, and handoff SHA-256 `b4fe0800e870a5e8bbae70fa34fa7679f756f3222365c4d002cab06872d8bef1`.

Live response bodies were consumed by the production executor; it did not retain separate raw HTTP body files. Sanitized byte/hash metadata and normalized hash-bound evidence remain installation-local under `/tmp/j-b04-a6-r2/` and `artifacts/m8r_06_03_workbench/umea-v1-55386b4d1e28bf5866ec/`. No raw source payloads or Security Master runtime files are committed.

## Final state

Security Master remains ACTIVE and `TWSE:2330` remains verified. H2 remains active only for its bounded TWSE route; selected executor: `phase_h_h2_twse_exright_pre_executor`. H3 is live re-accepted. J-B04 remains blocking pending exact-head closure review; Phase J is not started; MCP remains 6. PR #326 remains open, Draft, and unmerged.
