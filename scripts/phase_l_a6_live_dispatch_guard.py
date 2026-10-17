"""Offline-verifiable A6 dispatch accounting and one-shot authority latch.

The controller never performs HTTP. Production transports remain responsible
for acquisition; A6 instrumentation must reserve each actual dispatch first.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import OpenerDirector

AUTHORITY_ID = "USER_CHAT_2026-10-16_PHASE_L_L3_A6_BOUNDED_LIVE_SOURCE_DRIFT_RECERTIFICATION_AUTHORIZATION"
PHYSICAL_CEILING = 27
_BASELINE_IDS = [f"P{i:02d}" for i in range(1, 19)] + [f"B{i:02d}" for i in range(1, 6)]
_ALTERNATE_IDS = {"P04", "P05", "P06", "P07"}
socket_timeout_sentinel = object()
_OPENER_SCOPE: ContextVar[tuple["A6DispatchController", int, frozenset[int]] | None] = ContextVar("a6_opener_scope", default=None)
_PENDING_RESERVATION: ContextVar[tuple["A6DispatchController", dict[str, Any]] | None] = ContextVar("a6_pending_reservation", default=None)


class DispatchBlocked(RuntimeError):
    """A planned physical dispatch failed a fail-closed controller check."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _canonical_sha(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PlannedSource:
    logical_sequence: int
    source_contract_id: str
    family_id: str
    target_or_selector: str
    hostname: str
    method: str
    route: str
    timeout_seconds: int
    maximum_physical_dispatches: int
    alternate_policy: str = "NONE"
    alternate_route: str | None = None


def build_plan() -> list[PlannedSource]:
    """Materialize P01-P18/B01-B05 from the current active production seams."""
    from scripts.m8a_tpex_official_eod_adapter import URL as TPEX_EOD
    from scripts.m8a_twse_official_eod_adapter import URL as TWSE_EOD
    from scripts.phase_g.research_executor import ROUTES as RESEARCH_ROUTES
    from server.services.phase_h_h1_tpex_composite import SOURCES as H1_SOURCES
    from server.services.phase_h_h2_twse_exright_executor import ENDPOINT as H2_ENDPOINT
    from server.services.phase_h_h3_twse_stock_day_adapter import ENDPOINT as H3_ENDPOINT
    from server.services.phase_i_i1_production_candidate import SOURCE_DESCRIPTORS as I1
    from server.services.phase_i_i2_production_transport import SOURCE_ENDPOINT as I2_ENDPOINT
    from server.services.phase_i_i3_production_transport import URLS as I3_URLS
    from scripts.m8r_06_01b_materialize_production_inputs import (
        TWSE_ISIN_ZH, TWSE_DELISTED_URL, TPEX_DELISTED_URL, TWSE_ETN_EXPIRED_URL,
    )
    from urllib.parse import urlsplit

    def add(seq: int, sid: str, family: str, target: str, method: str, route: str,
            timeout: int, maximum: int = 1, alt: str = "NONE",
            alternate_route: str | None = None) -> PlannedSource:
        hostname = urlsplit(route).hostname
        if urlsplit(route).scheme != "https" or not hostname or timeout <= 0:
            raise ValueError("a6_plan_route_or_timeout_invalid")
        if alternate_route is not None and urlsplit(alternate_route).scheme != "https":
            raise ValueError("a6_alternate_route_invalid")
        return PlannedSource(seq, sid, family, target, hostname, method, route,
                             timeout, maximum, alt, alternate_route)

    items = [
        add(1, "P01", "F01", "TWSE:2330+TPEX:6488", "GET", "https://mis.twse.com.tw/stock/api/getStockInfo.jsp", 15),
        add(2, "P02", "F02", "TWSE:2330", "GET", TWSE_EOD, 15),
        add(3, "P03", "F02", "TPEX:6488", "GET", TPEX_EOD, 15),
    ]
    research = [
        ("material_disclosures", "TWSE", "TWSE:2330"),
        ("material_disclosures", "TPEX", "TPEX:6488"),
        ("monthly_revenue", "TWSE", "TWSE:2330"),
        ("monthly_revenue", "TPEX", "TPEX:6488"),
    ]
    for seq, (capability, market, target) in enumerate(research, start=4):
        route = RESEARCH_ROUTES[(capability, market)]
        items.append(add(seq, f"P{seq:02d}", "F03", target, "GET", route["csv_url"], 15, 2,
                         "EXISTING_GOVERNED_JSON_ALTERNATE_ONLY", route["json_url"]))
    for seq, source in enumerate(H1_SOURCES, start=8):
        items.append(add(seq, f"P{seq:02d}", "F04", "TPEX:6488", "GET", source["endpoint"], 60))
    items.extend([
        add(11, "P11", "F05", "TWSE:2330", "GET", H2_ENDPOINT, 15),
        add(12, "P12", "F06", "TWSE:2330;month=2026-10", "GET", H3_ENDPOINT, 15),
    ])
    for seq, sid in ((13, "I1-TWSE-FMTQIK-OPENAPI"), (14, "I1-TWSE-BREADTH-TWTAZU-OPENAPI"),
                     (15, "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI")):
        descriptor = I1[sid]
        target = "TPEX:6488" if seq == 15 else "TWSE:2330"
        items.append(add(seq, f"P{seq:02d}", "F07", f"market_context:{target}", "GET", descriptor["url"], 15))
    items.extend([
        add(16, "P16", "F08", "TX:regular:standard-monthly-nearest-outright", "GET", I2_ENDPOINT, 30),
        add(17, "P17", "F09", "TWSE:2330;trade_date=2026-10-15", "GET",
            I3_URLS["TWSE"].format(date="20261015"), 30),
        add(18, "P18", "F09", "TPEX:6488;source_reported_date", "GET", I3_URLS["TPEX"], 30),
        add(19, "B01", "F10", "ISIN:TWSE:mode2:zh", "GET", TWSE_ISIN_ZH.format(mode=2), 20),
        add(20, "B02", "F10", "ISIN:TPEX:mode4:zh", "GET", TWSE_ISIN_ZH.format(mode=4), 20),
        add(21, "B03", "F10", "lifecycle:TWSE:delisted", "GET", TWSE_DELISTED_URL, 20),
        add(22, "B04", "F10", "lifecycle:TPEX:delisted", "POST", TPEX_DELISTED_URL, 20),
        add(23, "B05", "F10", "lifecycle:TWSE:ETN:expired", "GET", TWSE_ETN_EXPIRED_URL, 20),
    ])
    if len(items) != 23 or [item.source_contract_id for item in items] != _BASELINE_IDS:
        raise ValueError("a6_source_plan_inventory_mismatch")
    if sum(item.maximum_physical_dispatches for item in items) != PHYSICAL_CEILING:
        raise ValueError("a6_source_plan_physical_ceiling_mismatch")
    return items


class A6DispatchController:
    """Reserve each physical call before transport and enforce frozen limits."""

    def __init__(self, plan: list[PlannedSource], *, reservation_path: Path | None = None,
                 consumed_path: Path | None = None, expected_head: str | None = None,
                 expected_tree: str | None = None, actual_head: str | None = None,
                 actual_tree: str | None = None, live_enabled: bool = False):
        self.plan = {item.source_contract_id: item for item in plan}
        self.sequence_map = {item.logical_sequence: item for item in plan}
        self.reservation_path = reservation_path
        self.consumed_path = consumed_path
        self.expected_head, self.expected_tree = expected_head, expected_tree
        self.actual_head, self.actual_tree = actual_head, actual_tree
        self.live_enabled = live_enabled
        self.authority_state = "AUTHORIZED_NOT_CONSUMED"
        self.authority_consumed_at: str | None = None
        self.physical_dispatch_count = 0
        self.per_source_dispatch_counts = {sid: 0 for sid in self.plan}
        self.completed_sources: set[str] = set()
        self.suppressed_hosts: set[str] = set()
        self.dispatch_ledger: list[dict[str, Any]] = []
        self.logical_results: dict[str, str] = {}
        self.current_logical_sequence: int | None = None
        self.last_logical_sequence = 0
        self._lock = threading.RLock()

    def begin_logical(self, sequence: int) -> PlannedSource:
        item = self.sequence_map.get(sequence)
        if item is None or self.current_logical_sequence is not None or sequence <= self.last_logical_sequence:
            raise DispatchBlocked("a6_logical_sequence_invalid")
        if item.source_contract_id in self.completed_sources:
            raise DispatchBlocked("a6_source_already_completed")
        self.current_logical_sequence = sequence
        return item

    def end_logical(self, *, verdict: str) -> None:
        with self._lock:
            sequence = self.current_logical_sequence
            if sequence is None:
                raise DispatchBlocked("a6_no_active_logical_source")
            source_id = self.sequence_map[sequence].source_contract_id
            self.logical_results[source_id] = verdict
            self.completed_sources.add(source_id)
            self.last_logical_sequence = sequence
            self.current_logical_sequence = None

    def skip_after_rate_limit(self, sequence: int) -> str:
        item = self.sequence_map.get(sequence)
        if (item is None or self.current_logical_sequence is not None
                or sequence <= self.last_logical_sequence
                or item.hostname not in self.suppressed_hosts):
            raise DispatchBlocked("a6_rate_limit_skip_not_applicable")
        self.logical_results[item.source_contract_id] = "SKIPPED_AFTER_RATE_LIMIT"
        self.completed_sources.add(item.source_contract_id)
        self.last_logical_sequence = sequence
        return "SKIPPED_AFTER_RATE_LIMIT"

    def reserve_before_dispatch(self, *, logical_sequence: int, source_contract_id: str,
                                hostname: str, method: str, route_identity: str,
                                purpose: str = "PRIMARY", retry_after: str | None = None) -> dict[str, Any]:
        with self._lock:
            if not self.live_enabled:
                raise DispatchBlocked("A6_LIVE_RESERVATION_NOT_FINALIZED")
            planned = self.sequence_map.get(logical_sequence)
            scope = _OPENER_SCOPE.get()
            scoped = scope is not None and scope[0] is self and logical_sequence in scope[2]
            if planned is None or (self.current_logical_sequence != logical_sequence and not scoped):
                raise DispatchBlocked("a6_logical_sequence_invalid")
            if planned.source_contract_id != source_contract_id:
                raise DispatchBlocked("a6_source_sequence_mismatch")
            if source_contract_id in self.completed_sources:
                raise DispatchBlocked("a6_source_already_completed")
            approved_host = planned.hostname
            if purpose == "GOVERNED_ALTERNATE" and planned.alternate_route:
                from urllib.parse import urlsplit
                approved_host = urlsplit(planned.alternate_route).hostname or ""
            if hostname != approved_host or method != planned.method:
                raise DispatchBlocked("a6_host_or_method_not_approved")
            expected_route = planned.route if purpose == "PRIMARY" else planned.alternate_route
            if route_identity != expected_route or expected_route is None:
                raise DispatchBlocked("a6_route_not_approved")
            if hostname in self.suppressed_hosts:
                raise DispatchBlocked("a6_hostname_suppressed_after_429")
            if purpose not in {"PRIMARY", "GOVERNED_ALTERNATE"}:
                raise DispatchBlocked("a6_dispatch_role_invalid")
            if purpose == "GOVERNED_ALTERNATE" and source_contract_id not in _ALTERNATE_IDS:
                raise DispatchBlocked("a6_alternate_not_authorized")
            if self.per_source_dispatch_counts[source_contract_id] >= planned.maximum_physical_dispatches:
                raise DispatchBlocked("a6_per_source_dispatch_ceiling")
            if purpose == "GOVERNED_ALTERNATE" and self.per_source_dispatch_counts[source_contract_id] != 1:
                raise DispatchBlocked("a6_alternate_requires_primary")
            if purpose == "PRIMARY" and self.per_source_dispatch_counts[source_contract_id] != 0:
                raise DispatchBlocked("a6_primary_already_dispatched")
            if self.physical_dispatch_count >= PHYSICAL_CEILING:
                raise DispatchBlocked("a6_global_dispatch_ceiling")
            self._consume_authority_before_dispatch()
            self.physical_dispatch_count += 1
            self.per_source_dispatch_counts[source_contract_id] += 1
            record = {
                "physical_dispatch_sequence": self.physical_dispatch_count,
                "logical_sequence": logical_sequence,
                "source_contract_id": source_contract_id,
                "family_id": planned.family_id,
                "hostname": hostname,
                "method": method,
                "route_identity": route_identity,
                "dispatch_role": purpose,
                "reserved_at": _now(),
                "retry_count": 0,
                "http_status": None,
                "retry_after_raw": retry_after,
            }
            self.dispatch_ledger.append(record)
            return record

    def _consume_authority_before_dispatch(self) -> None:
        if self.authority_state == "CONSUMED":
            return
        if not (self.reservation_path and self.consumed_path):
            raise DispatchBlocked("A6_LIVE_RESERVATION_NOT_FINALIZED")
        try:
            if self.consumed_path.exists():
                raise DispatchBlocked("a6_authority_already_consumed")
            reservation = json.loads(self.reservation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DispatchBlocked("A6_LIVE_RESERVATION_NOT_FINALIZED") from exc
        expected = {
            "authority_id": AUTHORITY_ID,
            "state": "RESERVED_NOT_CONSUMED",
            "pre_network_head": self.expected_head,
            "pre_network_tree": self.expected_tree,
        }
        if (any(reservation.get(key) != value for key, value in expected.items())
                or self.actual_head != self.expected_head or self.actual_tree != self.expected_tree):
            raise DispatchBlocked("a6_authority_reservation_binding_invalid")
        receipt = {
            "authority_id": AUTHORITY_ID,
            "state": "CONSUMED",
            "consumed_at": _now(),
            "pre_network_head": self.expected_head,
            "pre_network_tree": self.expected_tree,
            "first_logical_sequence": self.current_logical_sequence,
            "physical_dispatch_count_at_consumption": 0,
        }
        self._atomic_json(self.consumed_path, receipt)
        self.authority_state = "CONSUMED"
        self.authority_consumed_at = receipt["consumed_at"]

    @staticmethod
    def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, path)

    def observe_response(self, record: dict[str, Any], *, http_status: int | None,
                         retry_after: str | None = None) -> None:
        with self._lock:
            if record not in self.dispatch_ledger:
                raise DispatchBlocked("a6_unknown_dispatch_record")
            record["http_status"] = http_status
            record["retry_after_raw"] = retry_after
            record["transport_outcome"] = "http_response" if http_status is not None else "unknown"
            record["completed_at"] = _now()
            if http_status == 429:
                self.suppressed_hosts.add(record["hostname"])
                record["lifecycle_observation"] = "rate_limit_observed"
            elif http_status == 404:
                record["lifecycle_observation"] = "endpoint_not_found_observed"
            elif http_status == 410:
                record["lifecycle_observation"] = "endpoint_gone_observed"

    def observe_transport_failure(self, record: dict[str, Any], exc: BaseException) -> None:
        with self._lock:
            if record not in self.dispatch_ledger:
                raise DispatchBlocked("a6_unknown_dispatch_record")
            record["transport_outcome"] = "transport_failure"
            record["failure_class"] = type(exc).__name__[:64]
            record["completed_at"] = _now()

    @contextmanager
    def production_source_scope(self, logical_sequence: int, *, family_sequences: tuple[int, ...] = ()):
        """Mark the production operation whose actual urllib opens are being observed."""
        allowed = frozenset((logical_sequence, *family_sequences))
        if any(sequence not in self.sequence_map for sequence in allowed):
            raise DispatchBlocked("a6_logical_sequence_invalid")
        token = _OPENER_SCOPE.set((self, logical_sequence, allowed))
        try:
            yield
        finally:
            _OPENER_SCOPE.reset(token)

    @contextmanager
    def install_urllib_guard(self):
        """Instrument urllib's actual opener boundary without implementing HTTP."""
        original = OpenerDirector.open
        controller = self

        def guarded(opener: OpenerDirector, fullurl: Any, data: Any = None, timeout: Any = socket_timeout_sentinel):
            scope = _OPENER_SCOPE.get()
            if scope is None or scope[0] is not controller:
                raise DispatchBlocked("a6_unattributed_http_dispatch_blocked")
            request_url = fullurl.full_url if hasattr(fullurl, "full_url") else str(fullurl)
            method = fullurl.get_method() if hasattr(fullurl, "get_method") else ("POST" if data is not None else "GET")
            planned, role = controller._match_request(request_url, method)
            if timeout is socket_timeout_sentinel or isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout != planned.timeout_seconds:
                raise DispatchBlocked("a6_source_timeout_mismatch")
            pending = _PENDING_RESERVATION.get()
            if pending is not None and pending[0] is controller:
                record = pending[1]
                if (record["source_contract_id"] != planned.source_contract_id
                        or record["method"] != method or record["hostname"] != planned.hostname
                        or planned.logical_sequence not in scope[2]):
                    _PENDING_RESERVATION.set(None)
                    raise DispatchBlocked("a6_preset_reservation_binding_invalid")
                _PENDING_RESERVATION.set(None)
            else:
                record = controller.reserve_before_dispatch(
                    logical_sequence=planned.logical_sequence,
                    source_contract_id=planned.source_contract_id,
                    hostname=planned.hostname if role == "PRIMARY" else urlsplit(planned.alternate_route or "").hostname or "",
                    method=method,
                    route_identity=planned.route if role == "PRIMARY" else planned.alternate_route or "",
                    purpose=role,
                )
            try:
                response = original(opener, fullurl, data=data, timeout=timeout)
            except HTTPError as exc:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                controller.observe_response(record, http_status=exc.code, retry_after=retry_after)
                raise
            except BaseException as exc:
                controller.observe_transport_failure(record, exc)
                raise
            status = getattr(response, "status", None)
            headers = getattr(response, "headers", None)
            retry_after = headers.get("Retry-After") if headers is not None else None
            controller.observe_response(record, http_status=status, retry_after=retry_after)
            return response

        OpenerDirector.open = guarded
        try:
            yield self
        finally:
            pending = _PENDING_RESERVATION.get()
            if pending is not None and pending[0] is self:
                _PENDING_RESERVATION.set(None)
            OpenerDirector.open = original

    def _match_request(self, url: str, method: str) -> tuple[PlannedSource, str]:
        parsed = urlsplit(url)
        active = _OPENER_SCOPE.get()
        assert active is not None
        _controller, anchor, allowed = active
        candidates: list[tuple[PlannedSource, str]] = []
        for item in self.sequence_map.values():
            if item.logical_sequence not in allowed or item.method != method:
                continue
            if item.alternate_route and url == item.alternate_route:
                role = "GOVERNED_ALTERNATE"
                expected_host = urlsplit(item.alternate_route).hostname
            else:
                role = "PRIMARY"
                expected_host = item.hostname
            if role == "PRIMARY" and item.source_contract_id in {"P01", "P12"}:
                expected = urlsplit(item.route)
                if parsed.path != expected.path:
                    continue
                query = parse_qs(parsed.query, keep_blank_values=True)
                if item.source_contract_id == "P01":
                    channels = query.get("ex_ch", [""])[0].split("|")
                    if set(channels) != {"tse_2330.tw", "otc_6488.tw"} or query.get("json") != ["1"] or query.get("delay") != ["0"]:
                        continue
                else:
                    if query.get("stockNo") != ["2330"] or query.get("date") != ["20261001"] or query.get("response") != ["html"]:
                        continue
            elif role == "PRIMARY" and url != item.route:
                continue
            if parsed.hostname != expected_host:
                continue
            candidates.append((item, role))
        if len(candidates) != 1:
            raise DispatchBlocked("a6_route_not_approved_or_ambiguous")
        item, role = candidates[0]
        if item.logical_sequence != anchor and item.logical_sequence not in allowed:
            raise DispatchBlocked("a6_logical_sequence_invalid")
        return item, role


def invoke_reserved_transport(controller: A6DispatchController, *, logical_sequence: int,
                              source_contract_id: str, hostname: str, method: str,
                              route_identity: str, transport: Any,
                              purpose: str = "PRIMARY") -> tuple[Any, dict[str, Any]]:
    """Reusable decorator pattern: reserve before invoking an injected transport."""
    record = controller.reserve_before_dispatch(
        logical_sequence=logical_sequence, source_contract_id=source_contract_id,
        hostname=hostname, method=method, route_identity=route_identity, purpose=purpose,
    )
    try:
        response = transport(record)
    except BaseException as exc:
        controller.observe_transport_failure(record, exc)
        raise
    status = getattr(response, "status", None)
    headers = getattr(response, "headers", None)
    if status is not None:
        retry_after = None
        if headers is not None:
            try:
                retry_after = headers.get("Retry-After")
            except Exception:
                retry_after = None
        controller.observe_response(record, http_status=status, retry_after=retry_after)
    return response, record


def pre1_live_entrypoint(*_args: Any, **_kwargs: Any) -> None:
    """PRE1 has no final live reservation and cannot perform acquisition."""
    raise DispatchBlocked("A6_LIVE_RESERVATION_NOT_FINALIZED")


def plan_json() -> list[dict[str, Any]]:
    return [item.__dict__.copy() for item in build_plan()]


def contract_matrix() -> list[dict[str, Any]]:
    """Return transport-boundary evidence for all frozen logical members."""
    entries = []
    for item in build_plan():
        sid = item.source_contract_id
        detail = {
            "P01": ("scripts.m8r_06_03_production_adapter._current_observation", "scripts.m5k_common.execute_live_observation", "urllib.request.urlopen(req, timeout=timeout, context=ssl_context)", "timeout=request['timeout_seconds']=15", "write_latest=False; allow_individual_fallback=False", "A6 OpenerDirector.open pre-dispatch hook"),
            "P02": ("scripts.m8a_twse_official_eod_adapter.execute_twse_official_eod_adapter", "fetch_twse_official_eod_json", "urllib.request.urlopen(req, timeout=timeout)", "execute(..., timeout=15)", "in-memory adapter result only", "A6 OpenerDirector.open pre-dispatch hook"),
            "P03": ("scripts.m8a_tpex_official_eod_adapter.execute_tpex_official_eod_adapter", "fetch_tpex_official_eod_json", "urllib.request.urlopen(req, timeout=timeout)", "execute(..., timeout=15)", "in-memory adapter result only", "A6 OpenerDirector.open pre-dispatch hook"),
            "P04": ("scripts.m8r_06_03_production_adapter._research_batch_operation_adapter", "scripts.phase_g.research_executor.fetch_once", "urllib.request.urlopen(request, timeout=timeout)", "approved request timeout_seconds=15", "evidence root redirected to per-run temporary directory", "A6 OpenerDirector.open hook; CSV and governed JSON endpoints"),
            "P05": ("scripts.m8r_06_03_production_adapter._research_batch_operation_adapter", "scripts.phase_g.research_executor.fetch_once", "urllib.request.urlopen(request, timeout=timeout)", "approved request timeout_seconds=15", "evidence root redirected to per-run temporary directory", "A6 OpenerDirector.open hook; CSV and governed JSON endpoints"),
            "P06": ("scripts.m8r_06_03_production_adapter._research_batch_operation_adapter", "scripts.phase_g.research_executor.fetch_once", "urllib.request.urlopen(request, timeout=timeout)", "approved request timeout_seconds=15", "evidence root redirected to per-run temporary directory", "A6 OpenerDirector.open hook; CSV and governed JSON endpoints"),
            "P07": ("scripts.m8r_06_03_production_adapter._research_batch_operation_adapter", "scripts.phase_g.research_executor.fetch_once", "urllib.request.urlopen(request, timeout=timeout)", "approved request timeout_seconds=15", "evidence root redirected to per-run temporary directory", "A6 OpenerDirector.open hook; CSV and governed JSON endpoints"),
            "P08": ("server.services.phase_h_h1_tpex_composite.execute_composite_operation", "official_get(attention)", "opener.open(request, timeout=timeout_seconds)", "request timeout_seconds=60", "governed output root redirected to per-run temporary directory", "A6 opener hook attributes endpoint to P08"),
            "P09": ("server.services.phase_h_h1_tpex_composite.execute_composite_operation", "official_get(disposition)", "opener.open(request, timeout=timeout_seconds)", "request timeout_seconds=60", "governed output root redirected to per-run temporary directory", "A6 opener hook attributes endpoint to P09"),
            "P10": ("server.services.phase_h_h1_tpex_composite.execute_composite_operation", "official_get(changed-trading)", "opener.open(request, timeout=timeout_seconds)", "request timeout_seconds=60", "governed output root redirected to per-run temporary directory", "A6 opener hook attributes endpoint to P10"),
            "P11": ("server.services.phase_h_h2_twse_exright_executor", "official_get_once", "opener.open(request, timeout=timeout_seconds)", "timeout_seconds=15 <= TIMEOUT_SECONDS=15", "response returned in memory; executor output isolated", "A6 opener hook"),
            "P12": ("server.services.phase_h_h3_twse_stock_day_adapter.fetch_twse_stock_day_month", "_default_http_get", "opener.open(request, timeout_seconds)", "timeout_seconds=15 passed to injected HTTPGet", "pure result; no walker and no persistence", "A6 injected HTTPGet delegates through counted opener"),
            "P13": ("server.services.phase_i_i1_production_candidate._fetch_source", "_http_transport", "transport(url, TIMEOUT_SECONDS)", "TIMEOUT_SECONDS=15", "TransportObservation held in memory", "A6 source-specific transport delegate"),
            "P14": ("server.services.phase_i_i1_production_candidate._fetch_source", "_http_transport", "transport(url, TIMEOUT_SECONDS)", "TIMEOUT_SECONDS=15", "TransportObservation held in memory", "A6 source-specific transport delegate"),
            "P15": ("server.services.phase_i_i1_production_candidate._fetch_source", "_http_transport", "transport(url, TIMEOUT_SECONDS)", "TIMEOUT_SECONDS=15", "TransportObservation held in memory", "A6 source-specific transport delegate"),
            "P16": ("server.services.phase_i_i2_production_transport.acquire_taifex_once", "injected transport", "transport(url, TIMEOUT_SECONDS)", "TIMEOUT_SECONDS=30", "AcquiredSource held in memory", "A6 injected transport delegate"),
            "P17": ("server.services.phase_i_i3_production_transport.acquire_once(TWSE)", "single-dispatch opener", "client.open(req, timeout=TIMEOUT_SECONDS)", "TIMEOUT_SECONDS=30", "Acquisition held in memory", "A6 supplied opener"),
            "P18": ("server.services.phase_i_i3_production_transport.acquire_once(TPEX)", "single-dispatch opener", "client.open(req, timeout=TIMEOUT_SECONDS)", "TIMEOUT_SECONDS=30", "Acquisition held in memory", "A6 supplied opener"),
        }
        if sid.startswith("B"):
            executor = "skills/tw-security-master-classifier/scripts/probe_sources.probe"
            transport = "probe(url, ..., timeout=20, max_followed_redirects=0, save_raw=None)"
            timeout_expr = "probe(timeout=20) -> opener.open(request, timeout=timeout)"
            write = "save_raw=None; parser result held in memory"
            instrument = "A6 BootstrapDispatchBudget adapter reserves global controller before probe opener"
        else:
            executor, transport, expression, timeout_expr, write, instrument = detail[sid]
        redirect = "follow_limit=0; redirect observed without follow" if sid.startswith("B") else (
            "rejected by source transport" if sid in {"P11", "P17", "P18"} else
            "counted as a physical dispatch; source cap blocks excess before dispatch")
        entries.append({
            "sequence": item.logical_sequence,
            "source_contract_id": sid,
            "family_id": item.family_id,
            "production_executor": executor,
            "production_transport": transport,
            "transport_function": expression if not sid.startswith("B") else transport,
            "hostname": item.hostname,
            "method": item.method,
            "route_identity": item.route,
            "timeout_seconds": item.timeout_seconds,
            "timeout_enforcement_expression": timeout_expr,
            "maximum_physical_dispatches": item.maximum_physical_dispatches,
            "retry_supported": False,
            "a6_retry_allowed": False,
            "redirect_behavior": redirect,
            "persistent_write_behavior": write,
            "a6_nonpersistent_mode": write,
            "instrumentation_strategy": instrument,
        })
    if len(entries) != 23 or any(not e["timeout_enforcement_expression"] for e in entries):
        raise ValueError("a6_transport_matrix_incomplete")
    return entries


def canonical_json_sha(value: Mapping[str, Any]) -> str:
    return _canonical_sha(value)


class A6BootstrapBudgetAdapter:
    """Minimal probe_sources.BootstrapDispatchBudget-compatible adapter."""
    def __init__(self, controller: A6DispatchController, *, logical_sequence: int):
        self.controller = controller
        self.logical_sequence = logical_sequence
        self.used_dispatches = 0
        self.maximum_total_dispatches = 1
        self._record: dict[str, Any] | None = None

    @property
    def remaining_dispatches(self) -> int:
        return self.maximum_total_dispatches - self.used_dispatches

    def reserve_before_dispatch(self) -> int:
        if self.used_dispatches:
            raise DispatchBlocked("a6_bootstrap_per_source_ceiling")
        item = self.controller.sequence_map[self.logical_sequence]
        self._record = self.controller.reserve_before_dispatch(
            logical_sequence=self.logical_sequence,
            source_contract_id=item.source_contract_id,
            hostname=item.hostname,
            method=item.method,
            route_identity=item.route,
            purpose="PRIMARY",
        )
        _PENDING_RESERVATION.set((self.controller, self._record))
        self.used_dispatches += 1
        return self.used_dispatches


def transport_observation(*, source_contract_id: str, observed_at: str,
                          http_status: int | None, retry_after: str | None = None,
                          transport_outcome: str = "http_response",
                          contract_outcome: str = "unknown", semantic_outcome: str = "unknown",
                          response_form: str = "unknown", empty_response_policy: str = "unknown",
                          target_binding: str = "unknown", source_reported_period: str | None = None,
                          requested_period: str | None = None, previous_row_count: int | None = None,
                          current_row_count: int | None = None) -> dict[str, Any]:
    """Adapt explicit bounded facts into the accepted private A5 contract."""
    from server.services.phase_l_source_drift_contract import observe_source_attempt
    return observe_source_attempt(
        source_contract_id=source_contract_id, observed_at=observed_at,
        http_status=http_status, retry_after=retry_after,
        transport_outcome=transport_outcome, contract_outcome=contract_outcome,
        semantic_outcome=semantic_outcome, response_form=response_form,
        empty_response_policy=empty_response_policy, target_binding=target_binding,
        source_reported_period=source_reported_period, requested_period=requested_period,
        previous_row_count=previous_row_count, current_row_count=current_row_count,
    ).as_dict()
