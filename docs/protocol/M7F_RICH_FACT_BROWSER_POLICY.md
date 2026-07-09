# M7F Rich Fact Browser Policy

Status:
- policy_and_catalog_defined

Purpose:
- Establish M7F as a rich fact browser, operator workbench, and AI discussion handoff foundation.
- Ensure M7F is not summary-only.
- Allow broad display of parsed, governed, project-validated rich facts.
- Prevent raw endpoint payload exposure and trading-advice language.

Core principle:
- Useful project-validated rich facts should be displayable even when official per-field documentation is incomplete or unavailable.
- Official per-field documentation is not required for every displayable field, because many TWSE MIS source fields do not have official semantic documentation.
- Field-level provenance, confidence, and caveats are preferred over suppressing useful fields.

Display philosophy:
- Do not hide useful parsed fields merely because they are not officially field-verified.
- Do not display uncontrolled raw payloads.
- Do not convert market facts into trading advice.
- Do not claim real-time SLA.
- Do not imply full-market breadth, sector rotation, or capital flow.

Operator view:
- Can show broad field-level facts.
- Can show project-validated and source-observed fields.
- Must show caveats and confidence.
- Must distinguish field display from trading advice.

AI handoff view:
- Can include many rich facts, not just summaries.
- Must include currentness/calendar caveats.
- Must include no-trading-advice guardrails.
- Must exclude raw forbidden fields.

Raw forbidden fields:
- raw endpoint payload
- raw TWSE MIS payload
- raw rich facts object
- twse_mis_rich_facts raw object
- raw_unknown_facts
- full_ladder
- bid_prices raw arrays
- ask_prices raw arrays
- response_sample
- raw_fields_sample
- source_investigation_notes

Allowed with classification:
- parsed scalar fields
- parsed source-observed fields
- project-validated derived fields
- semantic-inferred fields
- unit-caveated fields
- currentness/calendar/source-health fields
- field availability metadata

Forbidden positive claims:
- buy / sell / hold recommendation
- trading signal
- target price
- support / resistance
- capital flow
- sector rotation
- full-market breadth
- market prediction

Use exactly this semantic stance:

Expose rich facts broadly, but label them.
Do not suppress useful fields by default.
Do not expose uncontrolled raw payloads.
