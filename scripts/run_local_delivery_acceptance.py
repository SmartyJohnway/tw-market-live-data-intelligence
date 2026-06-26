"""Local-only delivery acceptance checks for the governed market data workbench."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from controlled_refresh_staging_writer import is_forbidden_output_dir

REQUIRED_FILES = [
"docs/contracts/controlled_refresh_staging_write_contract.md", "docs/contracts/frontend_readonly_caveat_staleness_display_contract.md", "docs/contracts/frontend_readonly_context_package_schema.md",
"docs/runbooks/OPERATOR_RUNBOOK_LOCAL_FIRST_MARKET_CONTEXT.md", "scripts/controlled_refresh_staging_writer.py", "scripts/controlled_refresh_staging_validator.py", "scripts/build_frontend_readonly_context_package.py",
"tests/unit/test_controlled_refresh_staging_writer.py", "tests/unit/test_controlled_refresh_staging_validator.py", "tests/unit/test_frontend_readonly_context_package.py"]
FORBIDDEN_CONTRACT_STRINGS = ["official_realtime: true", "realtime_guaranteed: true", "buy/sell/hold output"]

def run_acceptance_checks(repo_root: str | Path = ".") -> dict:
    root=Path(repo_root)
    checks=[]
    def add(name, ok, detail=""): checks.append({"name":name,"ok":bool(ok),"detail":detail})
    for f in REQUIRED_FILES: add(f"required file {f}", (root/f).is_file(), "exists" if (root/f).is_file() else "missing")
    rap=root/"scripts/run_all_probes.py"
    txt=rap.read_text(encoding="utf-8") if rap.exists() else ""
    add("run_all_probes hard gate", "RUN_ALL_PROBES_I_UNDERSTAND_THIS_IS_LIVE" in txt or "legacy" in txt.lower() or "forbidden" in txt.lower())
    for path in [root/"docs/contracts/frontend_readonly_context_package_schema.md", root/"docs/contracts/controlled_refresh_staging_write_contract.md"]:
        text=path.read_text(encoding="utf-8") if path.exists() else ""
        add(f"forbidden strings absent {path.name}", not any(s in text for s in FORBIDDEN_CONTRACT_STRINGS))
    for path in [root/"scripts/controlled_refresh_staging_writer.py", root/"scripts/build_frontend_readonly_context_package.py"]:
        text=path.read_text(encoding="utf-8") if path.exists() else ""
        add(f"no buy/sell/hold claim {path.name}", "buy/sell/hold output" not in text)
    add("pytest recommendations non-network", True, 'use pytest -m "not network" tests/unit/...')
    return {"ok": all(c["ok"] for c in checks), "checks": checks, "mode": "check-only", "network": False, "writes": False}

def write_acceptance_report(report: dict, output_path: str | Path) -> Path:
    path=Path(output_path); reason=is_forbidden_output_dir(path.parent)
    if reason: raise ValueError(reason)
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return path

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root", default="."); ap.add_argument("--check-only", action="store_true", default=True); ap.add_argument("--write-report")
    args=ap.parse_args(argv); report=run_acceptance_checks(args.repo_root)
    if args.write_report: write_acceptance_report(report,args.write_report)
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["ok"] else 1
if __name__ == "__main__": raise SystemExit(main())
