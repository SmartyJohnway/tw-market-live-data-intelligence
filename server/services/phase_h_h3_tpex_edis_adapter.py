"""Dormant, deterministic TPEx EDIS S37/S38 file normalizer.

This adapter accepts one caller-supplied file payload. It performs no file,
network, clock, cache, or runtime-authority access and never discovers history.
The fixed-width source contract is parsed as bytes so multibyte names cannot
shift field offsets.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Mapping, Sequence


EDIS_HEADER_BYTES = 186
EDIS_DATA_RECORD_BYTES = 219
_HEADER_DATE = slice(0, 8)
_HEADER_TIME = slice(8, 12)
_HEADER_RECORD_LENGTH = slice(12, 15)
_HEADER_RECORD_COUNT = slice(15, 20)
_HEADER_RESERVED = slice(20, 184)
_HEADER_TERMINATOR = slice(184, 186)

# Official V1.33 S37/S38 data row byte positions; terminal CRLF is [217:219].
_CODE = slice(0, 6)
_NAME = slice(6, 22)  # Intentionally not decoded or used for binding.
_PRICE_FIELDS = (
    slice(22, 31), slice(31, 40), slice(40, 49), slice(49, 58),
    slice(59, 68), slice(68, 77), slice(77, 86), slice(86, 95),
    slice(95, 104), slice(104, 113), slice(113, 122), slice(122, 131),
    slice(131, 140),
)
_CLOSE = slice(49, 58)
_VOLUME = slice(140, 152)
_TRANSACTIONS = slice(152, 160)
_TRADING_VALUE = slice(160, 172)
_ISSUED_SHARES = slice(172, 185)
_MARKET_VALUE = slice(185, 199)
_INDUSTRY_CODE = slice(199, 201)
_CONSTITUENT_FLAG = slice(201, 202)
_COMMON_STOCK_CAP = slice(202, 217)


class TPExEDISFormatError(ValueError):
    """Deterministic rejection of an invalid EDIS file or target binding."""


@dataclass(frozen=True)
class TPExEDISResult:
    status: Literal[
        "available", "no_evidence_in_covered_scope", "source_failed", "binding_failed"
    ]
    source_contract_id: str
    trade_date: str | None = None
    production_time: str | None = None
    observation: dict | None = None
    error_code: str | None = None


def _digits(data: bytes, field: str, *, code: str) -> int:
    if not data or any(byte < 48 or byte > 57 for byte in data):
        raise TPExEDISFormatError(code)
    return int(data)


def _valid_target(target: Mapping[str, str]) -> tuple[str, str, str]:
    if not isinstance(target, Mapping) or set(target) != {"canonical_target_id", "market", "security_code"}:
        raise TPExEDISFormatError("binding_failed:invalid_target")
    try:
        canonical = target["canonical_target_id"]
        market = target["market"]
        security_code = target["security_code"]
    except (KeyError, TypeError) as exc:
        raise TPExEDISFormatError("binding_failed:invalid_target") from exc
    if not all(isinstance(part, str) and part for part in (canonical, market, security_code)):
        raise TPExEDISFormatError("binding_failed:invalid_target")
    if market != "TPEX" or canonical != f"TPEX:{security_code}":
        raise TPExEDISFormatError("binding_failed:target_identity_mismatch")
    if not (1 <= len(security_code) <= 6 and security_code.isascii() and security_code.isdigit()):
        raise TPExEDISFormatError("binding_failed:invalid_security_code")
    return canonical, market, security_code


def _date_from_header(raw: bytes) -> str:
    _digits(raw, "header_date", code="source_failed:invalid_header_date")
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8])).isoformat()
    except ValueError as exc:
        raise TPExEDISFormatError("source_failed:invalid_header_date") from exc


def _timestamp(value: str) -> None:
    if not isinstance(value, str):
        raise TPExEDISFormatError("source_failed:invalid_retrieved_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TPExEDISFormatError("source_failed:invalid_retrieved_at") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TPExEDISFormatError("source_failed:retrieved_at_timezone_required")


def _parse_file(payload: bytes) -> tuple[str, str, list[bytes]]:
    if not isinstance(payload, bytes) or len(payload) < EDIS_HEADER_BYTES:
        raise TPExEDISFormatError("source_failed:truncated_header")
    header = payload[:EDIS_HEADER_BYTES]
    if header[_HEADER_TERMINATOR] != b"\r\n" or any(byte != 32 for byte in header[_HEADER_RESERVED]):
        raise TPExEDISFormatError("source_failed:invalid_header_framing")
    trade_date = _date_from_header(header[_HEADER_DATE])
    production_time_bytes = header[_HEADER_TIME]
    _digits(production_time_bytes, "production_time", code="source_failed:invalid_production_time")
    hour, minute = int(production_time_bytes[:2]), int(production_time_bytes[2:])
    if hour > 23 or minute > 59:
        raise TPExEDISFormatError("source_failed:invalid_production_time")
    production_time = f"{hour:02d}{minute:02d}"
    record_length = _digits(header[_HEADER_RECORD_LENGTH], "record_length", code="source_failed:invalid_declared_record_length")
    if record_length != EDIS_DATA_RECORD_BYTES:
        raise TPExEDISFormatError("source_failed:invalid_declared_record_length")
    record_count = _digits(header[_HEADER_RECORD_COUNT], "record_count", code="source_failed:invalid_record_count")
    expected_size = EDIS_HEADER_BYTES + record_count * record_length
    if len(payload) != expected_size:
        raise TPExEDISFormatError("source_failed:record_count_mismatch")
    records: list[bytes] = []
    for index in range(record_count):
        start = EDIS_HEADER_BYTES + index * record_length
        record = payload[start : start + record_length]
        if len(record) != EDIS_DATA_RECORD_BYTES or record[217:219] != b"\r\n":
            raise TPExEDISFormatError("source_failed:invalid_record_framing")
        records.append(record)
    return trade_date, production_time, records


def _decode_security_code(field: bytes) -> str:
    # X(6) text identifiers are left-aligned; only trailing space padding is
    # permitted. Full-market files can contain alphanumeric non-target rows.
    try:
        value = field.decode("ascii")
    except UnicodeDecodeError as exc:
        raise TPExEDISFormatError("source_failed:invalid_security_code_field") from exc
    code = value.rstrip(" ")
    if not code or any(not ("!" <= char <= "~") for char in code):
        raise TPExEDISFormatError("source_failed:invalid_security_code_field")
    if value != code.ljust(6):
        raise TPExEDISFormatError("source_failed:invalid_security_code_field")
    return code


def _validate_data_record(record: bytes) -> tuple[str, float, int]:
    code = _decode_security_code(record[_CODE])
    # The name is an opaque 16-byte field. Its contents never participate in
    # identity binding and need not be decoded to validate its byte width.
    if len(record[_NAME]) != 16:
        raise TPExEDISFormatError("source_failed:invalid_security_name_width")
    for field in _PRICE_FIELDS:
        _digits(record[field], "price", code="source_failed:invalid_numeric_price")
    for field, label in (
        (_VOLUME, "volume"), (_TRANSACTIONS, "transactions"),
        (_TRADING_VALUE, "trading_value"), (_ISSUED_SHARES, "issued_shares"),
        (_MARKET_VALUE, "market_value"), (_COMMON_STOCK_CAP, "common_stock_cap"),
    ):
        _digits(record[field], label, code=f"source_failed:invalid_numeric_{label}")
    # H3 does not consume the change marker. Validate only that the X(1)
    # source field is a printable ASCII byte; do not infer marker semantics.
    if not 0x20 <= record[58] <= 0x7E:
        raise TPExEDISFormatError("source_failed:invalid_change_marker")
    try:
        record[_INDUSTRY_CODE].decode("ascii")
        record[_CONSTITUENT_FLAG].decode("ascii")
    except UnicodeDecodeError as exc:
        raise TPExEDISFormatError("source_failed:invalid_text_field") from exc
    close_decimal = Decimal(_digits(record[_CLOSE], "close", code="source_failed:invalid_numeric_price")).scaleb(-4)
    close = float(close_decimal)
    volume = _digits(record[_VOLUME], "volume", code="source_failed:invalid_numeric_volume")
    return code, close, volume


def normalize_tpex_edis_daily_quote(
    payload: bytes,
    *,
    variant: Literal["S37", "S38"],
    target: Mapping[str, str],
    retrieved_at: str,
    citation_ids: Sequence[str],
) -> TPExEDISResult:
    """Normalize one explicit S37 or S38 payload for one exact target.

    Structurally invalid source data returns ``source_failed``. Invalid target
    identity or duplicate exact target rows returns ``binding_failed``. A valid
    file without the exact code returns only ``no_evidence_in_covered_scope``.
    """
    if not isinstance(variant, str) or variant not in {"S37", "S38"}:
        return TPExEDISResult("source_failed", "TPEX_EDIS_UNKNOWN", error_code="invalid_file_variant")
    contract_id = f"TPEX_EDIS_{variant}"
    try:
        canonical, market, security_code = _valid_target(target)
    except TPExEDISFormatError as exc:
        return TPExEDISResult("binding_failed", contract_id, error_code=str(exc))
    try:
        _timestamp(retrieved_at)
        if not isinstance(citation_ids, Sequence) or isinstance(citation_ids, (str, bytes)) or not citation_ids:
            raise TPExEDISFormatError("source_failed:invalid_citation_ids")
        if any(not isinstance(item, str) or not item.strip() for item in citation_ids):
            raise TPExEDISFormatError("source_failed:invalid_citation_ids")
        if len(set(citation_ids)) != len(citation_ids):
            raise TPExEDISFormatError("source_failed:invalid_citation_ids")
        trade_date, production_time, records = _parse_file(payload)
        matched: list[tuple[float, int]] = []
        for record in records:
            code, close, volume = _validate_data_record(record)
            if code == security_code:
                matched.append((close, volume))
        if len(matched) > 1:
            return TPExEDISResult("binding_failed", contract_id, trade_date, production_time, error_code="duplicate_exact_target_rows")
        if not matched:
            return TPExEDISResult("no_evidence_in_covered_scope", contract_id, trade_date, production_time)
        close, volume = matched[0]
        observation = {
            "canonical_target_id": canonical,
            "market": market,
            "security_code": security_code,
            "trade_date": trade_date,
            "close": close,
            "volume": volume,
            "source_family": "TPEX_EDIS",
            "source_contract_id": contract_id,
            "retrieved_at": retrieved_at,
            "citation_ids": sorted(citation_ids),
        }
        return TPExEDISResult("available", contract_id, trade_date, production_time, observation)
    except TPExEDISFormatError as exc:
        return TPExEDISResult("source_failed", contract_id, error_code=str(exc))
