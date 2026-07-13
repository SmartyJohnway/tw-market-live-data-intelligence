# M8C-01 TAIFEX MIS bounded runtime final acceptance

Final status: `m8c_01_taifex_mis_bounded_snapshot_runtime_pass_with_caveats`.

M8C-01 implements the accepted M8C-00 architecture: same-origin REST bootstrap, ephemeral SockJS XHR polling, exact runtime-symbol subscription, `mode=1` initial quote-state collection, bounded termination, and compact normalized observations. Regular session is the only supported runtime session in this PR.

Caveats and boundaries: after-hours remains disabled unless separately live-validated; cross-midnight semantics remain unresolved; deltas are disabled and unsupported quote modes are counted but ignored; reconnect is disabled (`MAX_RECONNECT_ATTEMPTS=0`); no unsubscribe message is invented; raw payloads, cookies, SockJS session IDs, full option chains, raw QID maps, and `trueValues` are not retained or exposed; AI context, conversation projection, public API, MCP, frontend, scheduler, daemon, DB writes, and trading/recommendation behavior remain disabled until a later task.

Canonical next task: `M8C-02-TAIFEX-MIS-M8-CURRENTNESS-CONTEXT-INTEGRATION-AND-FINAL-ACCEPTANCE`.
