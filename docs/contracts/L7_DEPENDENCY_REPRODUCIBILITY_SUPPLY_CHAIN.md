# Dependency, reproducibility and supply-chain contract

Authority: `USER_CHAT_2026-10-25_PHASE_L_L7_A3_DEPENDENCY_REPRODUCIBILITY_SUPPLY_CHAIN_CONTRACT_AUTHORIZATION`.
This contract defines A3 validation inputs. It does not publish a stable release.
Technical acceptance is recorded separately after execution.

## Python and dependency authority

`config/dependency_authority.json` is the per-consumer authority map. CPython 3.13
is the canonical release/build/CI axis. CPython 3.11 remains a noncanonical
developer compatibility axis with its own Windows x64 artifact graph and proof.
Python 3.12 is unsupported. Native Tier-1 remains Windows 11 x64; historical
Windows 10 policy is not reopened. Exact patch/toolchain versions are recorded
for every build and acceptance environment; reproducibility comparisons use the
same patch and toolchain.

`requirements.txt` expresses direct human intent. `requirements-lock.txt` retains
the shared exact version projection and its historical generator provenance.
Neither a range nor a name/version pin alone identifies release artifact bytes.
Existing Native and Docker artifact locks remain their respective runtime
authorities. Separate compatibility, glibc CI and browser locks are referenced
by the one authority map. They do not create another release authority.

Release replay verifies the complete wheel set and every SHA-256, then installs
with `--no-index --no-deps --require-hashes --only-binary=:all:` and runs `pip check`.
An absent, extra, changed, yanked or incompatible artifact blocks acceptance.
Acquisition is an explicit setup operation; runtime never resolves or installs.

For example, from a disposable CPython 3.13 Windows venv, run:

```powershell
python -B scripts/dependency_authority.py --consumer release-ci-windows --wheelhouse <bounded-wheel-cache> --work <bounded-setup-output> --acquire --install
```

Omit `--acquire` for offline replay. Python 3.11 uses the
`developer-py311-windows` consumer. Linux CI and browser environments use
`ci-linux` and `browser-linux`. Native bootstrap and Docker builds continue
using their existing offline hash-verified package installers.

Core versions are preserved from accepted A2. Playwright remains 1.55.0.
Its previously unfrozen Python transitives are explicitly frozen as pyee 13.0.0
and greenlet 3.2.4, satisfying upstream constraints and providing CPython 3.13
binary artifacts; this establishes missing browser closure rather than upgrading
an accepted pinned graph. MCP remains 1.29.0; A4 owns its compatibility policy.

## Browser, tooling and system artifacts

`config/browser_artifact_authority.json` binds Playwright 1.55.0 to upstream
Chromium/headless-shell revision 1187 and FFmpeg revision 1011, their official
URLs and locally frozen archive hashes. `verify_browser_artifact.py` verifies
those bytes before safe offline extraction. A wheel version alone is insufficient.
Upstream does not provide an independent signed SHA-256 manifest: initial
acquisition relies on official HTTPS provenance, then project-frozen integrity.
This boundary is explicit and is not called artifact signing.

`config/system_artifact_authority.json` classifies non-Python prerequisites.
Docker retains its accepted immutable Alpine base digest. The disposable glibc
replay environment is a test prerequisite, not a replacement product base.
Git, Node, PowerShell and build tools have observed versions and scoped roles;
they are not unnecessarily vendored. Playwright's embedded Node is covered by
the wheel hash. Browser OS libraries are hosted-environment provenance: the
pinned Playwright driver installs prerequisites and the job records OS package
versions. They are not presented as byte-identical hosted OS images.

All workflow action references use verified immutable commits from
`config/github_actions_artifact_authority.json`. Hosted labels remain mutable;
jobs record ImageOS, ImageVersion, runner OS/architecture and toolchain identity.
Workflow orchestration provenance does not replace artifact build provenance.
Manual/pre-publication and Windows label opt-in semantics remain unchanged.

## Reproducibility and SBOM

Two clean independent Native builds must have identical ZIP bytes, ordered
members, hashes, timestamps, metadata and manifests. Unexplained differences
block acceptance. The existing builder fixes ZIP timestamps/order/permissions.

Two clean Docker builds use identical source, locks, base, platform and args.
Record config/image identity, manifest/layer identity and exported filesystem
content. Different OCI timestamps/layer metadata must be enumerated; file bytes,
ownership, modes, links, dependency graph, source and runtime config must agree.
Only then may an explicit content-reproducibility boundary be accepted. Payload
equivalence is never described as byte-identical OCI output.

`config/first_party_dependency_sbom.json` is generated deterministically by
`scripts/dependency_authority.py --sbom <output>` from frozen consumer and browser
authorities. It covers Native, Docker, compatibility, CI and browser dependencies
with artifact hashes, platform and provenance. It has no random identifiers or
generation timestamps. A6 owns regeneration of a final RC copy.

## Integrity, signing and publisher

Required: SHA-256 integrity, exact source/tree and dependency provenance,
first-party SBOM, and verified repository merge/source identity. Hashes are not
signatures. Authenticode, cosign and SLSA are not A3 technical closure prerequisites
because no accepted signing key/publisher-secret authority exists. No keys,
certificates or signing secrets are created. Later signing execution requires
separate A6/A7 authority.

The intended publisher is the Owner-authorized GitHub release of
`SmartyJohnway/tw-market-live-data-intelligence`. Actual publication belongs to
A7. A3 authorizes no tag, release, registry publication, merge, stable version,
MCP compatibility change, A4+ acceptance or Phase L closure.
