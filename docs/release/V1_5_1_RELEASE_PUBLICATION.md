# TW-Market v1.5.1 — Official GitHub Stable Publication

**Status: PUBLISHED / LATEST STABLE.**
2026-11-04 15:57:03 UTC = 2026-11-04 23:57:03 Asia/Taipei.

- [Official GitHub v1.5.1 Release](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.1)
- GitHub Release ID: `434114288`
- ProductVersion: `1.5.1`
- Source commit (annotated tag target):
  `1f3666eefdca7e2e9a1c88099f802696bf7970d6`
- Frozen Git tree: `d67e9bc1db34ff268b5b8d0f2a301d1a211df3b6`
- Annotated Git Tag object: `6f7d207ba7f58b82a76f309d7d301f200b2f34eb`
- Publication Manifest SHA-256:
  `791b42375f4f9d747d4389fcd0113dab16367aa04d6bd6b8bc8b95598be7af2b`
- Exact GitHub Windows/Linux main workflow:
  [successful run 41854420205](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/actions/runs/41854420205)

## What v1.5.1 changes for Windows Native users

Compared with v1.5.0, the core user-facing improvement is **a simpler,
guided Windows Native workflow** — from GUI first-run Setup and clear
daily controls to recoverable Workbench requests and auditable AI delivery.
This was Owner-driven and verified through RMA-0 through RMA-11.

- **First run (RMA-1):** Launch from `Launch-TW-Market.cmd` with clear
  Python readiness, one `Set Up TW-Market` step and transition to daily view;
  no developer shell commands are needed in the primary GUI path.
- **Daily operation (RMA-2/3):** one Launcher for Runtime, Workbench, Local
  MCP and Security Master status, plus explicit Start/Stop, Refresh,
  Diagnose, Install/Update and required Restart guidance.
- **Real local integration and safe request planning (RMA-4/5/6/7):**
  fixed six-tool MCP; identity resolution; capability-based Validate/Preview
  and authorization; verified official-source/TLS handling.
- **Truthful results and recovery (RMA-8/9):** Result/Audit/evidence
  hash/receipt traceability; fail-closed blocked states and bounded recovery
  rather than misleading success or hidden retries.
- **Portability (RMA-10):** isolated packages tested in different
  directories, including a path with spaces and a relocated HOME, with
  Launcher, local service and MCP startup-check verified.
- **End-user Workbench UX (RMA-11):** default-collapsed technical JSON,
  Request Builder aligned to current capability selection, blocked Preview
  explanations and recovery, authorization-readiness guidance,
  a separate explicit network-confirmation step, Execute Once feedback,
  and consistent Mode C Result/Audit/AI-ready Markdown.

[Complete guided Windows Native journey and RMA-0–11 traceability](../operator/WINDOWS_NATIVE_V151_GUIDED_WORKFLOW.md)

The accepted Owner E2E is the original RMA evidence carried forward through
source/runtime-equivalence into this frozen published release; do **not**
describe it as a newly repeated post-publication live E2E.
Python 3.13 x64 remains an external prerequisite, and neither Setup nor
Launcher startup acquires market data automatically.

## Six officially published release assets

All six were downloaded fresh **after official publication**, with exact
filename, byte-size and SHA-256 matches versus validated local staging assets.
Their GitHub public API digests independently match the same values.

| Role | Filename | Bytes | SHA-256 |
|---|---|---:|---|
| Native ZIP | `TW-Market-1.5.1-windows-x64.zip` | 40668112 | `e444852cfc5864ffe3651d90b1751f1e2e22385e6743d8d26581725e49475016` |
| Native sidecar | `TW-Market-1.5.1-windows-x64.zip.sha256` | 98 | `518cb715d7988fee543d95188a27abd214e6247e7b87382f6ddd4f9ae92c3f1c` |
| Windows MCPB | `tw-market-unified-mcp-v1.5.1-win-x64.mcpb` | 40848020 | `3bc7b12184076e241e61abf4c4525c846de12bce5aa2340c52ead497be2f9a39` |
| MCPB sidecar | `tw-market-unified-mcp-v1.5.1-win-x64.mcpb.sha256` | 108 | `f1e473907c3041b900c4307ad5646edc5fede7e41f24e3bab9f6f19f23390422` |
| First-party SBOM | `TW-Market-1.5.1-first-party-sbom.json` | 101953 | `4be21c477be71520e2bdc87b9e49d35e08dc8bea85a6654b12a3969c418913f2` |
| Publication Manifest | `TW-Market-1.5.1-publication-manifest.json` | 7235 | `791b42375f4f9d747d4389fcd0113dab16367aa04d6bd6b8bc8b95598be7af2b` |

Download base URL:
`https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/download/v1.5.1/`.
Append the exact filename from the table. Verify before running or importing.

## Release acceptance and limitations

- Formal Release Readiness: **PASS** with 15 blocking gates passed.
- Canonical `release-blocking-ci`: PASS; final `main` GitHub Windows and
  Linux workflow: SUCCESS.
- Native Windows offline acceptance: 21-stage PASS (including expected
  negative/fail-closed tests), MCPB structural/offline six-tool acceptance:
  PASS, Docker `linux/amd64` local build/replacement acceptance: PASS.
- Independent Manifest review and published six-asset remote readback: PASS.
- Supplemental diagnostics: **`default_ci=FAIL` and
  `full_non_network=FAIL`**; these were retained as nonblocking
  historical profiles, **not** asserted PASS.
- Live-owner E2E assurance is prior accepted RMA evidence carried forward by
  runtime equivalence, **not** fresh live full-market replication.
- Signing authority: **`NOT_ESTABLISHED`**. SHA-256, SBOM and typed
  manifest provide integrity/provenance, not publisher cryptographic
  signatures.
- Windows 11 x64 is Native Tier-1; CPython 3.13 is canonical for
  release/build/CI; Windows MCPB runtime declares `>=3.13,<3.14`.

## Publication and authorization boundaries

- `v1.5.1` GitHub Stable is published, but there is **no Docker Registry
  image release** and no MCP Registry `v1.5.1` publication.
- Official MCP Registry
  [entry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.SmartyJohnway%2Ftw-market-live-data-intelligence/versions/latest)
  was independently checked on 2026-11-05: `version=1.0.0`,
  `status=active`, `isLatest=true`; checked-in `server.json`
  remains `1.0.0` by design.
- Phase M: **`NOT_AUTHORIZED`**. No scheduler/monitoring, automated data
  fetch, hidden Watchlist execution, full-market scan, trading or
  realtime quote guarantee is included.
- Prior frozen stable [`v1.5.0`](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0)
  remains available, unchanged.
- Source notes file
  [`V1_5_1_RELEASE_NOTES_DRAFT.md`](V1_5_1_RELEASE_NOTES_DRAFT.md)
  is the **frozen exact-byte prepublication input** bound to the published
  manifest. Its words `DRAFT / Unpublished` describe its historical
  preparation state, not the currently Published Release. **Do not
  edit or rewrite that exact source/manifest binding**.
- Future documentation-only commits on `main` create a new branch commit
  but **do not move** `v1.5.1` Tag, alter six assets or redefine the
  frozen release tree/Source SHA.

## User navigation

- [Operator Quick Start: Launcher/Native, MCPB, Source](../operator/QUICK_START.md)
- [MCP Distribution](../distribution/MCP_DISTRIBUTION.md)
- [Unified MCP Reference](../reference/MCP_REFERENCE.md)
- [Current README](../../README.md)
- [繁體中文 README](../../README.zh-TW.md)
- [Release index](README.md)
