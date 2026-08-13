# M8R-08C-R1 Local Service Readiness Repair

## Baseline and observed production symptom

Baseline: `62c6f5db846d9a3aa42710dd6d98cdce9cfd7848` (M8R-08B merged).

Real Codex MCP host acceptance found a deterministic cold-readiness issue. The first direct production validation took `14.37s`; warm validations were `0.01–0.03s`. The M8R-08B Local Service client timeout is correctly bounded at `15.0s`, so the first `market_validate_request` returned `local_service_timeout`, although Uvicorn subsequently recorded the same request as HTTP 200. A warm retry passed.

The evidence identified a process boundary error: `--startup-check` activated the governed Security Master in a temporary process which then exited. Normal serving did not activate it before Uvicorn accepted requests. The existing production selection model is `PROCESS_LIFETIME_IMMUTABLE_SELECTION`; the first client therefore paid strict activation cost.

## Narrow repair

The official `scripts/run_unified_workbench.py` launcher now has one shared `preload_governed_runtime()` helper. It uses the accepted Mode A canonical schema/catalog paths and `_load_json`, then `get_production_mode_a_security_master(PRODUCTION_POINTER_PATH)`. It does not create a loader, cache, fallback, FastAPI lifespan hook, background process, or market access.

Normal order is now: parse arguments → validate loopback host → preload governed runtime in the serving process → fail closed if preload fails → `uvicorn.run`. `--startup-check` uses the same helper. Bounded errors expose only an error class, not filesystem paths. Invalid remote binding is rejected before expensive preload.

MCP timeout is intentionally unchanged at `15.0s`; this moves cold cost before readiness rather than masking it with a longer client timeout.

## Local acceptance on implementation head

Implementation code head: `2e76a2a83d106b5e8b4268c5397cecd146e706a2`.

With no prior Workbench listener on port 8000, the launcher was started at `127.0.0.1:8000`. Uvicorn readiness was observed after `11.749s`. Immediately after readiness, without a warm-up validation:

- first `POST /api/unified/validate-request`: HTTP 200 in `0.0453s`;
- second identical validation: HTTP 200 in `0.0083s`.

This demonstrates that the cold cost moved before server readiness and the first post-ready validation is well below the MCP 15-second timeout. This local acceptance made no production market request.

## Deterministic coverage and closure

Focused launcher/readiness, Security Master immutability, and M8R-08B compatibility selection: `54 passed`, `0 failed`, `1 warning`. Coverage proves preload-before-Uvicorn ordering, failure prevents bind, remote-host rejection occurs before preload, shared startup helper use, no fixture fallback, and unchanged MCP safe-tool surface.

Final-head full closure results are recorded in PR metadata after the documentation commit. Automatic external market-network calls remain `0`.

## Caveats

This repair intentionally changes only the official Workbench launcher. It does not preload arbitrary FastAPI/TestClient processes, change the Local Service contract, modify M8R-08B, or change production source behavior.

