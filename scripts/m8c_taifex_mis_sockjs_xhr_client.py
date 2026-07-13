from __future__ import annotations
import json, random
from .m8c_taifex_mis_limits import MAX_SINGLE_POLL_SECONDS
from scripts.m8c_taifex_mis_probe_common import decode_sockjs_frame, encode_sockjs_send, M8CProbeError

BASE='https://mis.taifex.com.tw/futures/rt'

def _body(resp):
    if hasattr(resp,'content'): return resp.content
    return resp.text.encode()

def collect_initial_states(session, symbols, budget, *, base_url=BASE):
    info=session.get(base_url+'/info', timeout=budget.timeout(MAX_SINGLE_POLL_SECONDS)); budget.add_response_payload(len(_body(info)))
    sid=str(random.randint(100,999)); sess=str(random.randint(100000,999999)); prefix=f'{base_url}/{sid}/{sess}'
    r=session.post(prefix+'/xhr', data=b'', timeout=budget.timeout(MAX_SINGLE_POLL_SECONDS)); budget.add_response_payload(len(_body(r))); budget.add_frame()
    if _body(r).decode().strip()!='o': raise M8CProbeError('sockjs_open_frame_required')
    msg=encode_sockjs_send([{'type':'subscribe','symbols':list(symbols)}]); budget.add_sockjs_send_payload(len(msg.encode()))
    session.post(prefix+'/xhr_send', data=msg, headers={'Content-Type':'text/plain;charset=UTF-8'}, timeout=budget.timeout(MAX_SINGLE_POLL_SECONDS))
    accepted={}; ignored=0; caveats=[]
    while set(accepted)!=set(symbols):
        p=session.post(prefix+'/xhr', data=b'', timeout=budget.timeout(MAX_SINGLE_POLL_SECONDS)); body=_body(p).decode(); budget.add_response_payload(len(_body(p))); budget.add_frame()
        frame=decode_sockjs_frame(body.strip()); budget.add_messages(len(frame.get('messages',[])))
        if frame['frame_type']=='heartbeat': continue
        if frame['frame_type']=='close': break
        if frame['frame_type']!='array': raise M8CProbeError('unexpected_sockjs_frame')
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
