"""One-shot A6 source-contract recertification orchestrator.

The runner calls the current source transport/parser seams. It owns no provider
client and cannot run live until a reservation bound to the exact committed
tree is supplied. ``--offline-simulate`` uses the same source bindings with a
deterministic fake urllib opener.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, Mapping
from email.message import Message
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import OpenerDirector

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.phase_l_a6_live_dispatch_guard import (  # noqa: E402
    A6BootstrapBudgetAdapter, A6DispatchController, DispatchBlocked,
    build_plan, contract_matrix, plan_json,
)
from server.services.phase_l_source_drift_contract import observe_source_attempt  # noqa: E402

VERDICTS = {"CONFORMING", "CONFORMING_WITH_UNCERTAINTY", "TRANSPORT_OR_HTTP_DEGRADED",
            "CONTRACT_DRIFT_OBSERVED", "SKIPPED_AFTER_RATE_LIMIT", "NOT_EXECUTED"}
OVERALL = {"PASS", "PARTIAL", "SOURCE_CHANGED", "INCONCLUSIVE"}


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _canonical_sha(value: Mapping[str, Any]) -> str:
    return _sha_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


class _FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, headers: Mapping[str, str] | None = None, url: str = ""):
        self._body = body
        self._offset = 0
        self.status = status
        self.code = status
        self.headers = Message()
        for key, value in (headers or {"Content-Type": "application/json"}).items():
            self.headers[key] = value
        self._url = url

    def read(self, amount: int = -1) -> bytes:
        if amount < 0:
            amount = len(self._body) - self._offset
        result = self._body[self._offset:self._offset + amount]
        self._offset += len(result)
        return result

    def geturl(self) -> str:
        return self._url

    def getcode(self) -> int:
        return self.status

    def close(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, *_args: Any) -> bool:
        self.close()
        return False


class _FakeOpener:
    """Offline-only source response delegate used beneath the A6 guard."""
    def __init__(self, response_factory: Callable[[str, str], tuple[int, bytes, Mapping[str, str]]]):
        self.response_factory = response_factory
        self.calls: list[dict[str, Any]] = []

    def open(self, opener: OpenerDirector, fullurl: Any, data: Any = None, timeout: Any = None):
        url = fullurl.full_url if hasattr(fullurl, "full_url") else str(fullurl)
        method = fullurl.get_method() if hasattr(fullurl, "get_method") else ("POST" if data is not None else "GET")
        self.calls.append({"url": url, "method": method, "timeout": timeout})
        status, body, headers = self.response_factory(url, method)
        if status >= 400:
            raise HTTPError(url, status, "offline simulated response", headers, None)
        return _FakeResponse(body, status=status, headers=headers, url=url)


def _json_response(rows: Any, *, content_type: str = "application/json") -> tuple[int, bytes, Mapping[str, str]]:
    return 200, json.dumps(rows, ensure_ascii=False).encode("utf-8"), {"Content-Type": content_type}


def _source_rows_for_research(route: Mapping[str, str], transport: str = "official_csv") -> list[dict[str, str]]:
    from scripts.phase_g.research_executor import SOURCE_FIELD_MAPPINGS
    aliases = SOURCE_FIELD_MAPPINGS[(route["contract"], transport)]
    row: dict[str, str] = {}
    for key, names in aliases.items():
        if key == "company_code": value = "2330" if route["contract"].endswith("_L") else "6488"
        elif key in {"publication_date", "reporting_period"}: value = "2026/10/16"
        elif key == "publication_time": value = "12:00"
        elif key == "company_name": value = "fixture"
        elif key == "note": value = ""
        else: value = "0"
        row[names[0]] = value
    return [row]


def _default_offline_response(url: str, method: str) -> tuple[int, bytes, Mapping[str, str]]:
    host = urlsplit(url).hostname or ""
    if host == "mopsfin.twse.com.tw" and url.endswith(".csv"):
        from scripts.phase_g.research_executor import ROUTES
        route = next(value for value in ROUTES.values() if value["csv_url"] == url)
        rows = _source_rows_for_research(route)
        fields = list(rows[0])
        body = (",".join(fields) + "\n" + ",".join(rows[0][key] for key in fields) + "\n").encode("utf-8")
        return 200, body, {"Content-Type": "text/csv; charset=utf-8"}
    if "/opendata/" in url and any(token in url for token in ("t187ap04", "t187ap05")):
        from scripts.phase_g.research_executor import ROUTES
        route = next(value for value in ROUTES.values() if value["json_url"] == url)
        return _json_response(_source_rows_for_research(route, "official_json_openapi"))
    if "getStockInfo.jsp" in url:
        a1 = ROOT / "tests/unit/test_l3_a1_twse_mis_response_contract.py"
        mis = json.loads((ROOT / "tests/fixtures/market_sources/twse_mis/success.json").read_text(encoding="utf-8"))
        matrix = json.loads((ROOT / "tests/fixtures/market_sources/twse_mis/normalization_v2_matrix.json").read_text(encoding="utf-8"))
        tpex_row = next(case["row"] for case in matrix["cases"] if case["name"] == "tpex_stock")
        tpex_row["c"] = "6488"
        tpex_row["ch"] = "6488.tw"
        mis["msgArray"] = [next(row for row in mis["msgArray"] if row.get("c") == "2330"), tpex_row]
        return _json_response(mis)
    if urlsplit(url).path == "/exchangeReport/STOCK_DAY":
        html = ("<!doctype html><html><head><meta charset='utf-8'></head><body><table><thead>"
            "<tr><th colspan='10'><div>115年10月 2330 台積電 各日成交資訊</div></th></tr>"
            "<tr><th>日期</th><th>成交股數</th><th>成交金額</th><th>開盤價</th><th>最高價</th><th>最低價</th><th>收盤價</th><th>漲跌價差</th><th>成交筆數</th><th>註記</th></tr>"
            "</thead><tbody><tr><td>115/10/01</td><td>1,000</td><td>1,000,000</td><td>1,000</td><td>1,010</td><td>990</td><td>1,005</td><td>5</td><td>100</td><td></td></tr></tbody></table></body></html>").encode("utf-8")
        return 200, html, {"Content-Type": "text/html; charset=utf-8"}
    if "DailyMarketReportFut" in url:
        row = {"Date":"20261016", "Contract":"TX", "ContractMonth(Week)":"202611", "Open":"1", "High":"1", "Low":"1", "Last":"1", "Change":"0", "%":"0", "Volume":"1", "SettlementPrice":"1", "OpenInterest":"1", "BestBid":"1", "BestAsk":"1", "TradingHalt":"N", "TradingSession":"一般"}
        return _json_response([row], content_type="application/octet-stream")
    if urlsplit(url).path.endswith("/fund/T86"):
        fixture = json.loads((ROOT / "tests/fixtures/phase_i_i3_a0/twse_synthetic.json").read_text(encoding="utf-8"))
        fixture["date"] = "20261015"
        fixture["data"][0][0] = "2330"
        return _json_response(fixture)
    if url.endswith("tpex_3insti_daily_trading"):
        fixture = json.loads((ROOT / "tests/fixtures/phase_i_i3_a0/tpex_synthetic_hypothesis_only.json").read_text(encoding="utf-8"))
        for row in fixture:
            row["Date"] = "1151015"
        fixture[0]["SecuritiesCompanyCode"] = "6488"
        return _json_response(fixture)
    if "/exchangeReport/FMTQIK" in url:
        return _json_response([{"Date":"1151016", "TradeVolume":"1200", "TradeValue":"345600", "Transaction":"42", "TAIEX":"23000.25", "Change":"-12.5"}])
    if "twtazu_od" in url:
        return _json_response([{"出表日期":"1151016", "類型":"股票", "上漲":"4", "漲停":"1", "下跌":"3", "跌停":"0", "持平":"2", "未成交":"1", "無比價":"0"}])
    if "mainborad_highlight" in url:
        return _json_response([{"Date":"1151016", "DailyTradingValue":"12.5", "DailyTradingVolume":"23.4", "CloseIndex":"200.5", "IndexChange":"-1.25", "PriceRiseCompanyNumbers":"4", "LimitUpCompanyNumbers":"1", "PriceDeclineCompanyNumbers":"3", "LimitDownCompanyNumbers":"0", "PriceFlatCompanyNumbers":"2", "UnmatchedCompanyNumbersSuspensionStocksIncluded":"1"}])
    if url.endswith("/TWT48U_ALL") or "/tpex_" in url or "/exchangeReport/" in url or "/opendata/" in url:
        # Empty arrays are accepted source-level observations for these contracts.
        return _json_response([])
    if "isin/" in url or "deListed" in url or "expireEnd" in url or "suspendListing" in url:
        if "isin/" in url or "suspendListing" in url:
            body = "<html><body>ISIN<table><tr><th>證券代號</th><th>國際證券辨識號碼</th></tr><tr><td>2330</td><td>TW0002330008</td></tr></table></body></html>".encode("utf-8")
        elif "expireEnd" in url:
            body = json.dumps({"stat":"ok", "title":"到期或終止上市資訊", "fields":["終止上市日期","證券代號","證券簡稱","發行證券商","終止上市理由"], "data":[]}, ensure_ascii=False).encode("utf-8")
            return 200, body, {"Content-Type":"application/json"}
        else:
            body = json.dumps({"stat":"ok", "tables":[{"title":"下櫃股票", "fields":[], "data":[], "totalCount":0}]}, ensure_ascii=False).encode("utf-8")
        return 200, body, {"Content-Type": "text/html" if body.startswith(b"<") else "application/json"}
    return _json_response([])


def _read_response(url: str, timeout: int) -> tuple[int, Mapping[str, str], bytes]:
    from urllib.request import Request, urlopen
    with urlopen(Request(url, method="GET"), timeout=timeout) as response:
        return int(response.status), dict(response.headers.items()), response.read()


def _invoke_source(sequence: int, controller: A6DispatchController, run_dir: Path) -> tuple[str, dict[str, Any]]:
    """Run exactly one planned source-level production transport/parser seam."""
    item = controller.sequence_map[sequence]
    sid = item.source_contract_id
    if sid == "P01":
        from scripts.m5k_common import execute_live_observation
        watchlist = {"schema_version": "m5k_watchlist.v1", "watchlist_id": "a6-source-recertification",
            "categories": [{"category_id": "a6", "label": "A6", "instruments": [
                {"symbol": "2330", "market": "twse", "instrument_type": "equity", "preferred_sources": ["TWSE_MIS"], "enabled": True},
                {"symbol": "6488", "market": "tpex", "instrument_type": "equity", "preferred_sources": ["TWSE_MIS"], "enabled": True},
            ]}]}
        result = execute_live_observation(watchlist, write_latest=False, timeout=15, allow_individual_fallback=False)
        summary = {"status": result.get("status"), "observation_count": len(result.get("observations", [])),
            "failure_count": len(result.get("failures", [])), "batch_status": result.get("source_investigation_notes", [{}])[-1].get("batch_request_status") if result.get("source_investigation_notes") else None}
        return _classify_result(summary, empty_ok=True), summary
    if sid in {"P02", "P03"}:
        if sid == "P02":
            from scripts.m8a_twse_official_eod_adapter import fetch_twse_official_eod_json, parse_twse_official_eod_rows
            rows, status, ctype = fetch_twse_official_eod_json(timeout=15)
            result = parse_twse_official_eod_rows(rows, requested_symbols=["2330"], http_status=status)
        else:
            from scripts.m8a_tpex_official_eod_adapter import fetch_tpex_official_eod_json, parse_tpex_official_eod_rows
            rows, status, ctype = fetch_tpex_official_eod_json(timeout=15)
            result = parse_tpex_official_eod_rows(rows, requested_symbols=["6488"], http_status=status)
        return ("CONFORMING_WITH_UNCERTAINTY" if result.get("batch_status") == "empty_non_trading_day" else _classify_result(result, empty_ok=True)), {"batch_status": result.get("batch_status"), "row_count": result.get("row_count_received"), "content_type": ctype}
    if sid in {"P04", "P05", "P06", "P07"}:
        from scripts.phase_g.research_executor import ROUTES, fetch_once, normalize_source_rows
        routes = list(ROUTES.items())
        (capability, market), route = routes[sequence - 4]
        primary_rate_limited = False
        def fetch(url: str):
            nonlocal primary_rate_limited
            if url == route["json_url"] and primary_rate_limited:
                # A6 containment: a governed alternate cannot evade primary 429.
                raise RuntimeError("a6_alternate_blocked_after_rate_limit")
            from urllib.request import Request, urlopen
            from urllib.error import HTTPError
            try:
                with urlopen(Request(url, method="GET"), timeout=15) as response:
                    body = response.read()
                    if response.status != 200:
                        raise RuntimeError("http_status")
                    return body
            except HTTPError as exc:
                if url == route["csv_url"] and exc.code == 429:
                    primary_rate_limited = True
                raise
        result = fetch_once(route, fetch, fetch)
        normalized = normalize_source_rows(route, result.transport, result.rows)
        records = [row for row in controller.dispatch_ledger if row["source_contract_id"] == sid]
        primary = records[0] if records else {}
        alternate = records[1] if len(records) > 1 else {}
        primary_status = primary.get("http_status")
        primary_outcome = ("http_degraded" if primary_status is not None and not 200 <= primary_status < 300
                           else "transport_degraded" if primary.get("transport_outcome") == "transport_failure"
                           else "valid")
        primary_failures = result.attempt_failures
        primary_contract_drift = any(
            failure.get("transport") == "official_csv" and str(failure.get("failure", "")).startswith("csv_")
            for failure in primary_failures
        )
        if primary_contract_drift:
            verdict = "CONTRACT_DRIFT_OBSERVED"
        elif primary_outcome != "valid":
            verdict = "TRANSPORT_OR_HTTP_DEGRADED"
        else:
            verdict = "CONFORMING_WITH_UNCERTAINTY" if not normalized else "CONFORMING"
        return verdict, {"transport": result.transport, "fallback_attempted": result.fallback_attempted,
            "alternate_dispatch_attempted": len(records) > 1, "primary_outcome": primary_outcome,
            "primary_http_status": primary_status, "alternate_outcome": "valid" if alternate else "not_dispatched",
            "alternate_http_status": alternate.get("http_status"), "primary_contract_drift": primary_contract_drift,
            "primary_failure_reasons": primary_failures, "row_count": len(normalized), "capability": capability, "market": market}
    if sid in {"P08", "P09", "P10"}:
        from server.services.phase_h_h1_tpex_composite import SOURCES, _decode_payload, _validate_source_rows, official_get
        from server.services.phase_h_trading_status_adapters import normalize_representative_tpex_h1_component
        source = SOURCES[sequence - 8]
        response = official_get(source["endpoint"], timeout_seconds=60)
        rows = _decode_payload(response)
        target = {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}
        _validate_source_rows(source, rows, target)
        normalized = normalize_representative_tpex_h1_component(source["source_id"], rows, target, observed_at=response.get("retrieved_at", _now()), citation_id=f"a6:{sid}")
        semantic = "CONFORMING_WITH_UNCERTAINTY" if not rows or normalized.get("status") == "no_evidence_in_covered_scope" else "CONFORMING"
        return semantic, {"row_count": len(rows), "normalized_status": normalized.get("status"), "source_id": source["source_id"]}
    if sid == "P11":
        from server.services.phase_h_h2_twse_exright_executor import ENDPOINT, _decode_rows, official_get_once
        from server.services.phase_h_corporate_action_adapters import normalize_twse_twt48u_all
        response = official_get_once(timeout_seconds=15)
        rows = _decode_rows(response)
        normalized = normalize_twse_twt48u_all(rows, {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}, observed_at=response.get("retrieved_at", _now()), citation_id="a6:P11")
        return ("CONFORMING_WITH_UNCERTAINTY" if normalized["status"] == "no_evidence_in_covered_scope" else "CONFORMING"), {"row_count": len(rows), "status": normalized["status"], "endpoint": ENDPOINT}
    if sid == "P12":
        from server.services.phase_h_h3_twse_stock_day_adapter import fetch_twse_stock_day_month
        result = fetch_twse_stock_day_month(target={"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}, instrument_family="company_share", instrument_type="common_share", requested_month="2026-10", retrieved_at=_now(), timeout_seconds=15, max_response_bytes=4 * 1024 * 1024, http_get=lambda request, timeout: _open_request(request, timeout))
        if result.status == "source_failed":
            return "CONTRACT_DRIFT_OBSERVED", {"status": result.status, "error_code": result.error_code, "month": result.requested_month}
        return ("CONFORMING_WITH_UNCERTAINTY" if result.status in {"not_yet_available", "no_evidence_in_covered_scope", "missing"} else "CONFORMING"), {"status": result.status, "month": result.requested_month, "error_code": result.error_code}
    if sid in {"P13", "P14", "P15"}:
        from server.services.phase_i_i1_production_candidate import SOURCE_DESCRIPTORS, _fetch_source, _selected_fmtqik, _selected_twse_breadth
        source_ids = ["I1-TWSE-FMTQIK-OPENAPI", "I1-TWSE-BREADTH-TWTAZU-OPENAPI", "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]
        source_id = source_ids[sequence - 13]
        observed = _fetch_source(source_id, retrieved_at=_now(), transport=lambda url, timeout: _read_response(url, timeout))
        if observed.error_code and observed.error_code != "unavailable:no_rows":
            return "CONTRACT_DRIFT_OBSERVED", {"error_code": observed.error_code, "http_status": observed.http_status}
        if observed.rows and sequence == 13: _selected_fmtqik(observed.rows)
        if observed.rows and sequence == 14: _selected_twse_breadth(observed.rows)
        return ("CONFORMING_WITH_UNCERTAINTY" if not observed.rows else "CONFORMING"), {"row_count": len(observed.rows), "source_id": source_id, "endpoint": SOURCE_DESCRIPTORS[source_id]["url"]}
    if sid == "P16":
        from server.services.phase_i_i2_production_transport import acquire_taifex_once
        from server.services.phase_i_i2_index_futures_adapters import normalize_taifex_tx_payload
        acquired = acquire_taifex_once(transport=lambda url, timeout: _read_response(url, timeout))
        normalized = normalize_taifex_tx_payload(acquired.body, governed_retrieved_at=acquired.retrieved_at,
            fmtqik_benchmark_date=None, citation_ids=["a6:P16"], transport={"http_status": acquired.http_status,
            "content_type": acquired.content_type, "response_byte_count": acquired.response_byte_count,
            "response_sha256": acquired.response_sha256, "retrieved_at": acquired.retrieved_at,
            "get_count": acquired.get_count, "retry_count": acquired.retry_count,
            "raw_payload_persisted": False})
        status = normalized.get("status")
        verdict = "CONFORMING_WITH_UNCERTAINTY" if status in {"unavailable", "binding_failed", "source_failed"} else "CONFORMING"
        return verdict, {"http_status": acquired.http_status, "content_type": acquired.content_type,
            "response_bytes": acquired.response_byte_count, "retry_count": acquired.retry_count,
            "selected_status": status, "selected_period": normalized.get("contract_period")}
    if sid in {"P17", "P18"}:
        from server.services.phase_i_i3_production_transport import acquire_once
        from server.services.phase_i_i3_cash_institutional_flow_adapters import load_frozen_contract, prepare_market_source
        market = "TWSE" if sid == "P17" else "TPEX"
        acquired = acquire_once(market, resolved_source_trade_date="2026-10-15" if market == "TWSE" else None)
        prepared = prepare_market_source(market, acquired.body, twse_governed_source_date="20261015" if market == "TWSE" else None, contract=load_frozen_contract())
        if prepared.error_code:
            return "CONTRACT_DRIFT_OBSERVED", {"error_code": prepared.error_code, "row_count": prepared.row_count}
        code = "2330" if market == "TWSE" else "6488"
        matching = prepared.index.get(code, [])
        return ("CONFORMING_WITH_UNCERTAINTY" if not matching else "CONFORMING"), {"row_count": prepared.row_count, "target_rows": len(matching), "reported_date": prepared.trade_date}
    if sid.startswith("B"):
        from scripts.m8r_06_01b_materialize_production_inputs import (
            MANIFEST_PATH, _tpex_delisted_request, SCHEMA_DIR,
        )
        from scripts.phase_l_a6_live_dispatch_guard import A6BootstrapBudgetAdapter
        skill_scripts = ROOT / "skills" / "tw-security-master-classifier" / "scripts"
        sys.path.insert(0, str(skill_scripts))
        try:
            from probe_sources import load_manifest, find_source_contract, probe
            from common import file_sha256
            manifest = load_manifest(MANIFEST_PATH)
            source_names = ["twse_isin_mode2_zh", "twse_isin_mode4_zh", "twse_delisted", "tpex_delisted", "twse_etn_expired"]
            source_id = source_names[sequence - 19]
            url = item.route
            try:
                contract = find_source_contract(manifest, source_id, url)
            except ValueError:
                contract = find_source_contract(manifest, None, url)
            kwargs: dict[str, Any] = {}
            method = item.method
            if source_id == "tpex_delisted":
                url, body, content_type = _tpex_delisted_request(manifest)
                kwargs.update(method="POST", body=body, content_type=content_type)
            result = probe(url, manifest["allowed_hosts"], contract=contract, timeout=20, save_raw=None,
                dispatch_budget=A6BootstrapBudgetAdapter(controller, logical_sequence=sequence),
                max_followed_redirects=0, **kwargs)
            status = result.get("http_status")
            if result.get("acquisition_status") in {"data", "schema_drift", "semantic_error"}:
                verdict = "CONFORMING" if result.get("acquisition_status") == "data" else "CONTRACT_DRIFT_OBSERVED"
            else:
                verdict = "TRANSPORT_OR_HTTP_DEGRADED" if status and status != 200 else "CONFORMING_WITH_UNCERTAINTY"
            return verdict, {"source_id": source_id, "acquisition_status": result.get("acquisition_status"),
                "http_status": status, "redirect_count": result.get("redirect_count"),
                "dispatch_reservations": result.get("dispatch_reservations"), "raw_saved": False}
        finally:
            sys.path.remove(str(skill_scripts))
    raise DispatchBlocked("a6_source_binding_missing")


def _open_request(request: Any, timeout: float):
    from urllib.request import urlopen
    return urlopen(request, timeout=timeout)


def _bounded(value: Any) -> Any:
    """Strip raw payload bodies from nested production return values."""
    if isinstance(value, Mapping):
        return {str(k): _bounded(v) for k, v in value.items() if str(k).lower() not in {"raw_bytes", "body", "payload", "raw_payload"}}
    if isinstance(value, (list, tuple)):
        return [_bounded(v) for v in value[:100]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value[:300] if isinstance(value, str) else value
    return type(value).__name__


def _classify_result(value: Any, *, empty_ok: bool = False) -> str:
    text = json.dumps(_bounded(value), ensure_ascii=False, default=str).lower()
    if any(token in text for token in ("schema_drift", "contract_invalid", "identity_mismatch", "duplicate_ambiguous")):
        return "CONTRACT_DRIFT_OBSERVED"
    if any(token in text for token in ("source_failed", "failed_closed", "batch_rows_rejected")):
        return "CONFORMING_WITH_UNCERTAINTY" if empty_ok else "TRANSPORT_OR_HTTP_DEGRADED"
    return "CONFORMING"


def _apply_transport_precedence(
    provisional_verdict: str,
    contract_outcome: str,
    semantic_outcome: str,
    bounded_detail: Mapping[str, Any],
    logical_dispatch_records: list[Mapping[str, Any]],
) -> tuple[str, str, str, str]:
    """Prefer observed physical transport facts over adapter error labels.

    This is a pure classification helper: it does not inspect clocks, payloads,
    or perform acquisition. Contract drift is retained only when a successful
    HTTP response exists in this logical source's dispatch records.
    """
    del bounded_detail  # Kept in the contract for source-specific future evidence.
    records = logical_dispatch_records
    all_transport_failed = bool(records) and all(
        row.get("transport_outcome") == "transport_failure" and row.get("http_status") is None
        for row in records
    )
    if all_transport_failed:
        return "TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed", "transport_failure"

    successful_response = any(
        row.get("transport_outcome") == "http_response"
        and isinstance(row.get("http_status"), int)
        and 200 <= row["http_status"] < 300
        for row in records
    )
    if provisional_verdict == "CONTRACT_DRIFT_OBSERVED" and not successful_response:
        projection = "http_response" if any(row.get("http_status") is not None for row in records) else "unknown"
        return "TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed", projection

    projection = "http_response" if any(row.get("http_status") is not None for row in records) else (
        "transport_failure" if records and all(row.get("transport_outcome") == "transport_failure" for row in records)
        else "unknown"
    )
    return provisional_verdict, contract_outcome, semantic_outcome, projection


def _validate_reservation(path: Path | None, *, repo: Path = ROOT, run_dir: Path | None = None) -> dict[str, Any]:
    if path is None or not path.is_file():
        raise DispatchBlocked("A6_LIVE_RESERVATION_NOT_FINALIZED")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DispatchBlocked("A6_LIVE_RESERVATION_NOT_FINALIZED") from exc
    execution_dir = (run_dir or path.parent).resolve()
    if path.parent.resolve() != execution_dir or path.name != "authority_reservation.json":
        raise DispatchBlocked("a6_authority_reservation_path_invalid")
    expected = {"authority_id": "USER_CHAT_2026-10-16_PHASE_L_L3_A6_BOUNDED_LIVE_SOURCE_DRIFT_RECERTIFICATION_AUTHORIZATION",
                "state": "RESERVED_NOT_CONSUMED", "pre_network_head": _git("rev-parse", "HEAD"),
                "pre_network_tree": _git("rev-parse", "HEAD^{tree}"), "logical_count": 23,
                "physical_ceiling": 27, "P17_trade_date": "2026-10-15"}
    if any(value.get(k) != v for k, v in expected.items()):
        raise DispatchBlocked("a6_authority_reservation_binding_invalid")
    if value.get("live_authority_consumed") is not False or value.get("planned_run_id") != execution_dir.name:
        raise DispatchBlocked("a6_authority_reservation_binding_invalid")
    try:
        plan_path = Path(value["source_plan_path"]).resolve()
        matrix_path = Path(value["transport_matrix_path"]).resolve()
        manifest_path = Path(value["pre2_manifest_path"]).resolve()
        plan_path.relative_to(repo.resolve())
        matrix_path.relative_to(repo.resolve())
        manifest_path.relative_to(repo.resolve())
        if (_sha_file(plan_path) != value.get("source_plan_sha256")
                or _sha_file(matrix_path) != value.get("transport_matrix_sha256")
                or _sha_file(manifest_path) != value.get("pre2_manifest_sha256")):
            raise ValueError("reservation_digest_mismatch")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_base = {key: item for key, item in manifest.items() if key != "manifest_sha256"}
        if (manifest.get("manifest_sha256") != _canonical_sha(manifest_base)
                or manifest.get("manifest_sha256") != value.get("pre2_manifest_canonical_sha256")):
            raise ValueError("reservation_manifest_mismatch")
        for row in manifest.get("files", []):
            artifact = (manifest_path.parent / row["path"]).resolve()
            artifact.relative_to(manifest_path.parent.resolve())
            if not artifact.is_file() or _sha_file(artifact) != row.get("sha256"):
                raise ValueError("reservation_manifest_file_changed")
        expected_ids = [f"P{i:02d}" for i in range(1, 19)] + [f"B{i:02d}" for i in range(1, 6)]
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        sources = plan.get("sources")
        entries = matrix.get("entries")
        if (not isinstance(sources, list) or [item.get("source_contract_id") for item in sources] != expected_ids
                or [item.get("logical_sequence", item.get("sequence")) for item in sources] != list(range(1, 24))
                or plan.get("logical_count", plan.get("logical_plan_count")) != 23
                or plan.get("physical_ceiling", plan.get("absolute_physical_ceiling")) != 27
                or plan.get("P17_trade_date", plan.get("p17_trade_date")) != "2026-10-15"
                or not isinstance(entries, list) or len(entries) != 23
                or {item.get("source_contract_id") for item in entries} != set(expected_ids)
                or _canonical_sha(sources) != _canonical_sha(plan_json())
                or _canonical_sha(entries) != _canonical_sha(contract_matrix())):
            raise ValueError("reservation_plan_invalid")
        manifest_files = {row.get("path"): row.get("sha256") for row in manifest.get("files", [])}
        for artifact in (plan_path, matrix_path):
            if manifest_files.get(artifact.relative_to(manifest_path.parent).as_posix()) != _sha_file(artifact):
                raise ValueError("reservation_artifact_not_manifest_bound")
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise DispatchBlocked("a6_authority_reservation_artifact_binding_invalid") from exc
    tracked = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=repo).returncode
    if tracked != 0:
        raise DispatchBlocked("a6_worktree_tracked_changes_before_live")
    allowed_root = execution_dir
    for line in _git("status", "--porcelain", "--untracked-files=all").splitlines():
        rel = line[3:].strip().strip('"')
        candidate = (repo / rel).resolve()
        if candidate != allowed_root and allowed_root not in candidate.parents:
            raise DispatchBlocked("a6_worktree_unrelated_untracked_before_live")
    if path.parent.joinpath("authority_consumed.json").exists():
        raise DispatchBlocked("a6_authority_already_consumed")
    return value


def _overall(results: list[dict[str, Any]]) -> str:
    verdicts = [row["verdict"] for row in results]
    if "CONTRACT_DRIFT_OBSERVED" in verdicts: return "SOURCE_CHANGED"
    if "SKIPPED_AFTER_RATE_LIMIT" in verdicts or "NOT_EXECUTED" in verdicts: return "INCONCLUSIVE"
    if "TRANSPORT_OR_HTTP_DEGRADED" in verdicts: return "PARTIAL"
    return "PASS"


def run(*, mode: str, run_dir: Path, reservation: Path | None = None,
        response_factory: Callable[[str, str], tuple[int, bytes, Mapping[str, str]]] | None = None) -> dict[str, Any]:
    if mode not in {"offline", "live"}:
        raise ValueError("a6_mode_invalid")
    plan = build_plan()
    matrix = contract_matrix()
    if len(plan) != 23 or len(matrix) != 23:
        raise DispatchBlocked("A6_PREFLIGHT_SOURCE_PLAN_MISMATCH")
    reservation_value = None
    if mode == "live":
        reservation_value = _validate_reservation(reservation, run_dir=run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    consumed_path = run_dir / "authority_consumed.json"
    if mode == "offline":
        # This ephemeral reservation is simulation state in the OS temp area;
        # it is never emitted as a governed live reservation or retained.
        sim_root = Path(tempfile.mkdtemp(prefix="a6-pre2-sim-"))
        reservation_path = sim_root / "simulation-reservation.json"
        _atomic_json(reservation_path, {"authority_id": "USER_CHAT_2026-10-16_PHASE_L_L3_A6_BOUNDED_LIVE_SOURCE_DRIFT_RECERTIFICATION_AUTHORIZATION", "state": "RESERVED_NOT_CONSUMED", "pre_network_head": "SIMULATED_OFFLINE", "pre_network_tree": "SIMULATED_OFFLINE"})
        consumed_path = sim_root / "authority_consumed.json"
        controller = A6DispatchController(plan, reservation_path=reservation_path, consumed_path=consumed_path,
            expected_head="SIMULATED_OFFLINE", expected_tree="SIMULATED_OFFLINE", actual_head="SIMULATED_OFFLINE", actual_tree="SIMULATED_OFFLINE", live_enabled=True)
        fake = _FakeOpener(response_factory or _default_offline_response)
        original_open = OpenerDirector.open
        OpenerDirector.open = lambda opener, fullurl, data=None, timeout=None: fake.open(opener, fullurl, data, timeout)
    else:
        fake = None
        consumed_path = (reservation.parent / "authority_consumed.json") if reservation is not None else run_dir / "authority_consumed.json"
        controller = A6DispatchController(plan, reservation_path=reservation, consumed_path=consumed_path,
            expected_head=reservation_value["pre_network_head"], expected_tree=reservation_value["pre_network_tree"],
            actual_head=_git("rev-parse", "HEAD"), actual_tree=_git("rev-parse", "HEAD^{tree}"), live_enabled=True)
        original_open = None
    results: list[dict[str, Any]] = []
    try:
        with controller.install_urllib_guard():
            for sequence, item in enumerate(plan, start=1):
                if item.hostname in controller.suppressed_hosts:
                    controller.skip_after_rate_limit(sequence)
                    results.append({"sequence": sequence, "source_contract_id": item.source_contract_id, "verdict": "SKIPPED_AFTER_RATE_LIMIT", "reason": "same_host_rate_limit"})
                    continue
                controller.begin_logical(sequence)
                before = len(controller.dispatch_ledger)
                semantic = "unknown"
                contract = "unknown"
                try:
                    with controller.production_source_scope(sequence):
                        verdict, detail = _invoke_source(sequence, controller, run_dir)
                    contract = "valid" if verdict in {"CONFORMING", "CONFORMING_WITH_UNCERTAINTY"} else "invalid"
                    semantic = "no_evidence_in_covered_scope" if verdict == "CONFORMING_WITH_UNCERTAINTY" else "available"
                except DispatchBlocked:
                    raise
                except Exception as exc:
                    records = controller.dispatch_ledger[before:]
                    last = records[-1] if records else None
                    if last and last.get("http_status") is not None and not 200 <= last["http_status"] < 300:
                        verdict, contract, semantic = "TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed"
                    elif isinstance(exc, (TimeoutError, OSError)) or str(getattr(exc, "code", "")).startswith("source_failed:transport"):
                        verdict, contract, semantic = "TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed"
                    else:
                        verdict, contract, semantic = "CONTRACT_DRIFT_OBSERVED", "invalid", "source_failed"
                    detail = {"failure_class": type(exc).__name__}
                    if hasattr(exc, "code") and isinstance(getattr(exc, "code"), str):
                        detail["failure_code"] = exc.code[:100]
                    if hasattr(exc, "attempts") and isinstance(getattr(exc, "attempts"), list):
                        detail["attempt_failures"] = _bounded(exc.attempts)
                records = controller.dispatch_ledger[before:]
                if records and records[-1].get("http_status") is not None:
                    observed_status = records[-1]["http_status"]
                    if observed_status == 429 or observed_status == 404 or observed_status == 410 or observed_status >= 500:
                        verdict, contract, semantic = "TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed"
                if item.source_contract_id in {"P04", "P05", "P06", "P07"} and records:
                    primary = records[0]
                    primary_status = primary.get("http_status")
                    primary_degraded = (primary_status is not None and not 200 <= primary_status < 300) or primary.get("transport_outcome") == "transport_failure"
                    primary_drift = bool(detail.get("primary_contract_drift")) or any(
                        row.get("transport") == "official_csv" and str(row.get("failure", "")).startswith("csv_")
                        for row in detail.get("attempt_failures", [])
                    )
                    detail.setdefault("primary_http_status", primary_status)
                    detail.setdefault("alternate_dispatch_attempted", len(records) > 1)
                    if len(records) > 1:
                        detail.setdefault("alternate_http_status", records[1].get("http_status"))
                    detail.setdefault("primary_outcome", "http_degraded" if primary_degraded else "contract_drift" if primary_drift else "valid")
                    detail.setdefault("alternate_outcome", "valid" if len(records) > 1 and records[1].get("http_status") == 200 else "degraded" if len(records) > 1 else "not_dispatched")
                    if primary_drift:
                        verdict, contract, semantic = "CONTRACT_DRIFT_OBSERVED", "invalid", "source_failed"
                    elif primary_degraded:
                        verdict, contract, semantic = "TRANSPORT_OR_HTTP_DEGRADED", "not_evaluated", "source_failed"
                records = controller.dispatch_ledger[before:]
                verdict, contract, semantic, transport_projection = _apply_transport_precedence(
                    verdict, contract, semantic, detail, records
                )
                if verdict not in VERDICTS:
                    raise DispatchBlocked("a6_source_verdict_invalid")
                status = records[-1].get("http_status") if records else None
                retry_raw = records[-1].get("retry_after_raw") if records else None
                response_empty = detail.get("row_count") == 0
                if response_empty and semantic == "available":
                    semantic = "no_evidence_in_covered_scope"
                try:
                    observation = observe_source_attempt(source_contract_id=item.source_contract_id, observed_at=_now(), http_status=status,
                        retry_after=retry_raw, transport_outcome=transport_projection,
                        contract_outcome=contract, semantic_outcome=semantic, response_form="empty_collection" if response_empty else "unknown",
                        empty_response_policy="allowed" if response_empty else "unknown",
                        target_binding="absent" if detail.get("target_rows") == 0 else "unknown",
                        requested_period="2026-10" if item.source_contract_id == "P12" else None)
                except ValueError as exc:
                    raise DispatchBlocked(f"a6_drift_observation_invalid:{item.source_contract_id}:{semantic}:empty={detail.get('row_count')}:targets={detail.get('target_rows')}:{exc}") from exc
                controller.end_logical(verdict=verdict)
                results.append({"sequence": sequence, "source_contract_id": item.source_contract_id, "verdict": verdict,
                    "bounded_detail": _bounded(detail), "drift_observation": observation.as_dict()})
    finally:
        if mode == "offline" and original_open is not None:
            OpenerDirector.open = original_open
    result = {"mode": "SIMULATED_OFFLINE" if mode == "offline" else "LIVE", "run_id": run_dir.name,
        "logical_planned": 23, "logical_adjudicated": len(results), "physical_dispatches": controller.physical_dispatch_count,
        "physical_ceiling": 27, "source_results": results, "overall_disposition": _overall(results),
        "authority_consumed": bool(controller.authority_consumed_at) if mode == "live" else False,
        "simulation_latch_exercised": bool(controller.authority_consumed_at) if mode == "offline" else False,
        "raw_provider_bodies_persisted": False}
    _atomic_json(run_dir / "dispatch_ledger.json", {"mode": result["mode"], "entries": controller.dispatch_ledger})
    _atomic_json(run_dir / "source_results.json", {"mode": result["mode"], "entries": results})
    _atomic_json(run_dir / "result.json", result)
    manifest_files = [p for p in sorted(run_dir.glob("*.json")) if p.name != "manifest.json"]
    manifest = {"mode": result["mode"], "files": [{"path": p.name, "sha256": _sha_file(p)} for p in manifest_files]}
    manifest["manifest_sha256"] = _canonical_sha(manifest)
    _atomic_json(run_dir / "manifest.json", manifest)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline-simulate", action="store_true")
    mode.add_argument("--execute-live", action="store_true")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--reservation", type=Path)
    args = parser.parse_args()
    if args.execute_live and args.reservation is None:
        raise SystemExit("A6_LIVE_RESERVATION_NOT_FINALIZED")
    result = run(mode="live" if args.execute_live else "offline", run_dir=args.run_dir.resolve(), reservation=args.reservation.resolve() if args.reservation else None)
    print(json.dumps({"overall_disposition": result["overall_disposition"], "logical_adjudicated": result["logical_adjudicated"], "physical_dispatches": result["physical_dispatches"], "mode": result["mode"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
