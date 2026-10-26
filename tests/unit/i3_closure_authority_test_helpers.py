"""Synthetic, independently adjudicated composite coverage for offline tests only.
No calendar or absence of DGPA events is promoted to real exchange authority.
"""
import copy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from scripts.phase_i_i3_execution_date import composite_closure_authority_ref
from scripts.m8r_05b_01.canonical import sha256_json


def closure_authority_fixture(evaluation, *, events=None, overrides=None, dates=None):
    local = datetime.fromisoformat(evaluation.replace('Z', '+00:00')).astimezone(ZoneInfo('Asia/Taipei')).date()
    coverage = dates if dates is not None else [(local-timedelta(days=i)).isoformat() for i in range(10)]
    authority = {
        'schema_version': 'i3_composite_closure_authority.v1', 'market': 'TWSE',
        'closure_events': copy.deepcopy(events or []),
        'taipei_closure_coverage_dates': list(coverage),
        'exchange_session_coverage_dates': list(coverage),
        'exchange_session_overrides': copy.deepcopy(overrides or []),
        'provenance': {
            'taipei_closure_authority_sha256': sha256_json({'synthetic_test_only': 'taipei', 'coverage': coverage, 'events': events or []}),
            'exchange_session_authority_sha256': sha256_json({'synthetic_test_only': 'exchange', 'coverage': coverage, 'overrides': overrides or []}),
        },
    }
    return {'closure_authority': authority, 'closure_authority_ref': composite_closure_authority_ref(authority)}
