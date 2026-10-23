# Phase L6-A3 — Native Application / Resource Distribution Packaging

POST-INCIDENT CLEAN REIMPLEMENTATION FROM MERGED A2.

Technical acceptance: PASS. Delivery: governance publication / push / PR pending at
this evidence commit. The final candidate commit/tree and delivered disposition are
recorded in the PR body. Owner acceptance: PENDING. No merge is authorized.

## Authority and identity

Owner authority: `USER_CHAT_2026-10-22_PHASE_L_L6_A3_CLEAN_REIMPLEMENTATION_FROM_MERGED_A2_AUTHORIZATION`.
Path clarification: `USER_CHAT_2026-10-23_L6_A3_THIRD_PARTY_UPSTREAM_EMBEDDED_PATH_EXCEPTION_AUTHORIZATION`.
Pytest addendum: `USER_CHAT_2026-10-23_L6_A3_PYTEST_UPSTREAM_EMBEDDED_PATH_EXCEPTION_ADDENDUM`.
Entry base `911a841b866795e8d0cd83d80b30b34701aa5980`, tree `72234b87fb3d47758c196c2ac80cc88549463837`, fetched from canonical origin/main (PR #399).
Branch: `phase-l/l6-a3-native-distribution-packaging-clean`.
Final package implementation/content commit `0c1850ac23db5a9a4e25a5196ca62dedf17ece2a`, tree `e2a2b27733f16a167facc265012c5b4dadedefe6`.
Final run `l6-a3-clean-final-20261023T010756Z`. All final consumer evidence binds this committed source and its exact ZIP.
The source/evidence preservation commit `3d7b905e8aaac979d41ded638624f9188dfdedd0` is not the accepted package source. Its blocked run is retained as intermediate history.
Lost original A3 commit/tree `3f4965bf55155c1e176e128c57c05ac0b69fefe8` / `5903859c136afc05201346100b4f4619e9966fb7` are HISTORICAL REFERENCE ONLY. Original A3 was not recovered or merged.

## Package C and resources

Versioned application bundle plus consumer-created bundle-local Python venv. APP_ROOT
is bundle/app. Runtime/venv is derived, rebuildable and noncanonical. HOME/state
identity/precedence remains A1/A2; canonical business state is external. No init or
acquisition occurs in bootstrap or launcher startup. No Docker or installer work.
The builder reads clean committed Git blobs through an exact-file role allowlist,
not a checkout copy followed by deletion. Runtime uses no Git. VERSION semantics
are unchanged and resolve to 1.0.0 without Git.

Inventory and every matched resource/authority reference line are classified in
`runtime_resource_inventory.json` / `resource_dependency_map.json`. The package
contains runtime Python closure, public schemas, exact contract/catalog/config
resources, Workbench assets and linked runtime skill resources. Four package
initializer imports and five legacy validator imports were explicitly closed.
An exact frozen I3 governance JSON is required by the active adapter and is included
unchanged. Two immutable legacy bounded-seed/template configs are explicitly
justified; they are not canonical installation SM/Watchlist state. Historical
data/artifact readers fail closed when their excluded artifacts are absent.
No user-state adoption or fixture activation is introduced.

## Dependencies, integrity, bootstrap and launchers

All 49 exact accepted dependencies are unchanged. Their Windows CPython 3.13 x64
wheel hashes were checked against official PyPI release JSON and committed in the
artifact lock. Builder rejects same-name/version artifact substitutions. Consumer
pip is isolated, no-index, wheelhouse-only, binary-only and hash-required; pip check
and exact installed distributions pass. This is not a signed attestation or final SBOM.
Exactly eight unchanged, hash-pinned upstream wheel identities have the Owner
embedded-path exception. No ninth exception was inferred. UTF-8/UTF-16 decompressed
member evidence is retained. First-party current-host leakage = 0; unapproved
D-drive literals = 0. Approved upstream strings are present and are not described
as absent. Compressed incidental bytes are not scan authority.

Standard-library integrity verification covers schema/self digest/count, unsafe and
Windows-reserved paths, duplicate/case-fold paths, member bytes/digests, unexpected
protected extras and reparse/symlink conditions. Actual tampered VERSION and
manifest cases fail before runtime creation. Bootstrap first run and idempotence
pass; stale relocated runtime is rejected. Runtime recreation, not venv relocation,
is the supported move procedure. Launchers locate relative to themselves, use the
bundle venv, clear Python path/home contamination, preserve quoted/non-ASCII CLI
arguments and exit status, and use UTF-8 output without changing system PATH.

## Fresh acceptance

Final ZIP: `TW-Market-1.0.0-windows-x64.zip`; 40613350 bytes.
SHA-256 `14dfd36c61ccf173999836932031304e151d93e9b342482bf3cd3d467b48ff7d`.
Archive members 333; manifested members 332 plus the manifest itself. Wheels 49.
Manifest canonical SHA-256 `d6a5f3ef948f6d2d022bc4db3c90032fb4ca5137eca2254324bbd4fd78b07445`.

Fresh consumer paths include spaces and non-ASCII characters, with cwd outside
repo, Git unavailable, no checkout/developer-venv sys.path fallback, and 110 loaded
first-party module origins beneath packaged APP_ROOT. Pre-init status is read-only
and does not create HOME. Explicit init yields installation READY / SM NOT_INITIALIZED.
Start/status/doctor/stop, MCP startup plus actual stdio initialize/tools-list with
exactly six public tools, and SM status pass. Doctor's SM warning is expected.
Normal runtime APP_ROOT fingerprint is unchanged. A second independent local venv
uses the same HOME/STATE, installation ID and settings at APP_ROOT B. This is the
A3_DISTRIBUTION_RELOCATION_PROBE, not final P1 acceptance.

Clean attempt reproduced SERVICE_EXITED_DURING_START; foreground stderr confirmed
a missing legacy validator import. Exact resource inclusion fixed the current
candidate; final start succeeds. No A2 lifecycle redesign was needed. The lost
original candidate's root cause is not independently proven and is not assumed.
SM staging is TEMP; retained provenance is STATE_ROOT. No live acquisition ran.

Final Python/inherited-Python guard events = []; external dependency/provider
network attempts during consumer acceptance = 0; production default HOME was not
targeted; no D commands issued or D writes observed. This is not OS-wide telemetry.
The early delegated smoke confinement gap remains historical and is not
retroactively declared PASS; final acceptance independently establishes its scope.

## Validation and limits

Focused tests: 101 passed, 0 failed. Required compile/Phase-H V3/portable Catalog/
runtime Skill-guide validators pass. Default CI remains FAIL: base and candidate
each 1246 passed / 44 failed / 4 skipped / 5 deselected; exact failed node sets
match, candidate-only failures = 0. Historical 41 are a subset. The three extra
current-environment failures require initialized HOME; controlled unchanged-A2
probes fail 3/3 before init and pass 3/3 with a separate explicitly initialized
bounded HOME. Tests and historical evidence were not weakened or rewritten.

A1-G07 CLOSED; A1-G16 CLOSED_A3 for packaged application/resource lookup. P1/P3
are materially improved but not final; P2/P4/P5 PARTIAL; P6 NOT_YET_IMPLEMENTED/A4.
No full P1-P6, Phase L completion, A4/A5, Docker, installer, L7 or Phase M claim.
Signing/release/final SBOM are future work. Current front doors point here; frozen
A0/A1/A2 evidence is unchanged. Push/PR is authorized after clean evidence
publication; PR creation is the stopping point. Owner/independent review pending.
