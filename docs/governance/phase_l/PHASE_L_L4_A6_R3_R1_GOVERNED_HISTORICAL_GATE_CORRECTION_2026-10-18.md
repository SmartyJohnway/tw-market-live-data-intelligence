# L4-A6-R3-R1 — Governed Historical-Test Gate Correction

Run: `l4-a6-r3-r1-20261018T004303Z`

R3's HOLD was operationally correct for its recorded invocation. It ran the
bounded integrated suite with zero deselections and therefore included two
historical Mode C replay nodes already governed by
`TG4_KNOWN_HISTORICAL_REPLAY_GAPS.v1.json`. Both nodes reproduced their known
historical failures. The R3 evidence remains immutable and continues to report
308 passed, 2 failed, 1 skipped, 0 deselected, and
`HOLD_INTEGRATED_GATE_FAILURE`.

Independent authority reconciliation confirmed the same nodes failed on a clean
Phase J baseline, are not J2 acceptance nodes, and are outside default-ci.
Phase L A0/A2/A3/A4 disclosures and the initial A6 run already treated them as
historical debt; the A6 initial run recorded exactly two deselections and zero
failures. R3-R1 corrected selection only by applying those exact two governed
deselections to the same bounded integrated scope. No tests or product code were
changed.

Corrected gate: 308 passed, 1 skipped, 2 governed deselected, 0 failed. The two
nodes are not passing, not repaired, and not a current regression.
`MODE C HISTORICAL DEBT RESOLVED = NO`. R3's memory, timeout, low-disk,
middleware, resource-finding, and A3 residual evidence was hash-verified and
reused without modification.

The corrected gate and offline validators passed with zero external socket
attempts, provider requests, live acquisition, or production user-state
mutations. Final technical disposition:
`L4_A6_RESOURCE_LOAD_CONCURRENCY_ACCEPTANCE_PASS`. Owner acceptance is pending;
A7 remains unauthorized. Evidence is in
`acceptance_runs/l4-a6-r3-r1-20261018T004303Z/`.
