import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from scripts.probe_twse_openapi import probe as probe_twse_openapi
from scripts.probe_tpex_openapi import probe as probe_tpex_openapi
from scripts.probe_twse_mis import probe as probe_twse_mis
from scripts.probe_yahoo import probe as probe_yahoo

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ALLOWED_SOURCES = ["TWSE_OpenAPI", "TPEx_OpenAPI", "TWSE_MIS", "Yahoo_Finance"]
PROHIBITED_SOURCES = ["FinMind", "Fugle", "Fubon"]
MAX_TARGETS = 5

PROBE_FUNCTIONS = {
    "TWSE_OpenAPI": probe_twse_openapi,
    "TPEx_OpenAPI": probe_tpex_openapi,
    "TWSE_MIS": probe_twse_mis,
    "Yahoo_Finance": probe_yahoo
}


def validate_targets(targets):
    if not targets:
        raise ValueError("Error: Target list cannot be empty.")
    if len(targets) > MAX_TARGETS:
        raise ValueError(f"Error: Maximum of {MAX_TARGETS} targets allowed. Provided: {len(targets)}")

def validate_sources(sources):
    for source in sources:
        if source in PROHIBITED_SOURCES:
            raise ValueError(f"Error: {source} is strictly prohibited.")
        if source not in ALLOWED_SOURCES:
            raise ValueError(f"Error: {source} is not in the allowed sources list.")

def map_targets_for_source(source, targets):
    mapped_targets = []
    for t in targets:
        if source == "Yahoo_Finance":
            if t == "TAIEX" or t.lower() == "t00":
                mapped_targets.append("^TWII")
            elif t in {"8069", "5347"}: # typically TPEx
                mapped_targets.append(f"{t}.TWO")
            else: # typically TWSE
                mapped_targets.append(f"{t}.TW")
        elif source == "TWSE_MIS":
            if t == "TAIEX" or t.lower() == "t00":
                mapped_targets.append("tse_t00.tw")
            elif t in {"8069", "5347"}: # typically TPEx
                mapped_targets.append(f"otc_{t}.tw")
            else: # typically TWSE
                mapped_targets.append(f"tse_{t}.tw")
        else:
            mapped_targets.append(t) # Keep raw code for OpenAPI
    return mapped_targets

def build_summary_entry(source, result, output_file, original_targets):
    if result is None:
        return {
            "status": "failed",
            "contract_status": "failed",
            "http_ok": False,
            "parse_status": "failed",
            "normalization_status": "failed",
            "failed_targets": original_targets,
            "errors": ["Result is None"],
            "output_file": str(output_file.name) if output_file else None
        }

    contract_status = result.get("contract_status", "unknown")
    http_ok = result.get("http_ok", False)
    parse_status = result.get("parse_status", "unknown")
    normalization_status = result.get("normalization_status", "unknown")
    failed_targets = result.get("failed_targets", [])
    errors = result.get("errors", [])

    return {
        "status": contract_status,
        "contract_status": contract_status,
        "http_ok": http_ok,
        "parse_status": parse_status,
        "normalization_status": normalization_status,
        "failed_targets": failed_targets,
        "errors": errors,
        "output_file": str(output_file.name) if output_file else None
    }


def print_caveats():
    logger.info("=========================================")
    logger.info("CAVEATS & WARNINGS:")
    logger.info("- DO NOT run unrestricted probes.")
    logger.info(f"- Bounded target maximum: {MAX_TARGETS}")
    logger.info("- Outputs must only be written to research/live_probe_runs/m3g_04/")
    logger.info("- No full-market scan.")
    logger.info("- No execution, routing, or real-time trading guarantees.")
    logger.info("- Fubon, Fugle, and FinMind are STRICTLY PROHIBITED.")
    logger.info("=========================================")


def main():
    parser = argparse.ArgumentParser(description="Run bounded controlled live probes.")
    parser.add_argument("--targets", required=True, nargs="+", help="Explicit target subset")
    parser.add_argument("--sources", required=True, nargs="+", help="Explicit source list")
    args = parser.parse_args()

    targets = args.targets
    sources = args.sources

    try:
        validate_targets(targets)
        validate_sources(sources)
    except ValueError as e:
        logger.error(str(e))
        exit(1)

    print_caveats()

    output_dir = Path("research/live_probe_runs/m3g_04")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "targets": targets,
        "sources_requested": sources,
        "results": {}
    }

    for source in sources:
        logger.info(f"Running probe for {source} with timeout=10s...")
        probe_func = PROBE_FUNCTIONS.get(source)

        # 1. Source-specific target mapping
        mapped_targets = map_targets_for_source(source, targets)

        try:
            result = probe_func(symbols=mapped_targets)

            out_file = output_dir / f"{source}_{timestamp}.json"

            summary["results"][source] = build_summary_entry(source, result, out_file, targets)

            with open(out_file, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"{source} output written to {out_file}")

        except Exception as e:
            logger.error(f"{source} failed: {e}")

            failed_result = {
                "contract_status": "failed",
                "http_ok": False,
                "parse_status": "failed",
                "normalization_status": "failed",
                "failed_targets": targets,
                "errors": [str(e)]
            }
            summary["results"][source] = build_summary_entry(source, failed_result, None, targets)

    summary_file = output_dir / f"run_summary_{timestamp}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Run summary written to {summary_file}")


if __name__ == "__main__":
    main()
