import json
import time
import pytest
from pathlib import Path

from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package
from scripts.m8r_03e_r5a_cross_layer_fixture import generate_fixtures_to_disk

FIX_DIR = Path("tests/fixtures/m8r_03e_r5a")

def load(name):
    return json.loads((FIX_DIR / name).read_text(encoding="utf-8"))

def test_pipeline_performance(tmp_path):
    req = load("bounded_request.json")
    source_data = load("source_observations.json")
    cap_registry = load("source_capability_snapshot.json")
    
    val_sm = load_verified_security_master_snapshot(
        str(FIX_DIR / "security_identity_snapshot.json"),
        str(FIX_DIR / "security_identity_snapshot_manifest.json"),
        allow_fixture_snapshot=True
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
            security_master=val_sm,
            source_capability_registry=cap_registry
        )
        plan = json.loads((tmp_path / "warmup_run" / "execution_plan.json").read_text(encoding="utf-8"))
        bundle = json.loads((tmp_path / "warmup_run" / "watchlist_snapshot_bundle.json").read_text(encoding="utf-8"))
        
        pkg = build_watchlist_ai_context_package(
            validated_request=req,
            execution_plan=plan,
            execution_result=res,
            watchlist_bundle=bundle,
            generated_at_utc="2026-07-16T03:00:00Z"
        )
        validate_watchlist_ai_context_package(pkg, upstream_artifacts={"validated_request": req, "execution_plan": plan, "execution_result": res, "watchlist_bundle": bundle})
        
    # 2. Iterations
    iterations = 20
    e2e_durations = []
    gen_durations = []
    val_durations = []
    
    for i in range(iterations):
        # 2a. 測量 Fixture 產生時間
        gen_path = tmp_path / f"gen_run_{i}"
        gen_path.mkdir()
        t_gen_start = time.perf_counter()
        generate_fixtures_to_disk(gen_path, seed_val=f"seed-{i}", clock_val="2026-07-16T03:00:00Z")
        t_gen_end = time.perf_counter()
        gen_durations.append((t_gen_end - t_gen_start) * 1000.0)
        
        # 2b. 測量 E2E Watchlist 執行 + Context Package 建立時間
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
            security_master=val_sm,
            source_capability_registry=cap_registry
        )
        plan = json.loads((tmp_path / run_id / "execution_plan.json").read_text(encoding="utf-8"))
        bundle = json.loads((tmp_path / run_id / "watchlist_snapshot_bundle.json").read_text(encoding="utf-8"))
        
        pkg = build_watchlist_ai_context_package(
            validated_request=req,
            execution_plan=plan,
            execution_result=res,
            watchlist_bundle=bundle,
            generated_at_utc="2026-07-16T03:00:00Z"
        )
        
        t_end = time.perf_counter()
        e2e_durations.append((t_end - t_start) * 1000.0)
        
        # 2c. 測量 Schema 驗證時間
        t_val_start = time.perf_counter()
        validate_watchlist_ai_context_package(pkg, upstream_artifacts={"validated_request": req, "execution_plan": plan, "execution_result": res, "watchlist_bundle": bundle})
        t_val_end = time.perf_counter()
        val_durations.append((t_val_end - t_val_start) * 1000.0)
        
    def calc_metrics(durations):
        durations.sort()
        n = len(durations)
        median_val = durations[n // 2]
        p95_idx = int(round(0.95 * (n - 1)))
        p95_val = durations[p95_idx]
        max_val = durations[-1]
        return median_val, p95_val, max_val
        
    e2e_med, e2e_p95, e2e_max = calc_metrics(e2e_durations)
    gen_med, gen_p95, gen_max = calc_metrics(gen_durations)
    val_med, val_p95, val_max = calc_metrics(val_durations)
    
    print(f"\n[R5A Performance Report - Basis: Provisional non-network execution baseline]")
    print(f"E2E Pipeline (20 runs): Median: {e2e_med:.2f}ms, P95: {e2e_p95:.2f}ms, Max: {e2e_max:.2f}ms")
    print(f"Fixture Generation (20 runs): Median: {gen_med:.2f}ms, P95: {gen_p95:.2f}ms, Max: {gen_max:.2f}ms")
    print(f"Schema Validation (20 runs): Median: {val_med:.2f}ms, P95: {val_p95:.2f}ms, Max: {val_max:.2f}ms")
    
    # 斷言符合效能契約
    assert e2e_med < 1000.0, f"E2E median violated: {e2e_med:.2f}ms"
    assert e2e_p95 < 1500.0, f"E2E P95 violated: {e2e_p95:.2f}ms"
    assert e2e_max < 2000.0, f"E2E max violated: {e2e_max:.2f}ms"
    assert gen_med < 1000.0, f"Fixture Gen median violated: {gen_med:.2f}ms"
    assert val_med < 500.0, f"Schema Val median violated: {val_med:.2f}ms"
