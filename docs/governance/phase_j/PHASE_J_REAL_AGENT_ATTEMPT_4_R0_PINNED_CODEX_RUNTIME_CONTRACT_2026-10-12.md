# Phase J Attempt #4-R0 — Pinned Codex Runtime Identity & Launch Contract Repair

Disposition: `PHASE_J_REAL_AGENT_ATTEMPT_4_R0_PINNED_CODEX_RUNTIME_CONTRACT_READY_FOR_INDEPENDENT_REVIEW`

## Authority and correction

Starting HEAD/TREE: `059285ecc063eb53eeeb804c5f9ad8b957f3bfcc` / `21d1b2a34c78a6c1620921d1b18def8f840e4b68`. PR #326 remains OPEN / Draft / unmerged. Review `5487580175` supersedes review `5487493040` for Attempt #4 launch authority.

The R3-R1 v1 contract remains immutable historical evidence with canonical SHA-256 `343f15876d6a0eb34a283719c8e85a824270285faaa3f187392c8a10589cded0`; it is superseded for future launch use. Root cause: the v1 builder accepted executable path and version as independent caller inputs and did not prove that the selected file emitted that version.

## Pinned runtime

- Accepted executable: `D:\Codex-Workspace\runtime\tw-market-live-data-intelligence\phase-j-real-agent-r4-r2\codex-pinned\0.160.1\codex.exe`
- Observed version: `codex-cli 0.160.1`
- SHA-256: `9e7c59c05cc1ce5677b1f94e835b2ac038ca3be14504e78d558eacdb0ea3f55d`
- Byte size: `326875440`
- PATH wrapper separately reports 0.160.1; OpenAI app binary at the old contract path reports `codex-cli 0.162.0-alpha.2`, SHA-256 `3553cd6e7df5a093d8cb8301cd8088a57e0971aba71ddbe0e67f7f44a15cdf68`, byte size `333357008`.

The v2 contract binds all four pinned values as one measured identity. Creation, offline validation, reservation gate, and future launch gate rehash and re-run `--version` against that same absolute executable. No caller-supplied version is accepted. The future launcher captures stdout JSONL, stderr, `--output-last-message`, and proxy log to deterministic per-slot files. Maximum slots is three; R0 reserved and launched zero.

Successor contract canonical SHA-256: `52a97e0362237cb93eca3733b7fdb1f8a11cdcf66a757b0fdd736623e1a78152`.

## Parser and transport preflight

Pinned Codex `exec --help` exposes `--ignore-user-config`; local login status reports ChatGPT authentication. In an isolated `CODEX_HOME`, `codex mcp list/get` both exited 0 and returned exactly one `phase_j_witness` definition with the expected Python command, proxy args, cwd, service URL, enabled state, and 30-second startup timeout. The override supplied `required=true`; the CLI JSON list/get projection does not echo a `required` member.

The normal Local Service reported healthy, contract `unified_market_evidence_local_service.v2`, and 14 capabilities; it was stopped after preflight. Direct stdio initialize/tools/list against the same proxy command passed with exactly six existing tools. Probe log SHA-256: `60b855dff7a3366ad410a6df3cddd16559b70fed5195c3f667d65b6374f32753`. Semantic calls: zero.

## Boundaries and derived state

Provider inference, formal sessions, semantic MCP calls, J1-21 execution, market GET/HEAD/POST, browser/firecrawl, Security Master acquisition/mutation, package generation, production/schema changes, and MCP surface changes were all zero. Runtime package inventory `caa4b43c67b235ce104c0277b1493031466d39159591e87f56c8765ed0c09096` remained unchanged.

`remaining_obligations=["real_agent_layer"]`; Phase J remains STARTED, Roadmap Phase J unchecked, Phase K NOT_STARTED, and PR #326 remains OPEN / Draft / unmerged. R0 grants no closure credit and does not launch Attempt #4.

## Test-only filesystem correction

A synthetic launcher test initially resolved its default slot directory inside the retained execution root and wrote mock reservation/start marker files there. It did not touch `control/umea-v1-64317f4f3435611c2bb5`, launch a provider, or call MCP semantics. The exact four test-created files were verified and removed; the empty directory was removed. The immutable R4-R2 validator then confirmed all 16 package files and the original inventory SHA-256. Slot evidence now defaults to the separate Git-external `phase-j-real-agent-r4-r2/attempt4` root, and the mock launcher test uses pytest temporary storage only. This incident is retained for independent review.
