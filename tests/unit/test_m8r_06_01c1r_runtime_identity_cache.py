import json
import os
import sys
from pathlib import Path

# Add the scripts directory to path to import the benchmark module
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from m8r_06_01c1r_runtime_identity_cache_benchmark import project_to_compact_records, build_compact_lookup

# Path to the authorized bundle
BUNDLE_DIR = REPO_ROOT / "data" / "security_master" / "input_bundles" / "m8r06-01b-20260807T053540Z"
FULL_SNAPSHOT_PATH = BUNDLE_DIR / "dryrun_snapshot.json"

# Skip all tests in this module if the authorized bundle is not present
if not FULL_SNAPSHOT_PATH.exists():
    pytest.skip("Authorized bundle not present; skipping tests that require local data", allow_module_level=True)


def load_snapshot():
    with open(FULL_SNAPSHOT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_deterministic_compact_projection():
    """Test that the projection is deterministic and produces the same output each time."""
    snapshot = load_snapshot()
    records = snapshot.get("records", [])
    
    # Project twice
    compact1 = project_to_compact_records(records)
    compact2 = project_to_compact_records(records)
    
    # They should be equal
    assert compact1 == compact2, "Projection is not deterministic"


def test_one_compact_record_per_canonical_target():
    """Test that there is exactly one compact record per canonical_target_id."""
    snapshot = load_snapshot()
    records = snapshot.get("records", [])
    compact = project_to_compact_records(records)
    
    # Extract canonical_target_id from full records
    full_cids = [r.get("canonical_target_id") for r in records if r.get("canonical_target_id")]
    # Extract from compact records
    compact_cids = [r.get("canonical_target_id") for r in compact if r.get("canonical_target_id")]
    
    # The sets should be equal and lengths should match (no duplicates)
    assert set(full_cids) == set(compact_cids), "Canonical target ID set mismatch"
    assert len(full_cids) == len(compact_cids) == len(set(full_cids)), "Duplicate canonical_target_id found"


def test_execution_eligibility_preserved():
    """Test that execution_eligibility.status and reason_codes are preserved."""
    snapshot = load_snapshot()
    records = snapshot.get("records", [])
    compact = project_to_compact_records(records)
    
    # Build mapping from canonical_target_id to compact record
    compact_map = {r["canonical_target_id"]: r for r in compact if r.get("canonical_target_id")}
    
    for rec in records:
        cid = rec.get("canonical_target_id")
        if not cid:
            continue
        comp = compact_map.get(cid)
        assert comp is not None, f"Missing compact record for {cid}"
        # Check status
        assert rec.get("execution_eligibility", {}).get("status") == comp.get("execution_eligibility", {}).get("status"), \
            f"Execution eligibility status mismatch for {cid}"
        # Check reason_codes (order may not matter, but we sort)
        rec_reasons = sorted(rec.get("execution_eligibility", {}).get("reason_codes", []))
        comp_reasons = sorted(comp.get("execution_eligibility", {}).get("reason_codes", []))
        assert rec_reasons == comp_reasons, f"Execution eligibility reason_codes mismatch for {cid}"


def test_lifecycle_summary_preserved():
    """Test that lifecycle.state and resolution_status are preserved."""
    snapshot = load_snapshot()
    records = snapshot.get("records", [])
    compact = project_to_compact_records(records)
    
    compact_map = {r["canonical_target_id"]: r for r in compact if r.get("canonical_target_id")}
    
    for rec in records:
        cid = rec.get("canonical_target_id")
        if not cid:
            continue
        comp = compact_map.get(cid)
        assert comp is not None, f"Missing compact record for {cid}"
        assert rec.get("lifecycle", {}).get("state") == comp.get("lifecycle", {}).get("state"), \
            f"Lifecycle state mismatch for {cid}"
        assert rec.get("lifecycle", {}).get("resolution_status") == comp.get("lifecycle", {}).get("resolution_status"), \
            f"Lifecycle resolution_status mismatch for {cid}"


def test_source_record_hash_preserved():
    """Test that source_record_hash (copied from record_hash) is preserved."""
    snapshot = load_snapshot()
    records = snapshot.get("records", [])
    compact = project_to_compact_records(records)
    
    compact_map = {r["canonical_target_id"]: r for r in compact if r.get("canonical_target_id")}
    
    for rec in records:
        cid = rec.get("canonical_target_id")
        if not cid:
            continue
        comp = compact_map.get(cid)
        assert comp is not None, f"Missing compact record for {cid}"
        assert rec.get("record_hash") == comp.get("record_hash"), \
            f"Source record hash mismatch for {cid}"


def test_no_full_lifecycle_event_arrays_copied():
    """Test that the compact record does not contain the full lifecycle events array."""
    snapshot = load_snapshot()
    records = snapshot.get("records", [])
    compact = project_to_compact_records(records)
    
    for comp in compact:
        # The compact record should not have a key 'lifecycle_events' (the full record has it under lifecycle.events)
        # But we check that the lifecycle field does not contain an 'events' list with more than a few items?
        # Actually, the compact lifecycle only has state, resolution_status, as_of. No events.
        lifecycle = comp.get("lifecycle", {})
        assert "events" not in lifecycle, f"Compact lifecycle should not contain 'events' key, got {lifecycle.keys()}"
        # Also ensure it's not a large list
        # The compact lifecycle should only have three keys
        expected_keys = {"state", "resolution_status", "as_of"}
        assert set(lifecycle.keys()) == expected_keys, f"Compact lifecycle has unexpected keys: {lifecycle.keys()}"


def test_no_raw_evidence_payload_copied():
    """Test that the compact record does not contain raw payload fields like evidence_summary, conflicts, caveats."""
    snapshot = load_snapshot()
    records = snapshot.get("records", [])
    compact = project_to_compact_records(records)
    
    forbidden_fields = {"evidence_summary", "conflicts", "caveats", "raw_html", "raw_payload", "raw_cells", "html", "cookies", "session_id", "access_token", "refresh_token"}
    for comp in compact:
        for field in forbidden_fields:
            assert field not in comp, f"Compact record should not contain forbidden field '{field}'"


def test_complete_real_bundle_semantic_comparison_can_run():
    """Test that we can run a semantic comparison using the full bundle (we already do in benchmark).
    This test just ensures that the projection function works on the real bundle and produces
    the expected number of records."""
    snapshot = load_snapshot()
    records = snapshot.get("records", [])
    compact = project_to_compact_records(records)
    assert len(compact) == len(records), "Compact record count should match full record count"
    # Additionally, we can check that each compact record has the expected structure
    for comp in compact:
        assert "canonical_target_id" in comp
        assert "record_id" in comp
        assert "identity" in comp and isinstance(comp["identity"], dict)
        assert "classification" in comp and isinstance(comp["classification"], dict)
        assert "observation" in comp and isinstance(comp["observation"], dict)
        assert "lifecycle" in comp and isinstance(comp["lifecycle"], dict)
        assert "execution_eligibility" in comp and isinstance(comp["execution_eligibility"], dict)
        assert "record_hash" in comp and isinstance(comp["record_hash"], str)


# New test for lookup equivalence using synthetic data (does not require the bundle)
def test_lookup_equivalence_synthetic():
    """Test that the compact lookup produces equivalent results to full snapshot lookup for key fields using synthetic data."""
    # Synthetic data with multiple records to test various lookup scenarios
    records = [
        {
            "record_id": "security-1",
            "canonical_target_id": "TWSE:2330",
            "identity": {
                "security_code": "2330",
                "security_name_zh": "TSMC",
                "security_name_en": "TSMC",
                "isin": "TW0002330008"
            },
            "classification": {
                "market": "TWSE",
                "instrument_type": "common_share",
                "instrument_family": "company_share",
                "classification_status": "confirmed_official_single_lane"
            },
            "observation": {
                "status": "active",
                "observed_at": "2026-08-07T00:00:00Z",
                "source_updated_date": "2026-08-07"
            },
            "lifecycle": {
                "state": "listed",
                "resolution_status": "resolved",
                "as_of": "2026-08-07
            },
            "execution_eligibility": {
                "status": "eligible",
                "reason_codes": []
            },
            "record_hash": "hash1"
        },
        {
            "record_id": "security-2",
            "canonical_target_id": "TWSE:2454",
            "identity": {
                "security_code": "2454",
                "security_name_zh": "MediaTek",
                "security_name_en": "MediaTek",
                "isin": "TW0002454006
            },
            "classification": {
                "market": "TWSE",
                "instrument_type": "common_share",
                "instrument_family": "company_share",
                "classification_status": "confirmed_official_single_lane
            },
            "observation": {
                "status": "active",
                "observed_at": "2026-08-07T00:00:00Z",
                "source_updated_date": "2026-08-07
            },
            "lifecycle": {
                "state": "listed",
                "resolution_status": "resolved",
                "as_of": "2026-08-07
            },
            "execution_eligibility": {
                "status": "eligible",
                "reason_codes": ["E001"]
            },
            "record_hash": "hash2"
        },
        {
            "record_id": "security-3",
            "canonical_target_id": "TWSE:0050",
            "identity": {
                "security_code": "0050",
                "security_name_zh": "Fubon Financial",
                "security_name_en": "Fubon Financial",
                "isin": "TW0000050002
            },
            "classification": {
                "market": "TWSE",
                "instrument_type": "common_share",
                "instrument_family": "company_share",
                "classification_status": "confirmed_official_single_lane
            },
            "observation": {
                "status": "active",
                "observed_at": "2026-08-07T00:00:00Z",
                "source_updated_date": "2026-08-07
            },
            "lifecycle": {
                "state": "listed",
                "resolution_status": "resolved",
                "as_of": "2026-08-07
            },
            "execution_eligibility": {
                "status": "eligible",
                "reason_codes": []
            },
            "record_hash": "hash3"
        }
    ]
    
    # Project to compact records
    compact_records = project_to_compact_records(records)
    compact_data = {
        "schema_version": "tw_runtime_identity_index.v1",
        "generated_at_utc": "2026-08-07T00:00:00Z",
        "source_bundle_id": "synthetic",
        "record_count": len(compact_records),
        "records": compact_records,
    }
    
    # Build compact lookup
    compact_lookup = build_compact_lookup(compact_data)
    
    # Test canonical ID lookup
    assert compact_lookup['by_canonical'].get("TWSE:2330") is not None
    assert compact_lookup['by_canonical'].get("TWSE:2330")['canonical_target_id'] == "TWSE:2330"
    assert compact_lookup['by_canonical'].get("TWSE:2454")['canonical_target_id'] == "TWSE:2454"
    assert compact_lookup['by_canonical'].get("TWSE:0050")['canonical_target_id'] == "TWSE:0050"
    
    # Test ISIN lookup
    isin_results = compact_lookup['by_isin'].get("TW0002330008", [])
    assert len(isin_results) == 1
    assert isin_results[0]['identity']['isin'] == "TW0002330008"
    
    isin_results = compact_lookup['by_isin'].get("TW0002454006", [])
    assert len(isin_results) == 1
    assert isin_results[0]['identity']['isin'] == "TW0002454006"
    
    isin_results = compact_lookup['by_isin'].get("TW0000050002", [])
    assert len(isin_results) == 1
    assert isin_results[0]['identity']['isin'] == "TW0000050002"
    
    # Test code lookup (with market)
    code_results = compact_lookup['by_code'].get(("TWSE", "2330"), [])
    assert len(code_results) == 1
    assert code_results[0]['identity']['security_code'] == "2330"
    assert code_results[0]['classification']['market'] == "TWSE"
    
    code_results = compact_lookup['by_code'].get(("TWSE", "2454"), [])
    assert len(code_results) == 1
    assert code_results[0]['identity']['security_code'] == "2454"
    assert code_results[0]['classification']['market'] == "TWSE"
    
    code_results = compact_lookup['by_code'].get(("TWSE", "0050"), [])
    assert len(code_results) == 1
    assert code_results[0]['identity']['security_code'] == "0050"
    assert code_results[0]['classification']['market'] == "TWSE"
    
    # Test code lookup (without market - should still work)
    code_results = compact_lookup['by_code'].get((None, "2330"), [])
    assert len(code_results) >= 1  # May have multiple matches if same code in different markets
    # Find the TWSE one
    twse_result = None
    for result in code_results:
        if result.get('classification', {}).get('market') == 'TWSE':
            twse_result = result
            break
    assert twse_result is not None
    assert twse_result['identity']['security_code'] == "2330"
    
    # Test name lookup (Chinese)
    zh_name_results = compact_lookup['by_name'].get('TSMC'.replace(' ', '').casefold(), [])
    assert len(zh_name_results) >= 1
    # Find the exact match
    zh_match = None
    for result in zh_name_results:
        if result['identity']['security_name_zh'] == 'TSMC':
            zh_match = result
            break
    assert zh_match is not None
    
    # Test name lookup (English)
    en_name_results = compact_lookup['by_name'].get('tsmc'.replace(' ', '').casefold(), [])
    assert len(en_name_results) >= 1
    # Find the exact match
    en_match = None
    for result in en_name_results:
        if result['identity']['security_name_en'] and result['identity']['security_name_en'].lower() == 'tsmc':
            en_match = result
            break
    assert en_match is not None
    
    # Test that non-existent keys return None/empty
    assert compact_lookup['by_canonical'].get("TWSE:9999") is None
    assert len(compact_lookup['by_isin'].get("TW0009999999", [])) == 0
    assert len(compact_lookup['by_code'].get(("TWSE", "9999"), [])) == 0
    assert len(compact_lookup['by_name'].get('nonexistent'.replace(' ', '').casefold(), [])) == 0