# M8R-06-01C1R Runtime Identity Cache Realignment Preflight

**Task**: M8R-06-01C1R-RUNTIME-IDENTITY-CACHE-REALIGNMENT-PREFLIGHT  
**Baseline**: `05b3d44e5aeb27645eb0ccfc52d649cb53deecad`  
**Authorized Bundle**: `m8r06-01b-20260807T053540Z`

## Executive Summary

This preflight benchmark analyzed the feasibility of replacing the full verified Security Master snapshot (approximately 78.55 MiB) with a compact runtime identity index for Mode A consumption. The compact index, projected from the existing authorized bundle, achieved a 58.7% size reduction (to 32.41 MiB) while preserving all essential identity resolution semantics required by current consumers.

No semantic loss was detected in the canonical target ID set, security code mapping, ISIN mapping, Chinese/English name mapping, market, instrument type, execution eligibility, lifecycle summary, or source record traceability.

The compact index schema is a candidate for discussion and may enable more efficient runtime identity resolution without modifying the existing production Security Master generation or validation pipelines.

## Key Findings

- **Size Reduction**: 58.7% (48,383,590 bytes saved)
- **Compact Index Size**: 32.41 MiB (below the 50 MiB gate)
- **Record Count**: 43,070 identities preserved
- **Semantic Preservation**: All tested identity resolution dimensions preserved
- **Performance**:
  - Full snapshot JSON load: ~1.950 seconds
  - Compact index JSON load: ~0.776 seconds
  - Full lookup build: ~0.660 seconds
  - Compact lookup build: ~0.199 seconds
  - Compact projection: ~0.288 seconds
  - Compact serialization: ~0.848 seconds
  - Offline export processing (snapshot generation): ~1.136 seconds
- **Lookup Performance**: Compact index construction and lookup times comparable to full snapshot, with average lookup time of approximately 4.2 microseconds per operation

## Recommendation

The compact runtime identity index is viable for Mode A consumption. All reviewer concerns have been addressed, including:
1. Fixed lookup_equivalence() function to correctly handle single vs multi-record comparisons
2. Restored fail-closed bundle verification behavior
3. Verified all tests pass including synthetic lookup equivalence test
4. Confirmed benchmark runs successfully and produces correct semantic preservation results
5. Ensured fresh-clone portability via separated synthetic test file
6. Verified proper Chinese test data usage (台積電、聯發科、富邦金)
7. Confirmed commit history is clean and synchronized with remote
8. Used canonical adapter lookup for full-side equivalence comparison without modifying the adapter
9. Removed duplicate/unreachable code
10. Fixed benchmark artifact freshness measurement
11. Restored complete canonical bundle verification (including classification_records and lifecycle_events SHA verification)

The next step is to implement the compact index generation and integration (M8R-06-01C1B) after confirming the design with stakeholders.

## Benchmark Details

See `artifacts/m8r_06_01c1r/benchmark_results.json` for raw measurements.

## Artifacts Generated

- `scripts/m8r_06_01c1r_runtime_identity_cache_benchmark.py` - Benchmark script
- `tests/unit/test_m8r_06_01c1r_runtime_identity_cache.py` - Unit tests for the projection logic
- `tests/unit/test_m8r_06_01c1r_runtime_identity_cache_synthetic.py` - Synthetic test for fresh-clone portability
- `artifacts/m8r_06_01c1r/compact_identity_index.json` - Compact index output (not committed)
- `artifacts/m8r_06_01c1r/benchmark_results.json` - Benchmark results (not committed)

## Open Questions

- Whether the compact index size (32.41 MiB) meets the runtime memory constraints for deployment.
- Whether any additional fields beyond those projected are required by undiscovered consumers.
- The optimal update strategy for the compact index (e.g., lazy rebuild, versioned snapshots).

## Status

**PASS_WITH_CAVEATS**

**Principal Decision**: READY_FOR_COMPACT_RUNTIME_IDENTITY_INDEX_IMPLEMENTATION

**Recommended Next Task**: M8R-06-01C1B-COMPACT-RUNTIME-IDENTITY-INDEX-IMPLEMENTATION

**Unauthorized Tasks**: M8R-06-01C2, M8R-06-02