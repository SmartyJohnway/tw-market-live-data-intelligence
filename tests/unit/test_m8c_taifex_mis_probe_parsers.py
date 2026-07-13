import pytest
from scripts.m8c_taifex_mis_probe_common import decode_sockjs_frame, encode_sockjs_send, parse_quote_message, redact, M8CProbeError

def test_sockjs_frames():
    assert decode_sockjs_frame('o')['frame_type']=='open'
    assert decode_sockjs_frame('h')['frame_type']=='heartbeat'
    assert decode_sockjs_frame('c[3000,"Go away"]')['frame_type']=='close'
    frame='a["{\\\"type\\\":\\\"quote\\\",\\\"mode\\\":1,\\\"quote\\\":{\\\"symbol\\\":\\\"TXFTEST-F\\\",\\\"values\\\":{},\\\"trueValues\\\":{}}}"]'
    out=decode_sockjs_frame(frame)
    assert out['frame_type']=='array' and out['messages'][0]['type']=='quote'

def test_send_encoding_and_quote_parse():
    body=encode_sockjs_send([{'type':'subscribe','symbols':['TXFTEST-F']}])
    assert body=='["{\\\"type\\\":\\\"subscribe\\\",\\\"symbols\\\":[\\\"TXFTEST-F\\\"]}"]'
    q=parse_quote_message({'type':'quote','mode':1,'quote':{'symbol':'TXFTEST-F','values':{'125':'1'},'trueValues':{}}})
    assert q['mode_label']=='observed_initial_quote_state_mode_1'
    assert parse_quote_message({'type':'quote','mode':2,'quote':{}})['status']=='unexpected_quote_mode'
    assert parse_quote_message({'type':'changeDate'})['status']=='unknown_message_type'

def test_malformed_and_redaction():
    with pytest.raises(M8CProbeError): decode_sockjs_frame('x')
    assert redact({'Set-Cookie':'abc','path':'/rt/a/b/xhr'})['Set-Cookie']=='[REDACTED]'
from scripts.m8c_taifex_mis_probe_common import read_bounded_response, LimitReached, check_deadline, enforce_count, MAX_RUNTIME_SYMBOLS
import time

class FakeResp:
    def __init__(self, chunks, headers=None):
        self._chunks=chunks; self.headers=headers or {}
    def iter_content(self, chunk_size=1):
        yield from self._chunks

def test_bounded_reader_rejects_content_length_and_stream_limit():
    with pytest.raises(LimitReached) as e:
        read_bounded_response(FakeResp([b'a'], {'Content-Length':'999'}), max_bytes=10, start=time.monotonic(), max_seconds=10)
    assert e.value.status=='wire_byte_limit_reached'
    with pytest.raises(LimitReached):
        read_bounded_response(FakeResp([b'12345', b'67890', b'X']), max_bytes=10, start=time.monotonic(), max_seconds=10)

def test_count_and_deadline_limits():
    with pytest.raises(M8CProbeError): enforce_count(MAX_RUNTIME_SYMBOLS+1, MAX_RUNTIME_SYMBOLS, 'symbol_count_limit_reached')
    with pytest.raises(LimitReached): check_deadline(time.monotonic()-100, 1)
