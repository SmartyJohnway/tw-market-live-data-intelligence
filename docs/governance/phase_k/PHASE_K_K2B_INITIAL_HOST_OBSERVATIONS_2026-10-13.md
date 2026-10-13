# Phase K K2-B — Initial Host Observations

**Date:** 2026-10-13  
**Status:** Hermes evaluated; Antigravity CLI evaluated; ChatGPT pending  
**Host evaluation count:** 2

This record summarizes adjudicable observations only. Raw transcripts remain runtime-only evidence and are not product dependencies. No hidden reasoning is captured or required.

## Shared boundaries

- One K2-A deterministic preparation instance was used.
- Market/source acquisition remained zero throughout these host runs.
- The canonical six-tool MCP surface was unchanged.
- No product schema, source route, execution semantics, or host-specific core fork was added.
- Outcome and `finding_class` are recorded separately.

## Hermes Agent 0.21.5

Overall pilot disposition: **NATIVE_PASS**. Provider/model observed during the run: NVIDIA `nvidia/nemotron-3-super-120b-a12b`.

| Scenario | Outcome | Finding class | Observed TW-Market tools | Semantic observation |
| --- | --- | --- | --- | --- |
| K1-01 | NATIVE_PASS | NONE | tool-surface metadata | Exactly six public tools; five read-only; `market_fetch_evidence` is the bounded action tool. |
| K1-02 | NATIVE_PASS | NONE | `market_describe_capabilities`, `market_fetch_evidence` | Host tried the action tool, but product failed closed with `ambiguous_target` before governed/source execution; host asked for clarification. |
| K1-03 | NATIVE_PASS | NONE | `market_describe_capabilities`, `market_preview_request`, `market_validate_request` | Resolved `TPEX:6488` execute-mode request stopped at owner-approval boundary; no fetch occurred. |
| K1-04 | NATIVE_PASS | NONE | `market_read_result`, `market_export_ai_handoff` | Result/Audit/citation/Handoff lineage was read consistently; no read/export order requirement appeared. |
| K1-05 | NATIVE_PASS | NONE | `market_read_result` | Available evidence remained distinct from stale currentness; source/retrieval times and no-trading constraints were preserved. |
| K1-06 | NATIVE_PASS | NONE | `market_read_result` | `partially_failed` remained distinct from full success; successful current observation remained available while official EOD source failure stayed explicit. |
| K1-07 | NATIVE_PASS | NONE | `market_validate_request` | Unsupported `financial_statements` failed closed at schema validation; no substitution or source execution. |
| K1-08 | NATIVE_PASS | NONE | K1-01 + K1-04 evidence | Native MCP attachment and representative non-trivial Result/Handoff handling succeeded. |

Notes:

- The first K1-03 attempt used a precondition-defective bare `6488` request and was excluded; the valid K1-03 run supplied the resolved `TPEX:6488` target required by K1.
- Windows console rendering showed occasional CP950 mojibake in the observer path, while Hermes structured session export preserved inspectable semantics. This is not classified as a TW-Market compatibility defect.

Runtime evidence references: `k2b-host-evidence/hermes/K1-01` through `K1-07` plus the valid `K1-03-R1` run.

## Antigravity CLI 1.3.3

Overall pilot disposition: **PARTIAL_HOST_LIMITATION**; overall finding class: **HOST_LIMITATION**.

Antigravity CLI headless mode requires pre-granted MCP permission because it cannot display an interactive approval prompt. A minimal persistent rule `mcp(tw-market/*)` was sufficient for normal TW-Market calls. No global auto-approval was enabled.

| Scenario | Outcome | Finding class | Observed TW-Market tools | Semantic observation |
| --- | --- | --- | --- | --- |
| K1-01 | NATIVE_PASS | NONE | MCP contract metadata | Exactly six public tools and the read-only/action distinction were understood without source acquisition. |
| K1-02 | PASS_WITH_DOCUMENTATION | HOST_LIMITATION | `market_describe_capabilities`, `market_validate_request`, `market_preview_request` | Initial headless MCP call was soft-denied; after the scoped MCP allow rule, ambiguous `3333` correctly required clarification with no fetch. |
| K1-03 | NATIVE_PASS | NONE | `market_describe_capabilities`, `market_validate_request`, `market_preview_request` | Resolved execute-mode request stopped at owner approval; no fetch occurred. |
| K1-04 | PARTIAL_HOST_LIMITATION | HOST_LIMITATION | `market_read_result`, `market_export_ai_handoff` plus host-side spill handling | Both TW-Market read tools succeeded, but Antigravity headless large-output synthesis spilled data to host files and then chose an additional `run_command` path that was soft-denied. Final response was empty. |
| K1-05 | NATIVE_PASS | NONE | `market_read_result`, `market_export_ai_handoff` | Available evidence was distinguished from stale currentness; source/retrieval timing and no-recommendation constraints were preserved. |
| K1-06 | NATIVE_PASS | NONE | `market_read_result`, `market_export_ai_handoff`, `market_describe_capabilities` | Partial success and failed official EOD source evidence remained distinct; successful evidence was preserved. |
| K1-07 | NATIVE_PASS | NONE | `market_validate_request` | Unsupported `financial_statements` was rejected by schema validation with no substitution or acquisition. |
| K1-08 | PARTIAL_HOST_LIMITATION | HOST_LIMITATION | K1-01 + K1-04 evidence | MCP transport and ordinary structured results work, but headless large Result/Handoff synthesis may require additional host-side file/command permissions. |

Targeted K1-04 retries established the boundary without widening permissions:

1. Headless MCP permission initially soft-denied; fixed with scoped `mcp(tw-market/*)`.
2. Large output spill then required reading Antigravity's own `brain` directory; scoped recursive read permission was granted.
3. The host subsequently chose `run_command` for synthesis; this remained soft-denied. No `command(*)` or `--dangerously-skip-permissions` was granted.
4. TW-Market `market_read_result` and `market_export_ai_handoff` themselves succeeded and market/source invocation count remained zero.

This is a host/output-permission limitation, not a product compatibility defect. A future host release, documentation pattern, or narrow adapter may remove the limitation without changing TW-Market core semantics.

Runtime evidence references: `k2b-host-evidence/antigravity/K1-01`, `K1-02-R1`, `K1-03`, `K1-04`/`K1-04-R1`/`K1-04-R2`, and `K1-05` through `K1-07`.

## Current pilot state

- Evaluated hosts: **2 / 3** — Hermes, Antigravity CLI.
- Pending initial host: **ChatGPT fresh conversation through Secure MCP Tunnel**.
- Product compatibility defects found: **0**.
- Fresh market/source requests: **0**.
- Phase K remains **STARTED** and the checklist remains unchecked.
