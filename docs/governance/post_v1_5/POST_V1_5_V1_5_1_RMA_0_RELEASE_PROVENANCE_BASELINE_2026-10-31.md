# Post-v1.5 — v1.5.1 RMA-0 Release / Provenance Baseline

Date: 2026-10-31 (Asia/Taipei)
Status: **PASS / BASELINE ESTABLISHED**

## 1. Purpose

RMA-0 freezes the exact repository, Native distribution, runtime installation,
Security Master and rollback identities used by subsequent RMA-1 through RMA-11.

No provider/network acquisition, product repair, runtime restart, commit, push,
tag, release or deletion was performed by RMA-0.

Evidence root:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-0\`

## 2. Repository baseline

```text
repository    D:\Codex-Workspace\projects\tw-market-live-data-intelligence
branch        main
HEAD          b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
HEAD tree     2c73a8dd0fd9dc62212aec08c97e60be02cbda0c
origin/main   3f2e5b3a3588d3778d5a4b380c9d8e0a2f41ca05
behind/ahead  0 / 3
VERSION       1.5.0
```
The three local product candidate commits remain:

1. `b38fde12` — Launcher v2 UX and native-entry guard;
2. `8b482be4` — explicit verified-TLS compatibility retry;
3. `b84f9fc8` — Native Mode B2 execute-once wrapper packaging closure.

At RMA-0 start the only working-tree changes were current RMA/governance docs.
Containment result: `unexpected_paths=0`; `git diff --check=PASS`.

The pre-result byte manifest covered 5,403 tracked files plus 3 untracked RMA
records and had SHA-256:

`6f6d7a4daaa307718331b3b69fbdc4832767eaedfac632374514ea8accf6dfbc`

A final post-record manifest is generated after this RMA-0 record and continuity
updates so later RMA groups can compare against the completed governance state.

## 3. Machine baseline

```text
OS           Microsoft Windows 11 Pro
OS version   10.0.26300
OS build     26300
PowerShell   5.1.26100.9818
Native Python 3.13.7
```
## 4. Operational Native distribution

Canonical operational bundle:

`D:\Project-Library\Stable\TW-Market-1.5.0-windows-x64`

Canonical ZIP:

`D:\Project-Library\Stable\TW-Market-1.5.0-windows-x64.zip`

```text
product_version       1.5.0
source_commit         b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
source_tree           2c73a8dd0fd9dc62212aec08c97e60be02cbda0c
ZIP SHA-256           58FF0FCE0D258E1C43C3531DE90CE640641986F35DDCA58D8C1DBABCBFA00D4F
manifest canonical    637d05ff1407984ab42e864aa728e342a0da08b15d946193fa8ede8d93ea4620
manifest member_count 341
```

The distribution manifest explicitly contains
`app/scripts/m8r_06_03_execute_once.py`, SHA-256
`8c3d7765be0bcfb3e9b5c795a1d2773a201e5572f16053dcf1cd85e6f8c8e87e`.

## 5. Installation and runtime authority

```text
installation_status READY
installation_id     47a8eb57-04ea-447c-b905-5a060f7052c4
HOME                C:\Users\weitang\AppData\Local\TW-Market
STATE_ROOT          C:\Users\weitang\AppData\Local\TW-Market\state
app_root            D:\Project-Library\Stable\TW-Market-1.5.0-windows-x64\app
Local Service       127.0.0.1:8000 / healthy
MCP readiness       READY
```
The observed Local Service process is launched from the Native bundle venv and
serves `scripts.tw_market_lifecycle _serve --host 127.0.0.1 --port 8000`.
The observed MCP child is launched from the same Native bundle through
`bootstrap\launch.py mcp --service-url http://127.0.0.1:8000`.

State-authority hashes at baseline:

```text
installation.json SHA-256 888A0F5CB2EA4F3D2A2F586C51C3BD44EDD60D521A39B3056413F8D9308CFD22
active.json       SHA-256 61D38E0AB58D3BA651DBC8BA7023C97CA11F2E6BCE14B87809DA79F2A544C87F
settings.json     SHA-256 250982C341A13EB7CE0D3AABBFEEE37D5D60E7B80F830108BF55905C0C3647AE
```

## 6. Security Master authority

```text
status                 ACTIVE
release_id             security-master-20261031T060730Z
release state          QUALIFIED
knowledge universe     54890
execution eligible     2204
quarantine             0
release index SHA-256  0148012346313754cda900c33f13e97fd400528192781c9548838559400e3e0e
release manifest SHA   5e1feb7a7220516a7f5a7a933e8468f4664e95c462ef16f0f718217df11c0fdb
```

The release manifest records producer repository commit `8b482be4...`; the later
`b84f9fc8` package-only fix did not rebuild Security Master identity content.

## 7. Preserved rollback references
Two prior operational Native distributions remain preserved and are not deleted:

```text
pre-modeb2fix folder
  source_commit 8b482be49962cb2403cdcd3b11130a93d4a3cfa3
  source_tree   29e4c4b7554c5aad5d1019c8bbf9434318577704
  ZIP SHA-256   52878B10FDAD62AB27D6F04C3B229F98998C728349D7E6BC4B554CB9CE62125A

pre-tlsretry folder
  source_commit b38fde12bbcc11853f41ac9cb8482c712797d4b3
  source_tree   b8c9fcea9af892d9ab9ffc91b5037457072cbc9d
  ZIP SHA-256   9FB3CB9BC592301F6C98D1FAB25F9FBD85805DBA0953B782A303A36CFF512CDB
```

These are rollback/reference evidence only. RMA-0 performed no rollback.

## 8. RMA-0 disposition

```text
REPOSITORY_PROVENANCE      PASS
NATIVE_PROVENANCE          PASS
RUNTIME_IDENTITY           PASS
SECURITY_MASTER_AUTHORITY  PASS
ROLLBACK_REFERENCE         PASS
SCOPE_CONTAINMENT          PASS
PROVIDER_NETWORK_ACTIVITY  NONE
PRODUCT_MUTATION           NONE
DELETE                     NONE
```

RMA-0 establishes the baseline for later RMA groups. The next planned group is
`RMA-1 — Fresh first-run installation`.

RMA-0 PASS does not authorize a `VERSION` change, commit, push, tag, release,
Phase M, P2–P5, or repair of `RMA-D001`.
