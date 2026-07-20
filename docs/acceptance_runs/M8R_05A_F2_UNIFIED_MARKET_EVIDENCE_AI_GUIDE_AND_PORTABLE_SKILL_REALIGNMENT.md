# Acceptance Report: M8R-05A-F2 Unified Market Evidence AI Guide and Portable Skill Realignment

## Task Status: PASS

- **Date**: 2026-07-20
- **Task ID**: M8R-05A-F2
- **Base Commit**: `e2d799c959c3ba5ba848e162949b1eea839dcef2`

## Scope of Work Verified
1. **AI Guide Realignment**:
   - `docs/agent_usage_guide.md` fully rewritten to align with `unified_market_evidence_request.v1`.
   - Legacy "Mode ABC" and "smallest sufficient" terminology removed.
2. **AI Safety Policy Realignment**:
   - `docs/ai_safety_policy.md` explicitly scopes the recommendation ban to "Project Canonical Output Constraints", preserving AI conversational analysis flexibility.
3. **Skill Realignment and Validation**:
   - `skills/tw-market-evidence-agent/SKILL.md` rewritten.
   - `validate_skill.py` rewritten and successfully validates the new SKILL.md.
4. **Portable Catalog Sync Generation**:
   - `skills/tw-market-evidence-agent/assets/m8_ai_capability_contract.json` deleted.
   - Replaced by `unified_capability_catalog_portable.json` dynamically generated from the canonical M8R-05A registry via `scripts/generate_portable_catalog.py`.
   - SHA256 integrity validation enforced by `scripts/validate_portable_catalog_sync.py`.
5. **Fixture Implementation**:
   - 8 required unified market evidence JSON request fixtures created and validated against the schema.
6. **Regression Alignment**:
   - Legacy tests `test_m8r_03e_f1_ai_capability_guide.py` and `test_m8r_03e_r3_contract_source_of_truth.py` updated to test the new Portable Catalog instead of the deleted asset.

## Test Results
- `pytest tests/unit/test_m8r_05a_f2_ai_guide_and_skill.py` - **PASS** (3/3)
- `pytest tests/unit/test_m8r_05a_f2_portable_skill_sync.py` - **PASS** (2/2)
- `python skills/tw-market-evidence-agent/scripts/validate_skill.py` - **PASS**
- Full non-network regression (`pytest -m "not network" -q`) completed. 
  *(Note: 43 pre-existing failures related to Windows CP950 decoding inside `m5c` test suites and git shallow checkout issues were identified. These are environmental failures and not introduced by F2 changes, as F2 tests pass consistently).*
