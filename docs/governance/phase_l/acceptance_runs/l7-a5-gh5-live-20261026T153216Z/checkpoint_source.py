from pathlib import Path
R=Path(r'C:\twmarket_temp\l7-a5\repo')
assert Path.cwd().resolve()==R.resolve()
import sys,os,json,hashlib,datetime,subprocess,ast,copy
B=Path(r'C:\twmarket_temp\l7-a5-current-authorities');E=Path((B/'temp/gh5-run-path.txt').read_text(encoding='utf-8'));sys.path[:]=[str(E),str(R),*[x for x in sys.path if Path(x).drive.upper()!='D:']]
os.environ.update(TW_MARKET_HOME=str(B/'home'),TW_MARKET_STATE_ROOT=str(B/'state'),LOCALAPPDATA=str(B/'temp/isolated-localappdata'),TEMP=str(B/'temp'),TMP=str(B/'temp'),PYTHONDONTWRITEBYTECODE='1')
net=[]
def deny(e,a):
 if e.startswith('socket.'):net.append(e);raise RuntimeError('GH5_CHECKPOINT_NETWORK_DENIED')
 if e=='open' and isinstance(a[0],(str,bytes)):
  p=os.fsdecode(a[0]);assert Path(p).drive.upper()!='D:' and not ('\\users\\' in p.lower() and '\\tw-market' in p.lower())
sys.addaudithook(deny)
from runner_guard_source import durable,sha,canonical,now,AUTH,ACCEPTANCE,HEAD,TREE
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
def write(n,v):durable(E/n,v)
def verify(root,expected):
 m=load(root/'manifest.json');v=dict(m);d=v.pop('self_digest');assert d==expected and hashlib.sha256(canonical(v)).hexdigest()==d
 for a in m['members']:assert sha(root/a['path'])==a['sha256'] and (root/a['path']).stat().st_size==a['bytes']
 return {'path':str(root),'self_digest':d,'member_mismatches':0}
checks=[]
for n in ['gh3_retired_unconsumed_binding.json','gh4_retired_unconsumed_binding.json','r5_r5_1_binding.json','r5_2_binding.json','composite_closure_authority_binding.json','previous_a5_hold_binding.json']:
 b=load(E/n);checks.append(verify(Path(b['path']),b['self_digest']))
for n,d in load(E/'schema_identity.json').items():assert sha(R/'schemas'/n)==d
cal=load(E/'calendar_binding.json');assert sha(Path(cal['path']))==cal['raw_sha256'];dates=load(E/'i3_source_date_binding.json');assert sha(Path(dates['closure_path']))==dates['closure_sha256']
from scripts.m8r_08g_security_master_releases import load_active_identity_service
service,pointer,release,manifest=load_active_identity_service(root=B/'state/security-master');sm=load(E/'security_master_binding.json');assert service.release_id==sm['release_id']
for f,d in sm['hashes'].items():assert sha(B/'state/security-master/releases'/service.release_id/f)==d
from scripts import m8r_06_03_production_adapter as product
from scripts.m8r_06_03_execute_once import load_control_package
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight,validate_accepted_preflight
from scripts.m8r_05b_02.validator import validate_execution_authorization
from scripts.m8r_05b_02.authorization import _time
packages=load(E/'fresh_gh_authorizations.json');assert load(E/'prepare_phase_result.json')['status']=='PASS' and load(E/'fresh_authorization_preflight.json')['status']=='PASS' and load(E/'scenario_h_offline_projection.json')['status']=='PASS'
package_checks=[]
for k,v in packages.items():
 root,a,m=load_control_package(v['authorization_id']);assert sha(root/'control/manifest.json')==v['control_manifest_sha256'];validate_execution_authorization(a['authorization'],a['plan']);pre=build_orchestrator_preflight(a['plan'],a['authorization'],a['consumption_binding'],supplied_consumption_state=a['unused_consumption_state'],evaluation_timestamp=now().isoformat().replace('+00:00','Z'),executor_registry_metadata=product.load_production_executor_metadata(),output_root=str(root));validate_accepted_preflight(a['preflight'],pre)
 assert not list((root/'claims').glob('*.json')) and not list((root/'receipts').glob('*.json')) and _time(v['expires_at'])>now()+datetime.timedelta(minutes=46)
 assert AUTH in a['authorization']['owner_identity_reference'] and a['authorization']['owner_review_reference']==ACCEPTANCE
 if k=='G':assert a['plan']['resolved_source_trade_date']=='2026-10-22' and a['plan']['source_date_binding']['closure_authority_ref']=='I3_COMPOSITE_CLOSURE:sha256:c7c6c4d3d6db4b38fbd0498d8d82ed3fcff53b99d5e7bfeba662328f8d22464a'
 for historical in [Path(load(E/'gh3_retired_unconsumed_binding.json')['path']),Path(load(E/'gh4_retired_unconsumed_binding.json')['path'])]:
  p=historical/(k.lower()+'_plan.json')
  if p.exists():assert load(p).get('plan_id')!=v['plan_id'] and load(p).get('plan_hash')!=v['plan_hash']
 package_checks.append({'scenario':k,'plan_id':v['plan_id'],'authorization_id':v['authorization_id'],'status':'PASS','claims':0,'receipts':0,'remaining_validity_seconds':(_time(v['expires_at'])-now()).total_seconds()})
carry=load(E/'a_to_f_carry_forward_binding.json')
from scripts.m8r_05c.canonical import hash_body_excluding_key
for x in carry['scenarios']:
 s=x['prior_summary'];assert sha(Path(s['audit_path']))==s['audit_sha256'];res=load(Path(s['result_path']));assert hash_body_excluding_key(res,'result_hash')==res['result_hash']==s['result_hash']
 for a in x['lineage']['artifacts']:assert sha(Path(a['path']))==a['sha256']
guard=load(E/'runner_guard_offline_tests.json');assert guard['status']=='PASS' and guard['failed']==0 and guard['external_network_attempts']==0 and load(E/'guard_phase_result.json')['status']=='PASS';assert sha(E/'runner_guard_source.py')==load(E/'runner_guard_hash.json')['sha256']
for num in ['03','04','05']:assert not (B/f'logs/l7-a5-gh-20261026-live-recert-{num}-consumption-latch.json').exists()
# Static phase-dependency proof: PREPARE cannot read GUARD/checkpoint/live outputs.
source=(E/'gh_live_runner_source.py').read_text(encoding='utf-8');tree=ast.parse(source)
branches={}
for node in tree.body:
 if isinstance(node,ast.If) and isinstance(node.test,ast.Compare) and isinstance(node.test.left,ast.Constant) and node.test.left.value in ['--prepare','--guard']:
  branches[node.test.left.value]=node
assert set(branches)=={'--prepare','--guard'}
prepare=ast.get_source_segment(source,branches['--prepare'])
assert not any(x in prepare for x in ['runner_guard_offline_tests.json','final_pre_network_checkpoint.json','live_request_ledger.json','execute_controlled_plan('])
# High-level live invocation must rely on the deferred default finalization clock.
for node in ast.walk(tree):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='execute_controlled_plan':assert all(k.arg!='finalized_at' for k in node.keywords)
for n in ['gh_live_runner_source.py','runner_guard_source.py','guard_tests_source.py','gh5_review.py']:compile((E/n).read_bytes(),str(E/n),'exec')
# Pure synthetic chronology proof exercises the exact live reviewer, no claim or source adapter.
from gh5_review import temporal_record
row={'operation_ids':['synthetic-op'],'capability':'cash_institutional_flow_context','executor':'synthetic-executor','reservation_timestamp':'2026-10-26T15:00:01Z','actual_dispatch_timestamp':'2026-10-26T15:00:02Z'}
claim={'claim_created_at':'2026-10-26T15:00:00Z','confirmation_bound_at':'2026-10-26T15:00:00Z','finalized_at':'2026-10-26T15:00:04Z'};receipt={'finalized_at':claim['finalized_at']};bundle=dict(receipt);result={'generated_at':claim['finalized_at']};evidence={'retrieved_at':'2026-10-26T15:00:03Z','transport':{'complete_body_received':True}}
assert temporal_record('G','TWSE:1101',row,evidence,claim,receipt,bundle,result)['status']=='PASS'
bad=copy.deepcopy(evidence);bad['retrieved_at']='2026-10-26T15:00:01Z';assert temporal_record('G','TWSE:1101',row,bad,claim,receipt,bundle,result)['status']=='FAIL'
write('harness_dependency_graph_review.json',{'status':'PASS','graph':['PREPARE','GUARD','FINAL_CHECKPOINT','LIVE_ONCE'],'prepare_forward_dependency':False,'high_level_precomputed_finalized_at':False,'synthetic_valid_chronology':'PASS','synthetic_inversion_rejected':'PASS','external_requests':len(net)})
git=lambda *a:subprocess.check_output(['C:/Program Files/Git/cmd/git.exe',*a],cwd=R,text=True).strip()
assert git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and git('branch','--show-current')=='phase-l/l7-a5-r5-temporal-provenance-repair' and not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert not net
write('authority_consumption.json',{'authority_token':AUTH,'acceptance_id':ACCEPTANCE,'consumed':False,'state':'UNCONSUMED','latch_present':False})
write('live_window.json',{'state':'NOT_STARTED','start':None,'deadline':None})
write('network_attempt_ledger.json',{'requests':[],'attempt_count':0})
write('harness_source_hashes.json',{n:sha(E/n) for n in ['bootstrap_source.py','gh_live_runner_source.py','runner_guard_source.py','guard_tests_source.py','gh5_review.py']})
write('final_pre_network_checkpoint.json',{'status':'PASS','cwd':str(Path.cwd()),'HEAD':HEAD,'tree':TREE,'tracked_changes':0,'immutable_evidence':checks,'calendar':'PASS','composite':'PASS','Security_Master':'PASS','A_F_carry_forward':'PASS','fresh_packages':package_checks,'pure_preflights':'PASS','guard_cases':guard['passed'],'guard_failures':0,'external_requests':0,'claims':0,'receipts':0,'GH3':'RETIRED_UNCONSUMED','GH4':'RETIRED_UNCONSUMED','real_latch_absent':True,'source_date':'2026-10-22','source_hashes':load(E/'harness_source_hashes.json'),'checkpoint_at':now().isoformat().replace('+00:00','Z')})
print(json.dumps({'status':'PASS','guard_cases':guard['passed'],'packages':2,'external_requests':0,'claims':0,'latch_present':False,'cwd':str(Path.cwd())}))
