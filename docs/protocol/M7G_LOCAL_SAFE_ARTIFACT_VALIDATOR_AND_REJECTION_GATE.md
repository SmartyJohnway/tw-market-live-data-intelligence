# M7G Local Safe Artifact Validator and Rejection Gate

Status: `local_safe_artifact_validator_rejection_gate_defined`

The canonical validator returns accepted/rejected validation status, `safe_to_render`, `safe_for_ai_handoff`, raw forbidden detection, and operator-safe errors. Rejection summary contains keys/reasons only, not raw values.

The validator validates already-loaded dictionaries only. It performs no network, no backend, no AI/model call, and no DB write. It does not read files and does not mutate artifacts.
