"""Production-neutral SockJS frame helpers for M8C TAIFEX MIS runtime."""
from __future__ import annotations
import json

class SockjsProtocolError(ValueError): pass

def encode_sockjs_send(messages:list[dict]) -> str:
    return json.dumps([json.dumps(m,separators=(',',':')) for m in messages], separators=(',',':'))

def decode_sockjs_frame(frame: str) -> dict:
    if frame == 'o': return {'frame_type':'open','messages':[]}
    if frame == 'h': return {'frame_type':'heartbeat','messages':[]}
    if frame.startswith('c'):
        try: close=json.loads(frame[1:])
        except Exception as exc: raise SockjsProtocolError('sockjs_frame_decode_failure') from exc
        return {'frame_type':'close','close':close,'messages':[]}
    if frame.startswith('a'):
        try: arr=json.loads(frame[1:])
        except Exception as exc: raise SockjsProtocolError('sockjs_frame_decode_failure') from exc
        if not isinstance(arr,list): raise SockjsProtocolError('sockjs_frame_decode_failure')
        out=[]
        for item in arr:
            if not isinstance(item,str): raise SockjsProtocolError('sockjs_frame_decode_failure')
            try: out.append(json.loads(item))
            except Exception as exc: raise SockjsProtocolError('sockjs_frame_decode_failure') from exc
        return {'frame_type':'array','messages':out}
    raise SockjsProtocolError('sockjs_frame_decode_failure')
