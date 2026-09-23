# TG6-C Stable Lifecycle Profile Naming — Exact Migration Preflight

Date: 2026-09-23

Baseline main: `c0d7590ce176989243876267ff4bd353091267c4`

Status: **PREFLIGHT PASS — EXACT MIGRATION CONTRACT FROZEN; IMPLEMENTATION NOT YET AUTHORIZED**

This preflight narrows TG6-C from the earlier cleanup recommendation into one exact, bounded naming migration. It does not change test selection, delete tests, move historical tests, change markers, modify production runtime, source activation, routing, frozen schemas, TG6-D/E/F/G, or Roadmap Phase I.

## 1. Objective

Remove migration-era TG2/TG4 lifecycle profile names from **current machine authority and current execution-profile configuration** while preserving:

- the accepted `default-ci` authority at 93 paths / 778 selected nodes;
- broad-current lifecycle semantics at 1150 nodes;
- historical milestone replay semantics at 94 nodes;
- release lifecycle semantics at 5 nodes;
- mixed historical diagnostic semantics at 4 nodes;
- the `pre-tg5-default-ci` rollback diagnostic;
- immutable TG2/TG3/TG4/TG5 evidence exactly as recorded;
- historical reproduction commands through deprecated runner aliases.

## 2. Exact stable-name contract

The TG6-C implementation SHALL use this exact mapping:

| Migration-era name | Stable current name | Current role |
|---|---|---|
| `tg2-default-ci-current-shadow` | `default-ci` | ordinary merge/default CI authority |
| `tg2-full-current-non-network-shadow` | `full-current` | broad deterministic current regression |
| `tg2-historical-acceptance-shadow` | `historical-milestone-replay` | manual historical milestone replay |
| `tg2-release-preflight-shadow` | `release-preflight-current` | manual current release-specific lifecycle |
| `tg4-mixed-historical-shadow` | `mixed-historical-diagnostic` | node-level mixed current/historical diagnostic |
| `pre-tg5-default-ci` | unchanged | rollback/current-tree diagnostic |

The first mapping is alias retirement, not a new profile: `default-ci` already contains the promoted 93-path definition.

## 3. Current config mutation rule

`config/test_execution_profiles.json` SHALL:

- remove the five migration-era profile keys listed above;
- retain `default-ci` unchanged;
- add the four stable lifecycle keys with profile bodies exactly equivalent to the four removed non-default profiles;
- update `purpose` text so it no longer describes a TG2/TG4 "shadow";
- keep all four stable lifecycle profiles `automatic_ci_allowed=false`;
- retain `pre-tg5-default-ci` unchanged.

No pytest path, expression, runner, network policy, browser policy, or live policy may change as part of TG6-C except wording-only purpose normalization.

## 4. Current authority mutation rule

`config/test_governance_authority.json` SHALL keep:

- state `TG5_PROMOTED_ACTIVE`;
- current merge authority = `default-ci`;
- 93 expected file paths;
- 778 expected selected nodes;
- rollback contract and baseline unchanged;
- TG2 semantic manifest classified as historical migration evidence.

Only current lifecycle role names change:

- `broad_current_profile = full-current`
- `historical_profile = historical-milestone-replay`
- `release_profile = release-preflight-current`
- `mixed_historical_profile = mixed-historical-diagnostic`

Expected node counts remain 1150 / 94 / 5 / 4.

## 5. Historical evidence integrity

The following MUST NOT be rewritten simply to replace old profile names:

- `config/test_governance_semantic_profiles.json`
- TG2/TG3 implementation and acceptance records
- TG4 acceptance / known-gap records
- TG5 cutover, rollback, and acceptance records
- `HISTORICAL_EVIDENCE_INTEGRITY_MANIFEST.v1.json`
- `TG5_ROLLBACK_DIAGNOSTIC_GAPS.v1.json`

Their `tg2-*` / `tg4-*` names are facts about the migration state at the time those records were produced.

## 6. Deprecated alias compatibility

Because historical evidence contains executable reproduction profile names, `scripts/run_test_profile.py` SHALL preserve a bounded compatibility map:

```text
tg2-default-ci-current-shadow       -> default-ci
tg2-full-current-non-network-shadow -> full-current
tg2-historical-acceptance-shadow    -> historical-milestone-replay
tg2-release-preflight-shadow        -> release-preflight-current
tg4-mixed-historical-shadow         -> mixed-historical-diagnostic
```

Requirements:

- aliases are runner compatibility only and MUST NOT reappear as current config profile keys;
- stable names are the canonical resolved profile;
- current automation/documentation should use stable names;
- a run requested through a deprecated alias should identify both requested alias and resolved stable profile in machine-readable output;
- aliases do not change selection semantics or automatic-CI authority.

## 7. Current executable references that must migrate

TG6-C implementation is expected to update current executable references in:

- `config/test_execution_profiles.json`
- `config/test_governance_authority.json`
- `scripts/run_test_profile.py`
- `scripts/analyze_test_governance_tg4_nodes.py`
- `scripts/validate_test_governance_tg4_shadow.py`
- `scripts/validate_test_governance_tg5.py`
- `scripts/validate_test_governance_tg2_tg3.py`
- current unit tests that assert current profile names/runner behavior.

Script filenames containing TG4/TG5 may remain until TG6-G; TG6-C changes their current role references, not their historical filenames.

## 8. TG2/TG3 validator treatment

`scripts/validate_test_governance_tg2_tg3.py` currently reads the historical semantic manifest and directly indexes current profiles by historical shadow name.

TG6-C SHALL NOT rewrite the semantic manifest. Instead the validator must explicitly map each historical shadow-set name to its current stable profile and verify profile-body equivalence relevant to the historical partition.

This keeps the validator useful as an evidence-integrity bridge instead of pretending TG2 names remain current authority.

## 9. Node-equivalence acceptance contract

Before merge, TG6-C must establish:

- `default-ci`: 778 selected, PASS;
- `full-current`: 1150 selected, PASS;
- `historical-milestone-replay`: 94 selected, exactly the two governed frozen historical failures;
- `release-preflight-current`: 5 selected, PASS;
- `mixed-historical-diagnostic`: 4 selected, exactly the two governed mixed historical failures;
- `pre-tg5-default-ci`: remains available, 1245 selected on current tree with only its governed topology diagnostic failures;
- deprecated alias command plans resolve exactly to their stable targets;
- migration-era profile keys are absent from current config;
- current authority contains only stable lifecycle names.

The existing `Full Non-Network Regression` must remain at exactly the two already-governed frozen historical assertions, with zero new unexplained failures.

## 10. CI / acceptance gates

Required pre-merge evidence:

1. Default CI — 778 selected, PASS.
2. Full Non-Network Regression — exactly 2 governed historical failures, no new failure.
3. Windows Compatibility Smoke — PASS.
4. TG6-C focused equivalence validation proving stable profile node counts and deprecated alias resolution.

TG6-C must not create a permanent new GitHub workflow. Focused equivalence proof should be exercised through repository tests/validators that are reached by the existing non-network regression.

## 11. Explicit exclusions

TG6-C does NOT authorize:

- changing the 778-node default authority;
- changing test paths/expressions for lifecycle roles;
- deleting tests;
- TG6-D duplicate cleanup;
- TG6-E marker adoption;
- TG6-F historical relocation;
- TG6-G validator retirement;
- cleanup of the separate stale `milestone-acceptance` profile;
- production runtime/source/routing/schema work;
- Roadmap Phase I.

The stale `milestone-acceptance` finding remains a separate cleanup item and is intentionally not bundled into this naming migration.

## 12. Stop rules

Stop without merge if any of the following occurs:

1. `default-ci` is not 93 paths / 778 selected nodes.
2. Stable profiles do not produce exact lifecycle node counts 1150 / 94 / 5 / 4.
3. A historical ledger/manifest must be rewritten merely to make current validation pass.
4. A deprecated alias resolves to different execution semantics than its stable target.
5. Full Non-Network gains any unexplained failure.
6. FNN-02/FNN-03 historical tests are edited to manufacture a green suite.
7. Test profile paths/expressions change beyond exact key migration.
8. TG6-D/E/F/G or Phase I enters the diff.

## 13. Preflight verdict

```text
TG6-C STABLE LIFECYCLE PROFILE NAMING
EXACT MIGRATION PREFLIGHT: PASS

Current main:
c0d7590ce176989243876267ff4bd353091267c4

Exact stable names:
FROZEN

Historical evidence rewrite:
PROHIBITED

Deprecated runner aliases:
REQUIRED

Default authority change:
NO

Implementation:
NOT YET AUTHORIZED
```
