# Post-Phase-L F0 — Frontdoor Inventory & Information Architecture

Date: `2026-10-28`

Status: `POST_PHASE_L_F0_FRONTDOOR_INFORMATION_ARCHITECTURE_CANDIDATE_COMPLETE`

## 1. Purpose and boundary

F0 is a documentation-governance inventory and information-architecture decision only. It does not change product behavior, runtime contracts, release artifacts, the `v1.5.0` tag, GitHub Release asset bytes, MCP Registry metadata, Docker registry state, or Phase M authority.

The frozen `v1.5.0` release remains defined by source commit `acaf726a5b59baee4c5a30521ea5a5d5ec0cec76` and source tree `d44f66dc154c21326ac8b105d2f15fd793f6071b`. Post-release documentation commits on `main` are allowed to move beyond that commit without redefining the frozen release.

This tranche intentionally separates:

1. current public/product documentation;
2. current engineering/operational authority;
3. frozen or historical gate evidence;
4. independently published external metadata such as the MCP Registry surface.

## 2. Accepted input authority

The Post-Phase-L documentation tranche consumes the already accepted release/closure facts below; it does not recreate or reinterpret them.

| Authority | Accepted fact | SHA-256 of decision/report |
|---|---|---|
| R3 final freeze decision | `STABLE_SOURCE_FROZEN=true`, `FINAL_ARTIFACT_HASHES_FROZEN=true`, L7-A6 overall acceptance PASS | `cd297d5173070478ff354b43a69facd628dd36f2b442950a4d4b5c29141f9ef9` |
| A7 publication decision | GitHub stable release `v1.5.0` published; six assets verified; Registry publication not performed | `2493766a4560135ffba6317735836d85e0a23f6bab317189e9a6ce30865f721b` |
| Phase L Owner final closure decision | `PHASE_L=CLOSED`, `PHASE_M=NOT_AUTHORIZED`, 29/29 L7 exits PASS, no release-blocking gaps | `7eb7e7245993927a770de83b872f0762ced6dca07ba1f7f91ad6b4d1f8d841c1` |
| Phase L Owner final closure report | Subsequent README / PROJECT / HANDOFF / GitHub frontdoor work is Post-Phase-L documentation work and must not redefine frozen v1.5.0 identities | `113b1b02a93b195a3e1d2c8a8e5cff9fd6bdde6aafef6e26ed82bc636a42ea92` |

Current GitHub `main` was independently checked at F0 and still points to the frozen source commit above. GitHub Release `v1.5.0` is the latest stable release.

### Frozen release asset set

The six verified publication assets are:

- `TW-Market-1.5.0-windows-x64.zip`
- `TW-Market-1.5.0-windows-x64.zip.sha256`
- `tw-market-unified-mcp-v1.5.0-win-x64.mcpb`
- `tw-market-unified-mcp-v1.5.0-win-x64.mcpb.sha256`
- `TW-Market-1.5.0-first-party-sbom.json`
- `TW-Market-1.5.0-publication-manifest.json`

No Post-Phase-L frontdoor tranche may replace or mutate those release assets.

## 3. F0 current-state findings

The repository contains strong product and governance documentation, but the root/current frontdoors still describe the pre-publication L7-A6-P0 state because the stable release and final Phase L closure happened after the frozen source was established.

The problem is therefore **post-release frontdoor reconciliation**, not a product defect and not a reason to reopen Phase L.

Principal contradictions found in current-facing surfaces:

| ID | Surface | Finding | Disposition |
|---|---|---|---|
| F0-C01 | `README.md` | says ProductVersion 1.5.0 is selected/unpublished and stable is v1.0.0 | F1 rewrite to current published stable truth |
| F0-C02 | `README.md`, `README.zh-TW.md` | primary MCP download links still point to v1.0.0 | F1/F2 point GitHub users to v1.5.0 while preserving Registry distinction |
| F0-C03 | `CHANGELOG.md` | heading is `1.5.0 (selected, unpublished)` and pre-A7 boundaries remain | F2 convert 1.5.0 entry to released history |
| F0-C04 | `docs/operator/QUICK_START.md` | source checkout is the primary onboarding path and a stale Phase H limitation is presented as current | F2 split Native / MCPB / source paths and reconcile current capability wording |
| F0-C05 | `docs/distribution/MCP_DISTRIBUTION.md` | presents v1.0.0 bundle as the current GitHub distribution | F2 distinguish latest GitHub v1.5.0 distribution from separately published Registry metadata |
| F0-C06 | `PROJECT.md`, `HANDOFF.md` | append-only history dominates the files; top sections still say A7 unauthorized / Phase L not closed / v1.0.0 stable | F3 rebuild as compact current authorities; preserve history elsewhere |
| F0-C07 | `ROADMAP.md`, `docs/governance/INDEX.md` | current headers/status metadata stop before A6/R3/A7/final closure | F3 targeted reconciliation only; do not rewrite frozen historical milestones |
| F0-C08 | `AGENTS.md` | collaboration rules remain valuable, but its current-phase headers stop at Phase J/K-era state | F3 reconcile only current boundary/stop rules; preserve durable AI collaboration rules |
| F0-C09 | `docs/PROJECT_HISTORY.md` | explicitly historical and useful, but chronology ends at 2026-09-23 | F3 extend high-level chronology before root history is removed from PROJECT/HANDOFF |
| F0-C10 | README lifecycle validators/tests | several scripts/tests require `selected/unpublished` to pass when VERSION=1.5.0 | F5 validation dependency; update validator semantics with the docs, not in F0 |
| F0-C11 | `packaging_native/README-PACKAGE.md` | frozen v1.5.0 embedded package text still says formal SBOM is future work | preserve for this tranche; it is release-embedded source, not the GitHub current frontdoor |
| F0-C12 | `server.json` | MCP Registry metadata remains v1.0.0 | intentional independent publication state; do not modify without separate Registry authorization |

No mass search/replace of phrases such as `unpublished`, `NOT_AUTHORIZED`, or `Phase L NOT_CLOSED` is permitted. Those phrases remain correct inside historical/frozen records describing earlier gates.

## 4. Information architecture decision

The repository documentation is organized conceptually into four layers.

### Layer 1 — Public product frontdoor

Purpose: answer, within one screen, what TW-Market is, why it is useful, what the current stable release is, and how a user should start.

Primary surfaces:

- `README.md`
- `README.zh-TW.md`
- GitHub About description/topics/homepage metadata
- `CHANGELOG.md`

Target public positioning:

> **Local-first Taiwan market evidence for humans and AI agents.**

Formal longer descriptor may continue to use:

> **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**

The repository name remains unchanged. The frontdoor must make clear that “live data” does not promise realtime quotes, autonomous polling, trading, or a quote-terminal product.

### Layer 2 — User and AI documentation

Purpose: get a user or agent to a successful governed workflow without requiring roadmap/governance knowledge.

Primary surfaces:

- Native installation / operator Quick Start
- MCPB distribution and MCP setup
- Workbench usage
- agent usage guide
- capability/reference documentation
- future `llms.txt` candidate

The default onboarding choice is three explicit paths:

1. **Windows Native ZIP** — normal local operator / Workbench path;
2. **Windows MCPB** — AI / MCP client path;
3. **Source checkout** — developer path.

Source checkout is no longer the universal first-run recommendation.

### Layer 3 — Current engineering authority

Purpose: describe current project truth, current stop point, durable roadmap scope, and collaboration rules without replaying the entire project chronology.

Primary surfaces:

- `PROJECT.md` — current project/product authority, not a chronological journal;
- `HANDOFF.md` — current stopping point, allowed next work, do-not-repeat rules, resume order;
- `ROADMAP.md` — durable architecture/phase scope plus concise reconciled status;
- `AGENTS.md` — durable repository/AI collaboration rules plus current stop boundary;
- `docs/INDEX.md` — persona-oriented navigation;
- `docs/governance/INDEX.md` — governance navigation and current governance pointer.

### Layer 4 — Frozen / historical evidence

Purpose: preserve exact gate truth and provenance at the time it was accepted.

Examples:

- `docs/governance/phase_l/**`
- acceptance runs and ledgers
- frozen contracts and gate decisions
- `docs/release/V1_5_0_RELEASE_NOTES_DRAFT.md`
- archive/review/protocol evidence

Historical records are not rewritten merely because later promotion or closure occurred.

## 5. Surface disposition matrix

| Surface | Class | Planned tranche | F0 disposition |
|---|---|---:|---|
| `README.md` | PUBLIC_CURRENT | F1 | substantial information-architecture rewrite |
| `README.zh-TW.md` | PUBLIC_CURRENT | F1 | rewrite for true English/Traditional-Chinese content parity |
| GitHub About description | PUBLIC_CURRENT_METADATA | F4 | current description is already strong; review, do not churn without benefit |
| GitHub homepage field | PUBLIC_CURRENT_METADATA | F4 | currently blank; keep blank unless a real docs/site destination exists |
| GitHub topics | PUBLIC_CURRENT_METADATA | F4 | retain current set; optional evidence/provenance topic polish only |
| `CHANGELOG.md` | PUBLIC_RELEASE_HISTORY | F2 | reconcile v1.5.0 as published release |
| `docs/operator/QUICK_START.md` | USER_CURRENT | F2 | redesign around Native / MCPB / source paths |
| `docs/distribution/MCP_DISTRIBUTION.md` | USER_CURRENT | F2 | update GitHub v1.5.0 distribution; explicitly separate Registry state |
| `docs/INDEX.md` | NAV_CURRENT | F3 | change governance-first navigation to persona-first navigation |
| `PROJECT.md` | ENGINEERING_CURRENT | F3 | compact to current truth; remove append-only milestone journal role |
| `HANDOFF.md` | OPERATIONS_CURRENT | F3 | compact to current stop/resume/allowed-work authority |
| `ROADMAP.md` | DURABLE_ROADMAP_CURRENT | F3 | targeted status/checklist reconciliation; preserve roadmap architecture |
| `AGENTS.md` | ENGINEERING_RULES_CURRENT | F3 | targeted current-boundary reconciliation; preserve durable rules |
| `docs/governance/INDEX.md` | GOVERNANCE_INDEX_CURRENT | F3 | update current pointer/header; retain historical navigation |
| `docs/PROJECT_HISTORY.md` | HISTORICAL_SUMMARY | F3 | extend high-level chronology; becomes destination for condensed root history |
| `docs/agent_usage_guide.md` | AI_CURRENT | F4 | currentness/link/capability audit; edit only where current authority proves drift |
| `skills/tw-market-evidence-agent/SKILL.md` | AI_CURRENT | F4 | audit against current six-tool/current-route authority; no speculative changes |
| `llms.txt` | AI_DISCOVERABILITY_NEW | F4 | candidate new short machine/agent frontdoor |
| simplified architecture diagram | PUBLIC_VISUAL_NEW | F4 | create product-flow diagram; full Workbench screenshot moves lower in README |
| `packaging_native/README-PACKAGE.md` | FROZEN_RELEASE_EMBEDDED_DOC | PRESERVE | no Post-Phase-L frontdoor edit |
| `docs/release/V1_5_0_RELEASE_NOTES_DRAFT.md` | HISTORICAL_RELEASE_INPUT | PRESERVE | retain exact pre-publication source wording |
| `config/l7_release_artifact_set.v1.json` | FROZEN_RELEASE_CONTRACT | PRESERVE | no frontdoor edit |
| `docs/contracts/L7_PUBLIC_COMPATIBILITY_MCP_SDK_VERSION_POLICY.md` | FROZEN_GATE_CONTRACT | PRESERVE | historical A4 policy remains gate truth |
| `docs/contracts/L7_RELEASE_SOURCE_AND_PUBLICATION_MANIFEST_CONTRACT.md` | FROZEN_GATE_CONTRACT | PRESERVE | historical R1 contract remains gate truth |
| `server.json` | EXTERNAL_REGISTRY_PUBLICATION_SURFACE | SEPARATE_AUTHORIZATION | Registry remains v1.0.0 until an explicitly authorized Registry publication |
| `scripts/validate_v1_front_door.py` | VALIDATION_DEPENDENCY | F5 | must learn published-v1.5 lifecycle semantics |
| `scripts/validate_v1_public_contracts.py` | VALIDATION_DEPENDENCY | F5 | must not infer `selected_unpublished` solely from ProductVersion 1.5.0 |
| `scripts/run_m5ij_end_to_end_acceptance.py` | VALIDATION_DEPENDENCY | F5 | current README wording acceptance requires reconciliation |
| `tests/unit/test_validate_v1_public_contracts.py` | VALIDATION_DEPENDENCY | F5 | add/adjust v1.5.0 published lifecycle coverage |
| `tests/unit/test_l7_a4_local_service_compatibility.py` | MIXED_CURRENT_AND_HISTORICAL_TEST | F5 | preserve historical A4 test intent; add current lifecycle proof separately rather than laundering A4 history |
| `tests/unit/test_l7_a6_r1_release_contract.py` | HISTORICAL_GATE_TEST | PRESERVE | retains R1 draft/gate semantics; do not update merely to make README current |

## 6. README decision for F1

The target README order is frozen for F1 planning as:

1. Hero / one-line positioning
2. Current stable release and a small badge set
3. **Choose your path** — Native ZIP / MCPB / source
4. 60-second Quick Start
5. What TW-Market does
6. How it works
7. MCP / AI Agent workflow
8. Deliberate safety boundaries and non-goals
9. Documentation map
10. Contributing / Security / License

The tall full Workbench screenshot is not the hero. F4 will create a simpler product-flow visual and retain the full screenshot lower in the document or behind a disclosure block.

## 7. Installation / distribution decision for F2

GitHub distribution truth and Registry truth are independent:

- GitHub stable release: `v1.5.0` — published and verified;
- Windows Native ZIP: current recommended local/operator distribution;
- Windows MCPB: current GitHub AI/MCP distribution;
- MCP Registry metadata: not updated by A7 and not authorized by this documentation tranche;
- Docker: validation/provenance only for v1.5.0; no Docker registry publication claim.

Public docs may link to the GitHub v1.5.0 assets. They must not imply that MCP Registry or Docker registry publication occurred.

## 8. PROJECT / HANDOFF consolidation decision for F3

`PROJECT.md` and `HANDOFF.md` are no longer allowed to function as append-only milestone journals.

Target roles:

- `PROJECT.md`: approximately 100–150 lines of current product/project authority;
- `HANDOFF.md`: approximately 60–120 lines covering current stop, current tranche, allowed next actions, forbidden/repeat work, and resume order.

Before removing historical blocks from those root files, F3 must verify that the durable historical meaning is represented by dedicated governance records or by `docs/PROJECT_HISTORY.md`. Where a useful high-level chronology exists only in the root journal, F3 must first add a concise history entry rather than silently discard it.

`ROADMAP.md` remains the durable architecture/phase-scope authority and is not collapsed into `PROJECT.md`. Its current status metadata and Phase L/Phase M boundary must, however, be reconciled.

## 9. AI/discoverability decision for F4

`llms.txt` is approved as a **candidate** for F4, not created by F0. It should be short and pointer-based rather than duplicate the agent guide, capability catalog, routing matrix, or skill.

F4 should also review:

- concise architecture/product-flow diagram;
- screenshot placement;
- 4–5 badges maximum;
- GitHub topics/description only where a concrete improvement exists;
- current AI guide / Skill route references.

A large `llms-full.txt` is not currently justified because the repository already has structured capability/routing data and AI usage guidance.

## 10. F5 validation dependency contract

Documentation maintenance is not complete merely because Markdown renders.

F5 must verify at minimum:

- no stale current-facing `selected/unpublished`, `v1.0.0 stable`, A7-not-authorized, or Phase-L-not-closed claims remain outside intentionally historical/frozen contexts;
- README validators represent `v1.5.0` as a published stable lifecycle without changing product SemVer;
- historical A4/R1 contract tests remain historical rather than being rewritten to pretend their earlier gate state never existed;
- current Markdown links and v1.5.0 download URLs resolve;
- exact six-tool MCP contract remains unchanged;
- current Native/MCPB/SBOM/manifest references match the frozen release names and hashes where hashes are stated;
- `git diff --check` passes;
- no runtime/product/release artifact bytes are changed by the documentation tranche unless separately authorized and explicitly classified.

## 11. Non-negotiable edit rules for F1–F5

1. Do not modify the `v1.5.0` tag or its six published assets.
2. Do not describe post-release `main` documentation commits as part of the frozen v1.5.0 source tree.
3. Do not mass-rewrite historical acceptance records to current state.
4. Do not change MCP Registry metadata (`server.json`) as a side effect of GitHub documentation work.
5. Do not publish Docker images or claim Docker registry availability.
6. Do not start or authorize Phase M.
7. Do not add a seventh MCP tool or alter execution semantics.
8. Preserve explicit authorization / preview / execute-once / audit semantics.
9. Keep realtime/trading/autonomous-polling non-goals visible.
10. Treat current documentation and historical gate truth as separate authority classes.

## 12. Planned tranche sequence

- **F1 — Public Product Frontdoor:** README / README.zh-TW and GitHub-facing product narrative.
- **F2 — Install / Quick Start / Distribution:** Native / MCPB / source entry paths, Quick Start, MCP distribution, CHANGELOG.
- **F3 — Engineering Frontdoor Consolidation:** PROJECT, HANDOFF, ROADMAP current-status reconciliation, AGENTS current boundary, docs indexes, high-level project history.
- **F4 — AI / Discoverability / Visual Polish:** `llms.txt` candidate, agent/skill audit, architecture diagram, screenshot/badge/topic polish.
- **F5 — Documentation-only Validation:** contradiction scan, link/download verification, validation-dependency updates, focused tests and final scope audit.

Each tranche remains independently reviewable. No later tranche is implied complete by F0.

## 13. F0 acceptance criteria

F0 is complete when all of the following are true:

- frozen v1.5.0 source/release identity is recorded;
- Phase L CLOSED / Phase M NOT_AUTHORIZED boundary is recorded;
- current public, engineering-current, historical/frozen, external-publication and validation-dependency surfaces are separated;
- current frontdoor contradictions are inventoried;
- F1–F5 ownership for affected surfaces is assigned;
- no product/runtime/release artifact or GitHub publication setting is modified;
- the F0 worktree differs from frozen source only by F0 governance record(s).

F0 does not itself authorize a commit, push, PR, merge, Registry update, Docker publication, or Phase M work.