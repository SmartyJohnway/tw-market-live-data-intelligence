"""Network-free inspection helpers for the J-B04-A6-P1 authority gate."""

from __future__ import annotations

import json
import ast
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
P0_PATH = REPO_ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_P0_INTEGRATED_ACCEPTANCE_PREFLIGHT_2026-10-09.json"
H3_OWNER_PATH = REPO_ROOT / "docs/governance/phase_h/PHASE_H_H3_TWSE_CONTROLLED_USE_OWNER_DECISION_2026-09-24.json"
MATERIALIZER_PATH = REPO_ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py"
PROBE_PATH = REPO_ROOT / "skills/tw-security-master-classifier/scripts/probe_sources.py"
MANIFEST_PATH = REPO_ROOT / "skills/tw-security-master-classifier/references/source-manifest.json"

EXPECTED_LOGICAL_PROBES = [
    {
        "source_id": "twse_isin_mode2_zh",
        "initial_url": "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2",
        "allowed_host": "isin.twse.com.tw",
        "source_contract_identifier": None,
        "parser": "isin_parser.parse_html(lane=zh, mode=2)",
        "qualification_role": "TWSE listed mixed security identity input",
    },
    {
        "source_id": "twse_isin_mode4_zh",
        "initial_url": "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4",
        "allowed_host": "isin.twse.com.tw",
        "source_contract_identifier": None,
        "parser": "isin_parser.parse_html(lane=zh, mode=4)",
        "qualification_role": "TPEx listed mixed security identity input",
    },
    {
        "source_id": "twse_delisted",
        "initial_url": "https://www.twse.com.tw/company/suspendListingCsvAndHtml?lang=zh&type=html",
        "allowed_host": "www.twse.com.tw",
        "source_contract_identifier": None,
        "parser": "parse_twse_delisted",
        "qualification_role": "TWSE delisted lifecycle evidence",
    },
    {
        "source_id": "tpex_delisted",
        "initial_url": "https://www.tpex.org.tw/www/zh-tw/company/deListed",
        "allowed_host": "www.tpex.org.tw",
        "source_contract_identifier": None,
        "parser": "parse_tpex_delisted",
        "qualification_role": "TPEx delisted lifecycle evidence",
    },
    {
        "source_id": "twse_etn_expired",
        "initial_url": "https://www.twse.com.tw/rwd/zh/ETN/expireEnd?response=json",
        "allowed_host": "www.twse.com.tw",
        "source_contract_identifier": None,
        "parser": "parse_twse_etn_expired_json",
        "qualification_role": "TWSE expired ETN lifecycle evidence",
    },
]

BOOTSTRAP_AUTHORIZATION_TEMPLATE: dict[str, Any] = {
    "template_type": "FUTURE_OWNER_AUTHORIZATION_METADATA_ONLY",
    "authorization_status": "NOT_AUTHORIZED",
    "authorized_head_sha": "<EXACT_FUTURE_REVIEWED_HEAD>",
    "authorized_tree_sha": "<EXACT_FUTURE_REVIEWED_TREE>",
    "logical_source_probes": [
        "TWSE listed ISIN",
        "TPEx listed ISIN",
        "TWSE delisted lifecycle",
        "TPEx delisted lifecycle",
        "TWSE ETN expiry lifecycle",
    ],
    "maximum_redirects_followed_per_probe": 1,
    "maximum_http_dispatches_per_probe": 2,
    "bootstrap_http_dispatch_hard_ceiling": 10,
    "retry_count": 0,
    "redirect_policy": "HTTPS and allowlisted host only",
    "prohibited": [
        "H3 live",
        "H2 live",
        "A6 execution",
        "H2 activation",
        "J-B04 closure",
        "Phase J start",
    ],
    "stop_conditions": [
        "unexpected source inventory",
        "redirect limit exceeded",
        "redirect host violation",
        "dispatch budget exhaustion",
        "source contract mismatch",
        "qualification-invalidating schema drift",
        "qualification failure",
        "identity conflict",
        "release rejection",
        "activation failure",
    ],
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_object:{path.name}")
    return value


def h3_automation_authority(owner_record: dict[str, Any]) -> dict[str, Any]:
    route = owner_record.get("selected_route", {})
    owner = owner_record.get("owner_decision", {})
    profile = owner_record.get("controlled_operating_profile", {})
    permission = route.get("provider_automation_permission")
    product_approved = route.get("owner_product_authorization") == "APPROVED_CONTROLLED_LOCAL_FIRST_USE"
    exact_owner_decision = owner.get("decision") == (
        "Use the official TWSE STOCK_DAY public web source as the default bounded TWSE recent-performance source "
        "for the owner's controlled local-first installation despite the known provider-terms conflict."
    )
    bounded = (
        profile.get("exact_target_only") is True
        and profile.get("request_time_only") is True
        and profile.get("explicit_authorization_required") is True
        and profile.get("execute_once") is True
        and profile.get("retry_storm") is False
        and profile.get("scheduler") is False
        and profile.get("polling") is False
        and profile.get("anti_bot_bypass") is False
        and profile.get("captcha_bypass") is False
        and profile.get("rate_limit_evasion") is False
    )
    accepted = (
        owner_record.get("status") == "OWNER_ACCEPTED_CONTROLLED_USE"
        and product_approved
        and exact_owner_decision
        and bounded
        and permission == "NOT_ESTABLISHED_TERMS_CONFLICTED"
    )
    return {
        "disposition": "J_B04_A6_H3_AUTOMATION_AUTHORITY_ACCEPTED" if accepted else "J_B04_A6_H3_AUTOMATION_AUTHORITY_INSUFFICIENT_EVIDENCE",
        "source_authenticity": "official TWSE STOCK_DAY public web source",
        "transport_accessibility": "technically demonstrated by cited bounded TWSE acceptance evidence; not a permission determination",
        "provider_automation_permission": permission,
        "owner_product_authorization": "APPROVED_CONTROLLED_LOCAL_FIRST_USE" if product_approved else "NOT_ESTABLISHED",
        "usage_permission": "Owner-authorized for the exact bounded local-first product profile; provider permission remains terms-conflicted",
        "redistribution_permission": "not established by this authority; no redistribution claim",
        "authority_path": "docs/governance/phase_h/PHASE_H_H3_TWSE_CONTROLLED_USE_OWNER_DECISION_2026-09-24.json",
        "terms_authority_path": "docs/governance/phase_h/Phase_H_H3_Owner_Official_Web_Automation_Product_Inclusion_2026-09-24.md",
        "provider_approval_claimed": False,
    }


def post_bootstrap_identity_acceptance(snapshot: dict[str, Any]) -> bool:
    """Check a sanitized production-loader/identity snapshot; performs no lookup."""
    return (
        snapshot.get("manager_status") == "ACTIVE"
        and snapshot.get("release_state") == "QUALIFIED"
        and snapshot.get("manifest_hash_valid") is True
        and snapshot.get("production_loader") == "PASS"
        and snapshot.get("resolution_status") == "resolved"
        and snapshot.get("reason") == "exact_listing_id"
        and snapshot.get("canonical_target_id") == "TWSE:2330"
        and snapshot.get("market") == "TWSE"
        and snapshot.get("security_code") == "2330"
        and snapshot.get("instrument_family") == "company_share"
        and snapshot.get("instrument_type") == "common_share"
        and snapshot.get("execution_eligibility") == "allowed"
        and isinstance(snapshot.get("release_id"), str)
        and bool(snapshot.get("release_id"))
        and isinstance(snapshot.get("manifest_sha256"), str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", snapshot["manifest_sha256"]))
        and isinstance(snapshot.get("release_index_sha256"), str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", snapshot["release_index_sha256"]))
        and isinstance(snapshot.get("active_selector"), str)
        and isinstance(snapshot.get("isin"), str)
        and bool(snapshot.get("isin"))
    )


def classify_bootstrap_dispatch() -> str:
    bounds = inspect_redirect_runtime_bounds()
    materializer = MATERIALIZER_PATH.read_text(encoding="utf-8")
    probe_source = PROBE_PATH.read_text(encoding="utf-8")
    explicit_project_limits = (
        "BOOTSTRAP_MAX_REDIRECTS_PER_PROBE = 1" in materializer
        and "BOOTSTRAP_MAX_DISPATCHES_PER_PROBE = 1 + BOOTSTRAP_MAX_REDIRECTS_PER_PROBE" in materializer
        and "BOOTSTRAP_MAX_TOTAL_DISPATCHES = 10" in materializer
        and materializer.count("dispatch_budget=dispatch_budget") == 2
        and "dispatch_budget.reserve_before_dispatch()" in probe_source
        and "self.redirect_count >= self.max_followed_redirects" in probe_source
    )
    return "PROJECT_OWNED_BOUNDED" if bounds["is_subclass"] and explicit_project_limits else "NOT_PROVEN"


def inspect_redirect_runtime_bounds() -> dict[str, Any]:
    """Load the real probe module without acquiring sources and read effective attrs."""
    script_path = str(PROBE_PATH.parent)
    sys.path.insert(0, script_path)
    try:
        spec = importlib.util.spec_from_file_location("a6p1_probe_sources_runtime", PROBE_PATH)
        if spec is None or spec.loader is None:
            raise ImportError("probe_sources_runtime_loader_unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(script_path)
        except ValueError:
            pass
    handler = module.SafeRedirectHandler([])
    parent = module.urllib.request.HTTPRedirectHandler
    return {
        "is_subclass": issubclass(module.SafeRedirectHandler, parent),
        "max_repeats": handler.max_repeats,
        "max_redirections": handler.max_redirections,
        "python_version": sys.version.split()[0],
    }


def bootstrap_authorization_template() -> dict[str, Any] | None:
    if classify_bootstrap_dispatch() != "PROJECT_OWNED_BOUNDED":
        return None
    return BOOTSTRAP_AUTHORIZATION_TEMPLATE


def source_inventory() -> list[dict[str, Any]]:
    manifest = load_json(MANIFEST_PATH)
    materializer = ast.parse(MATERIALIZER_PATH.read_text(encoding="utf-8"))
    values: dict[str, Any] = {}
    for node in materializer.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
    modes = values.get("IDENTITY_MODES")
    identity_url = values.get("TWSE_ISIN_ZH")
    lifecycle = values.get("lifecycle_sources")
    # lifecycle_sources is assigned inside main(), so extract its literal from that scope.
    if lifecycle is None:
        def resolve(node: ast.AST) -> Any:
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.Name):
                return values[node.id]
            if isinstance(node, (ast.Tuple, ast.List)):
                converted = [resolve(item) for item in node.elts]
                return tuple(converted) if isinstance(node, ast.Tuple) else converted
            raise ValueError("unsupported_materializer_literal")

        for node in ast.walk(materializer):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "lifecycle_sources":
                lifecycle = resolve(node.value)
                break
    actual = [
        {"source_id": f"twse_isin_mode{mode}_zh", "initial_url": identity_url.format(mode=mode)}
        for mode in (modes or [])
    ]
    actual += [
        {"source_id": source_id, "initial_url": url}
        for source_id, url, _parser in (lifecycle or [])
    ]
    expected = [{"source_id": p["source_id"], "initial_url": p["initial_url"]} for p in EXPECTED_LOGICAL_PROBES]
    if actual != expected:
        raise ValueError("materializer_source_inventory_drift")
    allowed = set(manifest.get("allowed_hosts", []))
    return [
        {
            **probe,
            "allowed_host_present": probe["allowed_host"] in allowed,
            "http_method": "POST" if probe["source_id"] == "tpex_delisted" else "GET",
            "redirect_policy": "production bootstrap follows at most one redirect; HTTPS and allowlisted host only; credentials prohibited",
            "maximum_redirects_followed_per_probe": 1,
            "maximum_http_dispatches_per_probe": 2,
            "bootstrap_http_dispatch_hard_ceiling": 10,
            "redirect_behavior": "project-owned redirect limit is checked before target dispatch; shared global slot is reserved before redirect request is returned",
            "timeout_seconds": 20,
            "response_size_bound_bytes": 20 * 1024 * 1024,
            "raw_acquisition_retention": "successful response bytes saved to ignored input-bundle raw_payloads; HTTP error stores only hash of up to 256 KiB read",
            "source_contract_note": (
                "Qualified single-response TPEx date=ALL form POST; parser/manifest contract requires row count == totalCount."
                if probe["source_id"] == "tpex_delisted"
                else "No stable source_contract_id is declared for these materializer probes; parser/manifest adapter metadata is the effective contract."
            ),
        }
        for probe in EXPECTED_LOGICAL_PROBES
    ]


def h2_activation_current_state() -> dict[str, Any]:
    catalog = load_json(REPO_ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    routing = load_json(REPO_ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json")
    catalog_items = catalog.get("data_need_capabilities", [])
    capability = next((item for item in catalog_items if item.get("capability_id") == "corporate_action_context"), None)
    routes = routing.get("routes", [])
    route = next((item for item in routes if item.get("capability_id") == "corporate_action_context"), None)
    return {"catalog": capability, "routing": route}
