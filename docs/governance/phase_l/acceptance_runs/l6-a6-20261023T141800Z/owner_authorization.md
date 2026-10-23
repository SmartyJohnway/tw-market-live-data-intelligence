# Phase L / L6-A6 — Packaging & Portability Technical Exit Review Authorization

By sending this instruction, the Owner authorizes the bounded:

**Phase L / L6-A6 — Packaging & Portability Technical Exit Review**

Owner authority token:

`USER_CHAT_2026-10-23_PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_AUTHORIZATION`

This authorization is for a **technical exit review only**.

It permits:

- offline/current-main technical review of L6 A0–A5;
- verification of all frozen/candidate L6 exit criteria;
- integrity/provenance validation of accepted A0–A5 evidence;
- rerunning deterministic tests and validators;
- generating review-only helpers/evidence when necessary;
- governance/front-door updates after a technical PASS;
- commit;
- push;
- opening an A6 PR after technical PASS.

It does **not** authorize:

- Owner final closure of L6;
- PR merge or auto-merge;
- L7;
- Phase M;
- release/signing/publication;
- Docker registry publication;
- MSI/MSIX/NSIS/Inno/SFX installer implementation;
- product/runtime feature implementation;
- dependency upgrades;
- public contract changes;
- a seventh MCP tool;
- new evidence families;
- new Catalog / Route / Executor authority;
- new backup/restore/migration authority;
- live provider acceptance;
- repairing unrelated historical CI failures.

If a true L6 blocker is discovered, stop and report it.
Do not silently repair product/runtime behavior inside A6.

---

# 1. Exact canonical entry

Repository:

`SmartyJohnway/tw-market-live-data-intelligence`

Required exact entry:

```text
origin/main:
365ea26e76e24aa0171945d29ba2b21f79c3a8db

tree:
811985144e835e24dc01f8a130c8b959f83c5f0d
```

This is the normal merge of PR #405, the Owner-accepted L6-A5 post-merge governance reconciliation.

Before mutation:

1. fetch `origin/main`;
2. verify exact commit;
3. verify exact tree;
4. verify clean worktree;
5. verify no unrelated existing branch changes are being adopted.

If commit or tree differs, stop:

`L6_A6_ENTRY_BASE_DRIFT`

Do not silently adopt a later main.

Create a fresh branch:

`phase-l/l6-a6-packaging-portability-technical-exit-review`

Preferred isolated workspace:

`C:\twmarket_temp\l6-a6\repo`

---

# 2. Filesystem safety boundary

D: remains under separate recovery activity.

For this L6-A6 work:

**DO NOT ACCESS D: AT ALL.**

No read, stat, list, search, Git discovery, temporary output, test root or evidence path may use any `D:\...` location.

Use only bounded C: paths, preferably:

`C:\twmarket_temp\l6-a6\`

If D: becomes necessary, stop:

`L6_A6_D_DRIVE_ACCESS_REQUIRED`

Final evidence must record:

`D_drive_access_commands = 0`

Do not use or mutate the Owner's production:

`%LOCALAPPDATA%\TW-Market`

Production-state mutations must remain:

`0`

---

# 3. Authority hierarchy

Use this order:

1. canonical `main@365ea26e...`;
2. Roadmap V3.2;
3. frozen L0 architecture contract;
4. Windows 11 x64 prospective Tier-1 supersession;
5. accepted L6-A0 current-state inventory;
6. frozen L6-A1 installation identity/state/configuration contract;
7. accepted L6-A2 Native lifecycle integration;
8. accepted L6-A3 Native Package C;
9. accepted L6-A4 Docker Local Service packaging;
10. accepted L6-A5 integrated P1–P6 portability acceptance;
11. existing L2 backup/restore/migration authority;
12. L4 security/resource boundaries;
13. L5 exact-six / extension architecture authority.

Historical evidence remains immutable evidence.

Do not reinterpret an older snapshot as current authority when a later accepted record supersedes its current-status prose.

---

# 4. Review nature

A6 is **not another implementation tranche**.

Begin with the presumption:

> A0–A5 are already Owner-accepted and merged. A6 must determine whether their integrated result satisfies the L6 exit contract on current canonical main.

Do not rerun expensive operational acceptance merely to produce new evidence when accepted immutable evidence plus unchanged implementation bytes are sufficient.

The review should use:

```text
accepted evidence
+
current-main byte/provenance verification
+
deterministic current-main regression validation
=
technical exit adjudication
```

Do not turn A6 into A5-R1.

If an accepted A5 assertion is invalidated by current-main product drift, contradictory evidence, or a reproducible defect, that is an exit blocker.

If no such contradiction exists, preserve the accepted A5 result.

---

# 5. Required A0 → A5 lineage review

Verify all A0–A5 accepted tranches and relevant reconciliation commits are ancestors of current main.

At minimum reconcile:

```text
L6-A0 merge:
7ec798d682ac91db776608a5e9a6a98e179dd1ec

L6-A1 merge:
430f280f9c1b4f8d0f387503bb22044214126b39

L6-A2 merge:
911a841b866795e8d0cd83d80b30b34701aa5980

L6-A3 normal merge:
a40141f43f3a1bdeccbab61e67a4a5e161eb8f37

L6-A3 post-merge reconciliation:
ee316f784831fe684e21fa8d146512d96a888050

L6-A4 normal merge:
85a4351f9be46efeb28794079ed7adfeeae0fc8a

L6-A4 post-merge reconciliation:
d5dac702c25e9728db86e9ef32f4fe8185086b89

L6-A5 normal merge:
08bec63ec3d924d2c3b206ecc4fcc017b259ea75

L6-A5 post-merge reconciliation / A6 entry:
365ea26e76e24aa0171945d29ba2b21f79c3a8db
```

Build a machine-readable lineage ledger.

No missing accepted tranche is allowed.

---

# 6. A0 finding reconciliation

A0 originally identified the major L6 problems:

- application tied to source checkout;
- missing persisted user configuration authority;
- incomplete installation lifecycle / no finalized `init`;
- Security Master acquisition/materialization tied to checkout-local paths;
- no accepted Native package;
- no accepted Docker Local Service packaging;
- P1/P4/P5 partial;
- P2/P3 gaps;
- P6 not implemented.

A6 must map each original A0 finding to its accepted downstream closure.

Expected architecture mapping should approximately be:

```text
A1
→ freeze installation identity/state/configuration contract

A2
→ Native init/lifecycle/state-root integration

A3
→ versioned Native Package C / replaceable application resources

A4
→ Docker Local Service packaging and durable mounts

A5
→ final integrated P1–P6 portability acceptance
   + deferred A1→L2 explicit-member state-transfer integration
```

Do not merely state "closed".

For every A0 finding record:

- original finding;
- closing tranche;
- exact accepted evidence;
- current-main verification;
- final PASS / BLOCKED status.

Unresolved L6 blockers must equal zero for technical exit PASS.

---

# 7. A1 contract / gap reconciliation

Review the complete accepted A1 installation identity/state/configuration contract and its implementation-gap map.

Verify that every A1 implementation gap has a final disposition.

In particular reconcile the historically deferred items, including:

- A1-G07 derived/application resource placement;
- A1-G15 explicit L2 restore/portability integration remainder;
- A1-G16 application/resource lookup rooted in source tree.

Do not rely only on old A2/A3 snapshots.

A6 must verify the **final current-main state**, including A5 closure of the deferred state-portability integration.

Produce:

`a1_gap_final_reconciliation.json`

Required condition:

```text
unresolved_A1_gaps = 0
```

Any unresolved required A1 gap is an L6 exit blocker.

---

# 8. Canonical 23 L6 exit criteria

A0 created the canonical candidate L6 exit criteria in:

`docs/governance/phase_l/acceptance_runs/l6-a0-20261021T092005Z/candidate_l6_exit_criteria.json`

A6 must adjudicate all 23 independently.

The criteria are:

```text
01 application/state separation

02 physical roots explicit / contained / backup-classified

03 CLI > ENV > persisted user config > default consistently

04 init/start/status/stop/doctor coherent; doctor read-only

05 fresh NOT_INITIALIZED state

06 explicit Security Master acquisition only;
   acquisition outside replaceable application tree

07 P1 relocation

08 P2 different Windows user

09 P3 new Win11 machine/user/path/no inherited runtime

10 P4 durable restore

11 P5 old supported state/new app/rollback

12 P6 fresh Docker Local Service

13 Native package without .git and with reproducible
   dependencies/resources

14 Docker durable mounts survive image replacement

15 no hidden acquisition

16 integration independence; host stdio MCP separate

17 exact six MCP tools

18 Request/Result/Audit compatible

19 no competing Catalog/Route/Executor

20 historical evidence immutable

21 historical default-CI failures exact and
   candidate-only regression = 0

22 L7 boundary preserved

23 Windows 11 x64 Tier-1 acceptance
```

Create a machine-readable exit matrix with at least:

```text
criterion_id
criterion
source_authority
accepted_closure_evidence
current_main_verification
status
notes
```

Technical exit PASS requires:

```text
23 / 23 PASS
```

Do not convert an unverified criterion to PASS by inference.

---

# 9. P1–P6 review rule

A5 already achieved:

```text
P1 = PASS
P2 = PASS
P3 = PASS
P4 = PASS
P5 = PASS
P6 = PASS
```

A6 does not needlessly redo all physical acceptance.

Instead:

### P1
Verify accepted actual relocation evidence and prove relevant current product/package source remains unchanged.

### P2 / P3
Verify committed Windows Sandbox guest evidence:

- genuine `WDAGUtilityAccount`;
- distinct SID/profile;
- fresh guest machine identity;
- Windows 11 x64;
- no inherited TW-Market runtime;
- no inherited host Python/Git runtime;
- actual Package C bootstrap/lifecycle acceptance.

Do not launch another Sandbox merely to reproduce evidence unless committed evidence is incomplete or contradicted.

### P4
Verify canonical L2 CORE/FULL_GOVERNED path, isolated restore, destination identity preservation and absence of second restore authority.

### P5
Verify actual accepted older A3 state/package → current app → rollback evidence and `SUPPORTED_NO_MIGRATION_REQUIRED`.

No fabricated migration.

### P6
Verify committed fresh-volume/image-replacement state-survival evidence.

The fact that the replacement image reference was no longer locally resolvable after the host reboot remains a disclosed retained limitation, not an automatic failure, provided:

- the accepted runtime/image evidence is intact;
- source/current product bytes are unchanged;
- no contradictory current-main evidence exists.

Do not publish/re-pull/reconstruct the historical replacement image solely to manufacture a new digest.

---

# 10. Acceptance-source → current-main immutability review

Accepted A5 runtime/package source:

```text
commit:
3707c553497240f6ff0f7e5358301395fd60205a

tree:
946e765b26b2520f623672dc49a51c913139f44f
```

Accepted A5 final candidate:

```text
32bc480cccdd7eb394062ccfe34a44958fc56bf1
tree:
041f7c660a3fba40b84d5fbab869c2ee353919ac
```

A5 merge:

```text
08bec63ec3d924d2c3b206ecc4fcc017b259ea75
```

Current A6 base:

```text
365ea26e76e24aa0171945d29ba2b21f79c3a8db
```

Prove that product/runtime/package/test authority has not drifted after accepted A5 source.

At minimum verify relevant classes:

- `scripts/`
- `server/`
- `packaging_native/`
- `packaging_docker/`
- schemas;
- capability/public contract files;
- routing/executor/source authority;
- dependency lock/requirements;
- product version;
- tests affecting L6 behavior.

Expected post-A5 changes should be governance/evidence/harness/front-door reconciliation only.

If a current-main product-affecting delta exists after the accepted A5 source that was not covered by A5 acceptance, stop:

`L6_A6_POST_ACCEPTANCE_PRODUCT_DRIFT`

Do not silently bless it.

Also revalidate A5's exact application-blob identity/provenance set where applicable.

---

# 11. Frozen L0 architecture review

A6 must explicitly determine whether current L6 satisfies the relevant frozen L0 obligations.

Review at least:

### Deployment
- Native Windows remains the primary operational baseline.
- Docker Local Service is a packaging profile, not a second product.
- host stdio MCP remains separate.

### Portability/state
- application replaceable;
- installation state durable;
- app/state/cache/log/temp ownership distinct;
- no developer-machine runtime dependency.

### Configuration
- CLI > ENV > user settings > default.

### Lifecycle
- init/start/status/stop/doctor coherent;
- doctor read-only;
- no hidden market acquisition.

### Upgrade
- no silent incompatible migration;
- supported state works;
- migration remains L2 authority;
- rollback semantics preserved.

### Backup/restore
- CORE and FULL_GOVERNED boundaries preserved;
- application/venv/Docker image/cache/temp not canonical backup.

### Integrations
Core remains independent of:

- Secure MCP Tunnel;
- ChatGPT;
- Hermes;
- Codex;
- Antigravity;
- model/provider-specific runtime state.

Any violation of frozen L0 is an exit blocker.

---

# 12. Windows Tier-1 policy

Historical L0-D03 remains immutable historical text.

But the accepted prospective L6 policy supersedes release-blocking Native Tier-1 for L6 onward:

```text
Windows 11 x64 = Tier-1
Windows 10 x64 = not release-blocking for L6+
```

A6 must not require Windows 10 acceptance.

Verify A5's genuine Windows 11 x64 acceptance is sufficient for criterion 23.

Do not rewrite historical L0-D03.

---

# 13. Native Package C review

Retain accepted Native identity:

```text
TW-Market-1.0.0-windows-x64.zip

SHA-256:
6772e8c3550525ff0d952929c7e36cef4833e265936b0009b6d517152ab74e04

members:
338

pinned Windows wheels:
49
```

Review conclusions must confirm:

- versioned replaceable bundle;
- bundle-local derived venv;
- external durable state;
- no `.git`;
- no developer checkout;
- no developer venv;
- offline wheelhouse bootstrap;
- arbitrary path support;
- installed supported CPython prerequisite remains explicit;
- package is not an installer;
- absence of MSI/MSIX/etc. is not by itself an L6 blocker under accepted A3 architecture.

Do not rebuild the ZIP and call a different byte stream the accepted A5 artifact.

A new build may be used only as a reproducibility diagnostic if clearly distinguished from the accepted artifact.

---

# 14. Docker review

Retain accepted identities:

```text
base:
python:3.13-alpine@
sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741

A5 source image:
sha256:2b25c1e54879b0761d3c0a3591236cb2a1f820c1530fee25f643ec93cf962675

A5 replacement image:
sha256:98bafa33505e0d5f4c088e58949e388768b21b0a0741f4da5649eff539f91323
```

Verify accepted evidence proves:

- Linux/amd64;
- one Local Service only;
- loopback-only host publishing;
- no generic remote exposure;
- explicit init;
- durable mounted state;
- state survives container/image replacement;
- image/container/network identity is not installation identity;
- no canonical state in image;
- no MCP server moved into the container;
- host stdio MCP still exact six.

Do not reset/prune unrelated Docker resources.

A6 does not authorize Docker publication.

---

# 15. Public contract and authority invariants

Verify no L6 work changed:

- Unified Request compatibility;
- Result semantics;
- Audit semantics;
- canonical AI Handoff lineage;
- Catalog authority;
- Route authority;
- Executor authority;
- source authority;
- authorization boundary.

MCP must remain exactly six tools:

```text
market_describe_capabilities
market_export_ai_handoff
market_fetch_evidence
market_preview_request
market_read_result
market_validate_request
```

Required:

```text
tool_count = 6
```

No seventh lifecycle/backup/portability/Docker tool.

No second Catalog.

No second routing authority.

No second execution authority.

No evidence text becomes executable authority.

---

# 16. L2 boundary review

A5 added only the bounded A1→L2 explicit-member integration deferred from earlier L6 work.

A6 must verify:

- L2 remains the sole canonical backup/restore/migration authority;
- A1 adapter does not discover arbitrary state;
- source members remain explicit;
- restore remains isolated;
- destination installation identity remains destination identity;
- source installation identity remains provenance only;
- settings admission remains bounded;
- runtime/PID/cache/log/temp remain nonportable;
- no second activation/migration engine exists.

Any competing transfer authority is an L6 blocker.

---

# 17. Deterministic regression validation

Run current-main deterministic validation sufficient to prove that accepted A5 implementation still behaves as reviewed.

At minimum include:

- relevant A1 contract tests;
- A2 lifecycle/installation tests;
- A3 Native packaging/resource tests;
- A4 Docker/network/mount contract tests;
- A5/L2 adapter tests;
- L2 backup/restore/migration tests;
- L4 network/path/security tests relevant to packaging/runtime;
- exact-six MCP/public-contract tests;
- Security Master root/acquisition boundary tests;
- package/Docker build-context validators;
- product-version/release-hygiene/front-door validators;
- compile/static checks;
- `git diff --check`.

Do not weaken/delete/reclassify tests to obtain PASS.

---

# 18. Expanded A5 applicability suite

A5 recorded:

```text
525 passed
2 failed
```

The two failures were preserved historical L5 no-product-change scope assertions which already failed on the exact A5 entry after accepted A4 and were superseded by later explicit L6 authority.

A6 must:

- identify them by exact node ID;
- reproduce/classify them if the suite is rerun;
- prove they are still the same historical scope assertions;
- not call the suite overall PASS;
- not delete/modify those tests;
- not count them as new L6 defects solely because they remain failing.

If either failure changes meaning or a new failure appears, investigate before exit PASS.

---

# 19. Default CI

A5 accepted evidence recorded:

```text
1245 passed
45 failed
4 skipped
5 deselected
```

for both exact base and A5 final candidate, with identical failed-node sets and:

```text
candidate-only regression = 0
```

This historical count is context, not a magic required number.

For A6:

1. run default CI on the exact A6 entry base;
2. run default CI on the final A6 candidate;
3. use the same environment;
4. compare exact failed node IDs.

Required:

```text
A6_candidate_only_failed_nodes = 0
```

If inherited failures remain, overall CI remains `FAIL`.

Do not rename inherited FAIL as PASS.

Also reconcile the current same-environment failure set against committed A5 evidence. If environmental drift changes counts, explicitly classify the drift and preserve same-environment base/candidate comparison as the controlling A6 regression test.

Any candidate-only failure is:

`L6_A6_CANDIDATE_ONLY_CI_REGRESSION`

and blocks PASS.

---

# 20. Historical evidence immutability

Verify A0–A5 acceptance records remain unchanged.

Do not rewrite:

- A0 evidence;
- A1 contract/evidence;
- A2 acceptance;
- A3 acceptance;
- A4 acceptance;
- A5 acceptance.

Recompute manifests/self-digests where provided.

Distinguish:

```text
historical run bytes
!=
current governance prose
```

A6 may add new review evidence but may not rewrite historical evidence to make it align with current state.

---

# 21. Retained limitations review

Create a machine-readable retained-limitations record.

At minimum consider:

1. existing default-CI historical failures;
2. two historical L5 scope-assertion failures in expanded A5 applicability;
3. A5 replacement Docker image reference not locally resolvable after reboot, while committed completed evidence remains intact;
4. Package C requires supported installed CPython rather than embedding Python;
5. Native distribution is ZIP/bundle based, not MSI/MSIX installer;
6. Docker image is not registry-published;
7. release signing/publication is not done;
8. Windows 10 is not L6+ release-blocking Tier-1;
9. A6 does not certify live provider availability;
10. Security Master live refresh is intentionally separate from install/start.

For every limitation record:

```text
limitation
why_nonblocking_for_L6
authority
reconsider_when
```

A limitation may remain only if it does not violate a frozen L0/L6 obligation.

---

# 22. L7 boundary

A6 must explicitly preserve L7.

The following remain outside L6-A6:

- release-version final decision;
- final v1.5.0 vs v2.0.0 adjudication;
- CI platform/release automation;
- signing;
- release manifest publication;
- GitHub Release;
- Docker registry;
- compatibility-range decision for MCP SDK;
- bounded live release acceptance;
- stable release publication.

Do not perform them.

Criterion 22 passes only if L7 remains clearly separate.

---

# 23. No live-provider activity

A6 is an offline technical exit review.

Expected:

```text
live_provider_requests = 0
market_acquisition_attempts = 0
Security_Master_live_updates = 0
production_state_mutations = 0
D_drive_access = 0
```

Allowed external activity is limited to ordinary Git/GitHub access and package/test environment preparation if genuinely needed.

Do not contact TWSE/TPEx/TAIFEX/Yahoo/FinMind/Fugle/Fubon merely to prove L6 exit.

---

# 24. A6 evidence

Create:

`docs/governance/phase_l/PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_2026-10-23.md`

Acceptance directory:

`docs/governance/phase_l/acceptance_runs/l6-a6-<timestamp>/`

At minimum include machine-readable:

```text
authority.json
entry_identity.json
a0_to_a5_lineage.json
a0_finding_reconciliation.json
a1_gap_final_reconciliation.json
l0_obligation_review.json
l6_exit_criteria_matrix.json
p1_p6_evidence_reverification.json
acceptance_source_current_main_diff.json
application_blob_integrity.json
native_package_review.json
docker_packaging_review.json
l2_boundary_review.json
public_contract_review.json
exact_six_mcp.json
historical_evidence_integrity.json
focused_validation.json
expanded_validation.json
base_default_ci.json
candidate_default_ci.json
failed_node_comparison.json
retained_nonblocking_limitations.json
scope_diff_verification.json
final_technical_review.json
manifest.json
```

Manifest must use a deterministic canonical digest/self-digest scheme consistent with existing governance practice.

No large ZIP/Docker export/venv/installers need be committed.

Record hashes instead.

---

# 25. A6 source-change policy

The preferred A6 implementation delta is:

```text
governance
+
acceptance/review evidence
+
review-only harness if necessary
```

Product/runtime code changes expected:

`0`

Public contract changes expected:

`0`

Test semantic changes expected:

`0`

Dependency changes expected:

`0`

If a technical exit blocker requires product/runtime repair, stop:

`L6_A6_REPAIR_TRANCHE_REQUIRED`

Do not fix it in the exit-review branch.

If a review helper is needed, keep it under A6 acceptance evidence/harness or other clearly review-only location and ensure it cannot become production authority.

---

# 26. Technical PASS conditions

Do not claim PASS unless all are true:

1. exact entry commit/tree verified;
2. clean isolated review branch;
3. A0–A5 accepted lineage verified;
4. A0 findings all have final accepted disposition;
5. unresolved A1 gaps = 0;
6. all 23 A0 candidate exit criteria = PASS;
7. P1–P6 accepted evidence remains valid;
8. no post-A5 unaccepted product drift;
9. frozen L0 deployment/state/config/lifecycle/upgrade/backup/integration obligations satisfied;
10. Windows 11 x64 Tier-1 acceptance satisfied;
11. Native Package C remains valid;
12. Docker Local Service profile remains valid;
13. application/state separation preserved;
14. physical root containment/classification preserved;
15. lifecycle/doctor/read-only semantics preserved;
16. no hidden acquisition;
17. L2 remains sole backup/restore/migration authority;
18. host stdio MCP remains outside Docker;
19. exact six MCP tools preserved;
20. Request/Result/Audit remain compatible;
21. no competing Catalog/Route/Executor;
22. historical evidence immutable;
23. focused validation passes;
24. historical expanded-suite failures remain correctly classified;
25. default CI base/candidate comparison completed;
26. candidate-only CI failures = 0;
27. production-state mutation = 0;
28. live-provider acquisition = 0;
29. D-drive access = 0;
30. L7 boundary preserved;
31. retained limitations do not violate frozen L0;
32. A6 diff contains no unauthorized product/runtime/test/dependency changes.

Only then use:

`PHASE_L_L6_EXIT_REVIEW_PASS`

And state:

```text
L6 status:
TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED

Owner final closure:
PENDING

L7:
NOT AUTHORIZED

Phase M:
NOT AUTHORIZED
```

---

# 27. Failure / hold semantics

If any required criterion cannot be proven, do not create a false PASS.

Use a precise HOLD/FAIL reason such as:

`L6_A6_ENTRY_BASE_DRIFT`

`L6_A6_D_DRIVE_ACCESS_REQUIRED`

`L6_A6_A0_FINDING_UNRESOLVED`

`L6_A6_A1_GAP_UNRESOLVED`

`L6_A6_EXIT_CRITERION_UNPROVEN`

`L6_A6_POST_ACCEPTANCE_PRODUCT_DRIFT`

`L6_A6_A5_EVIDENCE_INTEGRITY_FAILURE`

`L6_A6_PUBLIC_CONTRACT_DRIFT`

`L6_A6_MCP_SURFACE_DRIFT`

`L6_A6_L2_AUTHORITY_CONFLICT`

`L6_A6_HIDDEN_ACQUISITION_DETECTED`

`L6_A6_CANDIDATE_ONLY_CI_REGRESSION`

`L6_A6_REPAIR_TRANCHE_REQUIRED`

Do not widen scope to repair.

Return the exact blocker and the minimal separately-authorized repair that would be required.

---

# 28. Governance/front-door updates after PASS

Only after technical PASS update current governance/front doors to say:

```text
L6-A0 through L6-A5:
OWNER-ACCEPTED AND MERGED

L6-A6 technical review:
PHASE_L_L6_EXIT_REVIEW_PASS

L6:
TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED

Owner final closure:
PENDING

L7:
NOT AUTHORIZED

Phase M:
NOT AUTHORIZED
```

Do not write:

`L6 CLOSED`

Do not authorize L7.

Do not mark Phase L closed.

A6 technical exit is not Owner final closure.

---

# 29. Git / PR authority

After technical PASS:

1. verify exact changed paths;
2. verify no unauthorized product/runtime/test/dependency mutation;
3. run `git diff --check`;
4. commit review evidence/governance;
5. record exact A6 candidate commit/tree;
6. push;
7. open a PR to `main`.

Suggested PR title:

`L6-A6 packaging and portability technical exit review`

PR body must include:

- Owner authority token;
- exact entry commit/tree;
- exact A6 candidate commit/tree;
- A0–A5 lineage result;
- unresolved A0 findings count;
- unresolved A1 gaps count;
- 23/23 exit-criteria matrix disposition;
- P1–P6 reverification result;
- Native package identity;
- Docker identities;
- current-main vs accepted-source product-drift result;
- exact-six MCP result;
- public-contract result;
- L2 authority result;
- focused/expanded test results;
- base/candidate default-CI results;
- candidate-only failure count;
- historical evidence integrity result;
- retained limitations;
- D-drive access count;
- provider/live acquisition count;
- production-state mutation count;
- explicit statement:

```text
Technical disposition:
PHASE_L_L6_EXIT_REVIEW_PASS

L6 Owner final closure:
PENDING

Merge:
NOT AUTHORIZED

L7:
NOT AUTHORIZED

Phase M:
NOT AUTHORIZED
```

Push and PR opening are authorized.

**Merge is NOT AUTHORIZED.**

Do not enable auto-merge.

After PR opening, stop and return:

- PR URL/number;
- entry commit/tree;
- A6 candidate commit/tree;
- exit criteria 23/23 status;
- A0 finding reconciliation;
- A1 gap reconciliation;
- tests/CI;
- limitations;
- technical disposition;
- Owner final closure pending.

Do not begin L7.

---

# 30. Final instruction

Treat A6 as the **technical exit adjudication for all L6 Packaging & Portability work**, not as a new implementation tranche.

The core question is:

> Does canonical current main, using the already accepted A0–A5 implementation and immutable evidence, satisfy every frozen L6 packaging/portability obligation without unresolved blocker or new product drift?

If yes:

`PHASE_L_L6_EXIT_REVIEW_PASS`

If no:

stop with the exact blocker.

Even after technical PASS:

> **L6 is not CLOSED until separate Owner final closure is explicitly authorized and recorded.**

Proceed within this bounded authority.