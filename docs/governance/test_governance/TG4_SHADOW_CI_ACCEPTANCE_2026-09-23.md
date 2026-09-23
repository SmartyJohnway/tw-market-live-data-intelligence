# TG-4 Shadow CI Acceptance — 2026-09-23

Baseline main: `b438e3b1d06698e2e702284abbdaf0bbc9340b40`

Tested head: `170f663d01dcae2a17c4d6c2747eec91cdb6ce50`

Workflow: `35824957803` — **SUCCESS**

## Result

TG-4 proves that the existing legacy default merge gate can be explained by the
new semantic layers with **zero unexplained test-node loss**.

```text
Legacy default selected nodes      1245

Current every-PR layer              778
Broad current non-default layer     372
Historical acceptance layer          90
Release-preflight layer               5
Unexplained                            0
                                    ----
                                    1245
```

The layered union has eight additional historical-only nodes that the legacy
default already excluded through pytest markers.

## Runtime profile results

| Profile | Selected | Pass | Skip | Fail | Result |
|---|---:|---:|---:|---:|---|
| legacy default-ci | 1245 | 1241 | 4 | 0 | PASS |
| current shadow | 778 | 774 | 4 | 0 | PASS |
| full-current shadow | 1150 | 1146 | 4 | 0 | PASS |
| historical shadow | 94 | 94 | 0 | 0 | PASS |
| release shadow | 5 | 5 | 0 | 0 | PASS |
| mixed historical shadow | 4 | 2 | 0 | 2 | EXPECTED HISTORICAL GAP ONLY |

The two mixed-historical failures are exactly the two node IDs frozen in
`TG4_KNOWN_HISTORICAL_REPLAY_GAPS.v1.json`. No unexpected historical failure
is accepted.

## Important TG-4 correction

The first shadow observation exposed that current/full-current profiles were
running historical-marked cases inside a mixed file. TG-4 corrected the shadow
expressions to exclude `historical` and `release_preflight`, then added a
separate mixed-historical profile so those nodes remain visible instead of
silently disappearing.

This is why TG-4 compares **pytest node IDs**, not only test-file paths.

## Protection interpretation

The 467 nodes absent from the proposed current every-PR layer are not
unaccounted-for deletions:

- 372 remain in broad deterministic current regression;
- 90 move to historical-acceptance governance;
- 5 move to release-preflight governance.

The historical layer also exposes eight historical-only nodes that legacy
default CI did not execute.

## Authority boundary

TG-4 does not change the current merge gate.

- `default-ci` remains unchanged;
- no tests were deleted;
- no production runtime changed;
- no source activation/routing changed;
- no frozen schema changed;
- Phase I remains untouched.

## Exit decision

**TG-4: PASS**

The repository now has sufficient shadow evidence to discuss TG-5, but TG-5 is
a separate authority change. This acceptance does **not** authorize switching
default CI.
