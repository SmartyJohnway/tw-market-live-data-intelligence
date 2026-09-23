# TG6-D Bounded Exact Duplicate Test Cleanup — Preflight

Date: 2026-09-23

Baseline main: `881c899b8e04195806178198e0bf15d93cf41b00`

Status: **PREFLIGHT PASS — EXACT DELETE CONTRACT FROZEN; IMPLEMENTATION NOT YET AUTHORIZED**

TG6-D is intentionally limited to one previously identified byte-for-byte duplicate test pair. This preflight does not authorize generalized deduplication, test refactoring, marker work, historical relocation, validator retirement, runtime changes, or Roadmap Phase I.

## 1. Exact duplicate proof

The two files are still identical on the TG6-C-closed main:

```text
tests/unit/test_m8r_05b_02_consumption_binding_schema.py
tests/unit/test_m8r_05b_02_schema.py
```

Both resolve to Git blob SHA:

```text
4bc114b64098c80ed5e28f5ac25e9e347c2b73c9
```

Both contain the same single test node:

```text
test_schema_json
```

Both read the same governed schema and assert only that its title is present.

## 2. Exact keep/delete contract

TG6-D implementation SHALL:

**KEEP**

`tests/unit/test_m8r_05b_02_consumption_binding_schema.py`

Reason: the filename identifies the tested contract more precisely.

**DELETE**

`tests/unit/test_m8r_05b_02_schema.py`

Reason: it is the generic-named byte-for-byte duplicate.

No test body is to be rewritten, merged, generalized, renamed, or expanded as part of TG6-D.

## 3. Reference check

Repository search finds no current executable/configuration reference to either filename.

The only filename references are historical TG6 cleanup preflight records that documented the duplicate pair. Those historical records SHALL remain unchanged.

Neither file appears explicitly in any current governed lifecycle profile path list, including:

- `default-ci`
- `full-current`
- `historical-milestone-replay`
- `release-preflight-current`
- `mixed-historical-diagnostic`
- `pre-tg5-default-ci`

Therefore TG6-D must not change lifecycle profile configuration or authority counts.

## 4. Full Non-Network impact

`full-non-network` scans the full `tests/` tree, so the duplicate is part of that broad suite even though it is not in lifecycle profile path lists.

Accepted TG6-C baseline run `35863494074`:

```text
collected  = 2801
selected   = 2745
passed     = 2730
failed     = 2
skipped    = 13
deselected = 56
```

The two failures are the already-governed frozen historical assertions FNN-02 and FNN-03.

Because TG6-D deletes exactly one unmarked passing duplicate node, expected post-delete Full Non-Network counts are:

```text
collected  = 2800
selected   = 2744
passed     = 2729
failed     = 2
skipped    = 13
deselected = 56
```

The remaining failures must still be exactly FNN-02 and FNN-03. New unexplained failures must remain zero.

## 5. Default/lifecycle authority impact

Expected impact:

```text
default-ci                     778  unchanged
full-current                  1150  unchanged
historical-milestone-replay     94  unchanged
release-preflight-current        5  unchanged
mixed-historical-diagnostic      4  unchanged
pre-tg5-default-ci            1245  unchanged
```

The existing TG6-C focused governance test in Full Non-Network already performs real `pytest --collect-only` assertions for those six lifecycle counts. It must continue to pass after the duplicate deletion.

## 6. Required implementation diff

The implementation diff SHALL contain exactly:

1. deletion of `tests/unit/test_m8r_05b_02_schema.py`;
2. TG6-D-specific current acceptance evidence/tests only if needed for proof.

It SHALL NOT modify:

- the retained duplicate file;
- `config/test_execution_profiles.json`;
- `config/test_governance_authority.json`;
- historical TG2/TG3/TG4/TG5/TG6 evidence;
- workflows;
- production runtime;
- source activation/routing;
- frozen schemas.

## 7. Acceptance gate

Before merge:

1. **Default CI**
   - PASS
   - selected = 778

2. **Full Non-Network Regression**
   - GitHub conclusion may remain FAILURE due only to the two governed historical assertions;
   - selected = 2744;
   - passed = 2729;
   - failed = 2;
   - skipped = 13;
   - failures exactly FNN-02 + FNN-03;
   - new unexplained failures = 0;
   - TG6-C lifecycle collection-equivalence test still passes.

3. **Focused duplicate proof**
   - retained file exists;
   - deleted file is absent;
   - retained test still passes;
   - no profile or authority file changed.

Windows Compatibility Smoke is **not required** for TG6-D because the authorized diff is a platform-neutral deletion of one duplicate unit-test file outside the Windows smoke surface. If the implementation diff expands, this exemption is void.

## 8. Stop rules

Stop without merge if:

1. either file is no longer byte-for-byte identical before deletion;
2. a current executable dependency on the delete target is discovered;
3. `default-ci` changes from 778 selected;
4. any lifecycle count changes;
5. Full Non-Network has any new failure;
6. either frozen historical failure is edited or suppressed;
7. profile/authority/workflow/runtime/source/routing/schema files enter the implementation diff;
8. TG6-E/F/G or Phase I enters scope.

## 9. Preflight verdict

```text
TG6-D BOUNDED EXACT DUPLICATE TEST CLEANUP
PREFLIGHT: PASS

KEEP:
tests/unit/test_m8r_05b_02_consumption_binding_schema.py

DELETE:
tests/unit/test_m8r_05b_02_schema.py

Duplicate blob SHA:
4bc114b64098c80ed5e28f5ac25e9e347c2b73c9

Default authority change:
NO

Expected Full Non-Network selected:
2745 -> 2744

Implementation:
NOT YET AUTHORIZED
```
