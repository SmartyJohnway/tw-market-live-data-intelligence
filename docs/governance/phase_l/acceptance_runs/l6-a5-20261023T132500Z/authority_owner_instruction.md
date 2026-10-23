# Phase L / L6-A5 — Integrated P1–P6 Portability Acceptance Authorization

By sending this instruction, the Owner authorizes the bounded **Phase L / L6-A5 Integrated P1–P6 Portability Acceptance** tranche.

Owner authority token:

`USER_CHAT_2026-10-23_PHASE_L_L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_AUTHORIZATION`

This authorization permits:

- L6-A5 integrated portability implementation/hardening strictly required by the frozen contracts;
- actual Native Windows and Docker runtime acceptance;
- P1–P6 portability acceptance;
- the A1 installation-state ↔ existing L2 backup/restore/migration integration that A2 explicitly deferred to A5;
- deterministic acceptance harness/tests;
- governance/evidence;
- commit;
- push;
- opening a PR after technical PASS.

It does **not** authorize:

- PR merge or auto-merge;
- L6-A6 technical exit review;
- L7 CI/release/signing/publication;
- Phase M;
- MSI/MSIX/NSIS/Inno/SFX installer work;
- Docker registry publication or GitHub Release;
- new public HTTP/MCP semantics;
- a seventh MCP tool;
- new source/provider/evidence-family capabilities;
- trading/broker functionality;
- a second Catalog / Route / Executor;
- a second backup / restore / migration authority;
- live market/provider acceptance;
- silent migration;
- system-wide Windows provisioning beyond the bounded rules below.

---

# 1. Exact entry identity

Canonical repository:

`SmartyJohnway/tw-market-live-data-intelligence`

Required exact entry:

```text
origin/main:
d5dac702c25e9728db86e9ef32f4fe8185086b89

tree:
43aa778bbdc8a2bff016520d0cd1aff04a83b953
```

This is the normal merge of PR #403, the accepted L6-A4 post-merge governance reconciliation.

Before any mutation:

1. fetch `origin/main`;
2. verify exact commit;
3. verify exact tree;
4. verify clean worktree;
5. verify branch does not already contain unrelated work.

If either commit or tree differs, stop:

`L6_A5_ENTRY_BASE_DRIFT`

Do not silently rebase or reinterpret a later `main`.

Create a fresh branch:

`phase-l/l6-a5-integrated-p1-p6-portability-acceptance`

Preferred fresh workspace:

`C:\twmarket_temp\l6-a5\repo`

---

# 2. Filesystem safety boundary

D: remains under separate recovery activity.

For TW-Market L6-A5:

**DO NOT ACCESS D: AT ALL.**

No read, write, stat, list, search, Git discovery, environment probing, backup source lookup or temporary output on:

- `D:\Codex-Workspace`
- `D:\SMARTY`
- `D:\Project-Library`
- or any other `D:\...`

Primary host workspace and acceptance material must stay under:

`C:\twmarket_temp\l6-a5\`

A disposable Windows Sandbox / VM may use its own guest-local paths and a bounded mapped acceptance folder from `C:\twmarket_temp\l6-a5\`.

If D: becomes necessary, stop:

`L6_A5_D_DRIVE_ACCESS_REQUIRED`

Record final:

`D_drive_access_commands = 0`

---

# 3. Binding authority order

Use the following authority order:

1. current canonical `main`;
2. frozen Phase L L0 architecture contract;
3. accepted Windows 11 x64 prospective Tier-1 supersession;
4. accepted L6-A0 Packaging / Portability Inventory;
5. accepted L6-A1 Installation Identity / State / Configuration Contract;
6. merged L6-A2 Native Installation / Lifecycle Integration;
7. merged L6-A3 Native Application / Resource Distribution Packaging;
8. merged L6-A4 Docker Local Service Packaging;
9. L2 accepted backup / restore / migration authority;
10. L4 security/resource boundaries;
11. L5 canonical extension / exact-six / Catalog-Route-Executor authority.

Historical acceptance evidence is evidence, not a license to override later accepted authority.

Do not modify frozen historical acceptance artifacts.

---

# 4. A5 purpose

A5 is the **integrated final P1–P6 portability acceptance tranche**.

The six frozen scenarios are:

```text
P1 relocation:
same machine, different checkout/install path

P2 user portability:
different Windows user, no inherited user-local runtime

P3 machine portability:
different Win11 machine and user, fresh package, arbitrary path,
zero inherited TW-Market runtime state

P4 state portability:
restore supported durable state into a new installation

P5 upgrade portability:
newer application against supported older state, including rollback rules

P6 Docker portability:
fresh supported Docker Local Service deployment without developer-machine state
```

Do not collapse these into one generic portability test.

Each P1–P6 must receive its own machine-readable evidence and final status.

Technical PASS requires:

```text
P1 = PASS
P2 = PASS
P3 = PASS
P4 = PASS
P5 = PASS
P6 = PASS
```

`PARTIAL`, `SIMULATED`, `ASSUMED`, `INFERRED`, or `NOT_TESTED` is not sufficient for A5 technical completion.

---

# 5. A5 implementation policy

Begin by testing the merged A4 implementation as-is.

If all P1–P6 pass without product changes, A5 may remain an acceptance/governance-only tranche.

If an observed portability defect can be repaired with a **minimal bounded change consistent with existing frozen contracts**, A5 authorizes that repair.

Examples of permitted bounded A5 repair:

- connect A1 installation-state enumeration to existing L2 explicit-member adapters;
- correct source/destination installation-path handling;
- remove residual APP_ROOT dependence;
- correct portable settings/state mapping;
- fix destination identity preservation;
- fix an existing Docker/native portability seam;
- add deterministic acceptance tests;
- add thin integration adapters to existing L2 authority.

A5 does **not** authorize inventing new architecture.

Stop rather than self-widen if a fix requires:

- changing A1 frozen state semantics;
- changing installation identity semantics;
- changing L2 backup/restore/migration semantics;
- new dependency versions;
- public Request/Result/Audit changes;
- MCP tool/schema changes;
- new service/API authority;
- new migration authority;
- Docker network-boundary redesign;
- a new persisted configuration authority;
- a new product capability.

Relevant stops:

`L6_A5_STATE_CONTRACT_CONFLICT`

`L6_A5_L2_TRANSFER_CONTRACT_GAP`

`L6_A5_PUBLIC_CONTRACT_CHANGE_REQUIRED`

`L6_A5_DEPENDENCY_CHANGE_REQUIRED`

`L6_A5_NETWORK_BOUNDARY_REDESIGN_REQUIRED`

---

# 6. Acceptance-source provenance

Do not run final acceptance against an uncommitted dirty source tree.

Use this provenance sequence:

```text
exact A5 base
→ bounded implementation/repair if required
→ commit clean acceptance source
→ build Native package and Docker image from that exact commit/tree
→ execute P1–P6
→ freeze evidence
→ governance/evidence commit
→ final A5 candidate
```

If no product repair is required, the acceptance source may remain:

`d5dac702c25e9728db86e9ef32f4fe8185086b89`

Record separately:

- entry base commit/tree;
- acceptance-source commit/tree;
- Native package identity;
- Docker image identity;
- final governance/evidence candidate commit/tree.

No product/runtime change is permitted after the acceptance-source commit without rebuilding artifacts and rerunning the affected acceptance matrix.

---

# 7. Native Package C binding

Reuse the accepted A3 Package C architecture:

```text
TW-Market-<version>-windows-x64\
  app\
  bootstrap\
  wheelhouse\
  runtime\venv          # derived/rebuildable
  tw-market.cmd
  tw-market-mcp.cmd
  tw-market-security-master.cmd
  manifests...
```

But do **not** use the old A3 ZIP as the final A5 product under test because A4 subsequently changed current application source.

Build a fresh Native package from the exact A5 acceptance-source commit/tree using the accepted A3 resource policy and dependency contract.

The A3 accepted ZIP may be used only as historical regression evidence.

Native package requirements remain:

- no `.git`;
- no dev checkout requirement;
- no host PYTHONPATH fallback;
- no historical venv dependency;
- no production state;
- no secrets;
- bundle-local derived venv;
- installed supported CPython prerequisite;
- offline package bootstrap from wheelhouse;
- replaceable APP_ROOT;
- external durable HOME/STATE.

Record ZIP SHA-256, member count, dependency identity and resource manifest.

---

# 8. P1 — relocation acceptance

P1 must use the current A5 Native package.

Create an isolated installation under C:.

Use at least two materially different APP_ROOT paths, including:

- different directory depth;
- a path containing spaces;
- a non-ASCII path where host support permits.

Example acceptance concept:

```text
App A → external HOME/STATE
stop
move/extract same accepted application to App B
App B → same external HOME/STATE
start/status/doctor/MCP
```

Required P1 assertions:

- HOME unchanged;
- STATE_ROOT unchanged;
- installation ID unchanged;
- settings hash unchanged;
- durable-state hashes unchanged;
- APP_ROOT changed;
- old APP_ROOT is not consulted;
- no `.git` dependency;
- no developer venv dependency;
- no host-path leakage;
- lifecycle works after relocation;
- doctor remains read-only;
- exact six MCP tools remain exact;
- startup performs no hidden acquisition.

P1 cannot pass solely because unit tests say path handling is relocatable.

Actual packaged relocation is required.

---

# 9. P2 — different Windows user acceptance

P2 requires a **real distinct Windows security principal/profile**.

Do not fake P2 by only changing:

- `USERNAME`;
- `USERPROFILE`;
- `LOCALAPPDATA`;
- environment variables;
- HOME variables.

A simulated profile is not P2 acceptance.

Preferred execution:

1. already-available disposable Windows Sandbox or Win11 VM;
2. existing disposable secondary Win11 user/host if already available.

Do not automatically:

- create a permanent host Windows account;
- enable Hyper-V;
- enable Windows Sandbox;
- install WSL;
- alter local security policy;
- change machine-wide ACL policy;
- reboot the host.

If no genuine distinct-user environment is already available, stop:

`L6_A5_P2_DISTINCT_USER_ENVIRONMENT_REQUIRED`

P3's fresh Win11 environment may also satisfy P2 only if you record separate P2 assertions proving:

- distinct Windows profile/security context;
- no inherited source-user HOME/runtime;
- fresh per-user default HOME behavior;
- no old-profile absolute path becomes active authority.

Explicit portable-state transfer must use P4/L2 semantics, never profile copying.

---

# 10. P3 — fresh Windows 11 machine/user/path acceptance

P3 is the strongest Native fresh-install acceptance.

It requires an **actual fresh/disposable Windows 11 x64 environment**.

Preferred environment:

- Windows Sandbox, if already enabled and operational;
- otherwise an already-available disposable Win11 VM or secondary host.

Do not claim P3 from a new directory on the existing Windows session.

Do not enable OS virtualization features or create a VM requiring system configuration under this authority.

If no genuine fresh Win11 environment is available, stop:

`L6_A5_P3_FRESH_WIN11_ENVIRONMENT_REQUIRED`

If Windows Sandbox is available, it is acceptable to use a `.wsb` configuration with:

- a bounded mapped input/output folder under `C:\twmarket_temp\l6-a5\`;
- the accepted Native package;
- deterministic acceptance scripts;
- no source checkout mapping;
- no D: mapping;
- no dev venv mapping.

The fresh environment must begin with:

- no TW-Market HOME;
- no TW-Market STATE;
- no historical installation metadata;
- no package venv;
- no `.git`;
- no old checkout;
- no tunnel requirement;
- no Codex/Hermes/Antigravity requirement.

If supported CPython is not preinstalled, that is acceptable.

Install the documented supported CPython prerequisite freshly inside the disposable environment from an exact verified official installer, then run Package C's offline bootstrap.

Do not use the host developer Python as the guest runtime.

Record:

- Windows edition/build;
- x64 architecture;
- Python version and installer identity;
- package SHA-256;
- fresh-environment proof;
- zero inherited TW-Market state.

Required lifecycle sequence:

```text
application available
→ INSTALLATION_NOT_INITIALIZED
→ explicit offline init
→ installation READY
→ SECURITY_MASTER_NOT_INITIALIZED
→ explicit start
→ status
→ doctor
→ host/local MCP contract where applicable
```

`status`/`doctor` before init must not silently create installation state.

`init` must remain explicit, offline and idempotent.

P3 also must prove that Security Master acquisition remains **explicit only** and uses canonical STATE/temp/provenance roots rather than APP_ROOT.

Prefer an existing deterministic/offline accepted Security Master fixture or formal non-live path if available.

This A5 authority does **not** authorize general live market/provider acquisition.

If satisfying the explicit Security Master update requirement requires a live provider/source fetch and no deterministic existing acceptance path exists, stop:

`L6_A5_LIVE_SM_ACQUISITION_AUTHORIZATION_REQUIRED`

Do not silently weaken P3 and do not turn live source transport success into a portability criterion.

---

# 11. P4 — durable state portability / L2 integration

A2 explicitly deferred full explicit-member backup/restore portability integration and P4 acceptance to A5.

A5 therefore owns the **minimal integration between A1 installation ownership and the existing L2 authority**.

Do not create a new backup system.

Source enumeration must remain explicit and bounded.

At minimum exercise representative portable state covering:

### CORE

- portable user settings;
- Security Master durable authority or deterministic accepted representative state;
- Watchlists;
- required portable installation facts/pointers.

### FULL GOVERNED

Where supported by existing L2 classification:

- representative Result;
- Audit;
- authorization/control;
- retained governed provenance.

Use deterministic acceptance-only state.

Do not use production user data.

Source state may be seeded using existing accepted deterministic fixtures/builders, but the actual transfer must use canonical L2 backup/verify/restore mechanisms.

No `robocopy`, whole-directory ZIP, Docker-volume copy or ad-hoc filesystem copying may be presented as P4 acceptance.

Required flow:

```text
source installation
→ enumerate declared portable members
→ canonical L2 backup
→ verify manifest/version/hash
→ create separate destination installation
→ destination receives fresh installation identity
→ canonical isolated L2 restore
→ explicit supported activation/use
→ lifecycle verification
```

Required assertions:

- destination installation ID remains destination identity;
- source installation ID is provenance only;
- source PID/ownership is not active;
- source absolute HOME/STATE/APP paths are not active;
- cache/log/runtime/temp are not restored as canonical state;
- restored portable settings preserve portable preferences only;
- restored state hashes match declared backup contents;
- restore does not acquire market/source data;
- restore does not authorize/execute evidence;
- restore is isolated until explicit use;
- APP_ROOT remains replaceable.

If integration requires inventing a second restore/migration engine, stop.

If current L2 lacks the necessary declared-member adapter and it can be added as a thin adapter consistent with A1-D15, implement the minimum adapter in A5.

If the missing capability requires changing L2's frozen semantics, stop:

`L6_A5_L2_TRANSFER_CONTRACT_GAP`

Strong integrated probe:

Where the existing L2 portable representation is profile-neutral, also attempt one bounded cross-profile transfer, preferably:

```text
Native source backup
→ new Docker installation restore
```

or the reverse.

This is an integration probe, not a seventh P scenario.

Do not invent a new cross-profile protocol.

Any failure showing that a supposedly portable member activates a source Windows/container absolute path is an A5 portability defect and may not be ignored.

---

# 12. P5 — upgrade portability and rollback

P5 must test a real previous accepted installation state against the current A5 application.

Do not invent a fake historical schema version solely to obtain a PASS.

Use a prior accepted L6 Native installation implementation, preferably the exact accepted A2/A3 lineage, to create the older installation state under an isolated C: acceptance root.

Candidate historical identities include the accepted A2/A3 lineage already recorded by governance.

Then:

```text
older accepted app/state
→ stop cleanly
→ newer A5 application
→ inspect compatibility
→ start if supported
→ verify state
→ rollback to older compatible application when contract permits
```

Required assertions:

- upgrade does not create a new installation ID;
- application replacement does not relocate durable state;
- software upgrade does not trigger Security Master refresh;
- no hidden source acquisition;
- supported state starts normally;
- incompatible/newer state fails closed;
- older-but-migratable state reports MIGRATION_REQUIRED before mutation;
- no silent migration;
- rollback follows L2/frozen compatibility rules.

If the actual A2/A3 → A5 state schema is unchanged and compatible:

record explicitly:

`SUPPORTED_NO_MIGRATION_REQUIRED`

Then prove:

- newer application uses the old state successfully;
- no incompatible state rewrite occurred;
- direct application rollback succeeds;
- durable state identity/hashes remain compatible.

Do not fabricate a migration merely to exercise migration code.

Existing L2 migration acceptance may support the inherited migration semantics, but A5 must still perform the actual integrated compatible-upgrade/rollback probe.

If determining what historical state is officially "supported" requires a new release-compatibility policy rather than applying existing accepted schema/version rules, stop:

`L6_A5_UPGRADE_COMPATIBILITY_DECISION_REQUIRED`

L7 still owns final release compatibility-range policy.

---

# 13. P6 — final Docker portability acceptance

P6 was implemented in A4 but final portability acceptance belongs to A5.

Re-run P6 from the exact A5 acceptance source.

Required environment:

- Docker Desktop on Windows 11 x64;
- Linux/amd64 Local Service;
- accepted pinned base/dependency contract;
- host-side stdio MCP remains outside container.

Build from clean committed source.

Use a fresh isolated Compose project and fresh named volumes.

Required flow:

```text
fresh image
→ fresh volumes
→ pre-init status/doctor behavior
→ explicit init
→ start
→ health
→ status
→ doctor
→ host-side MCP initialize/tools/list
→ stop/remove container preserving volumes
→ distinct no-cache image rebuild or replacement
→ recreate using same volumes
→ verify state survives
```

Required assertions:

- host publish is loopback only;
- no generic remote-listener relaxation;
- container remains one Local Service;
- no MCP server in container;
- exact six tools from host-side MCP;
- installation ID survives container/image replacement;
- settings/state hashes survive;
- image/container/network IDs are not installation identity;
- application is image content and replaceable;
- durable state is mounted external state;
- no canonical state in image layers;
- no automatic SM update;
- no provider acquisition;
- no image publication;
- Docker volumes are not called L2 backup.

If Docker runtime is unavailable, stop:

`L6_A5_DOCKER_RUNTIME_UNAVAILABLE`

Do not reset or purge unrelated Docker data.

---

# 14. Configuration / lifecycle integrated gates

Across appropriate Native/Docker scenarios verify:

### Configuration precedence

```text
CLI
> ENV
> persisted settings
> product default
```

Verify host and port precedence.

Verify HOME bootstrap:

```text
--home
> TW_MARKET_HOME
> Windows default
```

Verify initialized STATE_ROOT metadata authority and fail-closed conflict behavior.

### Lifecycle

Verify:

- init explicit/offline/idempotent;
- start does not initialize;
- status read-only;
- doctor read-only;
- stop only stops owned service;
- process ownership remains installation-ID/PID-token/executable based;
- stale ownership is rejected;
- application replacement does not change installation identity.

Fingerprint relevant roots before/after read-only operations.

---

# 15. Application/state separation gates

Integrated A5 acceptance must prove:

- APP_ROOT contains replaceable application/resources only;
- canonical durable state is outside APP_ROOT;
- APP_ROOT normal runtime writes = 0;
- installation ID independent of app path, username, machine name and port;
- cache is rebuildable;
- logs are diagnostic, not Audit authority;
- runtime/temp are ephemeral;
- no durable state becomes image/package content;
- no source absolute path becomes destination authority.

Fingerprint APP_ROOT before and after all final Native/Docker runtime probes.

---

# 16. Integration independence

TW-Market core must operate without:

- Secure MCP Tunnel;
- ChatGPT connector;
- Hermes;
- Codex;
- Antigravity;
- OpenAI Runtime key/DPAPI state;
- preexisting browser state;
- developer checkout.

Those are optional integrations, not installation dependencies.

The product relationship remains:

```text
TW-Market Core
→ Local Service / local stdio MCP
→ optional Agent integration
```

A5 must prove core lifecycle and exact-six MCP availability without any external Agent dependency.

---

# 17. MCP and public-contract invariants

The public MCP tool list must remain exactly:

```text
market_describe_capabilities
market_export_ai_handoff
market_fetch_evidence
market_preview_request
market_read_result
market_validate_request
```

Tool count:

`6`

No seventh portability/Docker/backup tool.

No Request/Result/Audit schema drift.

No new Catalog.

No new Route authority.

No new Executor authority.

No evidence text interpreted as executable authority.

Run existing relevant L5/MCP/public-contract validators.

---

# 18. Network / acquisition policy

Allowed A5 external network use is limited to packaging/environment preparation:

- Git/GitHub;
- official Python distribution retrieval if required for a disposable fresh Win11 environment;
- exact pinned Python package artifact retrieval;
- Docker registry/base retrieval.

Product/runtime acceptance must not perform general live market/provider acquisition.

Forbidden unless separately authorized:

- TWSE live acceptance;
- TPEx live acceptance;
- TAIFEX live acceptance;
- Yahoo market acquisition;
- FinMind;
- Fugle;
- Fubon;
- other live evidence providers;
- arbitrary market refresh.

Provider/live market acquisition attempts expected:

`0`

Security Master acquisition is governed by the special P3 rule above.

No hidden acquisition may occur from:

- init;
- start;
- status;
- doctor;
- healthcheck;
- restore;
- migration inspection;
- app upgrade;
- Docker recreate.

---

# 19. Production-state isolation

Do not use or mutate the Owner's real installation:

`%LOCALAPPDATA%\TW-Market`

Do not use SMARTY state.

Do not use real production Watchlists, Results, Audits or Security Master.

All host acceptance installations must use isolated A5 paths under:

`C:\twmarket_temp\l6-a5\...`

except state contained entirely inside an already-disposable Win11 Sandbox/VM.

Production-user-state mutations:

`0`

---

# 20. Real P2/P3 requirement

A5 must explicitly distinguish:

```text
PATH ISOLATION TEST
≠
DISTINCT WINDOWS USER TEST
≠
FRESH WINDOWS MACHINE TEST
```

Environment-variable simulation cannot upgrade one category into another.

A5 technical PASS is prohibited unless actual evidence supports P2 and P3.

If required disposable infrastructure is not available, stop cleanly rather than weakening the gate.

---

# 21. Path / secret / provenance leakage

Inspect:

### Native package

- `.git`;
- `.github` unless runtime-required;
- dev venv;
- tests;
- acceptance evidence;
- developer source paths;
- `C:\Users\weitang`;
- any `D:\...`;
- credentials/tokens;
- `.env`;
- SSH material;
- browser credentials;
- Docker credentials;
- production state.

### Docker image

same classes plus:

- Windows host paths;
- source checkout;
- acceptance roots;
- canonical user state embedded in layers.

Third-party upstream wheel strings must be adjudicated using the existing A3 provenance policy.

Do not automatically invent new embedded-path exceptions.

If a new exception is actually required, stop:

`L6_A5_THIRD_PARTY_EMBEDDED_PATH_EXCEPTION_REQUIRED`

---

# 22. Native fresh-machine prerequisite test

Because Package C intentionally relies on a supported installed CPython rather than embedding Python, P3 must demonstrate the documented prerequisite flow.

A clean Win11 environment with no Python is valid.

The acceptance may:

1. obtain an exact official supported CPython x64 installer;
2. record version, source and SHA-256;
3. install it only inside the disposable environment;
4. run Package C bootstrap offline from its wheelhouse.

Do not modify host machine Python installation for this purpose.

If Package C cannot provide a workable fresh-machine flow even after documented Python prerequisite installation, classify this as a P3 defect.

---

# 23. A5 acceptance evidence

Create:

`docs/governance/phase_l/PHASE_L_L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_2026-10-23.md`

Acceptance directory:

`docs/governance/phase_l/acceptance_runs/l6-a5-<timestamp>/`

At minimum preserve machine-readable evidence for:

- `entry_identity`
- `authority`
- `acceptance_source_identity`
- `environment_matrix`
- `native_package_identity`
- `native_dependency_identity`
- `docker_image_identity`
- `p1_relocation`
- `p2_distinct_user`
- `p3_fresh_win11`
- `p4_state_portability`
- `p5_upgrade_rollback`
- `p6_docker_portability`
- `installation_identity_matrix`
- `state_root_hashes`
- `configuration_precedence`
- `doctor_read_only_guard`
- `app_root_write_guard`
- `hidden_acquisition_guard`
- `provider_network_guard`
- `host_path_leakage`
- `secret_scan`
- `integration_independence`
- `exact_six_mcp`
- `public_contract_regression`
- `l2_boundary_verification`
- `cross_profile_probe` if executed
- `focused_validation`
- `base_default_ci`
- `candidate_default_ci`
- `failed_node_comparison`
- `scope_diff_verification`
- `final_acceptance_review`
- manifest with canonical SHA-256/self-digest.

Do not commit large binary Native packages, Python installers, wheelhouses or Docker image exports merely as governance evidence.

Record their exact hashes/identities instead.

---

# 24. Tests / validators

Add focused tests where needed for actual A5 integration.

Run at minimum:

- new A5 tests;
- relevant A1 contract/integration tests;
- A2 installation/lifecycle tests;
- A3 Native packaging/resource/path tests;
- A4 Docker/network/mount tests;
- relevant L2 backup/restore/migration tests;
- L4 network/path/security tests;
- L5 exact-six/public-contract tests;
- Security Master root/acquisition-boundary tests if touched;
- compile/static checks;
- required repository validators;
- `git diff --check`.

Do not weaken or delete historical tests to obtain PASS.

---

# 25. Default-CI comparison

Run default CI against:

1. exact A5 entry base;
2. final A5 candidate;

under the same environment.

Historical A4 evidence recorded:

```text
1246 passed
44 failed
4 skipped
5 deselected
```

but this is historical context only.

Do not assume the current environment must reproduce those exact counts.

Required rule:

```text
candidate-only failed node IDs = 0
```

If inherited failures remain, report overall CI as FAIL.

Do not relabel inherited FAIL as PASS.

If candidate introduces any new failed node ID, stop:

`L6_A5_CANDIDATE_ONLY_CI_REGRESSION`

---

# 26. A5 final acceptance semantics

Each scenario must conclude independently:

```text
P1 = PASS
P2 = PASS
P3 = PASS
P4 = PASS
P5 = PASS
P6 = PASS
```

Only then may final technical disposition be:

`L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_PASS`

A5 PASS means the six frozen portability cases have passed integrated technical acceptance.

It does **not** mean:

- Phase L is closed;
- L6 technical exit review is complete;
- release is approved;
- v1.5.0 is published;
- L7 is started;
- installer work is authorized;
- Phase M is started.

L6-A6 remains separately Owner-authorized technical exit review work.

---

# 27. Hard completion gates

Do not claim A5 PASS unless all of the following are true:

1. exact entry base/tree verified;
2. D-drive access = 0;
3. production-state mutation = 0;
4. final acceptance source is committed/clean;
5. fresh Native package built from exact acceptance source;
6. Native package has no dev checkout/.git dependency;
7. P1 actual relocation PASS;
8. P2 actual distinct-user PASS;
9. P3 actual fresh-Win11 PASS;
10. P4 canonical L2 state portability PASS;
11. P4 destination identity preserved;
12. P4 source paths/PID/runtime do not become destination authority;
13. P5 actual previous accepted state → newer app PASS;
14. P5 rollback behavior PASS;
15. no silent migration;
16. P6 fresh Docker PASS;
17. P6 image replacement/state survival PASS;
18. host-loopback Docker boundary PASS;
19. exact-six MCP PASS under Native/Docker applicable paths;
20. configuration precedence PASS;
21. doctor read-only PASS;
22. APP_ROOT replaceability/immutability PASS;
23. no hidden acquisition;
24. live market/provider acquisition = 0;
25. integration independence PASS;
26. Request/Result/Audit compatibility preserved;
27. no second Catalog/Route/Executor;
28. historical evidence unchanged;
29. host/path/secret scans PASS;
30. focused validators PASS;
31. `git diff --check` PASS;
32. default-CI comparison completed;
33. candidate-only CI failures = 0;
34. no unauthorized dependency/public-contract changes;
35. all P1–P6 evidence is inspectable and committed;
36. final technical review is internally consistent.

---

# 28. Stop conditions

Stop immediately and report rather than self-widen on:

`L6_A5_ENTRY_BASE_DRIFT`

`L6_A5_D_DRIVE_ACCESS_REQUIRED`

`L6_A5_P2_DISTINCT_USER_ENVIRONMENT_REQUIRED`

`L6_A5_P3_FRESH_WIN11_ENVIRONMENT_REQUIRED`

`L6_A5_OS_PROVISIONING_CHANGE_REQUIRED`

`L6_A5_LIVE_SM_ACQUISITION_AUTHORIZATION_REQUIRED`

`L6_A5_STATE_CONTRACT_CONFLICT`

`L6_A5_L2_TRANSFER_CONTRACT_GAP`

`L6_A5_UPGRADE_COMPATIBILITY_DECISION_REQUIRED`

`L6_A5_PUBLIC_CONTRACT_CHANGE_REQUIRED`

`L6_A5_DEPENDENCY_CHANGE_REQUIRED`

`L6_A5_NETWORK_BOUNDARY_REDESIGN_REQUIRED`

`L6_A5_THIRD_PARTY_EMBEDDED_PATH_EXCEPTION_REQUIRED`

`L6_A5_DOCKER_RUNTIME_UNAVAILABLE`

`L6_A5_PRODUCTION_STATE_RISK`

`L6_A5_CANDIDATE_ONLY_CI_REGRESSION`

any exact-six MCP drift

any Request/Result/Audit drift

any competing Catalog/Route/Executor authority

any need to rewrite historical acceptance evidence

any P1–P6 FAIL/BLOCKED that cannot be repaired inside the existing frozen contracts.

Do not convert a blocker into a PASS by narrowing the scenario.

---

# 29. Governance/front-door update rule

Only after all six P scenarios technically pass:

update the current front-door governance to say:

```text
L6-A5 technical candidate:
L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_PASS

P1 = PASS
P2 = PASS
P3 = PASS
P4 = PASS
P5 = PASS
P6 = PASS

Owner acceptance = PENDING
```

Also state:

```text
L6-A6 = NOT AUTHORIZED
L7 = NOT AUTHORIZED
Phase M = NOT AUTHORIZED
installer/release/image publication = NOT AUTHORIZED
```

Do not claim Phase L/L6 closure.

---

# 30. Git / PR authority

After technical PASS only:

1. verify clean worktree;
2. verify exact diff scope;
3. commit final evidence/governance;
4. record exact candidate commit/tree;
5. push the branch;
6. open PR to `main`.

Suggested title:

`L6-A5 integrated P1-P6 portability acceptance`

PR body must include:

- Owner authority token;
- exact entry base/tree;
- acceptance-source commit/tree;
- final candidate commit/tree;
- P1–P6 disposition table;
- Native package SHA-256;
- Docker image/base identity;
- P2/P3 actual environment classification;
- P4 source/destination installation identity result;
- P5 upgrade/rollback result;
- P6 image replacement/state-survival result;
- exact-six MCP result;
- acquisition/provider count;
- production-state mutation count;
- D-drive access count;
- focused test result;
- base/candidate default-CI comparison;
- candidate-only failures;
- remaining limitations;
- explicit statement that A6/L7/M remain unauthorized.

Push and PR opening are authorized after technical PASS.

**Merge is NOT AUTHORIZED.**

Do not enable auto-merge.

After PR opening, stop and return:

- PR URL/number;
- entry base/tree;
- acceptance-source commit/tree;
- final head/tree;
- P1–P6 status;
- package/image identities;
- test/CI results;
- limitations/blockers;
- Owner acceptance pending.

Do not begin L6-A6.

---

# 31. Final instruction

Treat L6-A5 as an **actual integrated portability acceptance**, not a documentation exercise.

The most important correctness rule is:

> A directory change is not a different user, and a different user is not a fresh machine.

P2 and P3 must be genuine.

The second most important rule is:

> P4/P5 must reuse L2; never solve portability by inventing another state-transfer mechanism.

The third is:

> Native Package C and Docker Local Service are two deployment profiles of one product architecture, not two products.

Proceed within this bounded authority.