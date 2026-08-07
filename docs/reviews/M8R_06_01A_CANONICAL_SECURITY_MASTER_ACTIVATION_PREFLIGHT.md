# M8R-06-01A Canonical Security Master Activation Preflight

## Decision

**BLOCKED**.
Principal decision: `BLOCKED_BY_MISSING_PRODUCTION_GRADE_IDENTITY_INPUT`

The current repository authority establishes the `tw-security-master-classifier` Skill as the canonical producer of identity and lifecycle evidence. M8R-03D-F1 provides a fully functional, verified snapshot adapter and exporter. However, no production-grade inputs currently exist in the repository. The only available snapshots and input records are fixture-only (`tests/fixtures/m8r_05a_f3/`), which are explicitly rejected in production Mode A (`allow_fixture_snapshot=False`).

### Task Sequencing

1. **Current Status**: `BLOCKED_BY_MISSING_PRODUCTION_GRADE_IDENTITY_INPUT`
2. **Next Authorized Task**: `M8R-06-01B-PRODUCTION-GRADE-IDENTITY-AND-LIFECYCLE-INPUT-QUALIFICATION`
3. **Future Task After B**: `M8R-06-01C-GOVERNED-SNAPSHOT-MATERIALIZATION-AND-MODE-A-ACTIVATION`
4. **M8R-06-02**: `NOT_AUTHORIZED`

## Required Investigation

### A. Canonical authority
1. Canonical owner: `tw-security-master-classifier` Skill.
2. Producer/exporter: `scripts/m8r_03d_f1_security_master_snapshot_exporter.py`
3. Input contracts: `ClassificationRecord` and `LifecycleEvent` schemas.
4. Input grade: Current repository inputs are fixture-only or missing.
5. Loader readiness: The loader (`scripts/m8r_05a_f3/security_master_loader.py`) is production-ready and fully validates hashes, schemas, and counts, but requires non-fixture input.

### B. Artifact and configuration design
**Recommendation:** Store immutable artifacts under a governed data/artifact directory and keep only pointers in `config/`.

**Exact pointer schema and paths:**
Create a new pointer file:
`config/m8r_06_mode_a_security_master_pointer.json`

Pointer Schema:
```json
{
  "snapshot_path": "data/security_master/snapshots/<snapshot_id>/snapshot.json",
  "manifest_path": "data/security_master/snapshots/<snapshot_id>/manifest.json"
}
```

*Semantics:*
- **Current pointer semantics**: `config/m8r_06_mode_a_security_master_pointer.json` specifies the active snapshot. Mode A config loading must be updated to read this pointer instead of hardcoding `config/production_security_master_snapshot.json`.
- **Rollback pointer semantics**: To rollback, the operator rewrites `config/m8r_06_mode_a_security_master_pointer.json` to point to a previous `<snapshot_id>` directory.
- **Atomic update order**: Write snapshot -> write manifest -> update pointer file.
- **Path traversal prevention**: Pointer paths must be strict relative paths constrained within the repository's data directory.

### C. Coverage policy
**Policy:** `governed_bounded_operator_universe`

The coverage mode is explicitly defined as `governed_bounded_operator_universe`. The snapshot must strictly define its coverage scope (e.g. `requested_scope`, `qualified_scope`, `excluded_scope`, `coverage_effective_date`, `coverage_hash`). Mode A is a request inspection tool; therefore, any target not found within the qualified scope will return `TARGET_OUTSIDE_GOVERNED_SNAPSHOT_COVERAGE` instead of a generic `not_found`. This ensures that unknown targets are clearly identified as falling outside the explicit operator watchlist boundaries, rather than implying they do not exist in the market.

### D. Freshness policy
**Thresholds and Operator Behavior:**

1. **`fresh`**: Freshness classes are approved; numeric thresholds remain unresolved and must be established during M8R-06-01B based on input source cadence.
   *Behavior*: Mode A inspection and target resolution are allowed after M8R-06-01C activation acceptance. Mode B preview remains NOT_AUTHORIZED until M8R-06-02 is separately implemented and accepted.
2. **`stale_but_inspectable`**: Snapshot is older than the `fresh` threshold but has not yet reached hard expiry.
   *Behavior*: Mode A inspection is allowed with an explicit warning caveat. Mode B remains not authorized independently of freshness.
3. **`expired_and_blocked`**: Snapshot has reached hard expiry.
   *Behavior*: Mode A returns a controlled blocker (e.g. `canonical_security_master_expired`).

### E. Activation gate
Mode A currently returns `HTTP 409 canonical_security_master_unavailable` because `config/production_security_master_snapshot.json` does not exist.

Activation requires successfully passing the following checklist:
1. `snapshot_schema_validation`
2. `manifest_schema_validation`
3. `snapshot_hash_verification`
4. `schema_hash_verification`
5. `skill_contract_hash_verification`
6. `record_hash_verification`
7. `coverage_reconciliation`
8. `lifecycle_count_reconciliation`
9. `fixture_only_rejection`
10. `validation_status == passed`
11. `startup-check success`
12. `production API acceptance success`
13. `focused tests success`
14. `default-ci closure`

### F. Rollback and failure behavior
The failure matrix explicitly defines stable reason codes for all failure modes to ensure UI and test stability:

* **Missing snapshot**: `canonical_security_master_unavailable`
* **Missing manifest**: `canonical_security_master_manifest_missing`
* **Hash mismatch**: `canonical_security_master_hash_mismatch`
* **Schema drift**: `canonical_security_master_schema_drift`
* **Skill contract drift**: `canonical_security_master_skill_contract_drift`
* **Expired snapshot**: `canonical_security_master_expired`
* **Fixture observation found**: `fixture_snapshot_rejected_in_production`
* **Duplicate canonical target**: `duplicate_canonical_target_id`
* **Identity conflict**: `identity_conflict_blocked`
* **Lifecycle conflict**: `lifecycle_conflict_blocked`
* **Malformed pointer**: `canonical_security_master_pointer_malformed`

## Evidence Commands

The following validations were executed to confirm the current repository state:

1. **Startup Check**
   *Command*: `python scripts/run_unified_workbench.py --startup-check`
   *Exit code*: `1`
   *Stdout/stable reason*:
   ```json
   {
     "status": "error",
     "message": "canonical_security_master_unavailable"
   }
   ```

2. **Focused Tests**
   *Command*: `pytest tests/unit/m8r_06_01/ tests/integration/test_unified_workbench_api.py -q`
   *Exit code*: `0`
   *Status*: `11 passed`

3. **Default CI Profile**
   *Command*: `python scripts/run_test_profile.py default-ci --json`
   *Exit code*: `1`
   *Status*: `fail`
   *Attribution*: `not_determined`
   *Merge gate*: `not_proven`

4. **Diff Check**
   *Command*: `git diff --check`
   *Exit code*: `0`
   *Status*: No trailing whitespace or conflict markers.
