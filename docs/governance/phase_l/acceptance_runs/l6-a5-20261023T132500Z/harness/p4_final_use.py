"""Verified L2 backup -> fresh destination -> isolated restore -> explicit use."""
import hashlib,json,os,pathlib,sys
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run');sys.path.insert(0,str(r));import host_acceptance as h
os.environ['TW_MARKET_HOME']=str(r/'installations/p4-verified-destination')
h.OUT=r/'evidence-p4/final-use-lifecycle';h.OUT.mkdir(exist_ok=True)
paths=json.loads((r/'evidence-host-run4/packaged-runtime-paths.json').read_text(encoding='utf-8'));bundle=pathlib.Path(paths['bundle'])
sys.path.insert(0,str(bundle/'app'));os.chdir(bundle/'app')
from scripts.tw_market_installation import initialize_installation
from scripts.tw_market_l2_adapter import A1_COMPATIBILITY_CONTRACT
from server.services.unified_backup import verify_backup
from server.services.unified_restore import CompatibilityAttestation,restore_backup,verify_restored_state
from scripts.m8r_08g_security_master_releases import load_active_identity_service
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore
for tier in ['CORE','FULL_GOVERNED']:verify_backup(r/('p4-backup-'+tier),max_total_bytes=20_000_000)
dest=initialize_installation(home=r/'installations/p4-verified-destination')
metadata=dest.installation_metadata_path.read_bytes();settings=dest.settings_path.read_bytes();state_before=h.inventory(dest.state_root)
p=r/'evidence-p4/p4_state_portability.json';d=json.loads(p.read_text(encoding='utf-8'))
for tier in ['CORE','FULL_GOVERNED']:
    backup=r/('p4-backup-'+tier);manifest=json.loads((backup/'backup-manifest.json').read_text(encoding='utf-8'))
    facts={row['logical_member_id']:'1' for row in manifest['members'] if row['artifact_family'] in {'user_product_settings','security_master_active_release_pointer','security_master_release_history_and_rollback_artifacts','persistent_watchlists_and_revision_database'}}
    att=CompatibilityAttestation(manifest['manifest_integrity']['sha256'],facts);restored=r/('p4-verified-restored-'+tier)
    result=restore_backup(backup_path=backup,destination=restored,compatibility=att,contract=A1_COMPATIBILITY_CONTRACT,forbidden_roots=[dest.home,bundle,r/'installations/p4-source-v2'],max_total_bytes=20_000_000,max_member_count=100,restore_id='a5-final-'+tier,created_at='2026-10-23T00:00:00Z')
    assert result['status']=='RESTORED_STATE_VERIFIED'
    verify_restored_state(backup_path=backup,restored_path=restored,compatibility=att,contract=A1_COMPATIBILITY_CONTRACT,max_total_bytes=20_000_000,max_member_count=100)
    identity,*_=load_active_identity_service(root=restored/'state/security-master')
    store=PersistentWatchlistStore(root=restored/'state/watchlists',identity_service=identity,security_master_root=restored/'state/security-master')
    assert store.verify_integrity()['status']=='PASS' and store.list_watchlists()['watchlists']
    d['tiers'][tier].update(restore=result,restored_hashes=h.inventory(restored),destination_identity_preserved=True)
restored=r/'p4-verified-restored-FULL_GOVERNED';before=h.inventory(restored)
prefs=json.loads((restored/'config/settings.json').read_text(encoding='utf-8'))['service']
h.env.update(TW_MARKET_SECURITY_MASTER_ROOT=str(restored/'state/security-master'),TW_MARKET_WATCHLIST_ROOT=str(restored/'state/watchlists'),M8R_06_03_CONTROL_ROOT=str(restored/'state/governed/fixture-input/control'))
h.env['A5_APP_ROOT']=str(bundle/'app')
sys.path.insert(0,str(r/'sandbox/input'));from raw_stdio import probe
async def mcp(bundle,home,port):return probe(bundle/'runtime/venv/Scripts/python.exe',['-B',bundle/'bootstrap/launch.py','mcp','--home',home,'--service-url',f'http://127.0.0.1:{port}'],dict(h.env,TW_MARKET_HOME=str(home)),bundle)
h.mcp=mcp
app_before=h.inventory(bundle/'app');lifecycle=h.lifecycle(bundle,dest.home,prefs['port'])
assert lifecycle['status']['result']['identity']['status']=='ACTIVE'
assert lifecycle['status']['result']['installation']['installation_id']==dest.installation_id
assert lifecycle['doctor']['result']['installation']['diagnostics'].get('NONCANONICAL_ROOT_OVERRIDE')
assert h.inventory(restored)==before and h.inventory(bundle/'app')==app_before
assert dest.installation_metadata_path.read_bytes()==metadata and dest.settings_path.read_bytes()==settings and h.inventory(dest.state_root)==state_before
d.update(status='PASS',destination_installation_id=dest.installation_id,destination_home=str(dest.home),destination_metadata_sha256=hashlib.sha256(metadata).hexdigest(),destination_lifecycle=lifecycle,explicit_settings_use='verified restored loopback service preferences selected explicitly for this lifecycle; no source-root settings',explicit_state_use='existing A1/A2 operator root ENV seams select verified isolated L2 state explicitly; NONCANONICAL_ROOT_OVERRIDE disclosed; no metadata rewrite, merge, activation engine or new configuration authority',source_id_provenance_only=dest.installation_id!=d['source_installation_id'],flow='verify existing canonical L2 backups -> create fresh destination identity -> isolated canonical L2 restore -> explicit supported root selection/use -> lifecycle',app_root_unchanged=True)
p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8');print('P4 final explicit supported use PASS')
