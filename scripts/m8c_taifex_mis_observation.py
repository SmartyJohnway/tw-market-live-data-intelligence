from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import datetime
from zoneinfo import ZoneInfo
from .m8c_taifex_mis_currentness import evaluate_taifex_mis_currentness

def dec(v,caveats):
    if v in (None,''): return None
    try: return Decimal(str(v).replace(',','').strip())
    except (InvalidOperation, AttributeError): caveats.append('malformed_decimal_field'); return None

def resolve_source_ts(row,caveats):
    d=row.get('CDate'); t=row.get('CTime')
    if not d or not t: return None
    s=f'{d} {t}'
    for fmt in ('%Y/%m/%d %H:%M:%S','%Y-%m-%d %H:%M:%S','%Y%m%d %H:%M:%S'):
        try: return datetime.strptime(s,fmt).replace(tzinfo=ZoneInfo('Asia/Taipei')).isoformat()
        except Exception: pass
    caveats.append('source_timestamp_unresolved'); return None

def choose_field(fields, *rows):
    for source,row in rows:
        if not row: continue
        for f in fields:
            if f in row and row.get(f) not in (None,''):
                return row.get(f), {'source':source,'field':f}
    return None, {'source':None,'field':None}

def build_observation(selector, resolved, *, mode1_quote=None, detail_row=None, list_row=None, evaluation_time_asia_taipei=None, calendar_context=None):
    caveats=[]; rows=(('sockjs_mode_1', mode1_quote or {}),('exact_detail_fallback', detail_row or {}),('quote_list_fallback', list_row or {}))
    last,prov=choose_field(['CLastPrice','lastPrice','101'],*rows); bid1,pb1=choose_field(['CBidPrice1','CBestBidPrice','101'],*rows); ask1,pa1=choose_field(['CAskPrice1','CBestAskPrice','102'],*rows); bid2,pb2=choose_field(['743'],*rows); ask2,pa2=choose_field(['744'],*rows)
    cand={'family_101_102_113_114':{'bid':dec(bid1,caveats),'ask':dec(ask1,caveats)},'family_743_744_745_746':{'bid':dec(bid2,caveats),'ask':dec(ask2,caveats)}}
    canonical={'best_bid':None,'best_ask':None,'canonicalization_status':'top_of_book_field_family_unresolved'}
    if cand['family_101_102_113_114']==cand['family_743_744_745_746'] and cand['family_101_102_113_114']['bid'] is not None:
        canonical={'best_bid':cand['family_101_102_113_114']['bid'],'best_ask':cand['family_101_102_113_114']['ask'],'canonicalization_status':'candidate_families_agree'}
    src_ts=resolve_source_ts((mode1_quote or detail_row or list_row or {}), caveats)
    currentness=evaluate_taifex_mis_currentness(accepted_mode_1=bool(mode1_quote), source_timestamp_asia_taipei=src_ts, evaluation_time_asia_taipei=evaluation_time_asia_taipei, session=selector.session, market_phase=(mode1_quote or detail_row or list_row or {}).get('Status') or 'unresolved', calendar_context=calendar_context)
    return {'source_id':'TAIFEX_MIS','authority_level':'official_undocumented','timing_class':'liveish_intraday_snapshot','requested_product_id':selector.requested_product_id,'mis_cid':resolved['mis_cid'],'runtime_symbol_id':resolved['runtime_symbol_id'],'instrument_type':selector.instrument_type,'session':selector.session,'contract_month_or_week':selector.contract_month_or_week,'strike_price':str(selector.strike_price) if selector.strike_price is not None else None,'option_type':selector.option_type,'raw_CDate':(mode1_quote or detail_row or list_row or {}).get('CDate'),'raw_CTime':(mode1_quote or detail_row or list_row or {}).get('CTime'),'source_timestamp_asia_taipei':src_ts,'source_status_code':(mode1_quote or detail_row or list_row or {}).get('Status'),'market_phase':currentness['market_phase'],'currentness':currentness,'normalized_field_candidates':{'last_price':dec(last,caveats),'top_of_book_candidates':cand,**canonical},'field_provenance':{'last_price':prov,'bid_family_1':pb1,'ask_family_1':pa1,'bid_family_2':pb2,'ask_family_2':pa2},'network_scope':resolved.get('network_scope'), 'retained_scope':resolved.get('retained_scope'),'caveats':caveats,'raw_payload_retained':False}
