"""Line scanner for positive forbidden behavior claims with narrow negative-phrase exclusions."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

PATTERNS = {
    "live_probe_execution": r"\b(run|execute|start|invoke)\b[^.;\n]*(live probe)",
    "production_write": r"\b(write|refresh|publish|promote)\b[^.;\n]*(production|prod)",
    "frontend_public_write": r"\b(write|publish|refresh)\b[^.;\n]*frontend/public|frontend/public[^.;\n]*\b(write|publish|refresh)\b",
    "research_generated_write": r"\b(write|generate|publish)\b[^.;\n]*research/generated|research/generated[^.;\n]*\b(write|generate|publish)\b",
    "broker_auth_activation": r"\b(activate|enable|login|authenticate)\b[^.;\n]*(broker|auth)",
    "trading_signal": r"\b(buy|sell|hold)\b|target price|\branking\b|\brecommendation\b",
    "realtime_guarantee": r"realtime guaranteed|real-time guaranteed|official realtime",
}
NEGATIVE_PHRASES = [
    "no live probe", "do not run live probe", "live probe unauthorized", "live probe blocked",
    "no production write", "production write blocked", "no frontend/public write",
    "no research/generated write", "broker/auth activation blocked", "not a trading signal",
    "no trading signal", "no realtime guarantee", "not realtime guaranteed",
]


def _mask_negative_phrases(line: str) -> str:
    masked = line.lower()
    for phrase in NEGATIVE_PHRASES:
        masked = masked.replace(phrase, "")
    return masked


def scan_text(text: str, path: str = "<text>") -> list[dict]:
    findings = []
    for line_no, line in enumerate(text.splitlines(), 1):
        candidate = _mask_negative_phrases(line)
        for code, pattern in PATTERNS.items():
            if re.search(pattern, candidate, flags=re.IGNORECASE):
                findings.append({"code": code, "path": path, "line": line_no, "text": line.strip()})
    return findings


def scan_files(files: list[str | Path]) -> list[dict]:
    findings = []
    for file_path in files:
        findings.extend(scan_text(Path(file_path).read_text(encoding="utf-8"), str(file_path)))
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    findings = scan_files(args.files)
    print(json.dumps({"ok": not findings, "findings": findings}, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
