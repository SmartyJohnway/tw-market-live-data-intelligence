# Historical acceptance archive

This directory retains tests used to reproduce prior milestone or PR gates. It is excluded from ordinary `pytest` discovery by `pytest.ini` and is only executed by `python scripts/run_test_profile.py historical-acceptance --json`.

Failures here usually indicate historical drift in archived evidence, not necessarily a current product regression. Current regressions belong in default-ci/component/full-non-network profiles.
