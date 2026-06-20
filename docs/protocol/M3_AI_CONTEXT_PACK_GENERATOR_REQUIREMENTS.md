# M3 AI Context Pack Generator Requirements

**Important:** This document outlines the requirements for a *future* M3-02 generator. M3-01 is strictly a design-only phase. No implementation, generation, or validation code is introduced in M3-01.

## 1. Inputs

The future generator must source its data deterministically from the following baseline documents:
- `docs/protocol/M2_SOURCE_CONTRACT_BASELINE.md`
- `docs/protocol/M2_NORMALIZED_SCHEMA_INVENTORY.md`
- `docs/protocol/M3_READINESS_GATE.md`
- `docs/protocol/TARGET_TAXONOMY.md`
- `docs/protocol/SOURCE_TARGET_SUPPORT_MATRIX.md`
- `docs/source_catalog.md`
- `docs/capability_matrix.md`
- `frontend/public/matrix.json`
- `research/probe_log.md`

## 2. Outputs

The future generator is expected to produce two output artifacts:
- `research/generated/m3_ai_context_pack_v1.json`
- `research/generated/m3_ai_context_pack_v1.md`

*(Note: Do not create these output files during M3-01).*

## 3. Deterministic Behavior

- **Requirement:** Deterministic output under fixed inputs.
- **Expected behavior:** Given an unmodified set of input documents, the generator must produce the exact same output artifacts (excluding timestamps).
- **Candidate approach:** A Python script utilizing stable JSON sorting (`sort_keys=True`) and strictly ordered iteration over input keys.
- **M3-01 status:** Design-only; no deterministic generation logic is implemented in this PR.

## 4. Network and Live Probing

- **Requirement:** No live network dependency.
- **Expected behavior:** The generator must rely entirely on offline baseline documents. It must not execute HTTP requests, API calls, or invoke the active probe framework.
- **Candidate approach:** Read exclusively from local file paths using `pathlib` or `os` without importing `requests` or `httpx` in the generation loop.
- **M3-01 status:** Design-only; no network isolation logic is implemented in this PR.

## 5. Configuration Migration

- **Requirement:** No config migration requirement by default.
- **Expected behavior:** The generator must process existing config schemas (e.g., `config/market_targets.json`) without mutating them.
- **Candidate approach:** Read-only access to configuration files.
- **M3-01 status:** Design-only; no config migration logic is implemented in this PR.

## 6. Prohibited Semantics

- **Requirement:** No trading, recommendation, or execution semantics.
- **Expected behavior:** The generator must statically inject the guardrails defined in `docs/protocol/M3_AI_CONTEXT_GUARDRAILS.md`. It must not infer or append buy/sell advice.
- **Candidate approach:** Explicit string inclusion of prohibited usages into the final JSON output.
- **M3-01 status:** Design-only; no injection logic is implemented in this PR.

## 7. Required Validation

The future generator must include robust validation to ensure the integrity of the generated context pack.

### 7.1 JSON Schema Validation
- **Requirement:** JSON schema validation.
- **Expected behavior:** Future generator output must validate against the M3 context pack schema before being committed or consumed.
- **Candidate approach:** A future Python validator may use `jsonschema` or an equivalent strict schema validation library.
- **M3-01 status:** Design-only; no library is added and no validator is implemented in this PR.

### 7.2 Offline-only CI Compatibility
- **Requirement:** Offline-only CI compatibility.
- **Expected behavior:** Validation tests must pass in standard GitHub Actions environments without network access.
- **Candidate approach:** Integration with `pytest` utilizing the existing `-m "not network"` marker.
- **M3-01 status:** Design-only; no CI modifications are made in this PR.

### 7.3 Source Caveat Preservation Checks
- **Requirement:** Source caveat preservation checks.
- **Expected behavior:** Tests must verify that `must_show_caveats` defined in source protocols are correctly transposed into the final context pack.
- **Candidate approach:** Pytest assertions comparing raw source docs against the generated JSON structure.
- **M3-01 status:** Design-only; no caveat preservation tests are implemented in this PR.

### 7.4 Metadata Completeness Checks
- **Requirement:** Freshness / delay / staleness presence checks.
- **Expected behavior:** Every source entry must contain valid metadata regarding its temporal delay.
- **Candidate approach:** Schema requirements enforcing `freshness_status` and `delay_status` fields.
- **M3-01 status:** Design-only; no completeness tests are implemented in this PR.

### 7.5 Authority Distinction Checks
- **Requirement:** Official / unofficial / third-party / broker distinction checks.
- **Expected behavior:** Sources must be correctly labeled according to their authority level to prevent misrepresentation.
- **Candidate approach:** Strict enum validation on the `authority_level` field.
- **M3-01 status:** Design-only; no enum validation is implemented in this PR.

### 7.6 Support Status Visibility Checks
- **Requirement:** Candidate / unknown support visibility checks.
- **Expected behavior:** Sources with inferred support must clearly indicate unverified status.
- **Candidate approach:** Schema constraints rejecting ambiguous combinations like "unknown/auth_required".
- **M3-01 status:** Design-only; no status visibility tests are implemented in this PR.

### 7.7 Guardrail Integrity Checks
- **Requirement:** Prohibited-use / no-trading-signal checks.
- **Expected behavior:** The context pack must contain the explicit list of prohibited actions.
- **Candidate approach:** Substring or exact-match verification of guardrail blocks during testing.
- **M3-01 status:** Design-only; no guardrail integrity tests are implemented in this PR.

### 7.8 Artifact Mutation Isolation
- **Requirement:** No generated artifact mutation outside authorized output paths.
- **Expected behavior:** The generator must only write to `research/generated/m3_ai_context_pack_v1.*`. It must not modify `docs/*` or `config/*`.
- **Candidate approach:** Restricted file write permissions within the Python script scope.
- **M3-01 status:** Design-only; no path restriction logic is implemented in this PR.

## 8. Failure Behavior

- **Requirement:** Failure behavior when required source documents are missing.
- **Expected behavior:** If a required input document (e.g., `M2_SOURCE_CONTRACT_BASELINE.md`) is missing or malformed, the generator must halt execution and return a non-zero exit code.
- **Candidate approach:** Explicit existence checks (`Path.exists()`) and clear exception raising (`FileNotFoundError`).
- **M3-01 status:** Design-only; no error handling logic is implemented in this PR.

## 9. Versioning

- **Requirement:** Versioning scheme.
- **Expected behavior:** The generator must stamp the output with `pack_version` (e.g., `m3_ai_context_pack_v1`).
- **Candidate approach:** Hardcoded version string in the generator script, updated per major contract revision.
- **M3-01 status:** Design-only; no versioning implementation is provided in this PR.