# M5FGH Release Checklist

## Compile and tests
- [ ] `python -m compileall scripts server tests`
- [ ] Targeted M5F/M5FGH tests pass.
- [ ] `pytest -m "not network" -v` passes.

## Package reproducibility
- [ ] `build_m5f... --check-only` passes.
- [ ] `validate_m5f... --package-dir research/staging/m5f/m5f_canonical_market_context_01` passes.
- [ ] Rebuild under the platform temp directory, for example `/tmp` on Linux/macOS or `%TEMP%` on Windows is byte-identical.

## Manifest and lineage
- [ ] Exact file set is listed except manifest itself.
- [ ] M5D candidate, M5D manifest, M5D source binding, M5C package, M5C manifest/audit/correction hashes are recomputed and match.

## Exact market context
- [ ] Symbols exactly `0050`, `00929`, `2330`.
- [ ] Source exactly `TWSE_OpenAPI`.
- [ ] Source date exactly `2026-06-26`.
- [ ] Values exactly `103.1`, `29.96`, `2340.0`.

## Consumer consistency
- [ ] Frontend preview consumes M5F canonical package.
- [ ] FastAPI validates package before returning artifacts.
- [ ] MCP validates package before returning artifacts.
- [ ] Briefing reflects same package.

## Forbidden path and behavior gates
- [ ] No `frontend/public` changes.
- [ ] No `research/generated` changes.
- [ ] No M5B/M5C/M5D mutation.
- [ ] No network market-data calls, live probes, publication, production refresh, broker/auth activation, full-market scans, polling loops, trading signals, target prices, rankings, or realtime claims.

## Blockers
Any validation failure, package/consumer disagreement, forbidden path change, or positive realtime/trading/production-current-state claim blocks release.
