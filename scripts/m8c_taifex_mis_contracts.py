from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from datetime import datetime
from .m8c_taifex_mis_limits import RuntimeBudget

class SelectorError(ValueError): pass
@dataclass(frozen=True)
class ValidatedSelector:
    instrument_type:str; requested_product_id:str; contract_month_or_week:str; session:str; strike_price:Decimal|None=None; option_type:str|None=None
    @property
    def key(self): return (self.instrument_type,self.requested_product_id,self.contract_month_or_week,self.session,str(self.strike_price),self.option_type)

def _dec(s):
    try:
        d = Decimal(str(s).replace(',','').strip())
        if (not d.is_finite()) or d <= 0:
            raise InvalidOperation()
        return d
    except (InvalidOperation, AttributeError): raise SelectorError('invalid_strike_price')
def _cp(v):
    t=str(v or '').strip().lower()
    if t in ('c','call'): return 'call'
    if t in ('p','put'): return 'put'
    raise SelectorError('invalid_option_type')
def validate_selectors(items, budget:RuntimeBudget|None=None):
    if not isinstance(items,list) or not items: raise SelectorError('empty_or_invalid_selector_list')
    out=[]
    for x in items:
        if not isinstance(x,dict): raise SelectorError('invalid_selector_shape')
        it=str(x.get('instrument_type','')).lower(); session=str(x.get('session','')).lower(); prod=str(x.get('requested_product_id','')).upper(); month=str(x.get('contract_month_or_week','')).upper()
        if session!='regular': raise SelectorError('unsupported_session_after_hours_disabled')
        if it not in ('future','option'): raise SelectorError('invalid_instrument_type')
        if not prod or not re.match(r'^[A-Z0-9]+$', prod): raise SelectorError('invalid_product')
        if not month: raise SelectorError('invalid_contract_month_or_week')
        if re.match(r'^\d{6}$', month):
            try: datetime.strptime(month, '%Y%m')
            except ValueError: raise SelectorError('invalid_contract_month')
        elif not re.match(r'^\d{6}[WF]\d{1,2}$', month):
            raise SelectorError('unsupported_weekly_format')
        if it=='future': out.append(ValidatedSelector(it,prod,month,session))
        else: out.append(ValidatedSelector(it,prod,month,session,_dec(x.get('strike_price')),_cp(x.get('option_type'))))
    if len({s.session for s in out})>1: raise SelectorError('mixed_sessions_rejected')
    if len({s.key for s in out})!=len(out): raise SelectorError('duplicate_or_conflicting_selectors')
    if budget: budget.set_selector_counts(len(out),len({s.requested_product_id for s in out}),len({s.contract_month_or_week for s in out}),len({s.strike_price for s in out if s.strike_price is not None}))
    return out
