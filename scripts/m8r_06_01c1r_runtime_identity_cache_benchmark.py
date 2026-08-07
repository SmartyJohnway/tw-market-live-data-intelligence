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
    Verify that the bundle matches the committed manifest.
    Returns (success, manifest, bundle_id) where success is a boolean.
    On failure, manifest and bundle_id are None.
    """
    try:
        manifest = load_json(manifest_path)
    except Exception as e:
        print(f"ERROR: Failed to load manifest {manifest_path}: {e}")
        return False, None, None

    bundle_id = manifest.get("bundle_id")
    expected_id = "m8r06-01b-20260807T053540Z"
    if bundle_id != expected_id:
        print(f"ERROR: Bundle ID mismatch. Expected {expected_id}, got {bundle_id}")
        return False, None, None

    # Check each artifact
    artifacts = [
        ("classification_records.json", "classification_records"),
        ("lifecycle_events.json", "lifecycle_events"),
        ("source_evidence_manifest.json", "source_evidence_manifest"),
        ("qualification_report.json", "qualification_report"),
        ("dryrun_snapshot.json", "dryrun_snapshot"),
        ("dryrun_manifest.json", "dryrun_manifest"),
    ]
    for file_name, manifest_key in artifacts:
        file_path = bundle_dir / file_name
        if not file_path.exists():
            print(f"ERROR: Missing file {file_path}")
            return False, None, None
        local_hash = sha256_file(file_path)
        manifest_hash = manifest.get(manifest_key, {}).get("sha256")
        if local_hash != manifest_hash:
            print(f"ERROR: Hash mismatch for {file_name}")
            print(f"  Expected: {manifest_hash}")
            print(f"  Got:      {local_hash}")
            return False, None, None

    # Check raw payloads
    raw_payloads = manifest.get("raw_payloads", [])
    for entry in raw_payloads:
        file_name = entry["file_name"]
        file_path = bundle_dir / "raw_payloads" / file_name
        if not file_path.exists():
            print(f"ERROR: Missing raw payload {file_path}")
            return False, None, None
        local_hash = sha256_file(file_path)
        manifest_hash = entry.get("sha256")
        if local_hash != manifest_hash:
            print(f"ERROR: Hash mismatch for raw payload {file_name}")
            print(f"  Expected: {manifest_hash}")
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
                import re
                norm = re.sub(r'\s+', '', name or '').casefold()
                if norm:
                    lookup['by_name'].setdefault(norm, []).append(rec)
    return lookup


def main():
    print("Loading authorized bundle...")
    # Verify bundle integrity against the committed manifest
    success, manifest, bundle_id = verify_bundle_integrity(BUNDLE_DIR, COMMITTED_MANIFEST_PATH)
    if not success:
        sys.exit(1)
    print(f"Authorized bundle ID: {bundle_id}")

    # Load full snapshot
    print("Loading full dryrun snapshot...")
    start = time.perf_counter()
    full_snapshot = load_json(FULL_SNAPSHOT_PATH)
    load_time = time.perf_counter() - start
    print(f"Full snapshot loaded in {load_time:.3f} seconds")

    # Extract records
    records = full_snapshot.get("records", [])
    record_count = len(records)
    print(f"Found {record_count} records")

    # Measure full snapshot size on disk
    full_size_bytes = FULL_SNAPSHOT_PATH.stat().st_size
    full_size_mib = full_size_bytes / (1024 * 1024)
    print(f"Full snapshot size: {full_size_bytes} bytes ({full_size_mib:.2f} MiB)")

    # Analyze a sample record to understand structure
    if records:
        sample = records[0]
        print("\nSample record top-level keys:", list(sample.keys()))
        # We'll use this to inform our compact record design

    # Project to compact records
    print("\nProjecting to compact records...")
    project_start = time.perf_counter()
    compact_records = project_to_compact_records(records)
    project_time = time.perf_counter() - project_start
    print(f"Compact projection completed in {project_time:.3f} seconds")

    # Build the compact index data (simple version)
    compact_data = {
        "schema_version": "tw_runtime_identity_index.v1",
        "generated_at_utc": full_snapshot.get("generated_at_utc"),
        "source_bundle_id": bundle_id,
        "record_count": len(compact_records),
        "records": compact_records,
    }

    # Write compact index to artifacts
    serialize_start = time.perf_counter()
    with COMPACT_INDEX_PATH.open('w', encoding='utf-8') as f:
        json.dump(compact_data, f, ensure_ascii=False, separators=(',', ':'))
    serialize_time = time.perf_counter() - serialize_start
    print(f"Compact index serialized in {serialize_time:.3f} seconds")

    # Measure compact index size
    compact_size_bytes = COMPACT_INDEX_PATH.stat().st_size
    compact_size_mib = compact_size_bytes / (1024 * 1024)
    print(f"Compact index size: {compact_size_bytes} bytes ({compact_size_mib:.2f} MiB)")

    # Size reduction
    size_reduction_bytes = full_size_bytes - compact_size_bytes
    size_reduction_percent = (size_reduction_bytes / full_size_bytes) * 100 if full_size_bytes > 0 else 0
    print(f"Size reduction: {size_reduction_bytes} bytes ({size_reduction_percent:.1f}%)")

    # Benchmark: load times
    print("\nBenchmarking load and lookup construction...")
    # Load full snapshot again (to measure load time)
    full_load_times = []
    for _ in range(3):
        t0 = time.perf_counter()
        load_json(FULL_SNAPSHOT_PATH)
        t1 = time.perf_counter()
        full_load_times.append(t1 - t0)
    full_load_median = median(full_load_times)

    # Load compact index
    compact_load_times = []
    for _ in range(3):
        t0 = time.perf_counter()
        load_json(COMPACT_INDEX_PATH)
        t1 = time.perf_counter()
        compact_load_times.append(t1 - t0)
    compact_load_median = median(compact_load_times)

    # Build lookup from full snapshot (as done in the adapter)
    # We'll time the build_verified_security_master_lookup function from the adapter.
    sys.path.append(str(REPO_ROOT / "scripts"))
    from m8r_03d_f1_security_master_snapshot_adapter import build_verified_security_master_lookup

    full_build_times = []
    for _ in range(3):
        t0 = time.perf_counter()
        build_verified_security_master_lookup(full_snapshot)
        t1 = time.perf_counter()
        full_build_times.append(t1 - t0)
    full_build_median = median(full_build_times)

    # Build lookup from compact index: we need to create a similar lookup structure.
    # We'll use the build_compact_lookup function defined above.
    compact_build_times = []
    for _ in range(3):
        t0 = time.perf_counter()
        build_compact_lookup(compact_data)
        t1 = time.perf_counter()
        compact_build_times.append(t1 - t0)
    compact_build_median = median(compact_build_times)

    # Deterministic lookup benchmark: we'll pick 1000 keys from the canonical_target_id set
    # (or as many as available if less than 1000) and measure lookup time in the compact lookup.
    cids = [rec.get('canonical_target_id') for rec in compact_data.get('records', []) if rec.get('canonical_target_id')]
    # Remove duplicates and take first 1000
    unique_cids = list(dict.fromkeys(cids))[:1000]
    if not unique_cids:
        unique_cids = ["TWSE:2330"]  # fallback

    # We'll use the compact lookup built above (we can build it once and time lookups)
    compact_lookup = build_compact_lookup(compact_data)
    # Time 1000 lookups by canonical_target_id (should be O(1))
    lookup_times = []
    for _ in range(10):  # 10 rounds of 100 lookups each
        t0 = time.perf_counter()
        for cid in unique_cids:
            _ = compact_lookup['by_canonical'].get(cid)
        t1 = time.perf_counter()
        lookup_times.append((t1 - t0) / len(unique_cids))  # average per lookup
    lookup_avg_seconds = median(lookup_times)
    lookup_avg_nanoseconds = lookup_avg_seconds * 1_000_000_000

    # Offline export processing time: we can time the export_verified_security_master_snapshot
    # function from the exporter, but note that we are not to run the exporter for production
    # artifacts. However, we can time it as part of the benchmark because it's offline and uses
    # the local input files.
    # We'll load the classification_records and lifecycle_events from the bundle.
    from m8r_03d_f1_security_master_snapshot_exporter import export_verified_security_master_snapshot, compute_skill_contract_hash

    classification_records_path = BUNDLE_DIR / "classification_records.json"
    lifecycle_events_path = BUNDLE_DIR / "lifecycle_events.json"
    classification_records = load_json(classification_records_path)
    lifecycle_events = load_json(lifecycle_events_path)

    # We need to provide source_context and timestamps from the full snapshot.
    source_context = {
        "skill_contract_hash": manifest.get("skill_contract_hash"),
        "coverage_status": "governed_identity_knowledge_universe",  # as per task
    }
    generated_at_utc = full_snapshot.get("generated_at_utc")
    effective_observation_date = full_snapshot.get("effective_observation_date")

    export_times = []
    for _ in range(3):
        t0 = time.perf_counter()
        export_verified_security_master_snapshot(
            classification_records=classification_records,
            lifecycle_events=lifecycle_events,
            source_context=source_context,
            generated_at_utc=generated_at_utc,
            effective_observation_date=effective_observation_date,
        )
        t1 = time.perf_counter()
        export_times.append(t1 - t0)
    export_median = median(export_times)

    # Collect results
    results = {
        "full_snapshot_size_bytes": full_size_bytes,
        "full_snapshot_size_mib": round(full_size_mib, 2),
        "compact_index_size_bytes": compact_size_bytes,
        "compact_index_size_mib": round(compact_size_mib, 2),
        "size_reduction_bytes": size_reduction_bytes,
        "size_reduction_percent": round(size_reduction_percent, 1),
        "record_count": record_count,
        "compact_index_record_count": len(compact_records),
        "benchmark": {
            "full_json_load_seconds": round(full_load_median, 3),
            "compact_json_load_seconds": round(compact_load_median, 3),
            "full_lookup_build_seconds": round(full_build_median, 3),
            "compact_lookup_build_seconds": round(compact_build_median, 3),
            "compact_projection_seconds": round(project_time, 3),
            "compact_serialization_seconds": round(serialize_time, 3),
            "compact_lookup_average_seconds": round(lookup_avg_seconds, 6),
            "compact_lookup_average_nanoseconds": round(lookup_avg_nanoseconds, 0),
            "unique_lookup_keys": len(unique_cids),
            "benchmark_rounds": 10,
            "total_lookup_operations": len(unique_cids) * 10,
            "offline_export_processing_seconds": round(export_median, 3),
        },
        "notes": [
            "All measurements are offline and use the authorized bundle only.",
            "Lookup average is for canonical_target_id lookups in the compact index.",
            "Compact index schema is a candidate for discussion and is not a drop-in replacement for the full snapshot without further adjustments."
        ]
    }

    # Additionally, we can run a semantic preservation check (optional for now)
    # We'll do a quick check: ensure that every canonical_target_id in the full snapshot
    # appears in the compact index.
    full_cids = set()
    for rec in records:
        cid = rec.get('canonical_target_id')
        if cid:
            full_cids.add(cid)
    compact_cids = set()
    for rec in compact_records:
        cid = rec.get('canonical_target_id')
        if cid:
            compact_cids.add(cid)
    missing_in_compact = full_cids - compact_cids
    extra_in_compact = compact_cids - full_cids
    if missing_in_compact:
        print(f"WARNING: {len(missing_in_compact)} canonical_target_ids missing in compact index")
    if extra_in_compact:
        print(f"WARNING: {len(extra_in_compact)} extra canonical_target_ids in compact index")
    results["semantic_preservation"] = {
        "canonical_target_ids_preserved": len(missing_in_compact) == 0 and len(extra_in_compact) == 0,
        "missing_in_compact": list(missing_in_compact)[:5],
        "extra_in_compact": list(extra_in_compact)[:5],
    }

    # Write benchmark results
    with BENCHMARK_RESULTS_PATH.open('w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Benchmark results written to {BENCHMARK_RESULTS_PATH}")

    print("\nBenchmark complete.")


if __name__ == "__main__":
    main()