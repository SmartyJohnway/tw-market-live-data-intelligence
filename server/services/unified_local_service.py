"""Thin, deterministic Local Service projections over existing authorities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.m8r_06_03_production_adapter import load_production_executor_metadata


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "docs" / "data_capabilities" / "unified_market_evidence_capability_catalog.v1.json"
ROUTING_PATH = ROOT / "docs" / "data_capabilities" / "m8r_05b_capability_to_executor_routing_matrix.json"
SERVICE_CONTRACT_VERSION = "unified_market_evidence_local_service.v1"


class LocalServiceError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalServiceError("capability_authority_unavailable") from exc
    if not isinstance(value, dict):
        raise LocalServiceError("capability_authority_malformed")
    return value


def _authorities() -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    catalog = _load_json(CATALOG_PATH)
    routing = _load_json(ROUTING_PATH)
    capabilities = catalog.get("data_need_capabilities")
    routes = routing.get("routes")
    if not isinstance(capabilities, list) or not isinstance(routes, list):
        raise LocalServiceError("capability_authority_malformed")
    route_by_id = {route.get("capability_id"): route for route in routes if isinstance(route, dict)}
    if len(route_by_id) != len(routes) or any(not isinstance(c, dict) or not isinstance(c.get("capability_id"), str) for c in capabilities):
        raise LocalServiceError("capability_authority_malformed")
    try:
        metadata = load_production_executor_metadata()
        executors = metadata["executors"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LocalServiceError("production_executor_metadata_unavailable") from exc
    if not isinstance(executors, list) or any(not isinstance(entry, dict) for entry in executors):
        raise LocalServiceError("production_executor_metadata_malformed")
    return catalog, route_by_id, executors


def _availability(executors: list[dict[str, Any]], capability_id: str, market: str, executor_id: str | None) -> bool:
    return executor_id is not None and any(
        entry.get("executor_id") == executor_id
        and entry.get("capability_id") == capability_id
        and entry.get("market") == market
        and entry.get("bounded_execution_supported") is True
        for entry in executors
    )


def describe_capabilities() -> dict[str, Any]:
    """Project catalog → routing disposition → production registration truthfully."""
    catalog, routes, executors = _authorities()
    capabilities: list[dict[str, Any]] = []
    for capability in catalog["data_need_capabilities"]:
        capability_id = capability["capability_id"]
        route = routes.get(capability_id)
        if route is None:
            raise LocalServiceError("capability_routing_missing")
        routing_status = route.get("routing_status")
        if routing_status not in {"resolved", "plan_only", "blocked", "provisional"}:
            raise LocalServiceError("capability_authority_malformed")
        selected_executor = route.get("selected_executor_id")
        supported_markets = capability.get("supported_markets")
        provisional_markets = capability.get("provisional_markets")
        if not isinstance(supported_markets, list) or not isinstance(provisional_markets, list):
            raise LocalServiceError("capability_authority_malformed")
        market_entries: list[dict[str, Any]] = []
        for market in sorted(set(supported_markets + provisional_markets)):
            if market in provisional_markets:
                disposition = "provisional"
                available = False
            elif routing_status == "resolved":
                available = _availability(executors, capability_id, market, selected_executor)
                if not available:
                    raise LocalServiceError("selected_production_executor_unavailable")
                disposition = "executable"
            else:
                disposition, available = routing_status, False
            market_entries.append({
                "market": market,
                "disposition": disposition,
                "production_executor_available": available,
            })
        capabilities.append({
            "capability_id": capability_id,
            "description": capability.get("description", ""),
            "semantic_support_status": capability.get("support_status"),
            "target_required": route.get("target_required"),
            "allowed_parameters": capability.get("allowed_parameters", {}),
            "approval_required": route.get("approval_required"),
            "network_required": route.get("network_required"),
            "routing_disposition": routing_status,
            "selected_executor_id": selected_executor,
            "batching_scope": route.get("batching_scope"),
            "supported_security_types": route.get("supported_security_types", []),
            "possible_timing_classes": capability.get("possible_timing_classes", []),
            "known_limitations": capability.get("known_limitations", []),
            "blocking_reasons": route.get("blocking_reasons", []),
            "markets": market_entries,
        })
    return {
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "capability_catalog_schema_version": catalog.get("schema_version"),
        "routing_matrix_schema_version": _load_json(ROUTING_PATH).get("schema_version"),
        "capabilities": capabilities,
    }
