# Troubleshooting Guide

Pytest failures: rerun the named non-network test. Fixture validation failures: inspect validator error code and path. Forbidden path failures: choose tmp_path or docs/examples. Frontend package mismatch: regenerate in tmp and compare with golden. CI failures: run compileall, pytest -m "not network", and local acceptance. Stale/delayed caveats and TWSE_MIS risk flag failures indicate missing display or risk metadata. PR body changed-file mismatch means Actual changed files is stale.
