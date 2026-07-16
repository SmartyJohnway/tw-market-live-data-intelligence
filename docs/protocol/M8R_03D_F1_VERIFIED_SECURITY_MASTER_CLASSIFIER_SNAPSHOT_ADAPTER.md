# M8R-03D-F1 Verified Security-Master Classifier Snapshot Adapter

## Decision

**M8R-03D-F1 = GO_WITH_CAVEATS.** The repository now has a non-network producer/consumer path from the verified `tw-security-master-classifier` Skill contract into M8R-03D planning. Caveats remain: snapshot generation is manual, live Skill probing is not scheduled, and fixture coverage is partial and not living market truth.

## Producer-consumer architecture

The Skill remains the canonical owner of official identity evidence, taxonomy, bilingual lane merge, quarantine rules, lifecycle event semantics, and observation provenance. M8R-03D consumes only a bounded, versioned snapshot:

```text
Skill ClassificationRecord + LifecycleEvent inputs
→ tw_verified_security_master_snapshot.v1
→ tw_verified_security_master_snapshot_manifest.v1
→ strict loader + lookup index
→ m8r_03d_f1_security_identity_resolution.v1
→ M8R-03D source-route planner
```

Normal watchlist requests do **not** invoke Skill probes, source scraping, lifecycle pages, or market-wide classification.

## Snapshot schema

The snapshot schema is `tw_verified_security_master_snapshot.v1`. Top-level fields are `snapshot_id`, `generated_at_utc`, `effective_observation_date`, `source_skill`, `coverage`, and `records`. Each record carries bounded identity, canonical Skill classification taxonomy, observation provenance, derived lifecycle view, execution eligibility, evidence summary, conflicts, caveats, and `record_hash`.

Raw HTML cells and full official payloads are forbidden in runtime snapshots.

## Manifest schema and integrity

The manifest schema is `tw_verified_security_master_snapshot_manifest.v1`. It records `snapshot_sha256`, `schema_sha256`, `skill_contract_hash`, producer version, record counts, lifecycle event counts, coverage, and `validation_status`.

The loader fails closed when schema versions drift, producer versions are unsupported, schema hashes mismatch, snapshot hashes mismatch, generated/effective timestamps differ between manifest and snapshot, record or lifecycle event counts mismatch, snapshot IDs mismatch, coverage differs, Skill contract hashes mismatch, record hashes mismatch, duplicate canonical target IDs appear, unresolved duplicate ISIN identities are detected, forbidden raw fields appear, or `validation_status != passed`. By default it also requires `manifest.skill_contract_hash` to match the current repository Skill contract hash. Historical pinned snapshots may be accepted only by an explicit compatibility caller that sets `require_current_skill_contract=False`; this is for audit/replay, not production watchlist execution.

## Classification mapping

Skill markets `twse` and `tpex` map to `TWSE` and `TPEX`. Other Skill markets remain representable but are not automatically executable in M8R-03D. Instrument types are preserved without collapsing preferred shares, ETFs, warrants, bonds, derivatives, STOs, or unknown instruments into generic equity.

Runtime execution is initially eligible only for `common_share` and `etf` when classification and lifecycle policy allow it.

## Classification status policy

`confirmed_dual_lane` and `confirmed_official_single_lane` are potentially eligible. `provisional_single_lane` is allowed only with explicit caveats. `quarantine_conflict`, `quarantine_unknown`, hard classification conflicts, and identity conflicts block current execution.

Adapter results expose `classification_resolution_status` and `classification_execution_policy`.

## Observation provenance policy

`observed_in_latest_verified_snapshot` is accepted as current snapshot provenance. `observed_in_capture` carries a freshness caveat. `fixture_observation_only` is rejected in production execute mode unless `allow_fixture_snapshot=True`. `historical_capture` is historical only and does not authorize current execution.

## Lifecycle derivation

Lifecycle events are preserved. The adapter derives a current view without flattening event dates. Explicit effective termination, maturity, and suspension events block or caveat execution according to M8R-03D policy. Missing lifecycle evidence remains `unknown`; absence of a termination event is never treated as proof of active trading. Current verified observation may produce `active_with_current_observation_basis` with an explicit evidence-qualified caveat.

## Runtime resolution

The resolver supports canonical IDs, exact ISIN, exact code with market context, exact normalized Chinese or English names, and ambiguous candidate reporting. Fuzzy candidates are not auto-selected. Ambiguous, quarantined, fixture-only production, and market-mismatch outcomes block planning.

## M8R-03D planner integration

`build_execution_plan` accepts a `ValidatedVerifiedSecurityMasterSnapshot` object or explicit snapshot/manifest paths. Plain dict snapshot/lookup injection is rejected for verified evidence; legacy bounded seed dictionaries remain only for existing test/backward-compatibility paths. Invalid configured snapshots raise an adapter error and do not fall back to the bounded seed. Planned targets retain `snapshot_id`, `record_id`, `record_hash`, classification status, lifecycle state, execution eligibility, and resolution evidence references.

## Fixture policy

Fixtures under `tests/fixtures/m8r_03d_f1/` are regression evidence only. They are explicitly not living truth and must not enter production execute mode unless a test or diagnostic explicitly sets `allow_fixture_snapshot=True`.

## Failure modes

- Invalid manifest/hash/schema: fail closed.
- Quarantine/conflict: block current execution.
- Unsupported instrument: block current execution.
- Terminated/matured/suspended lifecycle: no current source route.
- Unknown lifecycle: explicit caveat policy.
- Fixture-only observation: production rejection by default.

## GO criteria status

The implementation consumes Skill contracts without duplicating taxonomy, exports deterministic snapshots, validates manifest/hash integrity, preserves quarantine and lifecycle evidence, blocks fixture-only records by default, and integrates with M8R-03D planning. Remaining caveats are manual snapshot production and partial fixture coverage.

## Next task

If accepted, the recommended next task is `M8R-03E-WATCHLIST-AI-CONTEXT-PACKAGE-AND-CONVERSATION-HANDOFF`. Do not begin M8R-03E in this PR.
