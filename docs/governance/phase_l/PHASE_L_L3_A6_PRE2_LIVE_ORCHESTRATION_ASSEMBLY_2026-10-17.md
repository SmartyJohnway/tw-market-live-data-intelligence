# Phase L L3-A6 PRE2 — Live Orchestration Assembly

## Authority and entry

PRE2 resumes from PRE1-R2 commit
`693deac848f0228cfa6a7e73e4f79e68612d8506` (tree
`f7de3c4623a677ed01f2646d0af8b62f38a9f6ec`). Canonical main remains
`7b3e73b2f3e2c2bec167b6d66f1846846fe4ec4c`.

PRE1 established the bounded dispatch guard/accounting design. PRE1-R1 passed
its normalized offline gate and remains accepted at its reviewed state. PRE2
offline E2E exposed that the guard checked a primary hostname before resolving
the exact governed alternate route. PRE1-R2 repaired that ordering and added
the A6-only block against using a cross-host research alternate after primary
429. No Phase G production fallback code changed.

PRE2 assembles the reviewed 23-source plan and existing production source
seams into `scripts/run_phase_l_l3_a6_live_recertification.py`. Its offline
simulation uses the same orchestration and parser/normalizer bindings behind a
fake urllib opener. Live mode validates the final reservation and exact
committed Git state before any transport can be reached. The separate
reservation creator reads HEAD/tree itself and binds the source plan, transport
matrix, PRE2 manifest, and planned run ID.

## Source-level recertification boundary

P08-P10 are adjudicated as three separately attributed H1 source components.
The runner uses their existing `official_get`, decoder, source validation, and
normalizer seams so same-host 429 suppression can stop later component
requests. It does not treat one composite executor invocation as one physical
dispatch.

P11 invokes the existing H2 source-level `official_get_once`, row decoder,
and normalizer. It avoids the capability executor because that path carries an
H3 dependency unrelated to recertifying the P11 source contract. P12 invokes
only `fetch_twse_stock_day_month` for `TWSE:2330` / `2026-10`; it does not call
the multi-month walker. P17 uses the already governed selector `TWSE:2330` /
`2026-10-15`, without date rediscovery or T86 probing.

Other source bindings reuse current production transports and parsers for MIS,
official EOD, Phase G research, I1, I2, I3, and bootstrap. Bootstrap probes use
`max_followed_redirects=0`, `timeout=20`, and `save_raw=None`. P01 uses one MIS
batch with `write_latest=False` and individual fallback disabled. Research
alternates are exact governed routes and are only reachable under the current
production fallback condition; a primary 429 blocks the alternate.

## Offline evidence

Run evidence is retained under
`acceptance_runs/l3-a6-pre2-20261017T021753Z/` and marked
`SIMULATED_OFFLINE`. Its manifest SHA-256 is
`74de7917887f180c2f5c1b083c693bbc4c3b57da37c88a1feca0968020fd3ca6`.
The evidence covers the 23-source/23-baseline/27-maximum plan and 12 fake
response scenarios, including baseline PASS, maximum 27 dispatches, research
alternate recovery, primary drift preservation, same-host 429 suppression,
404/410, timeout, 5xx, and contract drift (15 retained scenarios).

Focused PRE1 guard and PRE2 orchestration tests: **75 passed**. The combined
guarded source/offline regression gate: **611 passed, 1 deselected, 0 failed**.
The sole deselection is the already governed
`test_lifecycle_drift_failure_report_preserves_code_without_retry_authority`;
it is not represented as passing. The external-network sentinel recorded **0**
attempts. Source registry, Portable Catalog, runtime/Skill exact-six, V1
public-contract exact-six, and Phase H V3 validators passed. `compileall` and
`git diff --check` passed.

No production runtime, source registry, Catalog, Route, activation state,
Security Master, Watchlist, or production Result/Audit store was changed. No
provider request was made. The A6 market authority remains unconsumed and no
final live reservation was created. The next live checkpoint requires no
Python source-code change, but still requires the separately authorized final
reservation and explicit execution step.

PRE2 disposition: `PASS_READY_FOR_ONE_SHOT_LIVE_EXECUTION` — candidate pending
independent review. This is not Owner acceptance, live execution, or L3 closure.
