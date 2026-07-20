# M8R-05A-F1 AI Guide, Skill, and Contract Realignment Migration Plan

## Phase 1: Core AI Guide and Skill Rewrite (Next Task: M8R-05A-F2)

### 1. docs/agent_usage_guide.md
- **Current**: Legacy Phase B AI Guide.
- **Required Change**: Rewrite to align with M8R-05A Unified Request. Remove intent taxonomy (quick/standard/deep).
- **Priority**: P0

### 2. skills/tw-market-evidence-agent/SKILL.md
- **Current**: Instructions for LLM with old taxonomy.
- **Required Change**: Update to output Unified Market Evidence Request instead of old intents.
- **Priority**: P1

### 3. docs/ai_safety_policy.md
- **Current**: Prohibits recommendations and limits output scopes (smallest sufficient).
- **Required Change**: Clarify that project canonical output does not include recommendations, but AI may discuss scenarios based on policy. Remove smallest sufficient, replace with exhaustive within authorized bounds.
- **Priority**: P0

## Phase 2: Deprecate Legacy Assets

### 4. skills/tw-market-evidence-agent/references/capability_quick_guide.md
- **Current**: Redundant capability list.
- **Required Change**: Archive/Delete. Superseded by M8R-05A catalog JSON.
- **Priority**: P1

## Phase 3: Terminology and Frontend Update

### 5. docs/m5k_local_ai_workflow.md
- **Current**: Mode A/B/C and Level 1/2 in M5 AI context.
- **Required Change**: Re-interpret Mode A/B/C as frontend/operator concepts. Re-interpret Level 1/2 as metadata.
- **Priority**: P0
