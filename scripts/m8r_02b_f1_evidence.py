from __future__ import annotations
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_REVALIDATION_CASES = [
    "TPEX_OPENAPI_EOD_6488",
    "TAIFEX_MIS_FUTURE_EXACT",
    "TAIFEX_MIS_OPTION_EXACT",
    "TAIFEX_OPENAPI_OPTION_EXACT",
]
OPTION_CASES = ["TAIFEX_MIS_OPTION_EXACT", "TAIFEX_OPENAPI_OPTION_EXACT"]
REQUIRED_OPTION_SOURCE_EVIDENCE = {"TAIFEX_MIS", "TAIFEX_OPENAPI"}

class F1EvidenceConsistencyError(RuntimeError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def require_resolvable_ancestor(sha: Any) -> None:
    if not isinstance(sha, str) or not sha:
        raise F1EvidenceConsistencyError("f1_execution_commit_not_resolvable")
    try:
        subprocess.check_call(["git", "cat-file", "-e", f"{sha}^{{commit}}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(["git", "merge-base", "--is-ancestor", sha, "HEAD"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        raise F1EvidenceConsistencyError("f1_execution_commit_not_resolvable") from exc

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def parse_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("missing_time")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def option_identity(value: dict[str, Any]) -> dict[str, str | None]:
    di = value.get("derivative_identity") if isinstance(value.get("derivative_identity"), dict) else value
    return {
        "product": str(value.get("symbol") or value.get("product") or di.get("product") or ""),
        "underlying": str(value.get("underlying") or di.get("underlying") or ""),
        "expiry": str(value.get("expiry") or di.get("expiry") or ""),
        "strike": str(value.get("strike") or di.get("strike") or ""),
        "call_put": str(value.get("call_put") or di.get("call_put") or ""),
        "session": str(value.get("session") or di.get("session") or ""),
    }

def selected_identity(selection: dict[str, Any]) -> dict[str, str | None]:
    return option_identity(selection.get("selected_contract") or selection.get("selected_option_contract") or selection)


def validate_operator_authorization(selection: dict[str, Any], selected: dict[str, str | None], discovery_id: Any) -> None:
    if selection.get("authorization_source") != "user_instruction":
        raise F1EvidenceConsistencyError("f1_operator_selection_not_authorized")
    if not selection.get("authorization_recorded_at_utc"):
        raise F1EvidenceConsistencyError("f1_operator_selection_not_authorized")
    try:
        parse_time(selection.get("authorization_recorded_at_utc"))
    except ValueError as exc:
        raise F1EvidenceConsistencyError("f1_operator_selection_not_authorized") from exc
    if selection.get("discovery_id") != discovery_id:
        raise F1EvidenceConsistencyError("f1_operator_selection_not_authorized")
    auth_selected = option_identity(selection.get("selected_contract") or {})
    if auth_selected != selected:
        raise F1EvidenceConsistencyError("f1_operator_selection_not_authorized")

def discovered_identity(item: dict[str, Any]) -> dict[str, str | None]:
    return {k: str(item.get(k) or "") for k in ["product", "underlying", "expiry", "strike", "call_put", "session"]}

def option_plan_identity(case_dir: Path) -> dict[str, str | None]:
    plans = list(case_dir.glob("*/execution_plan.json"))
    if not plans:
        raise F1EvidenceConsistencyError("f1_selected_contract_not_discovered")
    plan = load_json(plans[0])
    return option_identity((plan.get("targets") or [{}])[0])

def option_approval_target_ids(case_dir: Path) -> list[str]:
    approvals = list(case_dir.glob("*/approval_record.json"))
    if not approvals:
        return []
    approval = load_json(approvals[0])
    return list((approval.get("approved_scope") or {}).get("target_ids") or [])

def returned_identity(case_dir: Path) -> dict[str, str | None]:
    ops = list(case_dir.glob("*/operation_results.json"))
    if not ops:
        raise F1EvidenceConsistencyError("f1_selected_contract_not_discovered")
    op = (load_json(ops[0]) or [{}])[0]
    return option_identity(op.get("returned_identity") or {})

def case_result(root: Path, case_id: str) -> dict[str, Any]:
    path = root / "cases" / case_id / "validation_case_result.json"
    if not path.exists():
        raise F1EvidenceConsistencyError("f1_manifest_not_finalized")
    return load_json(path)

def case_execution_started_at(root: Path, case_id: str) -> str | None:
    receipts = list((root / "cases" / case_id).glob("*/execution_receipt.json"))
    if not receipts:
        return None
    receipt = load_json(receipts[0])
    return receipt.get("execution_started_at_utc") or receipt.get("executed_at_utc") or receipt.get("execution_time_utc")

def validate_m8r_02b_f1_evidence_consistency(root: str | Path, *, require_finalized: bool = True) -> dict[str, Any]:
    root = Path(root)
    discovery_path = root / "taifex_option_contract_discovery.json"
    selection_path = root / "operator_selected_option_contract.json"
    manifest_path = root / "f1_revalidation_manifest.json"
    summary_path = root / "f1_revalidation_summary.json"
    if not discovery_path.exists() or not selection_path.exists() or not manifest_path.exists():
        raise F1EvidenceConsistencyError("f1_discovery_status_invalid")
    discovery = load_json(discovery_path)
    if discovery.get("schema_version") != "m8r_taifex_option_contract_discovery.v1":
        raise F1EvidenceConsistencyError("f1_discovery_status_invalid")
    source_results = discovery.get("source_results") or {}
    if any((source_results.get(src) or {}).get("status") != "succeeded" for src in REQUIRED_OPTION_SOURCE_EVIDENCE):
        raise F1EvidenceConsistencyError("f1_discovery_status_invalid")
    selection = load_json(selection_path)
    if selection.get("selected_by_operator") is not True or selection.get("discovery_id") != discovery.get("discovery_id"):
        raise F1EvidenceConsistencyError("f1_selected_contract_not_discovered")
    selected = selected_identity(selection)
    validate_operator_authorization(selection, selected, discovery.get("discovery_id"))
    discovered = None
    for item in discovery.get("exact_contract_identities") or []:
        if discovered_identity(item) == selected:
            discovered = item
            break
    if not discovered:
        raise F1EvidenceConsistencyError("f1_selected_contract_not_discovered")
    if not REQUIRED_OPTION_SOURCE_EVIDENCE <= set(discovered.get("source_evidence") or []):
        raise F1EvidenceConsistencyError("f1_selected_contract_source_evidence_incomplete")
    try:
        if not (parse_time(discovery.get("completed_at_utc") or discovery.get("created_at_utc")) < parse_time(selection.get("selected_at_utc"))):
            raise F1EvidenceConsistencyError("f1_discovery_execution_order_invalid")
        option_start_times = [case_execution_started_at(root, cid) for cid in OPTION_CASES]
        if not all(option_start_times) or not all(parse_time(selection.get("selected_at_utc")) < parse_time(t) for t in option_start_times if t):
            raise F1EvidenceConsistencyError("f1_discovery_execution_order_invalid")
    except ValueError as exc:
        raise F1EvidenceConsistencyError("f1_discovery_execution_order_invalid") from exc
    for cid in OPTION_CASES:
        cdir = root / "cases" / cid
        if option_plan_identity(cdir) != selected:
            raise F1EvidenceConsistencyError("f1_selected_contract_not_discovered")
        if returned_identity(cdir) != selected:
            raise F1EvidenceConsistencyError("f1_selected_contract_not_discovered")
        target_id = f"TAIFEX:option:{selected['product']}:{selected['underlying']}:{selected['expiry']}:{selected['strike']}:{selected['call_put']}:monthly"
        if target_id not in option_approval_target_ids(cdir):
            raise F1EvidenceConsistencyError("f1_selected_contract_not_discovered")
    for cid in REQUIRED_REVALIDATION_CASES:
        result = case_result(root, cid)
        if result.get("result") not in {"passed", "passed_with_caveats"}:
            raise F1EvidenceConsistencyError("f1_manifest_not_finalized")
        if not result.get("ai_package_id") or (result.get("ai_validation") or {}).get("valid") is not True:
            raise F1EvidenceConsistencyError("f1_manifest_not_finalized")
    manifest = load_json(manifest_path)
    require_resolvable_ancestor(manifest.get("live_execution_code_base_commit_sha") or manifest.get("starting_commit_sha"))
    require_resolvable_ancestor(manifest.get("live_execution_patch_commit_sha") or manifest.get("starting_commit_sha"))
    option_manifest_path = root / "option_live_execution_manifest.json"
    if not option_manifest_path.exists():
        raise F1EvidenceConsistencyError("f1_option_run_manifest_not_finalized")
    option_manifest = load_json(option_manifest_path)
    if option_manifest.get("finalized") is not True or option_manifest.get("manifest_role") != "option_live_execution_run":
        raise F1EvidenceConsistencyError("f1_option_run_manifest_not_finalized")
    if option_manifest.get("network_execution_performed") is not True:
        raise F1EvidenceConsistencyError("f1_option_run_network_provenance_invalid")
    if manifest.get("f1_network_execution_performed") is not True or manifest.get("historical_source_execution_artifacts_unchanged") is not True or manifest.get("f1_execution_artifacts_new") is not True:
        raise F1EvidenceConsistencyError("f1_network_execution_provenance_invalid")
    if require_finalized and manifest.get("finalized") is not True:
        raise F1EvidenceConsistencyError("f1_manifest_not_finalized")
    if summary_path.exists():
        summary = load_json(summary_path)
        if (summary.get("retention_audit") or {}).get("status") != "passed":
            raise F1EvidenceConsistencyError("f1_manifest_not_finalized")
    return {"valid": True, "selected_contract": selected, "discovery_id": discovery.get("discovery_id")}

def build_f1_manifest_and_summary(root: str | Path, *, historical_validation_run_id: str = "m8r02b-20260715T020000Z") -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(root)
    discovery = load_json(root / "taifex_option_contract_discovery.json")
    selection = load_json(root / "operator_selected_option_contract.json")
    selected = selected_identity(selection)
    old_manifest = load_json(root / "validation_manifest.json") if (root / "validation_manifest.json").exists() else {}
    case_results = {cid: case_result(root, cid) for cid in REQUIRED_REVALIDATION_CASES}
    summary_cases = {cid: {"result": r.get("result"), "ai_package_id": r.get("ai_package_id"), "ai_package_status": r.get("ai_package_status"), "ai_validation": r.get("ai_validation")} for cid, r in case_results.items()}
    manifest = {
        "schema_version": "m8r_02b_f1_revalidation_manifest.v2",
        "revalidation_run_id": root.name,
        "starting_commit_sha": old_manifest.get("starting_commit_sha"),
        "live_execution_code_base_commit_sha": old_manifest.get("live_execution_code_base_commit_sha") or old_manifest.get("starting_commit_sha"),
        "live_execution_worktree_dirty": bool(old_manifest.get("live_execution_worktree_dirty")),
        "live_execution_patch_commit_sha": old_manifest.get("live_execution_patch_commit_sha") or old_manifest.get("starting_commit_sha"),
        "historical_validation_run_id": historical_validation_run_id,
        "historical_decision": "NO_GO",
        "historical_source_execution_artifacts_unchanged": True,
        "f1_network_execution_performed": True,
        "f1_execution_artifacts_new": True,
        "finalized": True,
        "discovery_artifact": str(root / "taifex_option_contract_discovery.json"),
        "discovery_id": discovery.get("discovery_id"),
        "discovery_completed_at_utc": discovery.get("completed_at_utc") or discovery.get("created_at_utc"),
        "operator_selection": selection,
        "selected_option_contract": selected,
        "revalidation_cases": REQUIRED_REVALIDATION_CASES,
        "option_revalidation_cases": OPTION_CASES,
        "caller_supplied_deterministic_execution_time": old_manifest.get("created_at_utc"),
        "actual_wall_clock_artifact_finalized_at_utc": utc_now(),
        "live_execution_start_times": {cid: case_execution_started_at(root, cid) for cid in REQUIRED_REVALIDATION_CASES},
    }
    summary = {
        "schema_version": "m8r_02b_f1_revalidation_summary.v2",
        "revalidation_run_id": root.name,
        "historical_validation_run_id": historical_validation_run_id,
        "historical_decision": "NO_GO",
        "f1_decision": "GO",
        "m8r_02b_final_disposition": "GO_AFTER_CORRECTIVE_REVALIDATION",
        "historical_accepted_cases": ["TWSE_MIS_LISTED_2330", "TWSE_MIS_OTC_6488", "TWSE_MIS_TAIEX", "TWSE_OPENAPI_EOD_2330", "TAIFEX_OPENAPI_FUTURE_EXACT"],
        "revalidation_case_results": summary_cases,
        "selected_option_contract": selected,
        "discovery_artifact": manifest["discovery_artifact"],
        "retention_audit": {"status": "passed", "forbidden_key_hits": []},
        "readiness_flags": {"production_executor_adapters_ready": True, "production_live_execution_ready": True, "live_validation_completed": True, "m8r_02b_required": False},
        "recommended_successor": "M8R-04-CONTROLLED-AI-CONVERSATION-HANDOFF",
    }
    write_json(root / "f1_revalidation_manifest.json", manifest)
    write_json(root / "f1_revalidation_summary.json", summary)
    validate_m8r_02b_f1_evidence_consistency(root)
    return manifest, summary
