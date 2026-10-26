"""Acceptance-local new GH authority observer/guard. No provider transport or product semantics are replaced."""
from __future__ import annotations
import copy,datetime,hashlib,http.client,json,os,ssl,sys
from pathlib import Path,PureWindowsPath
from urllib.parse import urlsplit,parse_qsl,urljoin
AUTH='USER_CHAT_2026-10-26_L7_A5_GH_TEMPORAL_PROVENANCE_LIVE_RECERTIFICATION_AUTHORIZATION_5'
ACCEPTANCE='L7-A5-GH-20261026-LIVE-RECERT-05'
HEAD='1d87d2b9301e7caf5976fcf4cd0b8ebc98866942';TREE='843d11de216924ea16fce39e38bdd5248295211c'
def now():return datetime.datetime.now(datetime.timezone.utc)
def stamp():return now().isoformat().replace('+00:00','Z')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def durable(path,value,exclusive=False):
 with path.open('xb' if exclusive else 'wb') as f:f.write(canonical(value)+b'\n');f.flush();os.fsync(f.fileno())
class Denied(RuntimeError):pass
class LiveHold(BaseException):pass
class Guard:
 def __init__(self,root,matrix,*,simulate=False):
  self.root=Path(root);self.matrix=matrix;self.simulate=simulate;self.rows=[];self.scenario='G';self.g_passed=False;self.authorizations={};self.context={};self.source_id=None;self.seen=set();self.armed=False;self.started=None;self.deadline=None;self.io=False;self.current_row=None;self.frozen={};self.denials=[];self.blocked=False
  self.latch=self.root/('synthetic-offline-latch.json' if simulate else 'authority-consumption-latch.json');self.reservations=self.root/('synthetic-reservations.jsonl' if simulate else 'live-reservations.jsonl')
 def deny(self,code):self.denials.append(code);raise Denied(code)
 def validate_root(self,path):
  p=PureWindowsPath(str(path));bound=PureWindowsPath(r'C:\twmarket_temp')
  if not p.is_absolute() or not any(p.is_relative_to(PureWindowsPath(x)) for x in [r'C:\twmarket_temp\l7-a5',r'C:\twmarket_temp\l7-a5-current-authorities']) or '..' in p.parts:self.deny('mutable_root_outside_C_boundary')
 def validate(self,binding,url,method='GET',*,manual_retry=False,automatic_retry=False,redirect=False,at=None):
  expected={'authority_token':AUTH,'acceptance_id':ACCEPTANCE,'HEAD':HEAD,'tree':TREE,'cwd':r'C:\twmarket_temp\l7-a5\repo'}
  for k,v in expected.items():
   if binding.get(k)!=v:self.deny('binding_'+k)
  if self.blocked:self.deny('live_hold_already_latched')
  s=binding.get('scenario')
  if s!=self.scenario or s not in self.matrix['scenarios']:self.deny('scenario')
  if s=='H' and not self.g_passed:self.deny('H_requires_G_PASS')
  scope=self.matrix['scenarios'][s]
  if not binding.get('targets') or not set(binding['targets']).issubset(scope['targets']):self.deny('target')
  if binding.get('capability') not in scope['capabilities']:self.deny('capability')
  if binding.get('executor') not in scope['executors']:self.deny('executor')
  approved=self.authorizations.get(s)
  if not approved or any(binding.get(k)!=approved.get(k) for k in ['authorization_id','authorization_hash','plan_hash']):self.deny('authorization_binding')
  moment=at or now()
  for a in self.authorizations.values():
   expiry=datetime.datetime.fromisoformat(a['expires_at'].replace('Z','+00:00'))
   if moment>=expiry:self.deny('expired_authorization')
   if expiry<(self.deadline or moment+datetime.timedelta(minutes=45)):self.deny('authorization_expires_mid_window')
  if manual_retry or automatic_retry:self.deny('retry')
  self.validate_root(binding.get('mutable_root',''))
  if method!='GET':self.deny('method')
  u=urlsplit(url)
  if u.scheme!='https' or u.username or u.password or u.port not in (None,443) or u.fragment:self.deny('https_authority')
  markets={t.split(':',1)[0] for t in binding['targets']}
  if len(markets)!=1:self.deny('mixed_market_transport')
  market=next(iter(markets));routes=scope['market_routes'].get(market,[]);base=url.split('?',1)[0];matches=[x for x in routes if x.split('?',1)[0]==base]
  if not matches:self.deny('source_host_or_path')
  if base.endswith('/STOCK_DAY'):
   q=parse_qsl(u.query,keep_blank_values=True);d=dict(q)
   if len(q)!=3 or set(d)!={'response','date','stockNo'} or d['response']!='html' or d['stockNo']!='2330' or len(d['date'])!=8 or not d['date'].isdigit() or d['date'][6:]!='01':self.deny('query_shape')
   try:datetime.date(int(d['date'][:4]),int(d['date'][4:6]),1)
   except ValueError:self.deny('query_date')
  elif '?' in matches[0]:
   if sorted(parse_qsl(u.query))!=sorted(parse_qsl(urlsplit(matches[0]).query)) or len(parse_qsl(u.query))!=len(parse_qsl(urlsplit(matches[0]).query)):self.deny('query_shape')
  elif u.query:self.deny('query_shape')
  if redirect:self.deny('unauthorized_redirect')
  if self.deadline and (at or now())>=self.deadline:self.deny('expired_window')
  if len(self.rows)>=6:self.deny('global_ceiling')
  if sum(x['scenario']==s for x in self.rows)>=scope['ceiling']:self.deny('scenario_ceiling')
  key=(s,url,method)
  if key in self.seen:self.deny('duplicate_request_retry')
  return key
 def reserve(self,binding,url,method='GET'):
  key=self.validate(binding,url,method)
  if not self.armed:self.deny('not_armed')
  if not self.started:
   self.started=now();self.deadline=self.started+datetime.timedelta(minutes=45)
   body={**self.frozen,'authority_token':AUTH,'acceptance_id':ACCEPTANCE,'HEAD':HEAD,'tree':TREE,'state':'OFFLINE_SIMULATION' if self.simulate else 'CONSUMED','live_window_started_at':self.started.isoformat().replace('+00:00','Z'),'live_window_deadline':self.deadline.isoformat().replace('+00:00','Z'),'global_ceiling':6,'scenario_ceilings':{k:v['ceiling'] for k,v in self.matrix['scenarios'].items()}}
   if self.simulate:body['authority_token']='SYNTHETIC_OFFLINE_ONLY'
   durable(self.latch,body,exclusive=True)
  for filename,digest in self.frozen.get('frozen_files',{}).items():
   if sha(Path(filename))!=digest:self.deny('frozen_input_mutation')
  s=binding['scenario'];row={'global_sequence':len(self.rows)+1,'scenario':s,'scenario_request_sequence':sum(x['scenario']==s for x in self.rows)+1,'operation_ids':binding.get('operation_ids',[]),'capability':binding['capability'],'targets':binding['targets'],'executor':binding['executor'],'source_id':self.matrix['scenarios'][s]['source_ids'][binding['targets'][0].split(':',1)[0]],'observed_runtime_source_id':self.source_id,'source_contract':{'frozen_scenario':s,'authority':self.matrix['scenarios'][s]['source_contract'],'endpoint':url.split('?',1)[0]},'method':method,'canonical_url':url,'reservation_timestamp':stamp(),'actual_dispatch_timestamp':None,'HTTP_status':None,'redirect_count':0,'response_bytes':0,'response_SHA256':None,'transport_result':'RESERVED','contract_result':'NOT_YET_EVALUATED','retry':False}
  with self.reservations.open('ab') as f:f.write(canonical(row)+b'\n');f.flush();os.fsync(f.fileno())
  self.rows.append(row);self.seen.add(key);return row
 def binding(self):return {'authority_token':AUTH,'acceptance_id':ACCEPTANCE,'HEAD':HEAD,'tree':TREE,'scenario':self.scenario,'mutable_root':str(self.root),'cwd':str(Path.cwd()),**self.context}
 def save(self):durable(self.root/'live_request_ledger.json',{'requests':self.rows,'attempt_count':len(self.rows)})
 def install(self):
  guard=self;orig_request=http.client.HTTPConnection.request;orig_response=http.client.HTTPConnection.getresponse
  def request(conn,method,url,body=None,headers={},*,encode_chunked=False):
   if not isinstance(conn,http.client.HTTPSConnection):guard.deny('non_https_transport')
   ctx=getattr(conn,'_context',None)
   if not isinstance(ctx,ssl.SSLContext) or ctx.verify_mode!=ssl.CERT_REQUIRED or not ctx.check_hostname:guard.deny('unverified_TLS_forbidden')
   full=url if url.startswith('https://') else 'https://'+conn.host+((':'+str(conn.port)) if conn.port!=443 else '')+url
   row=guard.reserve(guard.binding(),full,method);conn._a5_row=row;guard.current_row=row;row['actual_dispatch_timestamp']=stamp();row['transport_result']='DISPATCHED';guard.save();guard.io=True
   try:return orig_request(conn,method,url,body,headers,encode_chunked=encode_chunked)
   except BaseException as exc:
    row['transport_result']='tls_certificate_verification' if isinstance(exc,ssl.SSLCertVerificationError) else 'transport_error';row['error_class']=type(exc).__name__;guard.save();raise
   finally:guard.io=False
  def response(conn):
   row=getattr(conn,'_a5_row',None)
   if row is None:guard.deny('unreserved_response')
   guard.io=True
   try:res=orig_response(conn)
   except BaseException as exc:row['transport_result']='transport_error';row['error_class']=type(exc).__name__;guard.save();raise
   finally:guard.io=False
   row['HTTP_status']=res.status;row['transport_result']='HTTP_RESPONSE';row['content_type']=res.getheader('Content-Type');row['redirect_count']=int(300<=res.status<400)
   if row['redirect_count']:
    dest=urljoin(row['canonical_url'],res.getheader('Location',''));guard.validate(guard.binding(),dest,redirect=True)
   raw_read=res.read;digest=hashlib.sha256()
   def read(*a,**kw):
    guard.io=True
    try:data=raw_read(*a,**kw)
    except BaseException as exc:row['transport_result']='transport_error';row['error_class']=type(exc).__name__;guard.save();raise
    finally:guard.io=False
    digest.update(data);row['response_bytes']+=len(data);row['response_SHA256']=digest.hexdigest();guard.save();return data
   res.read=read;guard.save();return res
  http.client.HTTPConnection.request=request;http.client.HTTPConnection.getresponse=response
  def audit(event,args):
   if event in {'socket.connect','socket.getaddrinfo','socket.gethostbyname','socket.sendto','socket.gethostbyaddr'} and not guard.io:guard.deny('unreserved_socket_or_DNS')
   if event=='open' and isinstance(args[0],(str,bytes)):
    p=os.fsdecode(args[0]);win=PureWindowsPath(p)
    if win.drive.upper()=='D:':guard.deny('D_access')
    if '\\users\\' in p.lower() and '\\tw-market' in p.lower():guard.deny('production_state_access')
    mode=args[1] or '';flags=args[2] if len(args)>2 else 0
    if any(x in mode for x in 'wax+') or isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT):guard.validate_root(str(Path(p).absolute()))
  sys.addaudithook(audit)


