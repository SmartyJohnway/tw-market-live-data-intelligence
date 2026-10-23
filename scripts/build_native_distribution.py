"""Build Package C from a clean committed tree and an exact offline wheel set.

Git is used only here, at build time. Runtime files are selected by a reviewed
exact-file role allowlist, never by copying and pruning a checkout.
"""
from __future__ import annotations

import argparse
import email
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packaging_native.bootstrap.package_integrity import canonical_digest, verify_bundle, _safe_relative
from packaging_native.path_scan import scan_payload

BASE = "911a841b866795e8d0cd83d80b30b34701aa5980"
A5_BASE = "d5dac702c25e9728db86e9ef32f4fe8185086b89"
PROFILE = "native-package-c-windows-cp313-x64"
FORBIDDEN = {".git", ".github", "tests", "acceptance_runs", "__pycache__", ".pytest_cache", ".venv", "venv", "data", "artifacts", "node_modules", ".env"}
RUNTIME_GOVERNANCE_EXCEPTION = "app/docs/governance/phase_i/PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-c", "core.hooksPath=NUL", *args], cwd=ROOT)


def normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def dependency_authority() -> dict[str, str]:
    """The accepted lock is exact; its only marker is Windows pywin32."""
    result = {}
    for line in (ROOT / "requirements-lock.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        requirement, *markers = line.split(";")
        if markers and markers != [' sys_platform == "win32"']:
            raise ValueError("unreviewed dependency marker")
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)", requirement.strip())
        if not match:
            raise ValueError("dependency authority must remain exactly pinned")
        name, version = match.groups()
        key = normalized_name(name)
        if key in result:
            raise ValueError("duplicate dependency authority")
        result[key] = version
    return result


def inspect_wheels(wheelhouse: Path) -> list[dict]:
    expected = dependency_authority()
    authority = wheel_hash_authority()
    observed = {}
    records = []
    for wheel in sorted(wheelhouse.iterdir()):
        if not wheel.is_file() or wheel.is_symlink() or wheel.suffix != ".whl":
            raise ValueError("wheelhouse contains a non-wheel member")
        if authority.get(wheel.name) != digest(wheel.read_bytes()):
            raise ValueError('wheel bytes differ from committed PyPI artifact authority')
        with zipfile.ZipFile(wheel) as archive:
            metadata_names = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
            if len(metadata_names) != 1:
                raise ValueError("ambiguous wheel metadata")
            metadata = email.message_from_bytes(archive.read(metadata_names[0]))
        name, version = normalized_name(metadata["Name"]), metadata["Version"]
        if name in observed or expected.get(name) != version:
            raise ValueError(f"dependency drift: {name}")
        observed[name] = version
        python_tag, abi_tag, platform_tag = wheel.stem.rsplit("-", 3)[-3:]
        if platform_tag not in {"any", "win_amd64"}:
            raise ValueError("non-Windows-x64 wheel")
        compatible = (abi_tag == 'none' and bool(set(python_tag.split('.')) & {'py3', 'py313'}))
        compatible |= python_tag == 'cp313' and abi_tag == 'cp313' and platform_tag == 'win_amd64'
        compatible |= (bool(re.fullmatch(r'cp3\d+', python_tag)) and abi_tag == 'abi3'
                       and 32 <= int(python_tag[2:]) <= 313 and platform_tag == 'win_amd64')
        if not compatible:
            raise ValueError('wheel does not support CPython 3.13 x64')
        records.append({"name": name, "version": version, "wheel_filename": wheel.name,
                        "wheel_sha256": digest(wheel.read_bytes()), "python_tag": python_tag,
                        "abi_tag": abi_tag, "platform_tag": platform_tag,
                        "source_dependency_authority": "app/requirements-lock.txt"})
    if observed != expected:
        raise ValueError("L6_A3_DEPENDENCY_CLOSURE_BLOCKED: incomplete wheel set")
    return records


def wheel_hash_authority() -> dict[str, str]:
    authority = json.loads((ROOT / 'packaging_native/wheelhouse-lock.json').read_text())
    if authority['requirements_lock_sha256'] != digest((ROOT / 'requirements-lock.txt').read_bytes()):
        raise ValueError('dependency authority changed; regenerate and review artifact lock')
    wheels = authority['wheels']
    result = {row['wheel_filename']: row['sha256'] for row in wheels}
    if len(result) != len(wheels):
        raise ValueError('duplicate wheel artifact authority')
    return result


def check_member(path: str, data: bytes) -> None:
    _safe_relative(path)
    parts = path.lower().split("/")
    if any(p in FORBIDDEN for p in parts) or ("docs/governance/" in path.lower() and path != RUNTIME_GOVERNANCE_EXCEPTION):
        raise ValueError(f"forbidden package member: {path}")
    if parts[-1] in {"installation.json", "settings.json", "auth.json", "handoff.md", "roadmap.md", "project.md"}:
        raise ValueError(f"state or governance member: {path}")
    # Scan bytes without logging matching contents. Wheels are opaque dependency
    # archives; their own members are scanned separately below.
    scan = scan_payload(path, data)
    if scan['blocking']:
        raise ValueError(f"host-path leakage in {path}")
    if re.search(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{32,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)", data):
        raise ValueError(f"secret-shaped payload in {path}")


def build(output: Path, wheelhouse: Path, *, acceptance_base: str | None = None) -> dict:
    if git("status", "--porcelain", "--untracked-files=all").strip():
        raise ValueError("final build requires clean committed source")
    base = BASE
    if acceptance_base is not None:
        if acceptance_base != A5_BASE or git('rev-parse', 'origin/main').decode().strip() != A5_BASE:
            raise ValueError('L6_A5_ENTRY_BASE_DRIFT')
        base = A5_BASE
    subprocess.run(["git", "merge-base", "--is-ancestor", base, "HEAD"], cwd=ROOT, check=True)
    if git('rev-list', '--merges', base + '..HEAD').strip():
        raise ValueError('candidate must retain a linear clean reimplementation from exact A2')
    commit = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    version = git("show", "HEAD:VERSION").decode().strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?", version):
        raise ValueError("invalid product VERSION")
    bundle = output / f"TW-Market-{version}-windows-x64"
    archive_path = output / (bundle.name + ".zip")
    if bundle.exists() or archive_path.exists():
        raise ValueError("output already exists; use a fresh output directory")
    policy = json.loads(git("show", "HEAD:packaging_native/resource-policy.json"))
    dependencies = inspect_wheels(wheelhouse)
    payload: dict[str, tuple[bytes, str]] = {}
    for entry in policy["members"]:
        source = _safe_relative(entry["source"])
        target = _safe_relative(entry["destination"])
        if target.casefold() in {p.casefold() for p in payload}:
            raise ValueError("duplicate inclusion destination")
        mode = git("ls-tree", "HEAD", "--", source).split(None, 1)[0]
        if mode not in {b"100644", b"100755"}:
            raise ValueError(f"source must be a tracked regular file: {source}")
        payload[target] = (git("show", "HEAD:" + source), entry["role"])
    for dep in dependencies:
        name = dep["wheel_filename"]
        payload["wheelhouse/" + name] = ((wheelhouse / name).read_bytes(), "dependency")
    payload["dependency-manifest.json"] = (json.dumps({"schema_version": 1, "dependencies": dependencies}, indent=2, sort_keys=True).encode(), "metadata")
    requirements = "".join(f"{d['name']}=={d['version']} --hash=sha256:{d['wheel_sha256']}\n" for d in dependencies)
    payload["bootstrap/requirements-wheelhouse.txt"] = (requirements.encode(), "metadata")
    scans = []
    for path, (data, _) in payload.items():
        check_member(path, data)
        report = scan_payload(path, data)
        if report['matches']:
            scans.append({'relative_path': path, **report})
    manifest = {"schema_version": 1, "product_name": "TW-Market", "product_version": version,
                "source_commit": commit, "source_tree": tree, "target_os": "windows", "target_arch": "x64",
                "python_requirement": "CPython 3.13 x64", "package_profile": PROFILE,
                "member_count": len(payload), "members": [
                    {"relative_path": p, "role": role, "bytes": len(data), "sha256": digest(data)}
                    for p, (data, role) in sorted(payload.items())]}
    manifest["manifest_canonical_sha256"] = canonical_digest(manifest)
    payload["distribution-manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True).encode(), "metadata")
    bundle.mkdir(parents=True)
    for path, (data, _) in payload.items():
        target = bundle / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    verify_bundle(bundle)
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, (data, _) in sorted(payload.items()):
            info = zipfile.ZipInfo(bundle.name + "/" + path, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return {"filename": archive_path.name, "bytes": archive_path.stat().st_size,
            "sha256": digest(archive_path.read_bytes()), "source_commit": commit, "source_tree": tree,
            "manifest_canonical_sha256": manifest["manifest_canonical_sha256"],
            "member_count": len(payload), "manifested_member_count": manifest["member_count"],
            "wheel_count": len(dependencies), "product_version": version, 'path_scan_evidence': scans}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--acceptance-base", choices=[A5_BASE])
    args = parser.parse_args()
    print(json.dumps(build(args.output.resolve(), args.wheelhouse.resolve(), acceptance_base=args.acceptance_base), indent=2))
