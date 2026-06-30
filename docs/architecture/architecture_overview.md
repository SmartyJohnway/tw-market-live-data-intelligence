# Architecture Overview

This repository is a local-first Taiwan market context workbench with two intentionally separated layers.

## Layer separation

| Layer | Purpose | Mutability | Consumer surfaces |
|---|---|---:|---|
| Level 1 Canonical Context | Reviewed historical M5F context package | Readonly in normal product operation | FastAPI, MCP, frontend readonly preview, AI briefing |
| Level 2 Live Observation | Explicit bounded observation over a watchlist | Local observation evidence only | FastAPI M5K endpoints, MCP M5K tools, readonly-preview workbench |

Level 2 outputs must not change Level 1 semantics or package structure.

## Contract convergence

The converged product contract is:

1. Source adapters plan bounded routes without network access.
2. Explicit observation adapters fetch only bounded targets.
3. Adapter rows normalize into one observation model or one failure model.
4. FastAPI, MCP, and frontend consume those models without source-specific payload shapes.
5. Capability endpoints expose supported routes and limitations separately from current observations.

## Evidence boundaries

Every source path must preserve source name, source type, URL/SDK, method, headers/session requirements, status, sample/failure semantics, parsed fields, timestamp fields, freshness, legal/maintenance risk, and AI-integration suitability. Raw payloads and credentials are not exposed through normalized observations.
