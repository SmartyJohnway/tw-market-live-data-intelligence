# TW-Market v1.5.1 — Release Notes (DRAFT / Unpublished)

## Product scope
TW-Market provides governed local Taiwan market evidence collection, research
context and AI-ready handoff for operators and AI agents. v1.5.1 is a
selected, unpublished patch candidate; v1.5.0 remains the current GitHub Stable
release until separately authorized publication.

## Improvements since v1.5.0
- RMA-0 through RMA-11 Owner E2E acceptance completed for Native Windows:
  lifecycle Setup / Security Master / Start, Workbench request/validation,
  preview, explicit authorization, one-shot execution and Mode C export.
- Clear Network Execution confirmation and an operator-readable audit reference;
  no automatic confirmation, no general-purpose background market execution.
- Consistent Recent Performance / Recent Return evidence projection with
  AI-ready Markdown de-duplication.
- Fail-closed TLS and distribution portability, State/HOME isolation,
  runtime/stale-state detection and offline package integrity.
- Retained Local Service v1 compatibility, governed V2/V3 capability semantics,
  and exactly six stdio MCP tools (mcp==1.29.0).

## Supported runtime and limitations
Canonical Native target is Windows 11 x64 with Python 3.13; Python 3.11 is
noncanonical developer/source compatibility; Python 3.12 is unsupported.
Historical default-ci Phase I/J exact-state mismatches and Windows
full-non-network POSIX-only fcntl import remain diagnostic debt, not canonical
release-blocking CI. Watchlist v0-to-v1 production migration is
KNOWN_NOT_IMPLEMENTED. Official data freshness and source-date caveats remain;
no generic realtime guarantee or forced stale-data promotion is claimed.
No Scheduler, background polling, trading execution or order routing is introduced.

## Supply chain and release authority
Native ZIP and MCPB must be rebuilt from the same final clean Git commit/tree.
Six assets are required: Native ZIP and SHA-256 sidecar, Windows MCPB and
SHA-256 sidecar, deterministic first-party SBOM release copy and typed L7
Publication Manifest. Docker remains validation only, not Registry publication.
Docker content/RootFS identity has an OCI metadata/timestamp nondeterminism boundary;
no byte-identical OCI claim. SHA-256/SBOM/provenance do not constitute a
cryptographic publisher signature; signing authority is NOT_ESTABLISHED.
Any final GitHub tag, Draft Release, Publish or Registry update needs distinct
Owner-governed gates. Stable source and final artifact hashes cannot be
predeclared before final source promotion. This document does not claim
v1.5.1 already published.
