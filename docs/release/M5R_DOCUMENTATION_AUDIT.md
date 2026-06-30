# M5R Documentation Audit

## Files reviewed

README, docs index, architecture docs, operator docs, reference docs, contributor docs, release docs, reviews index, archive index, FastAPI endpoints, MCP tools, scripts, config, M5F staging package, live observation runs, tests, and workflows were reviewed for release-hardening alignment.

## Stale wording repaired

The product README and docs index were rewritten to use current Mode A/B/C, Level 1/2, Local Release Candidate, not realtime guaranteed, and Not Production Ready language. Stale current-product references to legacy probe routes were replaced with fail-closed/disabled wording.

## Moved/archived docs

The pre-M5R README was archived at `docs/archive/readme/README_PRE_M5R_20260630_PRODUCT_RELEASE_HARDENING.md`. Existing historical docs were retained.

## Broken links repaired

The master docs index was rebuilt with links to existing files only. Manual link audit was performed for the M5R-created docs.

## Known remaining historical docs

Historical M3/M4/M5 milestone reports remain under `docs/reviews/` and protocol/authorization directories. They are retained as historical evidence and should not be read as the current product entry point unless linked from the master index.

## Commands checked

```bash
rg -n "M3G|M5E|production ready|realtime guaranteed|buy/sell/hold|target price|ranking|recommendation|polling|scheduler|full-market scan|frontend/public|research/generated" README.md docs
```

Results include valid forbidden-behavior warnings, historical archive/review references, and legacy protocol names. No current product page intentionally claims production readiness, realtime guarantees, trading outputs, polling, scheduler operation, full-market scans, or forbidden publication refreshes.

## Final documentation status

Pass: M5R documentation information architecture is release-ready with historical caveats preserved and current product entry points made explicit.
