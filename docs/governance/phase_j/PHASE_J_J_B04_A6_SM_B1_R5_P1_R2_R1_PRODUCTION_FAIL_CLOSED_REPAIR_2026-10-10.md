# J-B04-A6-SM-B1-R5-P1-R2-R1 — Production Fail-Closed Repair

Disposition: **`SM_B1_R5_P1_R2_R1_PRODUCTION_FAIL_CLOSED_REPAIR_PASS`**, ready for exact-head independent review.

The tranche started from `6bc39b5a86a6af3ac3bc726117ef62a9bed2e35f` (`0fd18c1c6f83f5919bcc87a3083d9cd64cb5534e`), with `origin/main` at `6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a`. Review `5478330630` accepted the R5-P1-R2 source qualification and required repair of two production control-flow defects and the combined regression test.

The TPEx qualification remains unchanged: one governed `POST` requests `date=ALL` with `paging-size=1000`; the captured response contained 582 of 582 rows, spanning 1992-10-27 through 2026-10-01, with no duplicate lifecycle identities. No endpoint qualification, source acquisition, or bootstrap was repeated in R1.

The implementation commit is `76e60b50ca835f56f52d7e6efec77191057cfde0` (tree `8c58f20c90b4adb7f8e69dfdf87bcfb28cd41332`). Phase B now keeps identity-source failures generic and contains no `is_tpex_api` reference. In Phase D, a failed TPEx acquisition records `BOOTSTRAP_TPEX_LIFECYCLE_SOURCE_FAILURE` with decision `BLOCKED_BY_TPEX_LIFECYCLE_SOURCE_FAILURE`, writes the sanitized report, and returns before the next lifecycle probe, Phase E, snapshot export, candidate construction, or activation. Schema drift remains separately classified as `BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT`.

The old combined transport/schema-drift test was split into independent TPEx transport-failure and parser-drift cases, plus a Phase B identity-failure regression. The transport test proves the fifth probe does not run, the fixed POST body remains unchanged, the parser is not called for a failed TPEx response, and qualification/export are not reached. The schema-drift test proves successful transport followed by parser drift is independently terminal. The existing POST-redirect test was corrected to assert the transport’s actual method-change rejection (`BOOTSTRAP_REDIRECT_REJECTED`); transport implementation was not changed.

The focused test set passed: 57 tests across the bootstrap-budget, TPEx JSON parser, A6-P1 authority, and R3 source-contract modules; 17 materialization and Security Master release tests also passed. The locally preserved 71,065-byte response replayed through the production parser as 582 schema-valid `LifecycleEvent` records with zero duplicate identities.

Clean-archive `default-ci` ran under CPython 3.12.14 / pytest 9.1.1, `TZ=Etc/UTC`, `PYTHONHASHSEED=0`, with external DNS and socket destinations denied. Base and candidate each collected 1,288 tests: 1,234 passed, 45 failed, 4 skipped, and 5 deselected. The 45 failed node IDs are identical (their sorted-list SHA-256 is recorded in the JSON), so the new failure delta is zero. An additional snapshot-fixture suite also had the same 8 failures and 10 passes on both base and candidate; its frozen contract hashes are pre-existing fixture debt.

`compileall`, AST phase-boundary assertions, six existing governance validators, strict duplicate-key JSON scanning, and `git diff --check` passed. Historical SM-B1, R2, R5-P1-R1, and R5-P1-R2 records remain byte-identical. The current Security Master remains `NOT_INITIALIZED`; `active.json` is absent and production identity remains unverified. Bootstrap attempt #2 remains unauthorized. Historical TWSE 307 blockers for `twse_delisted` and `twse_etn_expired` remain unresolved.

Network activity was zero: market GET/HEAD/POST `0/0/0`, Security Master live acquisition `0`. H2 remains inactive and plan-only; the selected executor is null; J-B04 remains blocking; Phase J remains not started; MCP remains 6. PR #326 was not merged or otherwise changed by this network-free tranche.
