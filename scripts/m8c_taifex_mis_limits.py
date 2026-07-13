"""M8C-01 TAIFEX MIS bounded runtime limits and budget."""
from __future__ import annotations
import time
from dataclasses import dataclass, field

MAX_SELECTORS=20; MAX_PRODUCTS=10; MAX_CONTRACT_MONTHS=3; MAX_OPTION_STRIKES=10; MAX_RUNTIME_SYMBOLS=20
MAX_BOOTSTRAP_ROWS=2000; MAX_OPTION_CHAIN_ROWS=2000; MAX_RESPONSE_PAYLOAD_BYTES=2_000_000; MAX_ACCOUNTED_PAYLOAD_BYTES=2_000_000
MAX_SOCKJS_FRAMES=100; MAX_DECODED_MESSAGES=500; MAX_SINGLE_REQUEST_SECONDS=10; MAX_SINGLE_POLL_SECONDS=5; MAX_TOTAL_EXECUTION_SECONDS=30
MAX_RECONNECT_ATTEMPTS=0; MAX_RETAINED_OBSERVATIONS=100

class LimitError(ValueError):
    def __init__(self, status:str): super().__init__(status); self.status=status

@dataclass
class RuntimeBudget:
    max_total_execution_seconds:int=20; max_accounted_payload_bytes:int=MAX_ACCOUNTED_PAYLOAD_BYTES; max_bootstrap_rows:int=MAX_BOOTSTRAP_ROWS
    max_option_chain_rows:int=MAX_OPTION_CHAIN_ROWS; max_frames:int=MAX_SOCKJS_FRAMES; max_decoded_messages:int=MAX_DECODED_MESSAGES
    max_retained_observations:int=MAX_RETAINED_OBSERVATIONS; monotonic_clock:object|None=None
    rest_request_payload_bytes:int=0; sockjs_send_payload_bytes:int=0; response_payload_bytes:int=0; total_accounted_payload_bytes:int=0
    rest_rows:int=0; frames:int=0; decoded_messages:int=0; selectors:int=0; products:int=0; months:int=0; strikes:int=0; symbols:int=0; retained_observations:int=0
    started:float=field(init=False); deadline:float=field(init=False)
    def __post_init__(self):
        limits={
            'max_total_execution_seconds': (self.max_total_execution_seconds, MAX_TOTAL_EXECUTION_SECONDS),
            'max_accounted_payload_bytes': (self.max_accounted_payload_bytes, MAX_ACCOUNTED_PAYLOAD_BYTES),
            'max_bootstrap_rows': (self.max_bootstrap_rows, MAX_BOOTSTRAP_ROWS),
            'max_option_chain_rows': (self.max_option_chain_rows, MAX_OPTION_CHAIN_ROWS),
            'max_frames': (self.max_frames, MAX_SOCKJS_FRAMES),
            'max_decoded_messages': (self.max_decoded_messages, MAX_DECODED_MESSAGES),
            'max_retained_observations': (self.max_retained_observations, MAX_RETAINED_OBSERVATIONS),
        }
        for name,(value,hard_max) in limits.items():
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise LimitError(f'invalid_caller_limit:{name}')
            if value > hard_max:
                raise LimitError('caller_limit_exceeds_hard_maximum')
        clock=self.monotonic_clock or time.monotonic; self.started=clock(); self.deadline=self.started+self.max_total_execution_seconds
    def _clock(self):
        clock = self.monotonic_clock or time.monotonic
        return clock()
    def remaining_total_deadline(self): return max(0.0,self.deadline-self._clock())
    def timeout(self, single):
        r=self.remaining_total_deadline()
        if r<=0: raise LimitError('bounded_time_limit_reached')
        return min(single,r)
    def effective_response_limit(self, per_response_limit=MAX_RESPONSE_PAYLOAD_BYTES): return min(per_response_limit, self.max_accounted_payload_bytes-self.total_accounted_payload_bytes)
    def _payload(self,n,kind):
        if n<0: raise LimitError('negative_payload_accounting')
        setattr(self, kind, getattr(self,kind)+n); self.total_accounted_payload_bytes+=n
        if self.total_accounted_payload_bytes>self.max_accounted_payload_bytes: raise LimitError('accounted_payload_limit_reached')
    def add_rest_request_payload(self,n): self._payload(n,'rest_request_payload_bytes')
    def add_sockjs_send_payload(self,n): self._payload(n,'sockjs_send_payload_bytes')
    def add_response_payload(self,n): self._payload(n,'response_payload_bytes')
    def add_rows(self,n, option=False):
        self.rest_rows+=n
        if self.rest_rows>self.max_bootstrap_rows: raise LimitError('bootstrap_row_limit_reached')
        if option and n>self.max_option_chain_rows: raise LimitError('option_chain_row_limit_reached')
    def add_frame(self): self.frames+=1; self.frames<=self.max_frames or (_ for _ in ()).throw(LimitError('frame_limit_reached'))
    def add_messages(self,n): self.decoded_messages+=n; self.decoded_messages<=self.max_decoded_messages or (_ for _ in ()).throw(LimitError('decoded_message_limit_reached'))
    def set_selector_counts(self,selectors,products,months,strikes,symbols=0):
        self.selectors=selectors; self.products=products; self.months=months; self.strikes=strikes; self.symbols=symbols
        if selectors>MAX_SELECTORS: raise LimitError('selector_count_limit_reached')
        if products>MAX_PRODUCTS: raise LimitError('product_count_limit_reached')
        if months>MAX_CONTRACT_MONTHS: raise LimitError('contract_month_limit_reached')
        if strikes>MAX_OPTION_STRIKES: raise LimitError('option_strike_limit_reached')
        if symbols>MAX_RUNTIME_SYMBOLS: raise LimitError('symbol_count_limit_reached')
    def retain_observation(self):
        self.retained_observations+=1
        if self.retained_observations>self.max_retained_observations: raise LimitError('retained_observation_limit_reached')
