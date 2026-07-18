#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import m8r_03d_watchlist_controlled_executor as executor
from scripts.m8r_03d_watchlist_controlled_executor import execute_watchlist
from scripts.m8r_03d_watchlist_execution_plan import build_execution_plan, canonical_request_hash
from scripts.m8r_03d_f1_security_master_snapshot_adapter import ValidatedVerifiedSecurityMasterSnapshot, build_verified_security_master_lookup
from scripts.m8r_03d_f1_security_master_snapshot_exporter import compute_skill_contract_hash, compute_schema_hash, SNAPSHOT_SCHEMA_VERSION, MANIFEST_SCHEMA_VERSION, PRODUCER_VERSION
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package, build_context_manifest, render_watchlist_ai_context_preview
from scripts.m8r_03e_conversation_handoff_builder import build_watchlist_conversation_handoff
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package, validate_watchlist_conversation_handoff, validate_watchlist_ai_context_manifest, sha256_json, canonical_json
from scripts.m8r_filesystem_safety import atomic_write_text, validate_authorized_root, safe_destination

@dataclass(frozen=True)
class R5AFixtureClock:
    now_utc: str

@dataclass(frozen=True)
class R5AFixtureSeed:
    value: str

def make_security_record(rec_id, target_id, symbol, name_zh, market, instrument_type, lifecycle_state="active", status="observed_in_capture", execution_status="allowed", caveats=None, reason_codes=None):
    record = {
        "record_id": rec_id,
        "canonical_target_id": target_id,
        "identity": {
            "security_code": symbol,
            "security_name_zh": name_zh,
            "security_name_en": f"EnglishName {symbol}",
            "isin": f"TW000{symbol}00",
            "cfi": "ESVUFR" if instrument_type == "equity" else "CEJVXX"
        },
        "classification": {
            "asset_class": "securities",
            "instrument_family": "equity" if instrument_type == "equity" else "structured_product",
            "instrument_type": instrument_type,
            "market": market.upper(), # 必須大寫以符合 _validate_canonical_identity
            "board": "main",
            "listed_common_stock_core_flag": instrument_type == "equity",
            "classification_status": "confirmed_official_single_lane",
            "reason_codes": [],
            "conflicts": []
        },
        "observation": {
            "status": status,
            "observed_at": "2026-07-16T03:00:00Z",
            "source_updated_date": "2026-07-16"
        },
        "lifecycle": {
            "state": lifecycle_state,
            "resolution_status": "resolved" if lifecycle_state != "unknown" else "unavailable",
            "as_of": "2026-07-16",
            "basis_event_ids": [],
            "events": []
        },
        "execution_eligibility": {
            "status": execution_status,
            "reason_codes": reason_codes or []
        },
        "evidence_summary": {},
        "conflicts": [],
        "caveats": caveats or []
    }
    record["record_hash"] = sha256_json({k:v for k,v in record.items() if k != "record_hash"})
    return record

def build_r5a_security_master(clock_str: str, seed: R5AFixtureSeed) -> tuple[dict, dict]:
    import random
    rng = random.Random(seed.value)
    name_suffix = f"-{seed.value}"
    
    records = [
        make_security_record("rec-01", "TWSE:2330", "2330", f"台積電{name_suffix}", "TWSE", "equity"),
        make_security_record("rec-02", "TWSE:2317", "2317", f"鴻海{name_suffix}", "TWSE", "equity"),
        make_security_record("rec-03", "TPEX:6488", "6488", f"環球晶{name_suffix}", "TPEX", "equity"),
        make_security_record("rec-04", "TWSE:0050", "0050", f"元大台灣50{name_suffix}", "TWSE", "etf"),
        make_security_record("rec-05", "TPEX:5347", "5347", f"世界{name_suffix}", "TPEX", "equity"),
        make_security_record("rec-06", "TWSE:0056", "0056", f"元大高股息{name_suffix}", "TWSE", "etf"),
        make_security_record("rec-07", "TWSE:2308", "2308", f"台達電{name_suffix}", "TWSE", "equity"),
        make_security_record("rec-08", "TWSE:2382", "2382", f"廣達{name_suffix}", "TWSE", "equity"),
        make_security_record("rec-09", "TWSE:3008", "3008", f"大立光{name_suffix}", "TWSE", "equity"),
    ]
    
    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_id": f"snap-r5a-{seed.value}",
        "generated_at_utc": clock_str,
        "effective_observation_date": "2026-07-16",
        "source_skill": {
            "name": "tw-security-master-classifier",
            "skill_version": "1.0.0",
            "skill_path": "skills/tw-security-master-classifier",
            "skill_contract_hash": compute_skill_contract_hash()
        },
        "coverage": {
            "markets": ["twse", "tpex"],
            "instrument_types": ["equity", "etf"],
            "record_count": len(records),
            "lifecycle_event_count": 0,
            "quarantined_lifecycle_event_count": 0,
            "total_lifecycle_event_count": 0,
            "coverage_status": "complete"
        },
        "quarantined_lifecycle_events": [],
        "records": records
    }
    
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "snapshot_id": f"snap-r5a-{seed.value}",
        "snapshot_path": "security_identity_snapshot.json", # 必須提供此欄位以符合 schema 規範
        "generated_at_utc": clock_str,
        "effective_observation_date": "2026-07-16",
        "producer_version": PRODUCER_VERSION,
        "schema_sha256": compute_schema_hash(),
        "record_count": len(records),
        "lifecycle_event_count": 0,
        "coverage": snapshot["coverage"],
        "skill_contract_hash": snapshot["source_skill"]["skill_contract_hash"],
        "snapshot_sha256": sha256_json(snapshot),
        "validation_status": "passed",
        "validation_issues": []
    }
    
    return snapshot, manifest

def build_r5a_cross_layer_fixture(
    *,
    seed: R5AFixtureSeed,
    clock: R5AFixtureClock,
) -> dict[str, Any]:
    clock_str = clock.now_utc
    import random
    rng = random.Random(seed.value)
    
    # 根據 seed 產生價格
    p_2330 = round(1000.0 + rng.uniform(-10.0, 10.0), 1)
    p_0050 = round(180.0 + rng.uniform(-5.0, 5.0), 2)
    p_5347 = round(120.0 + rng.uniform(-2.0, 2.0), 2)
    p_0056 = round(40.0 + rng.uniform(-1.0, 1.0), 2)
    p_2308 = round(350.0 + rng.uniform(-10.0, 10.0), 1)
    p_2382 = round(250.0 + rng.uniform(-8.0, 8.0), 1)
    
    # 1. Bounded Request
    request = {
        "schema_version": "m8r_ai_evidence_request.v1",
        "request_id": f"m8r03c-{seed.value}",
        "original_user_text": "我的觀察清單現在怎麼樣？",
        "conversation_intent": {
            "schema_version": "m8r_ai_market_conversation_intent.v1",
            "original_user_text": "我的觀察清單現在怎麼樣？",
            "scope_modes": ["watchlist"],
            "time_scope": {
                "mode": "current",
                "explicit_range": None,
                "lookback_trading_days": None
            },
            "evidence_depth": "standard",
            "explicit_user_constraints": {},
            "inferred_defaults": {},
            "clarification_required": False,
            "clarification_reason": None
        },
        "persistent_watchlist_reference": {
            "watchlist_id": f"wl-r5a-{seed.value}",
            "source": "local_fixture",
            "enabled_target_ids": [
                "TWSE:2330",
                "TWSE:2317",
                "TPEX:6488",
                "TWSE:0050",
                "TPEX:5347",
                "TWSE:0056",
                "TWSE:2308",
                "TWSE:2382",
                "TWSE:3008",
                "TWSE:9999"
            ]
        },
        "dynamic_entity_requests": [],
        "market_context_requests": [],
        "required_evidence": [
            {
                "capability_id": "twse_mis_listed_liveish",
                "fallback_behavior": "record_missing",
                "preferred_timing_class": "liveish_intraday_snapshot",
                "priority": "required",
                "required_for_answer": True,
                "source_family_preference": ["TWSE_MIS"],
                "time_scope": {
                    "mode": "current",
                    "explicit_range": None,
                    "lookback_trading_days": None
                }
            }
        ],
        "useful_evidence": [
            {
                "capability_id": "twse_official_eod",
                "fallback_behavior": "record_missing",
                "preferred_timing_class": "official_eod",
                "priority": "useful",
                "required_for_answer": False,
                "source_family_preference": ["TWSE_OPENAPI", "TPEX_OPENAPI"],
                "time_scope": {
                    "mode": "current",
                    "explicit_range": None,
                    "lookback_trading_days": None
                }
            }
        ],
        "optional_evidence": [],
        "execution_policy": {
            "operator_confirmation_required": False,
            "network_allowed": False,
            "polling": False,
            "scheduler": False
        },
        "explicit_user_constraints": {},
        "inferred_defaults": {},
        "identity_resolver_output": {},
        "clarification_required": False,
        "clarification_reason": None,
        "follow_up_context": None
    }
    
    # 2. Source observations (raw inputs for fixture)
    source_data = {
        "targets": {
            "TWSE:2330": {
                "TWSE_MIS": {
                    "symbol": "2330",
                    "market": "TWSE",
                    "price": p_2330,
                    "change": 10.0,
                    "source_timestamp": "2026-07-16T02:59:50Z",
                    "retrieved_at": clock_str
                },
                "TWSE_OPENAPI": {
                    "symbol": "2330",
                    "market": "listed",
                    "trade_date": "2026-07-15",
                    "retrieved_at_utc": clock_str,
                    "price": {"open": "990", "high": "1005", "low": "985", "close": "990"},
                    "activity": {"trade_volume": 20000}
                }
            },
            "TWSE:2317": {
                # TWSE_MIS 缺失 (模擬 live-ish 失敗)
                "TWSE_OPENAPI": {
                    "symbol": "2317",
                    "market": "listed",
                    "trade_date": "2026-07-15",
                    "retrieved_at_utc": clock_str,
                    "price": {"open": "200", "high": "205", "low": "198", "close": "202"},
                    "activity": {"trade_volume": 15000}
                }
            },
            "TPEX:6488": {
                # TPEX 只給 EOD
                "TPEX_OPENAPI": {
                    "symbol": "6488",
                    "market": "tpex_otc",
                    "trade_date": "2026-07-15",
                    "retrieved_at_utc": clock_str,
                    "price": {"open": "500", "high": "510", "low": "495", "close": "505"},
                    "activity": {"trade_volume": 500}
                }
            },
            "TWSE:0050": {
                "TWSE_MIS": {
                    "symbol": "0050",
                    "market": "TWSE",
                    "price": p_0050,
                    "change": 1.5,
                    "source_timestamp": "2026-07-16T02:59:50Z",
                    "retrieved_at": clock_str
                },
                "TWSE_OPENAPI": {
                    "symbol": "0050",
                    "market": "listed",
                    "trade_date": "2026-07-15",
                    "retrieved_at_utc": clock_str,
                    "price": {"open": "178", "high": "181", "low": "177", "close": "178.5"},
                    "activity": {"trade_volume": 8000}
                }
            },
            "TPEX:5347": {
                "TWSE_MIS": {
                    "symbol": "5347",
                    "market": "TPEX",
                    "price": p_5347,
                    "change": 0.5,
                    "source_timestamp": "2026-07-16T02:59:50Z",
                    "retrieved_at": clock_str
                },
                "TPEX_OPENAPI": {
                    "symbol": "5347",
                    "market": "tpex_otc",
                    "trade_date": "2026-07-15",
                    "retrieved_at_utc": clock_str,
                    "price": {"open": "119", "high": "121", "low": "118", "close": "119.5"},
                    "activity": {"trade_volume": 3000}
                }
            },
            "TWSE:0056": {
                "TWSE_MIS": {
                    "symbol": "0056",
                    "market": "TWSE",
                    "price": p_0056,
                    "change": -0.2,
                    "source_timestamp": "2026-07-16T02:59:50Z",
                    "retrieved_at": clock_str
                },
                "TWSE_OPENAPI": {
                    "symbol": "0056",
                    "market": "listed",
                    "trade_date": "2026-07-15",
                    "retrieved_at_utc": clock_str,
                    "price": {"open": "40.1", "high": "40.3", "low": "39.8", "close": "40.2"},
                    "activity": {"trade_volume": 12000}
                }
            },
            "TWSE:2308": {
                # Stale but usable
                "TWSE_MIS": {
                    "symbol": "2308",
                    "market": "TWSE",
                    "price": p_2308,
                    "change": 5.0,
                    "source_timestamp": "2026-07-15T02:59:50Z", # 大於 24 小時前
                    "retrieved_at": clock_str
                },
                "TWSE_OPENAPI": {
                    "symbol": "2308",
                    "market": "listed",
                    "trade_date": "2026-07-14",
                    "retrieved_at_utc": clock_str,
                    "price": {"open": "345", "high": "352", "low": "344", "close": "346"},
                    "activity": {"trade_volume": 5000}
                }
            },
            "TWSE:2382": {
                # Missing optional (不提供 OpenAPI EOD)
                "TWSE_MIS": {
                    "symbol": "2382",
                    "market": "TWSE",
                    "price": p_2382,
                    "change": -3.0,
                    "source_timestamp": "2026-07-16T02:59:50Z",
                    "retrieved_at": clock_str
                }
            },
            "TWSE:3008": {
                # One source failure but valid fallback
                "TWSE_OPENAPI": {
                    "symbol": "3008",
                    "market": "listed",
                    "trade_date": "2026-07-15",
                    "retrieved_at_utc": clock_str,
                    "price": {"open": "2400", "high": "2450", "low": "2390", "close": "2410"},
                    "activity": {"trade_volume": 400}
                }
            },
            "TWSE:9999": {} # Unresolved target, 無觀測值
        }
    }
    
    return {
        "request": request,
        "source_data": source_data
    }

def generate_fixtures_to_disk(output_root: str | Path, seed_val: str = "seed-r5a", clock_val: str = "2026-07-16T03:00:00Z"):
    root_path = validate_authorized_root(output_root)
    
    seed = R5AFixtureSeed(seed_val)
    clock = R5AFixtureClock(clock_val)
    
    # Build security master snapshot & manifest
    snap, man = build_r5a_security_master(clock.now_utc, seed)
    
    # Save security master snapshot & manifest
    sec_snap_dest = safe_destination(root_path, "security_identity_snapshot.json", create_parent=True)
    atomic_write_text(root_path, "security_identity_snapshot.json", json.dumps(snap, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    sec_man_dest = safe_destination(root_path, "security_identity_snapshot_manifest.json", create_parent=True)
    atomic_write_text(root_path, "security_identity_snapshot_manifest.json", json.dumps(man, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Save source capability snapshot
    cap_registry = json.loads(Path("docs/data_capabilities/m8_source_capability_registry.json").read_text(encoding="utf-8"))
    atomic_write_text(root_path, "source_capability_snapshot.json", json.dumps(cap_registry, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Build core request & observations
    core = build_r5a_cross_layer_fixture(seed=seed, clock=clock)
    req = core["request"]
    source_data = core["source_data"]
    
    # Save request & raw observations
    atomic_write_text(root_path, "bounded_request.json", json.dumps(req, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    atomic_write_text(root_path, "source_observations.json", json.dumps(source_data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Use production execution path to compile plans
    from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot
    val_sm = load_verified_security_master_snapshot(str(sec_snap_dest.path), str(sec_man_dest.path), allow_fixture_snapshot=True)
    
    # Execute watchlist in fixture mode
    # This will generate: validated_request, execution_plan, execution_result, bundle, and normalized_observations
    temp_dir_dest = safe_destination(root_path, "temp_run", create_parent=True)
    temp_dir = temp_dir_dest.path
    
    res = execute_watchlist(
        request=req,
        mode="fixture",
        bundle_type="snapshot",
        fixture_source_data=source_data,
        artifact_root=str(root_path),
        run_id="temp_run",
        generated_at_utc=clock.now_utc,
        security_master=val_sm,
        source_capability_registry=cap_registry
    )
    
    if res.get("status") not in {"success", "success_with_partial_coverage"}:
        raise ValueError(f"Watchlist execution failed: {res}")
        
    # Read generated assets from temp run
    plan = json.loads((temp_dir / "execution_plan.json").read_text(encoding="utf-8"))
    run_result = json.loads((temp_dir / "execution_result.json").read_text(encoding="utf-8"))
    bundle = json.loads((temp_dir / "watchlist_snapshot_bundle.json").read_text(encoding="utf-8"))
    
    # Clean up temp run directory
    for child in temp_dir.iterdir():
        child.unlink()
    temp_dir.rmdir()
    
    # Save core execution plan & result
    atomic_write_text(root_path, "execution_plan.json", json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    atomic_write_text(root_path, "evidence_bundle.json", json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Now generate downstream artifacts: package, handoff, manifest
    pkg = build_watchlist_ai_context_package(
        validated_request=req,
        execution_plan=plan,
        execution_result=run_result,
        watchlist_bundle=bundle,
        generated_at_utc=clock.now_utc
    )
    
    handoff = build_watchlist_conversation_handoff(
        context_package=pkg,
        generated_at_utc=clock.now_utc
    )
    
    manifest_upstream = {
        "validated_request": req,
        "execution_plan": plan,
        "execution_result": run_result,
        "watchlist_bundle": bundle
    }
    
    man = build_context_manifest(
        context_package=pkg,
        conversation_handoff=handoff,
        upstream_artifacts=manifest_upstream,
        generated_at_utc=clock.now_utc
    )
    
    preview = render_watchlist_ai_context_preview(pkg)
    
    # Verify package, handoff and manifest
    vp = validate_watchlist_ai_context_package(pkg, upstream_artifacts=manifest_upstream)
    vh = validate_watchlist_conversation_handoff(handoff, context_package=pkg)
    vm = validate_watchlist_ai_context_manifest(man, context_package=pkg, handoff=handoff, upstream_artifacts=manifest_upstream)
    
    if not (vp["valid"] and vh["valid"] and vm["valid"]):
        raise ValueError(f"Downstream validation failed: pkg: {vp}, hand: {vh}, man: {vm}")
        
    # Save downstream & expected validation result
    atomic_write_text(root_path, "context_projection.json", json.dumps(pkg, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    atomic_write_text(root_path, "expected_validation_result.json", json.dumps({"valid": True, "package_id": pkg["context_package_id"]}, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Provenance Manifest
    prov = pkg["source_lineage"]
    atomic_write_text(root_path, "provenance_manifest.json", json.dumps(prov, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Citation Map
    cite_map = pkg["citation_index"]
    atomic_write_text(root_path, "citation_map.json", json.dumps(cite_map, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Missing Evidence Register
    miss_reg = pkg["missing_evidence"]
    atomic_write_text(root_path, "missing_evidence_register.json", json.dumps(miss_reg, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Currentness Assessment
    curr_assessment = {
        "generated_at_utc": clock.now_utc,
        "targets": []
    }
    for t in pkg["targets"]:
        co = t.get("current_observation") or {}
        curr_assessment["targets"].append({
            "target_id": t["target_id"],
            "currentness_status": co.get("currentness_status") or "unresolved",
            "source_timestamp": co.get("source_timestamp"),
            "retrieved_at_utc": co.get("retrieved_at_utc")
        })
    atomic_write_text(root_path, "currentness_assessment.json", json.dumps(curr_assessment, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Expected Partial Failure Result
    # Create a simple validation structure for testing Variant A / B / C
    atomic_write_text(root_path, "expected_partial_failure_result.json", json.dumps({
        "expected_variant_a_status": "partial",
        "expected_variant_b_status": "partial",
        "expected_variant_c_status": "blocked"
    }, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    
    # Top-level Fixture Manifest
    def get_sha(rel):
        text = (root_path / rel).read_text(encoding="utf-8")
        return sha256_json(json.loads(text))
        
    tids = req["persistent_watchlist_reference"]["enabled_target_ids"]
    fixture_manifest = {
        "schema_version": "m8r_03e_r5a_cross_layer_fixture_manifest.v1",
        "fixture_id": f"fixture-r5a-{seed.value}",
        "fixture_version": "1",
        "seed": seed.value,
        "reference_clock_utc": clock.now_utc,
        "target_count": 10,
        "target_ids": tids,
        "source_families": ["TWSE_MIS", "TWSE_OPENAPI", "TPEX_OPENAPI"],
        "artifacts": [
            {"artifact_type": "fixture_manifest", "relative_path": "fixture_manifest.json", "schema_version": "m8r_03e_r5a_cross_layer_fixture_manifest.v1", "sha256": "", "producer": "generator", "consumers": ["tests"], "target_ids": []},
            {"artifact_type": "security_identity_snapshot", "relative_path": "security_identity_snapshot.json", "schema_version": SNAPSHOT_SCHEMA_VERSION, "sha256": get_sha("security_identity_snapshot.json"), "producer": "generator", "consumers": ["executor"], "target_ids": tids},
            {"artifact_type": "security_identity_snapshot_manifest", "relative_path": "security_identity_snapshot_manifest.json", "schema_version": MANIFEST_SCHEMA_VERSION, "sha256": get_sha("security_identity_snapshot_manifest.json"), "producer": "generator", "consumers": ["executor"], "target_ids": tids},
            {"artifact_type": "source_capability_snapshot", "relative_path": "source_capability_snapshot.json", "schema_version": "m8_source_capability_registry.v1", "sha256": get_sha("source_capability_snapshot.json"), "producer": "generator", "consumers": ["executor"], "target_ids": []},
            {"artifact_type": "bounded_request", "relative_path": "bounded_request.json", "schema_version": "m8r_ai_evidence_request.v1", "sha256": get_sha("bounded_request.json"), "producer": "generator", "consumers": ["executor"], "target_ids": tids},
            {"artifact_type": "execution_plan", "relative_path": "execution_plan.json", "schema_version": "m8r_03d_watchlist_execution_plan.v1", "sha256": get_sha("execution_plan.json"), "producer": "generator", "consumers": ["executor", "builder"], "target_ids": tids},
            {"artifact_type": "source_observations", "relative_path": "source_observations.json", "schema_version": "m8r_watchlist_source_data.v1", "sha256": get_sha("source_observations.json"), "producer": "generator", "consumers": ["executor"], "target_ids": tids},
            {"artifact_type": "currentness_assessment", "relative_path": "currentness_assessment.json", "schema_version": "m8r_watchlist_currentness_assessment.v1", "sha256": get_sha("currentness_assessment.json"), "producer": "generator", "consumers": ["tests"], "target_ids": tids},
            {"artifact_type": "evidence_bundle", "relative_path": "evidence_bundle.json", "schema_version": "m8r_watchlist_snapshot_bundle.v1", "sha256": get_sha("evidence_bundle.json"), "producer": "generator", "consumers": ["builder"], "target_ids": tids},
            {"artifact_type": "provenance_manifest", "relative_path": "provenance_manifest.json", "schema_version": "m8r_watchlist_provenance.v1", "sha256": get_sha("provenance_manifest.json"), "producer": "generator", "consumers": ["validator"], "target_ids": tids},
            {"artifact_type": "citation_map", "relative_path": "citation_map.json", "schema_version": "m8r_watchlist_citation_index.v1", "sha256": get_sha("citation_map.json"), "producer": "generator", "consumers": ["validator"], "target_ids": tids},
            {"artifact_type": "missing_evidence_register", "relative_path": "missing_evidence_register.json", "schema_version": "m8r_watchlist_missing_evidence.v1", "sha256": get_sha("missing_evidence_register.json"), "producer": "generator", "consumers": ["validator"], "target_ids": tids},
            {"artifact_type": "context_projection", "relative_path": "context_projection.json", "schema_version": "m8r_watchlist_ai_context_package.v2", "sha256": get_sha("context_projection.json"), "producer": "generator", "consumers": ["validator"], "target_ids": tids},
        ],
        "expected_states": {
            "TWSE:2330": "ready",
            "TWSE:2317": "partial",
            "TPEX:6488": "ready_with_caveats",
            "TWSE:0050": "ready",
            "TPEX:5347": "ready",
            "TWSE:0056": "ready",
            "TWSE:2308": "ready_with_caveats",
            "TWSE:2382": "partial",
            "TWSE:3008": "ready_with_caveats",
            "TWSE:9999": "blocked"
        },
        "hash_algorithm": "sha256",
        "canonicalization_contract": "canonical_json_utf8",
        "network_required": False
    }
    
    # Calculate manifest self-hash
    # We exclude manifest_hash field itself during serialization
    fixture_manifest["artifacts"][0]["sha256"] = ""
    fixture_manifest.pop("manifest_hash", None)
    final_manifest_hash = sha256_json(fixture_manifest)
    fixture_manifest["manifest_hash"] = final_manifest_hash
    
    atomic_write_text(root_path, "fixture_manifest.json", json.dumps(fixture_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return fixture_manifest

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--seed", default="seed-r5a")
    ap.add_argument("--clock", default="2026-07-16T03:00:00Z")
    args = ap.parse_args(argv)
    
    try:
        manifest = generate_fixtures_to_disk(args.output_root, seed_val=args.seed, clock_val=args.clock)
        print(json.dumps({"status": "success", "manifest_hash": manifest.get("manifest_hash"), "target_count": manifest.get("target_count")}))
        return 0
    except Exception as e:
        import traceback
        print(f"Error generating fixtures: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
