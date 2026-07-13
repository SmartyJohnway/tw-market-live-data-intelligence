"""M8C TAIFEX MIS preflight helpers.

Preflight-only. Network callers must require explicit operator confirmation.
"""
from __future__ import annotations
import json, re, time, argparse
from dataclasses import dataclass
from typing import Any

MAX_PRODUCTS=10
MAX_CONTRACT_MONTHS=3
MAX_OPTION_STRIKES=10
MAX_RUNTIME_SYMBOLS=20
MAX_BOOTSTRAP_ROWS=2000
MAX_OPTION_CHAIN_ROWS=2000
MAX_BOOTSTRAP_BYTES=2_000_000
MAX_WIRE_BYTES=2_000_000
MAX_SOCKJS_FRAMES=100
MAX_DECODED_MESSAGES=500
MAX_SINGLE_POLL_SECONDS=10
MAX_TOTAL_EXECUTION_SECONDS=30
MAX_RECONNECT_ATTEMPTS=0
HARD_MAX_RECONNECT_ATTEMPTS=1
MAX_RETAINED_OBSERVATIONS=100

REDACTED='[REDACTED]'
SENSITIVE_KEYS={'set-cookie','authorization','x-xsrf-token','entropy','session_id','sockjs_session','server_id'}

class M8CProbeError(ValueError): pass

def require_confirmed(args: argparse.Namespace) -> bool:
    return bool(getattr(args,'confirm_live_probe',False))

def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out={}
        for k,v in value.items():
            lk=str(k).lower()
            out[k]=REDACTED if (lk in SENSITIVE_KEYS or lk == 'cookie' or lk.endswith('-cookie')) else redact(v)
        return out
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value=re.sub(r'(Cookie|Set-Cookie|Authorization):[^\n]+', r'\1: '+REDACTED, value, flags=re.I)
        value=re.sub(r'/rt/[^/\s]+/[^/\s]+/', '/rt/[REDACTED]/[REDACTED]/', value)
    return value

def enforce_bytes(data: bytes|str, limit: int, status='wire_byte_limit_reached') -> None:
    n=len(data.encode('utf-8') if isinstance(data,str) else data)
    if n>limit: raise M8CProbeError(status)

def enforce_count(count:int, limit:int, status:str)->None:
    if count>limit: raise M8CProbeError(status)

def encode_sockjs_send(messages:list[dict]) -> str:
    return json.dumps([json.dumps(m,separators=(',',':')) for m in messages], separators=(',',':'))

def decode_sockjs_frame(frame: str) -> dict:
    if frame=='o': return {'frame_type':'open','messages':[]}
    if frame=='h': return {'frame_type':'heartbeat','messages':[]}
    if frame.startswith('c'):
        try: close=json.loads(frame[1:])
        except Exception as e: raise M8CProbeError('sockjs_frame_decode_failure') from e
        return {'frame_type':'close','close':close,'messages':[]}
    if frame.startswith('a'):
        try: arr=json.loads(frame[1:])
        except Exception as e: raise M8CProbeError('sockjs_frame_decode_failure') from e
        if not isinstance(arr,list): raise M8CProbeError('sockjs_frame_decode_failure')
        msgs=[]
        for item in arr:
            if not isinstance(item,str): raise M8CProbeError('sockjs_frame_decode_failure')
            msgs.append(json.loads(item))
        return {'frame_type':'array','messages':msgs}
    raise M8CProbeError('sockjs_frame_decode_failure')

def parse_quote_message(msg:dict)->dict:
    typ=msg.get('type')
    if typ!='quote': return {'message_type':typ or 'unknown','quote':None,'status':'unknown_message_type'}
    quote=msg.get('quote') or {}
    mode=msg.get('mode')
    status='ok' if mode==1 else 'unexpected_quote_mode'
    values=quote.get('values') or {}
    tv=quote.get('trueValues') or {}
    return {'message_type':'quote','mode':mode,'mode_label':'observed_initial_quote_state_mode_1' if mode==1 else 'unexpected_quote_mode','symbol':quote.get('symbol'),'value_key_count':len(values),'true_value_key_count':len(tv),'status':status}

def identity_key(obs:dict)->tuple:
    return (obs.get('runtime_symbol_id'), obs.get('session'), obs.get('market_type'))

def resolve_option_identity(rows:list[dict], *, cid:str, month:str, strike:str, option_type:str, session_suffix:str)->dict:
    matches=[]
    for r in rows:
        sym=str(r.get('SymbolID') or r.get('symbol') or '')
        if not sym.endswith(session_suffix): continue
        vals=' '.join(str(r.get(k,'')) for k in ('CID','CmdyCode','ContractMonth','ExpireMonth','StrikePrice','CP','CallPut'))
        if cid in vals and month in vals and str(strike) in vals and option_type.upper()[0] in vals.upper():
            matches.append(r)
    if not matches: return {'status':'no_symbol_match'}
    if len(matches)>1: return {'status':'multiple_symbol_matches'}
    return {'status':'resolved_from_bootstrap_row','runtime_symbol_id':matches[0].get('SymbolID')}

def classify_currentness(*, retrieved_recent:bool, source_timestamp_state:str, session_alignment:str, market_phase:str, quote_age_state:str, calendar_evidence:str)->dict:
    if source_timestamp_state in {'missing','unresolved'}: overall='source_timestamp_unresolved'
    elif session_alignment=='unresolved': overall='session_alignment_unresolved'
    elif session_alignment=='closed_session_aligned': overall='closed_session_latest_completed'
    elif session_alignment=='special_closure_aligned': overall='special_closure_latest_completed'
    elif session_alignment=='aligned' and quote_age_state=='fresh' and market_phase in {'trading','active'}: overall='active_session_fresh_liveish'
    elif session_alignment=='aligned' and quote_age_state=='aging': overall='active_session_aging_liveish'
    elif session_alignment=='aligned' and quote_age_state=='stale': overall='active_session_stale_liveish'
    else: overall='session_alignment_unresolved'
    return {'transport_state':None,'session_alignment':session_alignment,'market_phase':market_phase,'source_timestamp_state':source_timestamp_state,'quote_age_state':quote_age_state,'calendar_evidence':calendar_evidence,'retrieved_at_freshness_ignored_for_upgrade':True,'overall_ai_currentness':overall}

def build_arg_parser(desc:str):
    p=argparse.ArgumentParser(description=desc)
    p.add_argument('--confirm-live-probe', action='store_true')
    return p
from decimal import Decimal, InvalidOperation

class LimitReached(M8CProbeError):
    def __init__(self, status: str):
        super().__init__(status); self.status=status

def check_deadline(start: float, max_seconds: float):
    if time.monotonic() - start > max_seconds:
        raise LimitReached('bounded_time_limit_reached')

def read_bounded_response(response, *, max_bytes: int, start: float, max_seconds: float) -> bytes:
    length=response.headers.get('Content-Length')
    if length and length.isdigit() and int(length)>max_bytes:
        raise LimitReached('wire_byte_limit_reached')
    chunks=[]; total=0
    for chunk in response.iter_content(chunk_size=16384):
        check_deadline(start,max_seconds)
        if not chunk: continue
        total+=len(chunk)
        if total>max_bytes: raise LimitReached('wire_byte_limit_reached')
        chunks.append(chunk)
    return b''.join(chunks)

def bounded_json_post(session, url: str, *, json_body: dict, headers: dict, max_bytes: int, start: float, max_seconds: float, timeout: float):
    r=session.post(url,json=json_body,headers=headers,timeout=timeout,stream=True)
    body=read_bounded_response(r,max_bytes=max_bytes,start=start,max_seconds=max_seconds)
    try: data=json.loads(body.decode('utf-8'))
    except Exception as exc: raise M8CProbeError('rest_schema_drift') from exc
    return r.status_code, r.headers.get('content-type'), body, data

def _norm_dec(v: Any) -> Decimal | None:
    try: return Decimal(str(v).replace(',','').strip())
    except (InvalidOperation, AttributeError): return None

def normalize_cp(v: Any) -> str | None:
    t=str(v or '').strip().upper()
    if t in {'C','CALL','買權'}: return 'C'
    if t in {'P','PUT','賣權'}: return 'P'
    return None

def resolve_option_identity_exact(rows:list[dict], *, cid:str, month:str, strike:str, option_type:str, session_suffix:str)->dict:
    target_strike=_norm_dec(strike); target_cp=normalize_cp(option_type)
    if target_strike is None or target_cp is None: return {'status':'ambiguous_option_identity'}
    matches=[]
    for r in rows:
        sym=str(r.get('SymbolID') or '')
        row_cid=str(r.get('CID') or r.get('CmdyCode') or cid).strip()
        row_month=str(r.get('ExpireMonth') or r.get('ContractMonth') or month).strip()
        row_strike=_norm_dec(r.get('StrikePrice'))
        row_cp=normalize_cp(r.get('CP') or r.get('CallPut'))
        if row_cid==cid and row_month==month and row_strike==target_strike and row_cp==target_cp and sym.endswith(session_suffix):
            matches.append(r)
    if not matches: return {'status':'no_symbol_match'}
    if len(matches)>1: return {'status':'multiple_symbol_matches'}
    return {'status':'resolved_from_bootstrap_row','runtime_symbol_id':matches[0].get('SymbolID')}


class ProbeBudget:
    """Shared monotonic budget for M8C preflight network probes."""
    def __init__(self, *, total_seconds=MAX_TOTAL_EXECUTION_SECONDS, wire_bytes=MAX_WIRE_BYTES,
                 rest_rows=MAX_BOOTSTRAP_ROWS, frames=MAX_SOCKJS_FRAMES,
                 decoded_messages=MAX_DECODED_MESSAGES, products=MAX_PRODUCTS,
                 months=MAX_CONTRACT_MONTHS, strikes=MAX_OPTION_STRIKES,
                 symbols=MAX_RUNTIME_SYMBOLS, reconnects=MAX_RECONNECT_ATTEMPTS):
        self.started=time.monotonic(); self.deadline=self.started+total_seconds
        self.max_wire_bytes=wire_bytes; self.wire_bytes=0
        self.max_rest_rows=rest_rows; self.rest_rows=0
        self.max_frames=frames; self.frame_count=0
        self.max_decoded_messages=decoded_messages; self.decoded_message_count=0
        self.max_products=products; self.product_count=0
        self.max_months=months; self.month_count=0
        self.max_strikes=strikes; self.strike_count=0
        self.max_symbols=symbols; self.symbol_count=0
        self.max_reconnects=reconnects; self.reconnect_count=0
    def remaining(self) -> float:
        return max(0.0, self.deadline-time.monotonic())
    def timeout(self, single_timeout=MAX_SINGLE_POLL_SECONDS) -> float:
        rem=self.remaining()
        if rem <= 0: raise LimitReached('bounded_time_limit_reached')
        return min(single_timeout, rem)
    def check_deadline(self):
        if self.remaining() <= 0: raise LimitReached('bounded_time_limit_reached')
    def add_wire(self, n:int):
        self.wire_bytes += n
        if self.wire_bytes > self.max_wire_bytes: raise LimitReached('wire_byte_limit_reached')
    def add_rows(self, n:int, status='bootstrap_row_limit_reached'):
        self.rest_rows += n
        if self.rest_rows > self.max_rest_rows: raise LimitReached(status)
    def add_frame(self):
        self.frame_count += 1
        if self.frame_count > self.max_frames: raise LimitReached('frame_limit_reached')
    def add_messages(self, n:int):
        self.decoded_message_count += n
        if self.decoded_message_count > self.max_decoded_messages: raise LimitReached('decoded_message_limit_reached')
    def add_symbols(self, n:int):
        self.symbol_count += n
        if self.symbol_count > self.max_symbols: raise LimitReached('symbol_count_limit_reached')
    def add_products(self, n:int):
        self.product_count += n
        if self.product_count > self.max_products: raise LimitReached('product_count_limit_reached')
    def add_months(self, n:int):
        self.month_count += n
        if self.month_count > self.max_months: raise LimitReached('contract_month_limit_reached')
    def add_reconnect(self):
        self.reconnect_count += 1
        if self.reconnect_count > self.max_reconnects: raise LimitReached('reconnect_limit_reached')

def read_budgeted_response(response, *, budget: ProbeBudget, max_response_bytes: int | None = None) -> bytes:
    limit = max_response_bytes or (budget.max_wire_bytes - budget.wire_bytes)
    length=response.headers.get('Content-Length')
    if length and length.isdigit() and int(length)>limit:
        raise LimitReached('wire_byte_limit_reached')
    chunks=[]; total=0
    for chunk in response.iter_content(chunk_size=16384):
        budget.check_deadline()
        if not chunk: continue
        total += len(chunk)
        if total > limit: raise LimitReached('wire_byte_limit_reached')
        chunks.append(chunk)
    body=b''.join(chunks)
    budget.add_wire(len(body))
    return body

def budgeted_json_post(session, url: str, *, json_body: dict, headers: dict, budget: ProbeBudget, max_response_bytes: int = MAX_BOOTSTRAP_BYTES, timeout: float = MAX_SINGLE_POLL_SECONDS):
    r=session.post(url,json=json_body,headers=headers,timeout=budget.timeout(timeout),stream=True)
    body=read_budgeted_response(r,budget=budget,max_response_bytes=max_response_bytes)
    try: data=json.loads(body.decode('utf-8'))
    except Exception as exc: raise M8CProbeError('rest_schema_drift') from exc
    return r.status_code, r.headers.get('content-type'), body, data

def budgeted_get(session, url: str, *, headers: dict | None, budget: ProbeBudget, max_response_bytes: int = MAX_BOOTSTRAP_BYTES, timeout: float = MAX_SINGLE_POLL_SECONDS):
    r=session.get(url,headers=headers or {},timeout=budget.timeout(timeout),stream=True)
    body=read_budgeted_response(r,budget=budget,max_response_bytes=max_response_bytes)
    return r.status_code, r.headers.get('content-type'), body

def budgeted_post_raw(session, url: str, *, data: bytes | str | None, headers: dict, budget: ProbeBudget, max_response_bytes: int = MAX_WIRE_BYTES, timeout: float = MAX_SINGLE_POLL_SECONDS):
    data_bytes=(data.encode('utf-8') if isinstance(data,str) else (data or b''))
    budget.add_wire(len(data_bytes))
    r=session.post(url,data=data,headers=headers,timeout=budget.timeout(timeout),stream=True)
    body=read_budgeted_response(r,budget=budget,max_response_bytes=max_response_bytes)
    return r.status_code, r.headers.get('content-type'), body

# Deprecated: retained only to avoid import breakage; do not use for M8C identity decisions.
def resolve_option_identity(rows:list[dict], *, cid:str, month:str, strike:str, option_type:str, session_suffix:str)->dict:  # type: ignore[no-redef]
    return {'status':'deprecated_substring_resolver_not_allowed'}

def resolve_option_identity_exact(rows:list[dict], *, cid:str, month:str, strike:str, option_type:str, session_suffix:str)->dict:  # type: ignore[no-redef]
    target_strike=_norm_dec(strike); target_cp=normalize_cp(option_type)
    if target_strike is None or target_cp is None: return {'status':'ambiguous_option_identity'}
    matches=[]
    for r in rows:
        required=[r.get('SymbolID'), r.get('CID'), r.get('ExpireMonth') or r.get('ContractMonth'), r.get('StrikePrice'), r.get('CP') or r.get('CallPut')]
        if any(v in (None, '') for v in required):
            continue
        sym=str(r.get('SymbolID')).strip()
        row_cid=str(r.get('CID')).strip()
        row_month=str(r.get('ExpireMonth') or r.get('ContractMonth')).strip()
        row_strike=_norm_dec(r.get('StrikePrice'))
        row_cp=normalize_cp(r.get('CP') or r.get('CallPut'))
        if row_cid==cid and row_month==month and row_strike==target_strike and row_cp==target_cp and sym.endswith(session_suffix):
            matches.append(r)
    if not matches: return {'status':'no_symbol_match'}
    if len(matches)>1: return {'status':'multiple_symbol_matches'}
    return {'status':'resolved_from_bootstrap_row','runtime_symbol_id':matches[0].get('SymbolID')}
