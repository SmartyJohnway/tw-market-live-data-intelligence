"""Bounded, path-free failure diagnostics for hosted Windows Native acceptance.

Only fixed vocabulary codes and booleans leave the runner. Raw logs remain local.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

STEPS = {"bootstrap-A", "bootstrap-A-again", "bootstrap-B", "stale-runtime"}
PATTERNS = (
    ("GUARD_DENIAL", r"acceptance guard:"),
    ("NO_MATCHING_WHEEL", r"No matching distribution found|Could not find a version that satisfies"),
    ("WHEEL_HASH_MISMATCH", r"THESE PACKAGES DO NOT MATCH THE HASHES|hashes do not match"),
    ("ENSUREPIP_FAILURE", r"ensurepip.*(?:returned non-zero|failed|CalledProcessError)"),
    ("ACCESS_DENIED", r"\[WinError 5\]|Access is denied|Permission denied"),
    ("PATH_TOO_LONG", r"\[WinError 206\]|File name too long"),
    ("PYTHON_VERSION_REJECTED", r"Windows CPython 3\.13 x64 required"),
    ("MISSING_BOOTSTRAP_RESOURCE", r"bootstrap dependency resources missing"),
    ("DEPENDENCY_MANIFEST_MISMATCH", r"installed distributions differ from exact dependency manifest"),
    ("PIP_MODULE_MISSING", r"No module named pip"),
    ("CHILD_PROCESS_FAILED", r"returned non-zero exit status|CalledProcessError"),
)

def _step(stderr: str) -> str:
    if re.search(r"['\"]-m['\"]\s*,\s*['\"]venv['\"]", stderr):
        return "VENV_CREATION"
    if re.search(r"['\"]-m['\"]\s*,\s*['\"]pip['\"]", stderr):
        if "'install'" in stderr or '"install"' in stderr:
            return "OFFLINE_WHEEL_INSTALL"
        if "'check'" in stderr or '"check"' in stderr:
            return "PIP_CHECK"
        return "PIP_OTHER"
    return "UNDETERMINED"

SIGNALS = {
    "VENV": r"\bvenv\b", "ENSUREPIP": r"ensurepip",
    "PIP": r"\bpip\b", "INSTALL": r"\binstall\b",
    "CHECK": r"\bcheck\b", "WHEEL": r"\bwheel(?:s|house)?\b",
    "HASH": r"\bhash(?:es)?\b", "REQUIREMENT": r"requirement",
    "DISTRIBUTION": r"distribution", "METADATA": r"metadata",
    "DEPENDENCY": r"dependenc", "CONFLICT": r"conflict",
    "PERMISSION": r"permission|access.denied|winerror 5",
    "PATH": r"winerror 206|path.too.long|filename too long",
    "MISSING": r"not found|no such file|missing",
    "SSL": r"\bssl\b|certificate", "NETWORK": r"network|connection",
    "GUARD": r"acceptance guard", "PYTHON": r"python",
    "PROCESS": r"calledprocesserror|returned non.zero|subprocess",
    "TRACEBACK": r"traceback", "ERROR": r"\berror\b|failed",
}
def signals(text: str) -> list[str]:
    return sorted(k for k, pattern in SIGNALS.items()
                  if re.search(pattern, text[-131072:], re.IGNORECASE))

def runtime_probes(root: Path) -> dict[str, bool]:
    try:
        packages = root / "Location A With Spaces 非ASCII"
        dist = next((p for p in packages.iterdir() if p.is_dir()), None)
        if dist is None:
            return {"bundle_present": False}
        runtime = dist / "runtime"
        venv = runtime / "venv"
        site = venv / "Lib" / "site-packages"
        seen = set()
        for entry in site.glob("*.dist-info"):
            if entry.is_dir():
                metadata = entry / "METADATA"
                if metadata.is_file():
                    text = metadata.read_text(encoding="utf-8", errors="replace")[:8192]
                    fields = [line[6:].strip() for line in text.splitlines()
                              if line.startswith("Name: ")]
                    if fields:
                        seen.add(re.sub(r"[-_.]+", "-", fields[0]).lower())
        expected = set()
        manifest = dist / "dependency-manifest.json"
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            expected = {re.sub(r"[-_.]+", "-", d["name"]).lower()
                        for d in data.get("dependencies", [])}
        observed = seen - {"pip"}
        return {"bundle_present": True, "runtime_present": runtime.is_dir(),
                "venv_present": venv.is_dir(),
                "venv_python_present": (venv / "Scripts" / "python.exe").is_file(),
                "site_packages_present": site.is_dir(),
                "runtime_marker_present": (runtime / "runtime-marker.json").is_file(),
                "expected_distribution_count": len(expected),
                "observed_distribution_count": len(observed),
                "missing_distribution_count": len(expected - observed),
                "unexpected_distribution_count": len(observed - expected),
                "distribution_set_matches": bool(expected) and expected == observed}
    except OSError:
        return {"probe_error": True}

def diagnose(root: Path) -> dict:
    result = {"status": "DIAGNOSTIC_UNAVAILABLE", "last_stage": "NONE",
              "last_exit": -1, "bootstrap_substep": "UNDETERMINED",
              "failure_class": "UNKNOWN", "stderr_present": False}
    try:
        final = json.loads((root / "final_result.json").read_text(encoding="utf-8"))
        sequence = final.get("sequence", [])
        if not isinstance(sequence, list) or not sequence:
            return result
        if final.get("status") == "PASS":
            result["status"] = "PASS"
            result["last_exit"] = 0
            return result
        last = sequence[-1]
        label = last.get("label")
        result["status"] = "AVAILABLE"
        result["last_stage"] = label if label in STEPS else "OTHER_STAGE"
        code = last.get("exit_code")
        result["last_exit"] = code if type(code) is int and -1 <= code <= 255 else -1
        if label not in STEPS:
            return result
        record = json.loads((root / "logs" / (label + ".json")).read_text(encoding="utf-8"))
        stderr = record.get("stderr", "")
        if not isinstance(stderr, str):
            return result
        stderr = stderr[-131072:]
        stdout = record.get("stdout", "")
        if not isinstance(stdout, str):
            stdout = ""
        result["stderr_present"] = bool(stderr)
        result["stderr_signals"] = signals(stderr)
        result["stdout_signals"] = signals(stdout)
        result["runtime_probes"] = runtime_probes(root)
        result["bootstrap_substep"] = _step(stderr)
        for name, expression in PATTERNS:
            if re.search(expression, stderr, re.IGNORECASE | re.DOTALL):
                result["failure_class"] = name
                break
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return result
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args()
    print("NATIVE_BOOTSTRAP_DIAGNOSTIC " +
          json.dumps(diagnose(args.run), sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
