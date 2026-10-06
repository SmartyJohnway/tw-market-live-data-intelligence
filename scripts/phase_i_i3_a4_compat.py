"""Compatibility checks for historical gates after the additive I3-A4 candidate.

This projects only the explicitly authorized dormant I3 candidate additions out
of shared production/public JSON authorities before comparing an older gate's
baseline. It never changes the files being checked or activates runtime routes.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPABILITY = "cash_institutional_flow_context"
EVIDENCE_V2 = "cash_institutional_flow_context_evidence.v2"
I3_EXECUTOR = "phase_i_i3_cash_institutional_flow_context_executor"
CANDIDATE_BASELINE = "5c26e7b541bdb6c0d70a39c1e0eab8e129823373"
_DROP = object()


def _normalize_current_h1_v2_addition(value):
    """Project the authorized H1 v2 additive Result branch back to historical H1 v1.

    Older Phase I containment gates compare their original V3 snapshot. The
    current additive H1 acceptance is independently hash-pinned by the Phase H
    V3 validator and dated Phase J authority, so those historical comparisons
    retain their v1 baseline without treating the authorized sibling as I3 or
    rewriting any historical record.
    """
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key == "trading_status_context" and isinstance(item, dict) and isinstance(item.get("oneOf"), list):
                branches = item["oneOf"]
                versions = {
                    branch.get("properties", {}).get("schema_version", {}).get("const")
                    for branch in branches if isinstance(branch, dict)
                }
                if versions == {"trading_status_context_evidence.v1", "trading_status_context_evidence.v2"}:
                    v1 = [branch for branch in branches
                          if branch.get("properties", {}).get("schema_version", {}).get("const")
                          == "trading_status_context_evidence.v1"]
                    if len(v1) == 1:
                        item = v1[0]
            result[key] = _normalize_current_h1_v2_addition(item)
        return result
    if isinstance(value, list):
        return [_normalize_current_h1_v2_addition(item) for item in value]
    return value


def _without_i3(value):
    if value == CAPABILITY or value == EVIDENCE_V2:
        return _DROP
    if isinstance(value, dict):
        if value.get("capability_id") == CAPABILITY or value.get("executor_id") == I3_EXECUTOR \
                or value.get("surface_id") == I3_EXECUTOR:
            return _DROP
        properties = value.get("properties", {})
        if properties.get("capability_id", {}).get("const") == CAPABILITY:
            return _DROP
        if properties.get("schema_version", {}).get("const") == EVIDENCE_V2:
            return _DROP
        result = {}
        for key, item in value.items():
            if key == CAPABILITY or key == "cash_flow":
                continue
            projected = _without_i3(item)
            if projected is not _DROP:
                result[key] = projected
        return result
    if isinstance(value, list):
        return [projected for item in value
                if (projected := _without_i3(item)) is not _DROP]
    return value


def assert_non_i3_authority_unchanged(relative: str, baseline: str = CANDIDATE_BASELINE) -> None:
    """Require current shared JSON authority to equal baseline sans I3 additions."""
    if relative == "scripts/m8r_06_03_production_adapter.py":
        current_text = (ROOT / relative).read_text(encoding="utf-8")
        baseline_text = subprocess.check_output(
            ["git", "show", f"{baseline}:{relative}"], cwd=ROOT
        ).decode("utf-8")
        import_block = (
            "    from server.services.phase_i_i3_cash_institutional_flow_production_candidate import (\n"
            "        build_i3_production_candidate_registrations,\n"
            "    )\n"
        )
        registration_block = (
            "    registrations.extend(build_i3_production_candidate_registrations(\n"
            "        **({} if i3_acquire is None else {\"acquire\": i3_acquire})\n"
            "    ))\n"
        )
        current_text = current_text.replace(import_block, "", 1).replace(registration_block, "", 1)
        # The optional I3 injection seam is limited to the registry factory
        # signature; normalize that single signature back to its baseline form.
        current_text = current_text.replace(
            "def build_production_runtime_adapter_registry(*, i3_acquire: Any | None = None) -> RuntimeAdapterRegistry:",
            "def build_production_runtime_adapter_registry() -> RuntimeAdapterRegistry:", 1,
        )
        if current_text != baseline_text:
            raise AssertionError(f"non_i3_production_adapter_drift:{relative}")
        return
    current = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    old = json.loads(subprocess.check_output(
        ["git", "show", f"{baseline}:{relative}"], cwd=ROOT
    ).decode("utf-8"))
    normalized = _normalize_current_h1_v2_addition(_without_i3(current))
    if normalized != old:
        raise AssertionError(f"non_i3_production_authority_drift:{relative}")


def assert_candidate_is_dormant(catalog_relative: str, routing_relative: str) -> None:
    """Validate historical dormancy or delegate to current activation proof.

    The name is retained for historical callers; after the additive activation
    ledger exists, current runtime truth is checked by the dedicated validator.
    """
    activation = ROOT / "docs/governance/phase_i/PHASE_I_I3_A4_BOUNDED_PRODUCTION_ACTIVATION_2026-10-05.json"
    if activation.exists():
        from scripts.validate_phase_i_i3_a4_activation import validate
        validate()
        return
    catalog = json.loads((ROOT / catalog_relative).read_text(encoding="utf-8"))
    routing = json.loads((ROOT / routing_relative).read_text(encoding="utf-8"))
    capability = next((item for item in catalog["data_need_capabilities"]
                       if item.get("capability_id") == CAPABILITY), None)
    route = next((item for item in routing["routes"]
                  if item.get("capability_id") == CAPABILITY), None)
    if not (capability and capability.get("support_status") == "contract_supported"
            and route and route.get("routing_status") == "plan_only"
            and route.get("runtime_executable") is False
            and route.get("selected_executor_id") is None):
        raise AssertionError("i3_candidate_not_dormant")
