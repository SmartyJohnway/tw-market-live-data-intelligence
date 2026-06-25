import json
from pathlib import Path
from typing import Dict, Any, Optional

def load_run_summary(summary_path: str | Path) -> dict:
    """Loads and parses the run summary file."""
    path = Path(summary_path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"adapter_internal_error": str(e)}

def load_referenced_evidence(summary: dict, base_dir: str | Path) -> dict:
    """Loads all referenced per-source evidence files."""
    evidence = {}
    base_path = Path(base_dir)
    results = summary.get("results", {})

    for source_id, source_summary in results.items():
        output_file = source_summary.get("output_file")
        if not output_file:
            evidence[source_id] = {"error": "Missing output_file in summary"}
            continue

        evidence_path = base_path / output_file
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                evidence[source_id] = json.load(f)
        except Exception as e:
            evidence[source_id] = {"error": f"Failed to load evidence file: {e}"}

    return evidence

def standardize_symbol(source_id: str, source_symbol: str) -> Optional[str]:
    """
    Adapter-local symbol standardization.
    Strips source-specific extensions to produce a canonical symbol.
    """
    if source_id == "Yahoo_Finance":
        if source_symbol == "^TWII":
            return "TAIEX"
        # Remove .TW or .TWO
        if source_symbol.endswith(".TW"):
            return source_symbol[:-3]
        if source_symbol.endswith(".TWO"):
            return source_symbol[:-4]
        return source_symbol

    elif source_id == "TWSE_MIS":
        # e.g., tse_2330.tw -> 2330, otc_8069.tw -> 8069, tse_t00.tw -> TAIEX
        if source_symbol == "tse_t00.tw":
            return "TAIEX"

        parts = source_symbol.split("_")
        if len(parts) == 2:
            code_part = parts[1]
            if code_part.endswith(".tw"):
                return code_part[:-3]

        return None

    elif source_id in ["TWSE_OpenAPI", "TPEx_OpenAPI"]:
        # Keep plain stock code as-is
        return source_symbol

    return None

def map_source_evidence_to_snapshot_input(source_id: str, envelope: dict, summary_entry: dict) -> dict:
    """
    Translates a single source's evidence envelope into the snapshot input shape.
    Returns a dictionary of standardized symbols to snapshot data objects.
    """
    # If the summary indicates failure or identity mismatch, don't map data
    contract_status = summary_entry.get("contract_status", "")
    if contract_status == "identity_mismatch" or not summary_entry.get("http_ok", False):
        return {}

    normalized_sample = envelope.get("normalized_sample", {})
    if not normalized_sample:
        return {}

    snapshot_inputs = {}

    for raw_symbol, source_data in normalized_sample.items():
        std_symbol = standardize_symbol(source_id, raw_symbol)
        if not std_symbol:
            continue

        mapped_data = {
            "name": source_data.get("name"),
            "exchange": source_data.get("exchange"),
            "last_price": source_data.get("last_price") or source_data.get("regular_market_price"),
            "change": source_data.get("change"),
            "change_pct": source_data.get("change_pct"),
            "open": source_data.get("open"),
            "high": source_data.get("high"),
            "low": source_data.get("low"),
            "previous_close": source_data.get("previous_close"),
            "volume": source_data.get("volume"),
            "bid_ask": source_data.get("bid_ask"),
            "source_time": source_data.get("source_time"),
            "retrieved_time": source_data.get("retrieved_time"),
            "price_semantics": envelope.get("price_semantics"),
            "freshness_status": envelope.get("freshness_status"),
            "delay_status": envelope.get("delay_status"),
            "staleness_seconds": envelope.get("staleness_seconds"),
            "data_quality_flags": source_data.get("data_quality_flags", []),
            "caveats": envelope.get("warnings", []),
            "raw_payload_ref": source_data.get("raw_payload_ref")
        }

        # Apply source-specific mapping rules and caveats
        if source_id == "TWSE_MIS":
            mapped_data["price_semantics"] = "live_candidate"
            if "unofficial_source_risk" not in mapped_data["caveats"]:
                mapped_data["caveats"].append("unofficial_source_risk")

        elif source_id == "Yahoo_Finance":
            if mapped_data["delay_status"] == "delayed":
                mapped_data["price_semantics"] = "stale_candidate"
            else:
                mapped_data["price_semantics"] = "live_candidate"
            if "third_party_coverage_caveats" not in mapped_data["caveats"]:
                mapped_data["caveats"].append("third_party_coverage_caveats")

        elif source_id in ["TWSE_OpenAPI", "TPEx_OpenAPI"]:
            mapped_data["price_semantics"] = "official_eod_reference_only"
            if "official_eod_reference_only" not in mapped_data["caveats"]:
                mapped_data["caveats"].append("official_eod_reference_only")

        # Clean up None values
        snapshot_inputs[std_symbol] = {k: v for k, v in mapped_data.items() if v is not None}

    return snapshot_inputs

def build_mock_inputs_from_live_probe_run(summary_path: str | Path) -> dict:
    """Convenience function to get just the mock_inputs dict."""
    report = build_adapter_report(summary_path)
    return report.get("mock_inputs_preview", {})

def build_adapter_report(summary_path: str | Path) -> dict:
    """
    Main orchestration function.
    Reads the run summary and evidence, maps it, and returns a comprehensive report.
    Does not make network calls or write files.
    """
    path = Path(summary_path)
    base_dir = path.parent

    summary = load_run_summary(path)
    if "adapter_internal_error" in summary or "results" not in summary:
        return {
            "adapter_status": "malformed_input",
            "summary_path": str(summary_path),
            "sources_seen": [],
            "sources_mapped": [],
            "sources_blocked": [],
            "targets_mapped": [],
            "failed_targets": {},
            "unsupported_targets": {},
            "warnings": [],
            "errors": [summary.get("adapter_internal_error", "Malformed summary: missing 'results' key")],
            "mock_inputs_preview": {}
        }

    evidence_files = load_referenced_evidence(summary, base_dir)

    report = {
        "adapter_status": "mapping_pass",
        "summary_path": str(summary_path),
        "sources_seen": list(summary["results"].keys()),
        "sources_mapped": [],
        "sources_blocked": [],
        "targets_mapped": [],
        "failed_targets": {},
        "unsupported_targets": {},
        "warnings": [],
        "errors": [],
        "mock_inputs_preview": {}
    }

    all_mock_inputs = {}
    has_valid_source = False
    has_blocked_source = False

    for source_id, summary_entry in summary["results"].items():
        evidence = evidence_files.get(source_id, {})

        # Propagate failed/unsupported targets
        report["failed_targets"][source_id] = summary_entry.get("failed_targets", []) + evidence.get("failed_targets", [])
        report["unsupported_targets"][source_id] = evidence.get("unsupported_targets", [])

        contract_status = summary_entry.get("contract_status", "")
        if contract_status == "identity_mismatch":
            report["sources_blocked"].append(source_id)
            report["errors"].append(f"Source {source_id} blocked due to identity mismatch")
            has_blocked_source = True
            continue

        if "error" in evidence:
            report["sources_blocked"].append(source_id)
            report["errors"].append(f"Source {source_id} blocked: {evidence['error']}")
            has_blocked_source = True
            continue

        if not summary_entry.get("http_ok", False):
            report["sources_blocked"].append(source_id)
            report["warnings"].append(f"Source {source_id} not mapped (HTTP failed or offline)")
            has_blocked_source = True
            continue

        mapped_inputs = map_source_evidence_to_snapshot_input(source_id, evidence, summary_entry)
        if mapped_inputs:
            all_mock_inputs[source_id] = mapped_inputs
            report["sources_mapped"].append(source_id)
            report["targets_mapped"].extend(mapped_inputs.keys())
            has_valid_source = True
        else:
            report["warnings"].append(f"Source {source_id} processed but yielded no mapped targets")

    report["targets_mapped"] = list(set(report["targets_mapped"]))
    report["mock_inputs_preview"] = all_mock_inputs

    # Determine overall status
    if has_blocked_source:
        if has_valid_source:
            report["adapter_status"] = "partial_mapping"
        else:
            # Check if blocked purely by identity mismatch
            if any(summary["results"][s].get("contract_status") == "identity_mismatch" for s in summary["results"]):
                 report["adapter_status"] = "identity_mismatch_blocked"
            else:
                 report["adapter_status"] = "blocked_no_valid_inputs"
    elif not has_valid_source:
        report["adapter_status"] = "blocked_no_valid_inputs"

    return report
