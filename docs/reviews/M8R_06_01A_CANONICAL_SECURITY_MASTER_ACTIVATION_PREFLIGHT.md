# M8R-06-01A Canonical Security Master Activation Preflight

## Decision

**BLOCKED**.
Principal decision: `BLOCKED_BY_MISSING_PRODUCTION_GRADE_IDENTITY_INPUT`

The current repository authority establishes the `tw-security-master-classifier` Skill as the canonical producer of identity and lifecycle evidence. M8R-03D-F1 provides a fully functional, verified snapshot adapter and exporter. However, no production-grade inputs currently exist in the repository. The only available snapshots are fixture-only (`tests/fixtures/m8r_05a_f3/`), which are explicitly rejected in production Mode A (`allow_fixture_snapshot=False`).

## Required Investigation

### A. Canonical authority
1. Canonical owner: `tw-security-master-classifier` Skill.
2. Producer/exporter: `scripts/m8r_03d_f1_security_master_snapshot_exporter.py`
3. Input contracts: `ClassificationRecord` and `LifecycleEvent` schemas.
4. Input grade: Current repository inputs are fixture-only or missing.
5. Loader readiness: The loader (`scripts/m8r_05a_f3/security_master_loader.py`) is production-ready and fully validates hashes, schemas, and counts, but requires non-fixture input.

### B. Artifact and configuration design
**Recommendation:** Store immutable artifacts under a governed data/artifact directory and keep only pointers in `config/`.
*Why:* Snapshots will rotate. Committing full JSON snapshots directly to `config/` bloats the configuration path and mixes volatile market data with static configuration. By keeping only a pointer (`snapshot_path` and `manifest_path`) in `config/` and storing the snapshots elsewhere (e.g., `data/snapshots/`), we preserve a clean configuration boundary.

### C. Coverage policy
**Policy:** Bounded operator/watchlist universe initially, expanding to full current-active universe.
*Why:* For Mode A to provide value, it must at least cover the bounded target universe of current executing operators. If a target is not found, Mode A fails closed. The distinction between TWSE and TPEX is maintained strictly in the snapshot taxonomy.

### D. Freshness policy
* `generated_at_utc`: The exact time the exporter was run.
* `effective_observation_date`: The logical date of the source state.
* Behavior: Hard-expiry is currently not strictly enforced in the schema beyond manual rotation (snapshots are manually refreshed). Stale-but-usable requires explicit operator caveats.

### E. Activation gate
Mode A currently returns `HTTP 409 canonical_security_master_unavailable` because `config/production_security_master_snapshot.json` does not exist.
The offline startup check (`python scripts/run_unified_workbench.py --startup-check`) predictably fails with exit status `1` and stable failure code `canonical_security_master_unavailable`.

Activation requires:
1. Valid production-grade snapshot and manifest available at the configured path.
2. All hash, schema, and coverage reconciliations passing.
3. Startup check (`scripts/run_unified_workbench.py --startup-check`) succeeding.

### F. Rollback and failure behavior
Missing snapshots, hash mismatches, or fixture-only rejections all result in an immediate fail-closed state (HTTP 409). If the target is ambiguous, the resolver explicitly fails.

## Next Task
M8R-06-01B-GOVERNED-SECURITY-MASTER-MATERIALIZATION-AND-MODE-A-ACTIVATION

This task will materialize the production snapshot into the data directory, update the configuration pointer, and activate Mode A validation.
