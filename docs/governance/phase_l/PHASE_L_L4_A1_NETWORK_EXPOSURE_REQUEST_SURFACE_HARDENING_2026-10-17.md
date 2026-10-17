# Phase L4-A1 — Network Exposure & Request-Surface Hardening

## 1. Authority and exact base

Authority: `USER_CHAT_2026-10-17_PHASE_L_L4_A1_NETWORK_EXPOSURE_REQUEST_SURFACE_HARDENING_AUTHORIZATION`.

A1 started from the Owner-accepted and merged L4-A0 base:

- `origin/main`: `6c0759b384516d0a933a341cb8de4b9ef6c2cc2b`
- tree: `aeee7aaa8848cc5c7e29129991d76e245de43cb2`
- branch: `phase-l/l4-a1-network-exposure-request-surface-hardening`

Run evidence: `l4-a1-20261017T073048Z`.

## 2. A0 finding and threat boundary

A0 NET-002 was `PARTIAL / HARDENING_REQUIRED`: the supported launcher already restricts listener host values to `127.0.0.1`, `localhost`, or `::1`, but direct ASGI startup could bypass the launcher. The FastAPI application therefore needed an application-level boundary for requests whose actual ASGI socket addresses show non-loopback exposure.

The control evaluates ASGI `client` and `server` host values using `ipaddress.ip_address(value).is_loopback`. If any parseable address is non-loopback, the request is rejected. The decision does not rely on CORS, Host, Origin, Forwarded, X-Forwarded-For, or X-Real-IP.

## 3. Synthetic ASGI contract

Non-IP client/server identities do not by themselves describe a reachable network socket and remain usable as in-process ASGI transport. This is generic behavior; the middleware does not recognize TestClient names, pytest state, or test-only environment variables. A locally trusted but dishonest custom ASGI server can falsify its scope; application socket-origin enforcement is not an authenticity guarantee against that server.

## 4. Whole-app request surface

The middleware is installed on `server.main:app`, outside route-specific handling, and applies across the app rather than only `/api/unified/*`. Deterministic checks cover health, Unified capabilities, retained governance API, Workbench static entry, OpenAPI, and interactive docs. Rejections return bounded HTTP 403 JSON `{"error":"local_service_loopback_required"}` with `Cache-Control: no-store`; no stack trace or local details are exposed.

## 5. CORS and local relay limitation

CORS remains the existing browser-origin policy and is not network access control or authentication. A remote scope is rejected even when browser headers claim localhost; a loopback scope reaches the route even with a disallowed Origin (without an allow-origin response header).

A local reverse proxy, SSH port forward, or relay can present a genuine loopback peer to the application. A1 cannot identify the original caller in that topology. Local-caller identity/authorization remains a separate L4-A4 boundary. A1 adds no authentication, token, TLS client certificate, OS principal binding, secret storage, or credential behavior.

## 6. Launcher and MCP compatibility

Existing launcher host restrictions and lifecycle checks remain intact. The Local Service URL validation and MCP stdio route remain unchanged; the bounded gate reran launcher/lifecycle tests, Local Service URL/error mapping, exact-six MCP tool contract, and stdio-to-loopback service integration. The MCP surface remains exactly six tools; redirects remain disabled and environment proxy trust remains disabled under existing tests.

## 7. Test and validator evidence

The bounded A1 suite passed **91 tests, 0 failures** under the external-network sentinel. The sentinel recorded **0 external socket attempts** and the suite made **0 provider requests**. Its integration traffic is limited to loopback test services. The focused middleware module passed 8 tests, including IPv4/IPv6 loopback, IPv4/IPv6 non-loopback classification, remote client/server rejection, spoofed forwarded headers, synthetic in-process scopes, entire route surface, bounded response, and CORS separation.

One additional exploratory test, `tests/acceptance/test_m8r_08b_mcp_safe_surface.py::test_safe_surface_never_reaches_authorization_execution_or_raw_evidence`, failed independently with `mcp_adapter_internal_error`. It does not traverse `server.main` or the A1 middleware, is outside the bounded A1 required gate, and is disclosed in run evidence rather than represented as passing or silently removed from the selected gate.

Source registry, Portable Catalog sync, runtime/Skill exact-six, V1 public contracts exact-six, Phase H V3, compileall, changed-file py_compile, and `git diff --check` passed. Catalog, Route, public schemas, capability set, source registry, provider routes, Security Master authority, and the trading/order boundary were unchanged. `financial_statements` remains unsupported.

## 8. NET-002 reconciliation

- Network exposure dimension: `HARDENED / COVERED` for parseable socket-origin evidence visible to the FastAPI app.
- Local relay / local caller identity dimension: `NOT SOLVED BY A1`, deferred to L4-A4.
- NET-001 launcher loopback validation and NET-003 stdio/fixed-loopback MCP safeguards were retained.

## 9. A1 disposition and stop boundary

`L4_A1_NETWORK_EXPOSURE_REQUEST_SURFACE_HARDENING_PASS`.

A1 is a technical candidate only; Owner acceptance is pending. L4-A2+ and L5-L7 remain unauthorized. No provider acquisition, external network attempt, authentication system, or broader security/resource change was introduced.

Run artifact directory: `docs/governance/phase_l/acceptance_runs/l4-a1-20261017T073048Z/`.

## Owner Acceptance

Disposition: `L4_A1_NETWORK_EXPOSURE_REQUEST_SURFACE_HARDENING_OWNER_ACCEPTED_FOR_MERGE`.

Authority: `USER_CHAT_2026-10-17_PHASE_L_L4_A1_OWNER_ACCEPTANCE_AND_MERGE_AUTHORIZATION`.

Owner accepts the reviewed A1 network-origin hardening for merge. NET-002 network-origin dimension remains `COVERED`; local relay, reverse-proxy caller identity, and local-caller authentication remain `DEFERRED_TO_L4_A4`. External network attempts remain zero. The separately observed MCP safe-surface exploratory failure remains disclosed as `mcp_adapter_internal_error`; it is not represented as passing and is not repaired in this closure.
