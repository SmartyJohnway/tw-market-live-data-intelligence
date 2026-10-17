# Phase L4-A4 — Prompt-Tool Injection, Authorization, and Secret Boundary

Date: 2026-10-17
Authority: `USER_CHAT_2026-10-17_PHASE_L_L4_A4_PROMPT_TOOL_INJECTION_AUTHORIZATION_SECRET_BOUNDARY_AUTHORIZATION`
Base: `a23c9aeb48c120f1fd5c1d2fc168f86c5ada59d6` (`0f15cd23fd5564a5d9c714cce7847a5a7eaa3acf`)
Run: `l4-a4-20261017T110257Z`

## 1. Scope and authority

A4 addresses the A0 findings INJ-001, AUTH-001, AUTH-002, and SEC-002. It is
offline-only. It does not add an identity provider, authentication system,
secret store, provider route, or new MCP tool. A5-A7 remain unauthorized.

## 2. Control-plane boundary

`server/local_control_plane_boundary.py` classifies every current FastAPI POST
route into an explicit control-plane category. State-mutating and network
execution POSTs require JSON and reject browser requests whose Origin does not
match the actual loopback Local Service origin. `Sec-Fetch-Site`, when present,
must be `same-origin`. Forwarded headers are not authority. The existing
app-level network boundary remains outermost and protects the complete HTTP
application, including health, legacy, and static/workbench routes.

This is a browser-origin/CSRF boundary, not individual caller authentication.
Native local callers without browser-origin metadata continue to the existing
authorization and request validation paths. The product continues to trust a
same-user local process as its operator; binding calls to an OS principal is
not provided here and remains an explicit product trust boundary. A trusted
local relay can present a genuine loopback peer, so original remote-caller
attribution is not provided.

## 3. Prompt and tool injection

Source/evidence/handoff text remains data. The fixed six-tool dispatcher and
canonical argument validation remain the control plane; hostile quoted text
does not dispatch another tool, choose a route, widen network scope, or
self-authorize. Deterministic hostile-content tests cover handoff, evidence,
tool arguments, and fixed service destination. Downstream model interpretation
of malicious quoted content cannot be guaranteed by this application boundary.
INJ-001 is COVERED for the frozen TW-Market control-plane invariant: hostile
content cannot automatically become TW-Market authorization, routing,
capability, mutation, or execution authority. No prompt sanitizer is claimed.

## 4. Legacy execution and authorization

The retained FastAPI M5K live-observation and M7G controlled-refresh execution
routes now return stable HTTP 410 disabled responses and no longer import or
call their historical network executors from app startup. Existing probe
routes remain disabled. Mode B authorization, explicit confirmation,
execute-once, and Fetch Evidence execution-mode requirements are unchanged.
The route inventory and no-call regressions cover these boundaries.

AUTH-002 is COVERED for the identified reachable legacy acquisition routes.
AUTH-001 is COVERED for the current local-first contract: server-owned scoped
authorization, explicit confirmation and execute-once remain authoritative;
cross-origin browser actions are rejected; and same-user local-process trust
is explicit. Individual local caller authentication is not provided and is
not claimed.

## 5. Secret and diagnostic projection

Public error mapping now projects only stable error codes and normalized trace
IDs, not free-form upstream detail. Watchlist and M5F errors use bounded stable
messages and allowlisted detail fields. Lifecycle diagnostics expose only a
validated loopback service URL or `UNAVAILABLE`; arbitrary configured URLs,
credentials, query tokens, and exception URLs are not echoed. Secret canary
tests cover HTTP, MCP, diagnostics, stderr, JSONL, lifecycle status, and
subprocess-facing service URL projection.

SEC-002 is COVERED for the active runtime exposure surfaces inventoried here:
the canary matrix deterministically exercises the inspected public error,
diagnostic, lifecycle, MCP, and subprocess projections, and uncontrolled
exception values are not emitted through those active boundaries. This is not
a universal guarantee for future or uninspected feature-specific paths. No
current broker or order credential path was introduced.

## 6. A0 finding reconciliation

| Finding | A4 result | Remaining limitation |
| --- | --- | --- |
| INJ-001 | COVERED | Hostile content cannot become TW-Market control-plane authority; downstream model cognition is not claimed. |
| AUTH-001 | COVERED | Existing server-owned authorization remains authoritative and same-user local-process trust is explicit; no individual caller authentication is claimed. |
| AUTH-002 | COVERED | Identified legacy network execution routes are disabled and tested. |
| SEC-002 | COVERED | Active inventoried runtime output surfaces pass deterministic secret canaries; future/uninspected surfaces are not implied. |

The known A1 MCP safe-surface issue was traced to stale test-helper method
signatures after the client added keyword-only `trace_id`; the helper was
updated without changing production dispatch. The bounded integrated gate then
passed, so this is recorded as `RESOLVED_AS_TEST_HELPER_DRIFT`, not a product
defect.

## 7. Validation and compatibility

The focused A4/A1/lifecycle/MCP-safe-surface rerun passed 45 tests with zero
external socket attempts. The bounded integrated gate passed 320 tests, had one
existing skip for a Git-ignored local candidate, and had zero failures; its
socket sentinel recorded zero external and 143 loopback attempts. The existing
governed A0 historical Mode-C tests were not represented as passing; they were
not part of this gate. Source registry, Portable Catalog, runtime/Skill
exact-six, V1 public contracts, Phase H V3, compileall, changed-file py_compile,
and `git diff --check` passed.

No MCP tool, Request/Result/Audit schema, Catalog, Route, capability, provider
route, source registry, Security Master authority, financial-statements
support, or trading/order boundary changed. No provider acquisition occurred.

## 8. Disposition and stop boundary

Disposition: `L4_A4_PROMPT_TOOL_INJECTION_AUTHORIZATION_SECRET_BOUNDARY_PASS`.
This is a technical result only; Owner acceptance is pending. L4-A5+ and
L5-L7 remain unauthorized.

## 9. Owner acceptance for merge

`L4_A4_PROMPT_TOOL_INJECTION_AUTHORIZATION_SECRET_BOUNDARY_OWNER_ACCEPTED_FOR_MERGE`

Authority: `USER_CHAT_2026-10-17_PHASE_L_L4_A4_OWNER_ACCEPTANCE_AND_MERGE_AUTHORIZATION`

Owner accepts the A4 technical result for merge with the reviewed finding
dispositions preserved:

```text
INJ-001 = COVERED
AUTH-001 = COVERED
AUTH-002 = COVERED
SEC-002 = COVERED

LOCAL SAME-USER PROCESS TRUST = EXPLICIT_TRUST_BOUNDARY
LOCAL CALLER INDIVIDUAL AUTHENTICATION = NOT_PROVIDED_BY_CURRENT_PRODUCT

legacy M5K network execution = DISABLED
legacy M7G network execution = DISABLED
A1 MCP safe-surface debt = RESOLVED_AS_TEST_HELPER_DRIFT
```

The local trust model is not an authentication claim. No authentication
subsystem or secret store was introduced. Provider requests and external
network attempts were zero. L4-A5 is authorized only after this A4 merge;
L4-A6+ and L5-L7 remain unauthorized.
