"""Stage a Docker build context from committed A3 resource-policy Git blobs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = "ee316f784831fe684e21fa8d146512d96a888050"
A5_BASE = "d5dac702c25e9728db86e9ef32f4fe8185086b89"
sys.path.insert(0, str(ROOT))
from packaging_native.path_scan import scan_payload


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def _safe_relative(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts or ":" in value or "\\" in value:
        raise ValueError(f"unsafe committed resource path: {value}")
    return path.as_posix()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _secret_shaped(data: bytes) -> bool:
    return bool(re.search(
        rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
        rb"sk-[A-Za-z0-9]{32,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)",
        data,
    ))


def build_context(wheelhouse: Path, output: Path, *, acceptance_base: str | None = None) -> dict:
    status = _git("status", "--porcelain", "--untracked-files=all").decode().splitlines()
    if acceptance_base is not None:
        if acceptance_base != A5_BASE or _git("rev-parse", "origin/main").decode().strip() != A5_BASE:
            raise ValueError("L6_A5_ENTRY_BASE_DRIFT")
        if status:
            raise ValueError("committed Docker source must have a clean worktree")
        subprocess.run(["git", "merge-base", "--is-ancestor", A5_BASE, "HEAD"], cwd=ROOT, check=True)
        if _git("rev-list", "--merges", A5_BASE + "..HEAD").strip():
            raise ValueError("A5 source must retain linear lineage from exact entry")
        commit = _git("rev-parse", "HEAD").decode().strip()
        tree = _git("rev-parse", "HEAD^{tree}").decode().strip()
    elif _git("rev-parse", "origin/main").decode().strip() != BASE:
        raise ValueError("L6_A4_ENTRY_BASE_DRIFT")
    else:
        subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT, check=True)
        commit = _git("rev-parse", "HEAD").decode().strip()
    if acceptance_base is not None:
        pass
    elif commit == BASE:
        if any(line.startswith("??") or line[1] not in " " for line in status):
            raise ValueError("pre-commit Docker context requires all candidate files staged with no unstaged or untracked files")
        staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, check=False)
        if staged.returncode != 1:
            raise ValueError("pre-commit Docker context requires a verifiable staged candidate tree")
        tree = _git("write-tree").decode().strip()
    else:
        if status:
            raise ValueError("committed Docker source must have a clean worktree")
        parents = _git("rev-list", "--parents", "-n", "1", commit).decode().split()
        if parents != [commit, BASE]:
            raise ValueError("committed Docker source must be a direct child of the exact authorized base")
        tree = _git("rev-parse", f"{commit}^{{tree}}").decode().strip()
    if output.exists():
        raise ValueError("context output already exists; choose a fresh C: path")

    lock = json.loads(_git("show", f"{tree}:packaging_docker/dependency-lock-linux-amd64-cp313.json"))
    requirements = _git("show", f"{tree}:packaging_docker/requirements-linux-amd64-cp313.txt")
    lock_bytes = _git("show", f"{tree}:requirements-lock.txt")
    if lock.get("source_requirements_sha256") != _sha(lock_bytes):
        raise ValueError("Docker dependency lock no longer matches requirements-lock.txt")
    if lock.get("platform") != "linux/amd64" or lock.get("python") != "CPython 3.13":
        raise ValueError("Docker dependency platform authority mismatch")
    artifacts = lock.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != lock.get("artifact_count"):
        raise ValueError("Docker dependency lock malformed")
    expected = {row["wheel_filename"]: row["sha256"] for row in artifacts}
    if len(expected) != len(artifacts):
        raise ValueError("duplicate wheel identity in Docker lock")
    observed = {}
    wheel_files = sorted(wheelhouse.glob("*.whl"))
    for wheel in wheel_files:
        if wheel.is_symlink() or not wheel.is_file():
            raise ValueError("wheelhouse contains a non-regular member")
        digest = _sha(wheel.read_bytes())
        if expected.get(wheel.name) != digest:
            raise ValueError(f"Docker wheel hash differs from committed exact artifact lock: {wheel.name}")
        observed[wheel.name] = digest
        with zipfile.ZipFile(wheel) as archive:
            for info in archive.infolist():
                member = PurePosixPath(info.filename.replace("\\", "/"))
                if member.is_absolute() or ".." in member.parts or ":" in info.filename:
                    raise ValueError(f"unsafe wheel member: {wheel.name}:{info.filename}")
    if observed != expected:
        raise ValueError("Docker wheelhouse is incomplete or contains extras")

    output.mkdir(parents=True)
    (output / "app").mkdir()
    entries = json.loads(_git("show", f"{tree}:packaging_native/resource-policy.json"))["members"]
    payload_records = []
    destinations: set[str] = set()
    for entry in entries:
        destination = _safe_relative(entry["destination"])
        if not destination.startswith("app/"):
            continue
        source = _safe_relative(entry["source"])
        if destination.casefold() in destinations:
            raise ValueError(f"duplicate app destination: {destination}")
        destinations.add(destination.casefold())
        mode = _git("ls-tree", tree, "--", source).split(None, 1)[0]
        if mode not in {b"100644", b"100755"}:
            raise ValueError(f"runtime resource is not a committed regular file: {source}")
        data = _git("show", f"{tree}:{source}")
        scan = scan_payload(destination, data)
        if scan["blocking"] or _secret_shaped(data):
            raise ValueError(f"blocked first-party Docker payload: {destination}")
        target = output / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        blob = _git("rev-parse", f"{tree}:{source}").decode().strip()
        payload_records.append({"source": source, "git_blob": blob, "destination": destination,
                                "role": entry["role"], "bytes": len(data), "sha256": _sha(data)})

    files = {
        "Dockerfile": "packaging_docker/Dockerfile",
        "compose.yaml": "packaging_docker/compose.yaml",
        "requirements-linux-amd64-cp313.txt": "packaging_docker/requirements-linux-amd64-cp313.txt",
        "dependency-lock-linux-amd64-cp313.json": "packaging_docker/dependency-lock-linux-amd64-cp313.json",
    }
    for target_name, source in files.items():
        data = _git("show", f"{tree}:{source}")
        (output / target_name).write_bytes(data)
    wheel_out = output / "wheelhouse"
    wheel_out.mkdir()
    for wheel in wheel_files:
        shutil.copyfile(wheel, wheel_out / wheel.name)
    metadata = {
        "schema_version": 1,
        "candidate_commit": None if commit == BASE else commit,
        "candidate_head_base": commit,
        "candidate_tree": tree,
        "application_source_tree": tree,
        "entry_base_commit": BASE,
        "entry_base_tree": _git("rev-parse", f"{BASE}^{{tree}}").decode().strip(),
        "resource_policy_sha256": _sha(_git("show", f"{tree}:packaging_native/resource-policy.json")),
        "dependency_lock_sha256": _sha(_git("show", f"{tree}:packaging_docker/dependency-lock-linux-amd64-cp313.json")),
        "requirements_sha256": _sha(requirements),
        "application_member_count": len(payload_records),
        "application_members": sorted(payload_records, key=lambda row: row["destination"]),
        "wheel_count": len(wheel_files),
        "wheel_artifacts": [{"filename": name, "sha256": observed[name]} for name in sorted(observed)],
    }
    (output / "build-metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "PASS", "context": str(output), "candidate_commit": metadata["candidate_commit"],
            "candidate_tree": tree, "application_member_count": len(payload_records),
            "wheel_count": len(wheel_files), "dependency_lock_sha256": metadata["dependency_lock_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--acceptance-base", choices=[A5_BASE])
    args = parser.parse_args()
    try:
        result = build_context(args.wheelhouse.resolve(), args.output.resolve(), acceptance_base=args.acceptance_base)
    except (OSError, ValueError, subprocess.CalledProcessError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
