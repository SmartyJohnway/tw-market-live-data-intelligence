# J-B04-A5-L1-P0-R2 bounded live session

Disposition: `J_B04_A5_L1_P0_R2_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW`.

The Owner changed the live-call policy from a single-GET authorization to one
exact-HEAD, exact-tree, environment, and execution-lease-bound session with a
maximum of ten TWT48U GET attempts. The limit is a ceiling. Each CLI invocation
can make at most one GET and has zero internal retries. The runner does not
launch an automatic retry loop.

The authorization contains `max_market_gets: 10` and no `consumed` field. The
exact statement binds the reviewed HEAD and the execution lease SHA-256. The
external lease remains mandatory, is revalidated before each attempt, and is
never stored in Git or the session package. L1-P0's and R1's single-use attempt
budget is historical and superseded only in its attempt-budget policy; R1's
workspace-loss protection remains in force.

The session directory is
`docs/governance/phase_j/acceptance_runs/j-b04-a5-session-<STATEMENT_SHA_PREFIX>/`.
Its authorization receipt is created once and must exactly match on later
invocations. Before transport, each invocation atomically creates the next
`attempt-NNN/attempt_reserved.json` with state
`RESERVED_BEFORE_TRANSPORT`. Durable reservations are authoritative, contiguous
from 1 through 10, and count even if the process crashes before contacting the
source. Attempt 11 is rejected. A session summary is rebuilt from reservation
and attempt receipts, not trusted as the budget counter.

The same authorization can continue after a transient source failure or an
unavailable live stage witness, while attempts remain and all Git, lease, and
runtime checks still pass. PASS, a hard block, or budget exhaustion writes a
terminal session record and prevents further calls. Concurrent invocation
execution is serialized around allocation and transport, so a PASS cannot race
with an extra GET.

The exact Owner statement is:

```text
AUTHORIZE J-B04-A5 BOUNDED LIVE SESSION ON HEAD <EXACT_HEAD_SHA>
WITH EXECUTION LEASE <EXECUTION_INSTANCE_LEASE_SHA256>:
up to 10 GET attempts total to
https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL,
stop early when J-B04-A5 acceptance succeeds,
no redirects,
target TWSE:2330,
no H3 live calls,
no TWT49U/TPEx/browser fallback,
no raw payload persistence,
no H2 activation,
no J-B04 closure,
no Phase J start.
```

Every attempt retains the existing source limits: one logical GET and at most
one dispatch, no retry, no redirect, no HEAD/POST, no H3/TWT49U/TPEx/browser
fallback, and no Security Master acquisition. Raw TWT48U bytes and the decoded
full row set remain process-memory-only. Normalized governed H2/H4 evidence,
hashes, byte counts, and row counts may be persisted in per-attempt packages.
Cloud-clean identity remains
`acceptance_only_predeclared_source_target`; live success does not verify
production identity or waive A6 reverification.

No production execution lease was prepared, no Owner live authorization was
created, and no live request was made for R2.

## Validation

The A5 runner suites passed **70 tests**. Network-denied A3, Phase-H H2/H3/H4,
Mode A, Security Master lifecycle, and identity regressions passed **225 tests**
with **2 skipped**. P0-R2, L1-P0, R1, and R2 validators passed. A1/A2/A3,
Phase-H V3, Phase-J GHI, portable catalog sync, runtime Skill/guide sync,
compileall, and `git diff --check` passed. The strict duplicate-key scan passed
for **1,012 JSON files**.

The exact default-CI comparison used immutable Git archive checkouts of base
`1e84554c250d92e05b44eb8a543cd76fc154e55b` and implementation candidate
`89d78d8684a1f7699425b7249e5ff620d66aebb8` (tree
`d4c826abee92660ba645bd26baca2477f199da30`), CPython 3.12.14, the same
`/tmp/a5test-venv`, `TZ=Etc/UTC`, and `PYTHONHASHSEED=0`. Each collected 1,230
nodes, selected 1,225, deselected 5, and stopped at collection on the same five
`ModuleNotFoundError: requests` nodes. No test bodies ran. The shared nodes were
`test_twse_mis_normalization_v2.py`, `test_twse_openapi_normalization_v1.py`,
`test_tpex_openapi_normalization_v1.py`, `test_yahoo_normalized_chart_v1.py`,
and `test_m8c_01_taifex_mis_runtime.py`; new failure delta was **0**. The
default-ci profile reported `network_may_have_occurred=false`.

All R2-specific tests and validators were network-denied. Canonical state remains H2
`INACTIVE`, selected executor `null`, J-B04 `BLOCKING`, Phase J `NOT_STARTED`,
MCP `6`; market GET/HEAD/POST and Security Master live acquisition remain
`0/0/0` and `0` respectively.
