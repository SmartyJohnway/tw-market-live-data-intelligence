import json
import os
import sys
from pathlib import Path

# Add the scripts directory to path to import the benchmark module
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from m8r_06_01c1r_runtime_identity_cache_benchmark import (
    project_to_compact_records,
    build_compact_lookup,
    build_full_lookup,
)

def test_lookup_equivalence_synthetic():
    """Test that the compact lookup produces equivalent results to full snapshot lookup for key fields using synthetic data."""
    # Synthetic data with multiple records to test various lookup scenarios
    records = [
        {
            "record_id": "security-1",
            "canonical_target_id": "TWSE:2330",
            "identity": {
                "security_code": "2330",
                "security_name_zh": "台積電",
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
                "as_of": "2026-08-07"
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
                "security_name_zh": "聯發科",
                "security_name_en": "MediaTek",
                "isin": "TW0002454006"
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
                "as_of": "2026-08-07"
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
                "security_name_zh": "富邦金",
                "security_name_en": "Fubon Financial",
                "isin": "TW0000050002"
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
                "as_of": "2026-08-07"
            },
            "execution_eligibility": {
                "status": "eligible",
                "reason_codes": []
            },
            "record_hash": "hash3"
        }
    ]
    
    # Build full snapshot structure for synthetic data (as expected by build_full_lookup)
    full_snapshot = {
        "schema_version": "tw_runtime_identity_index.v1",
        "generated_at_utc": "2026-08-07T00:00:00Z",
        "source_bundle_id": "synthetic",
        "record_count": len(records),
        "records": records
    }
    
    # Build full lookup from the synthetic full snapshot
    full_lookup = build_full_lookup(full_snapshot)
    
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
    assert full_lookup['by_canonical'].get("TWSE:2330") is not None
    assert compact_lookup['by_canonical'].get("TWSE:2330") is not None
    assert full_lookup['by_canonical'].get("TWSE:2330")['canonical_target_id'] == "TWSE:2330"
    assert compact_lookup['by_canonical'].get("TWSE:2330")['canonical_target_id'] == "TWSE:2330"
    
    assert full_lookup['by_canonical'].get("TWSE:2454") is not None
    assert compact_lookup['by_canonical'].get("TWSE:2454") is not None
    assert full_lookup['by_canonical'].get("TWSE:2454")['canonical_target_id'] == "TWSE:2454"
    assert compact_lookup['by_canonical'].get("TWSE:2454")['canonical_target_id'] == "TWSE:2454"
    
    assert full_lookup['by_canonical'].get("TWSE:0050") is not None
    assert compact_lookup['by_canonical'].get("TWSE:0050") is not None
    assert full_lookup['by_canonical'].get("TWSE:0050")['canonical_target_id'] == "TWSE:0050"
    assert compact_lookup['by_canonical'].get("TWSE:0050")['canonical_target_id'] == "TWSE:0050"
    
    # Test ISIN lookup
    isin_results_full = full_lookup['by_isin'].get("TW0002330008", [])
    isin_results_compact = compact_lookup['by_isin'].get("TW0002330008", [])
    assert len(isin_results_full) == len(isin_results_compact) == 1
    assert isin_results_full[0]['identity']['isin'] == "TW0002330008"
    assert isin_results_compact[0]['identity']['isin'] == "TW0002330008"
    
    isin_results_full = full_lookup['by_isin'].get("TW0002454006", [])
    isin_results_compact = compact_lookup['by_isin'].get("TW0002454006", [])
    assert len(isin_results_full) == len(isin_results_compact) == 1
    assert isin_results_full[0]['identity']['isin'] == "TW0002454006"
    assert isin_results_compact[0]['identity']['isin'] == "TW0002454006"
    
    isin_results_full = full_lookup['by_isin'].get("TW0000050002", [])
    isin_results_compact = compact_lookup['by_isin'].get("TW0000050002", [])
    assert len(isin_results_full) == len(isin_results_compact) == 1
    assert isin_results_full[0]['identity']['isin'] == "TW0000050002"
    assert isin_results_compact[0]['identity']['isin'] == "TW0000050002"
    
    # Test code lookup (with market)
    code_results_full = full_lookup['by_code'].get(("TWSE", "2330"), [])
    code_results_compact = compact_lookup['by_code'].get(("TWSE", "2330"), [])
    assert len(code_results_full) == len(code_results_compact) == 1
    assert code_results_full[0]['identity']['security_code'] == "2330"
    assert code_results_compact[0]['identity']['security_code'] == "2330"
    assert code_results_full[0]['classification']['market'] == "TWSE"
    assert code_results_compact[0]['classification']['market'] == "TWSE"
    
    code_results_full = full_lookup['by_code'].get(("TWSE", "2454"), [])
    code_results_compact = compact_lookup['by_code'].get(("TWSE", "2454"), [])
    assert len(code_results_full) == len(code_results_compact) == 1
    assert code_results_full[0]['identity']['security_code'] == "2454"
    assert code_results_compact[0]['identity']['security_code'] == "2454"
    assert code_results_full[0]['classification']['market'] == "TWSE"
    assert code_results_compact[0]['classification']['market'] == "TWSE"
    
    code_results_full = full_lookup['by_code'].get(("TWSE", "0050"), [])
    code_results_compact = compact_lookup['by_code'].get(("TWSE", "0050"), [])
    assert len(code_results_full) == len(code_results_compact) == 1
    assert code_results_full[0]['identity']['security_code'] == "0050"
    assert code_results_compact[0]['identity']['security_code'] == "0050"
    assert code_results_full[0]['classification']['market'] == "TWSE"
    assert code_results_compact[0]['classification']['market'] == "TWSE"
    
    # Test code lookup (without market - should still work)
    code_results_full = full_lookup['by_code'].get((None, "2330"), [])
    code_results_compact = compact_lookup['by_code'].get((None, "2330"), [])
    assert len(code_results_full) >= 1  # May have multiple matches if same code in different markets
    assert len(code_results_compact) >= 1
    # Find the TWSE one in both
    twse_result_full = None
    for result in code_results_full:
        if result.get('classification', {}).get('market') == 'TWSE':
            twse_result_full = result
            break
    assert twse_result_full is not None
    assert twse_result_full['identity']['security_code'] == "2330"
    
    twse_result_compact = None
    for result in code_results_compact:
        if result.get('classification', {}).get('market') == 'TWSE':
            twse_result_compact = result
            break
    assert twse_result_compact is not None
    assert twse_result_compact['identity']['security_code'] == "2330"
    
    # Test name lookup (Chinese)
    zh_name_results_full = full_lookup['by_name'].get('台積電'.replace(' ', '').casefold(), [])
    zh_name_results_compact = compact_lookup['by_name'].get('台積電'.replace(' ', '').casefold(), [])
    assert len(zh_name_results_full) >= 1
    assert len(zh_name_results_compact) >= 1
    # Find the exact match
    zh_match_full = None
    for result in zh_name_results_full:
        if result['identity']['security_name_zh'] == '台積電':
            zh_match_full = result
            break
    assert zh_match_full is not None
    
    zh_match_compact = None
    for result in zh_name_results_compact:
        if result['identity']['security_name_zh'] == '台積電':
            zh_match_compact = result
            break
    assert zh_match_compact is not None
    
    # Test name lookup (English)
    en_name_results_full = full_lookup['by_name'].get('tsmc'.replace(' ', '').casefold(), [])
    en_name_results_compact = compact_lookup['by_name'].get('tsmc'.replace(' ', '').casefold(), [])
    assert len(en_name_results_full) >= 1
    assert len(en_name_results_compact) >= 1
    # Find the exact match
    en_match_full = None
    for result in en_name_results_full:
        if result['identity']['security_name_en'] and result['identity']['security_name_en'].lower() == 'tsmc':
            en_match_full = result
            break
    assert en_match_full is not None
    
    en_match_compact = None
    for result in en_name_results_compact:
        if result['identity']['security_name_en'] and result['identity']['security_name_en'].lower() == 'tsmc':
            en_match_compact = result
            break
    assert en_match_compact is not None
    
    # Test that non-existent keys return None/empty
    assert full_lookup['by_canonical'].get("TWSE:9999") is None
    assert compact_lookup['by_canonical'].get("TWSE:9999") is None
    assert len(full_lookup['by_isin'].get("TW0009999999", [])) == 0
    assert len(compact_lookup['by_isin'].get("TW0009999999", [])) == 0
    assert len(full_lookup['by_code'].get(("TWSE", "9999"), [])) == 0
    assert len(compact_lookup['by_code'].get(("TWSE", "9999"), [])) == 0
    assert len(full_lookup['by_name'].get('nonexistent'.replace(' ', '').casefold(), [])) == 0
    assert len(compact_lookup['by_name'].get('nonexistent'.replace(' ', '').casefold(), [])) == 0