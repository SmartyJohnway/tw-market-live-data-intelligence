# M8R-08E One-Shot Market Evidence MCP Implementation

## Scope

M8R-08E adds exactly one MCP-visible action, `market_fetch_evidence`, to the existing local stdio MCP. It reuses the canonical Unified Request, the Unified Local Service v1, Mode A, Mode B1, the existing M8R-05B execution ticket and atomic claim, bounded execute-once, and Mode C Result/Audit/AI handoff. No canonical Request or Result schema, production market adapter, browser Workbench semantics, remote listener, background work, trading, or MCP SDK generation changes.

Implementation code head: `8f4ffcf587d08a6e7dfa5a40b2b6a249e0d44588`.

Correctness repair implementation head: `37e596ddf5a04c83c7e1c7ddabacb49952c3b334`. Local-operator issuance now uses a process-monotonic microsecond timestamp while the Workbench retains its existing timestamp behavior. Two identical requests in the same wall-clock second therefore get distinct B2 tickets; each can be consumed once, while a second consumption of either remains denied. The action path also projects existing F3/B1 refusal vocabulary (ambiguity, not found, market-hint conflict, unsupported security/capability, blocked/plan-only capability, and resource bounds) instead of collapsing it to `preview_not_authorizable`.

## Contract

The MCP process exposes six tools. The original five remain compatible; the sixth accepts only `{ "request": <canonical Unified Request> }`. `market_fetch_evidence` requires `execution_mode == "execute"`; preview mode is rejected before Local Service action dispatch, ticket creation, or market access. The action uses the fixed loopback `POST /api/unified/fetch-evidence` route and no model-controlled execution fields, source URL, executor, or output location.

The local action composes canonical validation/planning with a server-owned existing B2 ticket whose provenance is `local_operator_mcp` / `local_operator_mcp_action`, then derives the fixed child confirmation protocol server-side. This does not claim a browser click, manual review, or human-presence event. Tickets remain single use and replay-denying; a new invocation gets a new bounded ticket rather than request-level permanent deduplication.

The action response is a Local Service v1 additive envelope containing execution/network accounting, authorization/control identifiers, canonical Result, Result hash, audit and citation references, and existing AI-ready Markdown. Its `market_network_executed` describes this action; Mode C's `additional_market_network_executed` remains false because projection itself does not make another source request. Raw source transport payloads are not exposed.

## Timeout and security boundary

Legacy Local Service calls retain `TIMEOUT_SECONDS = 15.0`. The action alone uses finite `ACTION_TIMEOUT_SECONDS = 85.0`, derived from the existing bounded 70-second execution child plus 15 seconds of bounded orchestration/materialization overhead; it has no retry. The client preserves numeric loopback normalization, `trust_env=False`, disabled redirects, request/response bounds, and no fallback route.

## Validation

Focused deterministic MCP contract/action tests verify six names and annotations, canonical schema reuse, preview rejection before service dispatch, execute delegation, action network-field distinction, raw boundary, and real stdio-to-loopback transport. A real loopback Local Service action using the deterministic transport completed with `execution_outcome=succeeded`, a materialized Mode C Result, and both `market_network_executed=false` and `additional_market_network_executed=false`. B2 coverage verifies truthful local-action provenance and preview-mode no-ticket behavior. External market network calls in non-action tests are zero.

The initial production-probe attempt was not issued because the production-mode Local Service did not become ready within the bounded 75-second local wait; it made no action request or external market call. The subsequent correctness-repair task explicitly authorized one new single-target attempt after environment stabilization.

`default-ci` was attempted twice with isolated pytest base directories. Both attempts stopped during collection on transient Windows filesystem errors (`WinError 1359`) while statting unrelated existing test files; no M8R-08E test failure was reported. The direct focused selection completed `47 passed, 1 warning` with an isolated base directory.

The closure environment was stabilized by assigning a clean local system `TEMP`/`TMP` directory (without a custom pytest base path). `default-ci` then completed with `920 passed, 4 skipped, 1 warning`, return code 0. The focused correctness selection completed `66 passed`. The single authorized production probe then succeeded for TWSE:2330 `current_observation`: control package `umea-v1-a672d00e39fc19ee6a77`, Result `umeresult-v1-ae2ff4281cfca6464108`, result hash `b830ddee5e495e8ddab7cf2fa8f6054f5b1d7aa0e85add8e608194e0885771cc`, and one executed market network action.

## Remaining boundaries

M8R-08F real agent closed-loop acceptance is not implemented or authorized by this change. Existing carried debts (current-observation failure observability, EOD currentness integration, Markdown freshness duplication, and CORS `Origin:null` hardening) remain outside M8R-08E.
