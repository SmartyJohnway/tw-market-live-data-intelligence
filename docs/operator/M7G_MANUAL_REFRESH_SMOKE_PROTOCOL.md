# M7G Manual Refresh Smoke Protocol

Status: `m7g_manual_refresh_smoke_protocol_defined`

This protocol is optional and non-blocking for default CI. It is manual-only and must not introduce auto refresh, polling, scheduler behavior, hidden fetch, AI/model calls, DB writes, raw payload exposure, or trading advice.

1. Start local server.
2. Open frontend.
3. Load or use valid safe artifact with TWSE listed and/or TPEx OTC symbols.
4. Build refresh request package.
5. Confirm PREPARE_REFRESH_REQUEST_ONLY.
6. Confirm EXECUTE_CONTROLLED_REFRESH_ONCE.
7. Execute controlled refresh once.
8. Confirm execution report.
9. Confirm returned safe artifact validates.
10. Confirm Load refreshed safe artifact button is disabled unless validation accepted.
11. Click Load refreshed safe artifact.
12. Confirm Rich Fact Browser updates.
13. Confirm AI handoff updates only after explicit load.
14. Confirm no raw payload, no trading advice, no auto refresh.
