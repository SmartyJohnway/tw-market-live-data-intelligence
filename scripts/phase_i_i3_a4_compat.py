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
A26_COMPOSITE_EXECUTOR = "phase_h_h1_tpex_composite_executor"
A26_H1_CAPABILITY = "trading_status_context"
A26_ADDED_SOURCES = {"H1-TPEX-DISPOSITION-OPENAPI", "H1-TPEX-CHANGED-TRADING-OPENAPI"}
A3_H2_CAPABILITY = "corporate_action_context"
A3_H2_EXECUTOR = "phase_h_h2_twse_exright_pre_executor"
_DROP = object()


def _normalize_current_h1_v2_addition(value):
    """Project authorized current H1/Composite additions to historical H1 v1.

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
                    and branch.get("properties", {}).get("schema_version", {}).get("const") is not None
                }
                composite_branch = {"$ref": "#/definitions/trading_status_context_composite"}
                if (versions == {"trading_status_context_evidence.v1", "trading_status_context_evidence.v2"}
                        and branches.count(composite_branch) == 1 and len(branches) == 3):
                    v1 = [branch for branch in branches
                          if branch.get("properties", {}).get("schema_version", {}).get("const")
                          == "trading_status_context_evidence.v1"]
                    if len(v1) == 1:
                        item = v1[0]
            result[key] = _normalize_current_h1_v2_addition(item)
        # The current Result V3 schema hash is independently pinned by the
        # Phase H current-contract validator. These exact dated Phase J
        # composite definitions are therefore projected out only when
        # comparing an older Phase I historical snapshot.
        definitions = result.get("definitions")
        if isinstance(definitions, dict):
            for key in (
                "trading_status_context_composite_component",
                "trading_status_context_composite_coverage",
                "trading_status_context_composite",
            ):
                definitions.pop(key, None)
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


def validate_current_a26_h1_authority() -> None:
    """Require the exact bounded Stage-B H1 state before historical projection."""
    catalog_path = ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"
    routing_path = ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    routing = json.loads(routing_path.read_text(encoding="utf-8"))
    cap = next(x for x in catalog["data_need_capabilities"] if x.get("capability_id") == A26_H1_CAPABILITY)
    route = next(x for x in routing["routes"] if x.get("capability_id") == A26_H1_CAPABILITY)
    assert cap["runtime_executable"] is True and cap["phase_h_activation_state"] == "selected_route_active"
    assert route["runtime_executable"] is True and route["routing_status"] == "resolved"
    assert route["selected_executor_id"] == A26_COMPOSITE_EXECUTOR
    assert route["output_evidence_contract"] == "trading_status_context_composite.v1"
    authority = routing["phase_h_source_authority"]
    active = {x["source_id"] for x in authority["records"]
              if x.get("activation_state") == "active" and x.get("runtime_executable") is True}
    assert authority["active_source_count"] == 4
    assert active == {
        "H1-TPEX-ATTENTION-OPENAPI", "H1-TPEX-DISPOSITION-OPENAPI",
        "H1-TPEX-CHANGED-TRADING-OPENAPI", "H3-TWSE-DEFAULT-BOUNDED",
    }


def validate_current_a3_h2_candidate() -> None:
    """Require the exact A3 plan-only candidate before historical projection."""
    routing = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "config/m8r_06_03_executor_registry_metadata.json").read_text(encoding="utf-8"))
    route = next(x for x in routing["routes"] if x.get("capability_id") == A3_H2_CAPABILITY)
    assert route["runtime_executable"] is False
    assert route["routing_status"] == "plan_only"
    assert route["selected_executor_id"] is None
    assert route["candidate_executor_ids"] == [A3_H2_EXECUTOR]
    assert route["network_required"] is True
    assert route["estimated_operation_rule"] == "A3 implementation candidate only; one explicit TWSE TWT48U_ALL GET, retry zero; remains plan-only and inactive until separately accepted"
    candidate = [x for x in registry["executors"] if x.get("executor_id") == A3_H2_EXECUTOR]
    assert len(candidate) == 1
    assert candidate[0]["capability_id"] == A3_H2_CAPABILITY
    assert candidate[0]["expected_evidence_contract"] == "corporate_action_context_evidence.v1"
    assert candidate[0]["network_required"] is True


def project_current_a3_h2_addition(relative: str, current, historical):
    """Project only the accepted inactive H2 candidate from old Phase-I comparisons."""
    if relative not in {
        "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json",
        "config/m8r_06_03_executor_registry_metadata.json",
    }:
        return current
    validate_current_a3_h2_candidate()
    result = json.loads(json.dumps(current))
    if relative.endswith("m8r_05b_capability_to_executor_routing_matrix.v3.json"):
        old_route = next(x for x in historical["routes"] if x.get("capability_id") == A3_H2_CAPABILITY)
        result["routes"] = [
            json.loads(json.dumps(old_route)) if row.get("capability_id") == A3_H2_CAPABILITY else row
            for row in result["routes"]
        ]
    else:
        result["executors"] = [x for x in result["executors"] if x.get("executor_id") != A3_H2_EXECUTOR]
    return result


def project_current_a26_h1_addition(relative: str, current, historical):
    """Remove only the authorized current A2.6 H1 overlay for old comparisons.

    This is a comparison projection; it never writes canonical files. Current
    Stage-B route/source authority is checked before projection so a missing or
    altered A2.6 route cannot be hidden by a historical test.
    """
    if relative not in {
        "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json",
        "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json",
        "config/m8r_06_03_executor_registry_metadata.json",
        "docs/data_capabilities/m8r_05b_existing_orchestrator_disposition.json",
    }:
        return current
    validate_current_a26_h1_authority()
    result = json.loads(json.dumps(current))
    if relative.endswith("unified_market_evidence_capability_catalog.v3.json"):
        field, key = "data_need_capabilities", "capability_id"
        current_rows, old_rows = result[field], historical[field]
        result[field] = [next((json.loads(json.dumps(old)) for old in old_rows if old.get(key) == row.get(key)), row)
                         if row.get(key) == A26_H1_CAPABILITY else row for row in current_rows]
        if isinstance(result.get("phase_h_contract"), dict) and isinstance(historical.get("phase_h_contract"), dict):
            result["phase_h_contract"]["active_phase_h_source_count"] = historical["phase_h_contract"]["active_phase_h_source_count"]
    elif relative.endswith("m8r_05b_capability_to_executor_routing_matrix.v3.json"):
        field, key = "routes", "capability_id"
        old_route = next(x for x in historical[field] if x.get(key) == A26_H1_CAPABILITY)
        result[field] = [json.loads(json.dumps(old_route)) if row.get(key) == A26_H1_CAPABILITY else row
                         for row in result[field]]
        authority = result.get("phase_h_source_authority")
        old_authority = historical.get("phase_h_source_authority")
        if isinstance(authority, dict) and isinstance(old_authority, dict):
            old_records = {x.get("source_id"): x for x in old_authority.get("records", [])}
            authority["records"] = [json.loads(json.dumps(old_records[row["source_id"]]))
                                     if row.get("source_id") in A26_ADDED_SOURCES
                                     and row.get("source_id") in old_records else row
                                     for row in authority.get("records", [])]
            authority["active_source_count"] = old_authority["active_source_count"]
        if "routing_scope" in historical:
            result["routing_scope"] = historical["routing_scope"]
    elif relative.endswith("executor_registry_metadata.json"):
        result["executors"] = [x for x in result["executors"] if x.get("executor_id") != A26_COMPOSITE_EXECUTOR]
    else:
        old_surfaces = {x.get("surface_id"): x for x in historical.get("surfaces", [])}
        result["surfaces"] = [
            json.loads(json.dumps(old_surfaces[row["surface_id"]]))
            if row.get("surface_id") == "phase_h_h1_tpex_attention_executor"
            and row.get("surface_id") in old_surfaces else row
            for row in result["surfaces"]
            if row.get("surface_id") != A26_COMPOSITE_EXECUTOR
        ]
    return result


def strip_a26_production_adapter_addition(text: str) -> str:
    """Project the exact Stage-B dispatch/registration additions from old code comparisons."""
    text = text.replace('PHASE_H_H1_COMPOSITE_EXECUTOR_ID = "phase_h_h1_tpex_composite_executor"\n', "", 1)
    text = text.replace(
        '    if request.get("executor_id") == PHASE_H_H1_COMPOSITE_EXECUTOR_ID:\n'
        '        from server.services.phase_h_h1_tpex_composite import production_composite_adapter\n'
        '        try:\n'
        '            return production_composite_adapter(request, context)\n'
        '        except ValueError as exc:\n'
        '            raise OrchestrationError(str(exc) or "phase_h_composite_execution_failed") from exc\n',
        "", 1)
    text = text.replace('        (PHASE_H_H1_COMPOSITE_EXECUTOR_ID, "trading_status_context", "TPEX"),\n', "", 1)
    text = text.replace('PHASE_H_H1_EXECUTOR_ID, PHASE_H_H1_COMPOSITE_EXECUTOR_ID, PHASE_H_H3_EXECUTOR_ID',
                        'PHASE_H_H1_EXECUTOR_ID, PHASE_H_H3_EXECUTOR_ID', 1)
    return text


def strip_a3_h2_production_adapter_addition(text: str) -> str:
    """Project the A3 inactive H2 adapter registration from old code baselines."""
    text = text.replace(
        "from server.services.phase_h_h2_twse_exright_executor import (\n"
        "    EXECUTOR_ID as PHASE_H_H2_EXECUTOR_ID,\n"
        "    execute_h2_twse_exright_pre,\n"
        ")\n", "", 1,
    )
    text = text.replace('PHASE_H_H2_SOURCE_ID = "H2-TWSE-EXRIGHT-PRE-OPENAPI"\n', "", 1)
    text = text.replace(
        "    if request.get(\"executor_id\") == PHASE_H_H2_EXECUTOR_ID:\n"
        "        return execute_h2_twse_exright_pre(request, context)\n", "", 1,
    )
    text = text.replace('        (PHASE_H_H2_EXECUTOR_ID, "corporate_action_context", "TWSE"),\n', "", 1)
    text = text.replace(
        "{PHASE_H_H1_EXECUTOR_ID, PHASE_H_H1_COMPOSITE_EXECUTOR_ID, PHASE_H_H3_EXECUTOR_ID, PHASE_H_H2_EXECUTOR_ID}",
        "{PHASE_H_H1_EXECUTOR_ID, PHASE_H_H1_COMPOSITE_EXECUTOR_ID, PHASE_H_H3_EXECUTOR_ID}", 1,
    )
    text = text.replace(
        "{PHASE_H_H1_EXECUTOR_ID, PHASE_H_H3_EXECUTOR_ID, PHASE_H_H2_EXECUTOR_ID}",
        "{PHASE_H_H1_EXECUTOR_ID, PHASE_H_H3_EXECUTOR_ID}", 1,
    )
    return text


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
        current_text = strip_a26_production_adapter_addition(current_text)
        current_text = strip_a3_h2_production_adapter_addition(current_text)
        if current_text != baseline_text:
            raise AssertionError(f"non_i3_production_adapter_drift:{relative}")
        return
    current = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    old = json.loads(subprocess.check_output(
        ["git", "show", f"{baseline}:{relative}"], cwd=ROOT
    ).decode("utf-8"))
    normalized = _normalize_current_h1_v2_addition(_without_i3(current))
    normalized = project_current_a26_h1_addition(relative, normalized, old)
    normalized = project_current_a3_h2_addition(relative, normalized, old)
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
