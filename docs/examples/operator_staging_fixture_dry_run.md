# Operator staging fixture dry run

Use local fixtures only. Example: `pytest -m "not network" tests/unit/test_staging_payload_fixture_corpus.py`. Temporary output, if needed, must go under a shell tmp directory and be cleaned up. No live probe, no production write, no frontend/public write, and no trading signal.
