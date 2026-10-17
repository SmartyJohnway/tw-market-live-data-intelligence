from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.phase_l_a6_live_dispatch_guard import A6DispatchController, DispatchBlocked, build_plan


def _controller(tmp_path: Path, *, source_id: str):
    plan = build_plan()
    item = next(row for row in plan if row.source_contract_id == source_id)
    reservation = tmp_path / f"{source_id}-reservation.json"
    consumed = tmp_path / f"{source_id}-consumed.json"
    reservation.write_text(json.dumps({"authority_id": "USER_CHAT_2026-10-16_PHASE_L_L3_A6_BOUNDED_LIVE_SOURCE_DRIFT_RECERTIFICATION_AUTHORIZATION",
        "state": "RESERVED_NOT_CONSUMED", "pre_network_head": "head", "pre_network_tree": "tree"}), encoding="utf-8")
    controller = A6DispatchController(plan, reservation_path=reservation, consumed_path=consumed,
        expected_head="head", expected_tree="tree", actual_head="head", actual_tree="tree", live_enabled=True)
    return item, controller


@pytest.mark.parametrize("source_id,primary_host,alternate_host", [
    ("P04", "mopsfin.twse.com.tw", "openapi.twse.com.tw"),
    ("P05", "mopsfin.twse.com.tw", "www.tpex.org.tw"),
    ("P06", "mopsfin.twse.com.tw", "openapi.twse.com.tw"),
    ("P07", "mopsfin.twse.com.tw", "www.tpex.org.tw"),
])
def test_governed_alternate_matches_exact_cross_host_route(tmp_path, source_id, primary_host, alternate_host):
    from urllib.parse import urlsplit

    item, controller = _controller(tmp_path, source_id=source_id)
    assert item.hostname == primary_host
    assert urlsplit(item.alternate_route).hostname == alternate_host
    controller.begin_logical(item.logical_sequence)
    fake_transport_calls = []
    with controller.production_source_scope(item.logical_sequence):
        primary, role = controller._match_request(item.route, item.method)
        assert primary.source_contract_id == source_id and role == "PRIMARY"
        record = controller.reserve_before_dispatch(logical_sequence=item.logical_sequence,
            source_contract_id=source_id, hostname=item.hostname, method=item.method,
            route_identity=item.route, purpose=role)
        fake_transport_calls.append(record["dispatch_role"])
        controller.observe_response(record, http_status=500)

        alternate, role = controller._match_request(item.alternate_route, item.method)
        assert alternate.source_contract_id == source_id and role == "GOVERNED_ALTERNATE"
        record = controller.reserve_before_dispatch(logical_sequence=item.logical_sequence,
            source_contract_id=source_id, hostname=alternate_host, method=item.method,
            route_identity=item.alternate_route, purpose=role)
        fake_transport_calls.append(record["dispatch_role"])
        controller.observe_response(record, http_status=200)
    controller.end_logical(verdict="TRANSPORT_OR_HTTP_DEGRADED")
    assert fake_transport_calls == ["PRIMARY", "GOVERNED_ALTERNATE"]
    assert controller.per_source_dispatch_counts[source_id] == 2


@pytest.mark.parametrize("source_id", ["P04", "P05", "P06", "P07"])
def test_wrong_or_nonexact_alternate_url_fails_before_reservation(tmp_path, source_id):
    item, controller = _controller(tmp_path, source_id=source_id)
    controller.begin_logical(item.logical_sequence)
    with controller.production_source_scope(item.logical_sequence):
        for unapproved in (item.alternate_route + "?added=1", "https://evil.example/" + item.alternate_route.split("/", 3)[-1]):
            with pytest.raises(DispatchBlocked, match="a6_route_not_approved_or_ambiguous"):
                controller._match_request(unapproved, item.method)


@pytest.mark.parametrize("source_id", ["P01", "P03"])
def test_other_source_cannot_borrow_governed_alternate(tmp_path, source_id):
    item, controller = _controller(tmp_path, source_id=source_id)
    alternate = next(row.alternate_route for row in build_plan() if row.source_contract_id == "P04")
    controller.begin_logical(item.logical_sequence)
    with controller.production_source_scope(item.logical_sequence):
        with pytest.raises(DispatchBlocked, match="a6_route_not_approved_or_ambiguous"):
            controller._match_request(alternate, "GET")


def test_alternate_before_primary_and_per_source_overflow_are_blocked(tmp_path):
    item, controller = _controller(tmp_path, source_id="P04")
    controller.begin_logical(item.logical_sequence)
    with controller.production_source_scope(item.logical_sequence):
        with pytest.raises(DispatchBlocked, match="a6_alternate_requires_primary"):
            controller.reserve_before_dispatch(logical_sequence=item.logical_sequence,
                source_contract_id="P04", hostname="openapi.twse.com.tw", method="GET",
                route_identity=item.alternate_route, purpose="GOVERNED_ALTERNATE")
        primary = controller.reserve_before_dispatch(logical_sequence=item.logical_sequence,
            source_contract_id="P04", hostname=item.hostname, method="GET",
            route_identity=item.route, purpose="PRIMARY")
        controller.observe_response(primary, http_status=500)
        alternate = controller.reserve_before_dispatch(logical_sequence=item.logical_sequence,
            source_contract_id="P04", hostname="openapi.twse.com.tw", method="GET",
            route_identity=item.alternate_route, purpose="GOVERNED_ALTERNATE")
        controller.observe_response(alternate, http_status=200)
        with pytest.raises(DispatchBlocked, match="a6_per_source_dispatch_ceiling"):
            controller.reserve_before_dispatch(logical_sequence=item.logical_sequence,
                source_contract_id="P04", hostname=item.hostname, method="GET",
                route_identity=item.route, purpose="PRIMARY")
