from __future__ import annotations
from decimal import Decimal
from .m8c_taifex_mis_contracts import ValidatedSelector
CID_SEEDS={'TX':'TXF','MTX':'MXF','TXO':'TXO'}
class IdentityError(ValueError): pass

def _cid(sel): return CID_SEEDS.get(sel.requested_product_id, sel.requested_product_id)
def _suffix(sel): return '-F' if sel.instrument_type=='future' else '-O'
def resolve_identities(selectors, rest):
    out={}; option_cache={}
    for s in selectors:
        cid=_cid(s); symtype='F' if s.instrument_type=='future' else 'O'
        prods=rest.products('0',symtype)
        if cid not in {str(r.get('CID')) for r in prods}: raise IdentityError('product_cid_validation_failed')
        months=rest.months(cid,'0',symtype)
        if s.contract_month_or_week not in {str(r.get('item') or r.get('ExpireMonth') or r.get('ContractMonth')) for r in months}: raise IdentityError('requested_month_not_available')
        if s.instrument_type=='future':
            rows=rest.quote_list(cid,s.contract_month_or_week,'F'); matches=[r for r in rows if str(r.get('SymbolID','')).endswith(_suffix(s))]
            if len(matches)!=1: raise IdentityError('futures_exact_identity_not_unique')
            sym=matches[0]['SymbolID']; detail=rest.detail([sym]); out[s.key]={'selector':s,'mis_cid':cid,'runtime_symbol_id':sym,'list_row':matches[0],'detail_row':detail[0] if detail else {},'network_scope':'exact_contract_month','retained_scope':'exact_runtime_symbol'}
        else:
            ck=(cid,s.contract_month_or_week); rows=option_cache.get(ck)
            if rows is None: rows=rest.option_chain(cid,s.contract_month_or_week); option_cache[ck]=rows
            cp='C' if s.option_type=='call' else 'P'; matches=[r for r in rows if str(r.get('SymbolID','')).endswith('-O') and Decimal(str(r.get('StrikePrice')).replace(',',''))==s.strike_price and str(r.get('CP')).upper().startswith(cp)]
            if len(matches)!=1: raise IdentityError('option_exact_identity_not_unique')
            sym=matches[0]['SymbolID']; detail=rest.detail([sym]); out[s.key]={'selector':s,'mis_cid':cid,'runtime_symbol_id':sym,'list_row':matches[0],'detail_row':detail[0] if detail else {},'network_scope':'whole_requested_contract_month_chain','retained_scope':'exact_requested_strike_and_option_type'}
    return out
