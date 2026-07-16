# M8 Remediation and Cleanup Plan

Baseline SHA: `bd3496efe7492e6cd3c7dacc169e142f90e6cd92`.

## R2 critical correctness/security remediation

Task: `M8R-03E-R2-CRITICAL-CORRECTNESS-AND-SECURITY-REMEDIATION`. Scope: P0/P1 correctness, authorization bypass, unsafe filesystem/network handling, data corruption, hash/lineage defects, and secret/raw-payload leakage. Current R1 evidence recommends output-root/symlink/path containment hardening.

## R3 architecture/code-health cleanup

Task: `M8R-03E-R3-ARCHITECTURE-AND-CODE-HEALTH-CLEANUP`. Scope: module boundaries, duplicate helpers, status/reason-code centralization, typed boundaries, obsolete conversation logic, suspected-orphan code, and maintainability.

## R4 performance/scalability baseline and hardening

Task: `M8R-03E-R4-PERFORMANCE-BASELINE-AND-SCALABILITY-HARDENING`. Scope: deterministic benchmarks for 1/10/50/100 targets, high citation and missing-evidence pressure, snapshot/performance bundles, partial source failure, schema caching, hash reuse, indexing, large-watchlist behavior, and resource limits.

## R5 testing/documentation/operations consolidation

Task: `M8R-03E-R5-TESTING-DOCUMENTATION-AND-OPERATIONS-CONSOLIDATION`. Scope: cross-layer tests, property tests, fixture/live taxonomy, documentation lifecycle labels, operations runbooks, and archive/superseded organization.
