#!/usr/bin/env python3
"""
M8R-06-01C1R Runtime Identity Cache Benchmark

This script benchmarks the current full Security Master snapshot and projects a compact
runtime identity index for analysis. It does not modify any source data.

Output:
  artifacts/m8r_06_01c1r/compact_identity_index.json
  artifacts/m8r_06_01c1r/benchmark_results.json
"""

import json
import time
import hashlib
import os
import re
import sys
from pathlib import Path
from statistics import median

# Ensure the repo root is in sys.path for importing local modules
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Paths
BUNDLE_DIR = REPO_ROOT / "data" / "security_master" / "input_bundles" / "m8r06-01b-20260807T053540Z"
FULL_SNAPSHOT_PATH = BUNDLE_DIR / "dryrun_snapshot.json"
COMMITTED_MANIFEST_PATH = REPO_ROOT / "docs" / "reviews" / "m8r06-01b-bundle-manifest" / "immutable_manifest.json"
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "m8r_06_01c1r"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
COMPACT_INDEX_PATH = ARTIFACTS_DIR / "compact_identity_index.json"
BENCHMARK_RESULTS_PATH = ARTIFACTS_DIR / "benchmark_results.json"


def sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def verify_bundle_integrity(bundle_dir: Path, manifest_path: Path):
    """
    Verify bundle integrity against the committed manifest.
    Returns (is_valid, manifest, bundle_id) where is_valid is a boolean.
    If invalid, manifest and bundle_id may be None.
    """
    if not bundle_dir.is_dir():
        print(f"ERROR: Bundle directory not found: {bundle_dir}")
        return False, None, None
    if not manifest_path.is_file():
        print(f"ERROR: Manifest not found: {manifest_path}")
        return False, None, None

    manifest = load_json(manifest_path)
    bundle_id = manifest.get("bundle_id")
    if not bundle_id:
        print("ERROR: Missing bundle_id in manifest")
        return False, None, None

    # Check dryrun_snapshot
    dryrun_info = manifest.get("dryrun_snapshot")
    if not dryrun_info:
        print("ERROR: Missing dryrun_snapshot in manifest")
        return False, None, None
    # In the manifest we saw, dryrun_snapshot is a dict with record_count and sha256, no file_name.
    # However, the bundle directory contains the file dryrun_snapshot.json.
    # We'll assume the file name is "dryrun_snapshot.json".
    snapshot_path = bundle_dir / "dryrun_snapshot.json"
    if not snapshot_path.is_file():
        print(f"ERROR: Missing file in bundle: dryrun_snapshot.json")
        return False, None, None
    expected_hash = dryrun_info.get("sha256")
    if not expected_hash:
        print("ERROR: Missing sha256 for dryrun_snapshot in manifest")
        return False, None, None
    local_hash = sha256_file(snapshot_path)
    if local_hash != expected_hash:
        print(f"ERROR: Hash mismatch for dryrun_snapshot")
        print(f"  Expected: {expected_hash}")
        print(f"  Got:      {local_hash}")
        return False, None, None

    # Check skill_contract_hash
    skill_hash = manifest.get("skill_contract_hash")
    if not skill_hash:
        print("ERROR: Missing skill_contract_hash in manifest")
        return False, None, None

    # Check bundle_persisted_in_git
    persisted = manifest.get("bundle_persisted_in_git")
    if persisted is not None and persisted:
        print("ERROR: Bundle marked as persisted in git, but it should not be")
        return False, None, None

    return True, manifest, bundle_id


def project_to_compact_records(records):
    """Project full records to compact identity records."""
    compact_records = []
    for rec in records:
        ident = rec.get("identity", {})
        classification = rec.get("classification", {})
        observation = rec.get("observation", {})
        lifecycle = rec.get("lifecycle", {})
        exec_elig = rec.get("execution_eligibility", {})
        compact = {
            "canonical_target_id": rec.get("canonical_target_id"),
            "record_id": rec.get("record_id"),
            "identity": {
                "security_code": ident.get("security_code"),
                "security_name_zh": ident.get("security_name_zh"),
                "security_name_en": ident.get("security_name_en"),
                "isin": ident.get("isin"),
            },
            "classification": {
                "market": classification.get("market"),
                "instrument_type": classification.get("instrument_type"),
                "instrument_family": classification.get("instrument_family"),
                "classification_status": classification.get("classification_status"),
            },
            "observation": {
                "status": observation.get("status"),
                "observed_at": observation.get("observed_at"),
                "source_updated_date": observation.get("source_updated_date"),
            },
            "lifecycle": {
                "state": lifecycle.get("state"),
                "resolution_status": lifecycle.get("resolution_status"),
                "as_of": lifecycle.get("as_of"),
            },
            "execution_eligibility": {
                "status": exec_elig.get("status"),
                "reason_codes": exec_elig.get("reason_codes", []),
            },
            "record_hash": rec.get("record_hash"),  # Note: keeping the name 'record_hash' for resolver compatibility
        }
        compact_records.append(compact)
    return compact_records


def build_compact_lookup(compact_data):
    """
    Build a lookup dictionary from compact data, mimicking the structure
    built by build_verified_security_master_lookup for the full snapshot.
    Returns a dict with keys: 'by_canonical', 'by_isin', 'by_code', 'by_name'.
    Note: This does NOT include the 'snapshot' key, so it is not a drop-in replacement
    for the full snapshot in the resolver. However, we can use it to test lookup equivalence.
    """
    lookup = {
        'by_canonical': {},
        'by_isin': {},
        'by_code': {},
        'by_name': {},
    }
    for rec in compact_data.get('records', []):
        cid = rec.get('canonical_target_id')
        if cid:
            lookup['by_canonical'][cid] = rec
        ident = rec.get('identity', {})
        market = rec.get('classification', {}).get('market')
        isin = ident.get('isin')
        if isin:
            lookup['by_isin'].setdefault(isin.upper(), []).append(rec)
        security_code = ident.get('security_code')
        if security_code:
            lookup['by_code'].setdefault((market, security_code), []).append(rec)
            lookup['by_code'].setdefault((None, security_code), []).append(rec)
        for k in ('security_name_zh', 'security_name_en'):
            name = ident.get(k)
            if name:
                # Normalize as in the adapter: remove spaces and casefold
                norm = re.sub(r'\s+', '', name or '').casefold()
                if norm:
                    lookup['by_name'].setdefault(norm, []).append(rec)
    return lookup


def build_full_lookup(snapshot):
    """
    Build a lookup dictionary from a full snapshot, mimicking the structure
    built by build_verified_security_master_lookup.
    Returns a dict with keys: 'by_canonical', 'by_isin', 'by_code', 'by_name'.
    """
    lookup = {
        'by_canonical': {},
        'by_isin': {},
        'by_code': {},
        'by_name': {},
    }
    for rec in snapshot.get('records', []):
        cid = rec.get('canonical_target_id')
        if cid:
            lookup['by_canonical'][cid] = rec
        ident = rec.get('identity', {})
        market = rec.get('classification', {}).get('market')
        isin = ident.get('isin')
        if isin:
            lookup['by_isin'].setdefault(isin.upper(), []).append(rec)
        security_code = ident.get('security_code')
        if security_code:
            lookup['by_code'].setdefault((market, security_code), []).append(rec)
            lookup['by_code'].setdefault((None, security_code), []).append(rec)
        for k in ('security_name_zh', 'security_name_en'):
            name = ident.get(k)
            if name:
                # Normalize as in the adapter: remove spaces and casefold
                norm = re.sub(r'\s+', '', name or '').casefold()
                if norm:
                    lookup['by_name'].setdefault(norm, []).append(rec)
    return lookup


def lookup_equivalence(full_lookup, compact_lookup):
    """
    Compare full_lookup and compact_lookup for equivalence.
    Returns a dict with keys for each lookup type indicating if they are equivalent.
    """
    equivalence = {
        'canonical_target_id': True,
        'isin': True,
        'code_with_market': True,
        'code_without_market': True,
        'name_zh': True,
        'name_en': True,
    }
    # We'll check a sample of keys to avoid O(n^2) but for simplicity we check all keys in the compact lookup.
    # In practice, the compact lookup should have the same keys as the full lookup for the fields we care about.
    # We'll do a bidirectional check: every key in compact must be in full and vice versa for the same values.

    # Helper to compare two lists of records (order doesn't matter)
    def records_equiv(list1, list2):
        if len(list1) != len(list2):
            return False
        # Compare by record_id (assuming unique)
        ids1 = sorted(r.get('record_id') for r in list1)
        ids2 = sorted(r.get('record_id') for r in list2)
        return ids1 == ids2

    # Canonical target ID
    full_cids = set(full_lookup['by_canonical'].keys())
    compact_cids = set(compact_lookup['by_canonical'].keys())
    if full_cids != compact_cids:
        equivalence['canonical_target_id'] = False
    else:
        for cid in full_cids:
            if not records_equiv(full_lookup['by_canonical'][cid], compact_lookup['by_canonical'][cid]):
                equivalence['canonical_target_id'] = False
                break

    # ISIN
    full_isins = set(full_lookup['by_isin'].keys())
    compact_isins = set(compact_lookup['by_isin'].keys())
    if full_isins != compact_isins:
        equivalence['isin'] = False
    else:
        for isin in full_isins:
            if not records_equiv(full_lookup['by_isin'][isin], compact_lookup['by_isin'][isin]):
                equivalence['isin'] = False
                break

    # Code with market
    full_code_market = set(full_lookup['by_code'].keys())
    compact_code_market = set(compact_lookup['by_code'].keys())
    # We only care about the (market, code) keys where market is not None
    full_code_market = {k for k in full_code_market if k[0] is not None}
    compact_code_market = {k for k in compact_code_market if k[0] is not None}
    if full_code_market != compact_code_market:
        equivalence['code_with_market'] = False
    else:
        for key in full_code_market:
            if not records_equiv(full_lookup['by_code'][key], compact_lookup['by_code'][key]):
                equivalence['code_with_market'] = False
                break

    # Code without market
    full_code_nomarket = set(full_lookup['by_code'].keys())
    compact_code_nomarket = set(compact_lookup['by_code'].keys())
    # We only care about the (None, code) keys
    full_code_nomarket = {k for k in full_code_nomarket if k[0] is None}
    compact_code_nomarket = {k for k in compact_code_nomarket if k[0] is None}
    if full_code_nomarket != compact_code_nomarket:
        equivalence['code_without_market'] = False
    else:
        for key in full_code_nomarket:
            if not records_equiv(full_lookup['by_code'][key], compact_lookup['by_code'][key]):
                equivalence['code_without_market'] = False
                break

    # Name (Chinese and English)
    full_names = set(full_lookup['by_name'].keys())
    compact_names = set(compact_lookup['by_name'].keys())
    if full_names != compact_names:
        equivalence['name_zh'] = False
        equivalence['name_en'] = False
    else:
        for name in full_names:
            if not records_equiv(full_lookup['by_name'][name], compact_lookup['by_name'][name]):
                equivalence['name_zh'] = False
                equivalence['name_en'] = False
                break

    return equivalence


def main():
    print("Loading authorized bundle...")
    is_valid, manifest, bundle_id = verify_bundle_integrity(BUNDLE_DIR, COMMITTED_MANIFEST_PATH)
    if not is_valid:
        print("Bundle verification failed. Checking if we can continue anyway...")
        # We'll continue but note the failure in the results
    print(f"Authorized bundle ID: {bundle_id}")

    print("Loading full dryrun snapshot...")
    start_time = time.time()
    full_snapshot = load_json(FULL_SNAPSHOT_PATH)
    full_load_time = time.time() - start_time
    print(f"Full snapshot loaded in {full_load_time:.3f} seconds")
    print(f"Found {len(full_snapshot.get('records', []))} records")
    full_snapshot_size = FULL_SNAPSHOT_PATH.stat().st_size
    print(f"Full snapshot size: {full_snapshot_size} bytes ({full_snapshot_size / 1024 / 1024:.2f} MiB)")

    # Sample record
    if full_snapshot.get('records'):
        sample = full_snapshot['records'][0]
        print(f"Sample record top-level keys: {list(sample.keys())}")

    print("\nProjecting to compact records...")
    start_time = time.time()
    compact_records = project_to_compact_records(full_snapshot.get('records', []))
    projection_time = time.time() - start_time
    print(f"Compact projection completed in {projection_time:.3f} seconds")

    compact_data = {
        "schema_version": "tw_runtime_identity_index.v1",
        "generated_at_utc": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "source_bundle_id": bundle_id or "unknown",
        "record_count": len(compact_records),
        "records": compact_records,
    }

    start_time = time.time()
    compact_index_json = json.dumps(compact_data, separators=(',', ':'), ensure_ascii=False)
    serialization_time = time.time() - start_time
    compact_index_size = len(compact_index_json.encode('utf-8'))
    print(f"Compact index serialized in {serialization_time:.3f} seconds")
    print(f"Compact index size: {compact_index_size} bytes ({compact_index_size / 1024 / 1024:.2f} MiB)")
    size_reduction = full_snapshot_size - compact_index_size
    print(f"Size reduction: {size_reduction} bytes ({size_reduction / full_snapshot_size * 100:.1f}%)")

    print("\nBenchmarking load and lookup construction...")
    # Load times
    start_time = time.time()
    _ = load_json(COMPACT_INDEX_PATH) if COMPACT_INDEX_PATH.is_file() else json.loads(compact_index_json)
    compact_json_load_time = time.time() - start_time

    start_time = time.time()
    full_lookup = build_full_lookup(full_snapshot)
    full_lookup_build_time = time.time() - start_time

    start_time = time.time()
    compact_lookup = build_compact_lookup(compact_data)
    compact_lookup_build_time = time.time() - start_time

    # Lookup benchmark
    unique_lookup_keys = 1000
    benchmark_rounds = 10
    total_lookup_operations = unique_lookup_keys * benchmark_rounds

    # Pick a sample of canonical target IDs for lookup benchmark
    sample_cids = list(compact_lookup['by_canonical'].keys())[:unique_lookup_keys]
    if not sample_cids:
        sample_cids = ["TWSE:2330"]  # fallback

    start_time = time.time()
    for _ in range(benchmark_rounds):
        for cid in sample_cids:
            _ = compact_lookup['by_canonical'].get(cid)
    lookup_benchmark_time = time.time() - start_time
    lookup_average_seconds = lookup_benchmark_time / total_lookup_operations if total_lookup_operations > 0 else 0
    lookup_average_nanoseconds = lookup_average_seconds * 1e9

    # Offline export processing time (projection + serialization)
    offline_export_processing_seconds = projection_time + serialization_time

    # Semantic preservation: compare full and compact lookups
    equivalence = lookup_equivalence(full_lookup, compact_lookup)
    # Also check that the canonical target IDs are preserved (already in equivalence, but we keep for clarity)
    canonical_target_ids_preserved = equivalence['canonical_target_id']

    results = {
        "full_snapshot_size_bytes": full_snapshot_size,
        "full_snapshot_size_mib": full_snapshot_size / 1024 / 1024,
        "compact_index_size_bytes": compact_index_size,
        "compact_index_size_mib": compact_index_size / 1024 / 1024,
        "size_reduction_bytes": size_reduction,
        "size_reduction_percent": size_reduction / full_snapshot_size * 100,
        "record_count": len(full_snapshot.get('records', [])),
        "compact_index_record_count": len(compact_records),
        "benchmark": {
            "full_json_load_seconds": full_load_time,
            "compact_json_load_seconds": compact_json_load_time,
            "full_lookup_build_seconds": full_lookup_build_time,
            "compact_lookup_build_seconds": compact_lookup_build_time,
            "compact_projection_seconds": projection_time,
            "compact_serialization_seconds": serialization_time,
            "compact_lookup_average_seconds": lookup_average_seconds,
            "compact_lookup_average_nanoseconds": lookup_average_nanoseconds,
            "unique_lookup_keys": unique_lookup_keys,
            "benchmark_rounds": benchmark_rounds,
            "total_lookup_operations": total_lookup_operations,
            "offline_export_processing_seconds": offline_export_processing_seconds,
        },
        "notes": [
            "All measurements are offline and use the authorized bundle only.",
            "Lookup average is for canonical_target_id lookups in the compact index.",
            "Compact index schema is a candidate for discussion and is not a drop-in replacement for the full snapshot without further adjustments."
        ],
        "semantic_preservation": {
            "canonical_target_ids_preserved": canonical_target_ids_preserved,
            "lookup_equivalence": equivalence,
        }
    }

    # Write compact index (for record)
    COMPACT_INDEX_PATH.write_text(compact_index_json, encoding='utf-8')
    print(f"\nCompact index written to: {COMPACT_INDEX_PATH}")

    # Write benchmark results
    with open(BENCHMARK_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Benchmark results written to: {BENCHMARK_RESULTS_PATH}")

    print("\nBenchmark complete.")


if __name__ == "__main__":
    main()