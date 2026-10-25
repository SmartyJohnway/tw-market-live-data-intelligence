# L7 public compatibility, MCP SDK and version policy

Current A4 policy under
`USER_CHAT_2026-10-25_PHASE_L_L7_A4_PUBLIC_COMPATIBILITY_MCP_SDK_RANGE_STABLE_VERSION_DECISION_AUTHORIZATION`
and `USER_CHAT_2026-10-25_L7_A4_PUBLIC_V1_CLIENT_BACKEND_COMPATIBILITY_BRIDGE_ADJUDICATION`.
Selected ProductVersion: **1.5.0**, unpublished. This selection is not technical
acceptance, an RC, a tag or a release; A4 governance evidence records acceptance separately.

## Independent version authorities

Product SemVer, Local Service contract, MCP adapter contract, MCP wire protocol
and artifact schema versions are independent. Component v2 does not imply product
v2. Within product v1.x, a published client implementing a supported PUBLIC_STABLE
or PUBLIC_COMPATIBILITY v1 contract remains usable against a later supported v1.x
backend for the behavior covered by that contract. A same-release-only guarantee
is rejected. This does not promise arbitrary forward compatibility or capabilities
introduced after the client's contract.

## Public surface

PUBLIC_STABLE includes the exact six Unified MCP tools and their governed inputs,
structured success/error envelopes, current Request V3, validation/preview,
supported Result/Audit readback and lineage, machine reason codes, Capability
Catalog, Persistent Watchlists, Taiwan identity semantics, AI handoff, canonical
`/workbench/`, installation state and the L2 inspect/preview/backup/apply/verify
policy. Request V1/V2, historical supported Result/Audit, published adapter/client
v1, Local Service v1, and L2 backup/restore formats are PUBLIC_COMPATIBILITY.

Current Local Service `unified_market_evidence_local_service.v2` and current
adapter v2 remain supported. Local Service v1 is retained throughout product
v1.x; removal cannot precede product v2 governance. Headerless published clients
select v1 compatibility. `X-TW-Market-Service-Contract` explicitly selects exact
v1 or exact v2; other values fail closed. V1 capabilities use retained v1
catalog/routing and current executor registration, not a relabeled v2 catalog.
Transport projection never rewrites canonical Result/Audit bytes or lineage.

The nine enumerated `/api/unified` operations provide governed Local Service
behavior, not a generic REST execution proxy. `/api/watchlists/*`,
`/api/evidence-request-previews` and `/api/watchlist-mutations/*` provide Workbench
backend compatibility. `/workbench/mode-a/` is PUBLIC_DEPRECATED and redirects.
Legacy/probe/diagnostic routes, storage paths, process ownership, implementation
classes, asset filenames and English diagnostic prose are INTERNAL. The retained
Phase J/K acceptance programs remain historical consumers; current MCP,
Workbench and lifecycle consumers explicitly select v2.

The exact six names remain `market_describe_capabilities`,
`market_validate_request`, `market_preview_request`, `market_read_result`,
`market_export_ai_handoff`, and `market_fetch_evidence`. No seventh tool exists.
Validation/preview never authorize; execution remains explicit, bounded and
auditable. No startup acquisition, polling, trading or order routing is supported.
Clients branch on governed machine codes, not English prose. Existing
`V1_API_ERROR_POLICY.md` remains authoritative for those codes.

## Data and durable state

Request V3 is preferred; V1/V2 remain supported compatibility inputs. Unsupported
versions fail closed. Supported historical Result/Audit bytes remain immutable,
readable and verified; current artifact schemas may be additive without changing
their provenance. Schema numerals alone neither prove nor disprove compatibility.

Supported installation/settings/Watchlist schema 1 and accepted qualified identity
releases, pointers, retained Result/Audit, authorization/evidence state and backup
metadata remain supported. The single accepted L2 authority governs portability:
inspect, preview, verified backup/checkpoint, explicit implemented apply, verify.
No silent incompatible migration occurs. Unknown/newer state fails closed;
older migratable state reports MIGRATION_REQUIRED. A backup precedes mutation.

The retained Watchlist v0-to-v1 registry entry is KNOWN_NOT_IMPLEMENTED and apply
fails MIGRATION_PATH_NOT_IMPLEMENTED. No production v0 transformer or historical
v0 stable support is claimed. Synthetic migration tests are classification and
copy-on-write rollback witnesses, not production transformer evidence. Published
v1 Watchlist source creates a synthetic schema-1 database that current and old
readers consume without changing its bytes. Rollback is conditional on retaining
supported state; it does not authorize an old application to consume unknown
future state.

## MCP Python SDK support and update policy

Policy: **EXACT_PIN_POLICY**, supported SDK **mcp==1.29.0**. Release resolution
continues to use exact A3 per-consumer locks, artifact hashes and transitive
closure. Dependency graph change = 0. No range is declared.

Official PyPI candidates were 1.28.1, 1.29.0, 1.29.1 and latest observed stable
2.3.0. Adjacent versions passed diagnostic stdio behavior while their public
entrypoints correctly rejected the noncanonical SDK; this is not full support.
2.3.0 does not satisfy the accepted graph (additional dependencies are absent).
The evidence does not prove only 1.29.0 could work; it justifies retaining one
supported/reproducible version rather than admitting untested future resolution.
Any future update requires the same behavioral matrix and affected A3 lock,
SBOM, reproducibility and A2 integration reconciliation under explicit authority.

## SemVer and governance boundary

Select v1.5.0 because supported public v1 behavior is retained through the real
bridge, Request compatibility and historical data readback remain available,
supported durable state remains compatible, and no intentional v2 break is
introduced. The historical published stable release remains v1.0.0. Its release
snapshot and historical acceptance evidence remain unchanged.

A4 technical PASS requires the complete original gate and versioned Native,
genuine Windows 11 and Docker repeat validation. A5 bounded live, A6 RC freeze,
A7 publication, merge, tags/releases/registry publication, Phase M and Phase L
closure remain unauthorized.
