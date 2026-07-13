from __future__ import annotations
from decimal import Decimal, InvalidOperation
CID_SEEDS={'TX':'TXF','MTX':'MXF','TXO':'TXO'}
class IdentityError(ValueError): pass

def _cid(sel): return CID_SEEDS.get(sel.requested_product_id, sel.requested_product_id)
def _suffix(sel): return '-F' if sel.instrument_type=='future' else '-O'
def _dec(v):
    try: return Decimal(str(v).replace(',',''))
    except (InvalidOperation, AttributeError): return None

def resolve_one_identity(s, rest, option_cache):
    cid=_cid(s); symtype='F' if s.instrument_type=='future' else 'O'
    prods=rest.products('0',symtype)
    if cid not in {str(r.get('CID')) for r in prods}: raise IdentityError('product_cid_validation_failed')
    months=rest.months(cid,'0',symtype)
    if s.contract_month_or_week not in {str(r.get('item') or r.get('ExpireMonth') or r.get('ContractMonth')) for r in months}: raise IdentityError('requested_month_not_available')
    if s.instrument_type=='future':
        rows=rest.quote_list(cid,s.contract_month_or_week,'F'); matches=[r for r in rows if str(r.get('SymbolID','')).endswith(_suffix(s))]
        if len(matches)!=1: raise IdentityError('futures_exact_identity_not_unique')
        sym=matches[0]['SymbolID']; detail=rest.detail([sym])
        if not detail or str(detail[0].get('SymbolID')) != sym: raise IdentityError('exact_detail_symbol_mismatch')
        return {'selector':s,'mis_cid':cid,'runtime_symbol_id':sym,'list_row':matches[0],'detail_row':detail[0],'network_scope':'exact_contract_month','retained_scope':'exact_runtime_symbol'}
    ck=(cid,s.contract_month_or_week); rows=option_cache.get(ck)
    if rows is None: rows=rest.option_chain(cid,s.contract_month_or_week); option_cache[ck]=rows
    cp='C' if s.option_type=='call' else 'P'; matches=[r for r in rows if str(r.get('SymbolID','')).endswith('-O') and _dec(r.get('StrikePrice'))==s.strike_price and str(r.get('CP')).upper().startswith(cp)]
    if len(matches)!=1: raise IdentityError('option_exact_identity_not_unique')
    sym=matches[0]['SymbolID']; detail=rest.detail([sym])
    if not detail or str(detail[0].get('SymbolID')) != sym: raise IdentityError('exact_detail_symbol_mismatch')
    return {'selector':s,'mis_cid':cid,'runtime_symbol_id':sym,'list_row':matches[0],'detail_row':detail[0],'network_scope':'whole_requested_contract_month_chain','retained_scope':'exact_requested_strike_and_option_type'}

def resolve_identity_results(selectors, rest):
    option_cache={}; successes=[]; failures=[]
    for s in selectors:
        try: successes.append(resolve_one_identity(s, rest, option_cache))
        except Exception as exc: failures.append({'selector':s.key,'status':'identity_resolution_failed','error':str(exc)})
    return successes, failures

def resolve_identities(selectors, rest):
    successes, failures=resolve_identity_results(selectors, rest)
    if failures: raise IdentityError(failures[0]['error'])
    return {r['selector'].key:r for r in successes}
