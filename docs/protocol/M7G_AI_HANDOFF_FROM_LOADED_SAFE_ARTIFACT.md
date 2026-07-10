# M7G AI Handoff from Loaded Safe Artifact

Status: `ai_handoff_from_loaded_safe_artifact_defined`

## Purpose

- Route AI handoff through active workbench context.
- If `loaded_safe_artifact` is active, handoff is built from the validated loaded safe artifact.
- If `static_demo` is active, handoff is built from static demo context.
- Handoff source context mode is explicit.
- Handoff includes safe artifact provenance, validation status, currentness/calendar metadata, source health summary, observation count, selected fields, caveats, and governance guardrails.

## Safety

- No AI/model call.
- No backend/API/MCP.
- No runtime network fetch.
- No hidden fetch.
- No refresh execution.
- No automatic clipboard write.
- Raw forbidden fields are not copied.
- Raw payload values are not exposed.
- Handoff remains Not trading advice, not recommendation, not trading signal, not market prediction.

## Source health

- Source health in handoff is artifact-reported metadata only.
- Source health is not a live probe.
- Source health does not imply realtime SLA.
- Missing `source_health` is allowed with caveat.

## Handoff package

The safe handoff package contains `handoff_source`, `artifact_provenance`, `currentness_calendar`, `source_health`, `governance_guardrails`, `selected_fields`, `selected_symbols`, `observations`, and `raw_forbidden_omission_notice`.

Loaded artifact handoff requires accepted validation and `safe_to_render=true`; rejected artifacts never reach handoff and fall back to `static_demo`.

## Downstream

- M7G-09 controlled manual refresh execution remains mandatory downstream work.
- M7G-06 does not execute refresh.
