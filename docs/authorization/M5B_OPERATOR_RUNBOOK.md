# M5B operator runbook

Run offline gates first. Execute exactly one `scripts/run_m5b_controlled_live_probe.py --execute-live` invocation only after authorization validation passes. Retry is limited to one transient TWSE_OpenAPI attempt. Build staging candidate from the bounded run directory only; do not promote.
