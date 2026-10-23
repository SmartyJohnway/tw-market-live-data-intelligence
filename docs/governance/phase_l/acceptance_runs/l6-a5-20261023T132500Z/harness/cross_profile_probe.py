"""Transport a canonical L2 artifact, then verify/restore it with L2 in Docker."""
import base64,hashlib,json,pathlib,subprocess
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run');package=r/'p4-backup-CORE'
manifest=json.loads((package/'backup-manifest.json').read_text(encoding='utf-8'))
names=['backup-manifest.json']+[m['backup_relative_path'] for m in manifest['members']]
payload={'artifact_files':{name:base64.b64encode((package/name).read_bytes()).decode() for name in names},'guard':(r/'docker-guard/python_guard.py').read_text(encoding='utf-8')}
code='''import base64,hashlib,json,os,pathlib,sys
p=json.loads(sys.stdin.buffer.read());os.environ['A5_PYTHON_GUARD_SOURCE']=p['guard'];exec(compile(p['guard'],'<a5_guard>','exec'))
from scripts.tw_market_installation import initialize_installation
from scripts.tw_market_l2_adapter import A1_COMPATIBILITY_CONTRACT
from server.services.unified_backup import verify_backup
from server.services.unified_restore import CompatibilityAttestation,restore_backup,verify_restored_state
from scripts.m8r_08g_security_master_releases import load_active_identity_service
from scripts.m8r_09_persistent_watchlists import PersistentWatchlistStore
artifact=pathlib.Path('/tmp/l2-artifact');artifact.mkdir()
for name,data in p['artifact_files'].items():
 path=pathlib.PurePosixPath(name);assert not path.is_absolute() and '..' not in path.parts
 target=artifact/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(base64.b64decode(data))
verified=verify_backup(artifact,max_total_bytes=20000000)
m=json.loads((artifact/'backup-manifest.json').read_text());facts={row['logical_member_id']:'1' for row in m['members']}
assert not pathlib.Path('/var/lib/tw-market/home/meta/installation.json').exists()
dest=initialize_installation();metadata=dest.installation_metadata_path.read_bytes()
att=CompatibilityAttestation(m['manifest_integrity']['sha256'],facts);restored=pathlib.Path('/tmp/isolated-restore')
result=restore_backup(backup_path=artifact,destination=restored,compatibility=att,contract=A1_COMPATIBILITY_CONTRACT,forbidden_roots=[dest.home,pathlib.Path('/opt/tw-market/app')],max_total_bytes=20000000,max_member_count=100,restore_id='a5-cross-profile',created_at='2026-10-23T00:00:00Z')
assert result['status']=='RESTORED_STATE_VERIFIED'
verify_restored_state(backup_path=artifact,restored_path=restored,compatibility=att,contract=A1_COMPATIBILITY_CONTRACT,max_total_bytes=20000000,max_member_count=100)
identity,*_=load_active_identity_service(root=restored/'state/security-master')
store=PersistentWatchlistStore(root=restored/'state/watchlists',identity_service=identity,security_master_root=restored/'state/security-master')
assert store.verify_integrity()['status']=='PASS' and store.list_watchlists()['watchlists']
assert dest.installation_id!=m['source_state_identity'] and dest.installation_metadata_path.read_bytes()==metadata
assert not pathlib.Path('/tmp/a5-guard-events.jsonl').exists()
print(json.dumps({'status':'PASS','source_profile':'Native Windows Package C','destination_profile':'Linux/amd64 Docker Local Service','tier':'CORE','backup_manifest_sha256':m['manifest_integrity']['sha256'],'source_installation_id':m['source_state_identity'],'destination_installation_id':dest.installation_id,'destination_metadata_sha256':hashlib.sha256(metadata).hexdigest(),'restore':result,'explicit_use':'existing SM loader and Watchlist reader','source_id_provenance_only':True,'network':'none','provider_attempts':0,'canonical_L2_transfer':True,'transport_only':'exact manifest + declared backup files through stdin; no direct active-state or volume copying'}))
'''
image='tw-market-local-service:l6-a5-3707c553-replacement'
args=['docker','run','--rm','-i','--network','none','--read-only','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--mount','type=volume,source=twmarket-l6-a5-final-cross-home,target=/var/lib/tw-market/home','--mount','type=volume,source=twmarket-l6-a5-final-cross-state,target=/var/lib/tw-market/state','--env','TW_MARKET_HOME=/var/lib/tw-market/home','--env','TW_MARKET_STATE_ROOT=/var/lib/tw-market/state','--entrypoint','python',image,'-B','-c',code]
proc=subprocess.run(args,input=json.dumps(payload).encode(),capture_output=True,timeout=120)
(r/'cross-profile.stderr.log').write_bytes(proc.stderr)
assert proc.returncode==0,proc.stderr.decode(errors='replace')
d=json.loads(proc.stdout);assert d['backup_manifest_sha256']==manifest['manifest_integrity']['sha256']
(r/'cross_profile_probe.json').write_text(json.dumps(d,indent=2),encoding='utf-8');print('Cross-profile CORE PASS')
