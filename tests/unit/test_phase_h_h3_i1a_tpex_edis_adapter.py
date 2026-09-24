"""Synthetic, fixture-only byte-contract tests for the dormant TPEx EDIS adapter."""

from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker

from scripts.validate_phase_h_v3_contracts import validate_recent_performance_semantics
from server.services.phase_h_h3_tpex_edis_adapter import (
    EDIS_DATA_RECORD_BYTES,
    EDIS_HEADER_BYTES,
    normalize_tpex_edis_daily_quote,
)
from server.services.phase_h_recent_performance import build_recent_performance_evidence


ROOT = Path(__file__).resolve().parents[2]
TARGET = {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"}
RETRIEVED = "2026-09-24T00:00:00+08:00"


def _price(raw: str = "000012345") -> bytes:
    return raw.encode("ascii")


def data_record(*, code: str = "6488", close: str = "000012345", volume: str = "000000001234") -> bytes:
    code_field = code.ljust(6).encode("ascii")
    # Multibyte CP950 text is deliberately opaque to the parser; it occupies
    # exactly 16 source bytes and is not used as target identity.
    name = "測試股票".encode("cp950").ljust(16, b" ")
    prices = [_price(), _price(), _price(), _price(close)] + [_price() for _ in range(9)]
    body = (
        code_field + name + b"".join(prices[:4]) + b"+"
        + b"".join(prices[4:]) + volume.encode("ascii")
        + b"00000001" + b"000000000001" + b"0000000000001"
        + b"00000000000001" + b"01" + b"Y" + b"000000000000001"
    )
    assert len(body) == 217
    return body + b"\r\n"


def payload(*records: bytes, trading_date: str = "20260923", production_time: str = "1745", declared_length: str = "219", declared_count: str | None = None, trailing: bytes = b"") -> bytes:
    count = len(records) if declared_count is None else declared_count
    header = (
        trading_date.encode("ascii") + production_time.encode("ascii")
        + declared_length.encode("ascii") + f"{count:0>5}".encode("ascii")
        + b" " * 160 + b"\r\n"
    )
    assert len(header) == EDIS_HEADER_BYTES
    return header + b"".join(records) + trailing


def parse(data: bytes, *, variant: str = "S37", target: dict = TARGET):
    return normalize_tpex_edis_daily_quote(
        data,
        variant=variant,
        target=target,
        retrieved_at=RETRIEVED,
        citation_ids=[f"synthetic-edis-{variant}-{data[0:8].decode('ascii', errors='ignore')}"],
    )


@pytest.mark.parametrize(("variant", "contract"), [("S37", "TPEX_EDIS_S37"), ("S38", "TPEX_EDIS_S38")])
def test_valid_variants_bind_exact_target_and_preserve_distinct_provenance(variant: str, contract: str) -> None:
    result = parse(payload(data_record()), variant=variant)
    assert result.status == "available"
    assert result.source_contract_id == contract
    assert result.trade_date == "2026-09-23"
    assert result.production_time == "1745"
    assert result.observation == {
        **TARGET,
        "trade_date": "2026-09-23",
        "close": 1.2345,
        "volume": 1234,
        "source_family": "TPEX_EDIS",
        "source_contract_id": contract,
        "retrieved_at": RETRIEVED,
        "citation_ids": [f"synthetic-edis-{variant}-20260923"],
    }


def test_name_is_not_used_for_binding_and_target_absence_is_scoped_no_evidence() -> None:
    other = parse(payload(data_record(code="2330 ")))
    assert other.status == "no_evidence_in_covered_scope"
    assert other.observation is None


def test_wrong_market_target_is_binding_failure() -> None:
    wrong = {"canonical_target_id": "TWSE:6488", "market": "TWSE", "security_code": "6488"}
    result = parse(payload(data_record()), target=wrong)
    assert result.status == "binding_failed"
    assert result.error_code == "binding_failed:target_identity_mismatch"


def test_duplicate_exact_target_rows_fail_closed() -> None:
    result = parse(payload(data_record(), data_record(close="000012346")))
    assert result.status == "binding_failed"
    assert result.error_code == "duplicate_exact_target_rows"


@pytest.mark.parametrize(
    ("data", "error"),
    [
        (b"", "source_failed:truncated_header"),
        (payload(data_record(), declared_length="218"), "source_failed:invalid_declared_record_length"),
        (payload(data_record(), declared_count="00002"), "source_failed:record_count_mismatch"),
        (payload(data_record()[:-2]), "source_failed:record_count_mismatch"),
        (payload(data_record(), trailing=b"X"), "source_failed:record_count_mismatch"),
        (payload(data_record(), trading_date="20260230"), "source_failed:invalid_header_date"),
        (payload(data_record(), trading_date="2026-923"), "source_failed:invalid_header_date"),
        (payload(data_record(), production_time="2460"), "source_failed:invalid_production_time"),
    ],
)
def test_malformed_header_and_record_framing_fail_closed(data: bytes, error: str) -> None:
    result = parse(data)
    assert result.status == "source_failed"
    assert result.error_code == error


@pytest.mark.parametrize(
    ("record", "error"),
    [
        (data_record(close="0000 2345"), "source_failed:invalid_numeric_price"),
        (data_record(volume="00000000A234"), "source_failed:invalid_numeric_volume"),
        (data_record(volume="-00000001234"), "source_failed:invalid_numeric_volume"),
        (data_record()[:-1] + b"X", "source_failed:invalid_record_framing"),
    ],
)
def test_malformed_price_volume_and_terminal_fail_closed(record: bytes, error: str) -> None:
    result = parse(payload(record))
    assert result.status == "source_failed"
    assert result.error_code == error


def test_all_data_records_are_validated_even_when_target_is_absent() -> None:
    malformed_other_code = data_record(code="2330 ", close="0000 2345")
    result = parse(payload(malformed_other_code))
    assert result.status == "source_failed"
    assert result.error_code == "source_failed:invalid_numeric_price"


def test_synthetic_daily_file_observations_feed_h3_i0_builder() -> None:
    observations = []
    for index, closing in enumerate(("000010000", "000011000")):
        trading_day = date(2026, 9, 21) + timedelta(days=index)
        result = parse(
            payload(data_record(close=closing), trading_date=trading_day.strftime("%Y%m%d")),
            variant="S38" if index else "S37",
        )
        assert result.status == "available"
        observations.append(result.observation)
    end_date = date(2026, 9, 23)
    end_result = parse(payload(data_record(close="000012000"), trading_date=end_date.strftime("%Y%m%d")), variant="S38")
    assert end_result.status == "available"
    schema = json.loads((ROOT / "schemas/recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8"))
    evidence = build_recent_performance_evidence(
        target=TARGET,
        observations=observations,
        governed_end_observation=end_result.observation,
        requested_observations=2,
        baseline_lookbacks=(2,),
        current_volume_basis="completed_session",
        schema=schema,
    )
    assert not list(Draft7Validator(schema, format_checker=FormatChecker()).iter_errors(evidence))
    validate_recent_performance_semantics(evidence)
    assert evidence["coverage_status"] == "complete"
    assert evidence["baselines"][0]["recent_return_pct"] == pytest.approx(20)
