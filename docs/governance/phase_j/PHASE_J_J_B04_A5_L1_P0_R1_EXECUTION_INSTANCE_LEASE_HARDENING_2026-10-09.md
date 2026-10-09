# J-B04-A5-L1-P0-R1 execution-instance lease hardening

Disposition: `J_B04_A5_L1_P0_R1_READY_FOR_EXACT_HEAD_INDEPENDENT_REVIEW`.

The L1-P0 review blocker was Cloud workspace-loss replay: the local consumed
receipt and authorization could disappear with the workspace while the same
Owner authorization and Git revision remained available elsewhere. R1 adds a
random execution-instance secret lease. The Owner authorization binds only its
lowercase SHA-256; the secret stays in an external file in the execution
instance and is never stored in the repository, acceptance package, or
authorization JSON.

The network-free preparation command is:

```bash
python scripts/phase_j_b04_a5_bounded_live_acceptance.py \
  --prepare-execution-lease \
  --execution-environment cloud_clean_source_acceptance \
  --execution-lease-file <EXTERNAL_PATH>
```

It creates at least 32 cryptographically random bytes with
`secrets.token_bytes`, refuses an existing destination and repository-contained
paths, applies owner-only POSIX permissions when supported, and prints only the
public SHA-256 plus safe metadata. Preparing a lease does not grant Owner
authorization, consume a market attempt, or change Git HEAD/TREE.

The future live command requires all four explicit inputs:

```bash
python scripts/phase_j_b04_a5_bounded_live_acceptance.py \
  --live-acceptance \
  --execution-environment cloud_clean_source_acceptance \
  --owner-authorization-json <EXTERNAL_AUTHORIZATION_FILE> \
  --execution-lease-file <EXTERNAL_SECRET_FILE>
```

The Owner authorization has exactly these fields:

```json
{
  "gate": "J-B04-A5",
  "authorized_head_sha": "<EXACT_HEAD>",
  "authorized_tree_sha": "<EXACT_TREE>",
  "execution_environment_class": "cloud_clean_source_acceptance",
  "execution_instance_lease_sha256": "<LOWERCASE_64_HEX>",
  "statement": "<EXACT_LEASE_BOUND_OWNER_STATEMENT>",
  "statement_sha256": "<LOWERCASE_64_HEX>",
  "consumed": false
}
```

The exact statement format is reconstructed from the authorized HEAD and lease
hash:

```text
AUTHORIZE J-B04-A5 LIVE ON HEAD <EXACT_HEAD_SHA>
WITH EXECUTION LEASE <EXECUTION_INSTANCE_LEASE_SHA256>:
exactly 1 GET to
https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL,
retry 0,
no redirects,
target TWSE:2330,
no H3 live calls,
no TWT49U/TPEx/browser fallback,
no raw payload persistence,
no H2 activation,
no J-B04 closure,
no Phase J start.
```

Before consumption the runner validates the exact authorization schema and
statement, HEAD/TREE/main lease, clean tracked worktree, P0 runtime invariants,
output destination, and external secret hash. It rechecks Git state, then
atomically creates the durable consumed receipt before transport. The receipt
contains `execution_instance_lease_sha256`, never the secret. Live mode does
not create or replace a missing lease and does not rewrite the Owner file.

The replay tests cover both recovery cases. In the same workspace, the lease
and consumed receipt survive, so reuse is rejected by the receipt. After a
simulated workspace loss, the same authorization in a fresh run directory is
rejected if the original lease is missing; a newly generated unrelated lease
also fails its hash check. This provides workspace-loss replay resistance
assuming the local secret is not deliberately exported or copied. It is not a
remote transactional lock, hardware-backed identity, or global revocation
service.

R1 leaves P0-R2 identity assurance, H2/H3/H4 production code, source target,
transport bounds, ephemeral capture, normalized evidence, H4 replay, and raw
payload controls unchanged. No production lease was prepared, no Owner live
authorization was created, and no real live execution occurred. Market
GET/HEAD/POST remains `0/0/0`; Security Master live acquisition remains `0`.
H2 stays inactive, selected executor stays null, J-B04 stays blocking, Phase J
stays not started, and MCP remains six. PR #326 remains Draft and unmerged.

## Validation

The network-denied A5 runner tests passed: 63 passed. The combined Phase H/J,
Security Master loader/lifecycle, and Taiwan Market Identity regressions passed:
179 passed, 2 skipped. P0-R2, L1-P0, R1, A1/A2/A3, Phase-H V3, Phase-J GHI,
portable catalog, and runtime Skill/guide validators passed. Compileall, diff
check, and a strict duplicate-key scan of 1,011 JSON files passed.

Default-CI was compared on the exact R1 baseline
`247e66f28424b205ddff1da3dd7cd07e0be9151c` and implementation commit
`4a9bc84c6d59d9475d1b136eecb8b5c0a97f0b95`, using immutable archived trees,
CPython 3.12.14, the same `/tmp/a5test-venv`, `TZ=Etc/UTC`,
`PYTHONHASHSEED=0`, and `python scripts/run_test_profile.py default-ci --json`.
Both collected 1,230 nodes, selected 1,225, deselected 5, and stopped at the
same five collection errors caused by `ModuleNotFoundError: requests`:

- `tests/unit/test_twse_mis_normalization_v2.py`
- `tests/unit/test_twse_openapi_normalization_v1.py`
- `tests/unit/test_tpex_openapi_normalization_v1.py`
- `tests/unit/test_yahoo_normalized_chart_v1.py`
- `tests/unit/test_m8c_01_taifex_mis_runtime.py`

No tests completed after collection. The new failure delta is zero. The
profile recorded `network_may_have_occurred=false`. No market or Security
Master source was contacted.
