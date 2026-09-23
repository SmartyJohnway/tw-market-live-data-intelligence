# TG-0 Initial Test-Governance Inventory Findings

Baseline main: `b42c73057a16ea39d73ed7efd8c96096ee49e131`

Inventory workflow:

- name: `Test Governance TG-0 Inventory`
- run: `35818190281`
- result: **SUCCESS**
- inventory artifact: `test-governance-tg0-inventory`
- artifact ID: `10732391431`

The full per-file inventory is generated deterministically by
`scripts/audit_test_governance.py`. Classification is advisory; this document
does not authorize test removal or default-CI cutover.

## Baseline

```text
repository Python test files       388
unit test files                    358
integration test files               7
default-ci explicit file paths     156
last accepted default-ci selected 1245
last accepted result              1241 passed / 4 skipped / 9 deselected
```

The static AST inventory sees 1,088 named `test_*` functions in the 156 files.
The larger runtime count is expected because parametrization expands collected
pytest items.

## Marker adoption

Of the 156 files:

```text
files with any pytest marker   32
files without a detected marker 124
```

The repository already defines markers such as `core`, `contract`,
`default_ci`, `historical`, `milestone`, and component markers, but current
code search found no normal use of `@pytest.mark.default_ci` or
`@pytest.mark.core`.

Therefore the present default CI is principally a hand-maintained path allowlist,
not a semantic marker policy.

## Brittle-coupling signals

The deterministic heuristic scan found:

| Signal | Default-CI files |
|---|---:|
| reads files under `docs/` | 57 |
| reads README | 6 |
| exact path / filename assertion signal | 61 |
| exact prose assertion signal | 33 |
| `next_task` literal signal | 19 |
| historical acceptance/preflight/closure name signal | 17 |

These are **review signals**, not automatic defects.

Examples such as schema-path checks can be completely valid current contract
tests. The purpose of TG-1 is to determine which signals protect a real current
invariant and which freeze historical prose/navigation.

## Advisory first-pass class signals

The classifier produced:

| Suggested class | Files |
|---|---:|
| CURRENT_CORE | 68 |
| CURRENT_CONTRACT | 13 |
| CURRENT_INTEGRATION | 6 |
| DOCUMENTATION_GOVERNANCE | 31 |
| HISTORICAL_ACCEPTANCE | 10 |
| RELEASE_PRECHECK | 4 |
| REVIEW_REQUIRED | 24 |

Only three files received high-confidence automatic classification; **153/156
still require human/governance review**. This is intentional: TG-0 is designed
to expose evidence, not silently decide what can leave default CI.

## Family distribution in current default CI

| Family | Files |
|---|---:|
| cross-cutting | 26 |
| M5 | 10 |
| M6 | 5 |
| M7 | 33 |
| M8 / M8A / M8B / M8C | 41 |
| M8R | 22 |
| Phase G | 11 |
| Phase H | 8 |

This confirms that the default merge gate still spans almost the entire project
history.

That fact is not automatically wrong. The question for TG-1 is whether each
older test protects a still-current invariant, an explicitly supported
compatibility promise, or only historical milestone state.

## Highest-priority TG-1 review buckets

### A. Historical acceptance controlling current documentation

Start with files such as:

- `tests/unit/test_m8_through_m8b_consolidated_acceptance.py`
- M8A/M8B/M8C preflight/final-acceptance tests that read `docs/`
- Phase G closure/public-surface tests that assert current prose as part of an
  older acceptance record

Review question:

> Is this assertion protecting a current machine/public contract, or merely
> requiring today's docs to keep the layout/wording expected by an earlier
> milestone?

### B. Release provenance encoded as prose regex

Start with:

- `scripts/validate_v1_public_contracts.py`
- `tests/unit/test_validate_v1_public_contracts.py`

Review question:

> Which release facts need permanent machine validation, and which should move
> from README regex to stable structured release/current-state metadata?

### C. Old `next_task` assertions

Nineteen default-CI files contain a `next_task` literal signal.

Review question:

> Is the field a historical snapshot that should be immutable, or is a test
> incorrectly requiring old roadmap sequencing to remain today's current state?

### D. Exact path assertions

Sixty-one files have an exact path/filename assertion signal.

Review question:

> Is the path itself a public/frozen contract, or only an implementation/
> documentation location that should be movable under repository governance?

## TG-0 containment result

The inventory workflow explicitly verified:

```text
config/test_execution_profiles.json unchanged
server/ unchanged
schemas/ unchanged
Phase H source descriptor unchanged
V3 routing matrix unchanged

tg0_selection_and_runtime_containment: PASS
```

No default test selection has changed.

## Decision

TG-0 confirms that a test-governance migration is justified, but does **not**
justify bulk test removal.

Next authorized analytical step should be TG-1:

1. review the 57 doc-reading files;
2. review the 19 `next_task` files;
3. identify exact current invariant for every historical-looking file;
4. record KEEP_DEFAULT / MOVE_COMPATIBILITY / MOVE_HISTORICAL /
   RELEASE_ONLY / REWRITE_BRITTLE_ASSERTION candidates;
5. do not change profile authority until that ledger is reviewed.
