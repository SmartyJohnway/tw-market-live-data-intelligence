# M8R-08D Local Operator Action Contract

## Status and supported deployment

This is the forward Phase E contract for M8R-08E. It changes no runtime. The supported deployment is **SELF_HOSTED_LOCAL_OPERATOR**: a user clones and runs this repository on their own machine; their AI host launches the MCP adapter over stdio; the adapter delegates only to the loopback Local Service and governed market sources. Public GitHub availability does not create a hosted service.

Unsupported architecture includes public or remote MCP, public HTTP MCP, SaaS/multi-tenant operation, remote administration, OAuth/accounts, cloud authorization infrastructure, and tenant isolation. There is one MCP product model, **LOCAL OPERATOR MCP**—not Safe and Operator profiles.

## Current truth and historical evidence

The current M8R-08B/08C implementation has exactly five tools: describe, validate, preview, Result read, and AI-handoff export. It has no action tool and cannot authorize or execute. Those historical facts remain correct and must not be rewritten. M8R-08E is the separately authorized successor implementation.

## Conversation-local one-shot retrieval

A clear active-conversation request for current market evidence is sufficient intent for one governed retrieval, for example “幫我查一下 2330 現在的狀況”. The host may notify the operator that it is obtaining one snapshot, but this is UX/operator awareness—not security authorization, authentication, a capability token, or a second human-presence proof.

Clarification remains required to understand genuinely ambiguous targets, scope, or hypothetical questions. It is not a ceremonial confirmation gate. “No silent autonomous execution” means no unsolicited, background, scheduled, polling, recurring, or unrelated fetch. It does not prohibit a one-shot fetch required by the active user conversation.

## Internal governed execution ticket

Existing M8R-05B authorization artifacts remain. For the future MCP action path their canonical role is an **internal execution ticket**: immutable request/plan binding, execution identity, atomic single-use claim, replay protection, receipt, audit lineage, and accounting. M8R-08E may create and consume this existing ticket internally; it must not expose separate `market_authorize_request` or `market_execute_request` tools.

No plan binding, claim, receipt, Result hash, Audit, or replay protection may be removed.

## Preferred M8R-08E action tool

The accepted product-level tool name is `market_fetch_evidence`.

Input is the existing closed MCP envelope:

```json
{ "request": "<canonical unified_market_evidence_request.v1 object>" }
```

`market_fetch_evidence` requires `request.execution_mode == "execute"`. A canonical Request with `execution_mode == "preview"` is rejected/fails closed through an existing-compatible bounded domain-error strategy: it creates no internal execution ticket, makes no market-network request, and is never silently rewritten to `execute`. This preserves the canonical Request, its hash, and all request/plan/ticket bindings without mutation.

There is no MCP-only Request, planner, resolver, Result, source selector, executor selector, target cap, or operation cap. M8R-08E must reuse existing canonical limits as bounded resource/source-load/failure-containment engineering—not as human-permission boundaries.

Lifecycle:

```text
canonical Request → production Mode A validation → deterministic B1 plan
→ internal B2 execution-ticket creation → atomic execute-once claim
→ bounded approved source execution → evidence/receipt/bundle
→ Mode C canonical Result and governed AI handoff → MCP response
```

Validation/ambiguity, blocked capability, bounded-resource, and identity failures preserve their existing fail-closed reason vocabulary. Optional or partial execution preserves governed partial-success/coverage/caveat semantics. The same internal execution ticket is denied by existing single-use/replay protection. A new `market_fetch_evidence` invocation is a new conversation-triggered one-shot retrieval and receives a new internal execution ticket, subject to canonical bounds and current capability; matching a prior normalized request does not create permanent request-level deduplication. `market_read_result` and `market_export_ai_handoff` remain the deterministic reread/reuse path.

## Truthful local-action provenance

The local-operator MCP action invocation is legitimate governed action provenance. M8R-08E may deterministically construct existing M8R-05B-02 execution-ticket decision input from this local action context, but must not fabricate browser review, manual owner review, human-presence proof, or another approval event that did not occur. Any `owner_identity_reference`, `owner_review_reference`, or successor provenance field must truthfully identify the local-operator action path. Exact accepted field materialization remains an existing-authority decision and must be locked by M8R-08E tests.

## Action response and annotations

The action should return enough governed information to answer in the same conversation without a forced second MCP call: `control_package_id`, execution outcome/status, `result_id`, `result_hash`, canonical Result, citations/references, currentness, coverage, caveats, audit reference, and existing AI-ready Markdown where its governed handoff is available. It must not return raw rich facts, source payloads, credentials, headers, or parser internals.

M8R-08E must verify the installed MCP SDK v1 annotation model, but the intended action annotations are: `readOnlyHint=false`, `destructiveHint=false`, `idempotentHint=false`, `openWorldHint=true`. It initiates bounded external market reads and repeat calls can retrieve fresh evidence; it must not be falsely labelled as a deterministic local read. This is not a trading action.

## Phase boundaries and retained invariants

| Tier | Status |
| --- | --- |
| 0: offline/preflight (describe, validate, preview) | current, no market network |
| 1: conversation-local one-shot evidence | required Phase E target |
| 2: persistent watchlists/preferences | Phase F or later, not 08E |
| 3: scheduler/polling/monitoring/notifications | Phase H or later, not 08E |
| 4: broker/account/order/trading action | out of project scope |

Retain stdio transport, loopback Local Service, canonical Request/resolver/catalog/planner/Result/Audit, finite timeouts, request/response bounds, controlled adapters, no generic proxy, no fixture production fallback, and all execution/audit/replay invariants. There is no persistent mutation, background refresh, full-market scan, broker credential, trading, or automatic recurring retrieval in Phase E.

## M8R-08E implementation handoff and acceptance

M8R-08E implementation begins only after explicit **OWNER AUTHORIZATION OF THE MILESTONE**. At runtime, a clear active-conversation retrieval request is sufficient to invoke `market_fetch_evidence`; no second security-authorization ceremony is required. Reuse Local Service Mode A/B1/B2/B2-execution/Mode C services and the existing `/api/unified/*` contract authorities; do not duplicate any business layer. Map Local Service errors through existing sanitized MCP error mapping; never reinterpret domain-invalid, ambiguity, blocked, partial, or failure outcomes.

The existing five tools remain behaviorally unchanged: `market_describe_capabilities`, `market_validate_request`, `market_preview_request`, `market_read_result`, and `market_export_ai_handoff`. M8R-08E adds exactly `market_fetch_evidence`; the expected MCP-visible total is six tools. It removes or renames none of the existing five and adds no separate authorize/execute MCP tools.

Acceptance requires: canonical Request parity; `execution_mode=execute` eligible for the one-shot action path; `execution_mode=preview` rejected with no ticket and no market network; exact existing validation/planning/authorization-ticket/claim/execution/Mode C chain; truthful local-action ticket provenance with no fabricated human/browser approval; same-ticket replay denial and new-fetch allowance; unchanged five legacy tools and total tool count six; one bounded requested fetch; correct no-network preflight and read/export behavior; governed partial/blocked/ambiguous behavior; result/audit/hash/citation preservation; action accounting; no raw expansion; no remote/background/persistent/trading behavior; deterministic regression and real-host closed-loop acceptance.

## Phase E exit gate

Phase E exits only when a natural-language request can lead, in the same active conversation, through canonical Request, validation, planning, one requested bounded retrieval, governed Result/AI handoff, and an AI answer—without browser handoff, manual JSON copy, manual authorization/execution, or Result copy-back. Phase F begins only after that conversation-local execute-once loop is stable.
