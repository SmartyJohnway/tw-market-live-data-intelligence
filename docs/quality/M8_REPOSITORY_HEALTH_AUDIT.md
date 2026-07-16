# M8 Repository Health Audit

Baseline SHA: `bd3496efe7492e6cd3c7dacc169e142f90e6cd92`.

## Executive conclusion

Disposition: **GO_WITH_CAVEATS**. Registry and roadmap contradictions that were low-risk were corrected. No P0 data-correctness blocker was verified, but P1 security/architecture risks remain bounded in R2/R3 and should be addressed before broad tool/API expansion. Phase B may proceed if it does not expand runtime trust boundaries.

## Architecture

Verified fact: M8R-03E builders project 03C/03D/03D-F1 evidence into deterministic packages. Audit inference: the current package exposes too much internal 03C/03D/03E complexity for an eventual simple AI-facing tool API. Recommended future work: Phase C should wrap existing layers instead of exposing internals directly.

## Code health

Largest Python files: `scripts/observation_contract.py` (1679 lines), `scripts/m5k_common.py` (1091), `server/mcp_server.py` (966), `scripts/m8r_ai_market_context_package.py` (798), `scripts/m8_multi_source_context_builder.py` (693). Largest functions include `normalize_yahoo_chart_result` (~214 lines), `build_multi_source_market_context` (~188), and `normalize_twse_mis_row` (~169). Wildcard imports and broad `except Exception` sites remain.

## Security

Verified fact: M8R-03E CLI rejects URL-like input and uses atomic writes. Audit inference: output root safety is incomplete for absolute paths/symlink containment, so R2 should harden path canonicalization before expanding write surfaces. Network execution remains controlled by existing authorization paths; this audit did not authorize live network calls.

## Performance

Baseline observation: current fixture tests are small and passing, but code inspection found repeated canonical serialization and citation scans under budget enforcement. Deterministic benchmark scenarios required for 1/10/50/100 targets, high citation pressure, high missing-evidence pressure, snapshot/performance bundles, and partial source failure are scheduled in R4.

## Testing

Unit tests cover M8, M8R-01/02/03B/03C/03D/03D-F1/03E contracts and fixtures. Gaps remain for producer/consumer compatibility, duplicate JSON keys, large/deep malformed inputs, path/symlink safety, and schema-version migration.

## Documentation

Documentation lifecycle classification: active protocol and data-capability files are normative/informational active; older reviews are historical; M8R-04 broad automation is superseded; M8R-03E AI-behavior fields are deprecated pending migration. Future hierarchy should consolidate roadmap, architecture, AI, quality, operations, and archive areas without mass moves in R1.

## AI behavior policy decoupling

Direct R1 correction records AI behavior hardcoding as deprecated direction in the registry. Compatibility-sensitive fields remain in M8R-03E contracts and are inventoried for migration to evidence-oriented fields. Data semantics such as currentness, timing class, official EOD/current observation, coverage, missing evidence, identity, source authority, and lineage remain strict.

## Blocking findings

No P0 findings. P1 security hardening for filesystem containment is recorded as a Phase-B condition if Phase B would expand artifact writes; otherwise R2 can proceed in parallel.

## Non-blocking debt

P2/P3 debt includes oversized modules, wildcard imports, broad exceptions, performance baselines, edge-case tests, and documentation lifecycle cleanup.

## Recommended successor

Recommended next task: `M8R-03E-F1-AI-CAPABILITY-GUIDE-AND-AGENT-SKILL-CONTRACT`, because no blocking P0 was verified and R2 is reserved for bounded P1 security hardening rather than a full Phase-B stop.

## Validation results recorded during R1

- `git diff --check`: pass.
- `python -m compileall scripts server tests skills`: pass.
- `python scripts/governance_forbidden_path_guard.py`: pass, no findings.
- `python scripts/forbidden_behavior_scanner.py`: pass, 187 checks and 0 failures.
- `python skills/tw-security-master-classifier/scripts/validate_skill.py`: pass.
- `pytest tests/unit/test_m8*.py -q`: pass, 579 tests.
- `pytest tests/unit/test_m8r_01*.py -q`: warning, no matching files in this checkout.
- `pytest tests/unit/test_m8r_02*.py -q`: pass, 13 tests.
- `pytest tests/unit/test_m8r_03b*.py -q`: pass, 32 tests.
- `pytest tests/unit/test_m8r_03c*.py -q`: pass, 16 tests.
- `pytest tests/unit/test_m8r_03d*.py -q`: pass, 26 tests.
- `pytest tests/unit/test_m8r_03d_f1*.py -q`: pass, 18 tests.
- `pytest tests/unit/test_m8r_03e*.py -q`: pass, 39 tests.
- `python scripts/run_test_profile.py default-ci --json`: pass, 721 tests.
- `python scripts/run_test_profile.py full-non-network --json`: failed with 1621 passed, 7 failed, 1 skipped. The failing cluster is the existing M5D/M5E frontend-public publication candidate baseline drift (`frontend_public_baseline_drift`), not a new runtime market-evidence code failure. This is recorded as R5 documentation/operations consolidation evidence unless future investigation shows artifact integrity impact.
