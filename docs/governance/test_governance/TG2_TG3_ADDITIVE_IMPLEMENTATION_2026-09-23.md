# TG-2 / TG-3 Additive Test-Governance Implementation

Baseline main: `b75bfda283d89adf62b46ee63c4c9c528ce92934`

Status: **additive implementation; no default-CI cutover**

## TG-2 — semantic profile normalization

TG-2 introduces a machine-readable semantic classification layer:

`config/test_governance_semantic_profiles.json`

The TG-1 proposal is refined in one place:

- `test_m8c_taifex_mis_currentness_preflight.py` is reclassified from
  historical candidate to broad full-current regression because it tests a pure
  deterministic M8C currentness helper and does not validate an immutable
  acceptance artifact.

The resulting partition of the existing 156 default-CI paths is:

```text
default-ci current candidate       91
mixed current/historical            2
full-current non-default           46
historical acceptance candidate    15
release-preflight candidate         2
                                   ---
                                   156
```

No source test is deleted.

### Additive shadow profiles

Four manual-only profiles are added:

- `tg2-default-ci-current-shadow` — 93 paths; 91 current + 2 mixed fail-safe
- `tg2-full-current-non-network-shadow` — 139 paths
- `tg2-historical-acceptance-shadow` — 15 paths
- `tg2-release-preflight-shadow` — 2 paths

All have:

```text
automatic_ci_allowed = false
```

The existing `default-ci` path list and pytest expression remain unchanged.

### Marker taxonomy

TG-2 adds marker definitions for compatibility, documentation governance,
full-current, and historical-candidate semantics.

Markers are **not applied yet** to existing default-CI files. Applying
`historical` before cutover would immediately change current collection because
the existing default expression excludes `historical`.

## TG-3 — historical evidence integrity

TG-3 adds:

`docs/governance/test_governance/HISTORICAL_EVIDENCE_INTEGRITY_MANIFEST.v1.json`

The manifest covers all 15 historical candidates and binds:

- candidate historical test file content identity;
- primary accepted final-acceptance/preflight/ledger evidence;
- M8C probe summaries where applicable;
- the preserved M8R-05C fixture input package.

Integrity uses Git blob identity recorded at the post-TG1 baseline. Validation
compares each recorded identity against the current repository tree.

This is an additive protection layer. It explicitly does **not**:

- delete historical tests;
- authorize removal from default CI;
- replace full historical reproduction;
- replace future TG-4 shadow comparison.

## Mixed files

Two files remain deliberately unsplit:

- `tests/unit/test_m8r_06_04_mode_c.py`
- `tests/unit/test_phase_g_pr_d_closure.py`

They remain in the current shadow fail-safe set until a later additive split is
reviewed.

## Exit criteria

TG-2/TG-3 may be accepted only if:

1. existing `default-ci` still has exactly the same 156 paths and expression;
2. semantic partitions are disjoint and union exactly to those 156 paths;
3. all shadow profiles are manual-only;
4. historical manifest content identities validate;
5. historical tests remain present;
6. existing default non-network CI still passes;
7. production runtime, source activation, routing and frozen schemas are
   unchanged;
8. Phase I remains untouched.

TG-4, not this workstream, will compare old and proposed profile execution.
