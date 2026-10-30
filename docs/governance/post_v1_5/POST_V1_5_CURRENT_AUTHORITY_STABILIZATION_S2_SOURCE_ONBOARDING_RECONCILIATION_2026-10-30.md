# S2 — Source Onboarding / First-run Reconciliation

Date: 2026-10-30 (Asia/Taipei). Status: READY_WITH_NOTES, uncommitted candidate for independent review.
Owner explicitly authorized S2 documentation, isolated verification and additive
test enrollment. COMMIT / PUSH / PR are NOT AUTHORIZED and were not performed.
This bounded authorization supersedes older root next-work prose only for S2.
S1 and S3/S3-R1 remain closed; S4/S5, P1/P2–P5 and Phase M are excluded.

## Baseline and protected authority

Starting branch main; HEAD = local origin/main =
`581928b0b7f38bf4c540d5b1dbef196fddc57f81`; clean tree; staged 0; ahead/behind 0/0.
S1 current V3 authority is canonical. S3/S3-R1 are canonical through PR #424;
merge authority remains current-merge-gate. No fetch or external acquisition was
used to establish this local starting state.
Stable v1.5.0 commit remains `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76`,
tree `d44f66dc154c21326ac8b105d2f15fd793f6071b`. Phase L CLOSED;
Phase M NOT_AUTHORIZED. Rollback target is starting HEAD, limited to this S2
candidate; no reset, rollback or deletion was executed.

## Documentation inventory (before edits)

| Path | S2 role | Source-start truth / stale point | Changed |
|---|---|---|---|
| docs/operator/QUICK_START.md | PRIMARY_ONBOARDING_AUTHORITY | Path C omitted lifecycle init and implied Workbench OR MCP independent launch | yes |
| README.md | SECONDARY_REFERENCE | duplicated incomplete source sequence; live identity update appeared prerequisite | yes; replace procedure with primary link |
| README.zh-TW.md | SECONDARY_REFERENCE | same duplicated sequence in Chinese | yes; primary link |
| docs/operator/LOCAL_WORKBENCH.md | SECONDARY_REFERENCE | direct launcher omitted initialized-installation prerequisite | yes; prerequisite/link |
| docs/reference/MCP_REFERENCE.md | SECONDARY_REFERENCE | direct stdio launcher omitted Local Service/init/preflight | yes; prerequisite/link |
| docs/distribution/MCP_DISTRIBUTION.md | SECONDARY_REFERENCE | source alternative lacked init/service sequence; identity vs installation wording mixed | yes; source prerequisite/link; frozen asset identity untouched |
| docs/operator/M8R_08B_MCP_LOCAL_CLIENT.md | SECONDARY_REFERENCE | service dependency correct, but init omitted; machine-specific paths and old V1 service-check wording | yes; portable placeholders, init link, current MCP V2 contract |
| docs/operator/TROUBLESHOOTING.md | SECONDARY_REFERENCE | direct source commands lacked installation/service prerequisites | yes; short explanations/link |
| docs/operator/MODE_ABC_WALKTHROUGH.md | SECONDARY_REFERENCE | launcher snippet assumed prior setup | yes; short prerequisite/link |
| docs/reference/API_REFERENCE.md | SECONDARY_REFERENCE | direct launcher assumed prior setup | yes; short prerequisite/link |
| CONTRIBUTING.md, docs/contributor/CONTRIBUTING.md | SECONDARY_REFERENCE | development/test guidance, no independent source-first-run procedure | no |
| docs/INDEX.md | SECONDARY_REFERENCE | correctly routes operators to Quick Start | no |
| docs/agent_usage_guide.md, llms.txt | NOT_RELEVANT | agent evidence semantics/discovery rather than source installation procedure | no |
| docs/contributor/DEVELOPMENT_GUIDE.md, docs/contributor/TESTING_GUIDE.md | NOT_RELEVANT | milestone development/testing guidance; no replacement S2 onboarding authority | no |
| docs/user/M8R_06_01_MODE_A_USER_GUIDE.md | HISTORICAL_ONLY for S2 | old compact-candidate activation / Mode A entry context, superseded by current operator frontdoor | no |
| docs/distribution/MCP_REGISTRY_READINESS.md | HISTORICAL_ONLY for S2 | old submission-readiness context, not current source first-run authority | no |
| docs/archive/, docs/reviews/, docs/protocol/, milestone acceptance/governance records | HISTORICAL_ONLY | historical commands and gate truth retained | no |

Inventory used source/installation/first-run, lifecycle, Local Service, Workbench,
MCP, startup-check, Security Master and root-variable searches across current
frontdoors and docs; historical records were not rewritten to current wording.

## Executable truth established before editing onboarding prose

Owners: scripts/tw_market_installation.py; scripts/tw_market_lifecycle.py;
scripts/run_unified_workbench.py; server/main.py;
server/unified_workbench_router.py; server/services/unified_mode_a.py;
scripts/run_unified_market_evidence_mcp.py; server/unified_mcp/local_service_client.py.
Existing L6 installation/lifecycle, launcher-readiness and API tests were inspected.

```text
existing current source + dependencies passing the supported environment verifier
-> verify_environment + current V3 source validator
-> lifecycle init (offline)
-> installation READY / identity NOT_INITIALIZED
-> Workbench launcher starts loopback Local Service and serves UI
-> MCP startup-check against that Local Service
-> MCP stdio for an MCP host

identity-dependent operation without active identity -> fail closed
```

Init command:
`python -B scripts/tw_market_lifecycle.py init --home <home> --state-root <state> --json`.
Fresh status is INSTALLATION_NOT_INITIALIZED; Workbench startup-check exits 1 and
MCP startup-check exits 2. Init exits 0 / INSTALLATION_READY; installation's
installation_status is READY, identity remains NOT_INITIALIZED, network_on_init
is false. Init makes HOME meta/config/cache/logs and STATE_ROOT security-master /
watchlists/governed directories. The two initial files are meta/installation.json
and config/settings.json. Init also performs temporary lock / bounded write-fsync-remove
probes and atomic publication staging, leaving no probe/lock files behind.
No identity pointer, release, Watchlist or acquisition
is created. Repeating init preserves installation ID and both file hashes.
Existing business state is not silently adopted. Metadata binds state-root;
conflicting requests fail STATE_ROOT_CONFLICT. CLI root arguments override env;
HOME otherwise uses LOCALAPPDATA/TW-Market and state defaults to HOME/state.
Runtime/temp are installation-ID keyed under system temp, outside source.

Security Master ACTIVE does not gate all startup. Missing fresh identity is a
supported preload result: status not_initialized, schema/catalog loaded, identity
not loaded, exit 0. Useful no-network health/UI/capability inspection remains
available. A schema-valid V3 identity validation request returns HTTP 503 /
SECURITY_MASTER_NOT_INITIALIZED. No identity fixture or fake ACTIVE state is used.
Corrupt/unavailable identity states are not generalized into benign fresh state.

Workbench is the browser surface served by Local Service, not an independent
backend stack. MCP is a stdio client of the same Local Service, not its service
launcher. With initialized state but service absent, MCP preflight exits 3 /
local_service_unavailable; with service ready and identity absent, it exits 0 /
startup_check=ok on stderr. Current MCP negotiates service V2 through its header;
plain capabilities GET retains the V1 compatibility default. Empty stdio input
may exit without checking the service because first-frame prefetch occurs first;
startup-check is the supported readiness proof without a real MCP host.

## Isolated smoke architecture and containment

One new file: tests/integration/test_source_onboarding_first_run.py, three tests:
real source-first-run process smoke; existing-default/state/network guard negative
controls; essential documentation startup-order/navigation consistency.
No product behavior is mocked to make first-run or identity succeed.

All eight required/user-location variables are isolated per fresh test root: TW_MARKET_HOME,
TW_MARKET_STATE_ROOT, LOCALAPPDATA, TEMP, TMP, HOME, USERPROFILE, APPDATA.
TW_MARKET_HOST / TW_MARKET_PORT also select an unused ephemeral endpoint before
any status/preflight command; no stage probes the developer default port.
Inherited TW_MARKET_ / M8R_ / A6_ overrides, service URL, Python path/home,
pytest options and proxy settings are removed before selected test settings.
No real installation is inspected to determine whether the test may pass.

A test-owned sitecustomize guard is injected through child PYTHONPATH. Each
command must record guard_loaded; the service PID must also record guard_loaded.
It audits Python child creation and sockets, rejects non-loopback network and
unguarded native children or explicit child environments that discard containment,
rejects reads/stat/discovery of original known
TW-Market state roots and test-owned initialized default decoy, and rejects writes
outside the disposable root. Parent HTTP requests use only the selected numeric
loopback endpoint with proxy and redirect following disabled. This is Python
process test containment, not an OS firewall or protection against hostile native
extensions. No native network client is invoked.

The negative control creates an actual initialized installation under isolated
LOCALAPPDATA, then fences it. Explicit fresh TW_MARKET_HOME still fails pre-init;
opening/stat-ing the fenced decoy and connecting to reserved external IPv4 are
rejected before access/connection. A connection to the unselected loopback port
8000 and a child launch that discards guard environment are also rejected.
The five intentional denials belong only to
this negative test; positive smoke requires zero denials.

A foreground Workbench/Local Service Python process binds 127.0.0.1 on an ephemeral
port. No browser/real MCP host is used. The handle is terminated in finally,
waited, and killed/waited only if necessary; closed port and terminated PID are
asserted. No managed detached runtime or background service is left behind.

Accepted focused command:
`python -B -m pytest -p no:cacheprovider tests/integration/test_source_onboarding_first_run.py --basetemp=C:/twmarket_temp/s2-20261030-port-isolated-final -q`.
Result: 3 passed in 31.51s, exit 0. Verified Windows 11 / CPython 3.13.7;
existing dependencies include mcp 1.29.0. No dependency installation or download.

Positive evidence root:
`C:/twmarket_temp/s2-20261030-port-isolated-final/test_isolated_source_first_run0/source-first-run/`.
smoke-evidence.json records commands, exits/stdout/stderr, all isolated roots,
health/UI, service contract, identity error, created files and service PID/teardown.
Positive audit: 30 events, zero denials. Final installation READY; identity
NOT_INITIALIZED; service terminated; port closed. Persistent product files are
installation/config/settings.json, installation/meta/installation.json and
installation/logs/operational-events.jsonl. Test-owned guard/audit/service logs
are also enumerated; no Security Master data or Watchlist DB was created.

Intermediate harness errors are retained: Windows Popen audit executable=None
required command-line executable extraction; raw capabilities GET used default
V1 rather than the MCP's explicit V2 header. Only tests were corrected; these
were not runtime defects. Documentation line endings were preserved as LF to
avoid unrelated full-file diffs. No runtime correction was made.
The initial default-profile validation used an intermediate port guard: default returned
1353 passed / 13 failed, including one S2 harness failure. The over-restrictive
guard blocked Windows asyncio's own socketpair. Final guard admits only the
selected service port plus connections to the same process's own ephemeral
loopback listener (weak socket ownership, no retained socket lifetime). An
asyncio probe passes while arbitrary port 8000 remains denied. Those intermediate
results under C:/twmarket_temp/s2-20261030-results-120529/ are preserved and are
not final acceptance. Complete final validators/merge/raw are rerun after this
harness correction; no skip, xfail, test weakening or diagnostic waiver was used.

Dependency verification is not full lock replay: the existing interpreter passes
verify_environment.py (including exact mcp 1.29.0), but installed versions such as
FastAPI 0.133.0 / jsonschema 4.25.0 / pandas 2.3.1 differ from the current lock
projection. No dependency install/download or canonical release qualification is
claimed. Source docs prescribe the lock; the isolated state smoke verifies the
actual supported-verifier environment and discloses this limit.

## Enrollment and S3 protection

Only default-ci and full-current gain the one new explicit test path and its
three node identities. Previous floor paths/nodes remain subsets. Floor metadata
retains original S3 provenance and adds an explicit S2 superset_updates entry
bound to this record and starting HEAD. Validator change is the floor SHA anchor
only: 071d9a24fcf432d55b5f6cbb5690cc6b2027a7afb0176b08167ab24a6c95eb67.
No known diagnostic ID/classification, merge semantics, historical TG authority,
release contract, release runner or workflow is changed.

Observed resulting floors: default 122 paths / 1370 nodes; full 169 / 1743.
Validator performs real collection for both; missing paths/nodes are empty.
No full-current execution is claimed by S2; its enrollment/selection is validated.

## Final validation and candidate handoff

Final required validators all PASS / exit 0:

```text
python -B scripts/validate_current_test_governance.py
python -B scripts/validate_test_governance_tg5.py
python -B scripts/validate_phase_h_v3_contracts.py
python -B scripts/validate_portable_catalog_sync.py
python -B scripts/validate_runtime_skill_guide_sync.py
python -B scripts/validate_l5_extension_publication_conformance.py
```

Final merge command:
`python -B scripts/run_current_merge_gate.py --output C:/twmarket_temp/s2-20261030-final-121846/merge.json`.
MERGE_VERDICT PASS; blocking_failures 0; known_diagnostic_failures 12;
known_diagnostic_now_passing []; coverage_status PASS; raw_pytest_exitstatus 1;
process exit 0. Full stdout/failure diagnostics are retained, not filtered.

Final raw command: `python -B scripts/run_test_profile.py default-ci --json`.
1375 collected; 1370 selected; 1354 passed; 12 failed; 4 skipped; 5 deselected;
process exit 1. Failed-node set is exactly equal to unchanged governed diagnostics;
no S2 failure is absorbed. Both final profile executions use the same unchanged
implementation inputs; only this record receives final evidence after testing.
PYTHONDONTWRITEBYTECODE=1 and no cache provider were selected for validation;
raw default used normal system temp (no source-state override for other tests).

Final raw failed IDs:

```text
tests/unit/test_phase_i_i3_a0_p1_adjudication.py::test_p1_governance_validator_passes_under_network_denial
tests/unit/test_phase_i_i3_a0_p3.py::test_p3_validator_production_containment_and_readiness
tests/unit/test_phase_i_i3_a0_p3_r1.py::test_r1_validator
tests/unit/test_phase_i_i3_a0_preflight.py::test_current_hold_record_and_runtime_containment
tests/unit/test_phase_i_i3_a0_preflight.py::test_p0_validator_cannot_claim_pass_or_rearm
tests/unit/test_phase_i_i3_a1.py::test_a1_validator_and_immutable_a0_anchors
tests/unit/test_phase_i_i3_a3_attempt_2_bounded_live.py::test_exact_mapping_and_frozen_candidate_and_production_containment
tests/unit/test_phase_i_i3_a3_r3_http520_lifecycle.py::test_committed_attempt4_pass_lineage_and_containment
tests/unit/test_phase_j_ghi_readiness_preflight.py::test_current_record
tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-08]
tests/unit/test_phase_j_ghi_readiness_preflight.py::test_missing_runtime_can_be_nonblocking_when_safe_or_optional[J1-10]
tests/unit/test_phase_j_ghi_readiness_preflight.py::test_unchecked_g_h_do_not_themselves_block_pass
```

`git diff --check` PASS before closing record; repeated after final record update.

Production runtime changes: NONE. S1 semantics, S3 merge semantics, schemas,
Routing/Catalog/executors/adapters, Local Service/MCP/Workbench implementations,
Security Master/Watchlists, P1, release assets/contract, Registry, workflow triggers
and Phase M are unchanged. No external acquisition or live authority was consumed.

Intended files: ten current docs from the changed inventory rows; the new smoke;
config/test_execution_profiles.json; config/current_test_coverage_floor.v1.json;
scripts/validate_current_test_governance.py (digest only); this S2 record.
Exact final containment, evidence and reviewer checklist follow. Staged 0; no commit/push/PR.

Limitations: Windows current-source verification only; existing installed
runtime/dependencies (not a full requirements-lock replay), no fresh dependency acquisition, browser E2E, live identity
activation or market-provider availability claim. No Linux/macOS/container
verification. Historical/capability/Registry and broader testing-guide prose
outside source onboarding are not reconciled by S2.


## Final changed-file containment

Exactly 15 intended candidate files (13 tracked modifications, 2 new):

- `README.md`
- `README.zh-TW.md`
- `config/current_test_coverage_floor.v1.json`
- `config/test_execution_profiles.json`
- `docs/distribution/MCP_DISTRIBUTION.md`
- `docs/operator/LOCAL_WORKBENCH.md`
- `docs/operator/M8R_08B_MCP_LOCAL_CLIENT.md`
- `docs/operator/MODE_ABC_WALKTHROUGH.md`
- `docs/operator/QUICK_START.md`
- `docs/operator/TROUBLESHOOTING.md`
- `docs/reference/API_REFERENCE.md`
- `docs/reference/MCP_REFERENCE.md`
- `scripts/validate_current_test_governance.py`
- `docs/governance/post_v1_5/POST_V1_5_CURRENT_AUTHORITY_STABILIZATION_S2_SOURCE_ONBOARDING_RECONCILIATION_2026-10-30.md`
- `tests/integration/test_source_onboarding_first_run.py`

Protected runtime/S1/S3 merge runner/current authority map/release/workflow files
were compared byte-for-byte with starting HEAD. Only the current validator's
reviewed floor digest is changed; its validation semantics are unchanged.
All 14 implementation/documentation/config/test input hashes remained identical
through final acceptance; this new governance record is finalized afterward.
Branch main; HEAD = origin/main = 581928b0b7f38bf4c540d5b1dbef196fddc57f81;
ahead/behind 0/0; staged 0. No commit, push, PR, branch deletion or repository
cleanup. No existing app state or historical artifact was modified.

## Evidence identities

Final local evidence directory: `C:/twmarket_temp/s2-20261030-final-121846/`.
Focused source evidence and audit remain at the explicitly listed disposable root
above. File inventory includes the generated smoke-evidence.json report itself
in addition to the pre-report created_files enumeration contained in that report.
Evidence hashes:

| Artifact | SHA-256 |
|---|---|
| `C:/twmarket_temp/s2-20261030-final-121846/summary.json` | `9952d2305094f75c4794928426669bf5381cdcce8f1b53585e67cf34c0259697` |
| `C:/twmarket_temp/s2-20261030-final-121846/merge.json` | `78626ff35b6b81cb81aa0c6c957d06c206c9e4d07c34d7671e5edb6c4f39eb85` |
| `C:/twmarket_temp/s2-20261030-final-121846/merge.log` | `6c9ed85d380cdd835467cd6abb6705be3849d4a3bd07187dfd886adcab939af1` |
| `C:/twmarket_temp/s2-20261030-final-121846/default-ci.log` | `fb399986f241c75088c858b009dd4b149d176497d18f20be6d12c5ab96d4647f` |
| `C:/twmarket_temp/s2-20261030-port-isolated-focused.log` | `775fbbc64f0e53c621b4addd35e09680b0e3ae05529f28425ed9648123a84749` |
| `C:/twmarket_temp/s2-20261030-port-isolated-final/test_isolated_source_first_run0/source-first-run/smoke-evidence.json` | `e39b3edbd2106d1d8eae35dcf2e18061e1077ccbe0e7b3626f442ce0643f5ee9` |

## Fresh independent-review checklist

1. Reconfirm starting HEAD/ref and the 15-file uncommitted candidate; staged 0.
2. Trace init/installation resolver, preload, HTTP routing and MCP client contract;
   do not infer topology from prose or empty stdin success.
3. Run the three S2 tests with a fresh outside-checkout disposable pytest root.
   Check all eight isolation variables, selected service port from the first
   inspection, zero positive guard denials and all five negative guard controls.
4. Verify actual initialized-default decoy cannot satisfy the fresh explicit root;
   identity stays NOT_INITIALIZED and schema-valid V3 identity validation is 503.
5. Verify init idempotence/file hashes, loopback health/UI/capabilities, MCP absent
   exit 3 / present exit 0, terminated service process and closed port.
6. Verify every previous path/node is retained; one path/three nodes added to both
   profiles and floors; known 12 classifications and four optional skips unchanged.
7. Re-run the six validators/current merge gate/raw default and compare exact
   failure IDs. Do not turn a new S2 failure into a known diagnostic.
8. Review primary Quick Start and short secondary links; respect disclosed Windows
   verifier-environment scope and absence of full dependency-lock reinstall proof.
9. Confirm protected runtime, historical authorities, release and workflows remain
   untouched. Commit/push/PR require later Owner authorization after review.
