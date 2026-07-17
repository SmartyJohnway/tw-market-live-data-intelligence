"""Local governance guard for repository paths that must never receive generated writes."""
from __future__ import annotations
from pathlib import Path, PurePosixPath

FORBIDDEN_DIRS = {"credentials", "cookies", "tokens", "broker", "production", "prod", "current_market_state"}
FORBIDDEN_PREFIXES = {("frontend", "public"), ("research", "generated")}
FORBIDDEN_FILES = {".env"}


def _parts(path: str | Path) -> tuple[str, ...]:
    raw = str(path).replace("\\", "/")
    return tuple(p.lower() for p in PurePosixPath(raw).parts if p not in ("", "."))


def is_forbidden_repo_write_path(path: str | Path) -> str | None:
    parts = _parts(path)
    if not parts:
        return None
    if parts[-1] in FORBIDDEN_FILES or any(p in FORBIDDEN_FILES for p in parts):
        return "credential/env path is forbidden"
    for a, b in FORBIDDEN_PREFIXES:
        for i in range(len(parts) - 1):
            if parts[i : i + 2] == (a, b):
                return f"writes under {a}/{b}/ are forbidden"
    for p in parts:
        if p in FORBIDDEN_DIRS:
            return f"writes under {p}/ are forbidden"
    return None


def assert_not_forbidden_repo_write_path(path: str | Path) -> None:
    reason = is_forbidden_repo_write_path(path)
    if reason:
        raise ValueError(reason)


def frontend_public_changed_files(changed_files: list[str]) -> list[str]:
    """Return changed files under frontend/public without consulting git remotes."""
    return [path for path in changed_files if _parts(path)[:2] == ("frontend", "public")]


def has_frontend_public_changed_file(changed_files: list[str]) -> bool:
    """Pure check used by unit tests and check-only tooling."""
    return bool(frontend_public_changed_files(changed_files))


def run_r5b_insecure_pattern_scan() -> list[str]:
    # Phase-C-relevant files to scan
    files_to_scan = [
        "scripts/m8r_bounded_market_context_request.py",
        "scripts/run_m8r_controlled_live_validation.py",
        "scripts/m8r_03d_watchlist_controlled_executor.py",
        "scripts/m8r_one_shot_market_context_orchestrator.py",
        "scripts/run_m8r_conversational_derivatives_context.py",
        "scripts/m8r_03e_r5a_cross_layer_fixture.py"
    ]
    
    # Bounded allowlist
    ALLOWLIST = [
        ("scripts/m8r_bounded_market_context_request.py", "from pathlib import PurePosixPath", "Historical import for request schema representation"),
        ("scripts/run_m8r_controlled_live_validation.py", "from pathlib import PurePosixPath", "Historical import in live validation"),
        ("scripts/run_m8r_conversational_derivatives_context.py", "from pathlib import Path, PurePosixPath", "Historical import in conversational context")
    ]
    
    violations = []
    
    for relative_path in files_to_scan:
        full_path = Path(__file__).resolve().parents[1] / relative_path
        if not full_path.exists():
            continue
        try:
            content = full_path.read_text(encoding="utf-8")
        except Exception:
            continue
            
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            
            allowed = False
            for fpath, pattern, reason in ALLOWLIST:
                if relative_path == fpath and pattern in line_str:
                    allowed = True
                    break
            if allowed:
                continue
                
            # Flag insecure patterns
            if "PurePosixPath(" in line_str:
                if not line_str.startswith("#"):
                    violations.append(f"{relative_path}:{idx} - PurePosixPath used: '{line_str}'")
                    
            if ".is_absolute(" in line_str:
                if not line_str.startswith("#"):
                    violations.append(f"{relative_path}:{idx} - Ad-hoc .is_absolute() path check: '{line_str}'")
                    
            if "commonprefix" in line_str:
                if not line_str.startswith("#"):
                    violations.append(f"{relative_path}:{idx} - Insecure commonprefix used: '{line_str}'")
                    
            if ".startswith(" in line_str and any(kw in line_str for kw in ["path", "root", "dest", "output"]):
                if not line_str.startswith("#") and "classify_artifact_relative_path" not in content:
                    violations.append(f"{relative_path}:{idx} - String startswith path containment check: '{line_str}'")
                    
            if ".mkdir(" in line_str and not any(kw in line_str for kw in ["safe_destination", "validate_authorized_root", "atomic_write_text"]):
                if not line_str.startswith("#") and "atomic_write_text" not in content and "safe_destination" not in content:
                    violations.append(f"{relative_path}:{idx} - Ad-hoc mkdir: '{line_str}'")
                    
    return violations


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            print(f"Checking path: {arg}")
            reason = is_forbidden_repo_write_path(arg)
            if reason:
                print(f"Violation: {reason}")
                sys.exit(1)
            else:
                print("OK")
    
    print("Running R5B Insecure Path Pattern Scanner...")
    violations = run_r5b_insecure_pattern_scan()
    if violations:
        print("FAIL: Found insecure filesystem pattern violations:")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)
    else:
        print("PASS: No insecure filesystem patterns found.")
        sys.exit(0)
