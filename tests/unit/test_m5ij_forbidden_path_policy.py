from scripts.run_m5ij_end_to_end_acceptance import classify_forbidden_path_changes


def test_allows_authorized_frontend_xss_remediation():
    changed = {
        "frontend/public/index.html",
        "tests/unit/test_frontend_static_security.py",
        "docs/reviews/M7E_PREFLIGHT_REPO_HEALTH_AUDIT.md",
    }

    classification = classify_forbidden_path_changes(changed)

    assert classification["unauthorized_forbidden_paths"] == []
    assert classification["authorized_exceptions"] == ["frontend/public/index.html"]
    assert classification["frontend_public_changes"] == ["frontend/public/index.html"]


def test_blocks_other_frontend_public_files():
    classification = classify_forbidden_path_changes({"frontend/public/bundle.js"})

    assert classification["unauthorized_forbidden_paths"] == ["frontend/public/bundle.js"]
    assert classification["authorized_exceptions"] == []


def test_blocks_generated_staging_and_credential_paths():
    changed = {
        "research/generated/latest_summary.json",
        "research/staging/m5c/candidate.json",
        "credentials/token.json",
    }

    classification = classify_forbidden_path_changes(changed)

    assert "research/generated/latest_summary.json" in classification["unauthorized_forbidden_paths"]
    assert "research/staging/m5c/candidate.json" in classification["unauthorized_forbidden_paths"]
    assert "credentials/token.json" in classification["unauthorized_forbidden_paths"]
    assert classification["authorized_exceptions"] == []


def test_blocks_mixed_frontend_public_changes():
    changed = {"frontend/public/index.html", "frontend/public/other.js"}

    classification = classify_forbidden_path_changes(changed)

    assert "frontend/public/index.html" in classification["unauthorized_forbidden_paths"]
    assert "frontend/public/other.js" in classification["unauthorized_forbidden_paths"]
    assert classification["authorized_exceptions"] == []
