# M7E Preflight Repo Health Audit

Status:
- pass_with_caveats

Scope:
- repo-wide semantic contract audit
- protocol/final acceptance audit
- inventory metadata audit
- runtime surface audit
- AI exposure safety audit
- frontend security audit
- test coverage audit
- code-health/moduleization audit
- Jules suggestions triage

Not in scope:
- M7E implementation
- market clock/session state implementation
- live probes
- broad refactor

## Startup and base verification

- Starting HEAD matched PR #102 merge commit `25699487474d54c4e2ccd6d9d494916d723fbdad`.
- `origin` remote was not configured in the Codex checkout, so remote fetch/pull could not be performed. This was accepted because local HEAD exactly matched the externally verified PR #102 merge commit `25699487474d54c4e2ccd6d9d494916d723fbdad`.
- M7D closure files and inventory metadata were verified before creating the preflight branch.

## Semantic contract audit

| item | result |
| --- | --- |
| M7A final status | pass_with_caveats retained |
| M7B final status | pass_with_caveats retained |
| M7C final status | pass_with_caveats retained |
| M7D final status | pass_with_caveats retained |
| next_task consistency | M7D inventory points to `M7E-MARKET-CLOCK-AND-SESSION-STATE` |
| safe_for_ai_context consistency | M7B/M7C/M7D remain controlled-promotion-only safe context surfaces |
| builder_output_safe_for_ai_context consistency | M7C and M7D builder outputs remain `false` |
| controlled context exposure only | preserved |
| raw_rich_facts_exposed=false | preserved |
| raw_full_ladder_exposed=false | preserved |
| bounded_watchlist_only=true | preserved for M7D |
| not_full_market_breadth=true | preserved for M7D |

## Runtime surface and AI exposure audit

- FastAPI and MCP work remains readonly for the added smoke tests; no network calls or live probe outputs were introduced.
- Raw TWSE MIS payloads, raw rich facts, raw unknown facts, bid/ask ladder arrays, and full-ladder structures remain blocked from AI context exposure.
- No trading signal, recommendation, target price, support/resistance, market-wide trend, sector rotation, or capital-flow language was introduced.

## Frontend security audit

- `frontend/public/index.html` previously used `innerHTML` for matrix load errors and matrix rows.
- The preflight cleanup replaces dynamic matrix/error rendering with `document.createElement`, `appendChild`/`replaceChildren`, and `textContent` helper insertion.
- Static security regression tests now assert that matrix row values and error messages are not interpolated into `innerHTML`.

## sys.path hack status

- `tests/unit/test_twse_mis_normalization_v2.py` no longer appends `../../scripts` to `sys.path`.
- `scripts/__init__.py` was added with a short docstring so the test can use package-style imports.

## Testing gaps and Jules triage

- Jules suggestions triaged: 39.
- Fixed now: 12 low-risk items covering frontend XSS, focused API/MCP smoke tests, import hygiene, and micro-cleanups.
- Deferred: 27 broader code-health or non-trivial test additions, tracked in `M7E_PREFLIGHT_REMEDIATION_BACKLOG.json`.
- Stale/already resolved, rejected, and needs-followup buckets are empty for this pass.

## Code-health backlog

- Several long or high-arity functions remain in legacy probe/build scripts and MCP evidence helpers.
- These are deliberately deferred because refactoring them safely would require broader extraction and semantic regression review.
- Deferred Jules code-health items should be handled as dedicated mechanical refactor PRs after M7E preflight and not mixed with market-clock implementation.

## Moduleization plan

Current issue:
- `scripts/observation_contract.py` now contains M7A, M7B, M7C, M7D contracts/builders/promotion helpers and normalization helpers.
- This should not block M7E, but M7E should avoid further growing this file.

Recommended future extraction:
- `scripts/twse_mis_rich_facts_contract.py`
- `scripts/ai_safe_market_context_contract.py`
- `scripts/deterministic_metrics_contract.py`
- `scripts/bounded_watchlist_cross_context.py`
- `scripts/market_clock_session_state.py`

Migration policy:
- preserve compatibility re-exports from `scripts/observation_contract.py`
- mechanical extraction only
- no semantic behavior changes
- tests before/after extraction
- do not combine with M7E implementation

## M7E readiness

- Ready to proceed to `M7E-MARKET-CLOCK-AND-SESSION-STATE` after merge.
- Caveats: broad module extraction and deferred Jules backlog remain future work.
- M7E implementation was not started in this PR.
