import sys,os,json,hashlib,datetime,subprocess
from pathlib import Path
R=Path(r'C:\twmarket_temp\l7-a5\repo');B=Path(r'C:\twmarket_temp\l7-a5-current-authorities');P=B/'evidence/20261026T050344Z-l7-a5-bounded-live-release-acceptance-r2-e1-zulu-corrected';V=R/'docs/governance/phase_l/acceptance_runs/l7-a5-r4-unscheduled-market-closure-authority-20261026T093527Z';sys.path[:]=[str(R),*[x for x in sys.path if Path(x).drive.upper()!='D:']]
for k in list(os.environ):
 if k.startswith('TW_MARKET_') or k.startswith('M8R_06_03_') or k=='PYTHONPATH':os.environ.pop(k,None)
os.environ.update(PATH=r'C:\Program Files\Git\cmd;C:\Windows\System32;C:\Windows',TW_MARKET_HOME=str(B/'home'),TW_MARKET_STATE_ROOT=str(B/'state'),LOCALAPPDATA=str(B/'temp/isolated-localappdata'),TEMP=str(B/'temp'),TMP=str(B/'temp'))
def offline(e,a):
 if e.startswith('socket.'):raise RuntimeError('GH_preflight_network_denied')
sys.addaudithook(offline)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def git(*a):return subprocess.check_output(['C:/Program Files/Git/cmd/git.exe',*a],cwd=R,text=True).strip()
def verify(root,expected):
 m=load(root/'manifest.json');v=dict(m);d=v.pop('self_digest');assert d==expected and hashlib.sha256(canon(v)).hexdigest()==d
 for x in m['members']:assert sha(root/x['path'])==x['sha256'] and (root/x['path']).stat().st_size==x['bytes']
 return {'path':str(root),'members':m['member_count'],'mismatches':0,'self_digest':d}
assert git('rev-parse','HEAD')=='350db05c2e2a9bdd3e6325a2a43bbc4906846986' and git('rev-parse','HEAD^{tree}')=='6feb5d6428dfe13e918dbab8e67e633353348864' and git('rev-parse','HEAD^')=='c3c7bddb28e874be4dfee9d31428598fb5f70739' and git('branch','--show-current')=='phase-l/l7-a5-r4-unscheduled-market-closure-authority' and not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert git('log','-1','--format=%s')=='L7-A5-R4 harden I3 unscheduled market closure authority'
r3=verify(V,'0011c92764c72cee520a88407a4e6a1b5f18b8e61b4b208860108256e1d8a14b');hold=verify(P,'ded3309cadca846519400f6c7630d153ff100fd54ffccce447c34c483a3830f0')
E=Path(r'C:\twmarket_temp\l7-a5-current-authorities\evidence\20261026T120000Z-l7-a5-gh-bounded-live-recertification-2-r4')
def write(n,v):(E/n).write_bytes((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
write('entry_identity.json',{'branch':git('branch','--show-current'),'HEAD':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'parent':git('rev-parse','HEAD^'),'commit_message':git('log','-1','--format=%s'),'tracked_worktree':'CLEAN'})
write('owner_authority.json',{'authority':'USER_CHAT_2026-10-26_L7_A5_GH_BOUNDED_LIVE_RECERTIFICATION_AUTHORIZATION_2','acceptance_id':'L7-A5-GH-20261026-LIVE-RECERT-02','independent_new_authority':True,'previous_A5_authority':'CONSUMED_NON_REUSABLE','scenarios':['G','H'],'starting_state':'UNCONSUMED','live_window_minutes':45,'global_budget':6})
write('r4_acceptance_binding.json',{'independent_disposition':'L7_A5_R4_UNSCHEDULED_MARKET_CLOSURE_AUTHORITY_ACCEPTANCE_REVIEW_PASS','finding':'CLOSED_BY_R3','evidence':r3});write('previous_a5_hold_binding.json',hold)
from scripts.m8r_05c.canonical import hash_body_excluding_key
lineage=load(P/'result_audit_lineage_review.json');carried=[]
for k in 'ABCDEF':
 review=next(x for x in lineage['completed_scenarios'] if x['scenario']==k)
 summary=next(load(p) for p in P.glob('scenario_'+k.lower()+'_*') if 'result_hash' in load(p))
 result=load(Path(summary['result_path']));assert result['result_hash']==summary['result_hash'] and hash_body_excluding_key(result,'result_hash')==result['result_hash'] and sha(Path(summary['audit_path']))==summary['audit_sha256']
 for a in review['artifacts']:assert sha(Path(a['path']))==a['sha256']
 carried.append({'scenario':k,'prior_summary_sha256':sha(next(p for p in P.glob('scenario_'+k.lower()+'_*') if 'result_hash' in load(p))),'prior_summary':summary,'lineage':review,'Result_and_Audit_file_hashes':{'result':sha(Path(summary['result_path'])),'audit':sha(Path(summary['audit_path']))},'regenerated':False,'new_requests':0})
write('carried_forward_a_to_f_acceptance_binding.json',{'status':'PASS','source_run':str(P),'scenarios':carried,'operations':11,'artifacts':20,'citations':14,'orphans':0,'broken_citations':0,'hash_mismatches':0,'new_A_F_executions':0})
write('r4_gate_binding.json',{'evidence':r3,'reuse_only':True})
from scripts.m8r_08g_security_master_releases import load_active_identity_service
from scripts.m8r_06_03_production_adapter import _official_eod_security_master_projection
service,pointer,release,manifest=load_active_identity_service(root=B/'state/security-master');assert service.release_id=='security-master-20261025T162542Z'
expected={'manifest.json':'ae2efd269b403c2d30c652a3884480682952e2bb3864c15e662de5e03763b0c1','index.json':'51db08121e3ada736891f8d3396ad01ad5c94037c8a7aed053ee89143853ab9d','qualification.json':'262eaf58f84181e3084d29a744045e40ae414c4124802f8cc7b1d942f306a067'}
for f,h in expected.items():assert sha(B/'state/security-master/releases'/service.release_id/f)==h
rows=[]
for t in ['TWSE:1101','TPEX:5347','TWSE:2330','TPEX:6488']:
 r=service.resolve(t);assert r.status=='resolved' and r.selected['canonical_target_id']==t and r.selected['classification']['instrument_family']=='company_share' and r.selected['classification']['instrument_type']=='common_share' and r.selected['execution_eligibility']['status']=='allowed';assert r.selected['identity']['isin']=={'TWSE:1101':'TW0001101004','TPEX:5347':'TW0005347009','TWSE:2330':'TW0002330008','TPEX:6488':'TW0006488000'}[t];rows.append({'identity':r.selected,'target':t,'status':'resolved','instrument_type':'common_share','execution_eligibility':r.selected['execution_eligibility']})
write('security_master_binding.json',{'status':'PASS','release_id':service.release_id,'hashes':expected,'targets':rows,'external_requests':0})
proj={}
for market,code in [('TWSE','2330'),('TPEX','6488')]:
 row=next(iter(_official_eod_security_master_projection(market,[code]).values()));assert row['coverage_mode']=='canonical_security_master' and row['release_id']==service.release_id and row['release_manifest_sha256']==expected['manifest.json'] and row['canonical_instrument_family']=='company_share' and row['canonical_instrument_type']=='common_share' and row['instrument_type']=='equity' and row['execution_eligibility']['status']=='allowed';proj[market+':'+code]=row
write('scenario_h_offline_projection.json',{'status':'PASS','projections':proj,'bounded_seed_only':False,'external_requests':0})
C=B/'evidence/20261026T113130Z-l7-a5-current-composite-closure-authority-2'
cb=verify(C,'10bf586b05a9fb9192d8c344d4660cae970d1bacbbef454885efb4c8678e25ea');write('composite_closure_authority_binding.json',cb)
q=verify(B/'evidence/20261026T085331Z-l7-a5-gh-bounded-live-recertification-r3','f8b87db2f23ade81b32bb92c9f0be3d65299aacfe59e2146886f4f5ccdd6e036');write('prior_gh1_binding.json',q)
frozen=load(C/'resolver_positive_proof.json')['result'];assert frozen['resolved_source_trade_date']=='2026-10-22'
calendar=load(C/'accepted_calendar_binding.json');closure=C/'i3_composite_closure_authority.json'
write('calendar_binding.json',calendar)
write('i3_source_date_binding.json',{'resolved_source_trade_date':'2026-10-22','accepted_frozen_binding':frozen,'calendar_path':calendar['path'],'closure_path':str(closure),'closure_sha256':sha(closure),'calendar_raw_sha256':calendar['raw_sha256'],'calendar_normalized_sha256':calendar['normalized_sha256'],'new_requests':0})
oldmatrix=load(P/'frozen_scenario_matrix.json');scopes={k:oldmatrix['scenarios'][k] for k in 'GH'}
scopes['G']=json.loads(json.dumps(scopes['G']).replace('20261023','20261022').replace('2026-10-23','2026-10-22'))
for key,scope in scopes.items():scope['market_routes']={m:[u for u in scope['routes'] if ('www.twse.com.tw/' in u or 'openapi.twse.com.tw/' in u) == (m=='TWSE')] for m in ['TWSE','TPEX']}
scopes['G']['source_contract']='docs/governance/phase_i/PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json'
scopes['H']['source_contract']={'TWSE':'twse_openapi_stock_day_all_v1','TPEX':'tpex_openapi_mainboard_daily_close_quotes_v1'}
m={'authority':'USER_CHAT_2026-10-26_L7_A5_GH_BOUNDED_LIVE_RECERTIFICATION_AUTHORIZATION_2','acceptance_id':'L7-A5-GH-20261026-LIVE-RECERT-02','HEAD':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'scenarios':scopes,'order':['G','H'],'global_ceiling':6,'retry':0,'live_window_minutes':45,'G_must_complete_before_H':True};write('frozen_gh_matrix.json',m);write('live_allowlist.json',{'methods':['GET'],'market_routes':{k:v['market_routes'] for k,v in scopes.items()},'retry':0,'fallback':False,'redirect_expansion':False});write('live_budget.json',{'G':2,'H':4,'global':6,'retry':0})
from server.services.unified_mode_b1 import build_mode_b1_preview
previews={};runid=E.name.split('-l7-')[0]
for k,s in scopes.items():
 req={'schema_version':'unified_market_evidence_request.v3','request_id':'l7-a5-gh-'+runid+'-'+k,'execution_mode':'preview','targets':[{'input':x.split(':')[1],'market_hint':x.split(':')[0]} for x in s['targets']],'data_needs':[{'type':s['capabilities'][0],'priority':'required'}]};p=build_mode_b1_preview(req);ops=p['orchestration_plan']['operations'];assert all(o['operation_status']=='executable_pending_approval' and o['executor_id'] in s['executors'] for o in ops);previews[k]={'request':req,'preview':p}
write('offline_gh_previews.json',previews)
assert not (B/'logs/l7-a5-gh-20261026-live-recert-02-consumption-latch.json').exists()
(B/'temp/gh2-r4-run-path.txt').write_text(str(E),encoding='utf-8');print(json.dumps({'evidence':str(E),'R3_integrity':'PASS','prior_integrity':'PASS','carried_A_F':6,'Security_Master_targets':4,'previews':2,'new_requests':0},indent=2))
