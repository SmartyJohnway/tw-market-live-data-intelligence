"""Synthetic P3 proof only; no historical payload reconstruction or network."""
from __future__ import annotations

import hashlib
import json
import shutil
import socket
from pathlib import Path

import pytest

from scripts import phase_i_i3_a0_source_transport as transport
from scripts import phase_i_i3_a0_attempt_authority as authority
from scripts.phase_i_i3_a0_future_evidence import source_findings, batching_findings
from scripts import validate_phase_i_i3_a0_attempt3 as historical


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("P3 external network forbidden")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


class Stream:
    status = 200

    def __init__(self, chunks, *, declared=None, transfer_encoding=None):
        self.chunks = list(chunks)
        self.headers = {"Content-Type": "application/json"}
        if declared is not None:
            self.headers["Content-Length"] = declared
        if transfer_encoding:
            self.headers["Transfer-Encoding"] = transfer_encoding
        self.limits = []
        self.closed = False

    def read(self, limit):
        assert 0 < limit <= transport.READ_CHUNK_BYTES
        self.limits.append(limit)
        if not self.chunks:
            return b""
        item = self.chunks.pop(0)
        if isinstance(item, Exception):
            raise item
        if len(item) > limit:
            self.chunks.insert(0, item[limit:])
        return item[:limit]

    def close(self):
        self.closed = True


def acquire(stream, monkeypatch=None):
    calls = []
    class Opener:
        def open(self, request, timeout):
            calls.append((request.full_url, timeout))
            return stream
    telemetry, body = transport.read_once("TPEx", opener_factory=lambda *h: Opener(), now=lambda: "2030-01-01T00:00:00Z")
    assert calls == [(transport.URLS["TPEx"], 30)]
    assert telemetry["retry_count"] == 0
    assert stream.closed
    return telemetry, body


def test_multi_chunk_eof_complete_body_and_hash():
    chunks = [b'[', b' ', b' ', b']']
    result, body = acquire(Stream(chunks))
    assert body == b'[  ]'
    assert result["complete_body_received"] is True
    assert result["response_byte_count"] == 4
    assert result["response_sha256"] == hashlib.sha256(body).hexdigest()


def test_exact_max_boundary_allowed():
    payload = b'[]' + b' ' * (transport.MAX_BYTES - 2)
    result, body = acquire(Stream([payload]))
    assert body == payload and result["complete_body_received"] is True
    assert result["response_byte_count"] == transport.MAX_BYTES


def test_overflow_only_max_plus_one_observed():
    stream = Stream([b' ' * (transport.MAX_BYTES + 100)])
    result, body = acquire(stream)
    assert body is None and result["error_code"] == "response_byte_limit_exceeded"
    assert result["partial_response_byte_count"] == transport.MAX_BYTES + 1
    assert result["response_byte_count"] == 0 and result["response_sha256"] is None
    assert result["complete_body_received"] is False
    assert stream.limits[-1] == 1


@pytest.mark.parametrize("chunks,count,classification", [
    ([ConnectionResetError(10054, "reset")], 0, "connection_reset"),
    ([b'x' * 65536, b'y' * 65536, ConnectionResetError(10054, "reset")], 131072, "connection_reset"),
    ([b'[]', TimeoutError("body timeout")], 2, "timeout"),
])
def test_body_error_partial_telemetry_no_json_or_raw_fragments(chunks, count, classification, monkeypatch):
    def forbidden(*args):
        raise AssertionError("partial bytes must not reach JSON decoder")
    monkeypatch.setattr(transport, "_decode_json", forbidden)
    result, body = acquire(Stream(chunks))
    assert body is None
    assert result["http_status"] == 200 and result["base_mime"] == "application/json"
    assert result["failure_phase"] == "response_body_read"
    assert result["reason_classification"] == classification
    assert result["complete_body_received"] is False
    assert result["partial_response_byte_count"] == count
    assert result["response_byte_count"] == 0 and result["response_sha256"] is None
    assert not any(isinstance(v, (bytes, bytearray)) for v in result.values())
    assert "body timeout" not in json.dumps(result)


def test_parseable_partial_json_still_not_analyzable(monkeypatch):
    monkeypatch.setattr(transport, "_decode_json", lambda *args: pytest.fail("partial JSON decoded"))
    result, body = acquire(Stream([b'[]', ConnectionResetError(10054, "reset")]))
    assert body is None and result["partial_response_byte_count"] == 2
    with pytest.raises(ValueError, match="partial_payload_semantics_forbidden"):
        source_findings({"exact_matches": 0}, complete_body_received=False)


@pytest.mark.parametrize("declared,expected", [("2", None), ("1", "content_length_mismatch"), ("3", "content_length_mismatch")])
def test_content_length_eof_equality(declared, expected):
    result, body = acquire(Stream([b'[]'], declared=declared))
    assert result["declared_content_length"] == int(declared)
    assert result["error_code"] == expected
    assert (body == b'[]') if expected is None else body is None
    if expected:
        assert result["response_byte_count"] == 0 and result["response_sha256"] is None


def test_declared_oversize_rejected_before_body_read():
    stream = Stream([b'[]'], declared=str(transport.MAX_BYTES + 1))
    result, body = acquire(stream)
    assert body is None and result["error_code"] == "response_byte_limit_exceeded"
    assert stream.limits == [] and result["partial_response_byte_count"] == 0


@pytest.mark.parametrize("declared", ["-1", "oops", "1.0", "9" * 100, " 2 ", ""])
def test_invalid_content_length_not_trusted(declared):
    result, body = acquire(Stream([b'[]'], declared=declared))
    assert body == b'[]' and result["declared_content_length"] is None


def test_transfer_encoding_uses_bounded_eof_not_content_length():
    result, body = acquire(Stream([b'[]'], declared="999", transfer_encoding="chunked"))
    assert body == b'[]' and result["declared_content_length"] is None


def test_unacquired_null_is_not_evaluated_zero_and_batching_not_fabricated():
    absent = source_findings(None, complete_body_received=False)
    assert absent["target_binding"] is None and absent["evaluation_status"] == "NOT_EVALUATED"
    assert absent["whole_dataset_arithmetic"] is absent["unit_proof"] is absent["normalized_observation"] is None
    zero = source_findings({"exact_matches": 0, "arithmetic": {}, "unit": "share", "observation": None,
                           "whole_market_payload": True}, complete_body_received=True)
    assert zero["target_binding"] == 0 and zero["evaluation_status"] == "EVALUATED"
    batch = batching_findings({"TWSE": zero, "TPEx": absent}, ["prior-qualified-evidence"])
    assert batch["batching_observation"] == {"TWSE": "PROVEN", "TPEx": "NOT_EVALUATED"}
    assert batch["mixed_market_observation"] == "NOT_EVALUATED"
    assert batch["batching_contract_support"]["prior_evidence_refs"] == ["prior-qualified-evidence"]


@pytest.mark.parametrize("corruption", ["absent", "status", "zero_match", "fresh_tpex", "fresh_mixed"])
def test_historical_erratum_required_and_false_attribution_rejected(tmp_path, corruption):
    for rel in (*historical.HISTORICAL_SHA, historical.ERRATUM_REL):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(historical.ROOT / rel, target)
    historical.validate_erratum(tmp_path)
    path = tmp_path / historical.ERRATUM_REL
    value = json.loads(path.read_text(encoding="utf-8"))
    if corruption == "absent":
        path.unlink()
    else:
        if corruption == "status":
            value["status"] = "IGNORED"
        elif corruption == "zero_match":
            value["defect_a"]["correct_interpretation"] = "ZERO_MATCH"
        else:
            key = "TPEx" if corruption == "fresh_tpex" else "mixed_market"
            value["defect_b"]["fresh_observation"][key] = "PROVEN_BY_ATTEMPT_3"
        path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises((AssertionError, FileNotFoundError)):
        historical.validate_erratum(tmp_path)


def test_v1_historical_valid_v2_explicit_and_attempt4_cannot_use_v1():
    assert authority.load_reviewed_authority_chain()["schema_version"].endswith(".v1")
    chain = authority.load_reviewed_authority_chain(version="v2", attempt_number=4)
    assert chain["schema_version"].endswith(".v2")
    with pytest.raises(ValueError, match="attempt4_requires_explicit_v2"):
        authority.load_reviewed_authority_chain(attempt_number=4)
    with pytest.raises(ValueError, match="attempt4_requires_explicit_v2"):
        authority.build_reservation(owner_authority="synthetic-not-authorized", starting_main="x", branch="x",
                                    branch_head="x", tree="x", max_gets={}, attempt_number=4)


@pytest.mark.parametrize("anchor", ["attempt_3", "attempt_3_reservation", "attempt_3_consumed", "attempt_3_erratum", "p3"])
def test_v2_tampered_anchors_fail_closed(monkeypatch, anchor):
    chain = authority.load_reviewed_authority_chain(version="v2")
    relative = chain["p3_closure_reference"]["path"] if anchor == "p3" else chain["additional_anchors"][anchor]["path"]
    damaged = authority.ROOT / relative
    original = Path.read_bytes
    def tampered(path):
        return b'tampered' if path == damaged else original(path)
    monkeypatch.setattr(Path, "read_bytes", tampered)
    with pytest.raises(ValueError, match="anchor_mismatch"):
        authority.load_reviewed_authority_chain(version="v2")


def test_p3_validator_production_containment_and_readiness():
    from scripts.validate_phase_i_i3_a0_p3 import validate
    assert validate()["decision"] == "P3_PASS"


def test_v2_future_latches_validate_all_added_anchors_without_persisting():
    reservation = authority.build_reservation(owner_authority="synthetic-not-authorized", starting_main="x",
        branch="x", branch_head="x", tree="x", max_gets={"TWSE": 0, "TPEx": 1, "retry": 0},
        version="v2", attempt_number=4)
    consumed = authority.build_consumed_latch(reservation, consumed_at="2030-01-01T00:00:00Z")
    authority.validate_consumed_latch(consumed)
    assert consumed["additional_anchors"] == reservation["additional_anchors"]
    consumed["additional_anchors"] = {}
    with pytest.raises(ValueError, match="consumed_v2_anchors_mismatch"):
        authority.validate_consumed_latch(consumed)


def test_explicit_socket_denial():
    with pytest.raises(AssertionError, match="network forbidden"):
        socket.create_connection(("www.tpex.org.tw", 443))


def test_both_observed_batching_not_based_on_prior_flags():
    observed = source_findings({"exact_matches": 1, "arithmetic": {}, "unit": "share", "observation": {},
                              "whole_market_payload": True}, complete_body_received=True)
    assert batching_findings({"TWSE": observed, "TPEx": observed}, [])["mixed_market_observation"] == "PROVEN"
