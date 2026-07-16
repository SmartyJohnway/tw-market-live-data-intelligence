from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import m8r_03d_watchlist_controlled_executor as executor
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_watchlist_execution_plan import (
    AUTH_SCHEMA_VERSION,
    MAX_WATCHLIST_TARGETS,
    build_execution_plan,
    canonical_request_hash,
)

pytestmark = [pytest.mark.core, pytest.mark.component_security]

FIX = Path('tests/fixtures/m8r_03d')
C = Path('tests/fixtures/m8r_03c')
SECURITY_MASTER = {
    ('listed', '2330'): {'instrument_type': 'equity', 'name': '台積電', 'listing_status': 'active', 'lifecycle_state': 'active', 'source': 'test'},
    ('listed', '2317'): {'instrument_type': 'equity', 'name': '鴻海', 'listing_status': 'active', 'lifecycle_state': 'active', 'source': 'test'},
    ('tpex_otc', '6488'): {'instrument_type': 'equity', 'name': '環球晶', 'listing_status': 'active', 'lifecycle_state': 'active', 'source': 'test'},
}

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))

def auth(req: dict, plan: dict, **patch) -> dict:
    base = {
        'schema_version': AUTH_SCHEMA_VERSION,
        'authorization_id': 'r2-auth',
        'one_shot_nonce': 'r2-nonce',
        'issued_at_utc': '2026-07-16T00:00:00Z',
        'expires_at_utc': '2026-07-17T00:00:00Z',
        'authorized_request_hash': canonical_request_hash(req),
        'authorized_bundle_types': ['snapshot'],
        'authorized_source_families': ['TWSE_MIS', 'TWSE_OPENAPI', 'TPEX_OPENAPI'],
        'authorized_target_ids': plan['target_order'],
        'max_target_count': MAX_WATCHLIST_TARGETS,
        'network_execution_allowed': True,
        'one_shot_only': True,
        'polling_allowed': False,
        'scheduler_allowed': False,
        'persistent_storage_allowed': False,
        'raw_payload_retention_allowed': False,
        'operator_approval': {'approved_by': 'r2-test'},
    }
    base.update(patch)
    return base

def fake_executors(calls: list[str]) -> dict:
    data = load(FIX / 'mixed_snapshot_source_data.json')
    def run(fam):
        def _inner(target_ids, **_kwargs):
            calls.append(fam)
            return {'targets': {tid: {fam: data['targets'][tid][fam]} for tid in target_ids if fam in data['targets'][tid]}}
        return _inner
    return {'TWSE_MIS': run('TWSE_MIS'), 'TWSE_OPENAPI': run('TWSE_OPENAPI'), 'TPEX_OPENAPI': run('TPEX_OPENAPI')}

def request_and_plan():
    req = load(FIX / 'mixed_snapshot_request.json')
    plan = build_execution_plan(req, bundle_type='snapshot', security_master=SECURITY_MASTER)
    return req, plan

def test_missing_authorization_with_valid_output_path_rejected_by_authorization_layer(tmp_path, monkeypatch):
    monkeypatch.setattr(executor, 'AUTHORIZATION_CONSUMPTION_ROOT', tmp_path / 'receipts')
    req, _plan = request_and_plan(); calls = []
    out = execute_watchlist(req, mode='execute', bundle_type='snapshot', artifact_root=str(tmp_path / 'artifacts'), executors=fake_executors(calls), security_master=SECURITY_MASTER)
    assert out['status'] == 'authorization_failed'
    assert {i['code'] for i in out['issues']} == {'authorization_required'}
    assert calls == []
    assert not list((tmp_path / 'artifacts').rglob('*.json'))

def test_wrong_scope_authorization_with_valid_output_path_rejected_by_authorization_layer(tmp_path, monkeypatch):
    monkeypatch.setattr(executor, 'AUTHORIZATION_CONSUMPTION_ROOT', tmp_path / 'receipts')
    req, plan = request_and_plan(); calls = []
    wrong = auth(req, plan, authorized_source_families=['TWSE_MIS'])
    out = execute_watchlist(req, mode='execute', bundle_type='snapshot', authorization=wrong, artifact_root=str(tmp_path / 'artifacts'), executors=fake_executors(calls), security_master=SECURITY_MASTER)
    assert out['status'] == 'authorization_failed'
    assert 'unauthorized_source_family' in {i['code'] for i in out['issues']}
    assert calls == []

def test_valid_authorization_with_escaping_output_path_rejected_before_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(executor, 'AUTHORIZATION_CONSUMPTION_ROOT', tmp_path / 'receipts')
    req, plan = request_and_plan(); calls = []
    with pytest.raises(ValueError, match='unsafe_artifact_root'):
        execute_watchlist(req, mode='execute', bundle_type='snapshot', authorization=auth(req, plan), artifact_root=str(Path('artifacts') / '..' / 'escape'), executors=fake_executors(calls), security_master=SECURITY_MASTER)
    assert calls == []

def test_invalid_authorization_with_escaping_output_path_does_not_execute_or_write(tmp_path, monkeypatch):
    monkeypatch.setattr(executor, 'AUTHORIZATION_CONSUMPTION_ROOT', tmp_path / 'receipts')
    req, plan = request_and_plan(); calls = []
    invalid = auth(req, plan, authorized_request_hash='0' * 64)
    with pytest.raises(ValueError, match='unsafe_artifact_root'):
        execute_watchlist(req, mode='execute', bundle_type='snapshot', authorization=invalid, artifact_root=str(Path('artifacts') / '..' / 'escape'), executors=fake_executors(calls), security_master=SECURITY_MASTER)
    assert calls == []
    assert not (tmp_path / 'escape').exists()

def test_valid_authorization_and_valid_contained_output_path_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr(executor, 'AUTHORIZATION_CONSUMPTION_ROOT', tmp_path / 'receipts')
    req, plan = request_and_plan(); calls = []
    out = execute_watchlist(req, mode='execute', bundle_type='snapshot', authorization=auth(req, plan), artifact_root=str(tmp_path / 'artifacts'), generated_at_utc='2026-07-16T01:30:05Z', executors=fake_executors(calls), security_master=SECURITY_MASTER)
    assert out['status'] == 'success'
    assert set(calls) == {'TWSE_MIS', 'TWSE_OPENAPI', 'TPEX_OPENAPI'}
    assert Path(out['artifact_paths']['bundle']).is_file()
    assert Path(out['artifact_paths']['bundle']).resolve().is_relative_to((tmp_path / 'artifacts').resolve())

def test_network_execution_authorization_does_not_grant_replay_or_arbitrary_output_root(tmp_path, monkeypatch):
    monkeypatch.setattr(executor, 'AUTHORIZATION_CONSUMPTION_ROOT', tmp_path / 'receipts')
    req, plan = request_and_plan(); calls = []
    token = auth(req, plan, authorization_id='scope-bound', one_shot_nonce='once')
    ok = execute_watchlist(req, mode='execute', bundle_type='snapshot', authorization=token, artifact_root=str(tmp_path / 'first'), generated_at_utc='2026-07-16T01:30:05Z', executors=fake_executors(calls), security_master=SECURITY_MASTER)
    replay = execute_watchlist(req, mode='execute', bundle_type='snapshot', authorization=token, artifact_root=str(tmp_path / 'second'), generated_at_utc='2026-07-16T01:31:05Z', executors=fake_executors(calls), security_master=SECURITY_MASTER)
    assert ok['status'] == 'success'
    assert replay['status'] == 'authorization_failed'
    assert 'authorization_replayed' in {i['code'] for i in replay['issues']}
