# Phase J Real-Agent Attempt #3-R1 — MCP Attachment Contract

Disposition: `PHASE_J_REAL_AGENT_ATTEMPT_3_R1_FORMAL_MCP_ATTACHMENT_CONTRACT_READY_FOR_INDEPENDENT_REVIEW`

This network-free, provider-free tranche establishes a reproducible future Codex formal-session MCP attachment contract. It did not launch a provider session, make semantic MCP calls, execute J1-21, or award closure credit.

## Authority and historical outcome

- Starting branch/head/tree: `phase-j/j-b04-a5-bounded-live-source-acceptance` / `2de3db62d6c63eea26e41f7b0d3b6c4958d41bc6` / `5996666cf9c47f63020ff908f79c3729072f0f89`.
- PR #326 remains OPEN / Draft / unmerged; exact Attempt #3 review: `5486947847`.
- Attempt #3 remains immutable: `PHASE_J_REAL_AGENT_ATTEMPT_3_HARD_BLOCK_MCP_WITNESS_PROXY_NOT_ATTACHED`. The model launched, but no witness proxy event log or semantic MCP call was observed.
- Independent root-cause classification: `FORMAL_CODEX_SESSION_EFFECTIVE_MCP_ATTACHMENT_NOT_ESTABLISHED`. The exact historical omitted CLI argument was not established.

## Future formal-session contract

Canonical launch-contract SHA-256: `343f15876d6a0eb34a283719c8e85a824270285faaa3f187392c8a10589cded0`.

- Codex: `C:\Users\weitang\AppData\Local\OpenAI\Codex\bin\9691020b546a15b2\codex.exe` (`codex-cli 0.160.1`), `exec --ignore-user-config --ephemeral --json`, with an explicit session-scoped `-c` override. CLI help states authentication continues to use CODEX_HOME, so `--ignore-user-config` isolates MCP config without discarding the authenticated runtime.
- Required MCP server: `phase_j_witness`, stdio, enabled and `required=true`, startup timeout 30 seconds. The executable is the absolute Python path in the JSON contract; the server argv explicitly binds the accepted proxy, fresh formal witness log path, and control package `umea-v1-64317f4f3435611c2bb5`.
- Proxy cwd: `D:\Codex-Workspace\projects\tw-market-live-data-intelligence`. It launches the existing `scripts/run_unified_market_evidence_mcp.py`.
- Local Service: `http://127.0.0.1:18264`. Prompt SHA-256: `8ee5459c7217ff34d091385f588d8b53794a1053ace2a44e5b262e4f6757621c`. Codex JSON events, stderr, and final output paths are bound in the structured contract.
- The formal log path is currently absent. The dry-probe log was moved to a distinct evidence path, so the future contract will fail closed if its unique log path already exists.

## Dry preflight evidence

Local Service `/api/health`: PASS; contract `unified_market_evidence_local_service.v2`; capability count 14; service stopped after the check. Isolated Codex `mcp list` and `mcp get` both exited 0 and showed exactly one configured server. A type-negative control rejected `required="yes"` with “expected a boolean,” verifying the required field is parsed as a boolean.

The exact proxy command/args/cwd/env from the launch contract was then connected through an MCP stdio client. Initialize and tools/list passed with protocol `2025-11-25`, exactly six existing tools, proxy exit code 0, and zero semantic calls. Probe event-log SHA-256: `60b855dff7a3366ad410a6df3cddd16559b70fed5195c3f667d65b6374f32753`.

The retained R4-R2 package inventory was recomputed from its physical files: `caa4b43c67b235ce104c0277b1493031466d39159591e87f56c8765ed0c09096` (16 files), matching accepted authority. Attempt #3 receipt/output and R4-R2 evidence hashes are checked by the validator.

## Boundaries and next state

Provider inference, real-agent sessions, semantic MCP calls, J1-21 executions, source fixture invocation delta, market GET/HEAD/POST, Browser Use, Firecrawl, Security Master acquisition/mutation, production changes, public schema changes, and MCP tool-count changes were all zero.

`remaining_obligations=["real_agent_layer"]`; Phase J remains STARTED, Roadmap Phase J unchecked, Phase K NOT_STARTED. This does not authorize Attempt #4.

Machine validation: `python scripts/validate_phase_j_attempt3_r1_mcp_attachment.py`.
