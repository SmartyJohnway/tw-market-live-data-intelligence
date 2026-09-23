from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "config/test_governance_authority.json"
PROFILES = ROOT / "config/test_execution_profiles.json"


def profile_name_for_role(role: str) -> str:
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    mapping = {
        "current": authority["current_merge_authority"]["profile"],
        "broad_current": authority["lifecycle_regression"]["broad_current_profile"],
        "historical": authority["lifecycle_regression"]["historical_profile"],
        "release": authority["lifecycle_regression"]["release_profile"],
        "mixed_historical": authority["lifecycle_regression"]["mixed_historical_profile"],
        "rollback": authority["rollback"]["diagnostic_profile"],
    }
    try:
        return mapping[role]
    except KeyError as exc:
        raise ValueError(f"Unknown test-governance role: {role}") from exc


def profile_paths_for_role(role: str) -> set[str]:
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))["profiles"]
    name = profile_name_for_role(role)
    return set(profiles[name].get("pytest_paths", []))
