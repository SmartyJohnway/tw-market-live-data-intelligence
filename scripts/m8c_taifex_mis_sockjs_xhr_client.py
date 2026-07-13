from __future__ import annotations
import random
from .m8c_taifex_mis_limits import MAX_SINGLE_POLL_SECONDS, MAX_RESPONSE_PAYLOAD_BYTES
from .m8c_taifex_mis_http_client import read_bounded_response
from .m8c_taifex_mis_sockjs_protocol import decode_sockjs_frame, encode_sockjs_send, SockjsProtocolError

BASE='https://mis.taifex.com.tw/futures/rt'

def _read_text(resp,budget, expected_statuses=(200,)):
    return read_bounded_response(resp,budget,per_response_limit=MAX_RESPONSE_PAYLOAD_BYTES, expected_statuses=expected_statuses).decode()

def collect_initial_states(session, symbols, budget, *, base_url=BASE):
    info=session.get(base_url+'/info', timeout=budget.timeout(MAX_SINGLE_POLL_SECONDS), stream=True); _read_text(info,budget)
    sid=str(random.randint(100,999)); sess=str(random.randint(100000,999999)); prefix=f'{base_url}/{sid}/{sess}'
    r=session.post(prefix+'/xhr', data=b'', timeout=budget.timeout(MAX_SINGLE_POLL_SECONDS), stream=True); budget.add_frame()
    if _read_text(r,budget).strip()!='o': raise SockjsProtocolError('sockjs_open_frame_required')
    msg=encode_sockjs_send([{'type':'subscribe','symbols':list(symbols)}]); budget.add_sockjs_send_payload(len(msg.encode()))
    send=session.post(prefix+'/xhr_send', data=msg, headers={'Content-Type':'text/plain;charset=UTF-8'}, timeout=budget.timeout(MAX_SINGLE_POLL_SECONDS), stream=True); _read_text(send,budget, expected_statuses=(200,204))
    accepted={}; ignored=0; caveats=[]
    while set(accepted)!=set(symbols):
        p=session.post(prefix+'/xhr', data=b'', timeout=budget.timeout(MAX_SINGLE_POLL_SECONDS), stream=True); budget.add_frame()
        frame=decode_sockjs_frame(_read_text(p,budget).strip()); budget.add_messages(len(frame.get('messages',[])))
        if frame['frame_type']=='heartbeat': continue
        if frame['frame_type']=='close': break
        if frame['frame_type']!='array': raise SockjsProtocolError('unexpected_sockjs_frame')
        for m in frame['messages']:
            if m.get('type')!='quote': continue
            q=m.get('quote') or {}; sym=q.get('symbol') or q.get('SymbolID')
            if m.get('mode')==1 and sym in symbols and sym not in accepted:
                vals=q.get('values') if isinstance(q.get('values'),dict) else q
                vals=dict(vals); vals.setdefault('SymbolID', sym); accepted[sym]=vals
            elif m.get('mode')!=1:
                ignored+=1; caveats.append('unsupported_quote_mode_ignored')
        if budget.frames>=budget.max_frames: break
    return {'accepted_initial_states':accepted,'unsupported_mode_count':ignored,'caveats':sorted(set(caveats)),'reconnect_attempts':0,'unsubscribe_sent':False}
