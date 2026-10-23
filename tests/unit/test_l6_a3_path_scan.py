import hashlib
import io
import json
import zipfile

from packaging_native.path_scan import scan_payload


def _wheel(name: str, member: bytes, compressed_extra: bytes = b"") -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("pkg/data.txt", member)
        if compressed_extra:
            # Incidental bytes outside decompressed member content are not evidence.
            zf.comment = compressed_extra
    return out.getvalue()


def test_first_party_payload_blocks_host_path():
    result = scan_payload("app/config.txt", b"root=C:\\twmarket_temp\\secret")
    assert result["status"] == "FAIL"
    assert result["classification"] == "FIRST_PARTY_HOST_PATH_LEAKAGE"
    assert result["blocking"]


def test_exact_allowlisted_hash_binds_exception_and_member_evidence(monkeypatch):
    import packaging_native.path_scan as module
    name = "pygments-2.21.0-py3-none-any.whl"
    payload = _wheel(name, b"built at D:\\upstream\\builder")
    monkeypatch.setitem(module._EXCEPTIONS, name, hashlib.sha256(payload).hexdigest())
    result = scan_payload(name, payload)
    assert result["status"] == "PASS"
    assert result["classification"] == "THIRD_PARTY_UPSTREAM_EMBEDDED_PATH_PROVENANCE_EXCEPTION"
    assert result["member_hashes"]["pkg/data.txt"] == hashlib.sha256(b"built at D:\\upstream\\builder").hexdigest()


def test_allowlist_does_not_cover_other_wheel():
    name = "other-1.0-py3-none-any.whl"
    result = scan_payload(name, _wheel(name, b"D:\\upstream\\builder"))
    assert result["status"] == "FAIL"


def test_compressed_incidental_bytes_are_not_authority():
    name = "other-1.0-py3-none-any.whl"
    result = scan_payload(name, _wheel(name, b"clean", compressed_extra=b"C:\\twmarket_temp\\incidental"))
    assert result["status"] == "PASS"
    assert result["matches"] == []


def test_exact_wheel_hash_mismatch_fails_even_without_paths():
    name = "pygments-2.21.0-py3-none-any.whl"
    result = scan_payload(name, _wheel(name, b"clean"))
    assert result["status"] == "FAIL"
    assert "exact_exception_hash_mismatch" in result["violations"]
