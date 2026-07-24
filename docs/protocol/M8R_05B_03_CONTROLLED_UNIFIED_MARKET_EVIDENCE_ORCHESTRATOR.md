# M8R-05B-03 Controlled Unified Market Evidence Orchestrator

## Commit 1 Boundary

Current head implements contracts and preflight only. It validates a 05B-01 plan,
a 05B-02 execution authorization, a 05B-02 consumption binding, explicit unused
consumption state, a closed executor metadata registry, and governed output
containment. It then produces one deterministic
`unified_market_evidence_orchestrator_preflight.v1` artifact.

Current head does not claim authorization, create consumption records, mutate
durable state, invoke executors, invoke source adapters, aggregate runtime
evidence, produce final execution receipts, finalize consumption, create queues,
write databases, or perform network access.

`ready_for_claim=true` means only that a later layer may attempt an atomic claim
after this preflight artifact is reviewed. It is not a claim and is not evidence
that execution occurred.

## Public Entry Point

The public package entry point is:

```python
from scripts.m8r_05b_03 import build_orchestrator_preflight
```

`execute_controlled_plan` is intentionally absent from Commit 1.

## Preflight Artifact

The preflight artifact includes immutable plan, authorization, binding, and
scope identifiers; approved operation order; resolved operation, batch, and
executor metadata bindings; bounded execution-request projections; network and
authorization booleans; governed output root; containment status; warnings;
blocking errors; and `created_by_component`.

The `preflight_identity_scope` excludes wall-clock fields. The evaluation
timestamp is used only to reuse the 05B-02 expiry/preflight checks.

## Executor Metadata Registry

Commit 1 accepts only closed executor metadata entries. A registry entry contains
`executor_id`, `capability_id`, `market`, `supported_security_types`,
`expected_evidence_contract`, `network_required`,
`bounded_execution_supported`, `timeout_seconds`, `maximum_result_items`, and
`output_policy`.

No callable adapter is accepted or stored by the registry. Unknown executors,
capability mismatch, market mismatch, unsupported security types, evidence
contract mismatch, network-required executors without authorization, unbounded
executors, invalid limits, and unsupported output policies are rejected before
`ready_for_claim`.

## Bounded Request Projection

For each approved operation, Commit 1 builds and schema-validates a deterministic
`unified_market_evidence_execution_request.v1` projection. The request contains
only closed approved fields and a deterministic contained relative output path.
It is not sent to any adapter.

Unavailable source fields, such as absent `requested_fields` or currentness
requirements, are reported as warnings instead of being invented.

## Output Containment

Preflight requires an existing absolute governed output root and deterministic
relative operation paths. It rejects absolute artifact paths, rooted paths, drive
relative paths, URI-like paths, `..` traversal, symlink escape, frontend-public
destinations, registry/source-controlled repository paths, and path collisions.
It does not create directories or files.

## Future Commits

Commit 2 may implement atomic claim and controlled dispatch, using this preflight
artifact as input. Commit 2 must remain fail-closed and must not expand scope.

Commit 3 may implement aggregation, final execution receipts, and final
consumption state transitions after Commit 2 behavior is reviewed and accepted.
