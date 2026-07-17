import json
import time
import pytest
from pathlib import Path

from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_f1_security_master_snapshot_adapter import ValidatedVerifiedSecurityMasterSnapshot, build_verified_security_master_lookup
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

def test_pipeline_performance(tmp_path):
    req = load("bounded_request.json")
    source_data = load("source_observations.json")
    snap = load("security_identity_snapshot.json")
    man = load("security_identity_snapshot_manifest.json")
    
    val_sm = ValidatedVerifiedSecurityMasterSnapshot(
        snapshot=snap,
        manifest=man,
        lookup=build_verified_security_master_lookup(snap),
        validation={"valid": True}
    )
    
    # 1. Warm-up
    for _ in range(3):
        res = execute_watchlist(
            request=req,
            mode="fixture",
            bundle_type="snapshot",
            fixture_source_data=source_data,
            artifact_root=str(tmp_path),
            run_id="warmup_run",
            generated_at_utc="2026-07-16T03:00:00Z",
            security_master=val_sm
        )
        plan = json.loads((tmp_path / "warmup_run" / "execution_plan.json").read_text(encoding="utf-8"))
        bundle = json.loads((tmp_path / "warmup_run" / "watchlist_snapshot_bundle.json").read_text(encoding="utf-8"))
        
        build_watchlist_ai_context_package(
            validated_request=req,
            execution_plan=plan,
            execution_result=res,
            watchlist_bundle=bundle,
            generated_at_utc="2026-07-16T03:00:00Z"
        )
        
    # 2. Iterations
    iterations = 20
    durations = []
    
    for i in range(iterations):
        run_id = f"perf_run_{i}"
        t_start = time.perf_counter()
        
        res = execute_watchlist(
            request=req,
            mode="fixture",
            bundle_type="snapshot",
            fixture_source_data=source_data,
            artifact_root=str(tmp_path),
            run_id=run_id,
            generated_at_utc="2026-07-16T03:00:00Z",
            security_master=val_sm
        )
        plan = json.loads((tmp_path / run_id / "execution_plan.json").read_text(encoding="utf-8"))
        bundle = json.loads((tmp_path / run_id / "watchlist_snapshot_bundle.json").read_text(encoding="utf-8"))
        
        build_watchlist_ai_context_package(
            validated_request=req,
            execution_plan=plan,
            execution_result=res,
            watchlist_bundle=bundle,
            generated_at_utc="2026-07-16T03:00:00Z"
        )
        
        t_end = time.perf_counter()
        durations.append((t_end - t_start) * 1000.0) # 轉為毫秒
        
    # 計算 median, p95, max
    durations.sort()
    median_val = durations[iterations // 2]
    p95_val = durations[int(iterations * 0.95)]
    max_val = durations[-1]
    
    print(f"\n[R5A Performance Report] Median: {median_val:.2f}ms, P95: {p95_val:.2f}ms, Max: {max_val:.2f}ms")
    
    # 斷言符合無網絡效能契約 (< 1000 毫秒)
    assert median_val < 1000.0, f"Performance contract violated: median was {median_val:.2f}ms"
