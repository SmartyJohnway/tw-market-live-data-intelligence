import hashlib,json,os,pathlib,sys
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run');out=r/'evidence-p4';out.mkdir(exist_ok=True)
paths=json.loads((r/'evidence-host-run4/packaged-runtime-paths.json').read_text(encoding='utf-8'));bundle=pathlib.Path(paths['bundle'])
sys.path.insert(0,str(bundle/'app'))
os.chdir(bundle/'app')
os.environ.update(TW_MARKET_HOME=str(r/'installations/p4-source-v2'),TEMP=str(r/'temp'),TMP=str(r/'temp'),PYTHONDONTWRITEBYTECODE='1')
import runpy
runpy.run_path(str(r/'host_guard.py'),run_name='_acceptance_guard')
from scripts.tw_market_installation import initialize_installation,resolve_installation,_settings
from scripts.tw_market_l2_adapter import DeclaredInstallationMember,installation_backup_plan,A1_COMPATIBILITY_CONTRACT
from server.services.unified_backup import A1_SETTINGS_BINDING,create_backup,verify_backup
from server.services.unified_restore import CompatibilityAttestation,restore_backup,verify_restored_state
from scripts.m8r_08g_security_master_releases import build_candidate_release,qualify_candidate_release,activate_qualified_release,load_active_identity_service
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(p):return {x.relative_to(p).as_posix():sha(x) for x in p.rglob('*') if x.is_file()}
source=resolve_installation(home=r/'installations/p4-source-v2').require_initialized()
source.settings_path.write_text(json.dumps({'schema_version':1,'service':{'host':'127.0.0.1','port':18454}}),encoding='utf-8')
record={'canonical_target_id':'TWSE:2330','identity':{'security_code':'2330','isin':'TW0002330008'},'classification':{'market':'TWSE','instrument_type':'common_share'},'lifecycle':{'state':'listed','resolution_status':'resolved','basis_event_ids':[],'events':[]},'execution_eligibility':{'status':'allowed','reason_codes':[]}}
prov={'source_type':'test','snapshot_id':'a5-offline-accepted-fixture','source_content_hashes':{'fixture':'a'*64},'producer_skill':{'name':'test','skill_version':'1','skill_contract_hash':'b'*64}}
rid='security-master-20261023T000000Z'
build_candidate_release(root=source.security_master_root,release_id=rid,records=[record],source_provenance=prov)
q,report=qualify_candidate_release(root=source.security_master_root,release_id=rid);assert q is not None and report['status']=='PASS'
activate_qualified_release(root=source.security_master_root,release_id=rid)
identity,*_=load_active_identity_service(root=source.security_master_root)
store=PersistentWatchlistStore(root=source.watchlist_root,identity_service=identity,security_master_root=source.security_master_root)
preview=store.preview({'schema_version':'persistent_watchlist_mutation_command.v1','command_type':'create_watchlist','actor_source':'human','name':'A5 portable acceptance'})
watchlist=store.commit(preview_id=preview['preview_id'],preview_hash=preview['content_sha256'],confirmed=True)['watchlist']
assert store.verify_integrity()['status']=='PASS'
members=[DeclaredInstallationMember('preferences','settings','settings.json','user_product_settings',A1_SETTINGS_BINDING,sha(source.settings_path))]
sm_paths=['active.json']+[f'releases/{rid}/{name}' for name in ['index.json','qualification.json','manifest.json','release.json']]
for i,rel in enumerate(sm_paths):
    family='security_master_active_release_pointer' if rel=='active.json' else 'security_master_release_history_and_rollback_artifacts'
    members.append(DeclaredInstallationMember('sm-'+str(i),'security_master',rel,family,'qualified-sm-release-v1',sha(source.security_master_root/rel)))
members.append(DeclaredInstallationMember('watchlists','watchlists','watchlists.sqlite3','persistent_watchlists_and_revision_database','watchlists-schema-v1',None,'sqlite'))
seed=json.loads((r/'governed-fixture-members.json').read_text(encoding='utf-8'))
for i,row in enumerate(seed['members']):members.append(DeclaredInstallationMember('governed-'+str(i),'governed',row['relative_path'],row['family'],'accepted-mode-c-fixture-v1',sha(source.governed_root/row['relative_path'])))
dest=initialize_installation(home=r/'installations/p4-destination')
dest_before=inventory(dest.home);source_before=inventory(source.home)
outcomes={}
for tier in ['CORE','FULL_GOVERNED']:
    plan=installation_backup_plan(source,members=tuple(members),backup_tier=tier,max_total_bytes=20_000_000)
    backup=r/('p4-backup-'+tier);create_backup(plan,destination=backup,backup_id='a5-'+tier,created_at='2026-10-23T00:00:00Z')
    verification=verify_backup(backup,max_total_bytes=20_000_000)
    manifest=json.loads((backup/'backup-manifest.json').read_text(encoding='utf-8'))
    versions={row['logical_member_id']:'1' for row in manifest['members'] if row['artifact_family'] in {'user_product_settings','security_master_active_release_pointer','security_master_release_history_and_rollback_artifacts','persistent_watchlists_and_revision_database'}}
    att=CompatibilityAttestation(manifest['manifest_integrity']['sha256'],versions)
    restored=r/('p4-restored-'+tier)
    result=restore_backup(backup_path=backup,destination=restored,compatibility=att,contract=A1_COMPATIBILITY_CONTRACT,forbidden_roots=[source.home,dest.home,bundle],max_total_bytes=20_000_000,max_member_count=100,restore_id='a5-'+tier,created_at='2026-10-23T00:00:00Z')
    assert result['status']=='RESTORED_STATE_VERIFIED'
    verify_restored_state(backup_path=backup,restored_path=restored,compatibility=att,contract=A1_COMPATIBILITY_CONTRACT,max_total_bytes=20_000_000,max_member_count=100)
    before_use=inventory(restored)
    restored_identity,*_=load_active_identity_service(root=restored/'state/security-master')
    restored_store=PersistentWatchlistStore(root=restored/'state/watchlists',identity_service=restored_identity,security_master_root=restored/'state/security-master')
    assert restored_store.get_watchlist(watchlist['watchlist_id'])['name']==watchlist['name']
    assert restored_store.verify_integrity()['status']=='PASS'
    preferences=_settings(restored/'config/settings.json');assert preferences[:2]==('127.0.0.1',18454)
    assert inventory(restored)==before_use
    if tier=='FULL_GOVERNED':
        from server.services import unified_mode_c
        unified_mode_c.CONTROL_ROOT=restored/'state/governed/fixture-input/control'
        read=unified_mode_c.build_mode_c_result_package({'control_package_id':seed['package_id']})
        assert read['materialization']=='existing_verified' and read['external_market_network_executed'] is False
        assert inventory(restored)==before_use
    assert inventory(dest.home)==dest_before and inventory(source.home)==source_before
    outcomes[tier]={'status':'PASS','manifest':manifest,'restore':result,'verification':verification,'restored_hashes':before_use,'explicit_use':'existing SM loader, Watchlist reader, v1 settings parser; FULL_GOVERNED READ_EXISTING only','destination_identity_preserved':True,'isolated_not_activated':True}
result={'status':'PASS_PENDING_DESTINATION_LIFECYCLE','source_installation_id':source.installation_id,'destination_installation_id':dest.installation_id,'destination_metadata_sha256':sha(dest.installation_metadata_path),'source_id_provenance_only':source.installation_id!=dest.installation_id,'tiers':outcomes,'provider_attempts':0,'restore_authority':'canonical L2 only','destination_home':str(dest.home),'portable_service_host':'127.0.0.1','portable_service_port':18454}
(out/'p4_state_portability.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(result['status'])
