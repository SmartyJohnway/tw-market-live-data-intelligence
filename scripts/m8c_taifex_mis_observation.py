from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import datetime
from zoneinfo import ZoneInfo
from .m8c_taifex_mis_currentness import evaluate_taifex_mis_currentness

QID_MAP={'125':'CLastPrice','129':'CRefPrice','143':'CTime','144':'CDate','145':'Status','404':'CTotalVolume','101':'bid_price_family_1','102':'ask_price_family_1','113':'bid_size_family_1','114':'ask_size_family_1','743':'bid_price_family_2','744':'ask_price_family_2','745':'bid_size_family_2','746':'ask_size_family_2'}
ACTIVE_STATUS_CODES={'active_regular_trading'}

def dec(v,caveats):
    if v in (None,''): return None
    try:
        d=Decimal(str(v).replace(',','').strip())
        if not d.is_finite(): raise InvalidOperation()
        return d
    except (InvalidOperation, AttributeError): caveats.append('malformed_decimal_field'); return None

def normalize_market_phase(status):
    if status in (None,''): return 'market_phase_unresolved'
    s=str(status).strip()
    return 'active_regular_trading' if s in ACTIVE_STATUS_CODES else 'market_phase_unresolved'

def get_value(field, qid, rows):
    for source,row in rows:
        if not row: continue
        if qid and qid in row and row.get(qid) not in (None,''):
            return row.get(qid), {'source':source,'field':qid,'field_kind':'sockjs_numeric_qid' if source=='sockjs_mode_1' else 'numeric_qid'}
        if field in row and row.get(field) not in (None,''):
            return row.get(field), {'source':source,'field':field,'field_kind':'named_rest_field' if source!='sockjs_mode_1' else 'named_field'}
    return None, {'source':None,'field':None,'field_kind':None}

def resolve_source_ts(rows,caveats):
    d,_=get_value('CDate','144',rows); t,_=get_value('CTime','143',rows)
    if not d or not t: return None, d, t
    s=f'{d} {t}'
    for fmt in ('%Y/%m/%d %H:%M:%S','%Y-%m-%d %H:%M:%S','%Y%m%d %H:%M:%S','%Y%m%d %H%M%S'):
        try: return datetime.strptime(s,fmt).replace(tzinfo=ZoneInfo('Asia/Taipei')).isoformat(), d, t
        except Exception: pass
    caveats.append('source_timestamp_unresolved'); return None, d, t

def build_observation(selector, resolved, *, mode1_quote=None, detail_row=None, list_row=None, evaluation_time_asia_taipei=None, calendar_context=None):
    caveats=[]; rows=(('sockjs_mode_1', mode1_quote or {}),('exact_detail_fallback', detail_row or {}),('quote_list_fallback', list_row or {}))
    last,prov=get_value('CLastPrice','125',rows); ref,refprov=get_value('CRefPrice','129',rows); vol,volprov=get_value('CTotalVolume','404',rows)
    bid1,pb1=get_value('CBidPrice1','101',rows); ask1,pa1=get_value('CAskPrice1','102',rows); bidsz1,psb1=get_value('CBidSize1','113',rows); asksz1,psa1=get_value('CAskSize1','114',rows)
    bid2,pb2=get_value('CBestBidPrice','743',rows); ask2,pa2=get_value('CBestAskPrice','744',rows); bidsz2,psb2=get_value('CBestBidSize','745',rows); asksz2,psa2=get_value('CBestAskSize','746',rows)
    cand={'family_101_102_113_114':{'bid':dec(bid1,caveats),'ask':dec(ask1,caveats),'bid_size':dec(bidsz1,caveats),'ask_size':dec(asksz1,caveats)},'family_743_744_745_746':{'bid':dec(bid2,caveats),'ask':dec(ask2,caveats),'bid_size':dec(bidsz2,caveats),'ask_size':dec(asksz2,caveats)}}
    canonical={'best_bid':None,'best_ask':None,'canonicalization_status':'top_of_book_field_family_unresolved'}
    if cand['family_101_102_113_114']['bid']==cand['family_743_744_745_746']['bid'] and cand['family_101_102_113_114']['ask']==cand['family_743_744_745_746']['ask'] and cand['family_101_102_113_114']['bid'] is not None:
        canonical={'best_bid':cand['family_101_102_113_114']['bid'],'best_ask':cand['family_101_102_113_114']['ask'],'canonicalization_status':'candidate_families_agree'}
    src_ts, raw_d, raw_t=resolve_source_ts(rows,caveats)
    raw_status, status_prov=get_value('Status','145',rows); market_phase=normalize_market_phase(raw_status)
    currentness=evaluate_taifex_mis_currentness(accepted_mode_1=bool(mode1_quote), source_timestamp_asia_taipei=src_ts, evaluation_time_asia_taipei=evaluation_time_asia_taipei, session=selector.session, market_phase=market_phase, calendar_context=calendar_context, session_suffix_aligned=str(resolved.get('runtime_symbol_id','')).endswith('-F' if selector.instrument_type=='future' else '-O'))
    return {'source_id':'TAIFEX_MIS','authority_level':'official_undocumented','timing_class':'liveish_intraday_snapshot','requested_product_id':selector.requested_product_id,'mis_cid':resolved['mis_cid'],'runtime_symbol_id':resolved['runtime_symbol_id'],'instrument_type':selector.instrument_type,'session':selector.session,'contract_month_or_week':selector.contract_month_or_week,'strike_price':str(selector.strike_price) if selector.strike_price is not None else None,'option_type':selector.option_type,'raw_CDate':raw_d,'raw_CTime':raw_t,'source_timestamp_asia_taipei':src_ts,'source_status_code':raw_status,'market_phase':currentness['market_phase'],'currentness':currentness,'normalized_field_candidates':{'last_price':dec(last,caveats),'reference_price':dec(ref,caveats),'total_volume':dec(vol,caveats),'top_of_book_candidates':cand,**canonical},'field_provenance':{'last_price':prov,'reference_price':refprov,'total_volume':volprov,'status':status_prov,'bid_family_1':pb1,'ask_family_1':pa1,'bid_size_family_1':psb1,'ask_size_family_1':psa1,'bid_family_2':pb2,'ask_family_2':pa2,'bid_size_family_2':psb2,'ask_size_family_2':psa2},'network_scope':resolved.get('network_scope'), 'retained_scope':resolved.get('retained_scope'),'caveats':caveats,'raw_payload_retained':False}
