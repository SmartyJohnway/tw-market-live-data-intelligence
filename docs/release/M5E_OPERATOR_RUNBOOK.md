# M5E Controlled Frontend Publication Runbook

This bundle is a fail-closed preparation system only. It does not authorize or perform publication.

## Preflight
Run `python scripts/run_m5e_controlled_frontend_publication.py --check-only` and confirm `ready_for_explicit_user_authorization_review=true`, `frontend_publication_authorized=false`, `publication_performed=false`, `execute_mode_available=false`, and `production_ready=false`.

## Future authorization review
A future explicit authorization must validate against `docs/authorization/m5e_publication_authorization_decision_schema.json` and bind the exact M5D candidate manifest hash, M5C lineage hashes, destination, baseline hash, expiry, acknowledgement, allowed action, and single-use ID.

## Execution
Repository-level execution remains blocked unless a separate explicit ceremony supplies a valid decision and token. Test execution is limited to `tmp_path`/`TemporaryDirectory` through injectable transaction functions.

## Rollback and recovery
Use the transaction journal to restore a preserved previous file or remove a newly created target. Ambiguous states return `manual_recovery_required` and must preserve evidence.

## Incident handling
Do not delete journal, backup, receipt, or temp evidence until hashes and states are inspected. Do not claim realtime, recommendation, ranking, trading, production, or authorization semantics.
