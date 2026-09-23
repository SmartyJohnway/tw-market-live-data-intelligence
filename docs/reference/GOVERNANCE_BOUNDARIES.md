# Governance Boundaries

## Product boundary

TW-Market is a governed evidence service. It is not a broker, trading engine,
investment-advice engine, general crawler, or autonomous monitor.

Forbidden unless a future explicitly governed contract changes the boundary:

- trading / order routing;
- broker credential handling;
- hidden startup market fetch;
- default scheduler or polling;
- silent background refresh;
- unbounded crawl or full-market scan;
- silent persistent mutation;
- silent identity migration;
- fixture fallback as production authority;
- unsupported realtime guarantee;
- parallel identity/request/result/execution cores.

## Authorization boundary

```text
Validate != Preview
Preview != Authorization
Authorization != Execution
```

Execution must be target/capability bounded, explicit, single-use where
specified, and auditable.

## Identity boundary

For supported cash securities:

- ISIN = durable instrument identity;
- `MARKET:CODE` = listing/routing identity;
- names/aliases = metadata.

Knowledge universe does not imply execution universe.

## Contract boundary

Current preferred Unified Request/Result/Audit is V3. V1/V2 remain
compatibility contracts. A schema being accepted does not make every capability
or source route executable.

The current Phase H active route set is incremental. Do not infer complete H1,
H2, or H3 coverage from V3 promotion.

## Evidence boundary

Preserve source, target binding, timing, currentness, coverage, missing/failure,
fallback, citation, lineage, and raw-artifact policy.

Distinct states must remain distinct:

- missing;
- unknown;
- not published;
- unsupported;
- source failed;
- stale;
- not applicable.

Missing is not zero. Source failure is not "no evidence".

## Persistence boundary

Persistent Watchlists mutate only through explicit governed mutation flow.
Conversation-local targets do not silently persist.

## Network boundary

Default deterministic CI and ordinary startup are non-network. Live acquisition
requires explicit bounded authorization. Live probing must not silently evolve
into monitoring.

## Documentation boundary

Historical acceptance/protocol/review documents preserve what was true at their
gate. Do not globally replace old state words such as "V2 preferred" inside
accepted history. Current-state truth belongs in current root/reference/operator
documents and current machine authority.
