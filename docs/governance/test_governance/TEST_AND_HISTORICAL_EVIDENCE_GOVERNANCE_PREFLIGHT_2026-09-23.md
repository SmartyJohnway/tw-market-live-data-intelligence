# Test & Historical Evidence Governance Preflight — 2026-09-23

Baseline main: `b42c73057a16ea39d73ed7efd8c96096ee49e131`

Status: **PREFLIGHT / INVENTORY ONLY**

Scope boundary:

> This workstream reorganizes test and historical-evidence governance. It does
> not implement Roadmap Phase I, does not change market-source activation, and
> does not reduce product safety semantics merely to lower the test count.

## 1. Why this preflight exists

The repository now has a clean documentation/governance front door, but the
test suite still carries multiple generations of milestone-specific governance
inside the normal PR merge path.

The immediate problem is not raw test runtime. The accepted documentation
consolidation ran 1,245 selected tests in about 30 seconds. The problem is
**temporal and authority coupling**:

- current runtime regressions;
- compatibility regressions;
- historical milestone reproduction;
- release provenance;
- human-readable prose/navigation assertions;

are partially mixed into the same default CI authority.

That produces **governance fossilization**: historically correct tests can
prevent legitimate current documentation or architecture governance changes.

## 2. Baseline facts

At this baseline:

- repository test Python files: **388**;
- unit test files: **358**;
- integration test files: **7**;
- acceptance archive Python files: **1**;
- current `default-ci` explicitly lists **156 test files**;
- accepted documentation consolidation selected **1,245 tests**;
- result: **1,241 passed, 4 skipped, 9 deselected**;
- `pytest.ini` already defines `core`, `contract`, `default_ci`,
  `historical`, `milestone`, component markers, network/browser/live and
  other useful classes;
- repository search found no normal use of `@pytest.mark.default_ci`;
- repository search found no normal use of `@pytest.mark.core`;
- historical marker use is very sparse;
- `default-ci` therefore currently behaves primarily as a manually maintained
  explicit path list rather than a semantic test policy.

Approximate path composition of the current 156-file default list:

| Family | File count |
|---|---:|
| M5/M6-prefixed | 15 |
| M7-prefixed | 33 |
| pre-M8R M8/M8A/M8B/M8C | 41 |
| M8R | 22 |
| Phase G | 11 |
| Phase H | 8 |
| filenames containing acceptance/closure/preflight semantics | 18 |

These groups overlap conceptually; they are not intended to sum to 156.

## 3. Concrete debt observed during repository governance consolidation

Two Run #14 failures illustrate the problem.

### Historical filename navigation coupled to current docs

`tests/unit/test_m8_through_m8b_consolidated_acceptance.py` required
`docs/INDEX.md` to contain the exact filename
`M8_THROUGH_M8B_CONSOLIDATED_FINAL_ACCEPTANCE.md`.

The historical artifact should remain protected and discoverable, but an old
milestone test should not indefinitely dictate the exact information
architecture of the current documentation index.

### Natural-language release prose treated as machine contract

`scripts/validate_v1_public_contracts.py` validates stable-release truth by
requiring specific README phrase patterns, including a specific Phase G
acceptance phrase.

Release truth should remain protected, but stable structured release metadata
is preferable to freezing prose formulation.

## 4. Governance objective

Create a test system in which:

```text
CURRENT PRODUCT TESTS
    protect current behavior and current authoritative contracts

COMPATIBILITY TESTS
    protect explicit supported backward-compatibility promises

HISTORICAL ACCEPTANCE
    preserves/reproduces earlier milestone evidence without controlling current
    documentation or runtime architecture

RELEASE / FROZEN EVIDENCE
    protects immutable accepted artifacts primarily through manifest/hash/
    schema checks, with full reproduction available separately

LIVE / BROWSER / PERFORMANCE
    remain explicit, bounded, non-default execution profiles
```

The goal is **not** a target number of tests.

A future repository with 1,200 well-classified tests is preferable to one with
600 tests whose time/authority semantics remain mixed.

## 5. Non-goals

This workstream must not:

- delete tests merely to reduce count;
- weaken security, fail-closed, identity, bounded-execution or source-failure
  semantics;
- rewrite accepted historical ledgers;
- mutate frozen schemas;
- change current market-source activation;
- change the six-tool MCP boundary;
- change product runtime behavior as a side effect;
- implement Phase I;
- introduce live network into default CI.

## 6. Proposed test classes

Every test file/test should ultimately have one primary governance role.

### A. CURRENT_CORE

Permanent current product behavior:

- identity;
- request validation;
- planning;
- authorization;
- execute-once;
- Result/Audit/Handoff;
- persistent Watchlist;
- Local Service/MCP;
- security/filesystem containment;
- current supported source normalization;
- current fail-closed semantics.

Expected default PR gate: **yes**.

### B. CURRENT_CONTRACT

Machine-readable authoritative contract compatibility:

- current schemas;
- Catalog/Route authority;
- executor registration;
- public API/tool inventory;
- persistence schemas;
- security boundaries.

Expected default PR gate: **yes**.

### C. COMPATIBILITY

Explicitly supported prior public contracts/behaviors, such as V1/V2 request
compatibility after V3 promotion.

Expected default PR gate: **yes when support is still promised**.

### D. CURRENT_INTEGRATION

High-value deterministic cross-layer behavior.

Expected default PR gate: selected high-signal subset.

### E. RELEASE_PRECHECK

Release packaging, versioning, distribution, public release provenance.

Expected default every-PR gate: only lightweight current invariants. Full
release reproduction belongs to release preflight.

### F. HISTORICAL_ACCEPTANCE

Reproduction or integrity of a completed milestone whose historical state is no
longer current runtime authority.

Expected default PR gate: **no**, except lightweight integrity/manifest checks.

### G. DOCUMENTATION_GOVERNANCE

Checks structured current metadata and navigation boundaries.

Expected behavior:

- test stable metadata, links and lifecycle classification;
- avoid exact natural-language prose unless wording itself is an external
  public contract;
- avoid forcing every historical filename into current front-door navigation.

### H. LIVE / BROWSER / PERFORMANCE

Explicit operator/release profiles only.

## 7. Preferred evidence model for history

Historical acceptance should move toward:

```text
historical evidence artifact
        +
accepted commit / immutable manifest
        +
sha256 / schema / required-evidence references
        +
optional manual reproduction profile
```

Default CI should primarily prove that accepted evidence has not been silently
rewritten or lost.

Full historical reproduction can remain available through
`historical-acceptance` or milestone-specific manual profiles.

## 8. Preferred documentation contract model

Machine tests should prefer structured truth.

For example:

```yaml
roadmap_version: "3.2"
phase_i_status: "NOT_STARTED"
preferred_request: "v3"
stable_release: "v1.0.0"
```

is more stable than requiring one exact English paragraph in README.

Human-readable Markdown can then evolve without losing governance.

This preflight does **not** yet introduce a new metadata authority; it first
inventories where structured authority already exists and where a small
current-state manifest would remove brittle prose coupling.

## 9. Execution tranches

### TG-0 — Inventory and classification

No test selection changes.

Produce machine-readable inventory for every current `default-ci` path:

- file;
- test count where deterministically obtainable;
- milestone/family;
- markers;
- reads production code?;
- reads docs/ledgers/manifests?;
- exact path assertion?;
- exact prose assertion?;
- current-runtime invariant?;
- compatibility promise?;
- historical-reproduction role?;
- candidate class;
- proposed future profile;
- confidence;
- notes.

Exit: every default-CI file has a proposed classification.

### TG-1 — Authority and brittle-coupling audit

Identify:

- exact prose assertions;
- exact historical filename/path assertions;
- old `next_task` assertions;
- assertions against mutable human docs;
- duplicate current-state assertions;
- tests where a historical snapshot is incorrectly acting as current authority.

No removals yet.

Exit: explicit debt ledger with proposed disposition for every identified
brittle assertion.

### TG-2 — Marker/profile normalization

Use existing marker vocabulary where adequate; extend only if required.

Initial target semantic profiles:

- `changed-fast`;
- `default-ci-current`;
- `full-current-non-network`;
- `compatibility`;
- `release-preflight`;
- `historical-acceptance`;
- `browser-e2e`;
- `bounded-live`;
- `performance`.

Do not cut over default CI yet.

### TG-3 — Historical evidence integrity layer

Build/normalize a historical-evidence manifest for accepted milestone artifacts
that need immutability protection.

Where appropriate, replace current-PR dependency on full historical
reproduction with:

- artifact exists;
- accepted hash/manifest matches;
- required references remain reachable.

Keep full reproduction tests available in historical/manual profiles.

### TG-4 — Shadow CI

Run old and proposed new default profiles side by side over a bounded period or
representative change set.

For every test removed from the proposed default path, document:

- why it is historical/release/manual;
- what protects the invariant now;
- what command/profile still reproduces it.

Exit: no unexplained protection gap.

### TG-5 — Default-CI cutover

Only after TG-0 through TG-4 acceptance:

- switch default CI from a 156-file hand-maintained list toward semantic current
  profiles/markers;
- retain rollback to the previous profile definition;
- record before/after selected-test composition;
- do **not** claim quality improvement merely from a lower test count.

### TG-6 — Optional physical test-tree cleanup

Only after policy is stable:

- move historical tests under a clearer historical tree if worth the churn;
- preserve import/fixture compatibility or migrate deliberately;
- remove genuinely duplicate tests only with explicit equivalence evidence.

Physical relocation is last, not first.

## 10. Required acceptance properties

The final migration must prove:

1. all current V3 product invariants remain protected;
2. V1/V2 promised compatibility remains protected;
3. six MCP tools remain protected;
4. Security Master / filesystem containment remains protected;
5. fail-closed source/identity/currentness semantics remain protected;
6. historical evidence remains immutable and discoverable;
7. full historical reproduction remains runnable when intentionally selected;
8. default CI remains non-network;
9. no Phase I implementation enters;
10. rollback to the pre-cutover test profile is documented and deterministic.

## 11. Metrics to collect — not targets

Track:

- default selected test count;
- default test file count;
- test duration;
- number of tests/files by governance class;
- number of exact prose assertions;
- number of exact historical path assertions;
- number of `next_task`/old milestone state assertions;
- duplicate invariant clusters;
- historical tests remaining in default CI;
- marker coverage;
- number of manual path entries in test profile config.

These are diagnostic metrics, not success scores.

## 12. Stop rules

Stop and require explicit review if a proposed migration would:

- remove the only test for a current security/fail-closed invariant;
- make V1/V2 compatibility untested while still advertised;
- rewrite or regenerate historical evidence instead of preserving it;
- require production runtime changes solely for test cleanup;
- require live network to establish normal PR correctness;
- touch Roadmap Phase I implementation.

## 13. Immediate next action

Proceed with **TG-0 only**:

1. build deterministic inventory tooling;
2. classify the current 156 default-CI files;
3. generate a human-readable and JSON report;
4. make **no** selection/profile cutover;
5. review the inventory before TG-1/TG-2 mutation work.

This makes the first implementation tranche reversible and evidence-producing,
rather than another large governance refactor.
