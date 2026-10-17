# Phase L4-A0 — Security & Resource Boundary Inventory

## 1. Authority and exact Git base

Authority: `USER_CHAT_2026-10-17_PHASE_L_L4_ENTRY_AND_A0_SECURITY_RESOURCE_BOUNDARY_INVENTORY_AUTHORIZATION`.

The inventory began on branch `phase-l/l4-a0-security-resource-boundary-inventory`, based on merged `origin/main` HEAD `cd5883d0089f3baaa7d9fc41fedad906953cbb78`, tree `ffb176bd2f22babbce590dfddc8b0b19b596d95b`. Run evidence: `l4-a0-20261017T064432Z`.

This is an offline inventory and threat-boundary contract. No implementation, provider acquisition, dependency operation, destructive load test, or penetration test was performed.

## 2. Frozen L4 obligations

Frozen L0 maps the combined security and resource subject matter to current L4. It includes localhost exposure, path containment, input/output bounds, prompt/tool-injection and authorization boundaries, dependencies/secrets, timeouts, memory/disk, large Watchlists and results, multi-target input, handoff size, and bounded concurrency. L0 intentionally defers exact values for target counts, rows, payload/artifact sizes, concurrency, timeouts, and resource ceilings; A0 records existing values and gaps without choosing new ones.

## 3. Current architecture/runtime entrypoints

The Local Service is launched through `scripts/tw_market_lifecycle.py` and `scripts/run_unified_workbench.py`; the latter checks the host allow-list before calling Uvicorn. The current Unified MCP path is `scripts/run_unified_market_evidence_mcp.py` with `server/unified_mcp`, which uses stdio and a fixed six-tool dispatcher. The HTTP app is `server/main.py`, with Unified routes in `server/unified_workbench_router.py`. Historical `server/mcp_server.py` is not treated as the current exact-six Unified adapter.

## 4. Network exposure inventory

The launcher defaults to `127.0.0.1:8000`; the lifecycle host/port can be selected by CLI/environment, but host validation accepts only `127.0.0.1`, `localhost`, or `::1`, and ports 1–65535. The Workbench launcher repeats the loopback allow-list. The app exposes health/status and legacy route families as well as Unified endpoints; CORS origin restrictions are browser policy and are not network authentication. The current MCP adapter is stdio-only and delegates to a validated loopback HTTP URL, disables redirects and environment proxy trust, and exposes exactly six static tools. No current Dockerfile/compose listener surface was found; container deployment remains a later portability concern rather than an active listener configuration.

NET-001 and NET-003 have explicit controls and deterministic coverage. NET-002 remains PARTIAL because direct alternate ASGI invocation or port forwarding can bypass launcher-only host enforcement and the Local Service has no independent caller authentication. These are assigned to L4-A1.

## 5. Path containment inventory

The repository has multiple intentionally distinct roots; A0 does not impose a universal root. Watchlists default to repository-local `data/watchlists` and can use `TW_MARKET_WATCHLIST_ROOT`; Security Master selection uses an installation pointer and resolves selected paths under governed runtime-index roots; Mode B control packages and Result/Audit artifacts use a separate control root and `m8r_filesystem_safety.safe_destination`/atomic-write helpers; backup/restore validates roots and members, including symlink/reparse components. Environment and CLI-selected config, diagnostic, cache, and temporary locations have feature-specific policies.

The output helper rejects absolute, traversal, UNC/device namespace, reserved Windows names, and alternate data streams; checks resolved containment and symlink escapes; and uses atomic temp-file replacement/exclusive creation where called. This does not establish equivalent protections for every SQLite/config/log root or eliminate filesystem race concerns. PATH-001, PATH-003, and PATH-005 are assigned to L4-A2; the backup and governed Security Master path controls are recorded as covered within their own scope.

## 6. Input/output boundary inventory

Unified HTTP POST handlers check a 1 MiB body ceiling after reading the request body. The catalog declares default/hard targets of 10/50 and operations of 30/100. Watchlists enforce 32 lists, 500 entries/list, 20 tags, 64-character tags, 4096-character notes, 120-character names, 1 MiB import, and JSON depth 20. Several source schemas/adapters also impose their own row and response-byte limits; these are not one global result ceiling.

The MCP client caps serialized requests at 1 MiB and streamed responses at 8 MiB. The response cap applies at the client after the service has built its response. Result/Audit schemas and adapters contain field/collection limits but no single total package-byte cap was found. AI handoff generation likewise lacks an independent producer-side byte ceiling. Input parsing, aggregate output, artifact count/size, and handoff limits are therefore PARTIAL/GAP findings assigned to L4-A3. No replacement numeric value is proposed.

## 7. Injection, authorization, and secrets inventory

The Unified MCP dispatcher accepts only fixed operations, validates against canonical schemas, and has no generic REST proxy. Validation and preview are non-executing; Mode B2 creates server-owned scoped/expiring authorization and requires explicit confirmation for execution; the child invocation is bounded and execute-once. Fetch Evidence requires execute mode. Source/evidence content is returned as data, and MCP server instructions state that returned content is not instructions. No current control path allows evidence text to select a route, widen network scope, alter capability, or self-authorize.

The remaining injection risk is downstream model interpretation of hostile quoted evidence; documentation cues are not a sanitizer. The Local Service trusts the local caller rather than binding authorization to an OS principal. These are mapped to L4-A4. Current source routes do not use broker/order credentials, and no trading credential path exists; future authenticated sources would require separate authority and secret-boundary review.

## 8. Dependency / supply-chain inventory

`requirements.txt` uses ranges for common packages, constrains jsonschema below 5, and pins MCP to 1.29.0. `requirements-lock.txt` records an exact resolved graph for CPython 3.11.15/Windows 11 x86_64. Browser E2E has a separate exact Playwright pin. No package installation, download, upgrade, or online vulnerability scan was run. No current package.json, lockfile, Dockerfile, or compose manifest was found. The active execution path uses fixed subprocess commands; no generic dynamic plugin loader was found in the Unified MCP path. Dependency provenance, lock/install policy, and executable inventory are assigned to L4-A5.

## 9. Resource/load inventory

Source timeouts are enforced at individual transport boundaries and vary by adapter; inspected examples include Local Service 15 seconds/action 145 seconds, I1 15 seconds, H1 60 seconds, I2/I3 30 seconds, and Mode B child timeout capped at 130 seconds. These examples do not establish one end-to-end deadline.

Operational diagnostics capture process-memory and disk-free observations, and diagnostic logs are bounded to 256 characters/string, 4 KiB/event, and 256 KiB/file. This telemetry is not application memory/disk admission control. No product-level concurrency semaphore, process-memory ceiling, or common disk-free threshold was identified. L0-deferred numeric ceilings are recorded as DEFERRED_VALUE for L4-A6; the current absence of bounded concurrent-call control is a GAP assigned to L4-A6.

## 10. Existing test/evidence coverage

The machine-readable inventory cites current focused suites for loopback launch, Unified routes, MCP stdio, Watchlist limits, path safety, backup/reparse handling, source-specific transport limits, Result/Audit contracts, and authorization/execute-once behavior. A0 ran no destructive load tests. Safe future load designs use synthetic fixtures and isolated temporary roots, not providers or production state.

## 11. Gap register

All PARTIAL/GAP findings in `l4_gap_register.json` map to exactly one next tranche and include severity. Deferred numeric choices are not treated as BLOCKER merely because L0 intentionally leaves their values open. No current violation was found where source/agent/evidence/artifact text itself grants authorization or control-plane authority.

## 12. Proposed L4 tranche sequence

The requested sequence remains appropriate:

1. L4-A0 — Security & Resource Boundary Inventory (this tranche).
2. L4-A1 — Localhost / Network Exposure & Request-Surface Hardening.
3. L4-A2 — Filesystem / Path Containment Hardening.
4. L4-A3 — Input / Output / Artifact Bound Enforcement.
5. L4-A4 — Prompt-Tool Injection / Authorization / Secret Boundary.
6. L4-A5 — Dependency & Supply-Chain Hardening.
7. L4-A6 — Resource / Load / Concurrency Acceptance and Numeric Ceiling Freeze.
8. L4-A7 — Technical Exit Review.

L4-A0 authorizes none of A1–A7.

## 13. A0 disposition

`L4_A0_SECURITY_RESOURCE_BOUNDARY_INVENTORY_COMPLETE`. The inventory represents all required families, distinguishes current enforcement from partial coverage and deferred values, assigns each gap to one next tranche, and introduces no implementation or arbitrary numeric limit.

## 14. Stop boundary

L3 remains Owner-closed. L4 is STARTED and L4-A0 inventory is complete upon this evidence commit. L4-A1+ remains NOT AUTHORIZED; L5–L7 remain NOT STARTED / NOT AUTHORIZED. No provider requests or external socket attempts were made.

### Offline test limitation recorded

The focused boundary suite completed with 86 passed and 1 skipped. An additional Mode C test module run completed with 92 passed, 1 skipped, and 2 failed: the historical v1 Result/Audit semantic-tamper tests expected v1 outputs that their helper did not materialize under the current preferred Result version. This was not repaired or represented as passing. The result does not change the PARTIAL/GAP classifications for aggregate output and artifact boundaries. Full details are in the run's offline_review.json.

## Owner Acceptance

Disposition: `L4_A0_SECURITY_RESOURCE_BOUNDARY_INVENTORY_OWNER_ACCEPTED_FOR_MERGE`.

Authority: `USER_CHAT_2026-10-17_PHASE_L_L4_A0_OWNER_ACCEPTANCE_AND_MERGE_AUTHORIZATION`.

The Owner accepts the inventory for merge. The reviewed inventory remains exactly 33 items: 7 COVERED, 19 PARTIAL, 3 GAP, 2 DEFERRED_VALUE, and 2 NOT_APPLICABLE; 22 PARTIAL/GAP findings consist of 15 HARDENING_REQUIRED, 7 TEST_COVERAGE_GAP, and 0 BLOCKER. The two historical Mode-C tamper-test failures remain disclosed evidence limitations and are not represented as passing. No implementation, test, schema, or config change was made in this closure.
