# M8R-06-01C2 Governed Mode A Security Master Pointer Activation

Baseline: `de8c684ee192a564bd4dc3ddc89dbb59a54305ee`

Status: **PASS_WITH_CAVEATS**

Principal decision: **READY_FOR_M8R_06_01C_POST_ACTIVATION_ACCEPTANCE_REVIEW**

This closes C2 implementation only. M8R-06-01C Post-Activation Acceptance and M8R-06-02 remain **NOT_AUTHORIZED**.

## Activated chain

Production Mode A now follows one fail-closed selection chain:

```text
config/m8r_06_mode_a_security_master_pointer.json
  -> committed C1B immutable candidate seal
  -> local compact manifest
  -> local compact index
  -> merged C1B strict validator
  -> canonical-compatible lookup
  -> existing F3 target validation and canonical resolver
```

The pointer binds the accepted sealed bundle, semantic snapshot ID, source and artifact hashes, both schema hashes, record and coverage counts, paths, artifact type, and local-only activation policy. Absolute paths, traversal, alternate candidates, missing dependencies, forged bindings, and tampered artifacts fail closed. No fixture or network fallback exists in production.

## Activation proof

The exact local candidate from PR #184 was reproduced and validated:

- compact index SHA-256: `ad467f077c76d9c7462545fcf322d4960cbd485d09d34463e26dfefea8c1c455`;
- compact manifest SHA-256: `01857224d025bd9342402917c140050f0fb40b385a65103702c856037dfc93db`;
- record count: 43,070;
- runtime eligible: 2,324.

An actual production API request for `2330 / TWSE` returned HTTP 200 and resolved to `TWSE:2330`. Additional governed runtime results were:

- `TPEX:5227`: resolved;
- `C2_NOT_FOUND_SENTINEL`: not found;
- `5227` with a TWSE hint: market mismatch;
- `TWSE:5871A`: unsupported security type;
- repeated `TWSE:2330`: duplicate.

Missing pointer/candidate/manifest/seal, pointer/path tampering, manifest/index tampering, seal mismatch, and coverage mismatch all fail closed. The API preserves HTTP 409 with `canonical_security_master_unavailable` and does not expose paths or tracebacks.

## Validation

- Focused C2 tests: 21 passed, including the non-skipped sealed local activation.
- C1B regressions: 23 passed.
- Canonical Security Master regressions: 18 passed.
- Mode A/F3 regressions: 42 passed.
- Workbench/API regressions: 8 passed with one existing deprecation warning.
- Python compileall: passed.
- Repository default CI: 789 passed, zero failed, no network.

## Performance preflight

Method: new Python process, no application cache, Windows OS file cache not cleared, `perf_counter` wall time, no network.

- candidate size: 68,256,184 bytes;
- compact JSON load: 1.077 seconds;
- strict validation: 8.754 seconds;
- lookup construction: 0.276 seconds;
- total runtime load: 9.152 seconds;
- 2330 resolver median: 0.0037 milliseconds; p95: 0.0041 milliseconds;
- two-target validation median excluding runtime load: 1.711 milliseconds;
- two-target production end-to-end: 9.713 seconds.

No existing contract defines a latency failure threshold. Peak memory was not measured reliably. The local-only candidate and full per-call validation cost are accepted C2 caveats for the subsequent, separately authorized Post-Activation Acceptance review.

## Scope boundary

Production runtime and the committed pointer are activated. No network probe was used. Mode B, Mode C, refresh scheduling, background refresh, MCP, watchlists, Post-Activation Acceptance, and M8R-06-02 were not started.
