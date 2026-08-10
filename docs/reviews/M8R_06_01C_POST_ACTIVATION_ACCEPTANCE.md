# M8R-06-01C Final Post-Activation Acceptance

Baseline: `24a5757e518f16def6f550e9e1c7ff64b0b7191f`

Status: **PASS_WITH_CAVEATS**

Principal decision: **READY_FOR_M8R_06_02_AUTHORIZATION_REVIEW**

This is a readiness recommendation only. M8R-06-02 and all later implementation scopes remain **NOT_AUTHORIZED**.

## Merged-main acceptance

The entire acceptance was rerun from merged main after PR #186. Startup, the real localhost server, the corrected workbench root, production Mode A activation, process-lifetime cache reuse, restart reactivation, fail-closed behavior, fixture isolation, and regression suites passed without modifying production files.

The accepted chain was validated directly:

```text
committed Mode A pointer
  -> committed C1B immutable seal
  -> local manifest
  -> local compact index
  -> strict C1B/C2 validation
  -> canonical-compatible lookup
  -> Mode A request validation
```

The exact candidate contained 43,070 records, including 2,324 runtime-eligible records and zero `fixture_observation_only` records. Its index SHA-256 was `ad467f077c76d9c7462545fcf322d4960cbd485d09d34463e26dfefea8c1c455`; its manifest SHA-256 was `01857224d025bd9342402917c140050f0fb40b385a65103702c856037dfc93db`.

## Startup and real HTTP

The independent startup check passed in 11.604883 seconds with Mode A active, no startup network, and all required schemas, Security Master data, and capability catalog loaded.

Two actual server processes were launched through `scripts/run_unified_workbench.py`, bound only to `127.0.0.1`, and fully terminated after testing. The first process returned HTTP 200 for `/api/health`, `/workbench/mode-a/`, the explicit HTML file, CSS, and JavaScript. The workbench root body contained `Unified Market Evidence Operator Workbench`.

The first real production request used the committed pointer, immutable seal, exact local candidate, strict loader, and production provider without monkeypatching or fixtures. It completed cold activation in 18.417912 seconds and resolved `2330 / TWSE` to `TWSE:2330`. The same process also proved:

- `TPEX:5227` resolved;
- an unknown sentinel returned `not_found`;
- `5227` with a TWSE hint returned `market_mismatch`;
- `TWSE:5871A` returned `unsupported_security_type`;
- repeated `TWSE:2330` returned `duplicate`;
- 51 targets returned `TARGET_LIMIT_EXCEEDED`;
- an invalid request returned `REQUEST_SCHEMA_INVALID`.

## Process-lifetime runtime

The accepted consistency model remains `PROCESS_LIFETIME_IMMUTABLE_SELECTION`; pointer changes require restart. After one cold activation, real localhost HTTP measurements were:

- 20 warm `2330 / TWSE` requests: median 7.024 ms, p95 8.540 ms;
- 20 warm two-target requests (`TWSE:2330` plus `TPEX:5227`): median 6.982 ms, p95 7.830 ms.

Warm requests remained millisecond-scale and did not repeat full artifact validation. A completely new second server process independently rebuilt the runtime from pointer, seal, and candidate, then returned HTTP 200 and resolved `TWSE:2330`. No hidden persistent cache dependency was required.

## Governance and regression closure

Synthetic temporary-artifact tests passed for missing or malformed pointers; missing index, manifest, or seal; pointer, manifest, index, seal, and coverage tampering; path traversal and absolute paths; fixture rejection; and failed-activation cache safety. Production-unavailable behavior remains HTTP 409 with `canonical_security_master_unavailable`, without alternate candidate, fixture, network fallback, filesystem path leakage, or traceback leakage.

Validation results:

- C2 focused and fail-closed tests: 25 passed, with real sealed-local tests executed and no skip;
- C1B compact runtime tests: 23 passed, including 43,070 canonical IDs and 86,160 resolver queries;
- canonical Security Master tests: 18 passed;
- Mode A/F3 tests: 42 passed;
- Workbench/API tests: 9 passed;
- repository default CI: 793 passed, zero failed, no network;
- compileall and `git diff --check`: passed;
- GitHub remote CI at evidence generation: `NOT_RUN`.

## Accepted caveats and boundary

The candidate remains intentionally local and Git-ignored; its absence fails closed. Cold activation remains expensive but is limited to once per process, and no repository hard threshold exists. Peak memory was not measured reliably. The existing Starlette/httpx TestClient deprecation warning remains non-blocking.

No external market-data probe, fresh source probe, refresh, Mode B, Mode C, M8R-06-02, M8R-07, MCP, background refresh, or scheduler work occurred.
