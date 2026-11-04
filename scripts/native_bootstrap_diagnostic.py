"""Bounded, path-free failure diagnostics for hosted Windows Native acceptance.

Only fixed vocabulary codes and booleans leave the runner. Raw logs remain local.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
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
        versions = {}
        for entry in site.glob("*.dist-info"):
            if entry.is_dir():
                metadata = entry / "METADATA"
                if metadata.is_file():
                    text = metadata.read_text(encoding="utf-8", errors="replace")[:8192]
                    fields = [line[6:].strip() for line in text.splitlines()
                              if line.startswith("Name: ")]
                    if fields:
                        name = re.sub(r"[-_.]+", "-", fields[0]).lower()
                        seen.add(name)
                        ver = [line[9:].strip() for line in text.splitlines()
                               if line.startswith("Version: ")]
                        if ver:
                            versions[name] = ver[0]
        expected_versions = {}
        manifest = dist / "dependency-manifest.json"
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            expected_versions = {re.sub(r"[-_.]+", "-", d["name"]).lower(): d["version"]
                                 for d in data.get("dependencies", [])}
        expected = set(expected_versions)
        observed = seen - {"pip"}
        mismatch = sum(versions.get(k) != v for k, v in expected_versions.items())
        pip_status = "NOT_RUN"
        pip_stdout_signals = []
        pip_stderr_signals = []
        py = venv / "Scripts" / "python.exe"
        if py.is_file():
            safe_env = {k: v for k, v in os.environ.items()
                        if not k.upper().startswith(("PIP_", "PYTHON"))}
            safe_env.update(PIP_CONFIG_FILE=os.devnull, PIP_NO_INDEX="1",
                            PYTHONDONTWRITEBYTECODE="1")
            try:
                completed = subprocess.run(
                    [str(py), "-I", "-B", "-m", "pip", "--isolated",
                     "check", "--disable-pip-version-check"],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=30, env=safe_env, check=False)
                pip_status = "PASS" if completed.returncode == 0 else "FAIL"
                pip_stdout_signals = signals(completed.stdout)
                pip_stderr_signals = signals(completed.stderr)
            except (OSError, subprocess.TimeoutExpired):
                pip_status = "EXECUTION_ERROR"
        guarded_status = "NOT_RUN"
        guarded_stdout_present = False
        guarded_stderr_present = False
        guard_script = root / "acceptance_guard.py"
        probe_script = Path(__file__).with_name("native_guard_pip_probe.py")
        if py.is_file() and guard_script.is_file() and probe_script.is_file():
            guarded_env = safe_env.copy()
            guarded_env.update(
                TW_MARKET_ACCEPTANCE_GUARD="1",
                TW_MARKET_ACCEPTANCE_GUARD_BASE=str(root.parents[2]),
                TW_MARKET_GUARD_LOG=str(root / "probe-guard-events.jsonl"))
            try:
                test = subprocess.run(
                    [str(py), "-I", "-B", str(probe_script), str(guard_script)],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=40, check=False,
                    env=guarded_env, cwd=root)
                if test.returncode == 0:
                    parsed = json.loads(test.stdout)
                    guarded_status = parsed.get("status", "UNREADABLE")
                    guarded_stdout_present = parsed.get("stdout_present") is True
                    guarded_stderr_present = parsed.get("stderr_present") is True
                else:
                    guarded_status = "EXECUTION_ERROR"
            except (OSError, ValueError, subprocess.TimeoutExpired):
                guarded_status = "EXECUTION_ERROR"
        return {"bundle_present": True, "runtime_present": runtime.is_dir(),
                "venv_present": venv.is_dir(),
                "venv_python_present": (venv / "Scripts" / "python.exe").is_file(),
                "site_packages_present": site.is_dir(),
                "runtime_marker_present": (runtime / "runtime-marker.json").is_file(),
                "expected_distribution_count": len(expected),
                "observed_distribution_count": len(observed),
                "missing_distribution_count": len(expected - observed),
                "unexpected_distribution_count": len(observed - expected),
                "version_mismatch_count": mismatch,
                "pip_check_status": pip_status,
                "pip_check_stdout_signals": pip_stdout_signals,
                "pip_check_stderr_signals": pip_stderr_signals,
                "guarded_pip_check_status": guarded_status,
                "guarded_pip_stdout_present": guarded_stdout_present,
                "guarded_pip_stderr_present": guarded_stderr_present,
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
        stage_match = re.search(
            r"BOOTSTRAP_CHILD_STAGE=(VENV_CREATE|PIP_INSTALL|PIP_CHECK|DISTRIBUTION_PROBE)",
            stderr)
        result["child_failure_stage"] = stage_match.group(1) if stage_match else "UNKNOWN"
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
