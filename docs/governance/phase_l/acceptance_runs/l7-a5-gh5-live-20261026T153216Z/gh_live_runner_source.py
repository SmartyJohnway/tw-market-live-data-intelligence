"""Independent one-shot G/H recertification, existing canonical product chain only."""
from __future__ import annotations
from pathlib import Path
R=Path(r"C:\twmarket_temp\l7-a5\repo")
assert Path.cwd().resolve()==R.resolve()
import sys,os,json,hashlib,datetime,dataclasses,subprocess,copy
from pathlib import Path
R=Path(r'C:\twmarket_temp\l7-a5\repo');B=Path(r'C:\twmarket_temp\l7-a5-current-authorities');E=Path((B/'temp/gh5-run-path.txt').read_text());sys.path[:]=[str(E),str(R),*[x for x in sys.path if Path(x).drive.upper()!='D:']]
for k in list(os.environ):
 if k.startswith('TW_MARKET_') or k.startswith('M8R_06_03_') or k in {'PYTHONPATH','A6_SESSION_ROOT'} or k.lower() in {'http_proxy','https_proxy','all_proxy'}:os.environ.pop(k,None)
os.environ.update(PATH=r'C:\Program Files\Git\cmd;C:\Windows\System32;C:\Windows',TW_MARKET_HOME=str(B/'home'),TW_MARKET_STATE_ROOT=str(B/'state'),LOCALAPPDATA=str(B/'temp/isolated-localappdata'),TEMP=str(B/'temp'),TMP=str(B/'temp'),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',NO_PROXY='*')
from runner_guard_source import Guard,Denied,LiveHold,AUTH,ACCEPTANCE,HEAD,TREE,sha,canonical,durable,now,stamp

def zstamp():return now().isoformat().replace('+00:00','Z')
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def write(n,v):durable(E/n,v)
def git(*a):return subprocess.check_output(['C:/Program Files/Git/cmd/git.exe',*a],cwd=R,text=True).strip()
L=B/'logs/l7-a5-gh-20261026-live-recert-05-consumption-latch.json'
assert not L.exists() and git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and git('rev-parse','HEAD^')=='cf90c697665e24b8bd5700bf8c033b102f1364e0' and git('branch','--show-current')=='phase-l/l7-a5-r5-temporal-provenance-repair' and not git('diff','--name-only') and not git('diff','--cached','--name-only')
for p in (B/'evidence').rglob('authority_consumption.json'):
 v=load(p)
 if v.get('acceptance_id')==ACCEPTANCE or v.get('authority_token')==AUTH:assert not v.get('consumed')
offline_attempts=[]
def offline_entry(event,args):
 if ('--prepare' in sys.argv or '--guard' in sys.argv) and event.startswith('socket.'):
  offline_attempts.append(event);raise RuntimeError('GH5_OFFLINE_NETWORK_DENIED')
sys.addaudithook(offline_entry)
from scripts import m8r_06_03_production_adapter as product
from scripts.m8r_06_01c2_mode_a_security_master_loader import get_production_mode_a_security_master
from scripts.m8r_filesystem_safety import reject_reparse_components
from scripts.phase_i_i3_execution_date import resolve_and_bind_i3_twse_plan
from scripts.m8r_05b_02.authorization import _time
from scripts.m8r_05b_03.preflight import build_orchestrator_preflight,validate_accepted_preflight
from server.services.unified_mode_b1 import build_mode_b1_preview
from server.services.unified_mode_b2 import _materialize_execution_ticket
from scripts.m8r_06_03_execute_once import load_control_package
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from server.services.unified_mode_c import build_mode_c_result_package
for p in [R,B,B/'home',B/'state',B/'state/security-master',B/'temp',E]:assert p.resolve().is_relative_to(Path(r'C:\twmarket_temp'));reject_reparse_components(p)
matrix=load(E/'frozen_gh_matrix.json');sm=load(E/'security_master_binding.json');date_binding=load(E/'i3_source_date_binding.json');service=get_production_mode_a_security_master().identity_service;assert service.release_id==sm['release_id'] and service.manifest_hash==sm['hashes']['manifest.json']

if '--prepare' in sys.argv:
 attempts=[]
 def offline(event,args):
  if event.startswith('socket.'):attempts.append(event);raise RuntimeError('GH_authorization_network_denied')
 sys.addaudithook(offline)
 binding={'authority_token':AUTH,'acceptance_id':ACCEPTANCE,'HEAD':HEAD,'tree':TREE,'matrix_sha256':sha(E/'frozen_gh_matrix.json'),'allowlist_sha256':sha(E/'live_allowlist.json'),'guard_sha256':sha(E/'runner_guard_source.py'),'budget':load(E/'live_budget.json'),'source_contracts':{k:v['source_contract'] for k,v in matrix['scenarios'].items()},'security_master_release':service.release_id,'security_master_manifest':service.manifest_hash,'I3_source_date':'2026-10-22','composite_closure_authority':load(E/'composite_closure_authority_binding.json'),'calendar_binding':load(E/'calendar_binding.json'),'R5_R5_1_evidence':load(E/'r5_r5_1_binding.json'),'R5_2_evidence':load(E/'r5_2_binding.json'),'GH3_retired':load(E/'gh3_retired_unconsumed_binding.json'),'GH4_retired':load(E/'gh4_retired_unconsumed_binding.json'),'closure_authority_sha256':date_binding['closure_sha256'],'closure_authority_ref':date_binding['accepted_frozen_binding']['closure_authority_ref'],'frozen_evaluation':date_binding['accepted_frozen_binding']['evaluation_time'],'previous_A5_HOLD_digest':load(E/'previous_a5_hold_binding.json')['self_digest'],'A_F_carry_forward_hash':sha(E/'carried_forward_a_to_f_acceptance_binding.json')};binding_digest=hashlib.sha256(canonical(binding)).hexdigest();write('acceptance_authorization_input_binding.json',{'binding':binding,'sha256':binding_digest})
 previews=load(E/'offline_gh_previews.json');packages={};checks=[]
 for key in 'GH':
  request=previews[key]['request'];preview=build_mode_b1_preview(request);plan=copy.deepcopy(preview['orchestration_plan'])
  if key=='G':
   frozen=date_binding['accepted_frozen_binding'];cal=load(Path(date_binding['calendar_path']));closure=load(Path(date_binding['closure_path']));assert sha(Path(date_binding['calendar_path']))==date_binding['calendar_raw_sha256'] and sha(Path(date_binding['closure_path']))==date_binding['closure_sha256']
   plan=resolve_and_bind_i3_twse_plan(plan,evaluation_time=frozen['evaluation_time'],official_calendar=cal,closure_events=closure['closure_events'],calendar_authority_ref=frozen['calendar_authority_ref'],closure_authority_ref=frozen['closure_authority_ref'],closure_authority_complete=True,closure_authority=closure);assert plan['resolved_source_trade_date']=='2026-10-22'
  t=now().replace(microsecond=0);fmt=lambda x:x.isoformat().replace('+00:00','Z');decision={'decision':'approved','decision_reason':'Independent GH Owner authorization; frozen acceptance binding sha256='+binding_digest,'owner_identity_reference':AUTH+'|binding-sha256='+binding_digest,'owner_review_reference':ACCEPTANCE,'reviewed_at':fmt(t),'issued_at':fmt(t),'expires_at':fmt(t+datetime.timedelta(seconds=3600)),'single_use':True,'replay_policy':'deny_replay','maximum_use_count':1,'approval_scope_mode':'whole_plan_executable_scope','approved_operation_ids':[],'approved_batch_group_ids':[],'approved_batch_membership':{}}
  write(key.lower()+'_plan.json',plan);ticket=_materialize_execution_ticket(request,plan,decision);root,artifacts,manifest=load_control_package(ticket['authorization_id']);write(key.lower()+'_authorization.json',artifacts['authorization']);evaluation=zstamp();rebuilt=build_orchestrator_preflight(artifacts['plan'],artifacts['authorization'],artifacts['consumption_binding'],supplied_consumption_state=artifacts['unused_consumption_state'],evaluation_timestamp=evaluation,executor_registry_metadata=product.load_production_executor_metadata(),output_root=str(root));validate_accepted_preflight(artifacts['preflight'],rebuilt)
  assert _time(ticket['expires_at'])>=now()+datetime.timedelta(minutes=46) and not list((root/'claims').glob('*.json')) and not list((root/'receipts').glob('*.json'))
  packages[key]={'authorization_id':ticket['authorization_id'],'authorization_hash':ticket['authorization_hash'],'plan_id':ticket['plan_id'],'plan_hash':ticket['plan_hash'],'issued_at':ticket['issued_at'],'expires_at':ticket['expires_at'],'package_path':str(root),'control_manifest_sha256':sha(root/'control/manifest.json'),'acceptance_binding_sha256':binding_digest,'owner_identity_reference':artifacts['authorization']['owner_identity_reference'],'authorization_consumed':False,'network_executed':False,'claims':0,'receipts':0}
  checks.append({'scenario':key,'status':'PASS','evaluation_timestamp':evaluation,'preflight_hash':rebuilt['preflight_hash'],'remaining_validity_seconds':(_time(ticket['expires_at'])-now()).total_seconds(),'covers_45_minute_window':True,'claims':0,'external_network_attempts':0})
 write('fresh_gh_authorizations.json',packages);write('fresh_authorization_preflight.json',{'status':'PASS','checks':checks,'canonical_MAX_LIFETIME_SECONDS':86400,'decision_lifetime_seconds':3600,'live_guard_window_seconds':2700,'external_network_attempts':len(attempts),'execute_controlled_plan_called':False});proj={}
 for market,code in [('TWSE','2330'),('TPEX','6488')]:
  row=next(iter(product._official_eod_security_master_projection(market,[code]).values()))
  assert row['coverage_mode']=='canonical_security_master' and row['classification_status']=='classified' and row['production_classification_completeness']=='complete' and row['release_id']==service.release_id and row['release_manifest_sha256']==service.manifest_hash and row['execution_eligibility']['status']=='allowed'
  proj[market+':'+code]=row
 write('scenario_h_offline_projection.json',{'status':'PASS','projections':proj,'bounded_seed_only':False,'external_requests':0})
 write('prepare_phase_result.json',{'status':'PASS','packages':packages,'claims':0,'receipts':0,'external_requests':len(attempts)+len(offline_attempts),'phase_dependencies':['immutable entry inputs'],'guard_output_required':False,'checkpoint_required':False})
 print(json.dumps({'fresh_packages':2,'pure_preflights':'PASS','validity_seconds':3600,'live_window_seconds':2700,'network_attempts':len(attempts)}));sys.exit(0)

if '--guard' in sys.argv:
 assert load(E/'prepare_phase_result.json')['status']=='PASS'
 assert load(E/'fresh_authorization_preflight.json')['status']=='PASS'
 assert load(E/'scenario_h_offline_projection.json')['status']=='PASS'
 for key in 'gh':
  assert (E/(key+'_plan.json')).is_file() and (E/(key+'_authorization.json')).is_file()
 assert not L.exists()
 import runpy
 runpy.run_path(str(E/'guard_tests_source.py'),run_name='__main__')
 assert load(E/'runner_guard_offline_tests.json')['status']=='PASS' and not L.exists()
 write('guard_phase_result.json',{'status':'PASS','real_latch_exists':False,'external_requests':len(offline_attempts),'cases':load(E/'runner_guard_offline_tests.json')['passed']})
 sys.exit(0)

assert '--live-once' in sys.argv, 'explicit phase required'
assert load(E/'prepare_phase_result.json')['status']=='PASS'
assert load(E/'guard_phase_result.json')['status']=='PASS'
assert load(E/'runner_guard_offline_tests.json')['status']=='PASS'
packages=load(E/'fresh_gh_authorizations.json');assert load(E/'fresh_authorization_preflight.json')['status']=='PASS'
g=Guard(E,matrix);g.latch=L;g.authorizations=packages;g.scenario='G'
frozen_files={str(E/n):sha(E/n) for n in ['frozen_gh_matrix.json','live_allowlist.json','runner_guard_source.py','gh_live_runner_source.py','fresh_gh_authorizations.json','acceptance_authorization_input_binding.json','carried_forward_a_to_f_acceptance_binding.json','gh5_review.py','r5_r5_1_binding.json','r5_2_binding.json','final_pre_network_checkpoint.json','guard_tests_source.py','gh3_retired_unconsumed_binding.json','gh4_retired_unconsumed_binding.json']}
g.frozen={'consolidated_acceptance_disposition':'L7_A5_R5_R5_1_R5_2_CONSOLIDATED_INDEPENDENT_REVIEW_PASS','composite_closure_authority':load(E/'composite_closure_authority_binding.json'),'calendar_binding':load(E/'calendar_binding.json'),'R5_R5_1_evidence':load(E/'r5_r5_1_binding.json'),'R5_2_evidence':load(E/'r5_2_binding.json'),'GH3_retired':load(E/'gh3_retired_unconsumed_binding.json'),'GH4_retired':load(E/'gh4_retired_unconsumed_binding.json'),'closure_authority_sha256':date_binding['closure_sha256'],'closure_authority_ref':date_binding['accepted_frozen_binding']['closure_authority_ref'],'frozen_evaluation':date_binding['accepted_frozen_binding']['evaluation_time'],'previous_A5_HOLD_digest':load(E/'previous_a5_hold_binding.json')['self_digest'],'A_F_carry_forward_hash':sha(E/'carried_forward_a_to_f_acceptance_binding.json'),'G_plan_authorization':packages['G'],'H_plan_authorization':packages['H'],'security_master_release':service.release_id,'security_master_manifest_hash':service.manifest_hash,'I3_source_date':'2026-10-22','matrix_hash':sha(E/'frozen_gh_matrix.json'),'allowlist_hash':sha(E/'live_allowlist.json'),'guard_hash':sha(E/'runner_guard_source.py'),'runner_hash':sha(E/'gh_live_runner_source.py'),'G_ceiling':2,'H_ceiling':4,'global_ceiling':6,'retry':0,'frozen_files':frozen_files}
g.frozen.update(cwd=str(Path.cwd()),repository_root=str(R),GH3_historical_state='RETIRED_UNCONSUMED',GH4_historical_state='RETIRED_UNCONSUMED',branch=git('branch','--show-current'),calendar_raw_sha256=date_binding['calendar_raw_sha256'],calendar_normalized_sha256=date_binding['calendar_normalized_sha256'],retry_policy={'automatic':0,'manual':0})
for path in [Path(date_binding['calendar_path']),Path(date_binding['closure_path'])]:
 frozen_files[str(path)]=sha(path)
for v in packages.values():assert _time(v['expires_at'])>=now()+datetime.timedelta(minutes=45)
assert Path.cwd().resolve()==R.resolve()
assert load(E/'final_pre_network_checkpoint.json')['status']=='PASS'
g.armed=True;g.install()
import server.operational_diagnostics as diag
original_timed=diag.timed_source_call
def timed(source_id,fn,**kw):
 old=g.source_id;g.source_id=source_id
 try:return original_timed(source_id,fn,**kw)
 finally:g.source_id=old
diag.timed_source_call=timed;product.timed_source_call=timed
observed=[]
def wrap(fn,batch):
 def call(requests,context):
  rs=requests if batch else (requests,);first=rs[0];g.context={'targets':sorted(set(t for r in rs for t in r['approved_security_identifiers'])),'capability':first['capability_id'],'executor':first['executor_id'],'operation_ids':[r['operation_id'] for r in rs],'authorization_id':first['authorization_id'],'authorization_hash':first['authorization_hash'],'plan_hash':first['plan_hash']}
  scope=matrix['scenarios'][g.scenario]
  if g.context['executor'] not in scope['executors'] or g.context['capability'] not in scope['capabilities'] or not set(g.context['targets']).issubset(scope['targets']):raise LiveHold('operation_scope_binding')
  before=len(g.rows);out=fn(requests,context);values=out if batch else [out];observed.extend({'scenario':g.scenario,'targets':g.context['targets'],'operation_result':v} for v in values);write('observed_operation_results.json',observed)
  for row in g.rows[before:]:row['contract_result']='CANONICAL_OPERATION_RETURNED'
  g.save()
  if any(x['transport_result'] in {'transport_error','tls_certificate_verification'} or x['HTTP_status'] is not None and not 200<=x['HTTP_status']<300 for x in g.rows[before:]) or g.denials:raise LiveHold('transport_or_guard_failure')
  if any(v.get('status')=='failed' for v in values):raise LiveHold('canonical_operation_failed')
  return out
 return call
# Read-only EOD event observer; all values and source semantics unchanged.
eod_observations=[];clock_events=[]
for module_name,market in [('scripts.m8a_twse_official_eod_adapter','TWSE'),('scripts.m8a_tpex_official_eod_adapter','TPEX')]:
 import importlib
 module=importlib.import_module(module_name);original_clock=module.utc_now
 def clock_observe(_fn=original_clock,_market=market):
  before=zstamp();value=_fn();after=zstamp()
  clock_events.append({'market':_market,'event':'adapter_utc_now','before':before,'after':after,'returned_value':value})
  write('eod_clock_observer.json',clock_events)
  return value
 module.utc_now=clock_observe
for name,market in [('execute_twse_official_eod_adapter','TWSE'),('execute_tpex_official_eod_adapter','TPEX')]:
 original=getattr(product,name)
 def observe(*args,_fn=original,_market=market,**kwargs):
  output=_fn(*args,**kwargs)
  eod_observations.append({'market':_market,'adapter_return_observed_at':zstamp(),'adapter_result':output})
  write('eod_adapter_output_observer.json',eod_observations)
  return output
 setattr(product,name,observe)
base=product.build_production_runtime_adapter_registry();registry=RuntimeAdapterRegistry([dataclasses.replace(r,adapter=wrap(r.adapter,False),batch_adapter=wrap(r.batch_adapter,True) if r.batch_adapter else None) for r in base._by_route.values()])
completed=[];summaries=[];failure=None
try:
 for key in 'GH':
  g.scenario=key
  if key=='H' and not g.g_passed:raise LiveHold('H_requires_G_full_success')
  info=packages[key];root,a,m=load_control_package(info['authorization_id']);assert sha(root/'control/manifest.json')==info['control_manifest_sha256'];before=len(g.rows);t=zstamp()
  result=execute_controlled_plan(a['plan'],a['authorization'],a['consumption_binding'],supplied_consumption_state=a['unused_consumption_state'],accepted_preflight=a['preflight'],evaluation_timestamp=t,claim_created_at=t,executor_registry_metadata=product.load_production_executor_metadata(),runtime_adapter_registry=registry,output_root=str(root),mode='execute-approved',confirm_execution=True,operator_confirmation_reference=ACCEPTANCE,confirm_network_execution=True)
  write('scenario_'+key.lower()+'_execution_output.json',result)
  inventory=result['aggregation']['artifact_inventory'];evidence=[]
  for item in inventory:
   p=root/item['relative_path'];assert sha(p)==item['sha256']
   if p.suffix=='.json':evidence.append(load(p))
  if key=='G':
   assert len(evidence)==2 and all(v.get('status')=='complete' for v in evidence)
  else:
   findings=[]
   def walk(v):
    if isinstance(v,dict):
     if v.get('coverage_mode')=='canonical_security_master' and v.get('release_id'):findings.append(v)
     for c in v.values():walk(c)
    elif isinstance(v,list):
     for c in v:walk(c)
   walk(evidence)
   for target in ['TWSE:2330','TPEX:6488']:
    matches=[v for v in findings if v.get('canonical_target_id')==target];assert matches and all(v['release_id']==service.release_id and v['release_manifest_sha256']==service.manifest_hash and v['production_classification_completeness']=='complete' and v['instrument_type']=='equity' and v['execution_eligibility']['status']=='allowed' for v in matches)
   write('scenario_h_active_security_master_provenance.json',{'status':'PASS','classifications':findings,'bounded_seed_only':False})
  modec=build_mode_c_result_package({'control_package_id':info['authorization_id']},output_schema_version='unified_market_evidence_result.v3');assert modec['result_status']=='full_success'
  summary={'scenario':key,'status':'PASS','targets':matrix['scenarios'][key]['targets'],'capability':matrix['scenarios'][key]['capabilities'][0],'executor':matrix['scenarios'][key]['executors'][0],'attempts':len(g.rows)-before,'Result_status':modec['result_status'],'Audit_lineage':'VERIFIED_BY_MODE_C','operation_count':len(result['dispatch_outcomes']),'artifact_count':len(inventory),'citation_count':len(modec['citation_references']),'result_hash':modec['result_hash'],'result_path':str(root/modec['canonical_result_reference']),'audit_path':str(root/modec['audit_reference']),'audit_sha256':sha(root/modec['audit_reference']),'authorization_id':info['authorization_id'],'plan_hash':info['plan_hash'],'authorization_hash':info['authorization_hash']}
  from gh5_review import review_scenario
  review_scenario(E,key,root,summary,result,modec,g.rows)
  write('scenario_g_i3_cash_flow.json' if key=='G' else 'scenario_h_official_eod.json',summary)
  summaries.append(summary);completed.append(key)
  if key=='G':g.g_passed=True
  print(json.dumps(summary),flush=True)
except BaseException as exc:
 code=getattr(exc,'code',None);code=code if isinstance(code,str) and len(code)<180 else str(exc) if isinstance(exc,(LiveHold,Denied,AssertionError)) and len(str(exc))<180 else type(exc).__name__;failure={'scenario':g.scenario,'failure_class':type(exc).__name__,'reason':code,'last_completed_new_scenario':completed[-1] if completed else None};print(json.dumps({'HOLD':failure,'requests':len(g.rows)}),flush=True)
finally:
 g.armed=False;g.blocked=True;g.save();consumed=L.exists();passed=not failure and completed==['G','H'];disposition='L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_5_TECHNICAL_PASS_READY_FOR_INDEPENDENT_REVIEW' if passed else 'L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_5_HOLD_'+g.scenario+('_TEMPORAL' if failure and 'temporal' in failure['reason'] else '_FUNCTIONAL') if consumed else 'L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_5_PREFLIGHT_BLOCKED'
 write('authority_consumption.json',{'authority_token':AUTH,'acceptance_id':ACCEPTANCE,'consumed':consumed,'state':'CONSUMED_NON_REUSABLE' if consumed else 'UNCONSUMED','latch_path':str(L),'latch_sha256':sha(L) if consumed else None,'consumed_at':g.started.isoformat().replace('+00:00','Z') if g.started else None,'previous_A5_authority':'CONSUMED_NON_REUSABLE'})
 write('live_window.json',{'state':'STOPPED' if consumed else 'NOT_STARTED','start':g.started.isoformat().replace('+00:00','Z') if g.started else None,'deadline':g.deadline.isoformat().replace('+00:00','Z') if g.deadline else None,'stopped_at':stamp(),'maximum_minutes':45})
 for key,name in [('G','scenario_g_i3_cash_flow.json'),('H','scenario_h_official_eod.json')]:
  if not (E/name).exists():write(name,{'scenario':key,'status':'HOLD' if failure and failure['scenario']==key else 'NOT_REACHED','attempts':sum(x['scenario']==key for x in g.rows),'Result_Audit':'NOT_FINALIZED','targets':matrix['scenarios'][key]['targets']})
 if not (E/'scenario_h_active_security_master_provenance.json').exists():write('scenario_h_active_security_master_provenance.json',{'status':'NOT_REACHED','offline_proof':'scenario_h_offline_projection.json'})
 write('network_accounting.json',{'A_F_new_requests':0,'G_TWSE':sum(x['scenario']=='G' and x['targets']==['TWSE:1101'] for x in g.rows),'G_TPEX':sum(x['scenario']=='G' and x['targets']==['TPEX:5347'] for x in g.rows),'H_TWSE':sum(x['scenario']=='H' and x['targets']==['TWSE:2330'] for x in g.rows),'H_TPEX':sum(x['scenario']=='H' and x['targets']==['TPEX:6488'] for x in g.rows),'G_total':sum(x['scenario']=='G' for x in g.rows),'H_total':sum(x['scenario']=='H' for x in g.rows),'GH_total':len(g.rows),'global_maximum':6,'automatic_retries':0,'manual_retries':0,'manual_probes':0,'diagnostic_probes':0,'Security_Master_requests':0,'calendar_requests':0,'DGPA_requests':0,'NCDR_requests':0,'non_GH_external_requests':0,'guard_denials':g.denials})
 write('transport_outcome_matrix.json',{'requests':g.rows,'failure':failure});write('contract_outcome_matrix.json',{'new_completed':summaries,'failure':failure,'observer_results':observed})
 write('composite_a_to_h_acceptance_matrix.json',{'A_F':'CARRIED_FORWARD_PASS_IMMUTABLE','G':'NEW_LIVE_PASS' if 'G' in completed else 'NEW_LIVE_HOLD','H':'NEW_LIVE_PASS' if 'H' in completed else 'NOT_REACHED' if 'G' not in completed else 'NEW_LIVE_HOLD','composite_PASS':passed})
 write('gap_closure_matrix.json',{'L7-GAP-15':'TECHNICALLY_CLOSED_PENDING_INDEPENDENT_REVIEW' if passed else 'OPEN'});write('exit_criteria_matrix.json',{'L7-EXIT-19':'TECHNICAL_PASS_PENDING_INDEPENDENT_REVIEW' if passed else 'NOT_PASS','A6_A7_claims':False})
 write('final_review.json',{'disposition':disposition,'failure':failure,'new_completed_scenarios':completed,'A_F':'CARRIED_FORWARD_ONLY','new_authority':'CONSUMED_NON_REUSABLE' if consumed else 'UNCONSUMED','requests':len(g.rows),'previous_A5_authority':'CONSUMED_NON_REUSABLE','Owner_final_acceptance':False,'STOP':True})
 print(json.dumps({'disposition':disposition,'requests':len(g.rows),'completed':completed,'failure':failure}),flush=True)
