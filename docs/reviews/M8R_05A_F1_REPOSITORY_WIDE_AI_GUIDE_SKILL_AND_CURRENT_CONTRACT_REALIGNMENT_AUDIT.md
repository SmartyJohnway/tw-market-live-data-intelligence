# M8R-05A-F1: Repository-Wide AI Guide, Skill, and Current Contract Realignment Audit

## 1. Executive decision
The project adopts M8R-05A as the current canonical AI-facing contract. The AI Skill is responsible for generating M8R-05A compliant requests, and the project is responsible for exhaustive canonical execution within the bounded request. Mode A/B/C are retained as frontend workflow stages, and Level 1/2 as evidence lifecycle metadata.

## 2. Audit scope and baseline
- **Baseline commit**: b9f9effdaa76d1a108ae430085737e4dad3af524
- **Scope**: Entire repository, focusing on AI-facing contracts, schemas, and legacy guides.

## 3. Current product north star
The project provides a Unified Market Evidence Workbench where AI acts as the requester and analyzer, while the project provides reliable, bounded, and exhaustive canonical data.

## 4. Repository-wide artifact inventory summary
Analyzed docs/, skills/, schemas/, and frontend/. Identified legacy intents in agent_usage_guide.md and SKILL.md that need rewriting.

## 5-10. Assessment Summaries
- **M5 model assessment**: M5 workflows heavily rely on Mode A/B/C as AI intents. Needs reinterpretation.
- **M8R-05A canonical contract assessment**: Solidified as the single source of truth for request/result.

## 11. Policy conflict analysis
- **Recommendations**: Project output is canonical and devoid of recommendations, but AI is free to hypothesize within policy bounds.
- **Smallest sufficient vs exhaustive**: Replaced with "exhaustive within authorized bounds".

## 12. Duplicate and source-of-truth analysis
- capability_quick_guide.md duplicates unified_market_evidence_capability_catalog.v1.schema.json. JSON schema wins.

## 13-14. Mode A/B/C and Level 1/2
- **Mode A/B/C**: Frontend workflow states (Inspect, Preview, Package).
- **Level 1/2**: Evidence lifecycle metadata.

## 15-22. Future architecture
- **Frontend**: Serves as Inspector, Previewer, and AI Handoff portal.
- **Recommended next task**: M8R-05A-F2-UNIFIED-MARKET-EVIDENCE-AI-GUIDE-AND-PORTABLE-SKILL-REALIGNMENT to implement the rewrites.
