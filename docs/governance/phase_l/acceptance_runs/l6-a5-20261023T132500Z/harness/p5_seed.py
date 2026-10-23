import argparse,json,os,pathlib,sys
p=argparse.ArgumentParser();p.add_argument('--bundle',type=pathlib.Path);p.add_argument('--home',type=pathlib.Path);a=p.parse_args()
os.environ['TW_MARKET_HOME']=str(a.home);sys.path.insert(0,str(a.bundle/'app'));os.chdir(a.bundle/'app')
from scripts.tw_market_installation import resolve_installation
from scripts.m8r_08g_security_master_releases import build_candidate_release,qualify_candidate_release,activate_qualified_release
inst=resolve_installation().require_initialized()
record={'canonical_target_id':'TWSE:2330','identity':{'security_code':'2330','isin':'TW0002330008'},'classification':{'market':'TWSE','instrument_type':'common_share'},'lifecycle':{'state':'listed','resolution_status':'resolved','basis_event_ids':[],'events':[]},'execution_eligibility':{'status':'allowed','reason_codes':[]}}
provenance={'source_type':'test','snapshot_id':'a5-previous-accepted-state','source_content_hashes':{'fixture':'a'*64},'producer_skill':{'name':'test','skill_version':'1','skill_contract_hash':'b'*64}}
rid='security-master-20261023T000001Z'
build_candidate_release(root=inst.security_master_root,release_id=rid,records=[record],source_provenance=provenance)
qualified,report=qualify_candidate_release(root=inst.security_master_root,release_id=rid);assert qualified is not None and report['status']=='PASS'
activate_qualified_release(root=inst.security_master_root,release_id=rid)
print(json.dumps({'installation_id':inst.installation_id,'state_root':str(inst.state_root),'installation_schema_version':json.loads(inst.installation_metadata_path.read_text())['installation_schema_version'],'source_commit':json.loads((a.bundle/'distribution-manifest.json').read_text())['source_commit']}))
