# M8R-08G-01 — Identity Service and local release realignment

Baseline: `f774c543a3d8fc41abab8551669c454b40a1be71`
Branch: `codex/m8r-08g-01-identity-service-local-release-realignment`

## Decision

The Taiwan Market Identity Service is now the release-bound, read-only identity
boundary for cash-market records.  ISIN is the durable `instrument_id`; the
existing `MARKET:CODE` value remains the `listing_id` and v1
`canonical_target_id` used for listing and execution routing.  Exact ISIN,
scoped code, normalized name, and governed alias lookup are supported.  No
fuzzy lookup selects a winner.

The knowledge universe remains broad.  Known cash records resolve even when
their instrument type is not executable; such records are returned with
`unsupported_instrument_type`.  `common_share` and `etf` records remain
eligible except where an independent lifecycle block is already present.

## Installation-local release lifecycle

`data/security_master/active.json` is the installation-local active selector.
It is intentionally ignored by Git, as are local releases, rejected releases,
and acquired input bundles.  A clean installation without it returns the
explicit legal state `NOT_INITIALIZED`; it never falls back to Candidate B.

Releases are built with immutable index, qualification, manifest, and release
bytes.  The manifest records `BUILDING`, `CANDIDATE`, and `QUALIFIED` history;
the active pointer is atomically replaced only after hash validation.  Rejected
and retired release diagnostics are retained locally.  Rollback selects a
previous qualified release; retired or rejected releases cannot be activated.
An already loaded Mode A selection remains immutable for the lifetime of its
process and a pointer change requires restart.

Lifecycle evidence is append-only: snapshot absence is not termination.  An
official ISIN successor produces `IDENTITY_MIGRATION_REVIEW_REQUIRED` with the
predecessor, successor, event, and evidence; it never rewrites an existing
instrument identity.

## Consumer compatibility

Mode A defaults to the installation-local active release.  The prior compact
pointer loader remains an explicit non-production test/migration adapter only.
F3 carries additive `instrument_id`, `listing_id`, execution eligibility, and
release provenance while preserving `canonical_target_id`.  B1 planning and
Mode C audit lineage use local release references when selected.  Local Service
and Unified MCP continue to consume the same Mode A/F3 boundary; their request
contract is not replaced.

Candidate B remains historical evidence only.  Its stored Skill-contract hash
is producer-time provenance; active local-release validation verifies persisted
release hashes and does not recompute the current working-tree classifier Skill.
Future releases bind the Skill contract present when they are produced.

## Pre-correction local live diagnostic

One explicitly authorized official acquisition was attempted.  Its governed
materialization report recorded five successful transports, 46,635 qualified
records, and `READY_FOR_GOVERNED_SNAPSHOT_MATERIALIZATION`.  The pre-existing
materializer returned non-zero after producing the qualified local snapshot, so
the new CLI did not activate through `update --live`.  The same locally
qualified snapshot was then supplied explicitly to the pre-correction
`update --records` path, without another network request.  It created and activated
`security-master-20260907T075809Z` (46,635 records; manifest
`4d8662b96d07b1bfc8499e4a35d47335d7d38e970efe6e33bab2b9a0a2b28590`).
It is retained only as a **PRE_CORRECTION_LOCAL_DIAGNOSTIC**, not corrected
release-governance acceptance.

Offline smoke validation through this active release resolved TWSE 2330 and
TPEX 6488 using their ISIN instrument identities while preserving their listing
routing IDs.  The active projection contains 1,971 normally eligible common
shares, three independently lifecycle-blocked common shares, and 360 eligible
ETFs.  A known preferred share remained identity-resolvable and blocked with
`unsupported_instrument_type`.

## Verification

- New deterministic identity/lifecycle/release tests: `12 passed`.
- Focused F3, Mode A, B1, Unified Workbench, B2, Mode C status/handoff, MCP,
  and M8R-08F compatibility surface: `203 passed, 2 skipped` in the final
  focused regression run.
- The historically recorded Mode C lineage-fixture `artifact_hash_mismatch`
  debt was not independently re-baselined in this correction.
- `python -m compileall scripts server tests`, both changed schema JSON parses,
  and `git diff --check` passed.

Phase F has not started.  The remaining follow-up is the separately governed
Skill/AI-guide portability closure, not persistent watchlist implementation.

## Governance correction

Principal review found that the original release constructor could label an
arbitrary list `QUALIFIED`.  This has been removed.  New releases now pass
through `CANDIDATE → validate_release_candidate → qualification report →
QUALIFIED|REJECTED`; activation accepts only a persisted PASS report validated
against the canonical release schemas.  Candidate validation rejects invalid or
mismatched cash ISINs, duplicate listing/canonical/instrument identities,
invalid JSON-schema shape, and unsupported lifecycle contradictions.  Rejected
diagnostics are created by failed qualification and leave Active unchanged.

Eight repository schemas now govern the candidate, record, index, qualification
report, manifest, immutable qualified release, local lifecycle status, and
active pointer.  The manifest binds schema hashes, repository
commit, producer version and Skill hash, source content hashes, counts, index
hash, and qualification-report hash.  `listing_history` is no longer fabricated
from a snapshot date; current observation is separate from supported listing
history.

The correction's single bounded `update --live` attempt failed closed because
the TWSE ISIN mode 2 and mode 4 acquisition attempts encountered `URLError`.
It created no corrected Active release and did not fall back to the
pre-correction local release.  Accordingly the implementation and offline
contract checks pass, but live bootstrap acceptance is classified
**LIVE_BOOTSTRAP_EXTERNALLY_UNVERIFIED_FAIL_CLOSED**; this does not assert a
TWSE outage.

The deterministic candidate, qualification, schema, trusted-provenance, and
one-command update contracts are independently covered. `--records` is now an
explicit non-production diagnostic path: self-asserted record provenance cannot
activate production. Strict legacy migration accepts only a Mode A loader
validated pointer/seal/index/manifest lineage and retains its historical source
hashes rather than deriving authority from a reserialized index. Temporary
external reachability is not an implementation-merge blocker.
