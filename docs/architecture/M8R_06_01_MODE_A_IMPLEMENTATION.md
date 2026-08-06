# M8R-06-01 Unified Workbench Mode A Implementation

This document describes the architecture, constraints, and operational characteristics of the Unified Operator Workbench - Mode A (Inspect and Validate) boundary.

## 1. Architectural Role
Mode A provides an isolated, localhost-only, deterministic presentation layer for `scripts.m8r_05a_f3.request_intake.validate_unified_market_evidence_request()`.
It does not parse domain logic in the UI. It passes raw request payload to the F3 validator and renders the resulting Canonical F3 Result.

## 2. API Contract & Bounded Surface
**Endpoint**: `POST /api/unified/validate-request`
**Route location**: `server.unified_workbench_router`
**Service Layer**: `server.services.unified_mode_a`

The endpoint forces a strict `< 1 MiB` body constraint, and rejects cross-origin HTTP traffic to enforce operator privacy and offline determinism.

## 3. Canonical Assets
Mode A must be able to load:
- `unified_market_evidence_request.v1.schema.json`
- `unified_market_evidence_capability_catalog.v1.json`
- `production_security_master_snapshot.json`

Currently, `PRODUCTION_SNAPSHOT_PATH` is loaded for the security master via `allow_fixture_snapshot=False`. Since a governed production security master snapshot does not exist in `config/`, the endpoint currently fails closed and validation is blocked.

## 4. No Network Boundary
Unit testing patches `socket`, `requests`, `httpx`, and `urllib` to prove F3 Mode A evaluates in strict offline bounds. No external asset URLs (Google Fonts, CDNs) are loaded by the `frontend/unified-workbench/UnifiedMarketEvidenceWorkbench.html` CSP `default-src 'self'`.

## 5. Security & State Transition
No path injection is allowed; schemas are referenced via `Path(__file__).resolve()`.
Invalid requests render properly as Canonical Validation Results (with HTTP 200 payload) ensuring operators see F3 blocking issues, but are prohibited from transitioning into Mode B1 (Preview).
