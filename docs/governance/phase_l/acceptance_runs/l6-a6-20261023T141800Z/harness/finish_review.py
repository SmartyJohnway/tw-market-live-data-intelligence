import pathlib,json,subprocess,shutil,xml.etree.ElementTree as ET,sys,re,hashlib
R=pathlib.Path(r'C:\twmarket_temp\l6-a6');P=R/'repo';REL='docs/governance/phase_l/acceptance_runs/l6-a6-20261023T141800Z';E=P/REL
BASE='365ea26e76e24aa0171945d29ba2b21f79c3a8db';SOURCE='3707c553497240f6ff0f7e5358301395fd60205a'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,d):(E/(n+'.json')).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def failed(p):return sorted(x.attrib['classname'].replace('.','/')+'.py::'+x.attrib['name'] for x in ET.parse(p).iter('testcase') if x.find('failure') is not None or x.find('error') is not None)
stage=sys.argv[1];label='candidate-prefrontdoor' if stage=='pre' else 'candidate-final'
c=read(R/f'ci/{label}-default-ci.json');b=read(R/'ci/base-default-ci.json');bf=failed(R/'ci/base-report.xml');cf=failed(R/f'ci/{label}-report.xml')
assert not set(cf)-set(bf),('L6_A6_CANDIDATE_ONLY_CI_REGRESSION',sorted(set(cf)-set(bf)))
assert (b['selected'],b['collected'])==(c['selected'],c['collected'])
assert len(cf)==c['failed'] and len(bf)==b['failed']
assert all(x['returncode']==0 for x in read(E/'required_validators.json')) and read(E/'compile_static.json')['returncode']==0
save('candidate_default_ci',c);shutil.copyfile(R/f'ci/{label}-report.xml',E/'candidate-default-ci.xml')
save('failed_node_comparison',{'status':'PASS','candidate_stage':label,'base_commit':BASE,'base_failed_node_ids':bf,'candidate_failed_node_ids':cf,'candidate_only_failed_nodes':sorted(set(cf)-set(bf)),'base_only_failed_nodes':sorted(set(bf)-set(cf)),'candidate_only_count':0,'base_counts':{k:b[k] for k in ['passed','failed','skipped','deselected','selected','collected']},'candidate_counts':{k:c[k] for k in ['passed','failed','skipped','deselected','selected','collected']},'overall_base_CI':'FAIL' if bf else 'PASS','overall_candidate_CI':'FAIL' if cf else 'PASS','same_wrapper_and_environment':True,'environment':'same absolute TEMP/TMP/HOME/LOCALAPPDATA/basetemp; explicit parent PYTHONUTF8=1; bounded PATH without Node; prior run directories preserved before reuse','A5_same_environment_failure_set':'a5_current_environment_ci_reconciliation.json'})
m=read(E/'l6_exit_criteria_matrix.json');m['rows'][20].update(status='PASS',current_main_verification='failed_node_comparison.json: same-environment exact base/candidate failed-node comparison; candidate-only=0; A5 failure set reconciliation unchanged');m.update(pass_count=23,pending_count=0,blocked_count=0);assert all(x['status']=='PASS' for x in m['rows']);save('l6_exit_criteria_matrix',m)
review={'technical_disposition':'PHASE_L_L6_EXIT_REVIEW_PASS','L6_status':'TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED','Owner_final_closure':'PENDING','L7':'NOT AUTHORIZED','Phase_M':'NOT AUTHORIZED','merge':'NOT AUTHORIZED','A0_A5_lineage':'PASS','unresolved_A0_findings':0,'unresolved_A1_gaps':0,'exit_criteria_pass':23,'P1_P6':'all accepted actual runs remain valid; current source byte identity reverified','post_acceptance_product_drift':0,'exact_six_MCP':True,'L2_sole_authority':True,'public_contract_changes':0,'historical_evidence_changes':0,'focused_validation':'PASS; actual L6/L2 domain tests within expanded run','expanded_validation':'525 passed/2 unchanged historical L5 scope failures, overallFAIL','default_CI_overall':'FAIL inherited45, candidate-only0','D_drive_access_commands':0,'live_provider_requests':0,'market_acquisition_attempts':0,'Security_Master_live_updates':0,'production_state_mutations':0,'product_runtime_changes':0,'test_semantic_changes':0,'dependency_changes':0,'candidate_identity':'final containing governance commit/tree explicitly recorded in PR; entry and accepted source are separate identities'}
save('final_technical_review',review)
if stage=='pre':
    # No front-door declaration occurs until the preceding technical gates pass.
    current='''## Current L6-A6 technical exit review (2026-10-23)

L6-A0 through L6-A5 are OWNER-ACCEPTED AND MERGED.
L6-A6 technical disposition: `PHASE_L_L6_EXIT_REVIEW_PASS`.
All 23 exit criteria PASS; unresolved A0 findings=0; unresolved A1 gaps=0.
Accepted P1–P6 actual portability evidence remains valid and relevant current
product bytes match A5 source `3707c553497240f6ff0f7e5358301395fd60205a`.
Default CI remains FAIL: base/candidate1245 passed,45 failed,4 skipped,5 deselected;
candidate-only failed nodes=0. Expanded validation remains525 passed/2 historical
L5 scope-assertion failures; neither inherited suite is reported overall PASS.

L6: **TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED**.
Owner final closure: **PENDING**. Phase L is not closed.
Merge/auto-merge, L7, Phase M, release/signing/image publication and installer
implementation remain **NOT AUTHORIZED**. Stop for independent review/Owner action.

Review: `docs/governance/phase_l/PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_2026-10-23.md`.
Evidence: `docs/governance/phase_l/acceptance_runs/l6-a6-20261023T141800Z/`.

'''
    for f in ['PROJECT.md','HANDOFF.md','ROADMAP.md','docs/governance/INDEX.md','docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md']:
        p=P/f;s=p.read_text(encoding='utf-8');s=s.replace('## Current L6-A5 merged state','## Historical L6-A5 merged state')
        if f=='ROADMAP.md':
            s=re.sub(r'^status_reconciled_through:.*$','status_reconciled_through: "2026-10-23: L6-A6 PHASE_L_L6_EXIT_REVIEW_PASS; 23/23 criteria; L6 TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED; Owner final closure pending; L7/Phase M/merge not authorized"',s,flags=re.M);pos=s.index('\n## ')+1
        else:pos=s.index('\n')+1
        s=s[:pos]+'\n'+current+s[pos:];p.write_bytes(s.encode())
    doc='''# L6-A6 — Packaging & Portability Technical Exit Review

Technical disposition: `PHASE_L_L6_EXIT_REVIEW_PASS`.
L6: **TECHNICAL EXIT PASS / NOT YET OWNER-CLOSED**.
Owner final closure: **PENDING**. Phase L is not closed.

Authority: `USER_CHAT_2026-10-23_PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_AUTHORIZATION`.
Exact entry `365ea26e76e24aa0171945d29ba2b21f79c3a8db`, tree
`811985144e835e24dc01f8a130c8b959f83c5f0d` (PR405 reconciliation).
Review-only branch `phase-l/l6-a6-packaging-portability-technical-exit-review`.
Final containing candidate commit/tree are recorded explicitly in the PR;
entry/source/evidence content identities are not substitutes for final identity.

## Exit adjudication

All nine required accepted merge/reconciliation commits are ancestors of the
exact entry. The ledger reconciles all A0 active coupling findings, fifteen
decisions, eleven physical roots, six portability gaps and configuration/SM
findings to their accepted downstream evidence. Unresolved A0 findings=0.
All sixteen A1 gaps have final dispositions, including G07/G16 application
resource distribution under A3/A5 and G15 explicit canonical L2 integration
under A5. Unresolved A1 gaps=0. All **23/23** canonical A0 exit criteria PASS;
each has its own authority, accepted evidence and current-main verification.

Current scripts/server/package definitions/schemas/catalog/routes/executors/
source authority/dependency locks/VERSION/tests/frontend/skills match accepted
A5 source `3707c553497240f6ff0f7e5358301395fd60205a`, tree
`946e765b26b2520f623672dc49a51c913139f44f`. Post-source changes are governance,
evidence and front-door reconciliation only. All 277 exact application hashes
agree across accepted Native manifest, Docker build context, actual Sandbox
APP_ROOT and current canonical Git blobs. No product repair is performed.

P1–P6 retain their independently accepted actual-run PASS. P2 and P3 remain
separate genuine WDAGUtilityAccount/security-profile and fresh Windows11x64
records; neither environment availability nor simulated ENV changes are used as
acceptance. No Sandbox was launched and no Docker image rebuilt/reconstructed.
P4 verifies canonical CORE/FULL_GOVERNED integrity/isolated restore and explicit
supported use via existing root seams, with NONCANONICAL_ROOT_OVERRIDE visible;
destination metadata/identity remains local and source identity provenance only.
P5 is actual accepted older A3 state→new app→rollback,
`SUPPORTED_NO_MIGRATION_REQUIRED`, with no fabricated migration.
P6 complete fresh-volume/replacement evidence remains intact; the missing local
replacement reference after reboot is the disclosed accepted limitation.

Frozen L0 deployment/state/config/lifecycle/upgrade/backup/integration obligations
are satisfied. Native remains primary; Docker is one Local Service packaging
profile with durable mounts and loopback-only host ingress. Host stdio MCP stays
outside the container and exposes exactly six tools. L2 remains sole canonical
backup/verify/isolated-restore/migration authority; explicit-member admission is
bounded and never discovers arbitrary state or adopts source PID/path identity.
Request/Result/Audit/Handoff and Catalog/Route/Executor/source/authorization
authorities are unchanged. The Win11 prospective policy is applied without
rewriting historical L0-D03 or requiring Windows10 release-blocking acceptance.

## Artifact and historical integrity

Accepted Native `TW-Market-1.0.0-windows-x64.zip`: SHA-256
`6772e8c3550525ff0d952929c7e36cef4833e265936b0009b6d517152ab74e04`,
338 members/49 pinned Windows wheels. The retained original ZIP and every
manifested member were rehashed; no replacement ZIP was built.
Base Docker `python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741`;
source image `sha256:2b25c1e54879b0761d3c0a3591236cb2a1f820c1530fee25f643ec93cf962675`;
replacement `sha256:98bafa33505e0d5f4c088e58949e388768b21b0a0741f4da5649eff539f91323`.

A0/A1/A2/A3 manifests and historical member hashes are verified at their bound
content commits, distinguishing old front-door snapshots from current prose.
A5 canonical self-digest and193 members are verified. A4 provides no full
evidence self-digest: its entire accepted Git evidence subtree is unchanged and
all273 application-resource manifest hashes verify at its bound source. All
accepted A0–A5 evidence subtrees remain byte-identical to their normal merges.
No historical evidence is rewritten.

## Deterministic validation

The actual expanded applicability run remains **525 passed/2 failed**, overall
FAIL. Exact failures are preserved:

- `tests/unit/test_l5_a5_existing_family_conformance.py::test_72_dimension_cells_keep_exact_frozen_classifications`
- `tests/unit/test_l5_a5_existing_family_conformance.py::test_entire_validator_is_offline_and_does_not_write`

They retain the same historical protected-product-no-change assertion since09d6,
including already accepted A4/A5 files. A6 section18 explicitly preserves their
historical scope classification; tests are not edited, deleted or relabeled.
The L6/L2 domain view of this same actual run has zero failures; its exact node
list/count is in focused_validation.json. Other L4/L5/SM/public-contract checks
are retained in the full expanded report, rather than suppressed.

Default CI on exact entry and final review candidate uses the same bounded
wrapper, explicit UTF-8 parent startup, absolute TEMP/TMP/HOME/LOCALAPPDATA,
test selection and PATH. Both remain **1245 passed/45 failed/4 skipped/5 deselected**,
selected1294/collected1299. Exact candidate-only failed nodes=0. Current entry's
failure set also equals accepted A5; no unexplained environment drift and no
claim that inherited FAIL is PASS. Required validators, compile/static and Git
whitespace/scope checks pass. A final candidate run after front-door updates is
retained separately from the initial technical-decision run.

## Retained limits and stop boundary

See retained_nonblocking_limitations.json for individual authority/revisit rules:
inherited CI/L5 failures; missing local historical replacement image reference;
explicit supported installed CPython prerequisite; ZIP rather than installer;
no registry publication/signing/release; Win11-only prospective Tier1; no live
provider certification; explicit separate SM refresh; P4 isolated restore and
explicit root selection rather than a new activation authority.

L7 retains release version/adjudication, CI release automation, signing,
release manifests/publication, registry, SDK compatibility-range decisions and
bounded live release acceptance. None is performed. No provider/live request,
market acquisition, SM live update, production-state mutation or D-drive access
command occurred (all0). No unrelated Docker resource was touched.

Evidence: [A6 review run](acceptance_runs/l6-a6-20261023T141800Z/).
Canonical manifest hashes exact committed review-member bytes and its own
compact sorted UTF-8 JSON excluding self_digest. Text copies are normalized to
LF/trailing-space removal with pre-normalization copy hashes retained; original
logs stay in bounded A6 workspace. No ZIP/wheel/venv/installer/image export is committed.

After PR opening, stop for independent review/Owner action. **Merge/auto-merge,
L7, Phase M, release/signing/publication and installer work remain NOT AUTHORIZED.**
A6 technical PASS is not Owner final closure of L6 or Phase L.
'''
    (P/'docs/governance/phase_l/PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_2026-10-23.md').write_bytes(doc.encode())
print('A6 technical gates PASS; '+('front doors updated after PASS' if stage=='pre' else 'final candidate comparison PASS'))
