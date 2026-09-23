# Source and Capability Model

The current product separates four concepts that must not be collapsed:

```text
Identity
Source Authority
Capability Contract
Executable Route
```

## Identity

The installation-local Security Master knows instruments and eligibility.
For cash securities, ISIN is durable identity and `MARKET:CODE` is the
listing/routing identity.

A known identity does not imply that every capability can execute.

## Source authority

Sources are evaluated by authority, transport, timing semantics, coverage,
license/usage constraints, target binding, failure behavior, and persistence
policy.

Official does not automatically mean realtime.

## Capability contract

The V3 Capability Catalog declares the semantic capability vocabulary and its
support status.

A `contract_supported` capability may be understood by the product while
remaining non-executable.

## Executable route

The V3 routing matrix plus executor registry determines the currently executable
subset.

Example: `trading_status_context` has TWSE/TPEX semantic scope, but current
Phase H route activation contains only the TPEx attention route. Therefore TPEx
attention is executable while unsupported/unactivated route combinations fail
closed.

## Evidence semantics

Every executable source path should preserve:

- target identity;
- source contract/family;
- source/effective/published/observed time where applicable;
- coverage;
- currentness;
- missing/failure distinctions;
- fallback use;
- citation/lineage;
- bounded persistence.

See [Source Matrix](../reference/SOURCE_MATRIX.md) and
[Capability Matrix](../reference/CAPABILITY_MATRIX.md).
