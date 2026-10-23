"""Build-time path leakage scan for native distribution payloads.

Wheel evidence is taken from decompressed members only; compressed-byte matches
are deliberately not authoritative.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import zipfile
from pathlib import PurePosixPath
from typing import Any


_ROOT = str(Path(__file__).resolve().parent)
_EXCEPTIONS = json.loads(
    open(_ROOT + "\\upstream-path-exceptions.json", encoding="utf-8").read()
)["wheels"]
_PATH_RE = re.compile(r"(?i)(?<![A-Za-z0-9_])([A-Z]:(?:\\+|/(?!/))[^\s\"'<>|`\x00-\x1f]*)")
_HOST_TOKENS = tuple(
    token.lower().replace("/", "\\")
    for token in (
        r"C:\twmarket_temp",
        r"C:\Users\weitang",
        r"D:\Codex-Workspace",
    )
)


def _path_matches(data: bytes) -> list[str]:
    texts = [data.decode("utf-8", errors="replace")]
    for encoding, signature in [('utf-16-le', b':\x00'), ('utf-16-be', b'\x00:')]:
        if signature in data:
            texts.append(data.decode(encoding, errors='replace'))
    return list(dict.fromkeys(m.rstrip(".,;:)]}") for text in texts for m in _PATH_RE.findall(text)))


def _unsafe_member(name: str, info: zipfile.ZipInfo) -> bool:
    p = PurePosixPath(name.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or ':' in name or name.startswith(("/", "\\")):
        return True
    # Unix mode symlink bit; symlinks are not valid portable wheel evidence.
    return ((info.external_attr >> 16) & 0o170000) == 0o120000


def _result(*, status: str, classification: str, matches: list[dict[str, Any]],
            wheel_hash: str | None = None, wheel_name: str | None = None,
            member_hashes: dict[str, str] | None = None,
            unsafe_members: list[str] | None = None,
            violations: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "classification": classification,
        "blocking": status == "FAIL",
        "matches": matches,
        "wheel_name": wheel_name,
        "wheel_sha256": wheel_hash,
        "member_hashes": member_hashes or {},
        "unsafe_members": unsafe_members or [],
        "violations": violations or [],
    }


def scan_payload(path: str, data: bytes) -> dict[str, Any]:
    """Scan a first-party payload or wheel and return auditable evidence."""
    wheel_name = path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    is_wheel = wheel_name.lower().endswith(".whl")
    matches: list[dict[str, Any]] = []
    member_hashes: dict[str, str] = {}
    unsafe: list[str] = []
    violations: list[str] = []
    wheel_hash = hashlib.sha256(data).hexdigest() if is_wheel else None
    exact = is_wheel and wheel_name in _EXCEPTIONS
    if is_wheel:
        try:
            archive = zipfile.ZipFile(__import__("io").BytesIO(data))
            with archive:
                for info in archive.infolist():
                    if _unsafe_member(info.filename, info):
                        unsafe.append(info.filename)
                        continue
                    member = archive.read(info)
                    member_hashes[info.filename] = hashlib.sha256(member).hexdigest()
                    for value in _path_matches(member):
                        matches.append({"member": info.filename, "path": value})
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            violations.append(f"invalid_wheel:{type(exc).__name__}")
    else:
        for value in _path_matches(data):
            matches.append({"member": None, "path": value})

    if unsafe:
        violations.append("unsafe_zip_member")
    if is_wheel and exact and wheel_hash != _EXCEPTIONS[wheel_name]:
        violations.append("exact_exception_hash_mismatch")

    for item in matches:
        normalized = re.sub(r'\\+', r'\\', item["path"].lower().replace("/", "\\"))
        if any(token in normalized for token in _HOST_TOKENS):
            violations.append("host_path_leakage")
        elif normalized.startswith('d:\\') and not (is_wheel and exact):
            violations.append("absolute_path_literal")
        # Generic platform/API examples such as C:\\ or C:\\foo are not this
        # build host's paths. They do not need an exception to section 33's
        # current-host-path gate. D-drive literals remain explicitly gated.

    if violations:
        return _result(status="FAIL", classification="FIRST_PARTY_HOST_PATH_LEAKAGE",
                       matches=matches, wheel_hash=wheel_hash, wheel_name=wheel_name if is_wheel else None,
                       member_hashes=member_hashes, unsafe_members=unsafe, violations=violations)
    if is_wheel and exact and matches:
        return _result(status="PASS", classification=_EXCEPTIONS and "THIRD_PARTY_UPSTREAM_EMBEDDED_PATH_PROVENANCE_EXCEPTION",
                       matches=matches, wheel_hash=wheel_hash, wheel_name=wheel_name,
                       member_hashes=member_hashes)
    return _result(status="PASS", classification="NONE", matches=matches,
                   wheel_hash=wheel_hash, wheel_name=wheel_name if is_wheel else None,
                   member_hashes=member_hashes)
