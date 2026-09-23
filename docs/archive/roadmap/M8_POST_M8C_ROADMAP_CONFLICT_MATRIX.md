# M8 Post-M8C Roadmap Conflict Matrix

Baseline SHA: `bd3496efe7492e6cd3c7dacc169e142f90e6cd92`.

| Finding ID | Current artifact/path | Current declaration | Actual implementation | New roadmap phase | Conflict type | Disposition | Breaking-change risk | Follow-up task |
|---|---|---|---|---|---|---|---|---|
| M8-CONFLICT-001 | docs/data_capabilities/m8_source_capability_registry.json | implemented_through_track ended at M8C | M8R-03E artifacts and tests are present | A | stale registry | corrected_in_r1 | low | none |
| M8-CONFLICT-002 | docs/data_capabilities/m8_source_capability_registry.json | recommended successor pointed to completed M8R-03D | M8R-03D and M8R-03E are present | B | stale successor | corrected_in_r1 | low | none |
| M8-CONFLICT-003 | original M8R-04 references | broad controlled AI conversation handoff active/blocking | M8R-04 was split by M8R-03B/C/D/E and post-M8C roadmap | B-E | obsolete roadmap | superseded | low | R5 documentation consolidation |
| M8-CONFLICT-004 | M8R-03E schemas/artifacts | unsupported/disallowed/prohibited AI-behavior fields remain | compatibility-sensitive schema fields still used by validators/tests | B/C | behavior policy in evidence layer | deprecated_pending_migration | medium | R3 schema/API cleanup |
| M8-CONFLICT-005 | docs/protocol/M8R_03E... | next task M8R-03F | revised architecture needs skill/capability guide first | B | stale next task | corrected by registry and R1 roadmap | low | M8R-03E-F1 |
