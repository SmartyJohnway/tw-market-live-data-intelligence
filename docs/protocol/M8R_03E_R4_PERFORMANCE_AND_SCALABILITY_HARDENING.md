# M8R-03E R4 performance and scalability hardening

R4 measures the existing evidence → optional handoff → manifest pipeline without changing evidence or AgentPolicy ownership. The machine-readable measurement contract is `docs/contracts/m8r_03e_r4_performance_measurement_contract.json`.

Production measurements are separately schema-valid one- and ten-target requests. Fifty and one hundred targets are **stress_only**, **non_contract** aggregates of independently valid ten-target pipelines. They do not authorize a larger watchlist or claim a single package/request is valid at those sizes.

The benchmark uses two warmups, five normal repetitions, and three stress repetitions. It measures monotonic-clock stages and `tracemalloc` allocation peak; process `ru_maxrss` is supplementary and platform-labelled. Timings are same-environment evidence, not cross-machine limits. Benchmark-only operation counters are injected into the harness and are never evidence fields.

The profile is manual under `NO_GITHUB_CI`; it performs no network, browser, or live work. Atomic-write measurements use temporary directories and the production `atomic_write_text` containment path.
