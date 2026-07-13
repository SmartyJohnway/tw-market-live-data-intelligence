# M8C-01 full non-network validation

Base SHA: `00760f0a4cb06ac9455d5210da3556863eb691c2`.

PR-head validation on July 13, 2026 ran `python scripts/run_test_profile.py full-non-network --json` against tested code containing the M8C-01 runtime hardening. The run collected 1279 tests, selected 1278, passed 1270, skipped 1, deselected 1, and failed only the known seven M5D/M5E frontend-publication baseline drift tests. No new M8/M8C regression was introduced. M8-family focused tests and default CI passed.

Known unchanged failures:

1. `tests/unit/test_m5d_frontend_publication_preflight.py::test_m5d_request_is_request_only`
2. `tests/unit/test_m5d_publication_candidate.py::test_candidate_validates`
3. `tests/unit/test_m5d_publication_candidate.py::test_frontend_public_baseline_recomputed_matches_current`
4. `tests/unit/test_m5d_publication_candidate.py::test_destination_already_exists_simulation`
5. `tests/unit/test_m5d_publication_candidate.py::test_rollback_no_existing_destination_deletes_new_file`
6. `tests/unit/test_m5d_publication_candidate.py::test_shallow_checkout_missing_pr57_commit_does_not_block`
7. `tests/unit/test_m5e_controlled_frontend_publication.py::test_reproducibility_materialize_candidate`
