# M8R-05C: Result and Audit Package Preflight

**Task**: M8R-05C-COMPLETE-AI-CONTEXT-RESULT-AND-SEPARATE-AUDIT-PACKAGE  
**Date**: 2026-08-05  
**Baseline SHA**: `370374aff9f4b515c26757583ef7adda6ec80891`  
**Predecessor**: M8R-05B-03 (accepted, PR #171, merged)

---

## 1. Authoritative Input Schemas

| Schema | Path |
|--------|------|
| `unified_market_evidence_request.v1` | `schemas/unified_market_evidence_request.v1.schema.json` |
| `unified_market_evidence_orchestration_plan.v1` | `schemas/unified_market_evidence_orchestration_plan.v1.schema.json` |
| `unified_market_evidence_execution_receipt.v1` | `schemas/unified_market_evidence_execution_receipt.v1.schema.json` |
| `unified_market_evidence_bundle.v1` | `schemas/unified_market_evidence_bundle.v1.schema.json` |
| `unified_market_evidence_orchestrator_preflight.v1` | `schemas/unified_market_evidence_orchestrator_preflight.v1.schema.json` |
| `unified_market_evidence_result.v1` (pre-05C) | `schemas/unified_market_evidence_result.v1.schema.json` |

---

## 2. Materialized Predecessor Artifacts

M8R-05B-03 materializes to a governed `output_root`. M8R-05C consumes these as explicit input:

| Artifact | Path Pattern |
|----------|-------------|
| Execution receipt | `receipts/{authorization_id}.execution-receipt.json` |
| Evidence bundle | `bundles/{authorization_id}.evidence-bundle.json` |
| Evidence artifacts | Per `bundle.operation_evidence_entries[].artifacts[].relative_path` |
| Finalization journal | `finalization/{authorization_id}.finalization-journal.json` |

---

## 3. Current Result Schema Gaps

The existing `unified_market_evidence_result.v1.schema.json` is missing:

### Missing Required Fields
- `result_id` (string, `^umeresult-v1-[0-9a-f]{20}$`)
- `result_hash` (string, sha256 hex)
- `generated_at` (datetime)
- `request_summary` (object with mode, counts, data_needs)

### Incomplete `audit_reference`
- Missing `audit_package_id`, `schema_version`, `relative_path`
- `audit_id` and `execution_time_ms` exist but are inadequate for 05C

### Compatibility Assessment
> **All gaps are additive.** No existing passing test fixture is broken by adding new `required` fields — the fixture update is mandatory and safe. **v1 in-place evolution. No v2 needed.**

---

## 4. Field Provenance Matrix

| Output Field | Source Artifact | Source Rule | Req. | AI/Audit |
|---|---|---|---|---|
| `result_id` | computed | `sha256_json({request_id, receipt_id, bundle_id})[:20]` prefixed `umeresult-v1-` | ✓ | AI |
| `result_hash` | computed | `sha256_json(body excluding result_hash)` | ✓ | AI |
| `generated_at` | receipt or CLI | `receipt.finalized_at` or `--calculated-at` | ✓ | AI |
| `request_id` | request | `request.request_id` | ✓ | AI |
| `request_summary.execution_mode` | request | `request.execution_mode` | ✓ | AI |
| `request_summary.target_count` | request | `len(request.targets)` | ✓ | AI |
| `request_summary.requested_data_needs` | request | sorted `[n.type for n in request.data_needs]` | ✓ | AI |
| `request_summary.required_data_needs` | request | sorted needs where `priority==required` | ✓ | AI |
| `request_summary.optional_data_needs` | request | sorted needs where `priority==optional` | ✓ | AI |
| `status` | computed | deterministic status rule (§5.4) | ✓ | AI |
| `targets[].resolution` | plan | `plan.operations[].canonical_target_ids` + market | ✓ | AI |
| `targets[].evidence.*` | bundle artifacts | `artifact_root + relative_path → JSON` | per need | AI |
| `targets[].citations[]` | bundle + request | deterministic from op_id + artifact sha256 | when evidence | AI |
| `targets[].coverage` | computed | provided vs missing data_needs | ✓ | AI |
| `partial_failures[].reason_code` | receipt | `operation_receipts[].error_code` | when failure | AI |
| `audit_reference.audit_package_id` | computed | `sha256_json({result_id, bundle_id})[:20]` prefixed `umeap-v1-` | ✓ | AI (ref) |
| `audit_reference.relative_path` | computed | `audit/unified_market_evidence_audit_package.v1.json` | ✓ | AI (ref) |
| **Audit: request_identity** | request | request_id + sha256 of request | ✓ | Audit |
| **Audit: target_validation_identity** | plan input_bindings | f3_validation_output_hash | ✓ | Audit |
| **Audit: plan_identity** | plan | plan_id + plan_hash | ✓ | Audit |
| **Audit: authorization_identity** | preflight | authorization_id + authorization_hash | ✓ | Audit |
| **Audit: claim_identity** | preflight | claim_id + claim_hash | ✓ | Audit |
| **Audit: receipt_identity** | receipt | execution_receipt_id + execution_receipt_hash | ✓ | Audit |
| **Audit: bundle_identity** | bundle | bundle_id + bundle_hash | ✓ | Audit |
| **Audit: operation_lineage[]** | plan + preflight + receipt + bundle | per-operation full provenance | ✓ | Audit |
| **Audit: artifact_inventory[]** | bundle | bundle.artifact_inventory | ✓ | Audit |
| **Audit: replay_manifest** | all | all predecessor IDs + hashes | ✓ | Audit |
| **Audit: citation_to_operation_map** | computed | citation_id → operation_id mapping | ✓ | Audit |
| **Audit: integrity_verification** | computed | hash cross-link verification results | ✓ | Audit |

---

## 5. Target / Data-Need / Operation Mapping Authority

**Rule**: For each `request.target`, the `plan.operations[]` that:
1. Include that target's resolved `canonical_target_id` in `canonical_target_ids`, AND
2. Whose `capability_id` matches a `request.data_need.type`

...constitute the authoritative operation set for that `(target, data_need)` pair.

**Authority Source**: `plan.operations[]` × `preflight.resolved_operation_bindings`

---

## 6. Timestamp Authority

| Field | Source |
|-------|--------|
| `generated_at` | `receipt.finalized_at` (authoritative) or CLI `--calculated-at` |
| `citation.retrieved_at` | `bundle.finalized_at` (fallback) or per-artifact evidence `retrieved_at` |
| `audit.projector_run_at` | CLI `--calculated-at` |
| **Pure function constraint** | Builder must NOT call `datetime.now()` or `time.time()` |

---

## 7. Canonical Hash Implementation

Reuse `scripts/m8r_05b_03/canonical.py`:
- `canonical_json(value)` — deterministic JSON, `sort_keys=True`, no NaN
- `sha256_json(value)` — sha256 hex of canonical JSON

Do **not** create a second canonicalization algorithm.

---

## 8. Hash Topology (No Circular Reference)

```
Step 1: result_id = "umeresult-v1-" + sha256_json({request_id, receipt_id, bundle_id})[:20]
Step 2: Build canonical result body:
        - includes audit_reference.audit_package_id (pre-computed)
        - does NOT include result_hash yet
Step 3: result_hash = sha256_json(result_body_without_result_hash)
Step 4: Build audit_package body:
        - includes result_id, result_hash, result relative_path
        - does NOT include audit_package_hash yet
Step 5: audit_package_hash = sha256_json(audit_body_without_audit_package_hash)

audit_package_id = "umeap-v1-" + sha256_json({result_id, bundle_id})[:20]
```

Result does NOT contain `audit_package_hash` (only `audit_package_id` + `relative_path`). No circular reference.

---

## 9. Output Containment Conventions

```text
ai_context/unified_market_evidence_result.v1.json
ai_context/unified_market_evidence_result.v1.md
audit/unified_market_evidence_audit_package.v1.json
```

Rejection rules:
- Absolute paths (drive-rooted, UNC, unix `/`)
- Path traversal (`..` segments)
- Prefix collision containment bypass
- Symlink/reparse: fail-closed per M8R-03E-R5B policy

Promotion policy: **stage-before-promote, atomic rename, validate schemas and hashes before promotion**. On failure, expose no partially-promoted final package.

---

## 10. Compatibility Impact on Existing Fixtures

| Test file | Action required |
|-----------|----------------|
| `test_m8r_05a_preview_result_contracts.py::test_valid_result_full_success` | Update fixture — add `result_id`, `result_hash`, `generated_at`, `request_summary`, extended `audit_reference` |
| `test_m8r_05a_preview_result_contracts.py::test_valid_result_not_yet_published` | Same |
| `test_m8r_05a_preview_result_contracts.py::test_invalid_result_has_raw_payload` | **No change** — remains valid |

---

## 11. Proposed Production/Test File Inventory

### New Schemas
- `schemas/unified_market_evidence_result.v1.schema.json` — MODIFY (v1 in-place completion)
- `schemas/unified_market_evidence_audit_package.v1.schema.json` — NEW

### New Production Modules (`scripts/m8r_05c/`)
- `__init__.py`, `errors.py`, `canonical.py`, `models.py`
- `artifact_loader.py`, `lineage_resolver.py`, `evidence_projector.py`
- `derived_metrics.py`, `citation_builder.py`, `result_builder.py`
- `audit_package_builder.py`, `markdown_renderer.py`, `containment.py`, `cli.py`

### Modified Validators/Docs
- `scripts/validate_unified_market_evidence_contracts.py` — add `validate_audit_package`
- `docs/protocol/M8R_05A_UNIFIED_MARKET_EVIDENCE_CONTRACT.md` — record v1 completion

### New Tests/Fixtures
- `tests/fixtures/m8r_05c/` — deterministic test fixtures
- `tests/unit/test_m8r_05c_schema.py`
- `tests/unit/test_m8r_05c_determinism.py`
- `tests/unit/test_m8r_05c_projection.py`
- `tests/unit/test_m8r_05c_derived_metrics.py`
- `tests/unit/test_m8r_05c_citation_audit.py`
- `tests/unit/test_m8r_05c_containment.py`
- `tests/unit/test_m8r_05c_markdown.py`
- `tests/unit/test_m8r_05c_no_network.py`

### Modified Tests
- `tests/unit/test_m8r_05a_preview_result_contracts.py` — update 2 result fixtures

### Acceptance (Commit 5 only)
- `docs/acceptance/M8R_05C_IMPLEMENTATION_RESULT.json`
- `docs/acceptance/M8R_05C_IMPLEMENTATION_RESULT.md`

---

## 12. Stop Condition Evaluation

| Condition | Status |
|-----------|--------|
| request target → bundle operations mappable | ✅ Resolved via `plan.operations[].canonical_target_ids × capability_id` |
| operation → data_need mappable | ✅ Via `plan.operations[].capability_id` |
| artifact hash independently verifiable | ✅ Via `bundle.artifact_inventory[].sha256` |
| target identity sources no conflict | ✅ `plan.operations[].canonical_target_ids` is authoritative |
| requested vs unrequested evidence distinguishable | ✅ Compare `request.data_needs[].type` vs `operation.capability_id` |
| currentness/session semantics traceable | ✅ From evidence artifact content + bundle `finalized_at` |
| result/audit hash no circular reference | ✅ One-way topology designed |

> **Verdict: NO_STOP_CONDITIONS_TRIGGERED — proceed to Commit 2**

---

## 13. Explicit Non-Goals

- No market-data network calls
- No executor adapter invocation  
- No new authorization or claim creation
- No execution replay
- No evidence refresh or watchlist modification
- No MCP, FastAPI, frontend, or Workbench UI
- No AI investment answers, recommendations, rankings, target prices, or sentiment labels
- No new market-data sources
- No silent inference of missing evidence
- No transport raw payloads in AI-context result
- No secrets, credentials, tokens, cookies, or local absolute paths
- No roadmap pointer advancement to M8R-06 before owner acceptance
