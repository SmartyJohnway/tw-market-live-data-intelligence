# Post-v1.5 — v1.5.1 RMA-4 Local Service + MCP Real Integration

Date: 2026-11-01 (Asia/Taipei)
Status: **PASS / CLOSED**

## 1. Purpose and authority

RMA-4 validates the actual Native Local Service and six-tool MCP surface, plus the
real ChatGPT-connected deployment path on this machine. Host-specific Secure MCP
Tunnel behavior is deployment evidence only and is not a TW-Market product or
Launcher dependency.

Repository checkpoint remained:

```text
branch        main
HEAD          b84f9fc8f9be9b1c6f5c02c58aea0bbc76edb76c
VERSION       1.5.0
```

No commit, push, tag, release, VERSION mutation, Phase M start, P2-P5 start, or
evidence deletion is authorized by this closure.
## 2. Candidate-local Native integration

Primary candidate evidence:

`C:\twmarket_temp\v1.5.1-rma-20261031\rma-4\attempt-02-native-local-service-mcp\`

The candidate was the RMA-3 60-second diagnostic Native ZIP, SHA-256:

`905FEF6EA830F318A6CC786416B4E68F9E1F2676949B5208F955C13A2C77A374`

It is noncanonical and not release-eligible. Attempt-02 used a fresh installation
home, isolated loopback port `18175`, and the preserved qualified ACTIVE Security
Master fixture SHA-256 `0ABD67479E6D323032AA9BAC1862D59CEFD4F7036BF32FE7737E203A753FDDE4`.

The result recorded `status=PASS`, `failed_checks=[]`, successful setup, ACTIVE
identity, real Local Service start, `/api/health = 200 / healthy`, v2 Capability
Catalog access, MCP startup-check, full stdio probe, and clean final Stop.
## 3. MCP protocol and six-tool acceptance

The stdio client initialized protocol `2025-11-25` against
`unified_market_evidence_mcp_adapter.v2`. `tools/list` returned exactly:

```text
market_describe_capabilities
market_validate_request
market_preview_request
market_read_result
market_export_ai_handoff
market_fetch_evidence
```

Capability description returned Local Service contract v2, Catalog v3, Routing
Matrix v3, accepted Request V1/V2/V3, preferred Request V3, and emitted Result V3.
Validation and preview both passed independently for Request V1, V2 and V3.

`market_read_result` and `market_export_ai_handoff` were exercised with a validly
shaped nonexistent control-package ID and failed boundedly. `market_fetch_evidence`
rejected preview mode and a plan-only execute request as governed errors. No market
network execution was performed by these negative-path checks.
## 4. Real ChatGPT-connected deployment evidence

The existing connected deployment was not repointed or modified. Process/config
evidence proves the current `$twmarket-local` path is:

```text
Stable Native bundle
D:\Project-Library\Stable\TW-Market-1.5.0-windows-x64
-> Local Service http://127.0.0.1:8000
-> tw-market-mcp.cmd / bootstrap\launch.py mcp
-> D:\MCP-Tunnel\Start-TwMarketMcp.cmd
-> tunnel-client profile tw-market-local
-> ChatGPT
```

Direct host `/api/health` returned `healthy`. From ChatGPT, connected calls to
`market_describe_capabilities`, V3 `market_validate_request`, and V3
`market_preview_request` succeeded. The V3 preview resolved `TWSE:2330` and
returned `ready_for_confirmation` with `PREVIEW_ONLY`, `NO_NETWORK_EXECUTED`, and
`EXECUTION_NOT_AUTHORIZED`.

Compact deployment evidence is retained under:
`C:\twmarket_temp\v1.5.1-rma-20261031\rma-4\deployment-evidence\`.
## 5. RMA-D008 disposition

RMA-4 attempt-01 returned one aggregate false negative because its direct HTTP
Capability Catalog probe omitted `X-TW-Market-Service-Contract`. The service
correctly negotiated backward-compatible contract v1, while the harness incorrectly
required v2. MCP itself already negotiated v2 successfully in that attempt.

`RMA-D008` was registered before changing the harness. Attempt-02 added the explicit
v2 header and reran the full candidate-local matrix with `failed_checks=[]`.
No product-code repair was made. `RMA-D008` is therefore **CLOSED_PASS** and is
not a release blocker.

## 6. Evidence composition and boundary

RMA-4 uses complementary evidence rather than mutating the working Stable tunnel:
current-candidate bytes prove Native -> Local Service -> MCP client behavior, while
the already connected Stable Native deployment proves the real MCP -> Tunnel ->
ChatGPT deployment path. This matches the contract rule that the Tunnel is host-
specific deployment evidence only, not a product dependency.

No claim is made that the RMA diagnostic candidate was temporarily deployed through
the production `tw-market-local` tunnel. No Tunnel profile or Stable installation
was repointed, stopped, or modified by RMA-4.
## 7. Final RMA-4 disposition

All required RMA-4 scenarios have accepted evidence:

```text
/api/health                              PASS
MCP startup-check                        PASS
stdio initialize                         PASS
tools/list exact six                     PASS
all six public tool paths                PASS
Request V1/V2/V3 compatibility           PASS
Capability Catalog access                PASS
real Native -> Service -> MCP -> ChatGPT  PASS (deployment evidence)
```

RMA-4 disposition is therefore **PASS / CLOSED**.

The next RMA group is `RMA-5 — Identity resolution matrix`. This closure does not
authorize starting RMA-5, committing the current candidate, changing VERSION,
publishing a release, or modifying the Stable deployment.
