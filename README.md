# TW-Market Live Data Intelligence

AI-native, local-first workbench for Taiwan market data context. The project helps humans and AI assistants discover, validate, compare, and consume Taiwan market data sources without claiming unverified realtime access or producing trading recommendations.

## Project Overview

This repository separates reviewed historical context from explicitly executed live observations:

- **Level 1 Canonical Context** is the reviewed M5F package under `research/staging/m5f/m5f_canonical_market_context_01/`. It is stale/historical, readonly, and used by the browser preview, FastAPI, MCP, and AI briefing artifacts.
- **Level 2 Live Observation** is an explicit, bounded, non-canonical observation layer for a user-provided watchlist. It never mutates M5F, `frontend/public`, `research/generated`, or production paths.
- **Governance** keeps source evidence, timestamp semantics, freshness, delay, risk, and failure reasons visible.

## Architecture

```text
AI / operator watchlist
        |
        v
Mode A: canonical readonly context  -> M5F package -> FastAPI / MCP / frontend preview
Mode B: plan live observation       -> adapter route plan, no network, no writes
Mode C: explicit bounded observation-> unified observation/failure contract
```

See [`docs/architecture/architecture_overview.md`](docs/architecture/architecture_overview.md) for the consolidated architecture.

## Level 1 Canonical Context

Level 1 is the stable product baseline. It is reviewed, reproducible, historical, and safe for local AI context. It must not be silently refreshed or treated as current market data.

Key contract: [`docs/architecture/level1_canonical.md`](docs/architecture/level1_canonical.md).

## Level 2 Live Observation

Level 2 is a bounded observation layer for current-source checks. It is explicit-only, local-first, source-risk-aware, and separate from canonical context.

Key contract: [`docs/architecture/level2_live_observation.md`](docs/architecture/level2_live_observation.md).

## AI Watchlist Workflow

M5N introduces a formal Watchlist Workspace centered on `config/m5k_default_watchlist.json`. The same importable/exportable JSON watchlist is consumed by FastAPI, MCP, frontend preview, adapter planning, explicit live observation, and the temporary AI conversation context builder. See [`docs/architecture/ai_watchlist_workflow.md`](docs/architecture/ai_watchlist_workflow.md), [`docs/operator/AI_WATCHLIST_OPERATOR_GUIDE.md`](docs/operator/AI_WATCHLIST_OPERATOR_GUIDE.md), and the M5OP operator runbook at [`docs/operator/M5OP_OPERATOR_WORKFLOW.md`](docs/operator/M5OP_OPERATOR_WORKFLOW.md).

## Mode A / Mode B / Mode C

- **Mode A — Readonly canonical context:** consume M5F artifacts only.
- **Mode B — Live observation plan:** validate a watchlist and show adapter routes without network calls.
- **Mode C — Explicit bounded live observation:** execute only after explicit confirmation and emit unified observations/failures.

Details: [`docs/architecture/mode_abc.md`](docs/architecture/mode_abc.md).

## Supported Sources

The current source architecture distinguishes official OpenAPI, browser JSON endpoints, unofficial/fragile endpoints, commercial APIs, and broker/auth SDKs. Capability endpoints remain available, but every source must expose freshness, delay, legal/maintenance risk, and suitability caveats.

Primary references:

- [`config/m5l_live_source_adapter_matrix.json`](config/m5l_live_source_adapter_matrix.json)
- [`docs/architecture/source_adapter_architecture.md`](docs/architecture/source_adapter_architecture.md)
- [`docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md`](docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md)
- [`docs/protocol/TWSE_MIS_PROTOCOL.md`](docs/protocol/TWSE_MIS_PROTOCOL.md)
- [`docs/m5l_live_sources_validation_matrix.md`](docs/m5l_live_sources_validation_matrix.md)

## Quick Start

```bash
python -m pip install -r requirements.txt
pytest -m "not network" -v
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Useful local endpoints:

- `GET /api/health`
- `GET /api/context/canonical`
- `GET /api/context/snapshot`
- `GET /api/m5l/source-capabilities`
- `GET /api/watchlist`
- `GET /api/watchlist/summary`
- `GET /api/watchlist/schema`
- `GET /api/conversation/context`
- Frontend workspace: `frontend/readonly-preview/M5KLocalAIWorkbench.html`
- `GET /api/m5k/watchlist/default`
- `POST /api/m5k/live-observation/plan`
- `POST /api/m5k/live-observation/execute?confirm_live_observation=true`

## Repository Structure

```text
config/                  Source registry, watchlist, adapter matrix
docs/                    Architecture, protocol, validation, operations, reviews, archive
frontend/readonly-preview/ Local readonly browser preview code
research/staging/m5f/    Level 1 canonical context package
research/live_observation_runs/ Level 2 observation evidence and latest local run state
scripts/                 Offline validators, builders, probes, normalization, governance tools
server/                  FastAPI and MCP readonly/explicit-local surfaces
tests/                   Offline regression tests and fixtures
```

## Current Limitations

- No source is represented as guaranteed realtime unless verified by the contract fields.
- M5F is historical/stale reviewed evidence, not production current state.
- Live observation is bounded-watchlist only and explicit-only.
- Controlled refresh remains disabled pending M5I authorization; broker/auth sources are feasibility/governance topics only and credentials must not be committed.
- The project does not emit buy/sell/hold, rankings, target prices, or trading recommendations.

## Roadmap

- Continue converging adapters onto the unified observation/failure contract.
- Expand fixture-backed validation for source-specific edge cases.
- Keep capability and source-risk documentation current as source behavior changes.
- Preserve manual authorization gates before any live evidence collection or publication flow.

## Documentation Index

Start with [`docs/INDEX.md`](docs/INDEX.md). Key entry points:

- Architecture overview: [`docs/architecture/architecture_overview.md`](docs/architecture/architecture_overview.md)
- Source adapter architecture: [`docs/architecture/source_adapter_architecture.md`](docs/architecture/source_adapter_architecture.md)
- Data contract: [`docs/data_contract.md`](docs/data_contract.md)
- AI watchlist workflow: [`docs/architecture/ai_watchlist_workflow.md`](docs/architecture/ai_watchlist_workflow.md)
- AI watchlist operator guide: [`docs/operator/AI_WATCHLIST_OPERATOR_GUIDE.md`](docs/operator/AI_WATCHLIST_OPERATOR_GUIDE.md)
- M5OP operator workflow: [`docs/operator/M5OP_OPERATOR_WORKFLOW.md`](docs/operator/M5OP_OPERATOR_WORKFLOW.md)
- MCP usage: [`docs/mcp_usage_guide.md`](docs/mcp_usage_guide.md)
- Operations runbook: [`docs/operations_runbook.md`](docs/operations_runbook.md)
- README archive: [`docs/archive/readme/README_20260630_M5LRM_ARCHITECTURE_CONVERGENCE.md`](docs/archive/readme/README_20260630_M5LRM_ARCHITECTURE_CONVERGENCE.md)
