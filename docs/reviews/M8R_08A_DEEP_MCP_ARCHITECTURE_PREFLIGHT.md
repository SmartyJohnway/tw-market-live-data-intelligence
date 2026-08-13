# M8R-08A Deep MCP Architecture / Security Preflight

## Decision

`PASS_WITH_CAVEATS`. The exact recommended M8R-08B v1 is:

- one host-spawned **stdio** MCP sidecar;
- the sidecar delegates only through bounded HTTP to the existing loopback `unified_market_evidence_local_service.v1` routes;
- no compatibility transport in v1 and no new listener;
- exactly five tools: describe capabilities, validate, preview, read governed Result, and export governed AI handoff;
- no MCP authorization or execution tool in v1;
- Strategy A (safe tools only); the browser Workbench remains the accepted authorization/execution surface;
- no MCP resources, prompts, sampling, or elicitation in v1;
- `mcp==1.29.0` for the separately authorized implementation, with a deliberate future SDK-v2 migration gate;
- no market-specific MCP schema, projector, registry, approval state, or artifact vocabulary.

This is the smallest architecture that preserves one semantic/runtime stack. M8R-08B remains `NOT_AUTHORIZED`; this review adds no MCP runtime or dependency.

## Scope, method, and evidence discipline

Repository code, schemas, tests, M8R-07 contracts, and post-merge acceptance were reconstructed before the external MCP design. External evidence was retrieved on **2026-08-12** and is labeled `SPEC`, `SDK_DOC`, `SDK_SOURCE`, `HOST_DOC`, `HOST_SOURCE`, `OFFICIAL_ISSUE_OR_DISCUSSION`, `ECOSYSTEM_EVIDENCE`, `INFERENCE`, or `UNKNOWN`. The source appendix supplies a direct URL and the exact question each source supports.

No TWSE, TPEX, or TAIFEX production source was contacted. Package, protocol, host-documentation, and official-source research is not a market-data call.

## Existing authority graph

The MCP adapter must end at the accepted Local Service boundary; it must not jump around it or reproduce any node below.

```text
unified_market_evidence_request.v1 schema
  -> Mode A / F3 validation
       Security Master + canonical capability catalog
  -> Mode B1 planning
       05B routing matrix + deterministic planner
  -> Mode B2 authorization
       Preview/plan identity + scope binding
  -> Mode B2 execute-once
       explicit execution/network confirmation
       atomic single-use claim + production executor registry
  -> Receipt + Bundle + governed evidence
  -> Mode C read-or-materialize
       canonical Result + Audit + AI-ready Markdown
  -> unified_market_evidence_local_service.v1
       /api/unified/*
  -> future stdio MCP transport adapter
```

| Authority | Current repository authority | MCP rule |
|---|---|---|
| Canonical request | `schemas/unified_market_evidence_request.v1.schema.json` | Nest the unchanged object under `request`; do not copy its fields into an MCP-specific market schema. |
| Validation / identity | `server/services/unified_mode_a.py`, `scripts/m8r_05a_f3/**` | Delegate through `POST /api/unified/validate-request`. |
| Planning | `server/services/unified_mode_b1.py`, `scripts/m8r_05b_01/**` | Delegate through `POST /api/unified/preview-request`. |
| Capability description | catalog + 05B routing matrix + production executor metadata, in the precedence fixed by M8R-07 | Delegate through `GET /api/unified/capabilities`; never infer executability in MCP. |
| Authorization | `server/services/unified_mode_b2.py` | Not exposed in MCP v1. No new approval state. |
| Execution / claim | `server/services/unified_mode_b2_execution.py`, `scripts/m8r_05b_03/**`, `scripts/m8r_06_03_production_adapter.py` | Not exposed in MCP v1. Never import or reproduce this path. |
| Result / Audit / Markdown | `server/services/unified_mode_c.py`, `scripts/m8r_05c/**` | Read or deterministically materialize only through the existing Local Service operations. |
| Transport contract | `server/services/unified_local_service.py`, `server/unified_workbench_router.py`, `docs/protocol/M8R_07B_LOCAL_SERVICE_CONTRACT.md` | Bind adapter v1 explicitly to `unified_market_evidence_local_service.v1`. |
| Browser client | `frontend/unified-workbench/**` | Remains a client of the same router and the sole accepted human action surface. |

The pre-M8R-07 `server/mcp_server.py` is a historical surface with direct legacy behavior. It is not an authority for the unified adapter, must not be imported or extended by M8R-08B, and should be clearly distinguished in operator configuration.

## Current protocol and SDK state

- `SPEC`, HIGH: the current stable MCP specification is **2026-07-28**. It retains stdio and Streamable HTTP as standard transports; the standalone legacy HTTP+SSE transport is deprecated. [Current specification](https://modelcontextprotocol.io/specification/2026-07-28), [transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports) (retrieved 2026-08-12).
- `SPEC`, HIGH: tools remain model-controlled and tool annotations are advisory, untrusted hints. Structured tool results may carry `structuredContent`, declared output schemas, and ordinary content. [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) (retrieved 2026-08-12).
- `SPEC`, HIGH: current elicitation uses an explicit client-mediated input-required interaction with accept/decline/cancel semantics; protocol support does not imply that any particular host renders a human UI. [Elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation) (retrieved 2026-08-12).
- `SDK_DOC`, HIGH: the current stable Python SDK is **2.0.0**. Same-ASGI mounting and modern elicitation exist, but v2 changes the low-level server API used by this repository's legacy server. [v2.0.0 release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0), [migration guide](https://py.sdk.modelcontextprotocol.io/migration/) (retrieved 2026-08-12).
- `SDK_DOC`, HIGH: the current v1 maintenance release is **1.29.0**. The repository currently declares `mcp>=1.0.0,<2`, and the acceptance interpreter had 1.28.1 installed. Safe stdio tools do not need v2-only multi-round-trip behavior. [v1.29.0 release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v1.29.0), [v1 docs](https://py.sdk.modelcontextprotocol.io/v1/) (retrieved 2026-08-12).

The implementation recommendation is therefore a deliberate v1 maintenance pin, not a claim that v1 is the current stable major:

```text
mcp==1.29.0
SDK_V2_MIGRATION_REQUIRED_BEFORE_MRTR_APPROVAL_TOOLS_OR_STREAMABLE_HTTP
```

That future migration must explicitly port or retire the historical low-level MCP server; it must not be hidden inside M8R-08B.

## Transport architecture comparison

| Criterion | A — same-ASGI Streamable HTTP | B — separate Streamable HTTP | C — stdio sidecar to Local Service | D — hybrid HTTP + stdio |
|---|---|---|---|---|
| Semantic duplication | low if it calls Local Service; direct imports would be high | low with HTTP delegation | **lowest and explicit** with HTTP delegation | low in logic, high in transport policy |
| Lifecycle / Windows | parent ASGI must own MCP session-manager lifespan | second service, port and shutdown owner | host owns child process and pipes; no port | both lifecycle models |
| Existing service dependency | in-process but still should call formal contract | Local Service must run | Local Service must run | topology-dependent |
| Failure isolation | shared process/lifespan | separate process | separate sidecar; clean bounded failure | two failure modes |
| Session state | SDK configuration-dependent | SDK configuration-dependent | ordinary stdio session | both |
| Host portability | good for local HTTP hosts; no benefit to cloud hosts unable to reach loopback | same limitation | broad local desktop/CLI support | broadest, at double cost |
| Network attack surface | adds `/mcp` on existing listener | adds listener | **no MCP listener** | one or two listeners |
| Host/Origin/DNS-rebinding work | required and distinct from CORS | required | not applicable to MCP transport | required for HTTP half |
| Dependency impact | v2 migration is the supported current mounting path | v2 preferred | v1.29 supports required safe stdio surface | v2 plus bridge compatibility |
| Testing complexity | high: ASGI paths, lifespan, HTTP security | high: process/listener/security | **lowest** | highest |
| ChatGPT web | loopback still unreachable directly | loopback still unreachable | needs documented Secure MCP Tunnel; no direct web connection | HTTP remains unreachable from cloud |
| Recommendation | technically feasible, not canonical | reject for v1 | **canonical** | reject for v1 |

`INFERENCE`, HIGH: a second or same-process localhost HTTP transport does not solve cloud-to-loopback reachability. ChatGPT's direct connector expects a reachable HTTPS server; its documented Secure MCP Tunnel is the development/private bridge. [ChatGPT connection documentation](https://developers.openai.com/plugins/deploy/connect-chatgpt) (retrieved 2026-08-12).

### Same-ASGI source-level feasibility

Result: **`SUPPORTED_WITH_CONSTRAINTS`**.

Official SDK v2 exposes `MCPServer.streamable_http_app()` for FastAPI/Starlette composition. The parent application's lifespan must run the MCP session manager because a mounted subapplication's lifespan does not run automatically. Mounting the default MCP inner path below `/mcp` can yield `/mcp/mcp`; an inner root path must be configured deliberately. [ASGI integration](https://py.sdk.modelcontextprotocol.io/run/asgi/), [deployment/lifespan guidance](https://py.sdk.modelcontextprotocol.io/run/deploy/) (`SDK_DOC`, HIGH, retrieved 2026-08-12).

For the hypothetical same-ASGI option, use current-protocol **sessionless** operation because the proposed tools keep no MCP-side state; legacy clients that require initialize/session identifiers would need the SDK's explicit compatibility/session mode and separate reconnect tests rather than silently sharing current behavior. No MCP session may become authorization state. The adapter would mount its inner app at `/` beneath parent `/mcp`, and the parent lifespan would enter `mcp.session_manager.run()` exactly once.

The SDK's transport-security code separately validates Host and Origin and returns bounded rejection statuses; this is DNS-rebinding protection, not FastAPI CORS. An absent Origin is allowed. The concrete hypothetical policy is Host allowlist `127.0.0.1:<configured-port>`, `localhost:<configured-port>`, and `[::1]:<configured-port>` only; Origin allowlist is exact `http://127.0.0.1:<configured-port>`, `http://localhost:<configured-port>`, and `http://[::1]:<configured-port>` where the SDK accepts bracketed IPv6. **`Origin:null` is rejected for `/mcp`**, even though current Workbench CORS accepts it. A no-Origin non-browser MCP request remains acceptable under the SDK's transport policy. [Transport security source](https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/transport_security.py) (`SDK_SOURCE`, HIGH, retrieved 2026-08-12).

One process can technically serve Workbench, REST, and MCP without startup market network. It is not selected because it adds lifecycle/path/security coupling and forces a deliberate SDK-v2 migration without a demonstrated local-client benefit.

## Host compatibility conclusion

The detailed, dated evidence is in [M8R-08A MCP Host Compatibility Matrix](M8R_08A_MCP_HOST_COMPATIBILITY_MATRIX.md). Summary:

| Host | Recommended stdio usable | Streamable HTTP | Elicitation | Consequence |
|---|---:|---:|---|---|
| Codex | yes | yes | `SUPPORTED_WITH_LIMITATIONS` | safe stdio v1 works; noninteractive/delegated elicitation is not a universal approval boundary |
| ChatGPT web | no direct local stdio | public HTTPS; private/local through tunnel | `SUPPORTED_WITH_LIMITATIONS`, exact modes unpublished | no direct Local-First connection; do not add a listener merely for naming compatibility |
| Claude Desktop | yes through local extension/config | remote HTTP documented | `NOT_DOCUMENTED` | manually verify stdio; never assume Desktop elicitation from Claude Code support |
| Claude Code | yes | yes | `SUPPORTED_WITH_LIMITATIONS` | safe v1 works; interactive mode would be required for future actions |
| VS Code Copilot Chat | yes | yes | `SUPPORTED` (form and URL) | safe v1 works even when approvals are bypassed because no action tool exists |
| Gemini CLI | yes | yes | `NOT_SUPPORTED` | proves an elicitation-dependent action surface is not portable |
| Hermes Agent | yes | yes | `SUPPORTED_WITH_LIMITATIONS` | current form acceptance does not collect required structured values; URL mode declines |
| MCP Inspector Web | yes | yes | `SUPPORTED_WITH_LIMITATIONS` across legacy/current protocol eras | preferred deterministic protocol debugger; CLI is not an elicitation test host |

Host tool approval, MCP elicitation, and Local Service confirmation fields are separate controls. Several hosts can trust, remember, bypass, or auto-approve tools. None of those host choices creates a server-verifiable human attestation.

## Candidate tool surface

The 1:1 model is selected. Combined convenience tools would collapse validate/preview or read/export boundaries, obscure which canonical operation failed, enlarge schemas and responses, and create MCP-only semantics. Higher-level conversational tools would duplicate interpretation and governance. Seven Local Service concepts do not imply seven exposed tools: semantic mapping is 1:1 only for the five safe operations.

| Tool | Local Service mapping | Authority / effects | Approval, claim, replay | Annotations `(readOnly, destructive, idempotent, openWorld)` | v1 disposition |
|---|---|---|---|---|---|
| `market_describe_capabilities` | `GET /api/unified/capabilities` | three-authority projection; no write/network | none; replay-insensitive | `(true,false,true,false)` | `EXPOSE_MCP_V1` |
| `market_validate_request` | `POST /api/unified/validate-request` | canonical Request/F3; no write/network | none; replay-insensitive | `(true,false,true,false)` | `EXPOSE_MCP_V1` |
| `market_preview_request` | `POST /api/unified/preview-request` | Mode B1 offline plan; no write/network | creates no authorization; replay-insensitive | `(true,false,true,false)` | `EXPOSE_MCP_V1` |
| `market_authorize_request` | `POST /api/unified/authorizations` | would create executable authority and local artifacts | explicit human boundary; non-idempotent | future conservative `(false,true,false,false)` | `DEFER_FROM_V1` |
| `market_execute_request` | `POST /api/unified/executions` | market network possible; artifacts written | consumes authorization and atomic claim; replay-sensitive | future `(false,true,false,true)` | `DEFER_FROM_V1` |
| `market_read_result` | `POST /api/unified/result-package` | Mode C verify/read or deterministic materialization; no new market call | no authorization/claim; idempotent for same governed package | `(false,false,true,false)` | `EXPOSE_MCP_V1` |
| `market_export_ai_handoff` | `GET /api/unified/result-package/{id}/handoff` | same governed Result/Audit/Markdown; materialization may write; no new market call | no authorization/claim; idempotent | `(false,false,true,false)` | `EXPOSE_MCP_V1` |

Annotations are semantic/UX hints, never security controls (`SPEC`, HIGH). `read_result` and `export_ai_handoff` are not marked read-only because their existing service path may deterministically materialize missing Mode C artifacts. Their `openWorldHint=false` is about the tool's own interaction: it opens no external world during the call, even though governed output can contain evidence fetched by a prior authorized execution. Execute would be open-world because it can contact approved market sources; it is non-idempotent because it consumes a single-use claim. Calling source retrieval “destructive” is conservative for future host review, not a claim that it trades securities.

### Complete effect ledger

- **`market_describe_capabilities`** — purpose: deterministic support/disposition discovery; input authority: closed empty MCP envelope; output authority: Local Service capability envelope derived from catalog, routing matrix, then registered-executor metadata; filesystem write: no; market network: no; creates/consumes authorization: no/no; consumes atomic claim: no; replay-sensitive: no; idempotent: yes; open-world: no; human approval: no; model-autonomous-safe: yes; disposition/reason: `EXPOSE_MCP_V1`, because it is a bounded read of committed/current local authority.
- **`market_validate_request`** — purpose: canonical identity/capability/schema validation; input authority: unchanged `unified_market_evidence_request.v1` nested in a closed transport envelope; output authority: F3 validation envelope; filesystem write: no; market network: no; creates/consumes authorization: no/no; consumes claim: no; replay-sensitive: no; idempotent: yes; open-world: no; human approval: no; autonomous-safe: yes; disposition/reason: `EXPOSE_MCP_V1`, because validation is already an autonomous-safe Local Service operation.
- **`market_preview_request`** — purpose: deterministic offline plan/estimate; input authority: same canonical Request envelope; output authority: existing validation + Mode B1 Preview/Plan envelope; filesystem write: no; market network: no; creates/consumes authorization: no/no; consumes claim: no; replay-sensitive: no; idempotent: yes; open-world: no; human approval: no; autonomous-safe: yes; disposition/reason: `EXPOSE_MCP_V1`, preserving Preview ≠ Authorization.
- **`market_authorize_request`** — purpose: create bound execute-once authority; input authority: existing Mode B2 authorization request; output authority: existing Authorization/control package; filesystem write: yes; market network: no; creates/consumes authorization: yes/no; consumes claim: no; replay-sensitive: yes because duplicate authority creation is consequential; idempotent: no; open-world: no; human approval: required; autonomous-safe: no; disposition/reason: `DEFER_FROM_V1`, because model arguments and host approval are not portable human proof and v1 deliberately has no elicitation boundary.
- **`market_execute_request`** — purpose: governed execute-once; input authority: existing Mode B2 execution/confirmation contract; output authority: existing claim, Receipt and Bundle; filesystem write: yes; market network: possible when authorized plan requires it; creates/consumes authorization: no/yes; consumes claim: yes; replay-sensitive: yes; idempotent: no; open-world: yes; human and explicit network confirmation: required; autonomous-safe: no; disposition/reason: `DEFER_FROM_V1`, because it is a non-retryable action boundary with non-uniform host human UX.
- **`market_read_result`** — purpose: verify/read or deterministically materialize governed Mode C package; input authority: canonical `control_package_id`; output authority: existing Result-package envelope and canonical Result/Audit; filesystem write: possible only for accepted deterministic Mode C materialization; market network: no; creates/consumes authorization: no/no; consumes claim: no; replay-sensitive: no; idempotent: yes; open-world: no for this call; human approval: no after governed package exists; autonomous-safe: yes; disposition/reason: `EXPOSE_MCP_V1`, because it cannot execute and reuses the verified projector.
- **`market_export_ai_handoff`** — purpose: return governed AI-facing Result/Markdown/citations; input authority: canonical `control_package_id`; output authority: existing Local Service handoff envelope; filesystem write: possible only through the same deterministic Mode C materialization; market network: no; creates/consumes authorization: no/no; consumes claim: no; replay-sensitive: no; idempotent: yes; open-world: no for this call; human approval: no after governed package exists; autonomous-safe: yes; disposition/reason: `EXPOSE_MCP_V1`, because it reuses canonical projection and does not expose raw evidence.

The guaranteed autonomous-safe set is:

```text
market_describe_capabilities
market_validate_request
market_preview_request
market_read_result
market_export_ai_handoff
```

It creates no authorization, consumes no claim, initiates no market request, does not widen evidence exposure, and excludes raw rich facts through the already accepted Local Service handoff.

## Exact schema and output design

The implementation-ready schemas are recorded in [M8R-08A MCP Implementation Blueprint](M8R_08A_MCP_IMPLEMENTATION_BLUEPRINT.md). Binding choices are:

- describe has an empty, closed input object;
- validate and preview use `{ "request": <unchanged unified_market_evidence_request.v1> }`, with `additionalProperties:false` at the envelope;
- read and export use one closed `control_package_id` envelope matching the existing identifier contract;
- no top-level copy of Request fields and no MCP-specific market enums;
- each output contract maps 1:1 to the Local Service envelope; declare `outputSchema` where a committed canonical schema can be composed without copying authority, and otherwise retain exact fixture/key parity until that transport schema is formalized;
- return canonical JSON in `structuredContent` plus short bounded text; export additionally returns the existing AI-ready Markdown as text;
- no resource links, embedded raw files, file URIs, absolute paths, headers, cookies, secrets, raw evidence, parser state, or rich facts;
- no new “compact Result” in v1. If size later proves harmful, any compact view must be a versioned projection of canonical governed output, not a second Result.

`SPEC`, HIGH: current tools support JSON Schema inputs, declared structured output, and ordinary content. Annotations remain hints. [Tool schema and results](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) (retrieved 2026-08-12).

## Approval threat model

Strategy A eliminates the MCP action entry point in v1 but does not erase local-machine threats. The adapter must still fail closed and preserve all Local Service bindings.

| Threat | Existing Local Service protection | MCP responsibility | Remaining risk and required fail-closed behavior |
|---|---|---|---|
| T1 model self-authorization | explicit authorization contract and identity binding | do not register authorize | `confirm_authorization=true` is never proof; unknown tool fails |
| T2 model self-execution | confirmations, preflight, atomic claim | do not register execute | tool cannot reach execution; no fallback to REST proxying |
| T3 prompt injection | governed projection and raw-fact exclusion | static tool descriptions; label returned evidence as data | never construct schemas/descriptions from evidence; source text cannot invoke actions |
| T4 tool-description confusion | fixed Local Service operations | static names/descriptions; exact route table | reject unknown aliases and ambiguous combined operations |
| T5 stale approval | authorization/plan/scope hashes | no v1 action; later pass identifiers unchanged | future action must accept Local Service denial, never refresh or substitute |
| T6 authorization substitution | authorization identity and control package binding | fixed typed inputs; no implicit “latest” | mismatch/not-found fails; never search for another package |
| T7 scope swap | Preview/plan/scope binding | preserve objects and reason codes byte-semantically | do not rebuild or modify scope in MCP |
| T8 replay | atomic single-use claim and replay denial | no v1 execute; future no retry | replay result passes through as failure |
| T9 host auto-approval | server-side authorization boundaries | security cannot depend on host UI | safe-only tools make auto-run non-authorizing/non-executing |
| T10 annotations ignored | Local Service enforcement | treat hints as non-security metadata | behavior remains safe if every annotation is ignored |
| T11 elicitation unsupported | no current MCP dependency | no action tools | future action absent or deterministic unsupported-client failure |
| T12 elicitation declined/cancelled | no authorization created by safe operations | preserve distinct decline/cancel | future call terminates with no confirmation field synthesis |
| T13 connection loss during approval | atomic claim protects execution | no action/retry; later require a fresh bounded interaction | never assume approval or retry execute after ambiguous loss |
| T14 duplicate delivery/retry | idempotent safe reads; atomic claim for execution | mark safe idempotency accurately; never auto-retry future action | duplicate safe preflight okay; action duplicate denied |
| T15 malicious MCP client | Local Service validation and binding | fixed loopback URL/routes, size/time bounds, no arbitrary proxy | a local process can still call REST directly; Local-First is not authentication |
| T16 confused deputy | package/authorization/scope identities | require explicit package ID; no implicit current-user/latest package | cross-client possession remains local-machine trust caveat; action tools remain absent |

## Elicitation and approval strategy

**Can elicitation provide a meaningfully stronger human-intent channel than ordinary tool arguments? `YES_WITH_LIMITATIONS`.** A capable interactive client can mediate a server-originated request that is distinguishable from the original model-authored tool arguments and return accept/decline/cancel. It proves that the client returned an elicitation result for that request. It does **not** cryptographically prove a person's identity, that a human rather than automation selected the answer, or that every host rendered the same warning. Host auto-policy, noninteractive execution, malformed required-field handling, disconnects, and protocol-version differences remain material.

Current-spec and current-SDK support exist (`SPEC`/`SDK_DOC`, HIGH): [elicitation specification](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation), [Python SDK elicitation](https://py.sdk.modelcontextprotocol.io/handlers/elicitation/) (retrieved 2026-08-12). Host support is not universal; Gemini does not advertise a handler, Claude Desktop is undocumented, Hermes cannot collect required structured values, and noninteractive Codex/Claude modes have caveats.

For any future action tool:

- client capability is mandatory and must match the selected protocol-era mechanism;
- unsupported/incompatible capability, decline, cancel, disconnect, timeout, malformed response, or ambiguous retry all fail closed;
- an auto-approved tool call does not bypass elicitation;
- no failure mode may copy `confirm=true` from model arguments;
- a successful response must bind the exact Preview, Plan, authorization, scope hash, control package and intended operation before delegating;
- SDK v2 migration and host-specific human acceptance are prerequisites.

### Strategy comparison

| Strategy | Intent/self-approval resistance | Host portability | Complexity/state | Decision |
|---|---|---|---|---|
| A safe tools only | strongest by removing MCP action entry points; Workbench remains explicit boundary | highest, including clients without elicitation | lowest; no new state/artifact | **MCP v1 recommendation** |
| B action tools + elicitation | stronger than arguments when client UI is genuine; still host-dependent | uneven | v2 migration, capability/timeout/session tests; reuse Local Service state only | future v1.x research gate |
| C out-of-band Workbench approval | strong for authorization, but an MCP execute tool would still need proof it may consume that authority | good for preflight/read | moderate user coordination; no new authority needed | operating pattern in v1, not an action-tool strategy |
| D new approval reference/capability | potentially strong | custom and nonportable | highest; risks a second approval system/artifact | reject |

The recommended approval strategy is **`STRATEGY_A`**. Humans may authorize and execute in the accepted Workbench, after which MCP may read/export that governed package. M8R-08B must not register a hidden tool that consumes an out-of-band authorization.

## Existing authorization binding reuse

No MCP approval state is required. In v1 the binding sequence is:

```text
MCP preflight -> canonical Request validation -> deterministic Preview
Human Workbench -> same Preview/Plan -> Authorization(scope_hash, identity)
Human Workbench -> execute confirmation + network confirmation
05B-03 -> atomic claim -> governed execution -> Receipt/Bundle
MCP read/export(control_package_id) -> Local Service -> verified Mode C package
```

The adapter never manufactures Preview identity, plan identity, authorization identity, `scope_hash`, consumption binding, claim, receipt, or replay decision. It passes only `control_package_id` to the read/export routes and accepts not-found/mismatch/failure as authoritative.

## Delegation and bounded errors

HTTP delegation is selected over direct Python imports:

- it makes the reviewed M8R-07 transport contract the one client-neutral authority;
- it preserves bounded HTTP status, reason codes, body limits and path containment;
- it prevents stdio topology from quietly becoming a second in-process runtime;
- it lets Workbench and MCP use exactly the same deployed service;
- it tests the public contract rather than an internal call graph.

The future client must use a fixed `http://127.0.0.1:<bounded-port>` configuration, constant routes, `trust_env=False`, no redirects, finite timeouts, request/response byte limits, no retries/polling/background work, and no cookies or credentials. It must reject non-loopback host, URL credentials, query and fragment before connecting. Tool arguments can never supply a URL or route. Stdout is protocol-only; logs go to stderr.

Malformed MCP args, unknown tools, or protocol violations are MCP errors. A successfully transported validation result remains a structured domain result even when the request is invalid. Bounded Local Service operational errors use an unsuccessful MCP tool result with sanitized structured fields retaining the existing `error` and `trace_id` fields plus adapter diagnostic `http_status`; they never rename or invent domain fields and never include absolute paths or raw bodies. HTTP 409, package not found, replay, unsupported capability and future elicitation outcomes must retain distinct existing reason codes rather than collapse to free text.

## Prompt injection and output boundary

All tool names, descriptions, annotations and schemas are static or derived from committed canonical schemas—never from market data, security names, Markdown or source responses. The server instruction must explicitly state that returned market/source text is evidence data, not instructions. The adapter passes only already-governed Local Service output and must not add a generic “sanitizer” that mutates deterministic Result/Audit/Markdown. Model safety comes from fixed capabilities, governed projection, labels, and the absence of action tools—not from pretending external evidence contains no adversarial text.

## Local trust and security boundary

The stdio transport adds no listener, so Host, Origin, CORS, CSRF-like browser requests, and DNS rebinding do not apply to the MCP transport itself. The child process can contact only the fixed loopback Local Service. The existing service remains bound to localhost; current CORS accepts localhost/127.0.0.1 plus `Origin:null`. CORS is not authentication and is irrelevant to the sidecar's non-browser HTTP client.

The end-to-end DNS-rebinding result is **`QUALIFIED`**: stdio creates no new rebinding surface, but the existing REST listener's `Origin:null` hardening debt remains. Another process on the same Windows account/machine, a modified MCP host configuration, or local malware can invoke the Local Service directly. M8R-08B must document that local-machine trust boundary, pin its launcher path/config, avoid shell interpolation, and reject arbitrary endpoints. A new authentication system is not justified in this Local-First milestone; action tools remain absent.

## Dependency, compatibility, performance, and versioning

Future dependency recommendation:

```text
package: mcp
current stable: 2.0.0
M8R-08B constraint: mcp==1.29.0
HTTP client: retain existing httpx, with a dedicated bounded client
Python: preserve repository-supported interpreter; verify the exact pin in CI
```

The exact v1 pin avoids silent behavior changes and is compatible with the repository's legacy v1 decorator API. SDK v2 introduces updated low-level APIs and newer transitive Starlette/Pydantic constraints, so migration needs its own compatibility test rather than an incidental dependency bump. `SDK_DOC`, HIGH: [v1.29.0](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v1.29.0), [v2.0.0](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0), [migration](https://py.sdk.modelcontextprotocol.io/migration/) (retrieved 2026-08-12).

Tool descriptions should be short and static; only validate/preview embed the canonical Request schema. Capability output, canonical Result and Markdown may be large, so M8R-08B tests must measure serialized bytes and context cost. Bounded responses prevent accidental host overload. No compact/full switch is proposed because it would add transport semantics before evidence demonstrates a need.

The adapter identifies itself as `unified_market_evidence_mcp_adapter.v1` and declares that it binds `unified_market_evidence_local_service.v1`. Adapter-version changes cover transport/tool-envelope compatibility; canonical Request, Preview, Authorization, Receipt, Result, Audit and Markdown keep their established versions. A Local Service contract mismatch fails startup rather than triggering best-effort translation.

## Implementation and acceptance blueprint

The exact future file tree, function boundaries, closed input schemas, output design, error mapping, five required flows, implementation test matrix, manual host script, and context-cost checks are in [M8R-08A MCP Implementation Blueprint](M8R_08A_MCP_IMPLEMENTATION_BLUEPRINT.md).

Minimum M8R-08B acceptance must prove:

- initialize, tools/list, schema and annotation determinism;
- exactly five safe tools and no action aliases;
- 1:1 fixed-route delegation and Local Service version match;
- deterministic capabilities, validation and Preview;
- governed Result/handoff reuse, complete citations and raw-rich-fact exclusion;
- zero additional market network and no source-adapter import;
- bounded malformed args, missing service, authority error and package-not-found behavior;
- no arbitrary URL, redirects, proxy inheritance, path/body/exception leakage, stdout logs, retries or polling;
- stdio lifecycle/reconnect on Windows and at least official SDK in-memory plus MCP Inspector Web smoke;
- one real supported host path, with Codex or Claude Code preferred and Gemini as a useful no-elicitation compatibility check;
- full M8R-07/default-ci regression with zero automatic market calls.

## Blockers, caveats, and exact next scope

Blocking findings: none. M8R-07 remains closed `PASS_WITH_CAVEATS`; the accepted Local Service is sufficient authority for a thin MCP adapter.

Caveats:

1. Current stable MCP Python SDK is v2, while the deliberately compatible M8R-08B recommendation is pinned to v1.29.0.
2. Elicitation and approval UX differ materially across hosts; therefore action tools are deferred.
3. ChatGPT web cannot directly reach a loopback stdio or HTTP service.
4. `Origin:null` and local-machine process trust remain accepted Local Service boundary caveats.
5. The historical `server/mcp_server.py` must be kept visibly separate.
6. Claude Desktop elicitation is not documented; Hermes structured elicitation is incomplete; Inspector CLI does not test elicitation.

Exact recommended M8R-08B scope: add `server/unified_mcp/{__init__.py,server.py,tool_contracts.py,local_service_client.py,error_mapping.py}` plus `scripts/run_unified_market_evidence_mcp.py`, pin `mcp==1.29.0`, register exactly five stdio safe tools, delegate over fixed loopback HTTP, add the blueprint's deterministic/security/host tests and operator guide, and change no Phase D or M8R-07 semantic contract. Do not add authorize, execute, Streamable HTTP, a second listener, resources, prompts, sampling, elicitation, retries, raw evidence, or production market probes.

## Source appendix

All sources were retrieved **2026-08-12**. Confidence is HIGH unless otherwise stated.

| ID | Tier | Classification | Title / vendor or project | Direct URL | Specific question supported |
|---|---:|---|---|---|---|
| S1 | 1 | `SPEC` | MCP 2026-07-28 specification / MCP | https://modelcontextprotocol.io/specification/2026-07-28 | current stable protocol date and overall authority |
| S2 | 1 | `SPEC` | Transports / MCP | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports | stdio, Streamable HTTP, security and legacy transport status |
| S3 | 1 | `SPEC` | Tools / MCP | https://modelcontextprotocol.io/specification/2026-07-28/server/tools | tool schemas, results, annotations and model control |
| S4 | 1 | `SPEC` | Elicitation / MCP | https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation | current input-required interaction and outcomes |
| S5 | 1 | `SPEC` | Authorization / MCP | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization | authorization applies to HTTP transport, not stdio host trust |
| I1 | 2 | `SDK_DOC` | Python SDK v2.0.0 release / MCP | https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0 | current stable SDK release |
| I2 | 2 | `SDK_DOC` | Python SDK v1.29.0 release / MCP | https://github.com/modelcontextprotocol/python-sdk/releases/tag/v1.29.0 | current v1 maintenance pin |
| I3 | 2 | `SDK_DOC` | ASGI integration / MCP Python SDK | https://py.sdk.modelcontextprotocol.io/run/asgi/ | mounted Streamable HTTP app and path/lifespan integration |
| I4 | 2 | `SDK_DOC` | Deployment / MCP Python SDK | https://py.sdk.modelcontextprotocol.io/run/deploy/ | session-manager lifespan and deployment constraints |
| I5 | 2 | `SDK_DOC` | Migration / MCP Python SDK | https://py.sdk.modelcontextprotocol.io/migration/ | v1-to-v2 low-level API break |
| I6 | 2 | `SDK_DOC` | SDK v1 documentation / MCP | https://py.sdk.modelcontextprotocol.io/v1/ | supported maintenance-line usage |
| I7 | 2 | `SDK_DOC` | Elicitation handlers / MCP Python SDK | https://py.sdk.modelcontextprotocol.io/handlers/elicitation/ | SDK elicitation APIs and outcomes |
| I8 | 2 | `SDK_SOURCE` | Low-level server source / MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/lowlevel/server.py | current server construction/callback model |
| I9 | 2 | `SDK_SOURCE` | Transport security source / MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/transport_security.py | Host/Origin validation and bounded rejection |
| I10 | 2 | `OFFICIAL_ISSUE_OR_DISCUSSION` | ASGI lifespan discussion / MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk/issues/1467 | mounted-app lifespan implementation reality |
| I11 | 2 | `OFFICIAL_ISSUE_OR_DISCUSSION` | Streamable HTTP integration issue / MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk/issues/2702 | current integration edge cases |
| H1 | 3 | `HOST_DOC` | Codex MCP / OpenAI | https://developers.openai.com/codex/mcp/ | Codex transports, config and approval modes |
| H2 | 3 | `HOST_SOURCE` | Codex elicitation / OpenAI | https://github.com/openai/codex/blob/main/codex-rs/codex-mcp/src/elicitation.rs | form/URL/extended elicitation implementation |
| H3 | 3 | `HOST_SOURCE` | Codex tool-call policy / OpenAI | https://github.com/openai/codex/blob/main/codex-rs/core/src/mcp_tool_call.rs | annotation/approval behavior |
| H4 | 3 | `HOST_DOC` | Connect MCP to ChatGPT / OpenAI | https://developers.openai.com/plugins/deploy/connect-chatgpt | public HTTPS and Secure MCP Tunnel connectivity |
| H5 | 3 | `HOST_DOC` | Build an MCP server / OpenAI | https://developers.openai.com/plugins/build/mcp-server | ChatGPT tools, annotations and elicitation guidance |
| H6 | 3 | `HOST_DOC` | Responses API MCP tools / OpenAI | https://developers.openai.com/api/docs/guides/tools-connectors-mcp | hosted tool approval versus undocumented elicitation |
| H7 | 3 | `HOST_DOC` | Local MCP servers / Anthropic | https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop | Claude Desktop local process support |
| H8 | 3 | `HOST_DOC` | Remote connectors / Anthropic | https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp | Claude cloud network/permission constraints |
| H9 | 3 | `HOST_SOURCE` | MCP server developer skill / Anthropic | https://github.com/anthropics/claude-plugins-official/blob/c54b5608d9be1910de9a5b91c2d15bf6673b9c35/plugins/mcp-server-dev/skills/build-mcp-server/SKILL.md#L75-L80 | Claude Code elicitation minimum and Desktop unconfirmed status |
| H10 | 3 | `HOST_DOC` | Claude Code MCP / Anthropic | https://code.claude.com/docs/en/mcp | transports, elicitation, tools/resources/prompts and auth |
| H11 | 3 | `HOST_DOC` | Claude Code permissions / Anthropic | https://code.claude.com/docs/en/permissions | tool approval/bypass separate from elicitation |
| H12 | 3 | `HOST_DOC` | MCP extension guide / Microsoft VS Code | https://code.visualstudio.com/api/extension-guides/ai/mcp | transports, capabilities, annotations and elicitation |
| H13 | 3 | `HOST_DOC` | MCP configuration / Microsoft VS Code | https://code.visualstudio.com/docs/agents/reference/mcp-configuration | local/remote configuration and constraints |
| H14 | 3 | `HOST_DOC` | VS Code 1.107 / Microsoft | https://code.visualstudio.com/updates/v1_107 | URL elicitation and protocol revision support |
| H15 | 3 | `HOST_DOC` | Agent approvals / Microsoft VS Code | https://code.visualstudio.com/docs/agents/approvals | approval scopes, bypass and Autopilot |
| H16 | 3 | `HOST_DOC` | MCP servers / Gemini CLI | https://geminicli.com/docs/tools/mcp-server/ | transports, trust, prompts/resources/tools and auth |
| H17 | 3 | `HOST_SOURCE` | MCP client / Gemini CLI | https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/tools/mcp-client.ts | roots-only client capability and no elicitation/sampling handler |
| H18 | 3 | `HOST_DOC` | MCP guide / Hermes Agent | https://github.com/NousResearch/hermes-agent/blob/a871948d8d4b0f774d4ec40467bab1078a9f28d5/website/docs/user-guide/features/mcp.md | transport, OAuth, resource/prompt/sampling behavior |
| H19 | 3 | `HOST_SOURCE` | Elicitation implementation / Hermes Agent | https://github.com/NousResearch/hermes-agent/blob/a871948d8d4b0f774d4ec40467bab1078a9f28d5/tools/mcp_tool.py#L1918-L2072 | empty accepted form content and URL decline |
| H20 | 3 | `HOST_SOURCE` | Trust gate / Hermes Agent | https://github.com/NousResearch/hermes-agent/blob/a871948d8d4b0f774d4ec40467bab1078a9f28d5/tools/mcp_tool.py#L3929-L4071 | default trust and readOnly-based consent behavior |
| H21 | 3 | `HOST_SOURCE` | Inspector server configuration / MCP Inspector | https://github.com/modelcontextprotocol/inspector/blob/c7bccd477d38c2c17afb4878bcca8ee5f563c5d2/docs/mcp-server-configuration.md | stdio/HTTP and protocol-era configuration |
| H22 | 3 | `HOST_SOURCE` | Inspector client capabilities / MCP Inspector | https://github.com/modelcontextprotocol/inspector/blob/c7bccd477d38c2c17afb4878bcca8ee5f563c5d2/core/mcp/inspectorClient.ts#L564-L700 | Web capability advertisement and requests |
| H23 | 3 | `HOST_SOURCE` | Inspector Web pending request UI / MCP Inspector | https://github.com/modelcontextprotocol/inspector/blob/c7bccd477d38c2c17afb4878bcca8ee5f563c5d2/clients/web/src/components/groups/PendingClientRequestModal/PendingClientRequestModal.tsx#L158-L238 | form/URL response UI |
| H24 | 3 | `HOST_SOURCE` | Inspector CLI / MCP Inspector | https://github.com/modelcontextprotocol/inspector/blob/c7bccd477d38c2c17afb4878bcca8ee5f563c5d2/clients/cli/src/cli.ts#L149-L155 | CLI disables elicitation/sampling |
| E1 | 4 | `OFFICIAL_ISSUE_OR_DISCUSSION` | Required-field elicitation under auto-approval / Codex | https://github.com/openai/codex/issues/23383 | host auto-approval can mishandle required input |
| E2 | 4 | `OFFICIAL_ISSUE_OR_DISCUSSION` | Sampling request / Codex | https://github.com/openai/codex/issues/4929 | sampling is not current Codex support |

### Unresolved unknowns

- Claude Desktop's exact released elicitation capability and UI remain `NOT_DOCUMENTED`.
- ChatGPT's exact supported elicitation modes are not published.
- Protocol revision and interactive behavior vary by installed host version; runtime acceptance must record versions.
- Cross-client isolation on one local Windows account is not an authenticated security boundary.
- Real Result/Markdown size effects on each host require implementation-era measurement.
