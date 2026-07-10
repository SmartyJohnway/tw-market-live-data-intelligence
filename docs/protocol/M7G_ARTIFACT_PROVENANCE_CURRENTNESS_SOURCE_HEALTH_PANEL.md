# M7G Artifact Provenance Currentness Source Health Panel

Status: artifact_provenance_currentness_source_health_panel_defined

Artifact provenance panel displays artifact_id, schema_version, artifact_type, created_at_utc, generated_by, source_scope, market, timezone, manifest, validation status, and observation count.

Currentness panel displays context-provided currentness/calendar fields only. It displays session_state, freshness_state, currentness_label, calendar_confidence, trading_day_status, calendar caveats, semantic caveats, no_realtime_sla, and not_trading_advice from the loaded safe artifact context.

Source health panel displays artifact-reported source health metadata only.

Source health is not a live probe.
Source health does not imply realtime SLA.
If source_health metadata is missing, UI displays unknown with caveat for missing source_health metadata.

Observation summary displays safe observation counts and governance flags; it does not render raw payloads, raw rich facts, ladders, bid/ask arrays, or source investigation note values.

M7G-09 controlled manual refresh execution remains mandatory downstream work.
M7G-04/05 does not execute refresh.
