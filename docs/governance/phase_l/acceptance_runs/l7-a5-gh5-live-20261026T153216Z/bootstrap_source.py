from pathlib import Path
R=Path(r'C:\twmarket_temp\l7-a5\repo')
assert Path.cwd().resolve()==R.resolve()
import os,sys,json,hashlib,datetime,subprocess
B=Path(r'C:\twmarket_temp\l7-a5-current-authorities');T=B/'temp';O=B/'evidence/20261026T120000Z-l7-a5-gh-bounded-live-recertification-2-r4';OLD3=B/'evidence/20261026T144120Z-l7-a5-gh-temporal-provenance-live-recertification-3'
sys.path[:]=[str(R),*[x for x in sys.path if Path(x).drive.upper()!='D:']]
for k in list(os.environ):
 if k.startswith(('TW_MARKET_','M8R_06_03_')) or k in {'PYTHONPATH','A6_SESSION_ROOT'} or k.lower() in {'http_proxy','https_proxy','all_proxy'}:os.environ.pop(k,None)
os.environ.update(PATH=r'C:\Program Files\Git\cmd;C:\Windows\System32;C:\Windows',TW_MARKET_HOME=str(B/'home'),TW_MARKET_STATE_ROOT=str(B/'state'),LOCALAPPDATA=str(T/'isolated-localappdata'),TEMP=str(T),TMP=str(T),PYTHONDONTWRITEBYTECODE='1',NO_PROXY='*')
net=[]
def deny(e,a):
 if e.startswith('socket.'):net.append(e);raise RuntimeError('GH4_OFFLINE_NETWORK_DENIED')
 if e=='open' and isinstance(a[0],(str,bytes)):
  p=os.fsdecode(a[0]);assert Path(p).drive.upper()!='D:'
  assert not ('\\users\\' in p.lower() and '\\tw-market' in p.lower())
sys.addaudithook(deny)
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
canon=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify(p,d,n):
 m=load(p/'manifest.json');v=dict(m);assert v.pop('self_digest')==d and hashlib.sha256(canon(v)).hexdigest()==d and m['member_count']==n
 for a in m['members']:assert sha(p/a['path'])==a['sha256'] and (p/a['path']).stat().st_size==a['bytes']
 return {'path':str(p),'member_count':n,'member_mismatches':0,'self_digest':d}
git=lambda *a:subprocess.check_output(['C:/Program Files/Git/cmd/git.exe',*a],cwd=R,text=True).strip()
H='1d87d2b9301e7caf5976fcf4cd0b8ebc98866942';TR='843d11de216924ea16fce39e38bdd5248295211c';PA='cf90c697665e24b8bd5700bf8c033b102f1364e0';BR='phase-l/l7-a5-r5-temporal-provenance-repair'
assert git('rev-parse','HEAD')==H and git('rev-parse','HEAD^{tree}')==TR and git('rev-parse','HEAD^')==PA and git('branch','--show-current')==BR and not git('diff','--name-only') and not git('diff','--cached','--name-only')
E=B/'evidence'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-l7-a5-gh-temporal-provenance-live-recertification-5');E.mkdir();(T/'gh5-run-path.txt').write_text(str(E),encoding='utf-8')
def write(n,v):(E/n).write_bytes(canon(v))
AUTH='USER_CHAT_2026-10-26_L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_AUTHORIZATION_5';ID='L7-A5-GH-20261026-LIVE-RECERT-05'
write('owner_authority.json',{'authority_token':AUTH,'acceptance_id':ID,'starting_state':'UNCONSUMED','scope':['G','H'],'window_minutes':45,'retry':0,'global_ceiling':6,'consolidated_disposition':'L7_A5_R5_R5_1_R5_2_CONSOLIDATED_INDEPENDENT_REVIEW_PASS'})
write('entry_identity.json',{'branch':BR,'HEAD':H,'tree':TR,'parent':PA,'tracked_worktree':'CLEAN','process_cwd':str(Path.cwd()),'status':git('status','--short').splitlines()})
old=verify(OLD3,'752b72883d4e2c9f1472771cf53f713c0e5bc066e1e1e1a104fc45dc521cbc0f',46);assert not (B/'logs/l7-a5-gh-20261026-live-recert-03-consumption-latch.json').exists();old.update(state='RETIRED_UNCONSUMED',disposition='PREFLIGHT_BLOCKED',requests=0);write('gh3_retired_unconsumed_binding.json',old)
OLD4=B/'evidence/20261026T151209Z-l7-a5-gh-temporal-provenance-live-recertification-4'
old4=verify(OLD4,'8975c4ede3b343ee56e11893b6e69bea26e6e2cc6f26bf8aeb3b08b9e0bf6977',52);assert not (B/'logs/l7-a5-gh-20261026-live-recert-04-consumption-latch.json').exists();old4.update(state='RETIRED_UNCONSUMED',disposition='PREFLIGHT_BLOCKED',requests=0);write('gh4_retired_unconsumed_binding.json',old4)
V=R/'docs/governance/phase_l/acceptance_runs'
write('r5_r5_1_binding.json',verify(V/'l7-a5-r5-1-cas-schema-gate-20261026T132528Z','afe11605254b2a82f3e6bde3f2f0f55564c3017a8a69e3003e9e81d944a5bfc1',31))
write('r5_2_binding.json',verify(V/'l7-a5-r5-2-windows-encoding-portability-20261026T141355Z','5e0cd3f561a34dc9f4040edaa51a0e0326838201e0837bf46174a20b59e3257d',26))
schemas={'cash_institutional_flow_context_evidence.v2.schema.json':'d33a2b23300ec6e910cf5ca0c6d438bffbed8fc082f1819bd46cbe4113c14d4f','unified_market_evidence_result.v3.schema.json':'700e13779757300699e6cf4dd2c81768dbd56eb853befc9f9cf218102b6a7b3a'}
for p,d in schemas.items():assert sha(R/'schemas'/p)==d
write('schema_identity.json',schemas)
from scripts.m8r_05b_02.validator import _schema
s=_schema();assert isinstance(s,dict) and Path('schemas/unified_market_evidence_execution_authorization.v1.schema.json').is_file();assert not Path(r'C:\twmarket_temp\schemas\unified_market_evidence_execution_authorization.v1.schema.json').exists()
write('cwd_schema_resolution_proof.json',{'cwd':str(Path.cwd()),'exists':True,'authorization_schema_load':'PASS','schema_sha256':sha(R/'schemas/unified_market_evidence_execution_authorization.v1.schema.json'),'historical_GH3_wrong_cwd_path_exists':False,'external_requests':len(net)})
write('cwd_preflight.json',{'status':'PASS','required_cwd':str(R),'actual_cwd':str(Path.cwd()),'auto_chdir':False})
C=B/'evidence/20261026T113130Z-l7-a5-current-composite-closure-authority-2';write('composite_closure_authority_binding.json',verify(C,'10bf586b05a9fb9192d8c344d4660cae970d1bacbbef454885efb4c8678e25ea',28))
cal=load(C/'accepted_calendar_binding.json');assert sha(Path(cal['path']))==cal['raw_sha256']=='f8a2e6908cda1595587d29f4eb3c8fd66a11104b9f41558c1d4735243141883a';assert cal['normalized_sha256']=='28c07f487c120a26c5b7c4cef1c74542880c85827b91878662dcfc88e2be9ca8';write('calendar_binding.json',cal)
# Canonical Security Master loading and exact target resolution; no projection until packages validate.
p=(T/'prepare_gh2_r4_corrected.py').read_text(encoding='utf-8');p=p[p.index('from scripts.m8r_05c.canonical'):]
a=p.index('from scripts.m8r_08g_security_master_releases');b=p.index('proj={}')
exec(p[a:b])
P=B/'evidence/20261026T050344Z-l7-a5-bounded-live-release-acceptance-r2-e1-zulu-corrected'
carry=p[:a].replace("write('r4_gate_binding.json',{'evidence':r3,'reuse_only':True})",'');exec(carry)
write('previous_a5_hold_binding.json',verify(P,'ded3309cadca846519400f6c7630d153ff100fd54ffccce447c34c483a3830f0',73))
write('a_to_f_carry_forward_binding.json',load(E/'carried_forward_a_to_f_acceptance_binding.json'))
frozen=load(C/'resolver_positive_proof.json')['result'];assert frozen['resolved_source_trade_date']=='2026-10-22'
assert sha(C/'i3_composite_closure_authority.json')=='c7c6c4d3d6db4b38fbd0498d8d82ed3fcff53b99d5e7bfeba662328f8d22464a'
write('i3_source_date_binding.json',{'resolved_source_trade_date':'2026-10-22','accepted_frozen_binding':frozen,'calendar_path':cal['path'],'closure_path':str(C/'i3_composite_closure_authority.json'),'closure_sha256':sha(C/'i3_composite_closure_authority.json'),'calendar_raw_sha256':cal['raw_sha256'],'calendar_normalized_sha256':cal['normalized_sha256']})
m=load(O/'frozen_gh_matrix.json');m.update(authority=AUTH,acceptance_id=ID,HEAD=H,tree=TR);write('frozen_gh_matrix.json',m);write('scenario_matrix.json',m)
for n in ['live_allowlist.json','live_budget.json']:write(n,load(O/n))
from server.services.unified_mode_b1 import build_mode_b1_preview
pre={}
for k,scope in m['scenarios'].items():
 req={'schema_version':'unified_market_evidence_request.v3','request_id':E.name+'-'+k,'execution_mode':'preview','targets':[{'input':x.split(':')[1],'market_hint':x.split(':')[0]} for x in scope['targets']],'data_needs':[{'type':scope['capabilities'][0],'priority':'required'}]};pre[k]={'request':req,'preview':build_mode_b1_preview(req)}
write('offline_gh_previews.json',pre)
g=(O/'runner_guard_source.py').read_text(encoding='utf-8').replace('USER_CHAT_2026-10-26_L7_A5_GH_BOUNDED_LIVE_RECERTIFICATION_AUTHORIZATION_2',AUTH).replace('LIVE-RECERT-02','LIVE-RECERT-05').replace('350db05c2e2a9bdd3e6325a2a43bbc4906846986',H).replace('6feb5d6428dfe13e918dbab8e67e633353348864',TR)
(E/'runner_guard_source.py').write_text(g,encoding='utf-8')
t=(T/'test_gh2_guard.py').read_text(encoding='utf-8').replace('gh2-r4-run-path.txt','gh5-run-path.txt').replace('.read_text()',".read_text(encoding='utf-8')")
t="from pathlib import Path\nR=Path(r'C:\\twmarket_temp\\l7-a5\\repo')\nassert Path.cwd().resolve()==R.resolve()\n"+t
for name,tok in [('old_GH2','USER_CHAT_2026-10-26_L7_A5_GH_BOUNDED_LIVE_RECERTIFICATION_AUTHORIZATION_2'),('retired_GH3','USER_CHAT_2026-10-26_L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_AUTHORIZATION_3')]:
 t=t.replace("for field in ['authority_token'",f"reject('{name}',lambda g,b,k:b.update(authority_token='{tok}'))\nfor field in ['authority_token'")
(E/'guard_tests_source.py').write_text(t,encoding='utf-8')

g=(E/'runner_guard_source.py').read_text(encoding='utf-8')
g=g.replace("'HEAD':HEAD,'tree':TREE}","'HEAD':HEAD,'tree':TREE,'cwd':r'C:\\twmarket_temp\\l7-a5\\repo'}")
g=g.replace("'mutable_root':str(self.root),**self.context}","'mutable_root':str(self.root),'cwd':str(Path.cwd()),**self.context}")
(E/'runner_guard_source.py').write_text(g,encoding='utf-8')
t=(E/'guard_tests_source.py').read_text(encoding='utf-8')
for name,tok in [('retired_GH4','USER_CHAT_2026-10-26_L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_AUTHORIZATION_4')]:
 t=t.replace("for field in ['authority_token'",f"reject('{name}',lambda g,b,k:b.update(authority_token='{tok}'))\nfor field in ['authority_token'")
t=t.replace("for field in ['authority_token','acceptance_id'", "for field in ['cwd','authority_token','acceptance_id'")
t=t.replace("reject('wrong_path'", "reject('diagnostic_probe',lambda g,b,k:k.update(url='https://www.twse.com.tw/diagnostic'))\nreject('Security_Master_refresh',lambda g,b,k:k.update(url='https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'))\nreject('calendar_refresh',lambda g,b,k:k.update(url='https://www.twse.com.tw/holidaySchedule/holidaySchedule'))\nreject('closure_refresh',lambda g,b,k:k.update(url='https://www.dgpa.gov.tw/'))\nreject('wrong_path'")
(E/'guard_tests_source.py').write_text(t,encoding='utf-8')

OLD4=B/'evidence/20261026T151209Z-l7-a5-gh-temporal-provenance-live-recertification-4'
p=(OLD4/'gh_live_runner_source.py').read_text(encoding='utf-8').replace('gh4-run-path.txt','gh5-run-path.txt').replace('live-recert-04','live-recert-05').replace('gh4_review','gh5_review').replace('RECERTIFICATION_4','RECERTIFICATION_5')
# Remove the forward dependency entirely; place it ONLY inside live branch.
p=p.replace("assert load(E/'runner_guard_offline_tests.json')['status']=='PASS'\n",'')
# Deny network before importing any repository module during offline modes.
mark='from scripts import m8r_06_03_production_adapter as product'
p=p.replace(mark,"offline_attempts=[]\ndef offline_entry(event,args):\n if ('--prepare' in sys.argv or '--guard' in sys.argv) and event.startswith('socket.'):\n  offline_attempts.append(event);raise RuntimeError('GH5_OFFLINE_NETWORK_DENIED')\nsys.addaudithook(offline_entry)\n"+mark)
# Final prepare-only projection; no dependency on guard/checkpoint/latch output.
projection="""proj={}
 for market,code in [('TWSE','2330'),('TPEX','6488')]:
  row=next(iter(product._official_eod_security_master_projection(market,[code]).values()))
  assert row['coverage_mode']=='canonical_security_master' and row['classification_status']=='classified' and row['production_classification_completeness']=='complete' and row['release_id']==service.release_id and row['release_manifest_sha256']==service.manifest_hash and row['execution_eligibility']['status']=='allowed'
  proj[market+':'+code]=row
 write('scenario_h_offline_projection.json',{'status':'PASS','projections':proj,'bounded_seed_only':False,'external_requests':0})
 write('prepare_phase_result.json',{'status':'PASS','packages':packages,'claims':0,'receipts':0,'external_requests':len(attempts)+len(offline_attempts),'phase_dependencies':['immutable entry inputs'],'guard_output_required':False,'checkpoint_required':False})
 """
p=p.replace("print(json.dumps({'fresh_packages':2",projection+"print(json.dumps({'fresh_packages':2")
# Add an explicit GUARD mode after prepare exits, before any live dependency reads.
guard_branch="""if '--guard' in sys.argv:
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

"""
p=p.replace("assert '--live-once' in sys.argv",guard_branch+"assert '--live-once' in sys.argv, 'explicit phase required'\nassert load(E/'prepare_phase_result.json')['status']=='PASS'\nassert load(E/'guard_phase_result.json')['status']=='PASS'\nassert load(E/'runner_guard_offline_tests.json')['status']=='PASS'")
# Bind both retired runs in authorization input and durable latch.
p=p.replace("'R5_2_evidence':load(E/'r5_2_binding.json')", "'R5_2_evidence':load(E/'r5_2_binding.json'),'GH3_retired':load(E/'gh3_retired_unconsumed_binding.json'),'GH4_retired':load(E/'gh4_retired_unconsumed_binding.json')")
p=p.replace("GH3_historical_state='RETIRED_UNCONSUMED',", "GH3_historical_state='RETIRED_UNCONSUMED',GH4_historical_state='RETIRED_UNCONSUMED',")
p=p.replace("'final_pre_network_checkpoint.json']", "'final_pre_network_checkpoint.json','guard_tests_source.py','gh3_retired_unconsumed_binding.json','gh4_retired_unconsumed_binding.json']")
# No provisional PASS summary persisted until temporal and lineage checks complete.
old="write('scenario_g_i3_cash_flow.json' if key=='G' else 'scenario_h_official_eod.json',summary);\n  from gh5_review"
p=p.replace(old,"from gh5_review")
p=p.replace("review_scenario(E,key,root,summary,result,modec,g.rows)\n  summaries", "review_scenario(E,key,root,summary,result,modec,g.rows)\n  write('scenario_g_i3_cash_flow.json' if key=='G' else 'scenario_h_official_eod.json',summary)\n  summaries")
# Source must be parsable and phase graph inspectable before any preparation.
compile(p,str(E/'gh_live_runner_source.py'),'exec')
(E/'gh_live_runner_source.py').write_text(p,encoding='utf-8')
review=(OLD4/'gh4_review.py').read_text(encoding='utf-8')
(E/'gh5_review.py').write_text(review,encoding='utf-8')
# Preserve the exact bootstrap including dependencies used by its deterministic exec blocks.
(E/'bootstrap_source.py').write_bytes(Path(__file__).read_bytes())
(E/'prior_prerequisite_inspection_source.py').write_bytes((T/'prepare_gh2_r4_corrected.py').read_bytes())
write('offline_initial_verification.json',{'status':'PASS','external_requests':len(net),'cwd':str(Path.cwd()),'HEAD':H,'tree':TR})
print(str(E))
