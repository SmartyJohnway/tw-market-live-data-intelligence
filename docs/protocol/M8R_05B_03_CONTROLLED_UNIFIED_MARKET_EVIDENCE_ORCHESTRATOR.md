# M8R-05B-03 Controlled Unified Market Evidence Orchestrator

## Current Implementation Stage: Commit 2 Boundary

Current head implements Commit 1 preflight and Commit 2 atomic authorization claim and controlled sequential dispatch. It validates a 05B-01 plan, a 05B-02 execution authorization, a 05B-02 consumption binding, explicit unused consumption state, a closed executor metadata registry, and governed output containment.

Upon successful preflight validation, Commit 2 executes an atomic compare-and-set claim (`unused` -> `claimed`) on the filesystem before dispatching approved, bounded execution requests to explicitly injected runtime adapters.

Current head does not implement evidence aggregation, final execution receipt creation, or final bundle generation (reserved for Commit 3).

## Public Entry Points

```python
from scripts.m8r_05b_03 import (
    RuntimeAdapterRegistration,
    RuntimeAdapterRegistry,
    build_orchestrator_preflight,
    claim_and_dispatch_approved,
)
```

## Atomic Authorization Claim

The authorization claim transitions the consumption state from `unused` to `claimed` via `atomic_create_text_exclusive`. It creates a `unified_market_evidence_consumption_record.v1` artifact.

Key invariants:
* Preflight identity hash and artifact hash must be valid.
* Supplied state must be `unused`.
* Authorization, binding, plan, and scope must match preflight.
* Atomic claim is compare-and-set (replay attempts or duplicate claims fail closed).

## Controlled Dispatch Boundary

Sequential dispatch invokes explicitly registered runtime adapters with bounded request projections.
* Runtime adapter registry is explicitly constructed by trusted code and never loaded from untrusted input artifacts.
* Adapters receive bounded execution requests only (no scope or target expansion).
* Network calls are forbidden during unit tests / dry-run mode.

## Future Commits

Commit 3 may implement aggregation, final execution receipts, and final consumption state transitions after Commit 2 behavior is reviewed and accepted.
