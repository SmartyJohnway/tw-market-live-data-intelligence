import json, subprocess, sys
from pathlib import Path
import pytest
from scripts.m8r_03c_watchlist_bundle_builder import *
from scripts.m8r_03c_conversation_contract_validator import M8R03CValidationError
FIX=Path('tests/fixtures/m8r_03c')
def load(n): return json.loads((FIX/n).read_text())
def test_snapshot_usable_and_separation():
    b=build_watchlist_snapshot_bundle(request=load('snapshot_request.json'), observations=load('snapshot_observations.json'), generated_at_utc='2026-07-16T01:30:05Z')
    assert [t['target_id'] for t in b['targets']]==['TWSE:2330','TWSE:2317']
    assert all(c['coverage_state']=='usable' for c in b['coverage']['targets'])
    assert b['targets'][0]['current_evidence']['source_family']=='TWSE_MIS'
    assert b['targets'][0]['eod_reference']['source_family']=='TWSE_OPENAPI'
    assert not b['derived_metrics']
def test_snapshot_partial_unavailable_stale_raw_rejected():
    b=build_watchlist_snapshot_bundle(request=load('snapshot_request.json'), observations=load('snapshot_partial_observations.json'), generated_at_utc='2026-07-16T01:30:05Z')
    assert [c['coverage_state'] for c in b['coverage']['targets']]==['partial','partial']
    req=load('snapshot_request.json'); req['persistent_watchlist_reference']['enabled_target_ids'].append('TWSE:9999')
    b=build_watchlist_snapshot_bundle(request=req, observations=load('snapshot_observations.json'), generated_at_utc='2026-07-16T01:30:05Z')
    assert b['coverage']['targets'][-1]['coverage_state']=='unavailable'
    b=build_watchlist_snapshot_bundle(request=load('snapshot_request.json'), observations=load('snapshot_stale_observations.json'), generated_at_utc='2026-07-16T01:30:05Z')
    assert b['coverage']['targets'][0]['coverage_state']=='partial'
    obs=load('snapshot_observations.json'); obs[0]['raw_payload']={}
    with pytest.raises(M8R03CValidationError) as e: build_watchlist_snapshot_bundle(request=load('snapshot_request.json'), observations=obs, generated_at_utc='x')
    assert e.value.code=='source_fact_boundary_invalid'
def test_performance_metrics_and_boundaries():
    b=build_watchlist_performance_bundle(request=load('performance_request.json'), observations=load('performance_observations.json'), generated_at_utc='2026-07-16T01:30:05Z')
    per_target=len([m for m in b['derived_metrics'] if m['metric_id']=='return_1d'])
    assert per_target==2
    sample={m['metric_id']:m for m in b['derived_metrics'] if m['source_dependencies'][0]['target_id']=='TWSE:2330'}
    assert sample['return_1d']['calculation_status']=='calculated'
    assert sample['return_20d']['calculation_status']=='calculated'
    assert sample['range_high']['unit']=='price'
    assert sample['relative_return_vs_market']['calculation_status']=='calculated'
    for f in b['facts']:
        assert 'return_1d' not in f['values']
def test_performance_insufficient_duplicate_and_no_benchmark():
    b=build_watchlist_performance_bundle(request=load('performance_request.json'), observations=load('performance_insufficient_observations.json'), generated_at_utc='2026-07-16T01:30:05Z')
    assert any(m['metric_id']=='return_20d' and m['calculation_status']=='input_unavailable' for m in b['derived_metrics'])
    obs=load('performance_observations.json')[:44]
    b=build_watchlist_performance_bundle(request=load('performance_request.json'), observations=obs, generated_at_utc='2026-07-16T01:30:05Z')
    assert any(m['metric_id']=='relative_return_vs_market' and m['calculation_status']=='formula_not_applicable' for m in b['derived_metrics'])
    with pytest.raises(M8R03CValidationError) as e: build_watchlist_performance_bundle(request=load('performance_request.json'), observations=load('performance_duplicate_conflict_observations.json'), generated_at_utc='x')
    assert e.value.code=='source_fact_boundary_invalid'
def test_cli_runs_and_determinism(tmp_path):
    out1=tmp_path/'s1.json'; out2=tmp_path/'s2.json'
    cmd=[sys.executable,'scripts/run_m8r_03c_watchlist_bundle_fixture.py','--request',str(FIX/'snapshot_request.json'),'--observations',str(FIX/'snapshot_observations.json'),'--bundle-type','snapshot','--output',str(out1)]
    assert subprocess.run(cmd, capture_output=True, text=True).returncode==0
    cmd[-1]=str(out2); assert subprocess.run(cmd, capture_output=True, text=True).returncode==0
    assert out1.read_text()==out2.read_text()
    assert subprocess.run([sys.executable,'scripts/run_m8r_03c_watchlist_bundle_fixture.py','--network'], capture_output=True, text=True).returncode!=0
