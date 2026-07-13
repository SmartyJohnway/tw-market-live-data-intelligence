# M8C-01 full non-network validation

Base SHA: `00760f0a4cb06ac9455d5210da3556863eb691c2`.
Tested runtime SHA: `280f9d2b34a14d9b51db2d44cd492c8873e865a0`.
Validation date: July 13, 2026.
Command: `python scripts/run_test_profile.py full-non-network --json`.

## Exact run counts

| Revision | Collected | Selected | Passed | Skipped | Deselected | Failed |
|---|---:|---:|---:|---:|---:|---:|
| Base `00760f0a4cb06ac9455d5210da3556863eb691c2` | 1270 | 1269 | 1261 | 1 | 1 | 7 |
| Tested runtime `280f9d2b34a14d9b51db2d44cd492c8873e865a0` | 1281 | 1280 | 1272 | 1 | 1 | 7 |

The failure set is identical between base and tested runtime. No new M8/M8C failure was introduced.

## Identical known failure set

1. `tests/unit/test_m5d_frontend_publication_preflight.py::test_m5d_request_is_request_only`
2. `tests/unit/test_m5d_publication_candidate.py::test_candidate_validates`
3. `tests/unit/test_m5d_publication_candidate.py::test_frontend_public_baseline_recomputed_matches_current`
4. `tests/unit/test_m5d_publication_candidate.py::test_destination_already_exists_simulation`
5. `tests/unit/test_m5d_publication_candidate.py::test_rollback_no_existing_destination_deletes_new_file`
6. `tests/unit/test_m5d_publication_candidate.py::test_shallow_checkout_missing_pr57_commit_does_not_block`
7. `tests/unit/test_m5e_controlled_frontend_publication.py::test_reproducibility_materialize_candidate`

`failure_set_identical=true`; `new_m8_or_m8c_failures=[]`.
