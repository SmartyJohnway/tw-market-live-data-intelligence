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

Network-denied lease, runner, governance, and focused regression results are
recorded in the companion JSON ledger. No market or Security Master source was
contacted.
