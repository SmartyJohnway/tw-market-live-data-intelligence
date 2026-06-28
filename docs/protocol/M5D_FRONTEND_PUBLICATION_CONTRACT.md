# M5D Frontend Publication Contract

M5D is request-only and simulation-only in this bundle. It binds to the M5C durable staging package and may describe a proposed `frontend/public` destination, but actual frontend publication is blocked until a separate user authorization is provided.

Required flags: `actual_frontend_publication_authorized=false`, `publication_performed=false`, and `next_required_action=user_authorization`.

## M5E controlled execution extension

The M5E publisher engine is fail-closed by default. `--check-only` and default invocations never write. `--execute-publication` requires exact candidate, lineage, destination, frontend baseline, expiry, acknowledgement, single-use token, unused authorization ID, and false governance flags. In this bundle no real authorization exists, so repository-level execution blocks before any `frontend/public` write.
