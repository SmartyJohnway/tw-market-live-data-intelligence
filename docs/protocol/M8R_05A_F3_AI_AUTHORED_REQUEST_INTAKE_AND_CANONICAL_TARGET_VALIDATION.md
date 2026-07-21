# M8R-05A-F3 AI-Authored Request Intake and Canonical Target Validation

## Purpose
This document defines the architecture boundary, input/output contracts, and validation semantics for the F3 layer of the M8 Unified Market Evidence workflow. F3 provides a deterministic, local-first, and fail-closed validation mechanism for Unified Market Evidence Requests authored by AI agents.

## Architecture Boundary
- **Input**: A JSON payload strictly conforming to `unified_market_evidence_request.v1`.
- **F3 Role**: 
  - Validates the incoming request against its schema.
  - Resolves target identities against local, read-only canonical security masters.
  - Evaluates requested capabilities (`data_needs`) against the canonical capability catalog.
  - Enforces bounds and limitations (e.g., duplicate policies, maximum targets).
- **Output**: A JSON payload strictly conforming to `unified_market_evidence_request_validation.v1`.
- **Non-Goals**: F3 is **NOT** a semantic router, network executor, LLM resolver, or fuzzy search engine. It does not perform orchestrations, compile 03C bundles, execute external probes, or mutate persistent watchlists.

## Input Contract
F3 accepts `unified_market_evidence_request.v1`. No wrapper schemas or alternative intent representations are permitted.

## Output Contract
F3 outputs `unified_market_evidence_request_validation.v1`. The output guarantees that AI can definitively know whether to proceed with execution, clarify ambiguity with the user, or abandon an invalid/unsupported request.

## Target Status Semantics
Each target evaluates to one of the following resolution statuses:
- `resolved`: Exact match found in the canonical master matching the target code and market hint.
- `ambiguous`: Multiple matches exist (e.g., identical names or aliases) or an exact match without a market hint yields multiple candidates.
- `not_found`: No matching target found.
- `unsupported_market`: The specified market hint is not supported by the platform.
- `unsupported_security_type`: The resolved security type is outside the supported scope.
- `invalid_market_hint`: The market hint is semantically invalid.
- `market_mismatch`: The target code is valid, but belongs to a different market than the requested market hint.
- `invalid_input`: The input string violates base constraints.
- `duplicate`: The target violates duplicate evaluation rules.

## Reason Codes
A stable taxonomy of machine-readable reason codes, including but not limited to:
- `REQUEST_SCHEMA_INVALID`
- `UNSUPPORTED_SCHEMA_VERSION`
- `TARGET_INPUT_EMPTY`
- `TARGET_NOT_FOUND`
- `TARGET_AMBIGUOUS`
- `TARGET_MARKET_MISMATCH`
- `TARGET_MARKET_UNSUPPORTED`
- `TARGET_SECURITY_TYPE_UNSUPPORTED`
- `TARGET_DUPLICATE`
- `MARKET_HINT_INVALID`
- `CAPABILITY_UNKNOWN`
- `CAPABILITY_UNSUPPORTED_FOR_MARKET`
- `CAPABILITY_PARAMETER_INVALID`
- `TARGET_LIMIT_EXCEEDED`
- `REQUIRED_TARGET_UNRESOLVED`
- `REQUIRED_CAPABILITY_UNAVAILABLE`

## Capability Validation
Capabilities are validated against the `unified_market_evidence_capability_catalog.v1`. 
- **Required Capabilities**: If a required capability is unsupported, invalid, or unknown, the top-level validation status becomes `invalid` or `unsupported`.
- **Optional Capabilities**: If unsupported, F3 retains them in the result with a warning, but they do not block a `valid` top-level status.

## Bounds
F3 enforces boundaries like `default_target_limit`, `hard_target_limit`, and duplicate checking policies without producing execution-dependent projections. If precise operation counts require the 05B orchestrator, F3 outputs `orchestrator_projection_required: true`.

## Fail-Closed Behavior
F3 fails closed under ambiguity, market mismatches, missing required targets, missing required capabilities, and schema violations. It does not auto-correct mismatches or silently omit invalid requirements.

## Examples

### Case: Exact Match
**Request:** `2330` with `TWSE`
**Result:** `resolved`, canonical identity populated, top-level `valid`.

### Case: Market Mismatch
**Request:** `2330` with `TPEX`
**Result:** `market_mismatch`. Top-level `invalid`.

### Case: Missing Required Capability
**Request:** `TAIFEX` target with required `current_observation` (not supported for TAIFEX currently).
**Result:** Capability status `unsupported`, top-level `unsupported`.
