# J-B04-A6-P1-R1 — Bootstrap Transport Bound Hardening

Disposition: **READY FOR EXACT-HEAD INDEPENDENT REVIEW**. This correction and hardening are network-free. The bootstrap was not run.

## Correction to P1

Independent review `5469703234` found that P1’s inspection looked only for limits declared inside `SafeRedirectHandler`. The handler inherits `urllib.request.HTTPRedirectHandler`; in the tested CPython `3.12.14` runtime, the effective inherited `max_repeats` is **4** and `max_redirections` is **10**. The helper now proves the subclass relationship and reads these runtime attributes. They are recorded as observations for this runtime, not universal Python constants.

P1’s finding that the project lacked a sufficiently tight bootstrap-wide dispatch bound remains valid. P1 is superseded **only for its redirect-bound classification**. Its Security Master, identity, H3 authority, and inactive H2 findings are preserved. The original P1 record and commit history are unchanged.

## Project-owned bootstrap bound

The existing `probe_sources.probe()` transport now accepts optional bounded parameters, preserving compatibility for generic diagnostic callers. The production materializer explicitly passes a single shared `BootstrapDispatchBudget` and a per-probe redirect cap to every probe:

```text
logical probes:                         5
maximum redirects followed per probe:  1
maximum dispatches per probe:          2
whole-bootstrap dispatch ceiling:      10
automatic retries:                     0
```

The initial request reserves its slot before `opener.open()`. An allowed redirect is validated for HTTPS and an allowlisted host, then reserves its slot inside `redirect_request()` before urllib receives the redirect request. A second redirect is rejected before its target dispatch. A disallowed host is rejected before target reservation. The shared budget prevents dispatch 11. Successful source payload persistence remains the existing installation-local materializer behavior; transport failures do not persist raw bodies for the new bounded outcomes.

Stable classifications are `BOOTSTRAP_REDIRECT_LIMIT_EXCEEDED`, `BOOTSTRAP_DISPATCH_BUDGET_EXHAUSTED`, and `BOOTSTRAP_REDIRECT_REJECTED`. No source, parser, fallback, or retry behavior was added.

## Future bootstrap authorization metadata

The companion JSON contains a metadata-only template bound to future reviewed HEAD/TREE placeholders, the exact five probes, the per-probe and total caps, zero retry, redirect policy, prohibited A6/H3/H2 actions, and stop conditions. It is **not authorization** and does not execute anything. No current lease or Owner authorization was created.

## Preserved authority state

Security Master remains `NOT_INITIALIZED`; production identity is not verified. H3 is accepted at the Owner product-authority level for the existing bounded TWSE route, while provider automation permission remains `NOT_ESTABLISHED_TERMS_CONFLICTED`; no provider approval or redistribution permission is claimed. H2 remains inactive, unselected, and `plan_only`. J-B04 remains blocking, Phase J has not started, and MCP remains six.

## Validation

All tests use fake transport and deny real sockets. The full five-probe envelope test uses exactly ten fake dispatches; the next reservation fails before fake transport. No Security Master bootstrap or market call was made. The machine validator is `scripts/validate_phase_j_b04_a6_p1_r1_bootstrap_transport_bound.py`.
