# M8R-06-01 Unified Workbench Mode A Implementation

This document describes the architecture, constraints, and operational characteristics of the Unified Operator Workbench - Mode A (Inspect and Validate) boundary.

## 1. Architectural Role
Mode A provides an isolated, localhost-only, deterministic presentation layer for `scripts.m8r_05a_f3.request_intake.validate_unified_market_evidence_request()`.
It does not parse domain logic in the UI. It passes raw request payload to the F3 validator and renders the resulting Canonical F3 Result.

## 2. API Contract & Bounded Surface
**Endpoint**: `POST /api/unified/validate-request`
**Mode B1 endpoint**: `POST /api/unified/preview-request`
**Route location**: `server.unified_workbench_router`
**Service Layer**: `server.services.unified_mode_a`

The endpoint forces a strict `< 1 MiB` body constraint, and rejects cross-origin HTTP traffic to enforce operator privacy and offline determinism.

## 3. Canonical Assets
Mode A loads:
- `unified_market_evidence_request.v1.schema.json`
- `unified_market_evidence_capability_catalog.v1.json`
- `config/m8r_06_mode_a_security_master_pointer.json`
- the committed immutable C1B seal and its strictly validated local compact candidate

The process-lifetime runtime uses an immutable selection; pointer changes require restart. Missing or invalid governed artifacts fail closed without fixture, alternate-candidate, or network fallback.

## 4. No Network Boundary
Unit testing patches `socket`, `requests`, `httpx`, and `urllib` to prove F3 Mode A evaluates in strict offline bounds. No external asset URLs (Google Fonts, CDNs) are loaded by the `frontend/unified-workbench/UnifiedMarketEvidenceWorkbench.html` CSP `default-src 'self'`.

## 5. Security & State Transition
No path injection is allowed; schemas are referenced via `Path(__file__).resolve()`.
Unified Request schema-invalid input returns the canonical F3 validation result but produces no canonical Preview. By contrast, governed target ambiguity and target-not-plannable outcomes may produce deterministic non-executable Mode B1 Previews that explain the blocker. Neither outcome becomes an executable plan or an authorization candidate.

## 6. Mode B1 Boundary

Mode B1 reruns production F3, cryptographically binds the request, F3 output, active Security Master, catalog, routing matrix, and handoff contract, then invokes the accepted M8R-05B-01 deterministic planner. The canonical Preview is explicitly `PREVIEW_ONLY`, `NO_NETWORK_EXECUTED`, and `EXECUTION_NOT_AUTHORIZED`. Mode B2 authorization/execution is outside this boundary.
