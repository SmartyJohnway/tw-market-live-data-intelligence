# L7-A3 dependency, reproducibility and supply-chain contract — 2026-10-25

Disposition: **L7_A3_DEPENDENCY_REPRODUCIBILITY_SUPPLY_CHAIN_CONTRACT_PASS**.
Technical PASS; independent review / Owner acceptance pending. L7-A0/A1/A2 remain
Owner-accepted and merged. A4+, merge, stable release/publication and Phase M are
not authorized. Phase L is not closed.

## Authority and exact source

Authority: `USER_CHAT_2026-10-25_PHASE_L_L7_A3_DEPENDENCY_REPRODUCIBILITY_SUPPLY_CHAIN_CONTRACT_AUTHORIZATION`.
Canonical entry: `5c62d6d8cc6c49b2803126aa2190a1778fa1d4ac`, tree
`06a87a1d66f18c775ef8891e19a4dac44b94d3c9`, parents
`2219552d9817e11219c08b53e606d2969a368d02` and
`d4087bc12f06d276d992356074d4995576bf42a1`.

Tested implementation: `ab2b2dc941aea68187145166a519757622d092e8`, tree
`1ccdb3e77ca99972d965a3f7eb771d2807fd7e73`. It retains the initial A3 authority
commit `ce378e027daddd2573104fff58c784c01ed88afd` and adds a targeted Docker
build-cache determinism correction. No amend, rebase or historical evidence rewrite.
Final candidate identity is reported in the PR and post-commit receipt, avoiding a
self-referential commit hash. Changes after this tested source are evidence and
current governance front doors only; the implementation projection is verified.

Evidence: `docs/governance/phase_l/acceptance_runs/l7-a3-20261024T182923Z/`.
Contract: `docs/contracts/L7_DEPENDENCY_REPRODUCIBILITY_SUPPLY_CHAIN.md`.

## Frozen authority

`config/dependency_authority.json` is the canonical consumer map. Human direct
intent remains in requirements.txt; requirements-lock.txt is the shared exact
version projection, with its original generator provenance preserved. Artifact
identity comes from the mapped exact hashes, not from name/version or ranges.

| Consumer | Python/platform | Exact authority |
| --- | --- | --- |
| Canonical developer/test and release CI, Windows | 3.13 / x64 | Native wheelhouse lock, 49 wheels |
| Noncanonical developer compatibility | 3.11 / Windows x64 | Separate compatibility lock, same 49 core versions |
| Native distribution | 3.13 / Windows x64 | Existing Native wheelhouse lock, 49 wheels |
| Linux CI | 3.13 / glibc amd64 | Exact glibc lock, 48 wheels |
| Docker distribution | 3.13 / Alpine musllinux amd64 | Existing Docker lock, 48 wheels |
| Browser validation | 3.13 / Linux amd64 | 51-wheel graph plus three frozen browser archives |
| GitHub actions / hosted tooling | Recorded runtime | Verified action commits; hosted provenance boundary |

CPython 3.13 is the canonical release/build/CI axis. Python 3.11 source/developer
compatibility is retained and independently proven; Python 3.12 is unsupported.
Native package bootstrap remains CPython 3.13 x64. Windows 11 x64 remains the only
release-blocking Native Tier-1; Windows 10 policy and historical L0-D03 are not reopened.

No accepted core dependency version or Native/Docker wheel bytes changed. MCP
remains 1.29.0; no SDK range/support or public/state compatibility decision is made.
Playwright remains 1.55.0. Its formerly unfrozen transitives are explicitly fixed
at pyee 13.0.0 and greenlet 3.2.4, satisfying upstream constraints with binary wheels.
Replay verifies complete artifact sets/hashes, uses no index or transitive free
resolution, and runs pip check. All selected wheels independently match official
PyPI metadata and are non-yanked. The Linux glibc CI/browser graphs (48/51 wheels) also replayed independently in
fresh network-disabled pinned Debian-family prerequisite containers with successful
imports; the product base remains the accepted Alpine digest.

## Reproducibility and provenance

Native: two independent clean builds are **byte-for-byte identical**.
ZIP `TW-Market-1.0.0-windows-x64.zip`; 40639383 bytes; 338 members;
49 wheels; SHA-256 `8f11b9d052c3c8ad7baede582b28a481c42554ea9949cb5da49bafaeb9a8e78d`.
Member ordering, bytes, metadata and both manifests agree. VERSION remains 1.0.0;
this is a validation artifact, not a stable release.

Docker: two no-cache builds preserve all **9702 exported filesystem
members**, including content, permissions, ownership and links. Content projection:
`475c14460d6d439229159b2c3524670a3cd5ec712e2e909ebb2995e7b0ffdf7b`. OCI image identities differ:
`sha256:1315eb1aa8331d37b10e3668a5cc3f05c67b6f0ebfffd5e01526370fce3b31f8` and `sha256:c3488eb215cb2c47c3736e46ecb284269fc1a330e9fbb7fd97cd4a0fd34bf788`.
Runtime configuration is identical. The 6361 changed mtimes,
config created/history timestamps, resulting layer identities and manifest/provenance
metadata are enumerated. Accepted boundary:
`REPRODUCIBLE_ROOTFS_CONTENT_WITH_EXPLICIT_OCI_METADATA_BOUNDARY`.
**No byte-identical OCI claim is made.**

The initial comparison exposed 419 differing generated .pyc files. The build now
suppresses bytecode writes and removes generated venv caches. Upstream wheels contain
no .pyc members and remain byte-identical. The failed comparison is retained.

The first-party deterministic SBOM has 297 consumer/artifact components;
SHA-256 `4be21c477be71520e2bdc87b9e49d35e08dc8bea85a6654b12a3969c418913f2`. Repeated canonical generation is identical. It covers
Native, Docker, compatibility, CI and browser package/binary identities. A6 owns the
final RC copy. Hash integrity, exact source/dependency provenance and this SBOM are
mandatory. Hashes are not signatures. Authenticode/cosign/SLSA are not prerequisites
for A3 technical closure; no accepted publisher signing-key authority exists and
no signing keys, certificates or secrets were created. Publication requires explicit
Owner-authorized GitHub release authority under A7.

Every active action reference is pinned to an official verified immutable commit:
checkout v4 → `11d5960a326750d5838078e36cf38b85af677262`;
setup-python v5 → `a26af69be951a213d495a4c3e4e4022e16d87065`.
Hosted image labels remain mutable. All jobs record image/runner/toolchain identity;
no hosted runner byte-identity claim or hosted workflow-execution PASS is made.
Browser revisions are Chromium/headless-shell 1187 and FFmpeg 1011, bound to official
archives and frozen SHA-256. Their package metadata matches upstream. Archive replay
and dependency closure are proven; this report does not claim a new hosted browser
E2E execution. Browser OS libraries remain explicitly recorded hosted prerequisites.

## Validation and retained diagnostics

| Gate | Result |
| --- | --- |
| Final canonical A1 gate, CPython 3.13 | 1895 passed, 0 failures, four contracted skips, 0 guard denials |
| Membership / selection | Exactly equal to accepted A2; no new exclusion, skip or xfail |
| Fresh exact source | PASS, actual fresh GitHub clone plus exact local implementation fetch |
| Native offline bootstrap / integrity / exact-six | PASS |
| Native lifecycle / doctor read-only / A→B / actual B restart | PASS, same durable identity/state, immutable app |
| Genuine fresh Windows 11 guest | Enterprise build 26100 x64; final artifact verified; child exit 0; PASS |
| Docker fresh state / lifecycle / A→B durable survival | PASS; loopback-only publication; 72 guard events, no external product attempts |
| Packaged schemas in derived consumer Python | 75 checked; integrity PASS; no source/developer-venv fallback |
| Required static validators and focused suite | PASS; 75 focused tests, zero guard denials |
| 3.11 compatibility focused proof | 39 passed, zero guard denials |
| 3.11 source lifecycle / exact-six | PASS, Native acceptance guard plus exact read-only cmd /c ver allowcase; negative controls PASS |

The optional full canonical-profile probe under 3.11 is **retained as FAIL**:
1893 passed, two failures, four contracted skips, six denied stdlib ver attempts.
Both failing nodes reproduce at exact entry. One inspects HTTPSHandler._context
before CPython 3.11 creates its default connection context; strict CERT_REQUIRED /
check_hostname were independently verified without connecting. The other expects a
Native-only CPython 3.13 bootstrap check to reach missing-resource validation on 3.11.
These are not new canonical-gate exemptions: the same nodes remain selected and pass
under the canonical 3.13 release axis. No 3.11 full release-gate PASS is asserted.
The initial 3.11 runtime probe also retained six guard denials and was not accepted;
its functional PASS field is not the overall acceptance disposition. A separate
source-runtime probe uses the existing Native acceptance guard with a stricter
anchored native-process allowlist for precisely read-only Windows version output.
Canonical A1 guard bytes are unchanged. One initial audit-adapter error is retained.

The first Docker runtime preflight lacked the compound tag@digest inspect cache
reference although the canonical digest was present. Explicit setup pull of the
same immutable digest established it; a fresh run then passed. No product/base
failure or version substitution is inferred. All failed attempts remain inspectable.
Earlier A2 blocked/repair/final/correction/post-merge evidence and the TEMP incident
remain unchanged. DEFAULT_CI/FULL_NON_NETWORK are not newly claimed green or exempted.

## Closure and boundaries

GAP08/09 CLOSED; GAP10 ACCEPTED_WITH_EXPLICIT_REPRODUCIBILITY_BOUNDARY;
GAP11 CLOSED_BY_EXPLICIT_POLICY; GAP12 HARDENED_WITH_HOSTED_RUNNER_PROVENANCE_BOUNDARY.
Only EXIT11/12/13/17/18 gain A3 PASS. A2 acceptance carries forward; exact-six/public
contracts are preservation checks, with final A4 acceptance deferred.

Setup network is separately recorded for official metadata/artifacts, source/action
provenance, browser acquisition and pinned base acquisition. An initial metadata-only
batch retained exact URI/response bytes but not its per-retry journal; no exact retry
count is fabricated. All such uses are setup, never product/provider activity.
Product/live requests, Security Master updates, refresh/polling, D access commands,
production state mutations, VERSION/MCP policy changes, new MCP tools, tag/release/
registry publication, signing-secret creation and branch-protection mutation are zero.
Instrumentation is Python/inherited Python plus scoped containers, not an OS firewall.

After the technically complete PR is opened: STOP for independent review / Owner
acceptance. Merge, A4+, stable release/publication and Phase M remain unauthorized.
