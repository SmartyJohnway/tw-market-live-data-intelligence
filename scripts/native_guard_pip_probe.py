"""Isolated offline acceptance-guard probe; prints only whitelisted outcomes."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

def main():
    guard = Path(sys.argv[1]).resolve()
    exec(compile(guard.read_text(encoding="utf-8-sig"), str(guard), "exec"),
         {"__file__": str(guard)})
    outcome = subprocess.run(
        [sys.executable, "-I", "-B", "-m", "pip", "--isolated",
         "check", "--disable-pip-version-check"],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=30, check=False)
    print(json.dumps({"status": "PASS" if outcome.returncode == 0 else "FAIL",
                      "stdout_present": bool(outcome.stdout),
                      "stderr_present": bool(outcome.stderr)},
                     sort_keys=True))

if __name__ == "__main__":
    main()
