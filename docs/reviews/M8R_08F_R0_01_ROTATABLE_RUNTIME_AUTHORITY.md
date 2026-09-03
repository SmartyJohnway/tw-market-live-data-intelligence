# M8R-08F-R0-01 Rotatable Governed Runtime Authority

Historical candidate A, `m8r06-01b-20260807T053540Z`, remains immutable. Its source and runtime seals remain at their accepted M8R-06 review paths, and the production pointer remains unchanged.

Future candidates use the sole accepted identity form `m8r06-01b-YYYYMMDDTHHMMSSZ`. A validated ID deterministically derives its input bundle, runtime index directory, reviewed source seal, and reviewed runtime seal. Callers do not supply arbitrary authority paths.

For a future candidate B, reviewed authorities are stored under `docs/reviews/security_master_candidates/<candidate-id>/` as `source_immutable_manifest.json` and `runtime_identity_immutable_manifest.json`. The local bundle also contains `immutable_manifest.json` as producer-stage metadata. C1B independently reads the reviewed source seal and verifies the complete local bundle before producing compact artifacts and a runtime seal.

C2 retains all existing pointer, containment, hash, schema, coverage, fixture-rejection, fail-closed, and process-lifetime selection checks. It accepts A's one historical runtime-seal path only for A; every valid future ID must use its derived per-candidate runtime-seal path.

R0-01 does not create a real candidate, modify the production pointer, acquire market data, or execute market network activity. Candidate B activation remains a separately reviewed R0-02 decision.
