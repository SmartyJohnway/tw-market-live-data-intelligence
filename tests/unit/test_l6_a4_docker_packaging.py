from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_docker_dependency_lock_is_exact_linux_subset_of_canonical_pins():
    lock = json.loads((ROOT / "packaging_docker/dependency-lock-linux-amd64-cp313.json").read_text())
    canonical = {}
    for line in (ROOT / "requirements-lock.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        req, *marker = line.split(";")
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)", req.strip())
        assert match
        if marker:
            assert marker == [' sys_platform == "win32"']
            continue
        canonical[re.sub(r"[-_.]+", "-", match.group(1)).lower()] = match.group(2)
    actual = {re.sub(r"[-_.]+", "-", row["name"]).lower(): row["version"] for row in lock["artifacts"]}
    assert actual == canonical
    assert len(lock["artifacts"]) == 48
    assert lock["platform"] == "linux/amd64"
    assert lock["python"] == "CPython 3.13"
    assert lock["source_requirements_sha256"] == hashlib.sha256((ROOT / "requirements-lock.txt").read_bytes()).hexdigest()
    assert all(row["official_sha256_verified"] and not row["yanked"] for row in lock["artifacts"])
    assert lock["embedded_path_review"]["disposition"] == "reviewed_exact_artifacts_no_new_exception_required"
    assert all(row["wheel"] in {a["wheel_filename"] for a in lock["artifacts"]}
               and len(row["sha256"]) == 64 for row in lock["embedded_path_review"]["findings"])
    reviewed = {(row["wheel"], row["sha256"], row["classification"])
                for row in lock["embedded_path_review"]["findings"]}
    assert ("click-8.5.0-py3-none-any.whl", "255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360",
            "THIRD_PARTY_UPSTREAM_DOCUMENTATION_EXAMPLE_NOT_HOST_PATH") in reviewed
    assert ("mcp-1.29.0-py3-none-any.whl", "f5a075bb611f23d6f4d080c6a1699fa62772eebc562ba9e66b306ddde1c755f7",
            "THIRD_PARTY_UPSTREAM_DOCUMENTATION_EXAMPLE_NOT_HOST_PATH") in reviewed


def test_docker_context_uses_the_accepted_exact_file_resource_policy():
    policy = json.loads((ROOT / "packaging_native/resource-policy.json").read_text())
    app_sources = {row["source"] for row in policy["members"] if row["destination"].startswith("app/")}
    assert "scripts/tw_market_docker.py" in app_sources
    builder = (ROOT / "scripts/build_docker_context.py").read_text()
    assert 'f"{tree}:packaging_native/resource-policy.json"' in builder
    assert 'tree = _git("write-tree")' in builder
    assert "shutil.copyfile(wheel" in builder
    assert "COPY . ." not in (ROOT / "packaging_docker/Dockerfile").read_text()
    assert ".git" not in app_sources
    assert not any(source.startswith("tests/") for source in app_sources)
    assert not any("acceptance_runs" in source for source in app_sources)


def test_docker_image_pins_base_and_keeps_runtime_application_read_only():
    dockerfile = (ROOT / "packaging_docker/Dockerfile").read_text()
    assert "python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741" in dockerfile
    assert "--no-index" in dockerfile and "--only-binary=:all:" in dockerfile and "--require-hashes" in dockerfile
    assert "COPY --from=dependencies" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "chmod -R a-w /opt/tw-market/app" in dockerfile
    assert "PYTHONDONTWRITEBYTECODE=\"1\"" in dockerfile


def test_compose_binds_host_only_to_loopback_and_mounts_named_state_volumes():
    compose = (ROOT / "packaging_docker/compose.yaml").read_text()
    assert '"127.0.0.1:${TW_MARKET_DOCKER_HOST_PORT:-8000}:8000"' in compose
    assert "- home:/var/lib/tw-market/home" in compose
    assert "- state:/var/lib/tw-market/state" in compose
    assert "restart: \"no\"" in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert "healthcheck:" in compose
    assert compose.count("    image:") == 1
    assert "mcp" not in compose.lower()
    assert "build:" not in compose
