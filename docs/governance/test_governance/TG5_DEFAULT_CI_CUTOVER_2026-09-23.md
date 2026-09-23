# TG-5 Default-CI Cutover Plan and Acceptance Contract — 2026-09-23

Baseline main: `2ff9707d901f40c1a108dd1317fce2f03cc79735`

Status: **CUTOVER CANDIDATE / NOT YET ACCEPTED**

## Objective

Promote the TG-4 proven current test layer to the repository's ordinary
`default-ci` authority.

This is the first stage in the test-governance program that intentionally
changes which tests can block an ordinary default-CI merge.

## Authority change

Before TG-5:

```text
default-ci
156 paths
1245 selected pytest nodes
```

TG-5 candidate:

```text
default-ci
93 paths
778 selected pytest nodes
```

The 467 legacy nodes no longer in ordinary default are not deleted:

```text
372  broad current regression
 90  historical acceptance
  5  release preflight
---
467
```

TG-4 proved that all 1245 legacy nodes have a semantic home with zero
unexplained loss.

## Rollback

The exact pre-TG5 default profile is frozen in:

`docs/governance/test_governance/TG5_ROLLBACK_CONTRACT_2026-09-23.json`

A runnable current-tree diagnostic profile is also retained:

`pre-tg5-default-ci`

It preserves the 156-path/expression topology, but it is **not** the authoritative
rollback proof because two TG-3-frozen historical acceptance files intentionally
assert the old default topology.

Authoritative rollback proof is a detached worktree at the frozen pre-TG5
baseline commit. Its native `default-ci` must select 1245 nodes and pass.

Operational rollback is repository-level: revert the TG-5 merge or restore the
repository to the frozen pre-TG5 baseline. Frozen historical evidence is never
rewritten merely to make current-tree rollback rehearsal appear green.

## Lifecycle profiles retained

- broad current: `tg2-full-current-non-network-shadow`
- historical: `tg2-historical-acceptance-shadow`
- release: `tg2-release-preflight-shadow`
- mixed historical: `tg4-mixed-historical-shadow`

Their older `tg2`/`tg4` names are retained during TG-5 to minimize churn.
Naming cleanup, marker migration, and physical test movement belong to TG-6.

## Historical validator realignment

TG-0 through TG-4 acceptance ledgers are not rewritten.

Their executable validators are made time-aware:

- TG-0/TG-1 audit the `pre-tg5-default-ci` baseline;
- TG-2/TG-3 validate their original 156-path partition against the frozen
  pre-TG5 source set;
- TG-4 validates that its baseline remains reproducible and that TG-5 promotes
  the exact current shadow candidate.

This prevents historical governance tests from fossilizing current authority.

## Required TG-5 acceptance

The acceptance workflow must prove:

1. new `default-ci` static contract = 93 paths;
2. new default selects exactly 778 nodes and passes;
3. TG-2 current shadow also selects exactly 778 and passes;
4. promoted default and current shadow have identical pytest node sets;
5. detached pre-TG5 baseline `default-ci` selects 1245 and passes;
6. current-tree `pre-tg5-default-ci` has only the two frozen historical self-membership diagnostic gaps;
7. broad current selects 1150 and passes;
8. historical selects 94 and passes;
9. release selects 5 and passes;
10. mixed historical has only the two already frozen replay gaps;
11. full `full-non-network` regression passes;
12. production runtime, source activation/routing and frozen schemas are
    unchanged;
13. no tests are deleted;
14. Phase I remains untouched.

## Out of scope

TG-5 does not:

- delete tests;
- rename/move historical tests;
- make historical or release profiles automatic;
- change browser/live/network policy;
- change GitHub branch-protection configuration;
- change workflow trigger policy;
- enter Roadmap Phase I.

## Promotion rule

TG-5 may merge only after the cutover candidate and rollback profile both pass
in the same acceptance run.

TG-6 physical cleanup remains a separate later decision.
