# J-B04-A6-SM-B1-R2 — Fail-Closed Repair and 3xx Diagnostics

**J_B04_A6_SM_B1_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW**

This network-free repair preserves the independently reviewed SM-B1 hard block (review 5476829857). The historical SM-B1 JSON and Markdown records remain byte-identical. No bootstrap retry was authorized or executed.

## Captured TPEx payload

The preserved 11,521-byte payload at `data/security_master/input_bundles/m8r06-01b-20261009T180413Z/raw_payloads/tpex_delisted.html` has SHA-256 `f6eaa4a4969219dc5a633f43e056d8fa2d31fa944c1e23125f24836733f86853`. It is an HTML document with no `<table>` elements. The captured page contains lifecycle search controls and a client-side table initializer configured with action `company/deListed`, but this response body contains no lifecycle result rows or embedded JSON data. The body references `API_PATTERN`, whose resolved endpoint and response are not established here. This supports `CAPTURE_HAS_ALTERNATE_STRUCTURED_DATA_REQUIRING_NEW_CONTRACT`; it does not establish a new authorized source or parser contract. Any parser/source-contract repair is `SM_B1_R2_SOURCE_CONTRACT_REPAIR_REQUIRED` and needs separate review. No current web state was consulted.

## Fail-closed repair

The materializer previously appended `LifecycleSchemaDrift` to failures and continued the lifecycle loop. It now records `BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT` with source, parser, issue code, bounded sanitized header-shape detail, and dispatch reservations, writes the failure evidence, and returns immediately. The fifth probe, Phase E aggregate qualification, snapshot/export, candidate construction, and activation cannot follow a mandatory lifecycle parser drift. The behavior applies to every `LifecycleSchemaDrift` issue code.

For HTTP 3xx errors reaching the `HTTPError` path, telemetry now records the status, whether Location exists, sanitized scheme/host/path, allowlist result, `redirect_followed=false`, and `BOOTSTRAP_HTTP_REDIRECT_NOT_FOLLOWED`. Query, fragment, credentials, and response body are not persisted. The diagnostic does not infer why the redirect was not followed. Ordinary 404/500 handling remains unchanged.

The five logical probes and shared limits remain unchanged: at most one followed redirect and two dispatch reservations per probe, ten total, no retry, and reservation before dispatch. Tests use fake transport only. The focused regression run passed 319 tests with 2 skips; the R2 fail-closed/3xx suite passed 15 tests. Validators, compileall, diff check, and strict duplicate-key scan (1,045 JSON files) passed. Default-CI base/head comparison is recorded after the implementation commit.

## State

Security Master remains `NOT_INITIALIZED`; `active.json` is absent and production identity remains unverified. Bootstrap retry is not authorized. H2 remains inactive and unselected with `plan_only` routing; J-B04 remains blocking, Phase J not started, and MCP count remains six. Market GET/HEAD/POST and Security Master live acquisition during R2 are `0/0/0` and `0`.

Default-CI was compared from clean archives of base `039b421e4d53be770f2a37124d01d4a16d31f452` and implementation commit `26f0079b79e098a783cadffed39b388ac49fb757`, using the same CPython 3.12.14 environment, command, UTC timezone, and `PYTHONHASHSEED=0`. Both runs collected 1,288, selected 1,283, passed 1,234, failed 45, skipped 4, and deselected 5. The 45 failed node IDs match exactly; new failure delta is zero. The profile reported `network_may_have_occurred=false`.
