from pathlib import Path
R=Path(r'C:\twmarket_temp\l7-a5\repo')
assert Path.cwd().resolve()==R.resolve()
import json,hashlib,datetime
from scripts.m8r_05c.canonical import hash_body_excluding_key
from jsonschema import Draft202012Validator,FormatChecker
from server.services.phase_i_i3_cash_institutional_flow_v2_evidence import validate_evidence_v2
class ReviewHold(BaseException):
 def __init__(self,code):self.code=code;super().__init__(code)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(E,n,v):(E/n).write_bytes(canon(v))
def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def require(ok,code):
 if not ok:raise ReviewHold(code)
def temporal_record(key,target,row,evidence,claim,receipt,bundle,result,adapter=None,clock_events=None):
 raw={'operation_id':evidence['operation_id'] if 'operation_id' in evidence else row['operation_ids'][0],'target':target,'market':target.split(':')[0],'capability':row['capability'],'executor':row['executor'],'reservation_timestamp':row['reservation_timestamp'],'actual_dispatch_timestamp':row['actual_dispatch_timestamp'],'claim_created_at':claim['claim_created_at'],'confirmation_bound_at':claim.get('confirmation_bound_at'),'receipt.finalized_at':receipt['finalized_at'],'claim.finalized_at':claim['finalized_at'],'bundle.finalized_at':bundle['finalized_at'],'Result.generated_at':result['generated_at'],'response_completed_at':'RESPONSE_COMPLETION_TIMESTAMP_NOT_RETAINED'}
 checks=[]
 def ck(name,ok,detail=None):checks.append({'invariant':name,'status':'PASS' if ok else 'FAIL','detail':detail})
 ck('claim <= reservation',dt(raw['claim_created_at'])<=dt(raw['reservation_timestamp']))
 ck('reservation <= dispatch',dt(raw['reservation_timestamp'])<=dt(raw['actual_dispatch_timestamp']))
 if key=='G':
  raw['retrieved_at']=evidence['retrieved_at'];raw['complete_body_received']=evidence['transport']['complete_body_received'];raw['adapter_completed_at_utc']=None
  ck('complete body implies retrieval string',raw['complete_body_received'] is True and isinstance(raw['retrieved_at'],str))
  ck('dispatch < retrieval',isinstance(raw['retrieved_at'],str) and dt(raw['actual_dispatch_timestamp'])<dt(raw['retrieved_at']))
  ck('source completion <= finalization',isinstance(raw['retrieved_at'],str) and dt(raw['retrieved_at'])<=dt(raw['receipt.finalized_at']))
  checks.append({'invariant':'retrieval <= adapter completion','status':'NOT_RETAINED'})
 else:
  obs=evidence['records'][0];raw['retrieved_at_utc']=obs['retrieved_at_utc'];raw['completed_at_utc']=adapter['adapter_result']['completed_at_utc'];raw['adapter_return_observed_at']=adapter['adapter_return_observed_at']
  events=[x for x in clock_events if x['market']==raw['market']];require(len(events)==2,'temporal_eod_clock_event_count')
  raw['clock_events']=events
  # The canonical EOD clock intentionally truncates to seconds. Preserve original
  # strings; independently recorded call boundaries prove causal ordering.
  ck('clock event values bind canonical evidence',events[0]['returned_value']==raw['retrieved_at_utc'] and events[1]['returned_value']==raw['completed_at_utc'])
  ck('dispatch < retrieval',dt(raw['actual_dispatch_timestamp'])<dt(events[0]['before']),{'comparison_basis':'preserved post-fetch utc_now call observation; canonical field precision = seconds','canonical_wall_clock_strict':dt(raw['actual_dispatch_timestamp'])<dt(raw['retrieved_at_utc'])})
  ck('retrieval <= adapter completion',dt(raw['retrieved_at_utc'])<=dt(raw['completed_at_utc']) and dt(events[0]['after'])<=dt(events[1]['before']))
  ck('adapter completion <= finalization',dt(events[1]['after'])<=dt(raw['adapter_return_observed_at'])<=dt(raw['receipt.finalized_at']))
  ck('clock observations within canonical second intervals',all(dt(x['returned_value'])<=dt(x['before'])<dt(x['returned_value'])+datetime.timedelta(seconds=1) and dt(x['returned_value'])<=dt(x['after'])<dt(x['returned_value'])+datetime.timedelta(seconds=1) for x in events))
 ck('last dispatch < finalization',dt(raw['actual_dispatch_timestamp'])<dt(raw['receipt.finalized_at']))
 ck('claim/receipt/bundle finalization equal',raw['claim.finalized_at']==raw['receipt.finalized_at']==raw['bundle.finalized_at'])
 ck('finalization == Result.generated_at',raw['receipt.finalized_at']==raw['Result.generated_at'])
 return {'raw':raw,'invariants':checks,'status':'PASS' if all(x['status']!='FAIL' for x in checks) else 'FAIL'}
def review_scenario(E,key,root,summary,execution,modec,rows):
 result=load(Path(summary['result_path']));audit=load(Path(summary['audit_path']));claim=execution['claim_record'];receipt=execution['execution_receipt'];bundle=execution['evidence_bundle']
 require(hash_body_excluding_key(result,'result_hash')==result['result_hash']==summary['result_hash'],'lineage_result_hash')
 for schema,obj in [('unified_market_evidence_result.v3',result),('unified_market_evidence_audit_package.v3',audit)]:
  errs=list(Draft202012Validator(load(R/'schemas'/(schema+'.schema.json')),format_checker=FormatChecker()).iter_errors(obj));require(not errs,'lineage_schema_'+schema)
 require(claim['state']=='consumed_success' and receipt['failed_operations']==0 and receipt['succeeded_operations']==2 and bundle['overall_status']=='succeeded','lineage_finalized_success')
 require(claim['execution_receipt_hash']==receipt['execution_receipt_hash']==bundle['execution_receipt_hash'],'lineage_receipt_crosslinks')
 require(hashlib.sha256(canon({k:v for k,v in receipt.items() if k not in {'schema_version','execution_receipt_id','execution_receipt_hash','created_by_component'}})).hexdigest()==receipt['execution_receipt_hash'],'lineage_receipt_hash')
 require(hashlib.sha256(canon({k:v for k,v in bundle.items() if k not in {'schema_version','bundle_id','bundle_hash'}})).hexdigest()==bundle['bundle_hash'],'lineage_bundle_hash')
 inventory=bundle['artifact_inventory'];items=[];paths=set();chron=[]
 adapters=load(E/'eod_adapter_output_observer.json') if key=='H' else [];clocks=load(E/'eod_clock_observer.json') if key=='H' else []
 for a in inventory:
  p=root/a['relative_path'];require(p.resolve().is_relative_to(root.resolve()) and sha(p)==a['sha256'] and p.stat().st_size==a['byte_size'],'lineage_artifact_hash');paths.add(a['relative_path']);v=load(p)
  if key=='G':
   validate_evidence_v2(v);target=v['canonical_target_id'];require(v['status']=='complete','functional_G_evidence')
   if target=='TWSE:1101':require(v['resolved_source_trade_date']=='2026-10-22','functional_G_source_date')
  else:
   require(len(v['records'])==1,'functional_H_record_count');classification=v['records'][0]['field_validation']['instrument_classification'];target=classification['canonical_target_id']
   require(classification['source']=='installation_active_security_master' and classification['coverage_mode']=='canonical_security_master' and classification['classification_status']=='classified' and classification['production_classification_completeness']=='complete' and classification['release_id']=='security-master-20261025T162542Z' and classification['release_manifest_sha256']=='ae2efd269b403c2d30c652a3884480682952e2bb3864c15e662de5e03763b0c1' and classification['canonical_instrument_family']=='company_share' and classification['canonical_instrument_type']=='common_share' and classification['instrument_type']=='equity' and classification['execution_eligibility']['status']=='allowed','functional_H_active_classification')
  matches=[r for r in rows if r['scenario']==key and r['targets']==[target]];require(len(matches)==1,'lineage_unique_transport');row=matches[0]
  require(row['HTTP_status']==200 and row['redirect_count']==0 and row['retry'] is False,'functional_transport')
  adapter=next((x for x in adapters if x['market']==target.split(':')[0]),None)
  chron.append(temporal_record(key,target,row,v,claim,receipt,bundle,result,adapter,clocks));items.append({'artifact':a,'path':str(p),'typed_evidence':v})
 actual={str(p.relative_to(root)).replace('\\','/') for p in (root/'evidence').rglob('*.json')};require(actual==paths,'lineage_orphan_artifact')
 maps=audit.get('citation_to_operation_map',[])
 for a in maps:require(a['artifact_relative_path'] in paths and sha(root/a['artifact_relative_path'])==a['artifact_hash'],'lineage_citation')
 require(len(inventory)==2 and len(chron)==2,'lineage_operation_count')
 for op in receipt['operation_receipts']:require(op['status']=='succeeded' and all(a['relative_path'] in paths for a in op['evidence_artifacts']),'lineage_operation_receipt')
 required={'TWSE:1101','TPEX:5347'} if key=='G' else {'TWSE:2330','TPEX:6488'};require({r['raw']['target'] for r in chron}==required,'lineage_target_set')
 write(E,key.lower()+'_temporal_chronology.json',{'status':'PASS' if all(x['status']=='PASS' for x in chron) else 'FAIL','operations':chron,'response_completed_at':'RESPONSE_COMPLETION_TIMESTAMP_NOT_RETAINED','temporal_ordering_code_authority':{'orchestrator':'scripts/m8r_05b_03/orchestrator.py:71; deferred clock after aggregation','I3_transport':'server/services/phase_i_i3_production_transport.py','EOD':'retrieval clock sampled after fetch returns; completion sampled after parse'}})
 combined=[]
 for k in 'GH':
  p=E/(k.lower()+'_temporal_chronology.json')
  if p.exists():combined.extend(load(p)['operations'])
 write(E,'temporal_invariant_matrix.json',{'status':'PASS' if all(x['status']=='PASS' for x in combined) else 'FAIL','operations':combined})
 require(all(x['status']=='PASS' for x in chron),'temporal_'+key+'_invariant_failure')
 summary.update(target_evidence=items,operation_receipts=receipt['operation_receipts'],temporal_provenance='PASS',claim_created_at=claim['claim_created_at'],finalized_at=receipt['finalized_at'],result_generated_at=result['generated_at'],resolved_source_trade_date='2026-10-22' if key=='G' else None)
 write(E,'scenario_'+key.lower()+'.json',summary)
 review={'scenario':key,'status':'PASS','operations':2,'artifacts':len(inventory),'citations':len(maps),'orphans':0,'broken_citations':0,'hash_mismatches':0,'unfinalized_successful_claims':0,'result_hash':result['result_hash'],'receipt_hash':receipt['execution_receipt_hash'],'bundle_hash':bundle['bundle_hash'],'audit_sha256':sha(Path(summary['audit_path']))}
 dest=E/'result_audit_lineage_review.json';existing=load(dest).get('new_GH_reviews',[]) if dest.exists() else [];existing.append(review)
 write(E,'result_audit_lineage_review.json',{'status':'PASS','new_GH_reviews':existing,'operations':sum(x['operations'] for x in existing),'artifacts':sum(x['artifacts'] for x in existing),'citations':sum(x['citations'] for x in existing),'orphans':0,'broken_citations':0,'hash_mismatches':0,'unfinalized_successful_claims':0})
