# Troubleshooting

## Environment / dependencies

Use the locked development environment:

```bash
python -m pip install -r requirements-lock.txt
python scripts/verify_environment.py
python scripts/run_environment_diagnostics.py
```

## Security Master is NOT_INITIALIZED

This is a valid fresh-install state, not corruption.

Check:

```bash
python scripts/manage_security_master.py status
```

Only initialize/update when explicitly intended:

```bash
python scripts/manage_security_master.py update --live
```

Do not substitute fixtures or historical Candidate B payloads.

## Workbench does not start

Use the canonical launcher:

```bash
python scripts/run_unified_workbench.py
```

Then open `http://127.0.0.1:8000/workbench/`.

## MCP startup failure

Use:

```bash
python scripts/run_unified_market_evidence_mcp.py
```

The current MCP has exactly six tools. If a host reports an older M5/M6 tool
surface, verify it is launching the current Unified MCP command rather than a
legacy compatibility server.

## Request validates but cannot execute

Check current capability/route truth. Common legitimate causes include:

- identity known but capability execution unsupported;
- route blocked or plan-only;
- target market not covered by the active route;
- required approval missing;
- Security Master not initialized;
- source failure;
- network confirmation missing.

V3 schema support alone does not activate a route.

## Phase H trading-status surprise

Current H1 execution is partial: only the TPEx attention route is active.
TWSE trading-status requests or disposition/suspension/resumption/
changed-trading requests may correctly fail closed or remain non-executable.

## Deterministic regression failure

Run:

```bash
python -m compileall -q scripts server tests
python scripts/validate_phase_h_v3_contracts.py
python scripts/validate_portable_catalog_sync.py
python scripts/validate_runtime_skill_guide_sync.py
python scripts/run_test_profile.py default-ci
git diff --check
```

Do not add live network access to make deterministic CI pass.

## TLS / source failures

Treat TLS, HTTP, schema drift, empty source and source-unavailable outcomes as
governed source failures. Do not silently disable TLS verification or retry in
an unbounded loop.

Historical M5/M6 TLS diagnostic tools may still exist for compatibility; they
are not the current product workflow.

## Browser tooling

Browser E2E remains optional tooling. If a specific acceptance requires it:

```bash
python -m pip install -r requirements-browser-e2e.txt
python -m playwright install chromium
```

Do not confuse missing optional browser dependencies with failure of the core
local Unified runtime.
