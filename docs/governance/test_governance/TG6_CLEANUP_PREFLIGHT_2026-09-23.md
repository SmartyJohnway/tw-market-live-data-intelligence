# TG-6 Cleanup Preflight — 2026-09-23

Baseline main: `db3340da61ea6e1f3391cfc1728d42b5376157c7`

Status: **PREFLIGHT ONLY — NO CLEANUP MUTATION**

TG-5 has already changed the ordinary merge authority to the accepted
93-path / 778-node current gate. TG-6 therefore has a different objective:
reduce governance clutter without reopening test-authority risk.

## Executive conclusion

The highest-value cleanup is **not** moving historical tests and **not** adding
markers to hundreds of files.

The preferred cleanup order is:

1. normalize current test-governance metadata;
2. retire completed one-time GitHub Actions workflows;
3. replace temporary TG-2/TG-4 profile names with stable lifecycle names;
4. remove the one proven byte-for-byte duplicate test;
5. adopt markers selectively, not repo-wide.

Physical historical-test relocation and aggressive retirement of TG0-TG5
validators should be deferred.

## Baseline

- Python test files: **393**
- unit test files: **363**
- integration test files: **7**
- current `default-ci`: **93 paths / 778 selected nodes**
- workflow YAML files currently under `.github/workflows`: **15**
- CI_POLICY_V1 expected current workflows: **5**
- surplus one-time milestone workflows: **10**
- test-governance documents: **17**
- TG-specific governance scripts: **6**
- TG-specific governance tests: **8**

## Finding 1 — current authority metadata has drifted

`config/test_governance_authority.json` is now the natural current machine
authority, but it still says:

```text
state = TG5_CUTOVER_CANDIDATE
```

even though TG-5 is merged.

At the same time,
`config/test_governance_semantic_profiles.json` still records its historical
TG-2 state:

```text
mode = TG-2_ADDITIVE_SHADOW_ONLY
default_ci_authority_changed = false
```

The TG-2 content is historically correct and should not be rewritten as if it
were current. The cleanup should instead make its lifecycle explicit:
**historical migration evidence**, not current authority.

### Recommendation

TG6-A should establish:

- one active machine authority: `config/test_governance_authority.json`;
- current state = TG-5 promoted/active;
- TG-2 semantic manifest retained as historical migration evidence.

## Finding 2 — 10 one-time workflows remain in the current workflow directory

There are **15** YAML workflows under `.github/workflows`, while
CI_POLICY_V1 expects exactly five current workflows.

The five intended current workflows are:

- `ci.yml`
- `non-network-ci.yml`
- `windows-compatibility-smoke.yml`
- `browser-operator-e2e.yml`
- `release-validation.yml`

Ten milestone-specific harnesses remain:

### Phase H one-time workflows

- `phase-h-h-acc-7l-live-e2e.yml`
- `phase-h-h-act-h1-bounded-live.yml`
- `phase-h-h-act-v3-promotion-preflight.yml`
- `phase-h-h-act-v3-promotion.yml`

### Repository/test-governance one-time workflows

- `repository-governance-consolidation.yml`
- `test-governance-tg0-inventory.yml`
- `test-governance-tg1-disposition.yml`
- `test-governance-tg2-tg3.yml`
- `test-governance-tg4-shadow.yml`
- `test-governance-tg5-cutover.yml`

They all monitor completed branch-specific workflows rather than current
repository CI policy.

This is not only cosmetic. Their continued presence is one reason the existing
`test_github_actions_execution_policy` / CI policy validation is part of the
known broad full-regression debt.

### Recommendation

TG6-B should retire these ten YAML files from the active workflow directory
while preserving their accepted run IDs and ledgers in governance evidence.

The acceptance target should be:

```text
workflow_count = 5
validate_github_actions_execution_policy = PASS
```

## Finding 3 — temporary shadow profile names have outlived promotion

The strongest example is exact redundancy:

```text
default-ci
tg2-default-ci-current-shadow
```

Both now have:

- exactly **93 paths**;
- identical path order;
- identical pytest expression.

The shadow alias has completed its purpose.

Other lifecycle roles still use migration-era names:

- `tg2-full-current-non-network-shadow`
- `tg2-historical-acceptance-shadow`
- `tg2-release-preflight-shadow`
- `tg4-mixed-historical-shadow`

### Recommendation

TG6-C should migrate to stable role names, for example:

```text
default-ci                      current every-PR authority
full-current                    broad deterministic current regression
historical-milestone-replay     historical milestone lifecycle
release-preflight-current       release-specific lifecycle
mixed-historical-diagnostic     node-level mixed-file diagnostic
pre-tg5-default-ci              retained rollback diagnostic
```

The exact naming can be adjusted, but migration should be equivalence-tested
before aliases are removed.

## Finding 4 — milestone-acceptance is stale

The profile still says it is the active M8R-03E-R2 acceptance profile and is
marked `automatic_ci_allowed=true`.

That is no longer an accurate description of repository state.

### Recommendation

Treat this as old milestone machinery. Deprecate it or make it manual/historical
instead of presenting it as current active authority.

## Finding 5 — marker taxonomy is mostly aspirational

The repository defines markers such as:

- `core`
- `default_ci`
- `compatibility`
- `documentation_governance`
- `full_current`
- `historical_candidate`

but searches currently find essentially no use of those TG-2 marker classes.
Historical markers exist only in a small number of files.

### Recommendation

Do **not** annotate 393 test files just to make the taxonomy look complete.

The accepted path-based profile registry should remain canonical for now.
Markers should be added:

- when a file contains both current and historical nodes;
- for new tests at creation time;
- when node-level selection materially improves lifecycle separation.

This avoids another high-churn migration with little operational gain.

## Finding 6 — one real duplicate test exists

Excluding empty package `__init__.py` files, only one exact duplicate group was
found by Git blob identity:

```text
tests/unit/test_m8r_05b_02_consumption_binding_schema.py
tests/unit/test_m8r_05b_02_schema.py
```

Both have blob SHA:

`4bc114b64098c80ed5e28f5ac25e9e347c2b73c9`

and both contain the same single schema-title assertion. Repository search found
no filename references to either.

### Recommendation

TG6-D may safely keep the more descriptive
`test_m8r_05b_02_consumption_binding_schema.py` and remove the generic
`test_m8r_05b_02_schema.py`, subject to the normal full-current/default
regression check.

## Finding 7 — physically moving historical tests is poor value

The 15 TG-3 historical candidates are now heavily referenced by:

- active/manual profiles;
- TG-2 semantic migration manifest;
- TG-3 historical integrity manifest;
- TG-5 rollback contracts;
- M8 test-suite lifecycle inventories;
- accepted review/acceptance evidence.

Individual filenames have roughly **6–17 repository references**.

Moving them to a cleaner directory would therefore create substantial evidence
and path churn without changing execution semantics.

### Recommendation

**Do not move them in initial TG-6.**

Path clutter is preferable to rewriting accepted historical references.

## Finding 8 — TG0-TG5 scripts/tests are a later cleanup question

The repo currently has six TG-specific governance scripts and several
TG-specific tests. Many are primarily connected to completed one-time workflow
harnesses.

However, immediately deleting them would mix workflow cleanup, reproducibility,
and current-authority migration in one operation.

### Recommendation

Retire one-time workflows first and stabilize profile names. Only then perform
a second reachability audit for:

- `audit_test_governance.py`
- `analyze_test_governance_tg4_nodes.py`
- `validate_test_governance_tg2_tg3.py`
- `validate_test_governance_tg4_shadow.py`
- `validate_test_governance_tg5.py`
- their TG-specific tests.

Keep `scripts/test_governance_authority.py` as the current role-resolution
surface unless replaced deliberately.

## Proposed TG-6 execution tranches

### TG6-A — Current authority normalization

Low risk.

- update active authority state to TG-5 promoted/active;
- clearly distinguish current authority from historical TG-2 migration data;
- no test-selection change.

### TG6-B — One-time workflow retirement

Low-to-medium risk.

- remove the ten completed milestone workflow YAML files;
- leave exactly the five CI_POLICY_V1 workflows;
- require CI policy validator PASS;
- preserve acceptance ledgers/run IDs.

### TG6-C — Stable lifecycle profile naming

Medium risk.

- retire redundant current-shadow alias;
- promote stable names for broad-current, historical, release and mixed
  diagnostic roles;
- update current authority mapping;
- prove exact node equivalence before removing aliases;
- retain `pre-tg5-default-ci` rollback diagnostic.

### TG6-D — Exact duplicate test cleanup

Low risk.

- remove only the proven duplicate generic schema test;
- no speculative deduplication.

### TG6-E — Selective marker adoption

Medium risk.

- markers only where node-level semantics need them;
- new tests should use current lifecycle markers from creation;
- no mass migration.

### TG6-F — Historical physical relocation

**DEFER / high risk.**

### TG6-G — TG milestone validator retirement

**DEFER until TG6-C is stable.**

## Stop rules

TG-6 must stop if a cleanup would:

- change the accepted 778-node `default-ci` authority without a separate
  authority-change gate;
- rewrite historical acceptance evidence to match current paths;
- remove the only protection for security, identity, fail-closed,
  compatibility, routing or contract invariants;
- use cleanup as an excuse to repair unrelated runtime failures;
- enter Roadmap Phase I.

## Recommended next action

Execute **TG6-A + TG6-B together** as the first bounded cleanup PR.

That first PR would:

1. correct current governance metadata;
2. retire one-time workflow clutter;
3. restore CI_POLICY_V1 workflow inventory to five;
4. leave test profiles, test paths and 778-node default authority unchanged.

Only after that should TG6-C profile-name cleanup begin.
