# Phase L / L7-A4 — Public Compatibility / MCP SDK / Stable Version Decision

Technical disposition: `L7_A4_PUBLIC_COMPATIBILITY_MCP_SDK_STABLE_VERSION_DECISION_PASS`.
Independent review passed under `L7_A4_INDEPENDENT_TECHNICAL_REVIEW_PASS` (review `5642080353`).
Owner accepted the exact candidate under `L7_A4_OWNER_ACCEPTED_FOR_MERGE` (review `5642097513`).
PR #416 normal-merged at `28a22ffc206db425ffefa8e578bf5ef7dcdb1a19`; A5+, stable publication,
Phase M and Phase L closure remain unauthorized.

## Authority and exact source

Original authority: `USER_CHAT_2026-10-25_PHASE_L_L7_A4_PUBLIC_COMPATIBILITY_MCP_SDK_RANGE_STABLE_VERSION_DECISION_AUTHORIZATION`.
Continuation: `USER_CHAT_2026-10-25_L7_A4_PUBLIC_V1_CLIENT_BACKEND_COMPATIBILITY_BRIDGE_ADJUDICATION`.

Canonical entry: `9bc3be99bd37d035cb7d1f02172569f7120781ea`, tree
`f7109f532234b95ce14e4a32681bd9befcfc0731`.
Tested implementation: `3b25055231a0a3970f5dc95928ce042ca6f482b3`, tree
`a11c5be938470270b69c903c5e4430fdd46e2ed0`.
The preceding implementation commit is `45960fa927649c36c2261b3ba92a68c8368fd1ec`.
No checkpoint was amended, rebased or deleted. Fresh exact source was used.

The final candidate is the evidence/governance sealing commit containing this
report, distinct from the tested implementation. Its exact head/tree, committed
manifest verification and implementation-input equality are recorded in the PR
and independently generated final candidate receipt after commit. Subsequent
runtime/build/test input changes are not permitted by this sealing sequence.

## Public compatibility and bridge

Owner affirmed the published v1 client promise and rejected a same-release-only
restriction. The legitimate original `L7_A4_PUBLIC_SURFACE_UNCLASSIFIED` evidence
under `C:\twmarket_temp\l7-a4\blocked-public-surface` remains unchanged. Its
historical failure is not relabeled PASS; the later real bridge resolves it.

The immutable published client from `e02bcb125999f542308a75f349c212f0ff3fee83`
now interoperates through real TCP/HTTP with the candidate backend. Headerless
clients select retained public v1 compatibility; current clients explicitly
select v2. Unknown exact contract values fail closed before Unified operations.
V1 capabilities use retained v1 catalog/routing and current executor registration,
with exactly the historical seven capabilities and field set. V2 capabilities
remain equal to the pre-bridge snapshot. Handoff/fetch transport identity
projection does not rewrite governed Result/Audit bytes or lineage.

Historical startup/describe, successful synthetic validate/preview, governed
Result read/export, structuredContent/TextContent/isError and error mapping pass.
Fetch's preview-mode rejection is proved before ticket/provider work; no live
fetch success is claimed. Current exact-six and v2 behavior remain supported.
There is one Local Service and one six-tool MCP surface.

The current policy is [L7 public compatibility policy](../../contracts/L7_PUBLIC_COMPATIBILITY_MCP_SDK_VERSION_POLICY.md).
Machine codes, Request V1/V2 compatibility and preferred V3, historical Result/Audit,
Watchlists, identity, AI handoff and Workbench remain governed. Enumerated Unified
operations are separated from Workbench backend routes and internal diagnostics;
this does not promote every Local Service route to a general public REST API.

## SDK and version decisions

`EXACT_PIN_POLICY`: supported `mcp==1.29.0`, no range, dependency graph/artifact
change = 0. Official PyPI candidates were 1.28.1, 1.29.0, 1.29.1 and latest
observed stable 2.3.0. Adjacent diagnostic stdio behavior passed, but unchanged
public launchers reject those versions. 2.3.0 requires additional dependencies
outside the accepted graph. No diagnostic success is called formal support.
A3 exact consumer locks, SBOM and release resolution remain unchanged.

VERSION changes from 1.0.0 to selected **1.5.0**, unpublished. Public v1 behavior
is preserved by the real bridge; supported state remains compatible; no intentional
product-v2 break exists. Component, adapter, wire and artifact schema versions are
independent. Published stable v1.0.0 and its release snapshot remain unchanged;
its exact bytes are now explicitly guarded rather than rewritten with a new version.
Current-version validator expectations were migrated without new exemptions.

## Acceptance

- Canonical A1: **1895 passed / 0 failed / 4 contracted witness skips**;
  zero unexpected skips/xfails/guard denials. Exact A3 member ledger equality.
- Focused compatibility/version/state suite: **240 passed**.
- Fresh Native artifact: `TW-Market-1.5.0-windows-x64.zip`, 40642506 bytes,
  SHA-256 `d36e97b32c5c9e948a59e2b05198348cc4552cca626fa10e4bc8007db54efe56`; 339 ZIP members,
  338 manifested members and 49 wheels.
- Native host: offline/idempotent bootstrap, pre-init, explicit init, lifecycle,
  exact-six, relocation with spaces/non-ASCII, read-only doctor, APP_ROOT guard,
  source/sys.path isolation and packaged Security Master probes PASS.
- Genuine fresh Windows 11 Sandbox: Enterprise build 26100 x64,
  WDAGUtilityAccount, no inherited TW-Market/Python/Git; official hash-verified
  disposable CPython 3.13.9, networking disabled, same Native artifact and full
  Native acceptance PASS. Host Sandbox processes returned to zero.
- Docker: exact pinned base, fresh task-owned volumes, loopback-only exposure,
  read-only application, lifecycle and A-to-B replacement PASS. Installation,
  settings and durable-state witness remain equal. Image A `sha256:44949d1d959ed5a63c9353bf10e8ce24edf268c097bee601b208d85d3a91cce6`;
  image B `sha256:464a2c120e99d534f9208691b973ec9d852f57559cd43b9f3b898448f68dda1d`. Application layers remain identical; controlled
  validation identities distinguish images. Additional real Docker v1/v2 client
  and unsupported-version probes PASS.
- Exact published v1 Watchlist implementation creates a synthetic schema-1
  database; selected 1.5 reader and historical reader rollback agree without
  changing database bytes. A prior accepted product-1.0 installation also passes
  packaged 1.5 lifecycle with installation/settings/business state unchanged.
- Noncanonical Python 3.11 source/runtime lifecycle, exact-six and published-v1
  handshake pass using the unchanged accepted A3 identity guard. It is not
  claimed as the canonical release graph or a clean full 3.11 canonical gate.
- Applicable dependency, workflow, public/schema/catalog/Skill/Guide, front-door,
  version, hygiene, forbidden-path, compile/static and focused validators PASS.

L7-GAP-13 = `CLOSED_BY_EXPLICIT_EXACT_PIN_POLICY`.
L7-GAP-14 = `CLOSED_BY_V1_5_0_PUBLIC_STATE_COMPATIBILITY_DECISION`.
Only L7-EXIT-08/09/10/14/15 gain A4 PASS. A5/A6/A7 criteria remain unaccepted.

## Retained limitations and diagnostics

L2 remains the sole backup/restore/migration authority. Watchlist v0-to-v1 is
KNOWN_NOT_IMPLEMENTED and production apply fails MIGRATION_PATH_NOT_IMPLEMENTED;
no previous stable v0 support or production transformer is invented. Synthetic
migration witnesses are classification/copy-on-write rollback evidence only.
A3's Docker equal-content/OCI-metadata boundary is preserved.

Earlier integration harness diagnostics remain inspectable: a Node `--check`
invocation was denied before child launch by the canonical guard's narrow Node
mode; Python 3.11's standard-library readonly `ver` probe likewise conflicts with
that canonical guard, as already seen historically in A3. Neither is relabeled
PASS. Final static syntax checks explicitly preload the unchanged Node guard;
noncanonical 3.11 runtime uses the exact accepted A3 identity guard. Canonical
A1 guard bytes remain unchanged and its final run has zero denials. The earlier
1.0.0 unit expectation after authorized VERSION application was corrected to the
exact 1.5.0 expectation, without skip/xfail/profile changes. Missing Docker cache
and credential-helper PATH setup are prerequisite diagnostics, not product failures.

D access commands = 0; production state mutations = 0; live provider requests = 0;
Security Master live updates/production refresh/background polling = 0;
tag/release/asset/registry publication = 0. Setup acquisition is separately
accounted. Guards attest Python/inherited-process scope, not an OS-wide firewall.

## Evidence seal

Final run: [manifest](acceptance_runs/l7-a4-20261025T064626Z/manifest.json),
93 members; self-digest `10705e65abe5565784a47c899877a3dd2e265147ce910e8ca6146a6e224bff17`.
Separate bridge continuation: [manifest](acceptance_runs/l7-a4-v1-compat-bridge-20261025T033011Z/manifest.json).
Committed member lengths/hashes/self-digests and implementation-input byte identity
were independently verified on exact candidate `902febc323b2fd568a2d00c00a18eac24f5ae655`, tree
`d264f509efda2affbf13c3253363e1844651cc17`. PR #416 was Owner-accepted and normal-merged at
`28a22ffc206db425ffefa8e578bf5ef7dcdb1a19`. This record does not authorize A5+, publication,
Phase M or Phase L closure.
