"""R4 synthetic session adjudication; incident facts are Owner inputs, never source probes."""
import copy
import hashlib
import json
import socket
from datetime import date, timedelta
from pathlib import Path

import pytest
from scripts.phase_i_i3_execution_date import resolve_i3_twse_source_trade_date, composite_closure_authority_ref
from tests.unit.i3_closure_authority_test_helpers import closure_authority_fixture
from tests.unit.test_phase_i_i3_execution_date import _calendar

EVALUATION = '2026-10-26T01:42:41.461562+08:00'
CLOSED = {'market': 'TWSE', 'date': '2026-10-23', 'session_status': 'closed',
          'closure_scope': 'full_day', 'reason': 'unscheduled_exchange_closure'}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail('R4 source probing forbidden')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def calendar():
    return _calendar(holidays={'2026-10-26'})


def resolve(kwargs=None, *, evaluation=EVALUATION, cal=None, events=None):
    events = [] if events is None else events
    kwargs = closure_authority_fixture(evaluation, events=events) if kwargs is None else kwargs
    return resolve_i3_twse_source_trade_date(evaluation_time=evaluation, official_calendar=calendar() if cal is None else cal,
        closure_events=events, calendar_authority_ref='synthetic:annual-scheduled-calendar', closure_authority_complete=True, **kwargs)


def rebind(kwargs):
    kwargs['closure_authority_ref'] = composite_closure_authority_ref(kwargs['closure_authority'])
    return kwargs


def test_owner_incident_skips_unscheduled_closed_weekday():
    authority = closure_authority_fixture(EVALUATION, overrides=[CLOSED])
    assert next(x for x in calendar()['dates'] if x['date']=='2026-10-23')['is_trading_day'] is True
    assert resolve(authority)['resolved_source_trade_date'] == '2026-10-22'
    # Counterfactual explicitly adjudicated CLEAR fixture, not missing authority.
    assert resolve()['resolved_source_trade_date'] == '2026-10-23'


def test_accepted_annual_artifact_remains_unchanged_and_override_corrects_effective_date():
    p=Path(__file__).resolve().parents[2]/'docs/governance/phase_l/acceptance_runs/l3-a6-p0-20261016T033822Z/twse_trading_calendar_2026.json'
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='f8a2e6908cda1595587d29f4eb3c8fd66a11104b9f41558c1d4735243141883a'
    annual=json.loads(p.read_text(encoding='utf-8'))
    assert resolve(closure_authority_fixture(EVALUATION,overrides=[CLOSED]),cal=annual)['resolved_source_trade_date']=='2026-10-22'


def test_DGPA_negative_and_complete_boolean_alone_cannot_qualify_exchange_coverage():
    with pytest.raises(ValueError,match='composite_closure_authority_required'):
        resolve({'closure_authority_ref':'DGPA:negative_lookup_complete'})


@pytest.mark.parametrize('field', ['taipei_closure_coverage_dates','exchange_session_coverage_dates'])
@pytest.mark.parametrize('missing_day', ['2026-10-26','2026-10-23','2026-10-22'])
def test_every_actually_traversed_day_requires_both_coverage_families(field,missing_day):
    # Missing exchange coverage on the CLOSED day also invalidates the override.
    kw=closure_authority_fixture(EVALUATION,overrides=[CLOSED]);kw['closure_authority'][field].remove(missing_day)
    with pytest.raises(ValueError,match='coverage'):
        resolve(rebind(kw))


def test_unadjudicated_exchange_candidate_without_override_fails_closed():
    kw=closure_authority_fixture(EVALUATION);kw['closure_authority']['exchange_session_coverage_dates'].remove('2026-10-23')
    with pytest.raises(ValueError,match='closure_coverage_unresolved'):
        resolve(rebind(kw))


def test_irrelevant_untraversed_day_does_not_require_coverage():
    dates=['2026-10-26','2026-10-25','2026-10-24','2026-10-23','2026-10-22']
    assert resolve(closure_authority_fixture(EVALUATION,overrides=[CLOSED],dates=dates))['resolved_source_trade_date']=='2026-10-22'


@pytest.mark.parametrize('scope,expected',[('full_day','2026-10-22'),('morning','2026-10-22'),('afternoon','2026-10-23')])
def test_existing_taipei_scope_semantics_preserved(scope,expected):
    evaluation='2026-10-23T21:00:00+08:00'
    events=[{'status':'Actual','area_name':'臺北市','area_level':'municipality','work_status':'closed',
             'decision_status':'closure_confirmed','target_date':'2026-10-23','closure_scope':scope}]
    assert resolve(closure_authority_fixture(evaluation,events=events),evaluation=evaluation,events=events)['resolved_source_trade_date']==expected


@pytest.mark.parametrize('evaluation,expected',[
    ('2026-10-23T19:59:59+08:00','2026-10-22'),
    ('2026-10-23T20:00:00+08:00','2026-10-23'),
    ('2026-10-25T21:00:00+08:00','2026-10-23'),
    ('2026-10-26T21:00:00+08:00','2026-10-23'),
])
def test_normal_cutoff_weekend_scheduled_holiday_preserved(evaluation,expected):
    assert resolve(evaluation=evaluation)['resolved_source_trade_date']==expected


@pytest.mark.parametrize('mutation',[
    'market','status','scope','reason','compact_date','week_date','invalid_date','unknown_key','missing_key','non_object',
])
def test_override_strict_shape_and_closed_only_scope(mutation):
    row=copy.deepcopy(CLOSED)
    if mutation=='market':row['market']='TPEX'
    elif mutation=='status':row['session_status']='open'
    elif mutation=='scope':row['closure_scope']='morning'
    elif mutation=='reason':row['reason']='arbitrary_provider_text'
    elif mutation=='compact_date':row['date']='20261023'
    elif mutation=='week_date':row['date']='2026-W43-5'
    elif mutation=='invalid_date':row['date']='2026-02-30'
    elif mutation=='unknown_key':row['source_url']='https://invalid.example/'
    elif mutation=='missing_key':row.pop('date')
    else:row='closed'
    with pytest.raises(ValueError):resolve(closure_authority_fixture(EVALUATION,overrides=[row]))


@pytest.mark.parametrize('conflict',[False,True])
def test_duplicate_identical_or_conflicting_override_rejected(conflict):
    second=copy.deepcopy(CLOSED)
    if conflict:second['session_status']='open'
    with pytest.raises(ValueError):resolve(closure_authority_fixture(EVALUATION,overrides=[CLOSED,second]))


@pytest.mark.parametrize('mutation',['unknown_shape','bad_schema','bad_market','missing_provenance','bad_provenance','unknown_provenance','duplicate_coverage','oversized_coverage','oversized_overrides'])
def test_composite_authority_strict_bounded_and_provenanced(mutation):
    kw=closure_authority_fixture(EVALUATION);a=kw['closure_authority']
    if mutation=='unknown_shape':a['source_url']='https://invalid.example/'
    elif mutation=='bad_schema':a['schema_version']='other'
    elif mutation=='bad_market':a['market']='TPEX'
    elif mutation=='missing_provenance':a.pop('provenance')
    elif mutation=='bad_provenance':a['provenance']['exchange_session_authority_sha256']='https://invalid.example/'
    elif mutation=='unknown_provenance':a['provenance']['source']='other'
    elif mutation=='duplicate_coverage':a['exchange_session_coverage_dates'].append(a['exchange_session_coverage_dates'][0])
    elif mutation=='oversized_coverage':a['exchange_session_coverage_dates']=[(date(2026,10,26)-timedelta(days=i)).isoformat() for i in range(369)]
    else:a['exchange_session_overrides']=[copy.deepcopy(CLOSED) for _ in range(369)]
    with pytest.raises(ValueError):resolve(rebind(kw))


def test_tampering_after_hash_binding_rejected():
    kw=closure_authority_fixture(EVALUATION);kw['closure_authority']['exchange_session_overrides']=[copy.deepcopy(CLOSED)]
    with pytest.raises(ValueError,match='hash_mismatch'):resolve(kw)


def test_caller_events_cannot_diverge_from_composite_hash_bound_events():
    with pytest.raises(ValueError,match='events_mismatch'):
        resolve(closure_authority_fixture(EVALUATION),events=[{'source':'unbound'}])


def test_input_authority_and_annual_calendar_are_not_mutated():
    kw=closure_authority_fixture(EVALUATION,overrides=[CLOSED]);annual=calendar();before=copy.deepcopy((kw,annual));resolve(kw,cal=annual);assert (kw,annual)==before
