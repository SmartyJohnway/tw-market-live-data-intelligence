from pathlib import Path
R=Path(r'C:\twmarket_temp\l7-a5\repo')
assert Path.cwd().resolve()==R.resolve()
import sys,json,datetime,http.client,ssl
from pathlib import Path
B=Path(r'C:\twmarket_temp\l7-a5-current-authorities');E=Path((B/'temp/gh5-run-path.txt').read_text(encoding='utf-8'));sys.path.insert(0,str(E))
def no_net(e,a):
 if e.startswith('socket.'):raise RuntimeError('GH_guard_tests_hard_network_deny')
sys.addaudithook(no_net)
from runner_guard_source import *
m=json.loads((E/'frozen_gh_matrix.json').read_text(encoding='utf-8'));T=B/'temp'/('gh-guard-tests-'+E.name.split('-l7-')[0]);T.mkdir(exist_ok=True);tests=[]
def make(s='G'):
 p=T/str(len(list(T.iterdir())));p.mkdir();g=Guard(p,m,simulate=True);g.scenario=s;g.g_passed=(s=='H');expiry=(now()+datetime.timedelta(hours=1)).isoformat().replace('+00:00','Z');g.authorizations={k:{'authorization_id':'offline-'+k,'authorization_hash':'a'*64,'plan_hash':'b'*64,'expires_at':expiry} for k in 'GH'};g.context={'targets':['TWSE:1101' if s=='G' else 'TWSE:2330'],'capability':m['scenarios'][s]['capabilities'][0],'executor':m['scenarios'][s]['executors'][0],'operation_ids':['OFFLINE_ONLY'],**g.authorizations[s]};return g

def reject(name,change,s='G'):
 g=make(s);b=g.binding();kw={};change(g,b,kw);url=kw.pop('url',m['scenarios'][s]['market_routes']['TWSE'][0])
 try:g.validate(b,url,**kw)
 except Denied as e:tests.append({'case':name,'status':'PASS','reason':str(e),'external_dispatches':0});return
 raise AssertionError(name)
reject('old_A5_authority',lambda g,b,k:b.update(authority_token='USER_CHAT_2026-10-25_PHASE_L_L7_A5_BOUNDED_LIVE_RELEASE_ACCEPTANCE_AUTHORIZATION'))
reject('old_GH1_authority',lambda g,b,k:b.update(authority_token='USER_CHAT_2026-10-26_L7_A5_GH_BOUNDED_LIVE_RECERTIFICATION_AUTHORIZATION_1'))
reject('old_GH2',lambda g,b,k:b.update(authority_token='USER_CHAT_2026-10-26_L7_A5_GH_BOUNDED_LIVE_RECERTIFICATION_AUTHORIZATION_2'))
reject('retired_GH3',lambda g,b,k:b.update(authority_token='USER_CHAT_2026-10-26_L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_AUTHORIZATION_3'))
reject('retired_GH4',lambda g,b,k:b.update(authority_token='USER_CHAT_2026-10-26_L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_AUTHORIZATION_4'))
for field in ['cwd','authority_token','acceptance_id','HEAD','tree','targets','capability','executor','authorization_id','authorization_hash','plan_hash']:
 reject('wrong_'+field,lambda g,b,k,f=field:b.update({f:['TWSE:9999'] if f=='targets' else 'INVALID'}))
for s in 'ABCDEF':reject('forbidden_scenario_'+s,lambda g,b,k,s=s:b.update(scenario=s))
for s in 'GH':
 for field in ['targets','capability','executor']:reject('wrong_'+s+'_'+field,lambda g,b,k,f=field:b.update({f:['TWSE:9999'] if f=='targets' else 'INVALID'}),s=s)
reject('wrong_host',lambda g,b,k:k.update(url='https://example.invalid/rwd/zh/fund/T86?date=20261022&selectType=ALLBUT0999&response=json'))
reject('diagnostic_probe',lambda g,b,k:k.update(url='https://www.twse.com.tw/diagnostic'))
reject('Security_Master_refresh',lambda g,b,k:k.update(url='https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'))
reject('calendar_refresh',lambda g,b,k:k.update(url='https://www.twse.com.tw/holidaySchedule/holidaySchedule'))
reject('closure_refresh',lambda g,b,k:k.update(url='https://www.dgpa.gov.tw/'))
reject('wrong_path',lambda g,b,k:k.update(url='https://www.twse.com.tw/other'))
reject('wrong_method',lambda g,b,k:k.update(method='POST'))
reject('wrong_query_date',lambda g,b,k:k.update(url=m['scenarios']['G']['market_routes']['TWSE'][0].replace('20261022','20261021')))
reject('wrong_market_source',lambda g,b,k:k.update(url=m['scenarios']['G']['market_routes']['TPEX'][0]))
reject('manual_retry',lambda g,b,k:k.update(manual_retry=True));reject('automatic_retry',lambda g,b,k:k.update(automatic_retry=True))
reject('unauthorized_fallback',lambda g,b,k:k.update(url='https://openapi.twse.com.tw/v1/fund/T86'))
reject('redirect_expansion',lambda g,b,k:k.update(redirect=True))
reject('G_request_3',lambda g,b,k:g.rows.extend([{'scenario':'G'}]*2))
reject('H_request_5',lambda g,b,k:g.rows.extend([{'scenario':'H'}]*4),s='H')
reject('global_request_7',lambda g,b,k:g.rows.extend([{'scenario':'OTHER'}]*6))
reject('expired_window',lambda g,b,k:setattr(g,'deadline',now()-datetime.timedelta(seconds=1)))
reject('expired_authorization',lambda g,b,k:g.authorizations['G'].update(expires_at=(now()-datetime.timedelta(seconds=1)).isoformat().replace('+00:00','Z')))
reject('authorization_expires_mid_window',lambda g,b,k:g.authorizations['H'].update(expires_at=(now()+datetime.timedelta(minutes=20)).isoformat().replace('+00:00','Z')))
reject('D_mutable_root',lambda g,b,k:b.update(mutable_root='D:\\forbidden'))
reject('production_LOCALAPPDATA',lambda g,b,k:b.update(mutable_root=r'C:\Users\forbidden\AppData\Local\TW-Market'))
reject('H_before_G_success',lambda g,b,k:setattr(g,'g_passed',False),s='H')
for s in 'GH':
 g=make(s);g.validate(g.binding(),m['scenarios'][s]['market_routes']['TWSE'][0]);tests.append({'case':'valid_'+s+'_binding','status':'PASS','external_dispatches':0})
# Exercise actual HTTP interception against a fake send, with hard socket deny still active.
g=make();g.armed=True;calls=[]
def fake(conn,*args,**kwargs):
 assert g.latch.exists() and g.reservations.exists() and g.rows[-1]['actual_dispatch_timestamp'];calls.append(True)
http.client.HTTPConnection.request=fake;g.install();conn=http.client.HTTPSConnection('www.twse.com.tw');url='/rwd/zh/fund/T86?date=20261022&selectType=ALLBUT0999&response=json';conn.request('GET',url);assert len(calls)==1
try:conn.request('GET',url);raise AssertionError('retry allowed')
except Denied:assert len(calls)==1
ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE;bad=http.client.HTTPSConnection('www.twse.com.tw',context=ctx)
try:bad.request('GET',url);raise AssertionError('unverified TLS allowed')
except Denied:assert len(calls)==1
tests.extend([{'case':'durable_synthetic_latch_and_reservation_before_fake_send','status':'PASS','external_dispatches':0},{'case':'failed_reservation_no_additional_fake_send','status':'PASS','external_dispatches':0},{'case':'unsafe_TLS_rejected_before_send','status':'PASS','external_dispatches':0}])
result={'status':'PASS','passed':len(tests),'failed':0,'external_network_attempts':0,'real_GH_consumption_latch_created':False,'tests':tests};durable(E/'runner_guard_offline_tests.json',result);durable(E/'runner_guard_hash.json',{'sha256':sha(E/'runner_guard_source.py'),'frozen_before_live':True,'guard_suite_passed':len(tests)});print(json.dumps({'guard_tests':len(tests),'failed':0,'network_attempts':0}))
