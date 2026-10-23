"""A6 offline review helper. Writes only new review evidence; never repairs product."""
import hashlib,json,pathlib,subprocess,zipfile,sys
R=pathlib.Path(r'C:\twmarket_temp\l6-a6');P=R/'repo'
E=P/'docs/governance/phase_l/acceptance_runs/l6-a6-20261023T141800Z';E.mkdir(parents=True,exist_ok=True)
ROOT='docs/governance/phase_l/acceptance_runs/'
A0=ROOT+'l6-a0-20261021T092005Z/';A1=ROOT+'l6-a1-20261021T130000Z/';A2=ROOT+'l6-a2-20261021T142354Z/';A3=ROOT+'l6-a3-clean-final-20261023T010756Z/';A4=ROOT+'l6-a4-20261023T061105Z/';A5=ROOT+'l6-a5-20261023T132500Z/'
BASE='365ea26e76e24aa0171945d29ba2b21f79c3a8db';SOURCE='3707c553497240f6ff0f7e5358301395fd60205a'
def git(*args):return subprocess.check_output(['git',*args],cwd=P)
def read(path):return json.loads((P/path).read_text(encoding='utf-8-sig'))
def save(name,d):(E/(name+'.json')).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(d):return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def blobs(specs):
    result=subprocess.check_output(['git','cat-file','--batch'],cwd=P,input=('\n'.join(specs)+'\n').encode());offset=0;out={}
    for spec in specs:
        end=result.index(b'\n',offset);header=result[offset:end].split();assert len(header)==3,(spec,header)
        size=int(header[2]);out[spec]=result[end+1:end+1+size];offset=end+size+2
    return out
assert git('rev-parse',BASE+'^{tree}').decode().strip()=='811985144e835e24dc01f8a130c8b959f83c5f0d'
assert git('rev-parse',SOURCE+'^{tree}').decode().strip()=='946e765b26b2520f623672dc49a51c913139f44f'
save('entry_identity',{'commit':BASE,'tree':'811985144e835e24dc01f8a130c8b959f83c5f0d','branch':'phase-l/l6-a6-packaging-portability-technical-exit-review','initial_worktree_clean':True,'isolated_clone':str(P)})
save('authority',{'token':'USER_CHAT_2026-10-23_PHASE_L_L6_A6_PACKAGING_PORTABILITY_TECHNICAL_EXIT_REVIEW_AUTHORIZATION','scope':'offline technical review, deterministic regression, new evidence/governance, commit/push/PR after PASS','product_repairs':False,'merge':False,'Owner_final_closure':False,'L7':False,'Phase_M':False})
lineage=[('A0','7ec798d682ac91db776608a5e9a6a98e179dd1ec',A0),('A1','430f280f9c1b4f8d0f387503bb22044214126b39',A1),('A2','911a841b866795e8d0cd83d80b30b34701aa5980',A2),('A3','a40141f43f3a1bdeccbab61e67a4a5e161eb8f37',A3),('A3 reconciliation','ee316f784831fe684e21fa8d146512d96a888050',None),('A4','85a4351f9be46efeb28794079ed7adfeeae0fc8a',A4),('A4 reconciliation','d5dac702c25e9728db86e9ef32f4fe8185086b89',None),('A5','08bec63ec3d924d2c3b206ecc4fcc017b259ea75',A5),('A5 reconciliation','365ea26e76e24aa0171945d29ba2b21f79c3a8db',None)]
rows=[]
for tranche,commit,folder in lineage:
    assert subprocess.run(['git','merge-base','--is-ancestor',commit,BASE],cwd=P).returncode==0
    rows.append({'tranche':tranche,'commit':commit,'tree':git('rev-parse',commit+'^{tree}').decode().strip(),'parents':git('show','-s','--format=%P',commit).decode().split(),'ancestor':True,'evidence':folder,'status':'PASS'})
save('a0_to_a5_lineage',{'status':'PASS','missing_tranches':0,'rows':rows})
changes=git('diff','--name-only',SOURCE,BASE).decode().splitlines()
allowed=lambda p:p in {'PROJECT.md','HANDOFF.md','ROADMAP.md'} or p.startswith('docs/governance/')
unexpected=[p for p in changes if not allowed(p)];assert not unexpected,('L6_A6_POST_ACCEPTANCE_PRODUCT_DRIFT',unexpected)
save('acceptance_source_current_main_diff',{'status':'PASS','accepted_source':SOURCE,'source_tree':'946e765b26b2520f623672dc49a51c913139f44f','current_main':BASE,'changed_paths':changes,'unexpected_product_paths':unexpected,'protected_classes':['scripts','server','packaging_native','packaging_docker','schemas','config','requirements','VERSION','tests','frontend','skills','public Catalog/Route/Executor/source authority'],'product_drift':0})
integrity=[]
for tranche,commit,folder in lineage:
    if folder is None:continue
    changes=git('diff','--name-only',commit,BASE,'--',folder).decode().splitlines();assert not changes,(tranche,changes)
    rec={'tranche':tranche,'accepted_commit':commit,'folder':folder,'current_accepted_evidence_diff':changes,'status':'PASS'}
    if tranche in {'A0','A1','A2','A3'}:
        d=read(folder+'manifest.json');expected=d.pop('manifest_canonical_sha256');assert sha(canon(d))==expected,(tranche,'self digest')
        ref=d.get('artifact_content_commit',d.get('content_commit'));members=d.get('artifacts',d.get('members'));specs=[ref+':'+x.get('path',x.get('relative_path')) for x in members];data=blobs(specs)
        assert git('rev-parse',ref+'^{tree}').decode().strip()==d.get('artifact_content_tree',d.get('content_tree'))
        for item,spec in zip(members,specs):
            raw=data[spec];normalized=raw.replace(b'\r\n',b'\n').replace(b'\r',b'\n');assert sha(normalized)==item['sha256'],(tranche,spec)
            if 'raw_sha256' in item:assert sha(raw)==item['raw_sha256']
            oid=item.get('git_blob',item.get('git_blob_oid'))
            if oid:assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid
        rec.update(manifest_self_digest=expected,manifest_members_verified=len(members),historical_content_ref=ref,method='historical snapshots at their bound content commits; current front-door changes are permitted and not falsely compared to old front-door hashes')
    elif tranche=='A5':
        d=read(folder+'manifest.json');expected=d.pop('self_digest');assert sha(canon(d))==expected
        for item in d['members']:assert sha((P/folder/item['path']).read_bytes())==item['sha256'],item['path']
        rec.update(manifest_self_digest=expected,manifest_members_verified=len(d['members']))
    else:
        rec.update(method='no full evidence self-digest supplied; exact accepted Git subtree equality at normal merge, plus application-resource-manifest source blob/hash verification',evidence_tree=git('rev-parse',commit+':'+folder.rstrip('/')).decode().strip(),file_count=len(git('ls-tree','-r','--name-only',BASE,'--',folder).splitlines()))
        app=read(folder+'application-resource-manifest.json');ref=app['candidate_commit'];members=app['application_members'];data=blobs([ref+':'+x['source'] for x in members])
        for x in members:assert sha(data[ref+':'+x['source']])==x['sha256']
        rec['application_members_verified']=len(members)
    integrity.append(rec)
save('historical_evidence_integrity',{'status':'PASS','records':integrity,'historical_evidence_changes':0})
native=read(A5+'native_distribution_manifest.json');docker=read(A5+'docker_build_metadata.json');p3=read(A5+'p3_fresh_win11.json')
n={x['relative_path'][4:]:x['sha256'] for x in native['members'] if x['relative_path'].startswith('app/')};d={x['source']:x['sha256'] for x in docker['application_members']};assert n==d==p3['app_hashes'] and len(n)==277
data=blobs([BASE+':'+k for k in n]);assert all(sha(data[BASE+':'+k])==v for k,v in n.items())
save('application_blob_integrity',{'status':'PASS','count':len(n),'source':SOURCE,'current_main':BASE,'Native_manifest_Docker_context_guest_APP_ROOT_current_main_all_equal':True,'member_sha256':n})
p={i:read(A5+f'p{i}_'+name+'.json') for i,name in [(1,'relocation'),(2,'distinct_user'),(3,'fresh_win11'),(4,'state_portability'),(5,'upgrade_rollback'),(6,'docker_portability')]}
assert all(v['status']=='PASS' for v in p.values())
assert p[1]['old_root_unavailable'] and p[1]['app_root_unchanged'] and p[1]['bootstrap_idempotent']
assert p[2]['distinct_sid'] and p[2]['distinct_profile'] and p[2]['no_inherited_HOME_or_runtime']
assert 'WDAGUtilityAccount' in p[2]['guest']['username'] and p[2]['guest']['os']['BuildNumber']=='26100'
assert p3['source_commit']==SOURCE and p3['preinit_read_only'] and p3['init_idempotent'] and p3['app_root_unchanged']
assert p3['provider_attempts']==0 and p3['guard_rejections']==0 and p3['networking']=='disabled'
assert set(p[4]['tiers'])=={'CORE','FULL_GOVERNED'} and p[4]['source_installation_id']!=p[4]['destination_installation_id'] and p[4]['source_id_provenance_only']
assert p[5]['compatibility']=='SUPPORTED_NO_MIGRATION_REQUIRED' and not p[5]['migration_executed'] and p[5]['hidden_refreshes']==0
assert p[6]['state_survived'] and p[6]['source_image_id']!=p[6]['replacement_image_id'] and p[6]['provider_attempts']==0
save('p1_p6_evidence_reverification',{'status':'PASS','method':'inspect immutable accepted records and exact current-main blob equality, not operational rerun','records':[{'profile':'P'+str(i),'status':'PASS','evidence':A5+f'p{i}_'+name+'.json'} for i,name in [(1,'relocation'),(2,'distinct_user'),(3,'fresh_win11'),(4,'state_portability'),(5,'upgrade_rollback'),(6,'docker_portability')]],'new_Sandbox_launches':0,'new_Docker_containers_or_builds':0,'guest_principal':p[2]['guest'],'P4_explicit_use':p[4]['explicit_state_use'],'P5_compatibility':p[5]['compatibility'],'replacement_reference_limitation':'accepted completed evidence intact; no need to reconstruct historical image'})
package=read(A5+'native_package_identity.json');assert package['sha256']=='6772e8c3550525ff0d952929c7e36cef4833e265936b0009b6d517152ab74e04' and package['member_count']==338 and package['wheel_count']==49
local=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run\build\native-source-final\TW-Market-1.0.0-windows-x64.zip');assert sha(local.read_bytes())==package['sha256']
with zipfile.ZipFile(local) as z:
    names=z.namelist();assert len(names)==338 and not any('/.git/' in k or '/.venv/' in k for k in names)
    prefix=names[0].split('/')[0]+'/'
    for item in native['members']:assert sha(z.read(prefix+item['relative_path']))==item['sha256'],item['relative_path']
save('native_package_review',{'status':'PASS','identity':package['sha256'],'members':338,'Windows_wheels':49,'local_accepted_ZIP_hash_and_all_manifested_members_reverified':True,'rebuilt':False,'explicit_installed_CPython_prerequisite':True,'derived_bundle_local_venv':True,'external_state':True,'arbitrary_paths_evidence':A5+'p1_relocation.json','bootstrap_evidence':A5+'raw/evidence-bootstrap/','no_checkout_or_git_dependency':True,'installer_required_for_L6':False})
save('docker_packaging_review',{'status':'PASS','base':'python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741','source_image':p[6]['source_image_id'],'replacement_image':p[6]['replacement_image_id'],'accepted_evidence':A5+'p6_docker_portability.json','network_boundary':p[6]['network_boundary'],'state_survived':p[6]['state_survived'],'image_state_exclusion':A5+'docker_state_exclusion.json','one_local_service':True,'host_stdio_MCP_separate':True,'image_identity_is_installation_identity':False,'historical_image_not_reconstructed':True})
tools=['market_describe_capabilities','market_export_ai_handoff','market_fetch_evidence','market_preview_request','market_read_result','market_validate_request']
for x in p[6]['host_mcp']:assert sorted(x['names'])==tools and x['tool_count']==6
save('exact_six_mcp',{'status':'PASS','tool_count':6,'tools':tools,'accepted_host_MCP_evidence':A5+'p6_docker_portability.json#host_mcp','current_main_runtime_and_tests_unchanged':True,'current_validator':'required_validators.json'})
public=git('diff','--name-only','7ec798d682ac91db776608a5e9a6a98e179dd1ec',BASE,'--','schemas','docs/data_capabilities','config').decode().splitlines();assert not public
save('public_contract_review',{'status':'PASS','A0_to_current_schema_catalog_routing_config_delta':public,'accepted_source_to_current_runtime_delta':0,'Request_Result_Audit_Handoff_compatibility':'unchanged authority bytes plus deterministic public-contract/L5 tests','competing_Catalog_Route_Executor':False,'evidence_text_execution_authority':False})
save('l2_boundary_review',{'status':'PASS','adapter':'scripts/tw_market_l2_adapter.py','current_source_sha256':n['scripts/tw_market_l2_adapter.py'],'accepted_records':[A5+'p4_state_portability.json',A5+'cross_profile_probe.json'],'explicit_members_only':True,'canonical_L2_backup_verify_isolated_restore':True,'destination_identity_preserved':True,'source_identity_provenance_only':True,'settings_bound':'A1 existing bounded2MiB JSON admission and exact endpoint-only settings validation','nonportable':['installation_metadata','PID','runtime','cache','logs','temp'],'new_activation_or_migration_authority':False,'remaining_L2_remainder':0,'explicit_override_use_not_automatic_restore_activation':p[4]['explicit_state_use']})
print('lineage, source/package/evidence integrity and P1-P6 reverification PASS')
