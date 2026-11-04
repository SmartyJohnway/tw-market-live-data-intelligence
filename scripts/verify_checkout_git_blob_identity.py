#!/usr/bin/env python3
"""Fail closed when a Windows CI checkout alters canonical Git object bytes.

The sentinel set covers the source artifacts whose SHA-256 authority caused
GHA-WIN-EOL-001. Git cleanliness alone cannot detect CRLF normalization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

SENTINELS = (
    "requirements-lock.txt",
    "docs/acceptance_runs/phase_g_pr_d_p0_ledger.json",
    "tests/fixtures/phase_g_pr_c/v1_mode_c_golden/ai_context/unified_market_evidence_result.v1.json",
    "packaging_docker/dependency-lock-linux-amd64-cp313.json",
    "docs/contracts/schemas/l7_publication_manifest.v1.schema.json",
    "config/first_party_dependency_sbom.json",
)


class CheckoutByteMismatch(ValueError):
    """Working tree bytes disagree with the exact committed blob."""


def git_bytes(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, check=True,
    )
    return result.stdout


def verify_file_bytes(repo: Path, path: str) -> str:
    expected = git_bytes(repo, "show", "HEAD:" + path)
    actual = (repo / path).read_bytes()
    if actual != expected:
        raise CheckoutByteMismatch(
            "checkout_blob_bytes_mismatch:" + path +
            ":blob_sha256=" + hashlib.sha256(expected).hexdigest() +
            ":worktree_sha256=" + hashlib.sha256(actual).hexdigest()
        )
    return hashlib.sha256(actual).hexdigest()


def verify(repo: Path, source_sha: str) -> dict[str, object]:
    if not re.fullmatch(r"[a-f0-9]{40}", source_sha):
        raise ValueError("invalid_source_sha")
    actual_sha = git_bytes(repo, "rev-parse", "HEAD").decode("ascii").strip()
    if actual_sha != source_sha:
        raise ValueError("source_commit_mismatch")
    autocrlf = git_bytes(repo, "config", "--local", "--get", "core.autocrlf").decode("ascii").strip()
    if autocrlf != "false":
        raise ValueError("checkout_core_autocrlf_not_false:" + autocrlf)
    hashes = {path: verify_file_bytes(repo, path) for path in SENTINELS}
    return {"status": "PASS", "source_commit": actual_sha, "core_autocrlf": autocrlf,
            "sentinel_count": len(hashes), "all_git_blob_bytes_match": True,
            "sentinel_sha256": hashes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    try:
        report = verify(args.repo.resolve(), args.source_sha)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
