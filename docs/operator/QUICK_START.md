# Operator Quick Start

This is the current source-checkout quick start for the local Unified product.

## 1. Install and verify

```bash
python -m venv .venv
# Activate .venv for your shell
python -m pip install -r requirements-lock.txt
python scripts/verify_environment.py
python scripts/manage_security_master.py status
```

A fresh installation returning `NOT_INITIALIZED` is valid and fail-closed.

Initialize/update the installation-local Taiwan Market Identity Service only
when explicitly intended:

```bash
python scripts/manage_security_master.py update --live
```

That command may use governed official external acquisition.

## 2. Start the Unified Workbench

```bash
python scripts/run_unified_workbench.py
```

Open:

```text
http://127.0.0.1:8000/workbench/
```

The normal product flow is:

```text
Request
-> Validate / Identity
-> Preview
-> explicit authorization
-> execute once
-> Result
-> Audit
-> AI Handoff
```

## 3. MCP host

Start the local stdio Unified MCP server with:

```bash
python scripts/run_unified_market_evidence_mcp.py
```

The MCP surface is exactly six tools. See
[../reference/MCP_REFERENCE.md](../reference/MCP_REFERENCE.md).

## 4. Current contract

- accepted Requests: V1 / V2 / V3
- preferred Request: V3
- new governed Result/Audit materialization: V3
- V1/V2 remain compatibility contracts
- existing historical packages keep their persisted version

Capability executability is determined by the current V3 Catalog/Route/Executor
authority. A supported schema does not imply an active route.

## 5. Current Phase H limitation

Only one Phase H source route is currently active:

`H1-TPEX-ATTENTION-OPENAPI`

Trading-status coverage is partial. Do not claim complete attention/disposition/
suspension/resumption/changed-trading coverage. H2/H3 activation remains
incomplete.

## 6. Deterministic validation

```bash
python -m compileall -q scripts server tests
python scripts/validate_phase_h_v3_contracts.py
python scripts/validate_portable_catalog_sync.py
python scripts/validate_runtime_skill_guide_sync.py
python scripts/run_test_profile.py default-ci
git diff --check
```

Default validation is non-network.

## Safety

No polling, scheduler, hidden startup market fetch, broad crawl, full-market
scan, automatic Watchlist execution, trading, order routing, or realtime
guarantee is implied by starting the Workbench or MCP server.
