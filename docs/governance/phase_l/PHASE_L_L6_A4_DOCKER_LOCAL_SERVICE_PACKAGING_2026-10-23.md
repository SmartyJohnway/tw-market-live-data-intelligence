# Phase L / L6-A4 — Docker Local Service Packaging

**Date:** 2026-10-23
**Authority:** `USER_CHAT_2026-10-23_PHASE_L_L6_A4_DOCKER_LOCAL_SERVICE_PACKAGING_AUTHORIZATION`
**Technical disposition:** `L6_A4_DOCKER_LOCAL_SERVICE_PACKAGING_COMPLETE`
**Owner acceptance:** PENDING
**P6 disposition:** `IMPLEMENTED_A4 / FINAL_ACCEPTANCE_PENDING_A5`

L6-A4 packages the existing Local Service as one Linux/amd64 Docker Compose service. The Windows host continues to own the stdio MCP adapter. This record does not claim final P1-P6 portability acceptance and does not authorize L6-A5, L7, Phase M, image publication, or merge.

## Candidate identity

- Exact authorized base commit/tree: `ee316f784831fe684e21fa8d146512d96a888050` / `81ffd2b114a0d4d5f880d9a0ce78a103ed13a608`; `origin/main` matched the base.
- Implementation source commit/tree: `5a747fad735527f349dfc2760366359ff5da67fd` / `729708fb292565d1414ef432c5723f199eadd6de`. The implementation commit is a direct child of the exact base.
- Docker context was rebuilt from the clean, committed source commit. The context manifest binds all 273 application files to the A3 resource policy and their Git blob IDs.
- Dependency manifest SHA-256: `4dce92718699974d74e62845884f3887d6471299967e52b3a2b1191562fd7a88`.
- Final governance/evidence-binding commit is the candidate head that contains this record and its acceptance evidence. Its exact commit and tree were read back from Git after commit and are included in the PR description. The Docker application payload remains the source commit/tree above; governance-only files were added afterward.

## Platform and dependencies

Docker Desktop Engine 29.8.1 (Docker Desktop 4.93.0), Linux/amd64, CPython 3.13.17 was exercised on the recovered host. The final base is `python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741`. Alpine was selected from artifact evidence: all 48 applicable canonical pinned Linux requirements have exact official, non-yanked CPython 3.13 musllinux or universal wheels. No dependency versions or canonical requirement semantics changed. Image installation uses a staged wheelhouse with `--no-index`, `--only-binary=:all:`, and `--require-hashes`; `pip check` passed.

The committed dependency lock retains exact filenames and SHA-256 values, official PyPI hash verification, and member-level path adjudication. The two `THIRD_PARTY_UPSTREAM_EMBEDDED_PATH_PROVENANCE_EXCEPTION` findings are the already Owner-authorized exact Pygments 2.21.0 and pytest 9.1.1 wheels from A3/A3 addendum. Other reviewed Click, MCP, Requests and NumPy strings are upstream documentation/test examples; ELF byte-pattern matches are classified as binary false positives. No new wheel exception or first-party path exception was used. No dependency wheel was rewritten.

## Runtime and state contract

Compose runs exactly one `local-service`, with no MCP server or other sidecar. The Windows host binding is `127.0.0.1:18343`; restart policy is `no`. Runtime is UID/GID `10001:10001`, read-only root filesystem, all Linux capabilities dropped, `no-new-privileges`, and a bounded noexec/nosuid/nodev `/tmp` tmpfs. The source image's `/opt/tw-market/app` is immutable and the runtime write probe returned `EROFS` (errno 30).

Named project volumes distinguish durable logical classes:

- `home` → `/var/lib/tw-market/home`: metadata, settings, rebuildable cache and logs.
- `state` → `/var/lib/tw-market/state`: Security Master, Watchlists, governed/control state and retained provenance.
- `/tmp/TW-Market/<installation-id>` → ephemeral container tmpfs.

A fresh project first reported `INSTALLATION_NOT_INITIALIZED` without creating installation metadata. Explicit canonical init returned `INSTALLATION_READY`, `network_on_init=false`, and installation ID `7d68c7d4-fc1d-4b3c-aeef-94d3bff0fa98`. Start on a separate fresh uninitialized project exited 1 with `installation_not_initialized` and left metadata absent. After init, health returned HTTP 200; canonical status showed installation READY and MCP READY. Doctor returned the expected warning for `SECURITY_MASTER_NOT_INITIALIZED`; no Security Master update was attempted.

The container was stopped and removed with ordinary `compose down`, without `--volumes`. A second no-cache build from the same committed source produced a distinct image ID. Recreating the service with the same two named volumes preserved the installation ID and exact SHA-256 hashes of installation metadata and settings; Security Master, Watchlist and governed state remained uninitialized/empty. Volume names and creation identities remained unchanged. This is an A4 implementation probe, not final A5 portability acceptance or an L2 backup/restore protocol.

## Network and MCP acceptance

The Local Service retains the explicit `docker-local-service` network profile. Middleware admits loopback and the narrowly identified private Compose gateway only when the service socket remains on the attached private subnet; forwarded headers do not establish authority. A second container on the same bridge, with a non-gateway peer address, received HTTP 403 `local_service_loopback_required`. The Windows host reached the service on loopback; probes to the host's current WSL, Wi-Fi and Tailscale IPv4 addresses on port 18343 were all unreachable. Native network-boundary tests passed.

The existing host-side MCP adapter completed stdio `initialize` and `tools/list` against `http://127.0.0.1:18343` after both source-image and replacement-image runs. It returned exactly six canonical tools: `market_describe_capabilities`, `market_export_ai_handoff`, `market_fetch_evidence`, `market_preview_request`, `market_read_result`, and `market_validate_request`. Tool calls during this acceptance: zero. No Docker-management MCP surface was added.

## Integrity, acquisition and environment boundaries

The image's 273 `/opt/tw-market/app` files and SHA-256 values exactly matched the committed resource manifest. First-party path scan blockers: 0. Secret-shaped matches: 0. A run of the image without mounted volumes contained no canonical installation state files. No `.git`, tests, developer environment or acceptance evidence was included in the app payload. Operational logs showed zero provider-like lines; provider/live acquisition attempts, Security Master updates, production user-state mutations, and D-drive access commands were all zero. All acceptance paths, contexts, wheelhouse, temporary directories, host MCP HOME/STATE and evidence were under `C:\twmarket_temp`.

## Validation

Focused A4 and affected A1/A2/A3/native/network/MCP tests: **179 passed**. Compileall and required Phase-H V3, portable Catalog, runtime Skill-guide, product-version, V1 front-door, source-registry, release-hygiene and forbidden-path validators all passed. `git diff --check` passed.

Default CI is **FAIL with zero candidate-only regressions**. Exact-base and candidate runs each selected 1,294 tests: 1,246 passed, 44 failed, 4 skipped and 5 deselected. All 44 failed node IDs matched; candidate-only failures = 0. The inherited failures are preserved as failures and are not waived.

## Evidence and limits

Machine-readable evidence is in [`acceptance_runs/l6-a4-20261023T061105Z/`](acceptance_runs/l6-a4-20261023T061105Z/), including base/engine/image/Compose identities, dependency hashes and path adjudication, resource manifest, pre-init/init/lifecycle records, loopback and peer probes, volume/image replacement hashes, MCP exact-six results, APP_ROOT guard, leakage/acquisition guards, focused validators, and base/candidate default-CI failed-node lists. `intermediate-attempts.json` preserves the resolved host Docker cache issue, the rejected internal-only bridge attempt, and the earlier isolated-MCP initialization correction; those are not recorded as product acceptance failures.

**Final A4 disposition:** `L6_A4_DOCKER_LOCAL_SERVICE_PACKAGING_COMPLETE`.
**Owner acceptance:** PENDING independent review.
**P6:** `IMPLEMENTED_A4 / FINAL_ACCEPTANCE_PENDING_A5`.
**L6-A5, L7, Phase M and merge:** NOT AUTHORIZED.
