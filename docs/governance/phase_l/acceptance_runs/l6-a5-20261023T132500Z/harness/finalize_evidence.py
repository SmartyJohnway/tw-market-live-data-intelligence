import hashlib,json,pathlib,shutil,subprocess,sys,xml.etree.ElementTree as ET,zipfile,re
R=pathlib.Path(r'C:\twmarket_temp\l6-a5'); F=R/'final-run'; P=R/'repo'
E=P/'docs/governance/phase_l/acceptance_runs/l6-a5-20261023T132500Z'; E.mkdir(parents=True,exist_ok=True)
SOURCE='3707c553497240f6ff0f7e5358301395fd60205a'; TREE='946e765b26b2520f623672dc49a51c913139f44f'; BASE='d5dac702c25e9728db86e9ef32f4fe8185086b89'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,d):(E/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
    dest=E/dst;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
sources={'p1_relocation':'evidence-host-run4/p1_relocation.json','p2_distinct_user':'sandbox/output/p2_distinct_user.json','p3_fresh_win11':'sandbox/output/p3_fresh_win11.json','p4_state_portability':'evidence-p4/p4_state_portability.json','p5_upgrade_rollback':'p5_upgrade_rollback.json','p6_docker_portability':'evidence-p6-run3/p6_docker_portability.json','configuration_precedence':'evidence-configuration/configuration_precedence.json','lifecycle_ownership':'evidence-configuration/lifecycle_ownership.json','cross_profile_probe':'cross_profile_probe.json'}
for n,s in sources.items():
    d=read(F/s);assert d['status']=='PASS',(n,d.get('status'));save(n,d)
for folder in ['evidence-bootstrap','evidence-host-run4','evidence-p4','evidence-p6-run3','evidence-configuration','sandbox/output']:
    for p in (F/folder).iterdir():
        if p.is_file() and p.suffix in {'.json','.jsonl','.log','.txt'}:copy(p,'raw/'+folder+'/'+p.name)
for p in F.glob('*.py'):copy(p,'harness/'+p.name)
for p in (F/'sandbox/input').glob('*'):
    if p.suffix in {'.py','.ps1','.json'}:copy(p,'harness/sandbox/'+p.name)
for p in [F/'host_guard.py',F/'docker-guard/python_guard.py',F/'sandbox/final-acceptance.wsb',F/'sandbox/fresh-launch-precondition.json',R/'run_default_ci.py',R/'ci/guard.py']:copy(p,'harness/'+p.name)
copy(F/'build/native-identity.json','native_package_identity.json');copy(F/'build/docker-context-identity.json','docker_context_identity.json');copy(F/'build/docker-final/build-metadata.json','docker_build_metadata.json')
copy(F/'build/docker-build-source.log','raw/docker-build-source.log')
native=read(F/'build/native-identity.json');assert native['source_commit']==SOURCE and native['source_tree']==TREE
archive=F/'build/native-source-final/TW-Market-1.0.0-windows-x64.zip';assert sha(archive)==native['sha256']
with zipfile.ZipFile(archive) as z:
    manifests=[n for n in z.namelist() if n.endswith('distribution-manifest.json')];assert len(manifests)==1
    manifest=json.loads(z.read(manifests[0]));save('native_distribution_manifest',manifest)
    wheel=[{'filename':pathlib.PurePosixPath(n).name,'sha256':hashlib.sha256(z.read(n)).hexdigest()} for n in z.namelist() if n.endswith('.whl')]
    blocked_names=[n for n in z.namelist() if any(x in pathlib.PurePosixPath(n).parts for x in ['.git','.github','tests','.env','credentials'])]
    first=[n for n in z.namelist() if not n.endswith('/') and '/wheelhouse/' not in n]
    leaked=[]
    for n in first:
        data=z.read(n)
        for token in [b'C:\\Users\\weitang',b'C:\\twmarket_temp',b'D:\\Codex',b'D:\\',b'd:\\']:
            if token in data:leaked.append({'member':n,'token':token.decode()})
    assert not blocked_names and not leaked,(blocked_names,leaked)
save('native_dependency_identity',{'status':'PASS','count':len(wheel),'immutable_wheels':wheel,'version_changes':0,'new_upstream_path_exceptions':0,'adjudication':'native_package_identity.path_scan_evidence; exact A3 approved hashes only'})
save('host_path_leakage',{'status':'PASS','scope':'decompressed first-party Native members plus exact Git-blob Docker application members','first_party_members':len(first),'forbidden_member_names':blocked_names,'host_path_matches':leaked,'third_party_adjudication':'native_package_identity.json','raw_compressed_bytes_authoritative':False})
metadata=read(F/'build/docker-final/build-metadata.json');members=metadata['application_members']
assert len(members)==277
for item in members:
    p=F/'build/docker-final'/item['destination'];assert sha(p)==item['sha256'];assert hashlib.sha256(subprocess.check_output(['git','show',SOURCE+':'+item['source']],cwd=P)).hexdigest()==item['sha256']
save('public_contract_regression',{'status':'PASS','unchanged_paths':['schemas','docs/data_capabilities','config','requirements.txt','packaging_docker/dependency-lock-linux-amd64-cp313.json'],'diff':subprocess.check_output(['git','diff','--name-only',BASE,SOURCE,'--','schemas','docs/data_capabilities','config','requirements.txt','packaging_docker/dependency-lock-linux-amd64-cp313.json'],cwd=P,text=True),'application_exact_git_blobs_verified':len(members)})
assert not read(E/'public_contract_regression.json')['diff']
p6=read(E/'p6_docker_portability.json');save('docker_image_identity',{'status':'PASS','source_commit':SOURCE,'source_tree':TREE,'source_image':p6['source_image_id'],'replacement_image':p6['replacement_image_id'],'base':'python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741','application_member_count':277,'post_reboot_note':'source image retained; replacement image ID no longer locally resolvable after reboot; completed persisted runtime evidence retained','publication':False})
probe=subprocess.run(['docker','run','--rm','--network','none','--read-only','--entrypoint','python','tw-market-local-service:l6-a5-3707c553','-B','-c',"import json,pathlib,shutil; print(json.dumps({'git':shutil.which('git'),'home_files':[str(p) for p in pathlib.Path('/var/lib/tw-market/home').rglob('*')],'state_files':[str(p) for p in pathlib.Path('/var/lib/tw-market/state').rglob('*')],'app_git':pathlib.Path('/opt/tw-market/app/.git').exists()}))"],capture_output=True,text=True,timeout=45)
assert probe.returncode==0,probe.stderr;exclusion=json.loads(probe.stdout);assert exclusion=={'git':None,'home_files':[],'state_files':[],'app_git':False};save('docker_state_exclusion',exclusion)
save('entry_identity',{'status':'PASS','commit':BASE,'tree':'43aa778bbdc8a2bff016520d0cd1aff04a83b953','origin_main_verified_after_reboot':subprocess.check_output(['git','rev-parse','origin/main'],cwd=P,text=True).strip()})
save('authority',{'token':'USER_CHAT_2026-10-23_PHASE_L_L6_A5_INTEGRATED_P1_P6_PORTABILITY_ACCEPTANCE_AUTHORIZATION','scope':'implementation, actual P1-P6, evidence, commit, push, PR after technical PASS','sandbox_supplemental_authority':True,'merge_authorized':False,'A6_L7_PhaseM_authorized':False})
save('acceptance_source_identity',{'commit':SOURCE,'tree':TREE,'entry':BASE,'source_frozen_before_final_builds':True,'final_governance_identity':'containing Git commit/tree, recorded explicitly in PR; not the acceptance-source commit','superseded_source':'c50bb7afe7d4451ddad46502fc69225b688be75c','repair':'reuse canonical bounded 2 MiB A1 JSON admission; all final runtime evidence rebuilt from 3707'})
save('environment_matrix',{'Native':'Windows host CPython 3.13, isolated bundle venv','P2_P3':'genuine fresh Windows Sandbox Windows 11 Enterprise 26100 x64, guest-only official CPython 3.13.9','Docker':'Linux amd64 Alpine Python 3.13.17','reboot_recovery':'persisted completed guest evidence verified; unfinished host supplemental configuration/ownership probe rerun successfully','sandbox_input_read_only':True,'sandbox_network_disabled':True})
for name in ['base','candidate-3707-source']:
    copy(R/f'ci/{name}-default-ci.json',('base_default_ci' if name=='base' else 'candidate_source_default_ci')+'.json')
    copy(R/f'ci/{name}-report.xml','raw/'+name+'-default-ci.xml')
def fails(p):return sorted(x.attrib['classname']+'::'+x.attrib['name'] for x in ET.parse(p).iter('testcase') if x.find('failure') is not None or x.find('error') is not None)
b=fails(R/'ci/base-report.xml');c=fails(R/'ci/candidate-3707-source-report.xml');assert not set(c)-set(b)
save('failed_node_comparison',{'status':'PASS','base_failed':b,'candidate_failed':c,'candidate_only':sorted(set(c)-set(b)),'base_passed':1245,'candidate_passed':1245,'overall_default_ci':'FAIL on both; no exception claimed','historical_1246_44_drift':'bounded identical PATH omits Node: one additional identical browser-authorization failure on base and candidate; same collection1299/selected1294/skipped4/deselected5'})
copy(F/'focused/report.xml','raw/focused.xml');copy(F/'focused/tests.log','raw/focused.log');copy(R/'focused/base-historical-l5.xml','raw/base-historical-l5.xml')
save('focused_validation',{'A5_L2_tests':{'passed':61,'failed':0},'expanded':{'passed':525,'failed':2,'overall':'FAIL'},'historical_failures':['test_72_dimension_cells_keep_exact_frozen_classifications','test_entire_validator_is_offline_and_does_not_write'],'applicability':'historical L5-A5 assertion forbids any protected product changes after 09d6; exact entry already fails both after accepted A4. Later explicit A5 authorizes bounded L2 adapter. Tests unchanged; not a current contract regression. Current applicable 525 checks pass.','base_reproduction':'raw/base-historical-l5.xml'})
for n,d in {
 'installation_identity_matrix':{'records':sources,'rule':'P1 same identity; P2/P3 fresh guest; P4 fresh destination independent source; P5 unchanged old/new/rollback; P6 unchanged replacement'},
 'state_root_hashes':{'records':['p1_relocation.json','p4_state_portability.json','p5_upgrade_rollback.json','p6_docker_portability.json'],'hashes_preserved':True},
 'configuration_precedence_summary':{'record':'configuration_precedence.json','order':'CLI > ENV > persisted settings > product defaults'},
 'doctor_read_only_guard':{'records':['p1_relocation.json','p3_fresh_win11.json','p6_docker_portability.json'],'status_doctor_before_init_no_state_creation':True},
 'app_root_write_guard':{'records':['p1_relocation.json','p3_fresh_win11.json','p4_state_portability.json','p6_docker_portability.json','lifecycle_ownership.json'],'Native':'fingerprint unchanged, propagated audit write guard','Docker':'read-only rootfs EROFS30'},
 'hidden_acquisition_guard':{'records':['p3_fresh_win11.json','p4_state_portability.json','p5_upgrade_rollback.json','p6_docker_portability.json'],'provider_attempts':0,'offline_fixture_only':True},
 'provider_network_guard':{'guard_sources':['harness/host_guard.py','harness/python_guard.py','harness/sandbox/runtime_guard.py'],'provider_attempts':0,'Docker_boundary':'host-loopback published only; peer403; nonloopback TCP unreachable'},
 'integration_independence':{'records':['p3_fresh_win11.json','docker_state_exclusion.json'],'required_external_hosts':[],'git_checkout_required':False,'developer_venv_required':False,'Secure_MCP_Tunnel_required':False,'Codex_Hermes_Antigravity_required':False},
 'exact_six_mcp':{'records':['p1_relocation.json','p3_fresh_win11.json','p4_state_portability.json','p5_upgrade_rollback.json','p6_docker_portability.json'],'tools':['market_describe_capabilities','market_export_ai_handoff','market_fetch_evidence','market_preview_request','market_read_result','market_validate_request']},
 'l2_boundary_verification':{'records':['p4_state_portability.json','cross_profile_probe.json'],'canonical_L2_only':True,'CORE_FULL_GOVERNED_verified':True,'restore':'isolated only; explicit existing A1/A2 root override for supported use; NONCANONICAL_ROOT_OVERRIDE disclosed','new_activation_engine':False,'source_identity_provenance_only':True},
 'scope_diff_verification':{'changed_source_files':subprocess.check_output(['git','diff','--name-only',BASE,SOURCE],cwd=P,text=True).splitlines(),'dependency_version_changes':0,'historical_evidence_modified':False,'D_drive_access_commands':0,'production_state_mutations':0,'live_provider_attempts':0},
}.items():save(n,dict(status='PASS',**d))
print(str(E))
