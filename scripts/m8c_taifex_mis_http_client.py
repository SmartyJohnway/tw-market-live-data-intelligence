"""Shared bounded HTTP response reader for M8C TAIFEX MIS runtime."""
from __future__ import annotations
from .m8c_taifex_mis_limits import MAX_RESPONSE_PAYLOAD_BYTES, LimitError

class HttpClientError(ValueError): pass

def validate_http_status(resp, expected_statuses=(200,)):
    code=getattr(resp,'status_code',None)
    if code not in expected_statuses:
        raise HttpClientError(f'http_status_not_ok:{code}')

def read_bounded_response(resp, budget, *, per_response_limit:int=MAX_RESPONSE_PAYLOAD_BYTES, expected_statuses=(200,)) -> bytes:
    validate_http_status(resp, expected_statuses)
    effective=budget.effective_response_limit(per_response_limit)
    if effective < 0: raise LimitError('accounted_payload_limit_reached')
    headers=getattr(resp,'headers',{}) or {}
    length=headers.get('Content-Length') or headers.get('content-length')
    if length and str(length).isdigit() and int(length)>effective:
        raise LimitError('response_payload_limit_reached')
    chunks=[]; total=0
    if hasattr(resp,'iter_content'):
        iterator=resp.iter_content(chunk_size=16384)
    elif hasattr(resp,'content'):
        iterator=[resp.content]
    else:
        iterator=[getattr(resp,'text','').encode()]
    for chunk in iterator:
        budget.timeout(0.001)
        if not chunk: continue
        total += len(chunk)
        if total > effective: raise LimitError('response_payload_limit_reached')
        chunks.append(chunk)
    body=b''.join(chunks)
    budget.add_response_payload(len(body))
    return body
