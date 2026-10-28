# Changelog

## 1.5.0 (2026-10-28)

Stable release: [GitHub Release v1.5.0](https://github.com/SmartyJohnway/tw-market-live-data-intelligence/releases/tag/v1.5.0)

- Publish the first stable Windows Native ZIP for the hardened v1.5 product line,
  with package-local bootstrap, exact hashed offline dependencies, explicit
  installation lifecycle, and application/state separation.
- Publish the deterministic Windows MCPB with the same exact six governed MCP
  tools over local stdio.
- Publish SHA-256 sidecars, the deterministic first-party SBOM, and the typed
  publication manifest as release provenance assets.
- Preserve published Local Service v1 compatibility through explicit version
  negotiation while retaining current V2/V3 contracts; Unified Request V3 is
  the preferred request authority.
- Preserve installation-local Taiwan Market Identity Service and Persistent
  Watchlists, explicit validation/preview/authorization, execute-once semantics,
  canonical Result/Audit lineage, citations, and AI-ready handoff.
- Harden timing/currentness, source provenance, finalization chronology, state
  portability, release reproducibility, and artifact hygiene without introducing
  trading, background polling, or a realtime guarantee.

### Retained release boundaries

- Windows 11 x64 is Native Tier-1; CPython 3.13 is canonical release/build/CI.
  Python 3.11 remains noncanonical source/developer compatibility and Python 3.12
  is unsupported by the v1.5.0 release contract.
- Watchlist v0 -> v1 production migration remains `KNOWN_NOT_IMPLEMENTED`.
- Docker remains a validated `linux/amd64` provenance surface for this release;
  no v1.5.0 container-registry image was published.
- MCP Registry publication is a separate surface. The GitHub v1.5.0 release did
  not update Registry metadata, which remains on the historical v1.0.0 package
  until separately authorized and published.
- SHA-256, provenance, and SBOM provide integrity and traceability; they are not
  cryptographic publisher signatures.

## 1.0.0 (2026-09-14)

- Promote the accepted V1 release-candidate contract to final V1 ProductVersion
  without runtime feature expansion. Stable `v1.0.0` was published on 2026-09-14.

## 1.0.0-rc.1 (2026-09-13)

- Freeze the local-first public contract around Unified Request, validation,
  preview, explicit bounded execution, Result/Audit, and AI-ready handoff.
- Add installation-local Persistent Watchlists with immutable revisions,
  optimistic concurrency, and single-use mutation previews.
- Establish tracked product-version authority and the V1 public-contract
  inventory. At RC publication time, final `v1.0.0` had not yet been released.
- Provide the canonical `/workbench/` operator surface, an explicit six-tool
  Unified MCP contract, and governed Result/Audit/AI handoff output.
- Keep execution local-first and bounded: no polling, scheduler, background
  refresh, trading, automatic Watchlist execution, or realtime guarantee.
- Preserve schema-1 Watchlist compatibility and historical legacy migration
  classification without claiming a production v0 -> v1 transformer; historical
  M5/M8 evidence remains audit material.

## v0.1.0

Initial Local-first Preview
