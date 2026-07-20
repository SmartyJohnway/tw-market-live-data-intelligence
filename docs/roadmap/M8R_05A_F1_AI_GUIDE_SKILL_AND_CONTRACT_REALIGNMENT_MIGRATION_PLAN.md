# M8R-05A-F1 AI Guide, Skill, and Contract Realignment Migration Plan

## P0 / P1 Artifacts

### 1. docs/ai_safety_policy.md
- **Current role**: Global safety rule with blanket ban.
- **Future role**: Ban applies strictly to canonical execution.
- **Modify in F2**: Yes
- **Breaking Risk**: High
- **Tests**: test_m8r_05a_f1_audit_validation.py
- **Acceptance**: Manual Review

### 2. docs/agent_usage_guide.md
- **Current role**: M5F/M5I-centric workflow.
- **Future role**: Pure M8R-05A request generation guide.
- **Modify in F2**: Yes
- **Breaking Risk**: High
- **Tests**: test_m8r_05a_f1_audit_validation.py
- **Acceptance**: Manual Review

### 3. skills/tw-market-evidence-agent/SKILL.md
- **Current role**: Fixed operations and smallest-sufficient mapping.
- **Future role**: Output Unified Request.
- **Modify in F2**: Yes
- **Breaking Risk**: High
- **Tests**: test_m8r_05a_f1_audit_validation.py
- **Acceptance**: Validation tests pass.

### 4. skills/tw-market-evidence-agent/references/capability_quick_guide.md
- **Current role**: Duplicate unstructured capability listing.
- **Future role**: Generated projection from canonical catalog.
- **Modify in F2**: Yes
- **Breaking Risk**: Medium
- **Tests**: test_m8r_05a_f1_audit_validation.py
- **Acceptance**: Hash-bound sync verified.

### 5. docs/ai/M8_AI_CAPABILITY_QUICK_GUIDE.md
- **Current role**: Duplicate unstructured capability listing.
- **Future role**: Deleted or replaced by generated projection.
- **Modify in F2**: Yes
- **Breaking Risk**: Medium
- **Tests**: None
- **Acceptance**: Removal verified.

### 6. docs/ai/m8_ai_capability_contract.json
- **Current role**: Duplicate JSON catalog.
- **Future role**: Deprecated in favor of data_capabilities catalog.
- **Modify in F2**: Yes
- **Breaking Risk**: High
- **Tests**: test_m8r_05a_f1_audit_validation.py
- **Acceptance**: Duplicate removed.

### 7. docs/data_capabilities/unified_market_evidence_capability_catalog.v1.json
- **Current role**: Primary capability source.
- **Future role**: CURRENT_CANONICAL content authority.
- **Modify in F2**: No
- **Breaking Risk**: None
- **Tests**: None
- **Acceptance**: Maintained as truth.

### 8. docs/current_limitations.md
- **Current role**: Outdated limitations.
- **Future role**: Align with M8R-05A.
- **Modify in F2**: Later phase
- **Breaking Risk**: Low
- **Tests**: None
- **Acceptance**: Review.

### 9. docs/evidence_semantics.md
- **Current role**: Outdated semantics.
- **Future role**: Align with M8R-05A.
- **Modify in F2**: Later phase
- **Breaking Risk**: Low
- **Tests**: None
- **Acceptance**: Review.

### 10. frontend/index.html
- **Current role**: Local M5 rendering.
- **Future role**: COMPATIBILITY_ONLY_LEGACY operator view.
- **Modify in F2**: Later phase
- **Breaking Risk**: Low
- **Tests**: test_m8r_05a_f1_audit_validation.py
- **Acceptance**: Passes compatibility tests.

### 11. server/main.py
- **Current role**: Legacy M5 backend endpoints.
- **Future role**: COMPATIBILITY_ONLY_LEGACY wrapper.
- **Modify in F2**: Later phase
- **Breaking Risk**: Low
- **Tests**: test_m8r_05a_f1_audit_validation.py
- **Acceptance**: Passes compatibility tests.

### 12. docs/reference/MCP_REFERENCE.md
- **Current role**: Legacy MCP tool definitions.
- **Future role**: COMPATIBILITY_ONLY_LEGACY.
- **Modify in F2**: Later phase
- **Breaking Risk**: Low
- **Tests**: None
- **Acceptance**: Review.

### 13. docs/data_capabilities/m8_source_capability_registry.json
- **Current role**: Internal execution source list.
- **Future role**: Primary internal runtime registry.
- **Modify in F2**: No
- **Breaking Risk**: None
- **Tests**: None
- **Acceptance**: Review.
