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

    if not targets:
        logger.error("Error: Target list cannot be empty.")
        exit(1)

    if len(targets) > MAX_TARGETS:
        logger.error(f"Error: Maximum of {MAX_TARGETS} targets allowed. Provided: {len(targets)}")
        exit(1)

    for source in sources:
        if source in PROHIBITED_SOURCES:
            logger.error(f"Error: {source} is strictly prohibited.")
            exit(1)
        if source not in ALLOWED_SOURCES:
            logger.error(f"Error: {source} is not in the allowed sources list.")
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
        try:
            result = probe_func(symbols=targets)

            summary["results"][source] = {
                "status": "completed"
            }

            out_file = output_dir / f"{source}_{timestamp}.json"
            with open(out_file, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"{source} output written to {out_file}")

        except Exception as e:
            logger.error(f"{source} failed: {e}")
            summary["results"][source] = {
                "status": "failed",
                "error": str(e)
            }

    summary_file = output_dir / f"run_summary_{timestamp}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Run summary written to {summary_file}")


if __name__ == "__main__":
    main()
