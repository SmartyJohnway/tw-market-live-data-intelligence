# Developer Onboarding: Local-First

Assumptions: supported CPython 3.11 or 3.13, dependencies installed from the
repository lock, and no credentials committed.

Install the supported core graph in a disposable virtual environment:

```bash
python -m pip install -r requirements-lock.txt
```

Safe commands: `python -m compileall scripts tests`, `pytest -m "not network"`, `python scripts/run_local_delivery_acceptance.py --check-only`.

Unsafe commands: live probes, `scripts/run_all_probes.py`, production refresh, broker/auth activation, writes under frontend/public or research/generated.

Use fixtures from tests/fixtures only as validation examples; do not interpret readonly data as trading signals or current market state.

Troubleshooting: inspect validator errors, forbidden path guard errors, and golden snapshot diffs.

PR body consistency check: use `python scripts/run_ci_delivery_acceptance.py --check-only --pr-body /tmp/pr_body.md --changed-files-file /tmp/changed_files.txt` with locally generated changed-file lists; this command does not require a live git remote.
