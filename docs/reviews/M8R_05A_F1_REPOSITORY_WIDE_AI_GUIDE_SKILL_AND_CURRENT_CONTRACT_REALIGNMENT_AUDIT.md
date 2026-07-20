# M8R-05A-F1: Repository-Wide AI Guide, Skill, and Current Contract Realignment Audit

## 1. Executive decision
The project adopts M8R-05A as the canonical AI-facing contract. The AI operates as a **request author and evidence analyst**, generating precisely validated but compositionally flexible requests, and analyzing the resulting exhaustive evidence.

## 2. Audit scope and baseline
- Baseline commit: b9f9effdaa76d1a108ae430085737e4dad3af524
- Scope: A comprehensive >60 artifact scan of M5/M6/M8/M8R schemas, skills, docs, frontend, server, tests, and policies, capturing explicit file SHAs and exact file contents/headers for strict provenance mapping.

## 3. Current product north star
A Unified Market Evidence Workbench where the AI is the request author and evidence analyst. It formulates strictly validated but compositionally flexible M8R-05A JSON requests to express its data needs. The canonical system backend provides exhaustive, objectively bounded evidence execution without AI interpolation or interpretation of the data.

## 4. Repository-wide artifact inventory summary
Identified 65 artifacts including comprehensive traversal of M8R-03C/D/E schemas, M5 workflows, legacy M6 interfaces, and duplicate capability catalogs. Exact evidence paths, blob SHAs, and content headers were extracted.

## 5. M5 model assessment
M5 Mode A/B/C and Level 1/2 were historically coupled with AI intents. They must be remapped. Level 1/2 is purely an evidence lifecycle metadata layer.

## 6. M6 frontend/API/MCP assessment
| Artifact | Current Role | Future Role |
|----------|--------------|-------------|
| frontend/readonly-preview/M5KLocalAIWorkbench.html | Legacy frontend rendering | COMPATIBILITY_ONLY_LEGACY operator view |
| server/main.py | Legacy M5 backend endpoints | COMPATIBILITY_ONLY_LEGACY wrapper |
| docs/reference/MCP_REFERENCE.md | Legacy MCP definitions | COMPATIBILITY_ONLY_LEGACY |

Legacy M6 APIs strictly wrap M5 schemas and are decoupled from the AI\'s M8R-05A workflow.

## 7. M8/M8C source and context assessment
| Source Family | Current Status | Future Role |
|---------------|----------------|-------------|
| TWSE_MIS | Active execution | Internal execution detail |
| TPEX_OPENAPI | Provisional | Internal execution detail |
All sources unequivocally map to m8_source_capability_registry.json.

## 8. M8R contract assessment
| Artifact Series | Current Status | Future Role |
|-----------------|----------------|-------------|
| M8R-03C / 03D / 03E | Active execution contracts | RETAIN_AND_STRENGTHEN (Internal Runtime) |
| M8R-03B | Quick/Standard/Deep intent map | COMPATIBILITY_ONLY_LEGACY mapping |

03C/D/E remain the active internal backend for executing M8R-05A requests. Only the AI-facing vocabulary of 03B is deprecated.

## 9. Phase B Guide and Skill assessment
The current Phase B Skill imposes fixed AI operations and a \'smallest sufficient\' limit. This must be replaced with the flexible M8R-05A composer.

## 10. M8R-05A canonical contract assessment
M8R-05A schemas (Request, Preview, Result, Catalog) are unequivocally confirmed as the single AI-facing contract-shape authority.

## 11. Policy conflict analysis
The blanket recommendation ban in docs/ai_safety_policy.md applies to the canonical project output execution, not the AI\'s analytical conversational freedom.

## 12. Duplicate and source-of-truth analysis
The capability catalogs represent massive duplication drift. The canonical instance must be singular (docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json), with AI projections dynamically synced via hash-bound tests.

## 13. Mode A/B/C retain-and-reinterpret decision
Retain as Operator Frontend States: Mode A (Inspect), Mode B (Preview Execution), Mode C (Package/Handoff).

## 14. Level 1/2 retain-and-reinterpret decision
Retain purely as Evidence Lifecycle Metadata. It describes the data returned, not a request parameter.

## 15. Frontend future role
The frontend is the operator workbench for inspection and approval of M8R-05A previews.

## 16. FastAPI/MCP compatibility role
Legacy compatibility wrappers around M5 endpoints.

## 17. Complete output package architecture
The output package is exhaustive within the bounded request. The system returns the full bounded set.

## 18. Portable Skill synchronization strategy
Maintained via a strict hash-bound sync from the canonical M8R-05A instances.

## 19. File-by-file disposition
Detailed comprehensively in the Migration Plan.

## 20. Migration sequence
Phase 1: Canonical Schemas & Safety Policy. Phase 2: Skills & AI Guides. Phase 3: Frontend/API Legacy labeling. Phase 4: Full Validation.

## 21. Risks and caveats
Schema drift risk remains high until the hash-bound synchronization tests are actively enforcing consistency.

## 22. Recommended next implementation task
M8R-05A-F2-UNIFIED-MARKET-EVIDENCE-AI-GUIDE-AND-PORTABLE-SKILL-REALIGNMENT
