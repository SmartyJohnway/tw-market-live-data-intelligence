# M8 through M8B full non-network base/head validation

## Purpose

Record reproducible evidence for the M8B-03 consolidated acceptance caveat that `full-non-network` fails because of pre-existing M5D frontend-publication baseline drift, not because of the M8-through-M8B changes.

## Compared revisions

| Revision | SHA / ref | Command |
|---|---|---|
| Clean base | `5353c9817f94e23b078dc107eda147b27c41022d` | `cd /tmp/m8b_base_check && python scripts/run_test_profile.py full-non-network --json` |
| PR head | working branch head with corrective changes | `python scripts/run_test_profile.py full-non-network --json` |

## Results

| Revision | Status | Passed | Failed | Failed tests |
|---|---:|---:|---:|---|
| Clean base | fail | 1221 | 7 | see list below |
| PR head | fail | 1233 | 7 | same list below |

Failed tests on both base and head:

- `tests/unit/test_m5d_frontend_publication_preflight.py::test_m5d_request_is_request_only`
- `tests/unit/test_m5d_publication_candidate.py::test_candidate_validates`
- `tests/unit/test_m5d_publication_candidate.py::test_frontend_public_baseline_recomputed_matches_current`
- `tests/unit/test_m5d_publication_candidate.py::test_destination_already_exists_simulation`
- `tests/unit/test_m5d_publication_candidate.py::test_rollback_no_existing_destination_deletes_new_file`
- `tests/unit/test_m5d_publication_candidate.py::test_shallow_checkout_missing_pr57_commit_does_not_block`
- `tests/unit/test_m5e_controlled_frontend_publication.py::test_reproducibility_materialize_candidate`

## M8-family result

Command: `python -m pytest tests/unit/test_m8*.py -q`

Result: pass, `191 passed`.

## Conclusion

The PR head introduces no new `full-non-network` failures relative to clean base. The consolidated M8-through-M8B status remains `m8_through_m8b_consolidated_acceptance_pass_with_caveats` with the explicit pre-existing M5D full-non-network caveat.
