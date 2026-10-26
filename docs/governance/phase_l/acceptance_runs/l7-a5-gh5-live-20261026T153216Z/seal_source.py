from pathlib import Path
R=Path(r'C:\twmarket_temp\l7-a5\repo')
assert Path.cwd().resolve()==R.resolve()
import sys,os,json,hashlib,subprocess,datetime
B=Path(r'C:\twmarket_temp\l7-a5-current-authorities');E=Path((B/'temp/gh5-run-path.txt').read_text(encoding='utf-8'));sys.path[:]=[str(E),str(R),*[x for x in sys.path if Path(x).drive.upper()!='D:']]
net=[]
def deny(e,a):
 if e.startswith('socket.'):net.append(e);raise RuntimeError('GH5_POSTLIVE_NETWORK_DENIED')
 if e=='open' and isinstance(a[0],(str,bytes)):
  p=os.fsdecode(a[0]);assert Path(p).drive.upper()!='D:' and not ('\\users\\' in p.lower() and '\\tw-market' in p.lower())
sys.addaudithook(deny)
c=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):
 with (E/n).open('wb') as f:f.write(c(v));f.flush();os.fsync(f.fileno())
def verify(root,digest):
 m=load(root/'manifest.json');v=dict(m);d=v.pop('self_digest');assert d==digest and hashlib.sha256(c(v)).hexdigest()==d
 for a in m['members']:assert sha(root/a['path'])==a['sha256'] and (root/a['path']).stat().st_size==a['bytes']
 return {'path':str(root),'members':m['member_count'],'member_mismatches':0,'self_digest':d}
from scripts.m8r_05c.canonical import hash_body_excluding_key
from scripts.m8r_05b_03.receipt import journal_relative_path
packages=load(E/'fresh_gh_authorizations.json');lineage=load(E/'result_audit_lineage_review.json');assert lineage['status']=='PASS' and lineage['operations']==4 and lineage['artifacts']==4 and lineage['citations']==4 and lineage['orphans']==lineage['broken_citations']==lineage['hash_mismatches']==lineage['unfinalized_successful_claims']==0
checks=[];summaries={};journal_checks=[]
for k in 'GH':
 summary=load(E/('scenario_'+k.lower()+'.json'));assert summary['status']=='PASS' and summary['temporal_provenance']=='PASS';summaries[k]=summary
 root=Path(packages[k]['package_path']);result=load(Path(summary['result_path']));audit=load(Path(summary['audit_path']));assert hash_body_excluding_key(result,'result_hash')==result['result_hash']==summary['result_hash'];assert hash_body_excluding_key(audit,'audit_package_hash')==audit['audit_package_hash'];assert sha(Path(summary['audit_path']))==summary['audit_sha256'];assert all(audit['integrity_verification'].values())
 out=load(E/('scenario_'+k.lower()+'_execution_output.json'));claim=out['claim_record'];receipt=out['execution_receipt'];bundle=out['evidence_bundle'];assert claim['finalized_at']==receipt['finalized_at']==bundle['finalized_at']==result['generated_at']
 assert len(list((root/'claims').glob('*.json')))==len(list((root/'receipts').glob('*.json')))==1
 for a in bundle['artifact_inventory']:assert sha(root/a['relative_path'])==a['sha256'] and (root/a['relative_path']).stat().st_size==a['byte_size']
 journal=load(root/journal_relative_path(packages[k]['authorization_id']));assert journal['state']=='claim_committed';journal_checks.append({'scenario':k,'path':str(root/journal_relative_path(packages[k]['authorization_id'])),'sha256':sha(root/journal_relative_path(packages[k]['authorization_id'])),'state':journal['state'],'record':journal,'redispatch':False,'second_claim':False,'finalization_journal_corrupt':False})
 checks.append({'scenario':k,'result_semantic_hash':result['result_hash'],'result_file_sha256':sha(Path(summary['result_path'])),'audit_semantic_hash':audit['audit_package_hash'],'audit_file_sha256':sha(Path(summary['audit_path'])),'audit_integrity_verification':audit['integrity_verification'],'hashes_valid':True})
write('result_audit_hash_reverification.json',checks);write('cas_finalization_journal_review.json',{'status':'PASS','journals':journal_checks,'unexpected_journal_corrupt':0,'finalization_retries':0})
temporal=load(E/'temporal_invariant_matrix.json');assert temporal['status']=='PASS' and len(temporal['operations'])==4 and all(x['status']=='PASS' for x in temporal['operations'])
rows=load(E/'live_request_ledger.json')['requests'];assert len(rows)==4 and [x['scenario'] for x in rows]==['G','G','H','H'] and all(x['HTTP_status']==200 and x['redirect_count']==0 and not x['retry'] for x in rows)
assert {x['targets'][0] for x in rows}=={'TWSE:1101','TPEX:5347','TWSE:2330','TPEX:6488'}
assert 'date=20261022' in next(x for x in rows if x['targets']==['TWSE:1101'])['canonical_url']
latch_path=B/'logs/l7-a5-gh-20261026-live-recert-05-consumption-latch.json';latch=load(latch_path);assert latch['state']=='CONSUMED' and latch['authority_token']==load(E/'owner_authority.json')['authority_token'] and latch['acceptance_id']=='L7-A5-GH-20261026-LIVE-RECERT-05' and latch['cwd']==str(R)
for f,d in latch['frozen_files'].items():assert sha(Path(f))==d
for f,d in load(E/'harness_source_hashes.json').items():assert sha(E/f)==d
write('durable_consumption_latch_snapshot.json',latch)
write('network_attempt_ledger.json',load(E/'live_request_ledger.json'))
network=load(E/'network_accounting.json');assert network['GH_total']==4 and network['G_total']==2 and network['H_total']==2 and not network['guard_denials'];network.update(total_external_requests=4,redirects=0,fallbacks=0,manual_probes=0,diagnostic_probes=0,Security_Master_requests=0,calendar_requests=0,closure_requests=0,DGPA_requests=0,Taipei_requests=0,NCDR_requests=0,search_requests=0,non_GH_external_requests=0,live_once_invocations=1,postlive_external_requests=len(net));write('network_accounting.json',network)
write('transport_accounting.json',{'status':'PASS','external_requests':4,'HTTP_200':4,'redirects':0,'retry':0,'raw_payload_persisted':False,'response_completed_at':'RESPONSE_COMPLETION_TIMESTAMP_NOT_RETAINED','requests':rows})
carry=load(E/'a_to_f_carry_forward_binding.json');assert carry['status']=='PASS' and carry['operations']==11 and carry['artifacts']==20 and carry['citations']==14
for x in carry['scenarios']:
 s=x['prior_summary'];assert sha(Path(s['audit_path']))==s['audit_sha256'];res=load(Path(s['result_path']));assert hash_body_excluding_key(res,'result_hash')==res['result_hash']==s['result_hash']
 for a in x['lineage']['artifacts']:assert sha(Path(a['path']))==a['sha256']
write('composite_a_to_h_acceptance_matrix.json',{'status':'TECHNICAL_PASS_PENDING_FINAL_INDEPENDENT_REVIEW','A':'IMMUTABLE_CARRIED_FORWARD_PASS','B':'IMMUTABLE_CARRIED_FORWARD_PASS','C':'IMMUTABLE_CARRIED_FORWARD_PASS','D':'IMMUTABLE_CARRIED_FORWARD_PASS','E':'IMMUTABLE_CARRIED_FORWARD_PASS','F':'IMMUTABLE_CARRIED_FORWARD_PASS','G':'FRESH_RECERTIFICATION_5_PASS','H':'FRESH_RECERTIFICATION_5_PASS','A_F_binding_sha256':sha(E/'a_to_f_carry_forward_binding.json'),'G_evidence_sha256':sha(E/'scenario_g.json'),'H_evidence_sha256':sha(E/'scenario_h.json'),'historical_regeneration':False})
lineage.update(carried_A_F={'operations':11,'artifacts':20,'citations':14,'regenerated':False,'binding_sha256':sha(E/'a_to_f_carry_forward_binding.json')},composite_totals={'operations':15,'artifacts':24,'citations':18});write('result_audit_lineage_review.json',lineage)
immutable=[]
for n in ['gh3_retired_unconsumed_binding.json','gh4_retired_unconsumed_binding.json','r5_r5_1_binding.json','r5_2_binding.json','composite_closure_authority_binding.json','previous_a5_hold_binding.json']:
 b=load(E/n);immutable.append(verify(Path(b['path']),b['self_digest']))
immutable.append(verify(B/'evidence/20261026T120000Z-l7-a5-gh-bounded-live-recertification-2-r4','59ebe67809e12d74e3ec24f02544a832377531f9c89ee3c2b9bdf966c185c502'))
write('immutable_evidence_post_verification.json',immutable)
for n,d in load(E/'schema_identity.json').items():assert sha(R/'schemas'/n)==d
sm=load(E/'security_master_binding.json')
for f,d in sm['hashes'].items():assert sha(B/'state/security-master/releases'/sm['release_id']/f)==d
cal=load(E/'calendar_binding.json');dates=load(E/'i3_source_date_binding.json');assert sha(Path(cal['path']))==cal['raw_sha256'] and sha(Path(dates['closure_path']))==dates['closure_sha256']
git=lambda *a:subprocess.check_output(['C:/Program Files/Git/cmd/git.exe',*a],cwd=R,text=True).strip()
i=load(E/'entry_identity.json');assert git('rev-parse','HEAD')==i['HEAD'] and git('rev-parse','HEAD^{tree}')==i['tree'] and git('branch','--show-current')==i['branch'] and not git('diff','--name-only') and not git('diff','--cached','--name-only')
write('repository_immutability.json',{'HEAD':i['HEAD'],'tree':i['tree'],'branch':i['branch'],'tracked_changes':0,'product_schema_test_changes':0,'status':git('status','--short').splitlines(),'preexisting_untracked_blocker_evidence_untouched':True,'commit':False,'push':False,'PR':False,'merge':False,'tag':False,'release':False})
write('filesystem_boundary.json',{'allowed_mutable_roots':[str(R.parent),str(B)],'D_access':0,'production_access':0,'production_mutation':0,'cwd':str(Path.cwd()),'postlive_network_attempts':len(net)})
window=load(E/'live_window.json');assert window['state']=='STOPPED' and datetime.datetime.fromisoformat(window['stopped_at'].replace('Z','+00:00'))<datetime.datetime.fromisoformat(window['deadline'].replace('Z','+00:00'))
window['actual_stop']=window['stopped_at'];write('live_window.json',window)
write('gap_closure_matrix.json',{'L7-GAP-15':'TECHNICALLY_CLOSED_PENDING_FINAL_INDEPENDENT_REVIEW'});write('exit_criteria_matrix.json',{'L7-EXIT-19':'TECHNICAL_PASS_PENDING_FINAL_INDEPENDENT_REVIEW','Owner_final_acceptance':False})
final=load(E/'final_review.json');assert final['failure'] is None and final['new_completed_scenarios']==['G','H'];final.update(PREPARE='PASS',GUARD='PASS',FINAL_CHECKPOINT='PASS',G_functional='PASS',G_temporal='PASS',G_Result_Audit='PASS',H_functional='PASS',H_temporal='PASS',H_active_Security_Master='PASS',H_Result_Audit='PASS',A_F_carry_forward='PASS',request_budget='PASS',response_completed_at='RESPONSE_COMPLETION_TIMESTAMP_NOT_RETAINED',EOD_precision_note='Canonical EOD retrieval/completion retain seconds. Preserved high precision utc_now call event boundaries establish post-fetch causal order; source timestamp strings unchanged.',L7_GAP_15='TECHNICALLY_CLOSED_PENDING_FINAL_INDEPENDENT_REVIEW',L7_EXIT_19='TECHNICAL_PASS_PENDING_FINAL_INDEPENDENT_REVIEW',orphans=0,broken_citations=0,hash_mismatches=0,unfinalized_successful_claims=0,Owner_final_acceptance=False,STOP=True);write('final_review.json',final)
# Preserve post-live sealing and final-checkpoint source too; never mutate live sources.
(E/'checkpoint_source.py').write_bytes((B/'temp/checkpoint_gh5.py').read_bytes());(E/'seal_source.py').write_bytes(Path(__file__).read_bytes())
required=['owner_authority.json','entry_identity.json','gh3_retired_unconsumed_binding.json','gh4_retired_unconsumed_binding.json','r5_r5_1_binding.json','r5_2_binding.json','cwd_preflight.json','schema_identity.json','composite_closure_authority_binding.json','calendar_binding.json','security_master_binding.json','a_to_f_carry_forward_binding.json','scenario_matrix.json','live_allowlist.json','live_budget.json','prepare_phase_result.json','g_plan.json','g_authorization.json','h_plan.json','h_authorization.json','fresh_authorization_preflight.json','scenario_h_offline_projection.json','guard_phase_result.json','runner_guard_offline_tests.json','final_pre_network_checkpoint.json','authority_consumption.json','live_window.json','network_attempt_ledger.json','network_accounting.json','scenario_g.json','scenario_h.json','g_temporal_chronology.json','h_temporal_chronology.json','temporal_invariant_matrix.json','scenario_h_active_security_master_provenance.json','result_audit_lineage_review.json','transport_outcome_matrix.json','contract_outcome_matrix.json','composite_a_to_h_acceptance_matrix.json','filesystem_boundary.json','repository_immutability.json','final_review.json']
assert all((E/n).is_file() for n in required) and not net
m={'canonicalization':'UTF-8 ensure_ascii=false sort_keys=true compact separators; self_digest excluded','member_count':0,'member_mismatches':0,'members':[]}
for p in sorted(E.iterdir(),key=lambda p:p.name):
 if p.is_file() and p.name!='manifest.json':m['members'].append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
m['member_count']=len(m['members']);m['self_digest']=hashlib.sha256(c(m)).hexdigest();write('manifest.json',m)
v=load(E/'manifest.json');d=v.pop('self_digest');assert hashlib.sha256(c(v)).hexdigest()==d
for a in v['members']:assert sha(E/a['path'])==a['sha256'] and (E/a['path']).stat().st_size==a['bytes']
print(json.dumps({'disposition':final['disposition'],'evidence':str(E),'members':m['member_count'],'mismatches':0,'self_digest':d,'window':window,'G_finalized_at':summaries['G']['finalized_at'],'H_finalized_at':summaries['H']['finalized_at'],'operations':4,'artifacts':4,'citations':4,'external_requests':4},ensure_ascii=False))
