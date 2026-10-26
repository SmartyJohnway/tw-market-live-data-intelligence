"""Composite closure authority uses the existing plan/authorization/request identity path."""
import copy
import socket
import pytest
from scripts.phase_i_i3_execution_pipeline import prepare_i3_authorized_execution
from scripts.phase_i_i3_dormant_orchestration import prepare_dormant_i3_execution
from tests.unit.test_phase_i_i3_a4_activation import _preview
from tests.unit.test_phase_i_i3_execution_date import _calendar
from tests.unit.i3_closure_authority_test_helpers import closure_authority_fixture
from tests.unit.test_l7_a5_r4_unscheduled_closure import EVALUATION, CLOSED


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*a,**k):pytest.fail('R4 date binding cannot probe sources')
    monkeypatch.setattr(socket.socket,'connect',denied);monkeypatch.setattr(socket,'getaddrinfo',denied)


def decision():
    return {'decision':'approved','decision_reason':'synthetic offline R4 identity proof','owner_identity_reference':'offline-test',
            'owner_review_reference':'R4-synthetic','reviewed_at':'2026-10-25T17:42:41Z','issued_at':'2026-10-25T17:42:41Z',
            'expires_at':'2026-10-25T18:42:41Z','single_use':True,'replay_policy':'deny_replay','maximum_use_count':1,
            'approval_scope_mode':'whole_plan_executable_scope','approved_operation_ids':[],'approved_batch_group_ids':[],
            'approved_batch_membership':{}}


def test_override_rebinds_date_plan_authorization_and_execution_request_identities():
    _,_,preview=_preview([{'input':'1101','market_hint':'TWSE'}],request_id='r4-binding-proof')
    original=copy.deepcopy(preview);annual=_calendar(holidays={'2026-10-26'})
    common={'evaluation_time':EVALUATION,'official_calendar':annual,'closure_events':[],
            'calendar_authority_ref':'synthetic:scheduled','closure_authority_complete':True,'decision_input':decision()}
    # Baseline is an explicitly CLEAR counterfactual test authority, never absence of coverage.
    baseline=prepare_i3_authorized_execution(preview,**common,**closure_authority_fixture(EVALUATION))
    closed=prepare_i3_authorized_execution(preview,**common,**closure_authority_fixture(EVALUATION,overrides=[CLOSED]))
    assert baseline['resolved_source_trade_date']=='2026-10-23' and closed['resolved_source_trade_date']=='2026-10-22'
    for key in ['plan_hash','plan_id']:assert baseline['plan'][key]!=closed['plan'][key]
    assert baseline['authorization']['authorization_hash']!=closed['authorization']['authorization_hash']
    a,b=baseline['execution_requests'][0],closed['execution_requests'][0]
    assert a['execution_request_hash']!=b['execution_request_hash'] and a['execution_request_id']!=b['execution_request_id']
    assert a['parameters']=={'resolved_source_trade_date':'2026-10-23'} and b['parameters']=={'resolved_source_trade_date':'2026-10-22'}
    assert set(closed['plan']['source_date_binding'])=={'market','evaluation_time','resolved_source_trade_date','calendar_authority_ref','closure_authority_ref'}
    assert closed['plan']['source_date_binding']['closure_authority_ref'].startswith('I3_COMPOSITE_CLOSURE:sha256:')
    assert closed['network_dispatched'] is False and preview==original


@pytest.mark.parametrize('mode',['production','dormant'])
def test_missing_composite_authority_stops_before_authorization_or_request_projection(monkeypatch,mode):
    import scripts.phase_i_i3_execution_pipeline as production
    import scripts.phase_i_i3_dormant_orchestration as dormant
    _,_,preview=_preview([{'input':'1101','market_hint':'TWSE'}],request_id='r4-fail-before-auth')
    module=production if mode=='production' else dormant;calls=[]
    monkeypatch.setattr(module,'build_execution_authorization',lambda *a,**k:calls.append('authorization'))
    monkeypatch.setattr(module,'build_execution_request_projection',lambda *a,**k:calls.append('request'))
    kwargs={'evaluation_time':EVALUATION,'official_calendar':_calendar(holidays={'2026-10-26'}),'closure_events':[],
            'calendar_authority_ref':'synthetic:scheduled','closure_authority_ref':'DGPA:negative-only','closure_authority_complete':True}
    with pytest.raises(ValueError,match='composite_closure_authority_required'):
        if mode=='production':prepare_i3_authorized_execution(preview,**kwargs,decision_input=decision())
        else:prepare_dormant_i3_execution(preview,**kwargs,owner_identity_reference='offline-test',owner_review_reference='R4')
    assert calls==[]
