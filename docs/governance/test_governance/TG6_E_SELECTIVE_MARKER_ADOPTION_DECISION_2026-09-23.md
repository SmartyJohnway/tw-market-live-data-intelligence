# TG6-E Selective Marker Adoption — Current-Tree Decision Preflight

Date: 2026-09-23

Baseline main: `959b26e2a0a338449f9feef0ab0458f88677a0fa`

Status: **PREFLIGHT PASS — CURRENT-TREE MARKER MUTATION NOT RECOMMENDED**

TG6-E was originally proposed as selective marker adoption after profile stabilization. After TG6-C, the current repository was re-evaluated to determine whether TG6-E should be bundled with the very small TG6-D duplicate cleanup.

The conclusion is **no**: marker adoption should not be bundled into TG6-D, because every currently meaningful retroactive marker mutation either changes accepted lifecycle/rollback node counts or produces churn without routing value.

## 1. Current marker state

`pytest.ini` already defines semantic markers including:

- `historical`
- `release_preflight`
- `full_current`
- `historical_candidate`
- `default_ci`
- `core`
- `compatibility`
- `documentation_governance`

Current code usage remains intentionally sparse.

Observed meaningful current usage includes:

- four `@pytest.mark.historical` nodes in `tests/unit/test_m8r_06_04_mode_c.py`;
- one network `@pytest.mark.release_preflight` integration test.

The four historical Mode C nodes are exactly the current `mixed-historical-diagnostic = 4` node-level diagnostic surface. No marker gap exists there.

## 2. Mixed Phase G closure cannot safely receive `historical` now

`tests/unit/test_phase_g_pr_d_closure.py` is a mixed current/historical semantic file.

The node:

`test_phase_g_closure_remains_historical_while_current_authority_is_v3`

does contain historical-evidence assertions, but it also validates current V3 authority.

The file is present in:

- `default-ci`;
- `full-current`;
- `pre-tg5-default-ci`.

All three expressions exclude `historical`.

Adding `@pytest.mark.historical` to this node would therefore change accepted node counts approximately as follows:

```text
default-ci          778  -> 777
full-current       1150  -> 1149
pre-tg5-default-ci 1245  -> 1244
```

That is an authority/rollback semantics change, not a cleanup-only marker adoption.

Disposition: **DO NOT MARK under TG6-E.**

## 3. Release-preflight files cannot safely receive `release_preflight` now

The current stable release profile contains:

- `tests/unit/test_build_v1_release_manifest.py` — 4 nodes
- `tests/unit/test_browser_e2e_requirements.py` — 1 node

Together they are exactly the five nodes of `release-preflight-current`.

At first glance, module-level `pytest.mark.release_preflight` would be a clean semantic annotation.

However, both files are also retained in `pre-tg5-default-ci`, whose expression explicitly excludes `release_preflight`.

Adding the marker would change:

```text
pre-tg5-default-ci 1245 -> 1240
```

and would break the TG6-C rollback diagnostic equivalence contract.

Disposition: **DO NOT MARK under TG6-E.**

## 4. Broad retroactive inert markers are poor value

Other existing markers such as `default_ci`, `full_current`, and `historical_candidate` are not currently used by lifecycle profile expressions.

Applying them retroactively would not improve execution routing today.

Examples:

- `default_ci` would imply high-churn annotation across the current default path set;
- `full_current` would require broad annotation across current non-default regression surfaces;
- `historical_candidate` is migration-era wording and is stale after TG6-C established `historical-milestone-replay` as the current lifecycle role.

The immutable TG2/TG3 manifests already contain the historical classification evidence. Duplicating that classification into inert markers creates drift risk without an operational benefit.

Disposition: **NO MASS OR TOKEN RETROACTIVE ANNOTATION.**

## 5. Current-tree TG6-E decision

TG6-E should **not perform marker mutations on the existing test tree**.

The accepted current model remains:

- path-based lifecycle profiles are canonical;
- `historical` is used only where node-level exclusion/diagnostic semantics are already deliberate and proven;
- current accepted lifecycle counts remain authoritative;
- no marker is added merely to make taxonomy look complete.

## 6. Forward marker policy

TG6-E still has value as a forward policy:

For **new tests created after TG6-E closure**:

1. use `historical` only when the test is intentionally outside current-product regression and the selection effect is reviewed;
2. use `release_preflight` only when the test is intentionally release-only and not part of rollback/current default authority;
3. use `full_current`, `default_ci`, `compatibility`, `documentation_governance`, or component markers only when they communicate a real lifecycle/component contract;
4. do not make marker presence a substitute for explicit profile-path authority until a separately authorized marker-based routing migration exists.

Marker introduction that changes selected nodes in `default-ci`, `full-current`, `historical-milestone-replay`, `release-preflight-current`, `mixed-historical-diagnostic`, or `pre-tg5-default-ci` requires a separate authority-change gate.

## 7. Relationship to TG6-D

TG6-D remains a low-risk exact duplicate deletion.

TG6-E is **not** a suitable code-change companion for TG6-D because the safe current-tree TG6-E outcome is no marker mutation.

Recommended execution:

```text
TG6-D implementation:
PROCEED ALONE

TG6-E current-tree marker mutation:
NO ACTION

TG6-E forward marker policy:
ACCEPT AS GOVERNANCE RULE
```

This keeps TG6-D acceptance simple and preserves all TG6-C lifecycle counts.

## 8. Closure recommendation

TG6-E may be closed after this decision is accepted as:

```text
TG6-E SELECTIVE MARKER ADOPTION
CURRENT TREE: NO MUTATION REQUIRED
FORWARD POLICY: ADOPT MARKERS AT TEST CREATION WHEN SEMANTICALLY MATERIAL
MASS MIGRATION: PROHIBITED
AUTHORITY-CHANGING MARKER WORK: SEPARATE GATE REQUIRED
```

No implementation PR is recommended for existing tests.
