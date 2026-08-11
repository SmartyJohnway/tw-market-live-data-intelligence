"""M8R-06-03 route identity regression tests.

One executor is permitted to serve several governed routes.  These tests keep
the route key as the only lookup authority and reject legacy executor-only
resolution once it would be ambiguous.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from scripts.m8r_05b_03.dispatch import RuntimeAdapterRegistry
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.registry import ExecutorMetadataRegistry, executor_route_key
from tests.unit.m8r_05b_03_test_helpers import registry_metadata, runtime_registration


EXECUTOR = "m8r_03d_watchlist_controlled_executor_adapter"
ROUTES = (
    ("current_observation", "TWSE"),
    ("current_observation", "TPEX"),
    ("official_eod_reference", "TWSE"),
    ("official_eod_reference", "TPEX"),
)


def _metadata() -> dict:
    payload = registry_metadata()
    prototype = payload["executors"][0]
    payload["executors"] = [
        {
            **prototype,
            "executor_id": EXECUTOR,
            "capability_id": capability_id,
            "market": market,
        }
        for capability_id, market in ROUTES
    ]
    return payload


def _registrations():
    prototype = runtime_registration()
    return [
        replace(
            prototype,
            executor_id=EXECUTOR,
            capability_id=capability_id,
            market=market,
            fake_adapter=True,
        )
        for capability_id, market in ROUTES
    ]


def test_four_routes_for_one_executor_coexist_and_resolve_exactly():
    metadata = ExecutorMetadataRegistry.from_json(_metadata())
    runtime = RuntimeAdapterRegistry(_registrations())

    assert metadata.route_keys() == tuple(sorted(executor_route_key(EXECUTOR, *route) for route in ROUTES))
    for capability_id, market in ROUTES:
        assert metadata.get_route(EXECUTOR, capability_id, market).market == market
        assert runtime.get_route(EXECUTOR, capability_id, market).capability_id == capability_id

    with pytest.raises(OrchestrationError, match="ambiguous_executor_lookup"):
        metadata.get(EXECUTOR)
    with pytest.raises(OrchestrationError, match="ambiguous_runtime_adapter_lookup"):
        runtime.get(EXECUTOR)


def test_exact_duplicate_route_rejected_but_wrong_route_has_no_fallback():
    duplicated = _metadata()
    duplicated["executors"].append(dict(duplicated["executors"][0]))
    with pytest.raises(OrchestrationError, match="duplicate_executor_route"):
        ExecutorMetadataRegistry.from_json(duplicated)

    registrations = _registrations()
    with pytest.raises(OrchestrationError, match="duplicate_runtime_adapter_route"):
        RuntimeAdapterRegistry([*registrations, registrations[0]])

    metadata = ExecutorMetadataRegistry.from_json(_metadata())
    with pytest.raises(OrchestrationError, match="unknown_executor_route"):
        metadata.get_route(EXECUTOR, "current_observation", "TAIFEX")
